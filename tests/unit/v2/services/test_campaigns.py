import unittest
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.common.gateways.activation_gateway import ActivationGateway
from app.common.gateways.campaign_service_gateway import CampaignServiceGateway
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.model.redis import CachedContact, CachedAddress
from app.common.services.lookup_service import LookupService
from app.common.view_models import (
    CampaignPutRequest,
    CampaignStatus,
    ListResponse,
    PacingType,
    SingleResponse,
)
from app.common.gateways.workflow_gateway import WorkflowGateway
from app.common.model.advertiser import AdvertiserType, CachedAdvertiser
from app.common.model.contact import InternalContact
from app.common.model.campaign_types import (
    InternalCampaignType,
)
from app.common.model.downstream.campaign_activation_service import (
    AddressReference,
    BillingInfo,
    Budget,
    CASAccount,
    CASCampaign,
    ClickThroughDestination,
    ContactReference,
    ExternalId,
)
from app.common.model.downstream.campaign_service import (
    CampaignResponse,
    CampaignsResponse,
    Meta,
    Page, CampaignSearchRequest,
)
from app.common.model.downstream.workflow import InitializeCampaignResponse
from app.common.model.pause_operation_type import PauseOperationType
from app.common.model.shared import (
    BudgetType,
    CampaignType,
    EntityMeta,
    InternalBudgetType,
    InternalPublishStatus,
    PublishStatus,
)
from app.common.services.contact_service import AdvertiserContactService
from app.v2.model.downstream.activation_service import ActivationResponseV2, ActivationResponse, ActivationMetaData
from app.v2.translations.ad_group_translation import AdGroupTranslation
from app.v2.utils.campaign_translations import CampaignTranslation
from app.v2.services import CampaignService
from app.v2.view_models import Campaign, CampaignPatchRequest, CampaignRequest
from tests.unit.services.constants import CAMPAIGNS_SINGLE_RESPONSE
from tests.unit.v2 import CAMPAIGN_SINGLE_RESPONSE
from tests.utils_for_testing.auto_mock import auto_mock


