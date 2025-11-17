from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator, field_serializer

from app.common.model.campaign_types import (
    CampaignType,
    InternalCampaignType,
    serialize_campaign_type,
    parse_campaign_type
)
from app.common.view_models import DATE_PATTERN, CampaignStatus, PacingType
from app.common.model.shared import BudgetType, InternalBudgetType
from app.v2.view_models.ad_group import AdGroupV2


class Campaign(BaseModel):
    id: int = Field(title="id", description="The campaign id.")
    name: Optional[str] = Field(
        default=None, title="name", description="The campaign name."
    )
    status: Optional[str] = Field(
        default=None, title="status", description="The campaign status."
    )
    campaignType: Optional[InternalCampaignType] = Field(
        default=None, title="campaignType", description="The campaign type."
    )
    startDate: Optional[str] = Field(
        default=None, title="startDate", description="The campaign start date."
    )
    endDate: Optional[str] = Field(
        default=None, title="endDate", description="The campaign end date."
    )
    budgetAmount: Optional[float] = Field(
        default=None, title="budgetAmount", description="The campaign budget amount."
    )
    budgetType: Optional[str] = Field(
        default=None, title="budgetType", description="The campaign budget type."
    )
    pacingType: Optional[str] = Field(
        default=None, title="pacingType", description="The campaign pacing type."
    )
    accountId: int = Field(title="accountId", description="The account id.")
    advertiserIds: List[int] = Field(
        title="advertiserIds", description="The advertiser ids."
    )
    billingInsertionOrder: Optional[str] = Field(
        default=None,
        title="billingInsertionOrder",
        description="The billing insertion order.",
    )
    billingPurchaseOrder: Optional[str] = Field(
        default=None,
        title="billingPurchaseOrder",
        description="The billing purchase order.",
    )
    billingAdditionalDetails: Optional[str] = Field(
        default="",
        title="billingAdditionalDetails",
        description="The billing additional details.",
    )
    billingContactId: Optional[int] = Field(
        default=None, title="billingContactId", description="The billing contact id."
    )
    billingAddressId: Optional[int] = Field(
        default=None, title="billingAddressId", description="The billing address id."
    )
    adGroups: Optional[List[AdGroupV2]] = Field(
        default=None, title="adGroups", description="The ad groups."
    )
    isArchived: Optional[bool] = Field(
        default=None, title="isArchived", description="The campaign is archived."
    )

    @field_validator("campaignType", mode="before")
    @classmethod
    def transform_campaign_type(cls, internal_value: Any) -> InternalCampaignType | None:
        return parse_campaign_type(internal_value, InternalCampaignType)

    @field_serializer("campaignType")
    def campaign_type_serializer(self, value: InternalCampaignType | None) -> CampaignType | None:
        return serialize_campaign_type(value, CampaignType)


class CampaignRequest(BaseModel):
    name: str = Field(description="The campaign name.")
    status: CampaignStatus = Field(description="The status of the campaign.")

    @field_validator("status")
    def validate_status(cls, v: CampaignStatus):
        if v in [CampaignStatus.DRAFT]:
            return v
        raise ValueError("Campaign status must be DRAFT when creating a campaign")

    startDate: str = Field(
        description="The start date of the campaign. Format: YYYY-MM-DD",
        pattern=DATE_PATTERN,
    )
    endDate: Optional[str] = Field(
        description="The end date of the campaign. Must be after start date. "
        'If null the campaign is considered "always-on". '
        "Cannot be null if budget type is LIFETIME",
        pattern=DATE_PATTERN,
        default="",
    )

    budgetAmount: float = Field(
        description="The total budget of the campaign. "
        "The sum of all the budgets from the ad group(s) may not exceed this number.",
        ge=1,
    )
    budgetType: BudgetType = Field(description="The type of budget.")
    pacingType: PacingType = Field(description="The pacing for the campaign.")
    accountId: int = Field(description="Id from the Account entity.")
    advertiserIds: List[int] = Field(
        description="Ids from the Advertiser entities associated with the account."
    )
    billingInsertionOrder: Optional[str] = Field(
        description="Insertion order number for this campaign.", default=None
    )
    billingPurchaseOrder: Optional[str] = Field(
        description="Purchase order number for this campaign.", default=None
    )
    billingAdditionalDetails: Optional[str] = Field(
        description="Notes that the advertiser wants to notify the billing department.",
        default=None,
    )
    billingContactId: int = Field(
        description="Id from the Contact entity associated with the account."
    )
    billingAddressId: int = Field(
        description="Id from the Address entity associated with the account."
    )
    campaignType: Optional[CampaignType] = Field(
        description="Type for this campaign.", default=CampaignType.PLA
    )


class CampaignPatchRequest(BaseModel):
    source: str = Field(title="source", description="The source of the request.")
    campaignId: int = Field(title="campaignId", description="The campaign id.")
    backgroundInfo: str = Field(
        title="backgroundInfo", description="The background info of the request."
    )
    budgetAmount: float = Field(
        title="budgetAmount", description="The budget amount of the request."
    )
    pacingType: PacingType = Field(
        title="pacingType", description="The pacing type of the request."
    )
    budgetType: InternalBudgetType = Field(
        title="budgetType", description="The budget type of the request."
    )
    isAlwaysOn: bool = Field(
        title="isAlwaysOn", description="The is always on flag of the request."
    )
    name: str = Field(title="name", description="The name of the request.")
    brandIds: List[str] = Field(
        title="brandIds", description="The brand ids of the request."
    )
    isPoRequired: Optional[bool] = Field(
        default=None,
        title="isPoRequired",
        description="The is PO required flag of the request.",
    )
    billingPurchaseOrder: Optional[str] = Field(
        default=None,
        title="billingPurchaseOrder",
        description="The billing purchase order of the request.",
    )
    isIoRequired: Optional[bool] = Field(
        default=None,
        title="isIoRequired",
        description="The is IO required flag of the request.",
    )
    billingInsertionOrder: Optional[str] = Field(
        default=None,
        title="billingInsertionOrder",
        description="The billing insertion order of the request.",
    )
    additionalBillingDetails: str = Field(
        title="additionalBillingDetails",
        description="The additional billing details of the request.",
    )
    contactList: List[Any] = Field(
        title="contactList", description="The contact list of the request."
    )
    internalContactList: List[Any] = Field(
        title="internalContactList",
        description="The internal contact list of the request.",
    )
    addressList: List[Any] = Field(
        title="addressList", description="The address list of the request."
    )
    accountId: str = Field(
        title="accountId", description="The account id of the request."
    )
    startDate: Optional[datetime] = Field(
        default=None, title="startDate", description="The start date of the request."
    )
    endDate: Optional[datetime] = Field(
        default=None, title="endDate", description="The end date of the request."
    )
    status: CampaignStatus = Field(
        title="status", description="The status of the request."
    )
    agencyId: Optional[str] = Field(
        default=None, title="agencyId", description="The agency id of the request."
    )
    isAgencyBilled: bool = Field(
        title="isAgencyBilled", description="The is agency billed flag of the request."
    )

class BillingInfo(BaseModel):
    is_po_required: bool = False
    billing_purchase_order: Optional[str] = None
    is_io_required: bool = False
    billing_insertion_order: Optional[str] = None
    additional_billing_details: str = ""
