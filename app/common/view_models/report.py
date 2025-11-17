from enum import Enum, StrEnum
from typing import Any, List

from pydantic import BaseModel, Field


class Dimensions(StrEnum):
    AD_GROUP_ID = "ad_group_id"
    ADVERTISER_ID = "advertiser_id"
    CAMPAIGN_ID = "campaign_id"
    ENTITY_ID = "entity_id"
    PURCHASED_ENTITY_ID = "purchased_entity_id"

class SortOrderCommon(StrEnum):
    ASC = "ASC"
    DESC = "DESC"

class FilterFields(StrEnum):
    ADVERTISER_ID = "advertiser_id"
    CAMPAIGN_ID = "campaign_id"
    AD_GROUP_ID = "ad_group_id"


class FilterOperator(StrEnum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    LIKE_IN = "LIKE_IN"
    NOT_IN = "NOT_IN"
    IS_NULL = "IS_NULL"
    NOT_NULL = "NOT_NULL"
    NOT_LIKE = "NOT_LIKE"
    BETWEEN = "BETWEEN"


class CaseInsensitiveStrEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.casefold() == value.casefold():
                    return member
        return super()._missing_(value)

class Filter(BaseModel):
    field: str = Field(title="field", description="The field to filter by")
    operator: FilterOperator = Field(
        title="operator", description="The operator to use for the filter"
    )
    values: List[str] = Field(title="values", description="The values to filter by")


class Pagination(BaseModel):
    offset: int = Field(title="offset", description="Offset from start of page")
    size: int = Field(title="size", description="Size of page")


class ReportRequestCommon(BaseModel):
    filters: List[Filter] = Field(title="filters", description="The filters to apply")
    startDate: str = Field(
        title="startDate", description="The start date of the report"
    )
    endDate: str = Field(title="endDate", description="The end date of the report")
    pagination: Pagination = Field(
        title="pagination", description="The pagination parameters"
    )
    advertiserIds: List[int] = Field(
        title="advertiserIds", description="The advertiser ids to filter by"
    )


class ReportResultHeader(BaseModel):
    name: str = Field(title="name", description="The name of the header")
    type: str = Field(title="type", description="The type of the header")
    title: str = Field(title="title", description="The title of the header")


class ReportResultResponse(BaseModel):
    headers: List[ReportResultHeader] = Field(
        title="headers", description="The headers of the report"
    )
    data: List[Any] = Field(title="data", description="The data of the report")
    totalCount: int = Field(
        title="totalCount", description="The total count of the report"
    )
