from datetime import datetime
from typing import Tuple, List

from fastapi import HTTPException

from app.common.view_models import CampaignStatus, CampaignPutRequest
from app.common.context.context import logging_extra_context
from app.common.model.advertiser import AdvertiserType, CachedAdvertiser
from app.common.model.downstream.campaign_activation_service import CASCampaign, CASAccount, Budget, ContactReference, \
    AddressReference
from app.common.model.shared import CampaignType, BudgetType, InternalBudgetType

from app.common.utils import filtered_logger
from app.v2.utils.campaign_validator import validate_dates_with_budget
from app.common.utils.context_tools import update_context
from app.common.utils.date_utils import parse_date
from app.v2.utils.filtering_monad_functors import CampaignFunctors

from app.v2.view_models import Campaign, CampaignRequest

logger = filtered_logger.get_logger(__name__)


def filter_campaigns(campaigns: List[CASCampaign], advertiser: CachedAdvertiser) -> List[CASCampaign]:
    filter_predicates = [
        CampaignFunctors.campaign_has_brands(logger),
        CampaignFunctors.campaign_has_correct_advertiser_brand_id(logger, advertiser)
    ]

    return list(filter(lambda campaign: all(predicate(campaign) for predicate in filter_predicates), campaigns))

def is_valid_campaign_type(campaign_type: str) -> bool:
    return campaign_type.strip() in CampaignType._value2member_map_

def get_agency_id(current_user: dict) -> str:
    """Extract agency ID from user information"""
    agency_id = None
    if current_user['is_agency'] is True:
        agency_id = current_user['works_for']['clientId']
    return agency_id

def log_campaign_creation_failure(short_id, success_details):
    """Log campaign creation failure"""
    update_context(
        logging_extra_context,
        campaign_id=short_id,
        **success_details
    )
    logger.warning(
        "Failed to create campaign",
        extra={
            "monitored_transaction": "CAMPAIGN-ERROR--CREATE",
        }
    )

def determine_advertiser_type(primary_account: CASAccount) -> AdvertiserType:
    """Determine advertiser type"""
    is_agency_involved = primary_account.isAgencyBeingInvolved or False

    is_agency_being_billed = primary_account.agency.billingInfo.isBeingBilled \
        if primary_account.agency and primary_account.agency.billingInfo else False

    return AdvertiserType.AGENCY if is_agency_involved and is_agency_being_billed else AdvertiserType.CPG

def determine_start_date(campaign: Campaign, campaign_request: CampaignRequest) -> datetime:
    if campaign_request.startDate:
        return parse_date(campaign_request.startDate)
    if campaign.startDate:
        return parse_date(campaign.startDate)
    raise HTTPException(status_code=400, detail="Failed to provide a valid start date.")

def determine_end_date(campaign_request: CampaignRequest) -> datetime | None:
    """Determine end date from request"""
    if not campaign_request.endDate:
        return None

    return parse_date(campaign_request.endDate)

async def process_dates_and_budget(
        campaign_request: CampaignRequest) -> Tuple[datetime, datetime | None, InternalBudgetType, bool]:
    """Process and validate campaign dates"""
    start_date = parse_date(campaign_request.startDate)

    end_date = None
    if campaign_request.endDate is not None and campaign_request.endDate != "":
        end_date = parse_date(campaign_request.endDate)

    budget_type = campaign_request.budgetType
    if campaign_request.budgetType == BudgetType.LIFETIME:
        budget_type = InternalBudgetType.CUSTOM

    # Validate dates
    await validate_dates_with_budget(start_date, end_date, campaign_request.budgetType)

    is_always_on = end_date is None

    return start_date, end_date, budget_type, is_always_on

def determine_budget_type(campaign: Campaign, campaign_request: CampaignRequest) -> BudgetType | None:
    budget_type = None

    if campaign.status == CampaignStatus.DRAFT:
        budget_type = campaign.budgetType if campaign_request.budgetType is None else campaign_request.budgetType

        if budget_type == BudgetType.LIFETIME:
            budget_type = InternalBudgetType.CUSTOM

    elif campaign.status in [
        CampaignStatus.ACTIVE,
        CampaignStatus.PAUSED,
        CampaignStatus.SCHEDULED,
    ]:
        budget_type = campaign.budgetType

    return budget_type

