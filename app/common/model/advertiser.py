from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.common.model.shared import Meta


class AdvertiserType(StrEnum):
    CPG = "CPG"
    AGENCY = "AGENCY"


class CachedAdvertiser(BaseModel):
    id: int = Field(default=0, title="id", description="The id of the advertiser.")
    brandId: str = Field(
        default="", title="brandId", description="The brand id of the advertiser."
    )
    name: str = Field(
        default="", title="name", description="The name of the advertiser."
    )
    accountId: int = Field(
        default=0, title="accountId", description="The account id of the advertiser."
    )
    description: str = Field(
        default="",
        title="description",
        description="The description of the advertiser.",
    )
    active: bool = Field(
        default=True, title="active", description="Whether the advertiser is active."
    )


class Advertiser(BaseModel):
    id: int = Field(default=0, title="id", description="The id of the advertiser.")
    name: str = Field(
        default="", title="name", description="The name of the advertiser."
    )
    accountId: int = Field(
        default=0, title="accountId", description="The account id of the advertiser."
    )
    description: str = Field(
        default="",
        title="description",
        description="The description of the advertiser.",
    )
    active: bool = Field(
        default=True, title="active", description="Whether the advertiser is active."
    )


class AdvertiserResponse(BaseModel):
    data: List[Advertiser] = Field(title="data", description="List of Advertisers.")
    meta: Meta = Field(title="meta", description="Response metadata.")

class CachedAdvertiserResponse(BaseModel):
    data: List[CachedAdvertiser] = Field(title="data", description="List of Advertisers.")


class KoddiAdvertiser(BaseModel):
    brandIds: List[str] = Field(title="brandIds", description="List of brand ids.")
    koddiId: int = Field(title="koddiId", description="The koddi id of the advertiser.")
    agencyId: Optional[str] = Field(
        default=None, title="agencyId", description="The agency id"
    )
    primaryBrandId: str = Field(
        title="primaryBrandId", description="The primary brand id of the advertiser."
    )
