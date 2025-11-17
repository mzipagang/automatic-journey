from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer

from app.common.model.campaign_types import (
    InternalCampaignType,
    parse_campaign_type,
    CASCampaignType,
    serialize_campaign_type
)
from app.common.model.shared import (
    ActivationErrors,
    ActivationPublishStatus,
    ActivationWarnings,
)


# took enum from media-mgmt-activation/app/model/activation_status.py
# https://github.com/8451LLC/media-mgmt-activation/blob/main/app/model/activation_status.py


class PublishResultEnum(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class PublishErrorByField(BaseModel):
    field_name: str = Field(
        title="field_name", description="Name of the field with an error."
    )
    error_message: str = Field(
        title="error_message", description="Error message for the field."
    )


class ChannelData(BaseModel):
    carouselHeadline: Optional[str] = Field(
        default=None,
        title="carouselHeadline",
        description="The headline for the carousel.",
    )
    name: Optional[str] = Field(
        default=None, title="name", description="The name of the activation."
    )
    startDate: Optional[str] = Field(
        default=None, title="startDate", description="The start date of the activation."
    )
    endDate: Optional[str] = Field(
        default=None, title="endDate", description="The end date of the activation."
    )
    alwaysOn: Optional[bool] = Field(
        default=None,
        title="alwaysOn",
        description="Whether the activation is always on.",
    )
    budgetType: Optional[str] = Field(
        default=None,
        title="budgetType",
        description="The type of budget for the activation.",
    )
    budgetAmount: Optional[float] = Field(
        default=None,
        title="budgetAmount",
        description="The amount of the budget for the activation.",
    )
    biddableEntities: Optional[List[str]] = Field(
        default=None,
        title="biddableEntities",
        description="The entities that are biddable for the activation.",
    )
    keywordBidModifierGroup: Optional[str] = Field(
        default=None,
        title="keywordBidModifierGroup",
        description="The keywords group for the activation.",
    )
    divisionBanners: Optional[List[str]] = Field(
        default=None,
        title="divisionBanners",
        description="The banners for the activation.",
    )
    placementType: Optional[List[str]] = Field(
        default=None,
        title="placementType",
        description="The type of placement for the activation.",
    )
    dayPartingStart: Optional[int] = Field(
        default=None,
        title="dayPartingStart",
        description="The start time for day parting.",
    )
    dayPartingEnd: Optional[int] = Field(
        default=None, title="dayPartingEnd", description="The end time for day parting."
    )
    carouselSubtext: Optional[str] = Field(
        default=None,
        title="carouselSubtext",
        description="Add subtext to carousel ad group."
    )
    model_config = ConfigDict(extra="allow")


class ChannelConfig(BaseModel):
    type: InternalCampaignType = Field(title="type", description="The type of the channel.")
    version: str = Field(title="version", description="The version of the channel.")

    @field_validator("type", mode="before")
    @classmethod
    def validate_upstream_campaign_type(cls, value: Any) -> InternalCampaignType | None:
        return parse_campaign_type(value, CASCampaignType)

    @field_serializer("type")
    def serialize_upstream_campaign_type(
            self,
            value: InternalCampaignType
    ) -> CASCampaignType | None:
        return serialize_campaign_type(value, CASCampaignType)


class ActivationPayload(BaseModel):
    channel_data: ChannelData = Field(
        title="channel_data", description="The data for the channel."
    )
    channel_config: ChannelConfig = Field(
        title="channel_config", description="The configuration for the channel."
    )
    campaign_id: str = Field(title="campaign_id", description="The ID of the campaign.")


class ActivationUpdatePayload(BaseModel):
    channel_data: ChannelData = Field(
        title="channel_data", description="The data for the channel."
    )


class ActivationsQueryBody(BaseModel):
    ids: Optional[List[str]] = Field(
        default=None, title="ids", description="List of activation IDs."
    )
    creative_group: Optional[str] = Field(
        default=None,
        title="creative_group",
        description="The creative group for the activation.",
    )
    koddi_id: Optional[str] = Field(
        default=None, title="koddi_id", description="The koddi ID for the activation."
    )
    campaign_ids: Optional[List[str]] = Field(
        default=None, title="campaign_ids", description="List of campaign IDs."
    )
    audience_id: Optional[str] = Field(
        default=None,
        title="audience_id",
        description="The audience ID for the activation.",
    )
    archive: Optional[str] = Field(
        default=None, title="archive", description="The archive for the activation."
    )


class ActivationStatus(StrEnum):
    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    SCHEDULED = "Scheduled"
    PAUSED = "Paused"
    ACTIVE = "Active"
    ENDED = "Ended"
    FAILED = "Failed"


class ActivationMetaData(BaseModel):
    created_at: str = Field(
        title="created_at",
        description="The date and time when the activation was created.",
    )
    created_by: Optional[str] = Field(
        default=None,
        title="created_by",
        description="The user who created the activation.",
    )
    created_by_user_id: Optional[str] = Field(
        default=None,
        title="created_by_user_id",
        description="The ID of the user who created the activation.",
    )
    created_by_user_name: Optional[str] = Field(
        default=None,
        title="created_by_user_name",
        description="The name of the user who created the activation.",
    )
    created_by_user_email: Optional[str] = Field(
        default=None,
        title="created_by_user_email",
        description="The email of the user who created the activation.",
    )
    created_by_client_id: Optional[str] = Field(
        default=None,
        title="created_by_client_id",
        description="The client ID of the user who created the activation.",
    )

    last_modified: Optional[datetime] = Field(
        default=None,
        title="last_modified",
        description="The date and time when the activation was last modified.",
    )
    last_modified_by_user_id: Optional[str] = Field(
        default=None,
        title="last_modified_by_user_id",
        description="The ID of the user who last modified the activation.",
    )
    last_modified_by_user_name: Optional[str] = Field(
        default=None,
        title="last_modified_by_user_name",
        description="The name of the user who last modified the activation.",
    )
    last_modified_by_user_email: Optional[str] = Field(
        default=None,
        title="last_modified_by_user_email",
        description="The email of the user who last modified the activation.",
    )
    last_modified_by_client_id: Optional[str] = Field(
        default=None,
        title="last_modified_by_client_id",
        description="The client ID of the user who last modified the activation.",
    )

    last_publish_result: Optional[ActivationPublishStatus] = Field(
        default=None,
        title="last_publish_result",
        description="The result of the last publish operation.",
    )
    last_published: Optional[datetime] = Field(
        default=None,
        title="last_published",
        description="The date and time when the activation was last published.",
    )
    last_published_by_user_id: Optional[str] = Field(
        default=None,
        title="last_published_by_user_id",
        description="The ID of the user who last published the activation.",
    )
    last_published_by_user_name: Optional[str] = Field(
        default=None,
        title="last_published_by_user_name",
        description="The name of the user who last published the activation.",
    )
    last_published_by_user_email: Optional[str] = Field(
        default=None,
        title="last_published_by_user_email",
        description="The email of the user who last published the activation.",
    )
    last_published_by_client_id: Optional[str] = Field(
        default=None,
        title="last_published_by_client_id",
        description="The client ID of the user who last published the activation.",
    )
    last_published_fields: Optional[List[str]] = Field(
        default=[],
        title="last_published_fields",
        description="List of fields that were last published.",
    )
    last_publish_system_errors: List[str] = Field(
        default=[],
        title="last_publish_system_errors",
        description="List of system errors that occurred during the last publish operation.",
    )
    last_publish_field_errors: List[PublishErrorByField] = Field(
        default=[],
        title="last_publish_field_errors",
        description="List of field errors that occurred during the last publish operation.",
    )

    deleted: bool = Field(
        default=False,
        title="deleted",
        description="Whether the activation has been deleted.",
    )
    approved: bool = Field(
        default=False,
        title="approved",
        description="Whether the activation has been approved.",
    )
    externalIDs: dict = Field(
        default={},
        title="externalIDs",
        description="External IDs associated with the activation.",
    )
    short_id: Optional[str] = Field(
        default=None, title="short_id", description="The short ID of the activation."
    )
    is_locked: bool = Field(
        default=False,
        title="is_locked",
        description="Whether the activation is locked.",
    )
    potential_status: Optional[ActivationStatus] = Field(
        default=None,
        title="potential_status",
        description="The potential status of the activation.",
    )
    is_archived: bool = Field(
        default=False,
        title="is_archived",
        description="Whether the activation is archived.",
    )
    discarded: bool = Field(
        default=False,
        title="discarded",
        description="Whether the activation has been discarded.",
    )


class EditabilityByField(BaseModel):
    name: Optional[bool] = Field(
        default=None, title="name", description="Whether the name field is editable."
    )
    alwaysOn: Optional[bool] = Field(
        default=None,
        title="alwaysOn",
        description="Whether the alwaysOn field is editable.",
    )
    startDate: Optional[bool] = Field(
        default=None,
        title="startDate",
        description="Whether the startDate field is editable.",
    )
    endDate: Optional[bool] = Field(
        default=None,
        title="endDate",
        description="Whether the endDate field is editable.",
    )
    budgetAmount: Optional[bool] = Field(
        default=None,
        title="budgetAmount",
        description="Whether the budgetAmount field is editable.",
    )
    budgetType: Optional[bool] = Field(
        default=None,
        title="budgetType",
        description="Whether the budgetType field is editable.",
    )
    divisionBanners: Optional[bool] = Field(
        default=None,
        title="divisionBanners",
        description="Whether the divisionBanners field is editable.",
    )
    dayPartingStart: Optional[bool] = Field(
        default=None,
        title="dayPartingStart",
        description="Whether the dayPartingStart field is editable.",
    )
    dayPartingEnd: Optional[bool] = Field(
        default=None,
        title="dayPartingEnd",
        description="Whether the dayPartingEnd field is editable.",
    )
    placementType: Optional[bool] = Field(
        default=None,
        title="placementType",
        description="Whether the placementType field is editable.",
    )
    keywordBidModifierGroup: Optional[bool] = Field(
        default=None,
        title="keywordBidModifierGroup",
        description="Whether the keywordBidModifierGroup field is editable.",
    )
    biddableEntities: Optional[bool] = Field(
        default=None,
        title="biddableEntities",
        description="Whether the biddableEntities field is editable.",
    )


class Configuration(BaseModel):
    id: str = Field(title="id", description="The ID of the configuration.")
    editability_by_field: EditabilityByField = Field(
        title="editability_by_field",
        description="The editability of the fields in the configuration.",
    )

    model_config = ConfigDict(extra="allow")


class EditableField(BaseModel):
    is_editable: Optional[bool] = Field(
        default=None, title="is_editable", description="Whether the field is editable."
    )
    min_bid_amount: Optional[float] = Field(
        default=None,
        title="min_bid_amount",
        description="The minimum bid amount for the field.",
    )
    max_bid_amount: Optional[float] = Field(
        default=None,
        title="max_bid_amount",
        description="The maximum bid amount for the field.",
    )


class ConfigurationByActivation(BaseModel):
    name: Optional[EditableField] = Field(
        default=None, title="name", description="The name of the activation."
    )
    alwaysOn: Optional[EditableField] = Field(
        default=None,
        title="alwaysOn",
        description="Whether the activation is always on.",
    )
    startDate: Optional[EditableField] = Field(
        default=None, title="startDate", description="The start date of the activation."
    )
    endDate: Optional[EditableField] = Field(
        default=None, title="endDate", description="The end date of the activation."
    )
    budgetAmount: Optional[EditableField] = Field(
        default=None,
        title="budgetAmount",
        description="The amount of the budget for the activation.",
    )
    budgetType: Optional[EditableField] = Field(
        default=None,
        title="budgetType",
        description="The type of budget for the activation.",
    )
    divisionBanners: Optional[EditableField] = Field(
        default=None,
        title="divisionBanners",
        description="The banners for the activation.",
    )
    dayPartingStart: Optional[EditableField] = Field(
        None, title="dayPartingStart", description="The start time for day parting."
    )
    dayPartingEnd: Optional[EditableField] = Field(
        None, title="dayPartingEnd", description="The end time for day parting."
    )
    placementType: Optional[EditableField] = Field(
        default=None,
        title="placementType",
        description="The type of placement for the activation.",
    )
    keywordBidModifierGroup: Optional[EditableField] = Field(
        default=None,
        title="keywordBidModifierGroup",
        description="The keywords group for the activation.",
    )
    biddableEntities: Optional[EditableField] = Field(
        default=None,
        title="biddableEntities",
        description="The entities that are biddable for the activation.",
    )

    model_config = ConfigDict(extra="allow")


class Included(BaseModel):
    configuration: List[Configuration] = Field(
        title="configuration", description="List of configurations."
    )
    configuration_by_activation: Dict[str, ConfigurationByActivation] = Field(
        title="configuration_by_activation", description="Configuration by activation."
    )


class ActivationResponse(BaseModel):
    id: str = Field(title="id", description="The ID of the activation.")
    channel_config: ChannelConfig = Field(
        title="channel_config", description="The configuration for the channel."
    )
    campaign_id: str = Field(
        title="campaign_id",
        description="The ID of the campaign where the activation is",
    )
    status: ActivationStatus = Field(
        title="status", description="The status of the activation."
    )
    metadata: ActivationMetaData = Field(
        title="metadata", description="The metadata of the activation."
    )
    channel_data: Optional[Dict] = Field(
        default={}, title="channel_data", description="The data for the channel."
    )
    published_data: Optional[Dict] = Field(
        default={},
        title="published_data",
        description="The data that has been published.",
    )
    unpublished_data: Optional[Dict] = Field(
        default={},
        title="unpublished_data",
        description="The data that has not been published.",
    )

    def is_video_carousel_activation(self) -> bool:
        return self.channel_data.get("creativeType") == "VIDEO"

    def has_creative_group_entities_ids(self) -> bool:
        creative_group_entities_list: List[str] | None = self.channel_data.get("creativeGroupEntities")
        return creative_group_entities_list is not None and len(creative_group_entities_list) > 0


class ActivationResponseV2[T](BaseModel):
    data: T = Field(title="data", description="The data for the activation.")
    errors: Optional[List[ActivationErrors]] = Field(
        default=[], title="errors", description="List of errors for the activation."
    )
    warnings: Optional[List[ActivationWarnings]] = Field(
        default=[], title="warnings", description="List of warnings for the activation."
    )
    meta: Optional[Any] = Field(
        default=None, title="meta", description="Metadata for the activation."
    )
    included: Optional[Included] = Field(
        default=None, title="included", description="Included data for the activation."
    )


class ValidationError(BaseModel):
    field: str = Field(title="field", description="The field that has an error.")
    type: str = Field(title="type", description="The type of the error.")
    mismatch_description: str = Field(
        title="mismatch_description", description="Description of the mismatch."
    )


class Validation(BaseModel):
    valid: bool = Field(title="valid", description="Whether the validation is valid.")
    errors: List[ValidationError] = Field(
        title="errors", description="List of errors for the validation."
    )
