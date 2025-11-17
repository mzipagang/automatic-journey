import asyncio
from copy import deepcopy
from typing import List

from fastapi import HTTPException
from fastapi.params import Depends

from app.common.gateways.activation_gateway import ActivationGateway
from app.common.gateways.campaign_service_gateway import CampaignServiceGateway
from app.common.model.redis import CachedAddress, CachedContact
from app.common.services.lookup_service import LookupService
from app.common.view_models import (
    CampaignPutRequest,
    CampaignStatus,
    ListResponse,
    SingleResponse,
    WorkflowActions,
)
from app.common.context.context import logging_extra_context
from app.common.gateways.workflow_gateway import WorkflowGateway
from app.common.model.advertiser import AdvertiserType, CachedAdvertiser
from app.common.model.campaign_types import InternalCampaignType, convert_enum
from app.common.model.downstream.campaign_activation_service import CASCampaign, AddressReference, ContactReference
from app.common.model.downstream.campaign_service import (
    CampaignSearchRequest,
)
from app.common.model.pause_operation_type import PauseOperationType
from app.common.model.shared import (
    BudgetType,
    EntityMeta,
    InternalBudgetType,
    InternalPublishStatus,
    Meta,
    Page,
    Warnings,
)
from app.common.services.account_service import AccountService
from app.common.services.address_service import AdvertiserAddressService
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.contact_service import AdvertiserContactService
from app.common.utils import filtered_logger
from app.common.utils.campaign_request_monitors import CampaignUpdateRequestMonitor
from app.v2.model.downstream.activation_service import (
    ActivationUpdatePayload, ChannelData, ActivationsQueryBody, ActivationResponse, ActivationResponseV2)
from app.v2.translations.ad_group_translation import AdGroupTranslation
from app.v2.translations.error_translation import ErrorTranslation
from app.v2.utils.campaign_tools import (
    contains_pause_or_unpause_request,
    determine_advertiser_type,
    determine_budget_type,
    determine_end_date,
    determine_start_date,
    get_address_internal_id,
    get_agency_id,
    get_billing_contact_internal_id,
    get_budget,
    get_dates,
    is_pause_requested,
    is_unpause_requested,
    log_campaign_creation_failure,
    process_billing_info,
    process_dates_and_budget,
    process_status,
    request_implies_no_delta,
)
from app.v2.utils.campaign_translations import CampaignTranslation
from app.v2.utils.campaign_validator import (
    CampaignValidator,
    from_upstream_campaign_validations,
    validate_multiple_brand_ids,
)
from app.common.utils.context_tools import update_context
from app.common.utils.jwt import validate_advertisers
from app.v2.utils.campaign_factory import CampaignFactory
from app.v2.view_models import Campaign, CampaignPatchRequest, CampaignRequest, AdGroupV2

logger = filtered_logger.get_logger(__name__)

