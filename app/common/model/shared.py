from __future__ import annotations

from enum import StrEnum
from typing import Dict, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')
M = TypeVar('M')


class SingleDataResponse[T, M](BaseModel):
    data: Optional[T]
    meta: M

class ListDataResponse[T, M](BaseModel):
    data: List[T]
    meta: M

class IgnoreCaseStrEnum(StrEnum):
    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.value.lower() == str(value).lower():
                return member
        return None

class BudgetType(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    LIFETIME = "LIFETIME"


class InternalBudgetType(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"

class CampaignType(IgnoreCaseStrEnum):
    PLA = "PLA" # Product Listing Ad
    TOA = "TOA" # Targeted Onsite Ad
    CAROUSEL = "CAROUSEL"

class InternalCampaignType(IgnoreCaseStrEnum):
    PLA = "PLA"
    TOA = "TOA"
    CAROUSEL = "CAROUSEL"
    IN_CAROUSEL = "PROMOTED_PRODUCTS_CAROUSEL"
    CS_CAROUSEL = "Promoted_Products_Carousel"
    BM_CAROUSEL = "PPC"

class BidManagerCampaignType(StrEnum):
    PLA = "PLA"  # Product Listing Ad
    TOA = "TOA"  # Targeted Onsite Ad
    CAROUSEL = "PPC"  # Promoted Products Carousel


class Page(BaseModel):
    offset: int = Field(
        default=0, title="offset", description="Offset from start of page"
    )
    size: int = Field(default=10, title="size", description="Size of page")
    hasMore: bool = Field(
        default=False, title="hasMore", description="Whether there are more pages"
    )


class Meta(BaseModel):
    page: Page = Field(title="page", description="Pagination information")


class DateTimeField(BaseModel):
    value: str = Field(title="value", description="Date and time value")
    timezone: str = Field(
        title="timezone", description="Timezone of the date and time value"
    )


class ActivationErrors(BaseModel):
    code: str = Field(title="code", description="Error code")
    reason: str = Field(title="reason", description="Error reason")
    datetime: DateTimeField = Field(
        title="datetime", description="Date and time of the error"
    )
    field_name: str = Field(
        title="field_name", description="Field name associated with the error"
    )
    identifier: str = Field(
        title="identifier", description="Identifier associated with the error"
    )


class ActivationWarnings(BaseModel):
    code: str = Field(title="code", description="Warning code")
    reason: str = Field(title="reason", description="Warning reason")
    datetime: DateTimeField = Field(
        title="datetime", description="Date and time of the warning"
    )
    field_name: str = Field(
        title="field_name", description="Field name associated with the warning"
    )
    identifier: str = Field(
        title="identifier", description="Identifier associated with the warning"
    )


class UpstreamValidationWarning(BaseModel):
    detail: Optional[List[str]] = Field(
        None, title="detail", description="Details about the validation warnings."
    )
    path: Optional[str] = Field(
        None,
        title="path",
        description="JSON path to the field with a validation warning.",
    )

    @staticmethod
    def from_upstream_campaign_validations(warnings):
        return UpstreamValidationWarning(
            detail=warnings.detail, path=warnings.path
        )

    @staticmethod
    def from_upstream_activation_validations(warnings: ActivationWarnings):
        return UpstreamValidationWarning(
            detail=[warnings.reason], path=warnings.field_name
        )


class Warnings(BaseModel):
    validation: Optional[List[UpstreamValidationWarning]] = Field(
        default=None, title="validation", description="List of validation warnings."
    )


class PublishStatus(StrEnum):
    EMPTY = "EMPTY"
    PENDING = "PENDING"
    FAILED = "FAILED"
    PUBLISHED = "PUBLISHED"


class InternalPublishStatus(StrEnum):
    EMPTY = "EMPTY"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DELIVERY_PENDING = "DELIVERY_PENDING"
    DELIVERY_SUCCESS = "DELIVERY_SUCCESS"


class ActivationPublishStatus(StrEnum):
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


class EntityMeta(BaseModel):
    success: bool = Field(
        ..., title="success", description="Whether the entity request was successful."
    )
    message: Optional[str] = Field(
        None,
        title="message",
        description="Error message if the request was not successful.",
    )
    code: Optional[int] = Field(
        None, title="code", description="Error code if the request was not successful."
    )
    publishStatus: Optional[PublishStatus] = Field(
        None, title="publishStatus", description="Publish status of the entity."
    )
    errors: Optional[List[Dict]] = Field(
        [],
        title="errors",
        description="List of errors if the request was not successful.",
    )
    warnings: Optional[Warnings] = Field(
        None, title="warnings", description="Upstream validation warnings."
    )


class KeywordsMeta(BaseModel):
    size: int = Field(..., title="size", description="Size of keywords list.")
    message: Optional[str] = Field(
        None,
        title="message",
        description="Error message if the request was not successful.",
    )
