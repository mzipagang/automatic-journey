from typing import Optional, List, Any

from pydantic import BaseModel, field_validator

from app.common.model.campaign_types import (
    InternalCampaignType,
    CASCampaignType,
    parse_campaign_type
)


class AddressReference(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None

class ContactReference(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None

class BillingInfo(BaseModel):
    isBeingBilled: Optional[bool] = None
    ioNumber: Optional[str] = None
    ioNumberId: Optional[int] = None
    ioLastModified: Optional[str] = None
    ioLastModifiedBy: Optional[str] = None
    ioLastModifiedByUser: Optional[str] = None
    ioLineItemId: Optional[int] = None
    ioLineItemLastModified: Optional[str] = None
    ioLineItemLastModifiedBy: Optional[str] = None
    poNumber: Optional[str] = None
    poLastModified: Optional[str] = None
    poLastModifiedBy: Optional[str] = None
    poLastModifiedByUser: Optional[str] = None
    budgetShare: Optional[float] = None
    isPORequired: Optional[bool] = None
    isIORequired: Optional[bool] = None

class Agency(BaseModel):
    id: Optional[str] = None
    billingInfo: Optional[BillingInfo] = None

class CASAccount(BaseModel):
    id: Optional[str] = None
    brands: Optional[List[str]] = None
    billingInfo: Optional[BillingInfo] = None
    addresses: Optional[List[AddressReference]] = None
    contacts: Optional[List[ContactReference]] = None
    isAgencyBeingInvolved: bool
    agency: Optional[Agency] = None

class Budget(BaseModel):
    amount: Optional[float] = None
    type: Optional[str] = None
    pacingType: Optional[str] = None

class ExternalId(BaseModel):
    id: Optional[int] = None
    partner: Optional[str] = None

class Division(BaseModel):
    clickThroughUrl: Optional[str] = None
    name: Optional[str] = None

class ClickThroughDestination(BaseModel):
    id: Optional[str] = None
    bannerizedURL: Optional[str] = None
    name: Optional[str] = None
    divisions: Optional[List[Division]] = None

class CASCampaign(BaseModel):
    id: Optional[str] = None
    goalID: Optional[str] = None
    shortId: Optional[str] = None
    created: Optional[str] = None
    createdBy: Optional[str] = None
    createdByUser: Optional[str] = None
    lastModified: Optional[str] = None
    lastModifiedBy: Optional[str] = None
    lastModifiedByClientID: Optional[str] = None
    lastModifiedByUser: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    backgroundInformation: Optional[str] = None
    isAlwaysOn: Optional[bool] = None
    primaryAccount: Optional[CASAccount] = None
    partnerAccounts: Optional[List[CASAccount]] = None
    name: Optional[str] = None
    budget: Optional[Budget] = None
    additionalBillingDetails: Optional[str] = None
    notesForAccounting: Optional[str] = None
    activations: Optional[List[str]] = None
    type: Optional[InternalCampaignType] = None
    source: Optional[str] = None
    status: Optional[str] = None
    externalIDs: Optional[List[ExternalId]] = None
    internalContacts: Optional[List[ContactReference]] = None
    clickThroughDestinations: Optional[List[ClickThroughDestination]] = None
    version: Optional[int] = None
    publishingStatus: Optional[str] = None
    isArchived: Optional[bool] = None

    def get_koddi_advertiser_id(self) -> int | None:
        external_ids: Optional[List[ExternalId]] = self.externalIDs
        if external_ids:
            advertiser_ids: List[ExternalId] = list(filter(
                lambda eid: eid.partner == "KODDI_ADVERTISER_ID", external_ids))
            if advertiser_ids:
                return advertiser_ids[0].id
        return None

    @field_validator("type", mode="before")
    @classmethod
    def validate_upstream_campaign_type(cls, value: Any) -> InternalCampaignType | None:
        return parse_campaign_type(value, CASCampaignType)
