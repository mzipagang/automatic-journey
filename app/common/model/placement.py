from enum import StrEnum
from typing import List

from pydantic import BaseModel, Field
from app.common.model.shared import Meta

class PlacementType(StrEnum):
    SEARCH_AND_BROWSE = "Search & Browse"
    SEARCH_AND_BROWSE_PPC = "Search & Browse PPC"
    BASKET_BUILDER = "Basket Builder"
    SAVINGS = "Savings"
    # TOA specific placement types
    SHOP_AND_DISCOVER = "Shop & Discover"
    IN_STORE = "In Store"

class Placement(BaseModel):
    id: int = Field(default=0, title="id", description="Id of the placement")
    name: str = Field(default="", title="name", description="Name of the placement")
    description: str = Field(default="", title="description", description="Description of the placement")
    active: bool = Field(default=True, title="active", description="Whether the placement is active")
    priceFloor: float = Field(default=0.0, title="priceFloor", description="Price floor of the placement")


class PlacementResponse(BaseModel):
    data: List[Placement] = Field(title="data", description="List of Placements.")
    meta: Meta = Field(title="meta", description="Response metadata.")
