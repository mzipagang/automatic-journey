from datetime import datetime
from typing import Tuple, List, Optional

from app.common.model.campaign_types import InternalCampaignType
from app.common.view_models import CampaignStatus
from app.common.model.advertiser import CachedAdvertiser
from app.common.model.contact import InternalContact
from app.common.model.downstream.campaign_activation_service import (
    CASCampaign, Budget, ContactReference, AddressReference, BillingInfo as CASBillingInfo)
from app.common.model.downstream.campaign_service import CampaignResponse
from app.common.model.shared import BudgetType, InternalBudgetType

from app.common.utils import filtered_logger

from app.v2.view_models import BillingInfo, CampaignPatchRequest, Campaign, CampaignRequest

logger = filtered_logger.get_logger(__name__)

class CampaignTranslation:

    @staticmethod
    def build_billing_info(campaign_request: CampaignRequest) -> BillingInfo:
        """Build billing information for the campaign"""
        is_po_required = False
        is_io_required = False
        billing_purchase_order = None
        billing_insertion_order = None

        if campaign_request.billingPurchaseOrder:
            is_po_required = True
            billing_purchase_order = campaign_request.billingPurchaseOrder

        if campaign_request.billingInsertionOrder:
            is_io_required = True
            billing_insertion_order = campaign_request.billingInsertionOrder

        additional_billing_details = campaign_request.billingAdditionalDetails or ""

        return BillingInfo(
            is_po_required=is_po_required,
            billing_purchase_order=billing_purchase_order,
            is_io_required=is_io_required,
            billing_insertion_order=billing_insertion_order,
            additional_billing_details=additional_billing_details,
        )


    @staticmethod
    def prepare_update_payload(campaign_request: CampaignRequest,
                               source: str,
                               short_id: int,
                               background_info: str,
                               budget_type: InternalBudgetType,
                               is_always_on: bool,
                               advertisers: List[CachedAdvertiser],
                               contact_list: List[ContactReference],
                               internal_contacts: List[InternalContact],
                               address_list: List[AddressReference],
                               account_id: str,
                               start_date: Optional[datetime],
                               end_date: Optional[datetime],
                               agency_id: Optional[str],
                               is_agency_billed: bool,
                               billing_details: BillingInfo
                               ) -> CampaignPatchRequest:
        """Prepare payload for campaign update"""
        return CampaignPatchRequest(
            source=source,
            campaignId=short_id,
            backgroundInfo=background_info,
            budgetAmount=campaign_request.budgetAmount,
            pacingType=campaign_request.pacingType,
            budgetType=budget_type,
            isAlwaysOn=is_always_on,
            name=campaign_request.name,
            brandIds=[advertiser.brandId for advertiser in advertisers],
            isPoRequired=billing_details.is_po_required,
            billingPurchaseOrder=billing_details.billing_purchase_order,
            isIoRequired=billing_details.is_io_required,
            billingInsertionOrder=billing_details.billing_insertion_order,
            additionalBillingDetails=billing_details.additional_billing_details,
            contactList=contact_list,
            internalContactList=internal_contacts,
            addressList=address_list,
            accountId=account_id,
            startDate=start_date,
            endDate=end_date,
            status=campaign_request.status,
            agencyId=agency_id,
            isAgencyBilled=is_agency_billed
        )

    @staticmethod
    def build_patch_payload(campaign: Campaign,
                            campaign_request: CampaignRequest,
                            source: str,
                            campaign_id: int,
                            is_always_on: bool,
                            advertisers: List[CachedAdvertiser],
                            contact_list: List[ContactReference],
                            internal_contacts: List[InternalContact],
                            address_list: List[AddressReference],
                            account_id: str,
                            is_agency_billed: bool,
                            budget_type: InternalBudgetType,
                            start_date: Optional[datetime],
                            end_date: Optional[datetime],
                            billing_info:Tuple[Optional[bool], Optional[bool], Optional[str], Optional[str]]) -> CampaignPatchRequest:
        """Build appropriate payload based on campaign status"""
        background_info = f"API Campaign ID: {campaign_id}"
        is_po_required, is_io_required, billing_purchase_order, billing_insertion_order = billing_info

        if campaign.status == CampaignStatus.DRAFT:
            return CampaignTranslation._build_draft_payload(
                campaign_request, source, campaign_id, background_info,
                is_always_on, advertisers, is_po_required, billing_purchase_order,
                is_io_required, billing_insertion_order, contact_list, internal_contacts,
                address_list, account_id, is_agency_billed, start_date, end_date,
                budget_type
            )
        else:
            return CampaignTranslation._build_active_payload(
                campaign_request, campaign, source, campaign_id, background_info,
                is_always_on, advertisers, contact_list, internal_contacts,
                address_list, account_id, is_agency_billed, end_date
            )

    @staticmethod
    def _build_draft_payload(campaign_request: CampaignRequest,
                             source: str,
                             campaign_id: int,
                             background_info: str,
                             is_always_on: bool,
                             advertisers: List[CachedAdvertiser],
                             is_po_required: bool | None,
                             billing_purchase_order: str | None,
                             is_io_required: bool | None,
                             billing_insertion_order: str | None,
                             contact_list: List[ContactReference],
                             internal_contacts: List[InternalContact],
                             address_list: List[AddressReference],
                             account_id: str,
                             is_agency_billed: bool,
                             start_date: datetime | None,
                             end_date: datetime | None,
                             budget_type: InternalBudgetType) -> CampaignPatchRequest:
        """Build payload for DRAFT campaigns"""
        return CampaignPatchRequest(
            name=campaign_request.name,
            status=campaign_request.status,
            startDate=start_date,
            endDate=end_date,
            budgetAmount=campaign_request.budgetAmount,
            budgetType=budget_type,
            pacingType=campaign_request.pacingType,
            additionalBillingDetails=campaign_request.billingAdditionalDetails or "",
            # retrieved data
            source=source,
            campaignId=campaign_id,
            backgroundInfo=background_info,
            isAlwaysOn=is_always_on,
            brandIds=[advertiser.brandId for advertiser in advertisers],
            isPoRequired=is_po_required,
            billingPurchaseOrder=billing_purchase_order,
            isIoRequired=is_io_required,
            billingInsertionOrder=billing_insertion_order,
            contactList=contact_list,
            internalContactList=internal_contacts,
            addressList=address_list,
            accountId=account_id,
            isAgencyBilled=is_agency_billed,
        )

    @staticmethod
    def _build_active_payload(campaign_request: CampaignRequest,
                              campaign: Campaign,
                              source: str,
                              campaign_id: int,
                              background_info: str,
                              is_always_on: bool,
                              advertisers: List[CachedAdvertiser],
                              contact_list: List[ContactReference],
                              internal_contacts: List[InternalContact],
                              address_list: List[AddressReference],
                              account_id: str,
                              is_agency_billed: bool,
                              end_date: datetime | None) -> CampaignPatchRequest:
        """Build payload for ACTIVE campaigns"""
        return CampaignPatchRequest(
            name=campaign_request.name,
            endDate=end_date,
            budgetAmount=campaign_request.budgetAmount,
            pacingType=campaign_request.pacingType,
            additionalBillingDetails=campaign_request.billingAdditionalDetails or "",
            status=campaign_request.status,
            # do not change
            # 'translate' budget type if necessary from "lifetime" to "custom", otherwise keep the same
            budgetType=(
                InternalBudgetType.CUSTOM
                if campaign.budgetType == BudgetType.LIFETIME
                else campaign.budgetType
            ),
            # retrieved data
            source=source,
            campaignId=campaign_id,
            backgroundInfo=background_info,
            isAlwaysOn=is_always_on,
            brandIds=[advertiser.brandId for advertiser in advertisers],
            contactList=contact_list,
            internalContactList=internal_contacts,
            addressList=address_list,
            accountId=account_id,
            isAgencyBilled=is_agency_billed,
        )

    @staticmethod
    def build_contact_list(billing_contact_id: str) -> List[ContactReference]:
        """Build the contact list for the campaign"""
        return [
            ContactReference(
                id=billing_contact_id,
                type="billing-contact",
            ),
            ContactReference(
                id=billing_contact_id,
                type="creative-contact",
            ),
            ContactReference(
                id=billing_contact_id,
                type="primary-client-contact",
            ),
        ]

    @staticmethod
    def build_address_list(corporate_address_id: str, billing_address_id: str) -> List[AddressReference]:
        """Build the address list for the campaign"""
        return [
            AddressReference(
                id=corporate_address_id,
                type="CORPORATE",
            ),
            AddressReference(
                id=billing_address_id,
                type="ALTERNATE",
            ),
        ]

    @staticmethod
    def get_campaign_and_publish_status_from_response(response: CampaignResponse) -> Tuple[CASCampaign, str]:
        campaign = CASCampaign(
            **{
                **(response.publishedChanges.__dict__ if response.publishedChanges else {}),
                **(response.unpublishedChanges.__dict__ if response.unpublishedChanges else {})
           }
        )
        return campaign, response.publishingStatus
