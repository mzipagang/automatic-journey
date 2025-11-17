# https://api.8451.com/location-groups/docs#/
from typing import List, Optional

from pydantic import BaseModel, Field


class DivisionBannerItem(BaseModel):
    bannerCode: str = Field(
        title="bannerCode", description="The banner code of the division."
    )
    divisionNumber: str = Field(
        title="divisionNumber", description="The division number"
    )


class LocationGroupCategory(BaseModel):
    type: str = Field(
        title="type", description="The type of the location group category."
    )
    items: List[DivisionBannerItem] = Field(
        title="items",
        description="The list of division banner items in the location group category.",
    )


class LocationGroup(BaseModel):
    id: str = Field(title="id", description="The id of the location group.")
    categories: List[LocationGroupCategory] = Field(
        title="categories", description="The list of categories in the location group."
    )


class LocationGroupResponseData(BaseModel):
    found: Optional[List[LocationGroup]] = Field(
        default=[], title="found", description="List of location groups found."
    )
    notFound: Optional[List[str]] = Field(
        default=[], title="notFound", description="List of location groups not found."
    )


class LocationGroupResponse(BaseModel):
    data: LocationGroupResponseData = Field(
        title="data",
        description="Response data containing found and not found location groups.",
    )
