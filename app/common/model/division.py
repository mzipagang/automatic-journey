from typing import List

from pydantic import BaseModel, Field

from app.common.model.shared import Meta


class Division(BaseModel):
    id: int = Field(default=0, title="id", description="Id of the division")
    name: str = Field(default="", title="name", description="Name of the division")
    active: bool = Field(default=True, title="active", description="Whether the division is active")


class DivisionResponse(BaseModel):
    data: List[Division] = Field(title="data", description="List of Divisions.")
    meta: Meta = Field(title="meta", description="Response metadata.")

class DivisionServiceResponse(BaseModel):
    id: str = Field(default="", title="id", description="Id of the division")
    label: str = Field(default="", title="label", description="Label of the division")
    preselected: bool = Field(
        default=False,
        title="preselected",
        description="Whether the division is preselected"
    )
    disabled: bool = Field(
        default=False,
        title="disabled",
        description="Whether the division is disabled"
    )
    flagged: bool = Field(
        default=False,
        title="flagged",
        description="Whether the division is flagged"
    )
    type: str = Field(
        default="division",
        title="type",
        description="Type of the division"
    )
    divisionNumber: str = Field(
        default="",
        title="division_number",
        description="Number of the division"
    )
    bannerCode: str = Field(
        default="",
        title="banner_code",
        description="Code of the banner associated with the division"
    )

# Used in division service to organize caching division lookups
class DivisionData(BaseModel):
    division: DivisionServiceResponse
    division_id: int | None
