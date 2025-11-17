from typing import List
from fastapi import HTTPException
from fastapi.params import Depends

from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.model.redis import CachedAddress, CachedContact
from app.common.view_models import AdGroupStatus
from app.common.decorators.decorators import conditionally_execute
from app.common.model.advertiser import AdvertiserType
from app.common.model.downstream.campaign_service import Validations
from app.common.model.shared import BudgetType, UpstreamValidationWarning
from app.common.services.account_service import AccountService
from app.common.services.address_service import AdvertiserAddressService
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.contact_service import AdvertiserContactService
from app.common.utils import filtered_logger
from app.common.utils.date_utils import add_years, parse_date
from app.common.utils.jwt import validate_account, validate_advertisers
from app.v2.view_models import CampaignPatchRequest, AdGroupV2
from app.common.services.lookup_service import LookupService

logger = filtered_logger.get_logger(__name__)


async def validate_dates_with_budget(start_date, end_date, budget_type):
    """Validate campaign dates"""
    if end_date is not None and end_date >= add_years(start_date, 2):
        raise HTTPException(status_code=400, detail="Campaign end date must be within 2 years after start date")

    if budget_type == BudgetType.LIFETIME and end_date is None:
        raise HTTPException(status_code=400, detail="End date must be provided for lifetime campaigns")


@conditionally_execute(flag_name=HarnessFeatureFlags.DISABLE_MULTIPLE_BRAND_IDS)
def validate_multiple_brand_ids(campaign_request: CampaignPatchRequest):
    """Validate brand ids"""
    if len(campaign_request.brandIds) > 1:
        raise HTTPException(status_code=400, detail="Multi-brand campaigns are not yet supported")


def from_upstream_campaign_validations(warnings: Validations):
    return UpstreamValidationWarning(
        detail=warnings.detail,
        path=warnings.path)


class CampaignValidator:
    account_service: AccountService
    advertiser_service: AdvertiserService
    address_service: AdvertiserAddressService
    contact_service: AdvertiserContactService
    lookup_service: LookupService

    def __init__(
            self,
            account_service: AccountService = Depends(AccountService),
            advertiser_service: AdvertiserService = Depends(AdvertiserService),
            address_service: AdvertiserAddressService = Depends(AdvertiserAddressService),
            contact_service: AdvertiserContactService = Depends(AdvertiserContactService),
            lookup_service: LookupService = Depends(LookupService)):

        self.account_service = account_service
        self.advertiser_service = advertiser_service
        self.address_service = address_service
        self.contact_service = contact_service
        self.lookup_service = lookup_service

    async def validate_account_and_advertisers(self, current_user, campaign_request):
        """Validate user permissions for campaign creation"""
        await validate_account(current_user, campaign_request.accountId, self.account_service)
        await validate_advertisers(current_user, campaign_request.advertiserIds, self.advertiser_service)

    async def validate_dates_with_ad_groups(self, ad_groups: list[AdGroupV2], campaign, end_date, start_date):
        """Validate campaign end date"""
        if end_date:
            # Check if related ad groups have valid end dates
            if not campaign.endDate and not await self._related_adgroups_have_valid_enddate(
                    ad_groups, end_date):
                raise HTTPException(
                    status_code=400, detail="Campaign end date cannot be set:"
                                            " a related active Ad Group end date is null or greater than requested.")

            # TODO: the validation below has been removed in CAS, do we remove this on our end?
            if end_date >= add_years(start_date, 2):
                raise HTTPException(status_code=400,
                                    detail="Campaign end date must be within 2 years after start date.")

    async def _related_adgroups_have_valid_enddate(self, ad_groups: list[AdGroupV2], end_date_ref) -> bool:
        is_valid = True
        for ad_group in ad_groups:
            if (ad_group.status != AdGroupStatus.ENDED and ad_group.endDate is None) or (
                    ad_group.endDate is not None and parse_date(ad_group.endDate) > end_date_ref):
                is_valid = False

        return is_valid

    async def validate_billing_info(
            self,
            address: CachedAddress,
            contact: CachedContact,
            account_id,
            agency_id=None
    ):
        """Validate billing information and return processed billing details"""
        is_agency_billed = False

        if agency_id is not None:
            if address.addressType == AdvertiserType.AGENCY:
                logger.info("Agency user selected an agency address")
                corporate_address_id = await self.address_service.get_corporate_address_by_internal_account_id(
                    agency_id)
                if await self.contact_service.validate_address_on_agency_involved_campaign(contact, account_id):
                    billing_contact_id = contact.id
                    is_agency_billed = True
                else:
                    raise HTTPException(
                        status_code=400, detail="Billing address belongs to an agency, but the contact does not")
            else:
                corporate_address_id = await self.address_service.get_corporate_address_by_internal_account_id(
                    account_id)
                billing_contact_id = contact.id
                if contact.contactType == AdvertiserType.AGENCY:
                    raise HTTPException(
                        status_code=400, detail="Billing contact belongs to an agency, but the address does not")
        else:
            corporate_address_id = await self.address_service.get_corporate_address_by_internal_account_id(account_id)
            billing_contact_id = contact.id
            if contact.contactType == AdvertiserType.AGENCY:
                raise HTTPException(
                    status_code=400,
                    detail="Billing contact belongs to an agency, but the address does not")

        if billing_contact_id is None:
            raise HTTPException(status_code=400, detail="Failed to provide a valid billing contact ID")

        billing_address_id = address.id
        if billing_address_id is None:
            raise HTTPException(status_code=400, detail="Failed to provide a valid billing address ID")

        if corporate_address_id is None:
            logger.warning("Failed to find a valid corporate address id, using the provided address ID")
            corporate_address_id = billing_address_id

        return {
            "billing_contact_id": billing_contact_id,
            "billing_address_id": billing_address_id,
            "corporate_address_id": corporate_address_id,
            "is_agency_billed": is_agency_billed
        }

    async def validate_campaign_multi_supplier(self, advertisers_ids: List[int], account_long_id: str):
        cached_advertisers = await self.lookup_service.get_advertiser_details_by_short_ids(advertisers_ids)

        if len(advertisers_ids) != len(list(filter(lambda advertiser: advertiser is not None, cached_advertisers))):
            raise HTTPException(status_code=400, detail="Invalid advertiser Ids")

        if any( advertiser.client.clientId != account_long_id
               for advertiser in cached_advertisers if advertiser is not None):
            raise HTTPException(status_code=400, detail="Multi-supplier campaigns are not yet supported")