class CampaignService:
    # Dependencies injected via FastAPI for use in service methods
    account_service: AccountService
    advertiser_service: AdvertiserService
    address_service: AdvertiserAddressService
    contact_service: AdvertiserContactService
    lookup_service: LookupService
    campaign_factory: CampaignFactory
    campaign_gateway: CampaignServiceGateway
    workflow_gateway: WorkflowGateway
    validator: CampaignValidator
    activation_gateway: ActivationGateway
    ad_group_translation: AdGroupTranslation
    error_translation: ErrorTranslation

    def __init__(
            self,
            account_service: AccountService = Depends(AccountService),
            advertiser_service: AdvertiserService = Depends(AdvertiserService),
            address_service: AdvertiserAddressService = Depends(AdvertiserAddressService),
            contact_service: AdvertiserContactService = Depends(AdvertiserContactService),
            lookup_service: LookupService = Depends(LookupService),
            campaign_factory: CampaignFactory = Depends(CampaignFactory),
            campaign_gateway: CampaignServiceGateway = Depends(CampaignServiceGateway),
            workflow_gateway: WorkflowGateway = Depends(WorkflowGateway),
            activation_gateway: ActivationGateway = Depends(ActivationGateway),
            ad_group_translation: AdGroupTranslation = Depends(AdGroupTranslation),
            validator: CampaignValidator = Depends(CampaignValidator),
            error_translation: ErrorTranslation = Depends(ErrorTranslation),
    ):
        self.account_service = account_service
        self.advertiser_service = advertiser_service
        self.address_service = address_service
        self.contact_service = contact_service
        self.lookup_service = lookup_service
        self.campaign_factory = campaign_factory
        self.campaign_gateway = campaign_gateway
        self.workflow_gateway = workflow_gateway
        self.activation_gateway = activation_gateway
        self.ad_group_translation = ad_group_translation
        self.validator = validator
        self.error_translation = error_translation

        self.__backend_service_error_message = 'Backend service unavailable'

    async def create_campaign(
            self,
            campaign_request: CampaignRequest,
            current_user: dict,
            source: str
    ) -> SingleResponse[Campaign]:
        """Create a new campaign"""
        try:
            # Validate user permissions for account and advertisers
            await self.validator.validate_account_and_advertisers(current_user, campaign_request)

            # If user is an agency, retrieve the client the agency works for
            agency_id = get_agency_id(current_user)

            # Process campaign dates, budget type, and always-on status
            start_date, end_date, budget_type, is_always_on = await process_dates_and_budget(campaign_request)

            # Fetch internal account ID using short ID
            account_id = await self.lookup_service.get_account_long_id_by_short_id(campaign_request.accountId)

            # Validate multi-supplier campaign
            await self.validator.validate_campaign_multi_supplier(campaign_request.advertiserIds, account_id)

            # Retrieve advertiser details using numeric IDs
            advertisers = await self.advertiser_service.get_advertisers_by_numeric_ids(campaign_request.advertiserIds)

            # Fetch and validate billing address and contact details
            address = await self.lookup_service.get_address_details_by_short_id(campaign_request.billingAddressId)
            contact = await self.lookup_service.get_contact_details_by_short_id(campaign_request.billingContactId)
            billing_info = await self.validator.validate_billing_info(address, contact, account_id, agency_id)

            # Convert external to internal campaign type and create campaign in Campaign Activation Service (CAS)
            internal_campaign_type = convert_enum(
                campaign_request.campaignType,
                InternalCampaignType
            )
            upstream_campaign: CASCampaign = await self._start_campaign(internal_campaign_type)
            internal_campaign_id: str = upstream_campaign.id
            short_id: int = int(upstream_campaign.shortId)
            background_info = f'API Campaign ID: {upstream_campaign.shortId}'

            # Construct contact and address lists for the campaign
            contact_list = CampaignTranslation.build_contact_list(billing_info['billing_contact_id'])
            address_list = CampaignTranslation.build_address_list(
                billing_info['corporate_address_id'],
                billing_info['billing_address_id']
            )
            internal_contacts = await self.contact_service.get_internal_default_contacts(account_id)

            # Extract billing details from the request
            billing_details = CampaignTranslation.build_billing_info(campaign_request)

            # Prepare payload for updating campaign details
            payload = CampaignTranslation.prepare_update_payload(
                campaign_request, source, short_id, background_info,
                budget_type, is_always_on, advertisers,
                contact_list, internal_contacts, address_list,
                account_id, start_date, end_date, agency_id,
                billing_info['is_agency_billed'], billing_details
            )

            # Update campaign with detailed information
            success = await self._update_campaign_with_details(internal_campaign_id, payload)

            if success:
                # Update the campaign's workflow status
                await self._update_workflow_status(internal_campaign_id)
                # Return the newly created campaign
                return await self.get_campaign_single_response_by_id(short_id)

            # Log failure if campaign creation unsuccessful
            log_campaign_creation_failure(short_id, success)
            return SingleResponse[Campaign](data=None, meta=EntityMeta(success=False))

        except HTTPException:
            # Propagate HTTP exceptions
            raise
        except Exception as e:
            # Log unexpected errors and raise a generic HTTP exception
            logger.error(f'Unexpected error creating campaign: {str(e)}')
            raise HTTPException(status_code=500, detail='Failed to create campaign due to an internal error')

    async def _start_campaign(self, campaign_type: InternalCampaignType) -> CASCampaign:
        """Initialize a campaign workflow and retrieve it from the upstream service"""
        # Initialize the campaign workflow
        workflow_data = await self.workflow_gateway.initialize_campaign(campaign_type)
        if workflow_data.businessKey is None or workflow_data.businessKey == '':
            logger.error("Business key not found in workflow response")
            raise HTTPException(status_code=500, detail=self.__backend_service_error_message)

        # Fetch campaign data from upstream service using business key
        upstream_campaign_response = await self.campaign_gateway.get_campaign(workflow_data.businessKey)
        unpublished_changes = upstream_campaign_response.unpublishedChanges
        published_changes = upstream_campaign_response.publishedChanges
        campaign_upstream = CASCampaign().model_dump()
        if published_changes:
            campaign_upstream = published_changes.model_dump()
        if unpublished_changes:
            # Merge unpublished changes into the campaign data
            campaign_upstream = {**campaign_upstream, **unpublished_changes.model_dump()}

        campaign = CASCampaign(**campaign_upstream)

        if campaign.id and campaign.shortId:
            return campaign

        # Raise an exception if campaign creation fails
        raise HTTPException(status_code=500, detail='Campaign failed to create')

    async def get_campaign_single_response_by_id(
        self,
        campaign_id: int,
        include_ad_groups: bool = False,
        include_ad_group_errors: bool = False,
    ) -> SingleResponse[Campaign]:
        """Retrieve a campaign by ID with optional ad groups"""
        # Convert short campaign ID to internal ID
        internal_campaign_id = await self.get_campaign_long_id(campaign_id)

        # Fetch campaign data from upstream service
        upstream_response = await self.campaign_gateway.get_campaign(internal_campaign_id)
        upstream_validations = upstream_response.validations
        upstream_campaign_data, publication_status = CampaignTranslation.get_campaign_and_publish_status_from_response(
            upstream_response
        )

        # Process any validation warnings from the upstream service
        validation_warnings = list(
            map(from_upstream_campaign_validations, upstream_validations)
        ) if upstream_validations else []

        # Generate the campaign object with optional ad groups
        campaign_response = await self._generate_campaign_response(
            campaign_response=upstream_campaign_data,
            publish_status=publication_status,
            include_ad_groups=include_ad_groups,
            include_ad_group_errors=include_ad_group_errors,
            warnings=Warnings(validation=validation_warnings))

        # Update logging context with campaign details
        update_context(logging_extra_context,
                       campaign_status=campaign_response.data.status,
                       advertiser_ids=campaign_response.data.advertiserIds,
                       account_id=campaign_response.data.accountId)

        # Return the campaign response with metadata
        return campaign_response

    async def _generate_campaign(self, campaign: CASCampaign) -> Campaign:
        """Generate a Campaign object from CASCampaign data"""
        short_id = campaign.shortId

        # Retrieve or create cached account ID
        account_id = await self.account_service.get_or_create_cached_account_id(campaign.primaryAccount.id)
        # Retrieve or create cached advertiser IDs
        advertiser_ids = await self.advertiser_service.get_or_create_cached_advertiser_ids(
            campaign.primaryAccount.brands
        )
        # Determine the type of advertiser
        advertiser_type = determine_advertiser_type(campaign.primaryAccount)

        # Fetch numeric ID for the address
        address_numeric_id = await self._get_address_numeric_id(
            campaign.primaryAccount.addresses,
            advertiser_type,
            short_id
        )

        # Fetch contact ID
        contact_id = await self._get_contact_id(campaign.primaryAccount.contacts)

        # Process the campaign's status
        status = process_status(campaign.status, short_id)

        # Extract start and end dates
        start_date, end_date = get_dates(campaign)

        # Retrieve budget information
        budget = get_budget(campaign)

        # Use additional billing details if available, otherwise empty string
        billing_details = campaign.additionalBillingDetails if campaign.additionalBillingDetails is not None else ''

        # Construct and return the Campaign object
        return Campaign(
            id=int(short_id),
            name=campaign.name,
            status=status,
            startDate=start_date,
            endDate=end_date,
            budgetAmount=budget.amount,
            budgetType=budget.type,
            campaignType=campaign.type,
            pacingType=budget.pacingType,
            accountId=account_id,
            advertiserIds=advertiser_ids,
            billingInsertionOrder=campaign.primaryAccount.billingInfo.ioNumber,
            billingPurchaseOrder=campaign.primaryAccount.billingInfo.poNumber,
            billingAdditionalDetails=billing_details,
            billingContactId=contact_id,
            billingAddressId=address_numeric_id,
            isArchived=campaign.isArchived
        )

    async def _patch_campaign(
            self,
            internal_campaign_id: str,
            patch_request: CampaignPatchRequest,
            existing_campaign: Campaign = None) -> bool:
        """Patch an existing campaign with the provided request"""
        try:
            if existing_campaign:
                # Build patch payload for an existing campaign update
                patch_payload = self.campaign_factory.build_campaign(patch_request, 'UPDATE')
            else:
                # Determine Koddi advertiser ID based on agency status
                koddi_advertiser_id = await self.advertiser_service.get_koddi_advertiser_multi_brand(
                    patch_request.brandIds,
                    patch_request.agencyId
                )

                # Build patch payload for campaign creation
                patch_payload = self.campaign_factory.build_campaign(
                    patch_request,
                    'CREATE',
                    koddi_advertiser_id=koddi_advertiser_id
                )

            # Apply the patch to the campaign via the gateway
            result = await self.campaign_gateway.patch_campaign(internal_campaign_id, patch_payload)
            return result
        except ValueError as ex:
            # Log and raise an exception for invalid values
            logger.error('Invalid value: %s', ex)
            raise HTTPException(status_code=500, detail='Unable to complete request. Try again later.') from ex

    async def get_campaigns_paginated_by_external_advertiser(
            self,
            advertiser: CachedAdvertiser,
            campaign_type: InternalCampaignType,
            offset: int,
            size: int
    ) -> ListResponse[Campaign]:
        """Retrieve a paginated list of campaigns for an advertiser"""
        # Search for campaigns using the campaign gateway
        response = await self.campaign_gateway.search_campaigns(CampaignSearchRequest(
            brandIDs=[advertiser.brandId],
            campaignType=[campaign_type],
            page_offset=offset,
            page_size=size,
        ))

        # Generate a list of Campaign objects
        campaigns = [await self._generate_campaign(campaign) for campaign in response.data]

        # Return the paginated response
        return ListResponse[Campaign](
            data=campaigns,
            meta=Meta(page=Page(offset=response.meta.page.offset,
                                size=response.meta.page.size,
                                hasMore=response.meta.page.hasMore)))

    async def update_campaign(self, campaign_id, campaign_request, current_user, source):
        """Update an existing campaign"""
        logger.info('Updating campaign')

        # Fetch current campaign details
        campaign_response = await self.get_campaign_single_response_by_id(campaign_id)
        campaign = campaign_response.data
        internal_campaign_id = await self.lookup_service.get_campaign_long_id_by_short_id(campaign_id)

        # Handle pause or unpause requests if present
        if contains_pause_or_unpause_request(campaign, campaign_request):
            return await self._handle_pause_request(campaign_id, internal_campaign_id, campaign, campaign_request)

        # Validate user permissions for the campaign's advertisers
        await validate_advertisers(current_user, campaign.advertiserIds, self.advertiser_service)

        # Use current status if not specified in the request
        if campaign_request.status is None:
            campaign_request.status = campaign.status

        # Determine campaign dates and budget type
        start_date = determine_start_date(campaign, campaign_request)
        budget_type = determine_budget_type(campaign, campaign_request)
        end_date = determine_end_date(campaign_request)

        query_body = ActivationsQueryBody(campaign_ids=[internal_campaign_id])
        activations = await self.activation_gateway.get_activations(query_body)
        ad_groups_info = await asyncio.gather(*[
            self.ad_group_translation.ad_group_from_activation(activation)
            for activation in activations.data
        ])
        ad_groups: list[AdGroupV2] = [ad_group.adGroup for ad_group in ad_groups_info]

        # Validate end date against ad groups
        await self.validator.validate_dates_with_ad_groups(ad_groups, campaign, end_date, start_date)

        # Adjust budget type for lifetime budgets
        if campaign_request.budgetType == BudgetType.LIFETIME:
            budget_type = InternalBudgetType.CUSTOM

        # Fetch account and advertiser information
        account_id = await self.lookup_service.get_account_long_id_by_short_id(campaign.accountId)
        advertisers = await self.advertiser_service.get_advertisers_by_numeric_ids(campaign.advertiserIds)

        # Process contact and address details
        contact_list, billing_contact = await self._process_contacts(campaign)
        address_list, address = await self._process_addresses(campaign, account_id)
        internal_contacts = await self.contact_service.get_internal_default_contacts(account_id)

        # Determine agency billing status and ID
        is_agency_billed, agency_id = await self._process_agency_info(
            current_user,
            address,
            billing_contact,
            account_id
        )

        # Check if the campaign is always-on (no end date)
        is_always_on = campaign_request.endDate is None

        # Monitor the update request for logging or analytics
        CampaignUpdateRequestMonitor.monitor_request(
            request=campaign_request,
            existing_entity=campaign,
            account_id=campaign.accountId,
            campaign_id=campaign_id
        )

        # Process any changes to billing information
        billing_info = process_billing_info(campaign, campaign_request)

        # Construct the patch payload for the campaign update
        payload = CampaignTranslation.build_patch_payload(campaign=campaign, campaign_request=campaign_request,
            source=source, campaign_id=campaign_id, is_always_on=is_always_on, advertisers=advertisers,
            contact_list=contact_list, internal_contacts=internal_contacts, address_list=address_list,
            account_id=account_id, is_agency_billed=is_agency_billed, budget_type=budget_type, start_date=start_date,
            end_date=end_date, billing_info=billing_info)

        # Perform the campaign update
        success = await self._update_campaign(
            internal_campaign_id=internal_campaign_id,
            patch_request=payload,
            existing_campaign=campaign,
            current_user=current_user
        )

        # Handle campaign activation if update successful and conditions met
        await self._handle_activation(success, campaign_request, internal_campaign_id)

        # Return the updated campaign
        return await self.get_campaign_single_response_by_id(campaign_id)

    async def _process_agency_info(
            self,
            current_user,
            address: AddressReference,
            billing_contact: CachedContact,
            account_id: str
    ):
        """Determine agency billing status and retrieve agency ID"""
        is_agency_billed = False
        agency_id = None

        # Check if the user belongs to an agency
        if current_user['is_agency'] is True:
            agency_id = current_user['works_for']['clientId']

        if agency_id is not None and billing_contact is not None:
            # Verify if the address is an agency address
            if address.type == AdvertiserType.AGENCY:
                logger.info('Agency user selected an agency address')
                # Validate contact for agency-billed campaign
                if await self.contact_service.validate_address_on_agency_involved_campaign(billing_contact, account_id):
                    is_agency_billed = True
                else:
                    raise HTTPException(
                        status_code=400, detail='Billing address belongs to an agency, but the contact does not.')

        return is_agency_billed, agency_id

    async def _process_contacts(self, campaign):
        """Build contact list and retrieve billing contact"""
        contact_list = []
        billing_contact = None

        if campaign.billingContactId is not None:
            # Fetch billing contact details
            billing_contact = await self.lookup_service.get_contact_details_by_short_id(campaign.billingContactId)
            if billing_contact.id:
                billing_contact_id = billing_contact.id
                # Construct contact list with multiple roles
                contact_list = [
                    ContactReference(id=billing_contact_id, type='billing-contact'),
                    ContactReference(id=billing_contact_id, type='creative-contact'),
                    ContactReference(id=billing_contact_id, type='primary-client-contact'),
                ]

        return contact_list, billing_contact

    async def _process_addresses(self, campaign, account_id):
        """Build address list and retrieve billing address"""
        # Fetch corporate address ID
        corporate_address_id = await self.lookup_service.get_address_short_id_by_long_id(account_id)
        # Fetch billing address details
        address = await self.lookup_service.get_address_details_by_short_id(campaign.billingAddressId)

        if address is None:
            raise HTTPException(status_code=400, detail='Failed to provide a valid billing address ID.')
        if corporate_address_id is None:
            # Use billing address ID if corporate address unavailable
            logger.warning('Failed to find a valid corporate address ID, using the provided address ID.')
            corporate_address_id = address.id

        # Construct address list with corporate and alternate addresses
        address_list = [
            AddressReference(id=str(corporate_address_id), type='CORPORATE'),
            AddressReference(id=str(address.id), type='ALTERNATE'),
        ]

        return address_list, AddressReference(id=str(address.id), type=address.addressType)

    async def _has_activations(self, internal_campaign_id: str) -> bool:
        """Check if the campaign has any activations"""
        campaign_response = None
        try:
            response = await self.campaign_gateway.get_campaign(internal_campaign_id=internal_campaign_id)
            campaign_response, _ = CampaignTranslation.get_campaign_and_publish_status_from_response(response)

            if campaign_response is not None and hasattr(campaign_response, 'activations'):
                return len(campaign_response.activations) > 0
            return False
        except TypeError as ex:
            # Log error and raise exception if response malformed
            update_context(logging_extra_context, fetch_campaign_response=campaign_response)
            logger.error('Malformed response from Campaign Service API.')
            raise HTTPException(status_code=500, detail='Error while fetching campaign') from ex

    async def _process_pause_requests(
            self, campaign: Campaign, campaign_id: str, request: CampaignPutRequest) -> CampaignPutRequest:
        """Process pause or unpause requests"""
        if is_pause_requested(campaign, request):
            return await self._pause_or_unpause_campaign(campaign_id, PauseOperationType.PAUSE, request)
        elif is_unpause_requested(campaign, request):
            return await self._pause_or_unpause_campaign(campaign_id, PauseOperationType.UNPAUSE, request)
        return request

    async def _pause_or_unpause_campaign(
            self,
            internal_campaign_id: str,
            operation: PauseOperationType,
            put_request: CampaignPutRequest) -> CampaignPutRequest:
        """Execute pause or unpause operation on the campaign"""
        # Apply pause or unpause operation via gateway
        await self.campaign_gateway.pause_or_unpause_campaign(internal_campaign_id, operation)
        # Remove status from request to avoid conflicts
        request: dict = deepcopy(put_request).model_dump(exclude_none=True, exclude_unset=True)
        request.pop('status')
        return CampaignPutRequest(**request)

    async def _update_campaign(
            self,
            internal_campaign_id: str,
            patch_request: CampaignPatchRequest,
            existing_campaign: Campaign = None,
            current_user: dict = None,
    ) -> bool:
        """Update the campaign with the provided patch request"""
        # Validate multiple brand IDs in the patch request
        validate_multiple_brand_ids(patch_request)
        # Apply the patch to the campaign
        result: bool = await self._patch_campaign(internal_campaign_id, patch_request, existing_campaign)

        # Update ad groups if budget type changes (temporary workaround)
        if existing_campaign and current_user:
            campaign_response = await self.get_campaign_single_response_by_id(
                existing_campaign.id,
                include_ad_groups=True
            )
            updated_campaign = campaign_response.data
            the_updated_campaign: Campaign = updated_campaign

            if the_updated_campaign.budgetType != existing_campaign.budgetType and the_updated_campaign.adGroups:
                for ad_group in the_updated_campaign.adGroups:
                    ad_group_long_id: str = await self.lookup_service.get_adgroup_long_id_by_short_id(ad_group.adGroupId)
                    await self.activation_gateway.update_activation(
                        internal_activation_id=ad_group_long_id,
                        payload=ActivationUpdatePayload(
                            channel_data=ChannelData(budgetType=updated_campaign.budgetType)))
        return result

    async def _handle_activation(self, success, campaign_request, internal_campaign_id):
        """Publish the campaign if conditions are met after a successful update"""
        campaign_has_activations = await self._has_activations(internal_campaign_id)

        # Publish campaign if update successful, not in draft, and has activations
        if success and campaign_request.status not in [CampaignStatus.DRAFT] and campaign_has_activations:
            await self.campaign_gateway.publish_campaign(internal_campaign_id)

    async def _handle_pause_request(self, campaign_id, internal_campaign_id, campaign, campaign_request):
        """Handle pause or unpause request and return updated campaign if no further changes"""
        # Process the pause/unpause request
        campaign_request = await self._process_pause_requests(
            campaign_id=internal_campaign_id,
            campaign=campaign,
            request=campaign_request
        )

        # Fetch updated campaign
        campaign_response = await self.get_campaign_single_response_by_id(campaign_id)
        campaign = campaign_response.data

        # Return response if request implies no additional changes
        if request_implies_no_delta(campaign, campaign_request):
            return campaign_response
        return None

    async def _get_contact_id(self, contacts):
        """Retrieve the numeric contact ID from contact data"""
        contact_internal_id = get_billing_contact_internal_id(contacts)
        if contact_internal_id is None:
            return None
        return await self._get_contact_numeric_id(contact_internal_id)

    async def _get_contact_numeric_id(self, contact_internal_id):
        """Convert internal contact ID to numeric ID"""
        contact_id = await self.lookup_service.get_contact_short_id_by_long_id(contact_internal_id)
        if contact_id is None:
            logger.warning('Contact id not found in cache for contact salesforce id %s', contact_internal_id)
        return contact_id

    async def _get_address_numeric_id(self, addresses, advertiser_type, short_id=None):
        """Retrieve the numeric address ID from address data"""
        address_internal_id = get_address_internal_id(addresses, short_id)
        if address_internal_id is None:
            return None
        return await self._get_or_create_address_numeric_id(address_internal_id, advertiser_type)

    async def _get_or_create_address_numeric_id(self, address_internal_id, advertiser_type):
        """Get or create a numeric address ID from an internal ID"""
        address_numeric_id = await self.lookup_service.get_address_short_id_by_long_id(address_internal_id)
        if address_numeric_id is None:
            # Create new numeric ID if not found in cache
            address_numeric_id = await self.lookup_service.set_address_short_id_by_long_id(address_internal_id)
            await self.lookup_service.set_address_details_by_short_id(address_numeric_id, CachedAddress(**{
                'id': address_internal_id,
                'addressType': advertiser_type.value,
            }))
            logger.warning('Address numeric id not found in cache for id %s , but assigned one', address_internal_id)
        return address_numeric_id

    async def _generate_campaign_response(
            self,
            campaign_response: CASCampaign,
            publish_status: str,
            include_ad_groups: bool = False,
            include_ad_group_errors: bool = False,
            warnings: Warnings = None
    ) -> SingleResponse[Campaign]:
        """Generate a SingleResponse[Campaign] from upstream campaign data"""
        # Generate the Campaign object
        campaign = await self._generate_campaign(campaign_response)
        # Calculate external publication status
        publish_status = self.campaign_gateway.calculate_external_publication_status(
            InternalPublishStatus(publish_status)
        )

        ad_group_errors = []
        ad_group_warnings = []
        if include_ad_groups and hasattr(campaign_response, 'activations') and campaign_response.activations:
            activations_query_body: ActivationsQueryBody = ActivationsQueryBody(ids=campaign_response.activations)
            activations_response = await self.activation_gateway.get_activations(
                query_body=activations_query_body)
            activations_data: List[ActivationResponse] = activations_response.data

            ad_groups_details = {
                item.id: int(item.metadata.short_id) for item in activations_data
            }
            await self.ad_group_translation.cache_ad_groups_by_short_id(ad_groups_details)
            await self.ad_group_translation.cache_ad_groups_by_long_id(ad_groups_details)
            ad_groups_info = [
                await self.ad_group_translation.ad_group_from_activation(activation)
                for activation in activations_data
            ]
            campaign.adGroups = [ad_group_info.adGroup for ad_group_info in ad_groups_info]
            if include_ad_group_errors:
                ad_group_errors = await self.error_translation.errors_from_ad_groups_info(
                    ad_groups_info=ad_groups_info,
                    activations_response=activations_response
                )
                ad_group_warnings = await self.error_translation.warnings_from_ad_groups_info(
                    ad_groups_info=ad_groups_info,
                    activations_response=activations_response
                )
        else:
            campaign.adGroups = []

        response = SingleResponse[Campaign](
            data=campaign,
            meta=EntityMeta(
                publishStatus=publish_status,
                success=True,
                warnings=warnings
            )
        )

        if include_ad_groups and include_ad_group_errors:
            response.errors = ad_group_errors
            response.warnings = ad_group_warnings

        return response

    async def _update_campaign_with_details(self, internal_campaign_id, payload):
        """Update campaign details including contacts and addresses"""
        # Update campaign data
        success_patch = await self._update_campaign(internal_campaign_id, payload)
        # Update associated contacts and addresses
        success_patch_contacts = await self.campaign_gateway.patch_contacts_and_addresses(internal_campaign_id, payload)
        return success_patch and success_patch_contacts

    async def _update_workflow_status(self, internal_campaign_id):
        """Update the workflow status of the campaign"""
        workflow_result = await self.workflow_gateway.set_workflow_campaign_status(
            internal_campaign_id,
            WorkflowActions.CAMPAIGN_CREATE
        )
        if workflow_result is False:
            logger.error('Failed to update campaign workflow')
        logger.info('Workflow Result: %s', workflow_result)

    async def get_campaign_long_id(self, short_campaign_id: int) -> str:
        internal_campaign_id = await self.lookup_service.get_campaign_long_id_by_short_id(short_campaign_id)
        if internal_campaign_id is None:
            campaign_by_short_id = CampaignSearchRequest(
                shortIDs=[f"{short_campaign_id}"],
                page_offset=0,
                page_size=1
            )
            found_campaigns = await self.campaign_gateway.search_campaigns(campaign_by_short_id)
            if not found_campaigns.data:
                raise HTTPException(status_code=404, detail="Campaign not found")
            found_campaign = found_campaigns.data[0]
            internal_campaign_id = found_campaign.id
        return internal_campaign_id
