from datetime import datetime, timezone
from enum import StrEnum
from typing import List, Optional, TypeVar
from pydantic import BaseModel, Field

from app.common.model.shared import EntityMeta, Meta, DateTimeField

T = TypeVar('T')

class ErrorDateTime(BaseModel):
    value: str = Field(title="value", description="ISO time string")
    timezone: str = Field(title="timezone", description="Timezone abbreviation")

    @staticmethod
    def now():
        return ErrorDateTime(
            value=datetime.now(timezone.utc).isoformat(),
            timezone="UTC",
        )

    @staticmethod
    def from_date_time_field(date_time_field: DateTimeField):
        return ErrorDateTime(
            value=date_time_field.value,
            timezone=date_time_field.timezone,
        )

# Domain types help us understand what kind of object caused the error
class DomainType(StrEnum):
    AD_GROUP = "ad_group"
    CAMPAIGN = "campaign"
    ENTITY = "entity"
    KEYWORD = "keyword"

# This new error class provides specific information on the source of the error
class DomainError(BaseModel):
    domain: DomainType = Field(
      title="domain", description="Type of object related to this error"
    )
    id: Optional[int | str] = Field(
      default=None, title="id", description="Id of the object related to this error"
    )
    fieldName: str = Field(
      title="fieldName", description="Name of the field in the object that has an error"
    )
    code: str = Field(
      title="code", description="Generic error code"
    )
    reason: str = Field(
      title="reason", description="Human readable reason for the error"
    )
    datetime: ErrorDateTime = Field(
      title="datetime", description="Time the error occurred"
    )
    rootCauses: Optional[List['DomainError']] = Field(
      default=None, title="rootCauses", description="Root causes for this error"
    )

class SingleResponse[T](BaseModel):
    data: Optional[T] = Field(
        default=None, title="data", description="Data of the response."
    )
    meta: EntityMeta = Field(title="meta", description="Response metadata.")
    errors: Optional[List[DomainError]] = Field(
        default=None, title="errors", description="Errors for this response"
    )
    warnings: Optional[List[DomainError]] = Field(
        default=None, title="warnings", description="Warnings for this response"
    )


class ListResponse[T](BaseModel):
    data: List[T] = Field(title="data", description="List of single response data.")
    meta: Meta = Field(title="meta", description="Response metadata.")
    errors: Optional[List[DomainError]] = Field(
        default=None, title="errors", description="Errors for this response"
    )
    warnings: Optional[List[DomainError]] = Field(
        default=None, title="warnings", description="Warnings for this response"
    )

class ErrorDetail(BaseModel):
    code: str = Field(title="code", description="The error code.")
    reason: str = Field(title="reason", description="Reason for the error.")

class KrogerError(ErrorDetail):
    datetime: ErrorDateTime = Field(title="datetime", description="Time the error occurred.")
    rootCauses: List[ErrorDetail] = Field(title="rootCauses", description="List of root causes for this error.")