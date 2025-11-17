from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_serializer

from app.common.model.campaign_types import InternalCampaignType, CASCampaignType,\
    serialize_campaign_type
from app.common.model.downstream.campaign_activation_service import CASCampaign
from app.common.model.shared import InternalPublishStatus


class Validations(BaseModel):
    path: Optional[str] = Field(
        default=None,
        title="path",
        description="JSON path to the field with a validation warning.",
    )
    detail: Optional[List[str]] = Field(
        default=None,
        title="detail",
        description="Details about the validation warnings.",
    )


class StatusDateTime(BaseModel):
    value: Optional[str] = Field(
        default=None,
        title="value",
        description="The date and time of the status change.",
    )
    timezone: Optional[str] = Field(
        default=None, title="timezone", description="The timezone of the date and time."
    )


class PublishingMetaData(BaseModel):
    code: Optional[str] = Field(
        default=None, title="code", description="The code of the publishing meta data."
    )
    description: Optional[str] = Field(
        default=None,
        title="description",
        description="The description of the publishing meta data.",
    )
    datetime: Optional[StatusDateTime] = Field(
        default=None,
        title="datetime",
        description="The date and time of the publishing meta data.",
    )
    errorCode: Optional[int] = Field(
        default=None,
        title="errorCode",
        description="The error code of the publishing meta data.",
    )
    errorMessages: Optional[List[dict]] = Field(
        default=None,
        title="errorMessage",
        description="The error messages of the publishing meta data.",
    )
    changes: Optional[List[str]] = Field(
        default=None,
        title="changes",
        description="The changes of the publishing meta data.",
    )


class ValidateResponse(BaseModel):
    status: Optional[str] = Field(
        default=None, title="status", description="The status of the validation."
    )


class PublishResponse(BaseModel):
    status: Optional[InternalPublishStatus] = Field(
        default=None, title="status", description="The status of the publish."
    )
    datetime: Optional[StatusDateTime] = Field(
        default=None, title="datetime", description="The date and time of the publish."
    )


class CampaignResponse(BaseModel):
    validations: Optional[List[Validations]] = Field(
        default=None,
        title="validations",
        description="The validations of the campaign.",
    )
    unpublishedChanges: Optional[CASCampaign] = Field(
        default=None,
        title="unpublishedChanges",
        description="The unpublished changes of the campaign.",
    )
    publishedChanges: Optional[CASCampaign] = Field(
        default=None,
        title="publishedChanges",
        description="The published changes of the campaign.",
    )
    publishingMetaData: Optional[PublishingMetaData] = Field(
        default=None,
        title="publishingMetaData",
        description="The publishing meta data of the campaign.",
    )
    publishingStatus: Optional[InternalPublishStatus] = Field(
        default=None,
        title="publishingStatus",
        description="The publishing status of the campaign.",
    )
    changes: Optional[List[Any]] = Field(
        default=None, title="changes", description="The changes of the campaign."
    )


class Page(BaseModel):
    offset: Optional[int] = Field(
        default=None, title="offset", description="The offset of the page."
    )
    size: Optional[int] = Field(
        default=None, title="size", description="The size of the page."
    )
    hasMore: Optional[bool] = Field(
        default=None, title="hasMore", description="Whether there are more pages."
    )
    totalPages: Optional[int] = Field(
        default=None, title="totalPages", description="The total number of pages."
    )
    totalCount: Optional[int] = Field(
        default=None, title="totalCount", description="The total number of items."
    )


class Meta(BaseModel):
    page: Optional[Page] = Field(
        default=None, title="page", description="The page of the meta data."
    )


class CampaignsResponse(BaseModel):
    data: List[CASCampaign] = Field(
        default=None, title="data", description="The data of the campaigns."
    )
    meta: Optional[Meta] = Field(
        default=None, title="meta", description="The meta data of the campaigns."
    )


class ContactInner(BaseModel):
    ACCOUNT_EXECUTIVE: Optional[List[str]] = Field(
        None,
        title="ACCOUNT_EXECUTIVE",
        description="The account executive of the contact.",
    )
    ACCOUNT_MANAGER: Optional[List[str]] = Field(
        None, title="ACCOUNT_MANAGER", description="The account manager of the contact."
    )
    INTERNAL_CONTACT_TYPE_AS_KEY: Optional[List[str]] = Field(
        default=None,
        title="INTERNAL_CONTACT_TYPE_AS_KEY",
        description="The internal contact type as key of the contact.",
    )


class ContactsMain(BaseModel):
    contacts: Optional[ContactInner] = Field(
        default=None, title="contacts", description="The contacts of the campaign."
    )


class CampaignSearchRequest(BaseModel):
    primaryAccountIDs: Optional[List[str]] = Field(
        default=None,
        title="primaryAccountIDs",
        description="The primary account IDs of the campaign.",
    )
    id: Optional[List[str]] = Field(
        default=None, title="id", description="The ID of the campaign."
    )
    name: Optional[str] = Field(
        default=None, title="name", description="The name of the campaign."
    )
    externalPartner: Optional[str] = Field(
        default=None,
        title="externalPartner",
        description="The external partner of the campaign.",
    )
    externalPartnerID: Optional[int] = Field(
        default=None,
        title="externalPartnerID",
        description="The external partner ID of the campaign.",
    )
    externalPartnerIDs: Optional[List[int]] = Field(
        default=None,
        title="externalPartnerIDs",
        description="The external partner IDs of the campaign.",
    )
    brandIDs: Optional[List[str]] = Field(
        default=None, title="brandIDs", description="The brand IDs of the campaign."
    )
    page_offset: Optional[int] = Field(0, serialization_alias="page.offset")
    page_size: Optional[int] = Field(30, serialization_alias="page.size")
    startDate: Optional[str] = Field(
        default=None, title="startDate", description="The start date of the campaign."
    )
    startDateRange: Optional[str] = Field(
        default=None,
        title="startDateRange",
        description="The start date range of the campaign.",
    )
    endDateRange: Optional[str] = Field(
        default=None,
        title="endDateRange",
        description="The end date range of the campaign.",
    )
    searchTerm: Optional[str] = Field(
        default=None, title="searchTerm", description="The search term of the campaign."
    )
    endDate: Optional[str] = Field(
        default=None, title="endDate", description="The end date of the campaign."
    )
    status: Optional[List[str]] = Field(
        default=None, title="status", description="The status of the campaign."
    )
    sortBy: Optional[str] = Field(
        default=None, title="sortBy", description="The sort by of the campaign."
    )
    shortIDs: Optional[List[str]] = Field(
        default=None, title="shortIDs", description="The short IDs of the campaign."
    )
    campaignType: Optional[List[InternalCampaignType]] = Field(
        default=None,
        title="campaignType",
        description="The campaign type of the campaign.",
    )
    publishingStatus: Optional[List[str]] = Field(
        default=None,
        title="publishingStatus",
        description="The publishing status of the campaign.",
    )
    isArchived: Optional[bool] = Field(
        default=None,
        title="isArchived",
        description="Whether the campaign is archived.",
    )
    contacts: Optional[ContactsMain] = Field(
        default=None, title="contacts", description="The contacts of the campaign."
    )

    @field_serializer('campaignType')
    def serialize_outgoing_campaign_types(
            self,
            campaign_types: Optional[List[InternalCampaignType]]
    ):
        if not campaign_types:
            return None
        return [
            serialize_campaign_type(campaign_type, CASCampaignType)
            for campaign_type in campaign_types
            if campaign_type != InternalCampaignType.UNSUPPORTED
        ]