class TestCampaignService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_account_service = AsyncMock()
        self.mock_advertiser_service = AsyncMock()
        self.mock_address_service = AsyncMock()
        self.mock_contact_service = Mock(spec=AdvertiserContactService)
        self.mock_lookup_service = Mock(spec=LookupService)
        self.mock_campaign_factory = AsyncMock()
        self.mock_campaign_gateway = Mock(spec=CampaignServiceGateway)
        self.mock_workflow_gateway = Mock(spec=WorkflowGateway)
        self.mock_activation_gateway = Mock(spec=ActivationGateway)
        self.mock_ad_group_translation = Mock(spec=AdGroupTranslation)
        self.mock_validator = AsyncMock()

        self.service = CampaignService(
            account_service=self.mock_account_service,
            advertiser_service=self.mock_advertiser_service,
            address_service=self.mock_address_service,
            contact_service=self.mock_contact_service,
            lookup_service=self.mock_lookup_service,
            campaign_factory=self.mock_campaign_factory,
            campaign_gateway=self.mock_campaign_gateway,
            workflow_gateway=self.mock_workflow_gateway,
            activation_gateway=self.mock_activation_gateway,
            ad_group_translation=self.mock_ad_group_translation,
            validator=self.mock_validator
        )

    @pytest.mark.asyncio
    async def test_create_campaign__valid_data__should_return_single_response(self):
        campaign_request = CampaignRequest(
            name='Test Campaign',
            status=CampaignStatus.DRAFT,
            budgetAmount=1000.0,
            budgetType=BudgetType.DAILY,
            pacingType=PacingType.EVEN,
            startDate=datetime.now().strftime('%Y-%m-%d'),
            advertiserIds=[1],
            accountId=1,
            billingInsertionOrder='IO-001',
            billingContactId=1,
            billingAddressId=1,
            campaignType=CampaignType.PLA
        )
        current_user = {
            'username': 'test_user',
            'is_agency': True,
            'works_for': {'clientId': 'agency-123'},
        }

        self.service.validator.validate_account_and_advertisers = AsyncMock()
        self.mock_lookup_service.get_account_long_id_by_short_id.return_value = 'acct-1'
        self.service.advertiser_service.get_advertisers_by_numeric_ids.return_value = [CachedAdvertiser(
            id=1,
            brandId='0a849f1f-f866-4cfe-ad2a-f48f8daf9de2',
            name='advertiser_name',
            accountId=1,
            description='advertiser_description',
            active=True
        )]
        self.mock_lookup_service.get_address_details_by_short_id.return_value = CachedAddress(**{"id": "1", "addressType": "AGENCY"})
        self.mock_lookup_service.get_contact_details_by_short_id.return_value = CachedContact(**{"id": "1", "contactType": "CPG"})
        self.mock_contact_service.get_internal_default_contacts.return_value = \
            [InternalContact(type='ACCOUNT_EXECUTIVE', id='1')]
        self.service.validator.validate_billing_info.return_value = {
            'billing_contact_id': "1",
            'corporate_address_id': "2",
            'billing_address_id': "1",
            'is_agency_billed': True,
        }

        mock_campaign = MagicMock()
        mock_campaign.id = 'internal-123'
        mock_campaign.shortId = '321'
        self.service._start_campaign = AsyncMock(return_value=mock_campaign)
        self.service._update_campaign_with_details = AsyncMock(return_value=True)
        self.service.get_campaign_single_response_by_id = AsyncMock(return_value='response')

        result = await self.service.create_campaign(campaign_request, current_user, source='test')
        self.assertEqual(result, 'response')

    @pytest.mark.asyncio
    async def test_start_campaign__missing_business_key__should_raise_http_exception(self):
        self.service.workflow_gateway.initialize_campaign.return_value = InitializeCampaignResponse(businessKey="")
        with self.assertRaises(Exception) as context:
            await self.service._start_campaign(InternalCampaignType.PLA)

        self.assertEqual(str(context.exception.detail), 'Backend service unavailable')

    @pytest.mark.asyncio
    async def test_get_campaign_by_id__should_return_campaign_and_publish_status(self):
        mock_campaign = Campaign(id=1, accountId=1, advertiserIds=[])
        self.mock_lookup_service.get_campaign_long_id_by_short_id.return_value = 'internal-id'
        self.mock_campaign_gateway.get_campaign.return_value = CampaignResponse(**{'mock': 'response'})
        self.service._generate_campaign_response = AsyncMock(return_value=SingleResponse[Campaign](
            data=mock_campaign,
            meta=EntityMeta(publishStatus=PublishStatus.PUBLISHED, success=True)
        ))

        campaign_response = await self.service.get_campaign_single_response_by_id(campaign_id=1)

        self.assertEqual(campaign_response.data, mock_campaign)
        self.assertEqual(campaign_response.meta.publishStatus, PublishStatus.PUBLISHED)

    @pytest.mark.asyncio
    async def test_process_addresses__should_return_address_list(self):
        self.mock_lookup_service.get_address_short_id_by_long_id.return_value = 10
        self.mock_lookup_service.get_address_details_by_short_id.return_value = CachedAddress(**{"id": "20", "addressType": "AGENCY"})

        result = await self.service._process_addresses(
            campaign=MagicMock(billingAddressId=20),
            account_id=123
        )

        expected = ([AddressReference(id="10", type='CORPORATE'), AddressReference(id="20", type='ALTERNATE')],
                    AddressReference(id="20", type='AGENCY'))

        self.assertEqual(result, expected)

    @pytest.mark.asyncio
    async def test_process_addresses__missing_billing_address__should_raise_http_exception(self):
        self.mock_lookup_service.get_address_details_by_short_id.return_value = None

        with self.assertRaises(Exception) as context:
            await self.service._process_addresses(
                campaign=MagicMock(billingAddressId=999),
                account_id=123
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, 'Failed to provide a valid billing address ID.')

    @pytest.mark.asyncio
    async def test_update_campaign__pause_or_unpause__should_process_and_return(self):
        mock_campaign = Campaign(id=100, accountId=1, advertiserIds=[], status=CampaignStatus.DRAFT)

        campaign_request = CampaignPutRequest(name='Test Campaign',
                                              status=CampaignStatus.PAUSED,
                                              budgetAmount=1000.0,
                                              budgetType=BudgetType.DAILY,
                                              pacingType=PacingType.EVEN,
                                              startDate='2021-01-01',
                                              billingInsertionOrder=None,
                                              billingPurchaseOrder=None)
        mock_response = SingleResponse[Campaign](
            data=mock_campaign,
            meta=EntityMeta(publishStatus=PublishStatus.PUBLISHED, success=True)
        )
        self.service.get_campaign_single_response_by_id = AsyncMock(return_value=mock_response)
        self.mock_lookup_service.get_campaign_long_id_by_short_id.return_value = 'internal-100'
        self.mock_contact_service.get_internal_default_contacts.return_value = []
        self.mock_lookup_service.get_account_long_id_by_short_id.return_value = 'Test Account'
        self.mock_lookup_service.get_contact_details_by_short_id.return_value = CachedContact(**{"id": "1"})
        self.mock_lookup_service.get_address_details_by_short_id.return_value = CachedAddress(**{"id": "1", "addressType": "AGENCY"})

        self.service._process_pause_requests = AsyncMock(return_value=campaign_request)
        self.service._has_activations = AsyncMock(return_value=False)
        self.mock_campaign_factory.build_campaign = MagicMock()

        result = await self.service.update_campaign(
            campaign_id=100,
            campaign_request=campaign_request,
            current_user={
                'username': 'test_user',
                'internal': True,
                'is_agency': True,
                'works_for': {'clientId': 'agency-123'},
            },
            source='test'
        )

        self.assertEqual(result, mock_response)

    @pytest.mark.asyncio
    async def test_process_agency_info__invalid_contact_for_agency_address__should_raise(self):
        self.mock_contact_service.validate_address_on_agency_involved_campaign.return_value = False
        address = AddressReference(id="123", type=AdvertiserType.AGENCY)
        billing_contact = CachedContact(id="1", contactType=AdvertiserType.CPG)
        current_user = {
            'is_agency': True,
            'works_for': {'clientId': 'agency-123'}
        }

        with self.assertRaises(HTTPException) as context:
            await self.service._process_agency_info(current_user, address, billing_contact, account_id="1")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, 'Billing address belongs to an agency, but the contact does not.')

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    async def test__update_campaign__with_multiple_brand_ids__should_raise(
            self,
            mock_is_harness_flag_on: MagicMock):
        patch_request = MagicMock()
        patch_request.brandIds = ['brand1', 'brand2']

        current_user = {'username': 'test_user'}

        self.service._patch_campaign = AsyncMock()

        with self.assertRaises(HTTPException) as context:
            result = await self.service._update_campaign(
                internal_campaign_id='abc123',
                patch_request=patch_request,
                current_user=current_user,
            )

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual("Multi-brand campaigns are not yet supported", context.exception.detail)

        self.service._patch_campaign.assert_not_awaited()
        mock_is_harness_flag_on.assert_called_once_with(
            HarnessFeatureFlags.DISABLE_MULTIPLE_BRAND_IDS, 'default')

    @pytest.mark.asyncio
    async def test__generate_campaign_response__with_ad_groups__should_attach_ad_groups(self):
        campaign_response = CASCampaign(
            shortId='123',
            activations=['a1'],
            primaryAccount=CASAccount(
                id='1',
                brands=[],
                billingInfo=None,
                contacts=[],
                addresses=[],
                isAgencyBeingInvolved=False
            ),
            status='ACTIVE'
        )
        mock_activation_response = MagicMock(spec=ActivationResponse)
        mock_activation_response.id = "938983746382234"
        mock_activation_response.metadata = MagicMock(ActivationMetaData)
        mock_activation_response.metadata.short_id = "456"
        mock_ad_group = MagicMock()
        self.service._generate_campaign = AsyncMock(return_value=Campaign(id=1, accountId=1, advertiserIds=[]))
        self.mock_activation_gateway.get_activations = AsyncMock(
            return_value=ActivationResponseV2[List[ActivationResponse]](
                data=[mock_activation_response]
            ))
        self.mock_ad_group_translation.ad_group_from_activation.return_value = MagicMock(adGroup=mock_ad_group)
        self.mock_campaign_gateway.calculate_external_publication_status.return_value = PublishStatus.PUBLISHED

        campaign_response = await self.service._generate_campaign_response(
            campaign_response, InternalPublishStatus.IN_PROGRESS, include_ad_groups=True)

        self.assertEqual(campaign_response.data.adGroups, [mock_ad_group])
        self.assertEqual(campaign_response.meta.publishStatus, PublishStatus.PUBLISHED)

    @pytest.mark.asyncio
    async def test_get_campaigns_paginated_by_external_advertiser__should_filter_and_paginate(self):
        advertiser = CachedAdvertiser(
            brandId='1',
            name='Test Advertiser',
            accountId=1,
            description='Test Description',
            active=True
        )
        campaign_type = InternalCampaignType.PLA
        mock_campaign = CASCampaign(
            id='123abc',
            goalID='goal123',
            shortId='789',
            created='2023-10-01T12:00:00Z',
            createdBy='0001-22-3-asdf-asdf',
            createdByUser='Test User',
            lastModified='2023-10-02T12:00:00Z',
            lastModifiedBy='0001-22-3-asdf-asdf',
            lastModifiedByClientID='client-123',
            lastModifiedByUser='Test User',
            startDate='2023-10-01T00:00:00Z',
            endDate='2023-12-31T23:59:59Z',
            backgroundInformation='Test background information',
            isAlwaysOn=True,
            primaryAccount=CASAccount(
                id='123',
                brands=['1', '2'],
                billingInfo=BillingInfo(
                    ioNumber='1',
                    poNumber='2',
                ),
                addresses=None,
                contacts=None,
                isAgencyBeingInvolved=False,
                agency=None
            ),
            partnerAccounts=[
                CASAccount(
                    id='partner-456',
                    brands=['3'],
                    billingInfo=None,
                    addresses=None,
                    contacts=None,
                    isAgencyBeingInvolved=True,
                    agency={'id': 'agency-789', 'billingInfo': None}
                )
            ],
            name='Test Campaign',
            budget=Budget(
                amount=10000.0,
                type='CPC',
                pacingType='STANDARD'
            ),
            additionalBillingDetails='Test billing details',
            notesForAccounting='Test notes',
            activations=['activation1', 'activation2'],
            type='PLA',
            source='SOURCE_A',
            status='ACTIVE',
            externalIDs=[ExternalId(id=456, partner='Test Partner')],
            internalContacts=[ContactReference(id='contact-123', type='ACCOUNT_EXECUTIVE')],
            clickThroughDestinations=[
                ClickThroughDestination(
                    id='destination-123',
                    bannerizedURL='http://example.com',
                    name='Test Destination',
                    divisions=[{
                        'clickThroughUrl': 'http://example.com/division1',
                        'name': 'Division 1'
                    }]
                )
            ],
            version=1,
            publishingStatus='PUBLISHED'
        )
        mock_campaign_response = CampaignsResponse(data=[mock_campaign] * 5, meta=Meta(page=Page(hasMore=True, size=5, offset=0)))
        self.mock_campaign_gateway.search_campaigns.return_value = mock_campaign_response

        result: ListResponse = await self.service.get_campaigns_paginated_by_external_advertiser(
            advertiser=advertiser,
            campaign_type=campaign_type,
            offset=0,
            size=5
        )

        self.assertEqual(len(result.data), 5)
        self.assertTrue(result.meta.page.hasMore)

    @pytest.mark.asyncio
    @patch('app.v2.services.campaign.get_address_internal_id', return_value='internal-id')
    async def test__get_address_numeric_id__should_return_existing_id(self, mock_get_address_internal_id: MagicMock):
        addresses = [AddressReference(id='internal-id')]
        advertiser_type = AdvertiserType.AGENCY

        self.service._get_or_create_address_numeric_id = AsyncMock(return_value=42)

        numeric_id = await self.service._get_address_numeric_id(addresses, advertiser_type)

        mock_get_address_internal_id.assert_called_once()
        self.assertEqual(numeric_id, 42)

    @pytest.mark.asyncio
    async def test__get_address_numeric_id__none_internal__returns_none(self):
        # Arrange: no internal ID found
        addresses = []
        self.mock_lookup_service.get_address_short_id_by_long_id.return_value = None
        # call under test
        result = await self.service._get_address_numeric_id(addresses, advertiser_type=MagicMock(), short_id=123)
        self.assertIsNone(result)

    @pytest.mark.asyncio
    async def test__get_address_numeric_id__cache_hit__returns_numeric(self):
        addresses = [AddressReference(id='long-1')]
        self.mock_lookup_service.get_address_short_id_by_long_id.return_value = 77

        result = await self.service._get_address_numeric_id(addresses, advertiser_type=MagicMock(), short_id=None)
        self.assertEqual(result, 77)
        self.mock_lookup_service.set_address_short_id_by_long_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test__get_address_numeric_id__cache_miss__creates_and_returns(self):
        addresses = [AddressReference(id='long-2')]
        self.mock_lookup_service.get_address_short_id_by_long_id.return_value = None
        self.mock_lookup_service.set_address_short_id_by_long_id.return_value = 88

        result = await self.service._get_address_numeric_id(addresses, advertiser_type=MagicMock(value="AGENCY"),
                                                            short_id=None)
        self.assertEqual(result, 88)
        self.mock_lookup_service.set_address_short_id_by_long_id.assert_awaited_once_with("long-2")
        self.mock_lookup_service.set_address_details_by_short_id.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('app.v2.services.campaign.request_implies_no_delta', return_value=True)
    async def test__handle_pause_request__should_return_campaign_if_no_delta(self, mock_request_implies_no_delta: MagicMock):
        campaign = MagicMock()
        request = MagicMock()

        self.service._process_pause_requests = AsyncMock(return_value=request)
        self.service.get_campaign_single_response_by_id = AsyncMock(return_value=MagicMock(data=CAMPAIGN_SINGLE_RESPONSE))

        result = await self.service._handle_pause_request('cid', 'internal_id', campaign, request)

        mock_request_implies_no_delta.assert_called_once()
        self.assertEqual(result.data, CAMPAIGN_SINGLE_RESPONSE)

    @pytest.mark.asyncio
    @patch('app.v2.services.campaign.request_implies_no_delta', return_value=False)
    async def test__handle_pause_request__with_delta__returns_none(self, mock_request_implies_no_delta: MagicMock):
        campaign = MagicMock()
        request = MagicMock()

        self.service._process_pause_requests = AsyncMock(return_value=request)
        self.service.get_campaign_single_response_by_id = AsyncMock(
            return_value=MagicMock(data=CAMPAIGN_SINGLE_RESPONSE))

        result = await self.service._handle_pause_request('cid', 'internal_id', campaign, request)

        mock_request_implies_no_delta.assert_called_once()
        self.assertIsNone(result)

    @pytest.mark.asyncio
    async def test_create_campaign__http_exception__should_propagate(self):
        # Arrange
        campaign_request = CampaignRequest(
            name="Test Campaign",
            status=CampaignStatus.DRAFT,
            budgetAmount=1000.0,
            budgetType=BudgetType.DAILY,
            pacingType=PacingType.EVEN,
            startDate="2025-01-01",
            advertiserIds=[1],
            accountId=1,
            billingInsertionOrder="IO-001",
            billingContactId=1,
            billingAddressId=1,
            campaignType="PLA"
        )
        current_user = {"username": "test_user"}
        self.service.validator.validate_account_and_advertisers.side_effect = HTTPException(status_code=400, detail="Invalid request")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await self.service.create_campaign(campaign_request, current_user, source="test")
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid request")

    @pytest.mark.asyncio
    @patch("app.v2.services.campaign.logger.error")
    async def test_create_campaign__unexpected_exception__should_log_and_raise_http_exception(self, mock_logger_error):
        # Arrange
        campaign_request = CampaignRequest(
            name="Test Campaign",
            status=CampaignStatus.DRAFT,
            budgetAmount=1000.0,
            budgetType=BudgetType.DAILY,
            pacingType=PacingType.EVEN,
            startDate="2025-01-01",
            advertiserIds=[1],
            accountId=1,
            billingInsertionOrder="IO-001",
            billingContactId=1,
            billingAddressId=1,
            campaignType="PLA"
        )
        current_user = {"username": "test_user"}
        self.service.validator.validate_account_and_advertisers.side_effect = Exception("Unexpected error")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await self.service.create_campaign(campaign_request, current_user, source="test")
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Failed to create campaign due to an internal error")
        mock_logger_error.assert_called_once_with("Unexpected error creating campaign: Unexpected error")

    async def test_start_campaign__campaign_creation_fails__should_raise_http_exception(self):
        # Lines 319-322
        self.mock_workflow_gateway.initialize_campaign.return_value = MagicMock(businessKey="business-key")
        self.mock_campaign_gateway.get_campaign.return_value = CampaignResponse(
            unpublishedChanges=None,
            publishedChanges=None,
        )

        with self.assertRaises(HTTPException) as context:
            await self.service._start_campaign(InternalCampaignType.PLA)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Campaign failed to create")

    async def test_process_contacts__no_billing_contact__should_return_empty_list(self):
        # Line 367
        campaign = MagicMock(billingContactId=None)

        contact_list, billing_contact = await self.service._process_contacts(campaign)

        self.assertEqual(contact_list, [])
        self.assertIsNone(billing_contact)

    async def test_update_campaign__should_update_ad_groups(self):
        # Line 444
        patch_request = MagicMock()
        campaign = MagicMock(budgetType=BudgetType.DAILY)
        campaign.adGroups = [MagicMock(adGroupId=1)]
        current_user = {"username": "test_user"}

        existing_campaign = MagicMock(budgetType=BudgetType.WEEKLY)

        self.service._patch_campaign = AsyncMock(return_value=True)
        self.service.get_campaign_single_response_by_id = AsyncMock(return_value=MagicMock(data=campaign))

        result = await self.service._update_campaign(
            internal_campaign_id="abc123",
            patch_request=patch_request,
            existing_campaign=existing_campaign,
            current_user=current_user,
        )

        self.assertTrue(result)
        self.mock_activation_gateway.update_activation.assert_awaited_once()

    async def test_update_campaign_with_details__should_return_success(self):
        # Lines 458-463
        self.service._update_campaign = AsyncMock(return_value=True)
        self.mock_campaign_gateway.patch_contacts_and_addresses = AsyncMock(return_value=True)
        payload = MagicMock()
        result = await self.service._update_campaign_with_details("internal-id", payload)

        self.assertTrue(result)
        self.service._update_campaign.assert_called_once_with("internal-id", payload)
        self.mock_campaign_gateway.patch_contacts_and_addresses.assert_called_once_with("internal-id", payload)

    @patch("app.v2.services.campaign.logger.error")
    async def test_update_workflow_status__failure__should_log_error(self, mock_logger_error):
        # Lines 496-504
        self.mock_workflow_gateway.set_workflow_campaign_status.return_value = False

        await self.service._update_workflow_status("internal-campaign-id")

        mock_logger_error.assert_called_once_with("Failed to update campaign workflow")

    async def test_update_workflow_status__success__should_log_info(self):
        # Lines 509-513
        self.mock_workflow_gateway.set_workflow_campaign_status.return_value = True

        with patch("app.v2.services.campaign.logger.info") as mock_logger_info:
            await self.service._update_workflow_status("internal-campaign-id")

            mock_logger_info.assert_called_once_with("Workflow Result: %s", True)

    async def test_handle_activation__should_publish_campaign(self):
        # Lines 522-526
        self.service._has_activations = AsyncMock(return_value=True)
        self.mock_campaign_gateway.publish_campaign = AsyncMock()

        await self.service._handle_activation(
            success=True,
            campaign_request=MagicMock(status=CampaignStatus.ACTIVE),
            internal_campaign_id="internal-campaign-id",
        )

        self.mock_campaign_gateway.publish_campaign.assert_called_once_with("internal-campaign-id")

    async def test_handle_activation__should_not_publish_campaign(self):
        # Line 563
        self.service._has_activations = AsyncMock(return_value=False)
        self.mock_campaign_gateway.publish_campaign = AsyncMock()

        await self.service._handle_activation(
            success=True,
            campaign_request=MagicMock(status=CampaignStatus.ACTIVE),
            internal_campaign_id="internal-campaign-id",
        )

        self.mock_campaign_gateway.publish_campaign.assert_not_awaited()

    async def test_process_pause_requests__should_return_original_request(self):
        # Lines 588-591
        self.service._pause_or_unpause_campaign = MagicMock()

        result = await self.service._process_pause_requests(
            campaign=MagicMock(),
            campaign_id="campaign-id",
            request=MagicMock(),
        )

        self.assertIsNotNone(result)
        self.service._pause_or_unpause_campaign.assert_not_called()

    async def test_get_address_numeric_id__should_return_none_if_no_internal_id(self):
        # Lines 630-632
        self.mock_lookup_service.get_address_short_id_by_long_id.return_value = None

        result = await self.service._get_address_numeric_id([], advertiser_type=MagicMock(), short_id=123)

        self.assertIsNone(result)

    async def test_get_address_numeric_id__should_return_cached_id(self):
        # Lines 646-647
        self.mock_lookup_service.get_address_short_id_by_long_id.return_value = 77

        result = await self.service._get_address_numeric_id(
            [MagicMock(id="long-id")], advertiser_type=MagicMock(), short_id=None
        )

        self.assertEqual(result, 77)

    async def test_get_or_create_address_numeric_id__should_create_and_return_id(self):
        # Lines 659-662
        self.mock_lookup_service.get_address_short_id_by_long_id.return_value = None
        self.mock_lookup_service.set_address_short_id_by_long_id.return_value = 88

        result = await self.service._get_or_create_address_numeric_id("long-id", advertiser_type=MagicMock(value="CPG"))

        self.assertEqual(result, 88)
        self.mock_lookup_service.set_address_short_id_by_long_id.assert_awaited_once_with("long-id")
        self.mock_lookup_service.set_address_details_by_short_id.assert_awaited_once()

    @patch("app.v2.services.campaign.logger.error")
    async def test_create_campaign__unexpected_exception__should_log_and_raise_http_exception_missed(self, mock_logger_error):
        campaign_request = MagicMock()
        current_user = {"username": "test_user"}
        self.service.validator.validate_account_and_advertisers.side_effect = Exception("Unexpected error")

        with self.assertRaises(HTTPException) as context:
            await self.service.create_campaign(campaign_request, current_user, source="test")

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Failed to create campaign due to an internal error")
        mock_logger_error.assert_called_once_with("Unexpected error creating campaign: Unexpected error")

    async def test_start_campaign__missing_business_key__should_raise_http_exception_missed(self):
        self.mock_workflow_gateway.initialize_campaign.return_value = MagicMock(businessKey=None)

        with self.assertRaises(HTTPException) as context:
            await self.service._start_campaign(InternalCampaignType.PLA)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Backend service unavailable")

    async def test_start_campaign__campaign_creation_fails__should_raise_http_exception_missed(self):
        self.mock_workflow_gateway.initialize_campaign.return_value = MagicMock(businessKey="business-key")
        self.mock_campaign_gateway.get_campaign.return_value = CampaignResponse(
            unpublishedChanges=None,
            publishedChanges=None,
        )

        with self.assertRaises(HTTPException) as context:
            await self.service._start_campaign(InternalCampaignType.PLA)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Campaign failed to create")

    async def test_process_addresses__missing_billing_address__should_raise_http_exception_missed(self):
        self.mock_lookup_service.get_address_details_by_short_id.return_value = None

        with self.assertRaises(HTTPException) as context:
            await self.service._process_addresses(
                campaign=MagicMock(billingAddressId=999),
                account_id=123
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Failed to provide a valid billing address ID.")

    @patch("app.v2.services.campaign.logger.error")
    async def test_patch_campaign__existing_campaign__should_patch_successfully(self, mock_logger_error):
        # Arrange
        internal_campaign_id = "internal-123"
        patch_request = CampaignPatchRequest(
            source="API_PARTNER__UNRECOGNIZED_CONSUMER",
            campaignId=1,
            backgroundInfo="API Campaign ID: 1",
            budgetAmount=1000.0,
            pacingType=PacingType.EVEN,
            budgetType=InternalBudgetType.DAILY,
            isAlwaysOn=False,
            name="Updated Campaign",
            brandIds=[],
            isPoRequired=False,
            billingPurchaseOrder="111",
            additionalBillingDetails="",
            contactList=[
                {"id": "0n3c0n74c71d", "type": "billing-contact"},
                {"id": "0n3c0n74c71d", "type": "creative-contact"},
                {"id": "0n3c0n74c71d", "type": "primary-client-contact"},
            ],
            internalContactList=[InternalContact(type="ACCOUNT_EXECUTIVE", id="1")],
            addressList=[{"id": 1, "type": "CORPORATE"}, {"id": 1, "type": "ALTERNATE"}],
            accountId="3b5c15a3-008e-4591-82be-26e06b913733",
            startDate=datetime.now(),
            endDate=datetime.now(),
            status=CampaignStatus.ACTIVE,
            isAgencyBilled=True,
        )
        existing_campaign = Campaign(id=123, name="Existing Campaign", accountId=1, advertiserIds=[1])

        self.mock_campaign_factory.build_campaign = MagicMock(return_value = {"name": "Updated Campaign"})
        self.mock_campaign_gateway.patch_campaign = AsyncMock(return_value = True)

        # Act
        result = await self.service._patch_campaign(internal_campaign_id, patch_request, existing_campaign)

        # Assert
        self.assertTrue(result)
        self.mock_campaign_factory.build_campaign.assert_called_once_with(patch_request, "UPDATE")
        self.mock_campaign_gateway.patch_campaign.assert_called_once_with(internal_campaign_id, {"name": "Updated Campaign"})
        mock_logger_error.assert_not_called()

    @patch("app.v2.services.campaign.logger.error")
    async def test_patch_campaign__new_campaign__should_patch_successfully(self, mock_logger_error):
        # Arrange
        internal_campaign_id = "internal-123"
        patch_request = CampaignPatchRequest(
            source="API_PARTNER__UNRECOGNIZED_CONSUMER",
            campaignId=1,
            backgroundInfo="API Campaign ID: 1",
            budgetAmount=1000.0,
            pacingType=PacingType.EVEN,
            budgetType=InternalBudgetType.DAILY,
            isAlwaysOn=False,
            name="New Campaign",
            brandIds=["brand-1"],
            isPoRequired=False,
            billingPurchaseOrder="111",
            additionalBillingDetails="",
            contactList=[
                {"id": "0n3c0n74c71d", "type": "billing-contact"},
                {"id": "0n3c0n74c71d", "type": "creative-contact"},
                {"id": "0n3c0n74c71d", "type": "primary-client-contact"},
            ],
            internalContactList=[InternalContact(type="ACCOUNT_EXECUTIVE", id="1")],
            addressList=[{"id": 1, "type": "CORPORATE"}, {"id": 1, "type": "ALTERNATE"}],
            accountId="3b5c15a3-008e-4591-82be-26e06b913733",
            startDate=datetime.now(),
            endDate=datetime.now(),
            status=CampaignStatus.ACTIVE,
            isAgencyBilled=True,
        )

        self.mock_advertiser_service.get_koddi_advertiser_multi_brand = AsyncMock(return_value = "koddi-123")
        self.mock_campaign_factory.build_campaign =  MagicMock(return_value = {"name": "New Campaign", "koddiAdvertiserId": "koddi-123"})
        self.mock_campaign_gateway.patch_campaign =  AsyncMock(return_value = True)

        # Act
        result = await self.service._patch_campaign(internal_campaign_id, patch_request)

        # Assert
        self.assertTrue(result)
        self.mock_advertiser_service.get_koddi_advertiser_multi_brand.assert_called_once_with(["brand-1"], None)
        self.mock_campaign_factory.build_campaign.assert_called_once_with(
            patch_request, "CREATE", koddi_advertiser_id="koddi-123"
        )
        self.mock_campaign_gateway.patch_campaign.assert_called_once_with(
            internal_campaign_id, {"name": "New Campaign", "koddiAdvertiserId": "koddi-123"}
        )
        mock_logger_error.assert_not_called()

    @patch("app.v2.services.campaign.logger.error")
    async def test_patch_campaign__new_campaign_with_agency__should_patch_successfully(
        self, mock_logger_error
    ):
        # Arrange
        internal_campaign_id = "internal-123"
        patch_request = CampaignPatchRequest(
            source="API_PARTNER__UNRECOGNIZED_CONSUMER",
            campaignId=1,
            backgroundInfo="API Campaign ID: 1",
            budgetAmount=1000.0,
            pacingType=PacingType.EVEN,
            budgetType=InternalBudgetType.DAILY,
            isAlwaysOn=False,
            name="Test Campaign",
            brandIds=["brand-1"],
            isPoRequired=False,
            billingPurchaseOrder="111",
            additionalBillingDetails="",
            contactList=[
                {"id": "0n3c0n74c71d", "type": "billing-contact"},
                {"id": "0n3c0n74c71d", "type": "creative-contact"},
                {"id": "0n3c0n74c71d", "type": "primary-client-contact"},
            ],
            internalContactList=[InternalContact(type="ACCOUNT_EXECUTIVE", id="1")],
            addressList=[{"id": 1, "type": "CORPORATE"}, {"id": 1, "type": "ALTERNATE"}],
            accountId="3b5c15a3-008e-4591-82be-26e06b913733",
            startDate=datetime.now(),
            endDate=datetime.now(),
            status=CampaignStatus.ACTIVE,
            isAgencyBilled=True,
            agencyId="agency-123",
        )

        self.mock_advertiser_service.get_koddi_advertiser_multi_brand = AsyncMock(
            return_value="koddi-456"
        )
        self.mock_campaign_factory.build_campaign = MagicMock(
            return_value={"name": "New Campaign", "koddiAdvertiserId": "koddi-456"}
        )
        self.mock_campaign_gateway.patch_campaign = AsyncMock(return_value=True)

        # Act
        result = await self.service._patch_campaign(internal_campaign_id, patch_request)

        # Assert
        self.assertTrue(result)
        self.mock_advertiser_service.get_koddi_advertiser_multi_brand.assert_called_once_with(
            ["brand-1"], "agency-123"
        )
        self.mock_campaign_factory.build_campaign.assert_called_once_with(
            patch_request, "CREATE", koddi_advertiser_id="koddi-456"
        )
        self.mock_campaign_gateway.patch_campaign.assert_called_once_with(
            internal_campaign_id, {"name": "New Campaign", "koddiAdvertiserId": "koddi-456"}
        )
        mock_logger_error.assert_not_called()

    @patch("app.v2.services.campaign.logger.error")
    async def test_patch_campaign__invalid_value__should_raise_http_exception(
        self, mock_logger_error
    ):
        # Arrange
        internal_campaign_id = "internal-123"
        patch_request = CampaignPatchRequest(
            source="API_PARTNER__UNRECOGNIZED_CONSUMER",
            campaignId=1,
            backgroundInfo="API Campaign ID: 1",
            budgetAmount=1000.0,
            pacingType=PacingType.EVEN,
            budgetType=InternalBudgetType.DAILY,
            isAlwaysOn=False,
            name="Updated Campaign",
            brandIds=[],
            isPoRequired=False,
            billingPurchaseOrder="111",
            additionalBillingDetails="",
            contactList=[
                {"id": "0n3c0n74c71d", "type": "billing-contact"},
                {"id": "0n3c0n74c71d", "type": "creative-contact"},
                {"id": "0n3c0n74c71d", "type": "primary-client-contact"},
            ],
            internalContactList=[InternalContact(type="ACCOUNT_EXECUTIVE", id="1")],
            addressList=[{"id": 1, "type": "CORPORATE"}, {"id": 1, "type": "ALTERNATE"}],
            accountId="3b5c15a3-008e-4591-82be-26e06b913733",
            startDate=datetime.now(),
            endDate=datetime.now(),
            status=CampaignStatus.ACTIVE,
            isAgencyBilled=True,
        )
        existing_campaign = Campaign(
            id=123, name="Existing Campaign", accountId=1, advertiserIds=[1]
        )

        value_error = ValueError("Invalid value")
        self.mock_campaign_factory.build_campaign = MagicMock(side_effect=value_error)

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await self.service._patch_campaign(
                internal_campaign_id, patch_request, existing_campaign
            )

        # Assert the exception details
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Unable to complete request. Try again later.")

        # Verify that the mocked methods were called as expected
        self.mock_campaign_factory.build_campaign.assert_called_once_with(patch_request, "UPDATE")
        self.mock_campaign_gateway.patch_campaign.assert_not_called()
        mock_logger_error.assert_called_once_with("Invalid value: %s", value_error)

    @patch("app.v2.services.campaign.logger.error")
    async def test_has_activations__campaign_with_activations__should_return_true(
        self, mock_logger_error
    ):
        # Arrange
        internal_campaign_id = "internal-123"
        campaign_data = CAMPAIGNS_SINGLE_RESPONSE.get("data")
        self.mock_campaign_gateway.get_campaign = AsyncMock(
            return_value=CampaignResponse(**campaign_data)
        )

        # Act
        result = await self.service._has_activations(internal_campaign_id)

        # Assert
        self.assertTrue(result)
        self.mock_campaign_gateway.get_campaign.assert_called_once_with(
            internal_campaign_id=internal_campaign_id
        )
        mock_logger_error.assert_not_called()

    @patch("app.v2.services.campaign.logger.error")
    async def test_has_activations__campaign_without_activations__should_return_false(
        self, mock_logger_error
    ):
        # Arrange
        internal_campaign_id = "internal-123"
        campaign_data = CAMPAIGNS_SINGLE_RESPONSE.get("data")
        campaign_data["publishedChanges"]["activations"] = []
        self.mock_campaign_gateway.get_campaign = AsyncMock(
            return_value=CampaignResponse(**campaign_data)
        )
        # Act
        result = await self.service._has_activations(internal_campaign_id)

        # Assert
        self.assertFalse(result)
        self.mock_campaign_gateway.get_campaign.assert_called_once_with(
            internal_campaign_id=internal_campaign_id
        )
        mock_logger_error.assert_not_called()

    @patch("app.v2.services.campaign.deepcopy")
    async def test_pause_or_unpause_campaign__pause_operation__should_return_updated_request(
        self, mock_deepcopy
    ):
        # Arrange
        internal_campaign_id = "internal-123"
        operation = PauseOperationType.PAUSE
        put_request = CampaignPutRequest(
            name="Test Campaign",
            status=CampaignStatus.ACTIVE,
            budgetAmount=1000.0,
            budgetType=BudgetType.DAILY,
            pacingType=PacingType.EVEN,
            startDate="2021-01-01",
            billingInsertionOrder=None,
            billingPurchaseOrder=None,
        )

        # Mock deepcopy to return a modified request
        mock_deepcopy.return_value = put_request

        # Act
        result = await self.service._pause_or_unpause_campaign(
            internal_campaign_id, operation, put_request
        )

        # Assert
        self.mock_campaign_gateway.pause_or_unpause_campaign.assert_called_once_with(
            internal_campaign_id, operation
        )
        mock_deepcopy.assert_called_once_with(put_request)
        self.assertNotIn("status", result.model_dump(exclude_none=True))
        self.assertIsInstance(result, CampaignPutRequest)

    @patch("app.v2.services.campaign.deepcopy")
    async def test_pause_or_unpause_campaign__unpause_operation__should_return_updated_request(
        self, mock_deepcopy
    ):
        # Arrange
        internal_campaign_id = "internal-123"
        operation = PauseOperationType.UNPAUSE
        put_request = CampaignPutRequest(
            name="Test Campaign",
            status=CampaignStatus.PAUSED,
            budgetAmount=1000.0,
            budgetType=BudgetType.DAILY,
            pacingType=PacingType.EVEN,
            startDate="2021-01-01",
            billingInsertionOrder=None,
            billingPurchaseOrder=None,
        )

        # Mock deepcopy to return a modified request
        mock_deepcopy.return_value = put_request

        # Act
        result = await self.service._pause_or_unpause_campaign(
            internal_campaign_id, operation, put_request
        )

        # Assert
        self.mock_campaign_gateway.pause_or_unpause_campaign.assert_called_once_with(
            internal_campaign_id, operation
        )
        mock_deepcopy.assert_called_once_with(put_request)
        self.assertNotIn("status", result.model_dump(exclude_none=True))
        self.assertIsInstance(result, CampaignPutRequest)


    @patch("app.v2.services.campaign.logger.warning")
    async def test_get_contact_numeric_id__contact_found__should_return_contact_id(self, mock_logger_warning):
        # Arrange
        contact_internal_id = "internal-contact-id"
        self.mock_lookup_service.get_contact_short_id_by_long_id.return_value = "numeric-contact-id"

        # Act
        result = await self.service._get_contact_numeric_id(contact_internal_id)

        # Assert
        self.assertEqual(result, "numeric-contact-id")
        self.mock_lookup_service.get_contact_short_id_by_long_id.assert_awaited_once_with(contact_internal_id)
        mock_logger_warning.assert_not_called()

    @patch("app.v2.services.campaign.logger.warning")
    async def test_get_contact_numeric_id__contact_not_found__should_log_warning_and_return_none(self, mock_logger_warning):
        # Arrange
        contact_internal_id = "internal-contact-id"
        self.mock_lookup_service.get_contact_short_id_by_long_id.return_value = None

        # Act
        result = await self.service._get_contact_numeric_id(contact_internal_id)

        # Assert
        self.assertIsNone(result)
        self.mock_lookup_service.get_contact_short_id_by_long_id.assert_awaited_once_with(contact_internal_id)
        mock_logger_warning.assert_called_once_with(
            "Contact id not found in cache for contact salesforce id %s", contact_internal_id
        )

    async def test_get_campaign_long_id__gets_id_from_lookup(self):
        short_id = 1234
        expected_long_id = "long_campaign_id"
        self.mock_lookup_service.get_campaign_long_id_by_short_id.return_value = expected_long_id

        long_id = await self.service.get_campaign_long_id(short_id)

        self.assertEqual(expected_long_id, long_id)
        self.mock_lookup_service.get_campaign_long_id_by_short_id.assert_called_once_with(short_id)

    async def test_get_campaign_long_id__gets_id_from_campaign_search_if_not_in_lookup(self):
        short_id = 1234
        expected_long_id = "long_campaign_id"
        expected_campaign_search_request = CampaignSearchRequest(
            shortIDs=[f"{short_id}"],
            page_offset=0,
            page_size=1
        )
        self.mock_lookup_service.get_campaign_long_id_by_short_id.return_value = None
        self.mock_campaign_gateway.search_campaigns.return_value = auto_mock({
            "data": [{"id": expected_long_id}]
        }, MagicMock())

        long_id = await self.service.get_campaign_long_id(short_id)

        self.assertEqual(expected_long_id, long_id)
        self.mock_lookup_service.get_campaign_long_id_by_short_id.assert_called_once_with(short_id)
        self.mock_campaign_gateway.search_campaigns.assert_called_once_with(expected_campaign_search_request)

    async def test_get_campaign_long_id__raises_error_if_campaign_not_found(self):
        short_id = 1234
        expected_campaign_search_request = CampaignSearchRequest(
            shortIDs=[f"{short_id}"],
            page_offset=0,
            page_size=1
        )
        self.mock_lookup_service.get_campaign_long_id_by_short_id.return_value = None
        self.mock_campaign_gateway.search_campaigns.return_value = auto_mock({
            "data": []
        }, MagicMock())

        with self.assertRaises(HTTPException) as context:
            await self.service.get_campaign_long_id(short_id)

        self.mock_lookup_service.get_campaign_long_id_by_short_id.assert_called_once_with(short_id)
        self.mock_campaign_gateway.search_campaigns.assert_called_once_with(expected_campaign_search_request)
        self.assertIsNotNone(context)
        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Campaign not found", context.exception.detail)