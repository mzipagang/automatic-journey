from typing import List, Optional

from pydantic import BaseModel, Field

from app.common.model.advertiser import AdvertiserType
from app.common.model.shared import Meta


class AdvertiserAddress(BaseModel):
    id: int = Field(default=0, title="id", description="Id of the address.")
    companyName: str = Field(default="", title="companyName", description="The name of the company the address is for.")
    addressLine1: str = Field(default="", title="addressLine1", description="The first line of the address.")
    addressLine2: str = Field(default="", title="addressLine2", description="The second line of the address.")
    city: str = Field(default="", title="city", description="The city of the address.")
    state: str = Field(default="", title="state", description="The state of the address.")
    postalCode: str = Field(default="", title="postalCode", description="The postal code of the address.")
    country: str = Field(default="", title="country", description="The country of the address.")
    addressType: AdvertiserType = Field(default=AdvertiserType.CPG, title="addressType", description="The advertiser type of the address.")
    active: bool = Field(default=True, title="active", description="Whether the address is active or not.")


class AdvertiserAddressResponse(BaseModel):
    data: List[AdvertiserAddress] = Field(title="data", description="List of Addresses.")
    meta: Meta = Field(title="meta", description="Response metadata.")


class AccountAddress(BaseModel):
    id: str = Field(default="", title="id", description="Id of the address.")
    addressType: str = Field(default="", title="addressType", description="The address type.")
    addressLines: Optional[List[str]] = Field(default="", title="addressLines", description="The address lines.")
    cityTown: str = Field(default="", title="cityTown", description="The city/town of the address.")
    stateProvince: str = Field(default="", title="stateProvince", description="The state/province of the address.")
    postalCode: str = Field(default="", title="postalCode", description="The postal code of the address.")
    countryCode: str = Field(default="", title="countryCode", description="The country code of the address.")
    status: str = Field(default="", title="status", description="The address status.")


class AccountAddressResponse(BaseModel):
    data: List[AccountAddress] = Field(title="data", description="List of Addresses.")