def get_address_internal_id(addresses: List[AddressReference], short_id=None) -> str | None :
    """Extract address internal ID from addresses list"""
    if not addresses:
        if short_id:
            logger.warning("Unable to find address in list: %s, for campaign %s . Returned 'None'",
                           addresses, short_id)
        return None

    if len(addresses) > 1:
        # Find address with type ALTERNATE
        alternate_address = next((address for address in addresses if address.type == 'ALTERNATE'), None)
        if alternate_address is not None:
            return alternate_address.id

    # Default to first address
    return addresses[0].id

def get_billing_contact_internal_id(contacts: List[ContactReference]) -> str | None :
    """Extract billing contact internal ID from contacts list"""
    if not contacts:
        return None

    billing_contact = next(
        (contact for contact in contacts if contact.type.upper() == 'BILLING-CONTACT'),
        None)

    return billing_contact.id if billing_contact else None

def process_status(status: str, short_id: str) -> str:
    """Process campaign status"""
    status = status.upper()

    if status not in ('ACTIVE', 'DRAFT'):
        logger.warning('Campaign %s has status %s', short_id, status)

    return status

def contains_pause_or_unpause_request(campaign: Campaign, campaign_request: CampaignPutRequest) -> bool:
    return (is_pause_requested(campaign, campaign_request)
            or is_unpause_requested(campaign, campaign_request))

def is_pause_requested(campaign: Campaign, campaign_request: CampaignPutRequest) -> bool:
    return campaign.status == CampaignStatus.ACTIVE and campaign_request.status == CampaignStatus.PAUSED

def is_unpause_requested(campaign: Campaign, campaign_request: CampaignPutRequest) -> bool:
    return campaign.status == CampaignStatus.PAUSED and campaign_request.status == CampaignStatus.ACTIVE

def request_implies_no_delta(campaign: Campaign, campaign_request: CampaignPutRequest) -> bool:
    campaign_dict = campaign.model_dump(exclude_unset=True, exclude_none=True)
    request_dict = campaign_request.model_dump(exclude_unset=True, exclude_none=True)
    effective_request = {k: v for k, v in request_dict.items() if campaign_dict.get(k) != request_dict.get(k)}
    return len(effective_request.keys()) == 0

def process_billing_info(
        campaign: Campaign,
        campaign_request: CampaignPutRequest
) -> tuple[bool | None, bool | None, str | None, str | None]:
    is_po_required = None
    is_io_required = None
    billing_purchase_order = None
    billing_insertion_order = None

    if campaign.status != CampaignStatus.DRAFT:
        return is_po_required, is_io_required, billing_purchase_order, billing_insertion_order

    if campaign_request.billingPurchaseOrder is not None:
        if len(campaign_request.billingPurchaseOrder) == 0:
            is_po_required = False
        elif len(campaign_request.billingPurchaseOrder) > 0:
            is_po_required = True
            billing_purchase_order = campaign_request.billingPurchaseOrder

    if campaign_request.billingInsertionOrder is not None:
        if len(campaign_request.billingInsertionOrder) == 0:
            is_io_required = False
        elif len(campaign_request.billingInsertionOrder) > 0:
            is_io_required = True
            billing_insertion_order = campaign_request.billingInsertionOrder

    return is_po_required, is_io_required, billing_purchase_order, billing_insertion_order

def get_budget(campaign: CASCampaign) -> Budget:
    """Process budget information"""
    budget_type = campaign.budget.type.upper()

    # If budget type is CUSTOM change it to LIFETIME
    if budget_type == 'CUSTOM':
        budget_type = 'LIFETIME'

    return Budget(
        amount=campaign.budget.amount,
        type=budget_type,
        pacingType=campaign.budget.pacingType
    )

def get_dates(campaign: CASCampaign) -> tuple[str, str]:
    """Process start and end dates"""
    start_date = _extract_date(campaign.startDate)
    if not start_date:
        logger.warning("Campaign %s does not have a start date", campaign.shortId,
                       extra={
                           'kap_campaign_id': campaign.id,
                           'internal_campaign_id': campaign.shortId,
                           'campaign_status': (campaign.status or '').upper(),
                           'monitored_transaction': 'CAMPAIGN-START-DATE-MISSING'
                       })

    end_date = _extract_date(campaign.endDate)
    return start_date, end_date

def _extract_date(date_string: str | None) -> str:
    """Extract date from date string"""
    if not date_string:
        return ''

    return date_string.split('T')[0]
