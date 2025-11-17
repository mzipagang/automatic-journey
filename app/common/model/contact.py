from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer

from app.common.model.advertiser import AdvertiserType
from app.common.model.shared import Meta


class InternalContactType(StrEnum):
    ACCOUNT_EXECUTIVE: str = "ACCOUNT_EXECUTIVE"
    PRIMARY_ACCOUNT_MANAGER: str = "PRIMARY_ACCOUNT_MANAGER"


class AdvertiserContact(BaseModel):
    id: int = Field(default=0, title="id", description="Id of this contact.")
    firstName: Optional[str] = Field(
        default="", title="firstName", description="First name of this contact."
    )
    lastName: Optional[str] = Field(
        default="", title="lastName", description="Last name of this contact."
    )
    email: str = Field(
        default="", title="email", description="Email address of this contact."
    )
    contactType: AdvertiserType = Field(
        default=AdvertiserType.CPG, title="contactType", description="Type of contact."
    )
    active: bool = Field(
        default=True,
        title="active",
        description="Whether this contact is active or not.",
    )
    accountIds: List[str] = Field(
        default=[],
        title="accountIds",
        description="List of account ids this contact belongs to.",
    )

    @field_serializer('firstName', 'lastName')
    def serialize_name(
            self,
            name: Optional[str],
    ) -> str:
        return name or ""


class AdvertiserContactResponse(BaseModel):
    data: List[AdvertiserContact] = Field(title="data", description="List of Contacts")
    meta: Meta = Field(title="meta", description="Response metadata.")


class InternalContact(BaseModel):
    type: str = Field(default="", title="type", description="Type of contact.")
    id: str = Field(default="", title="id", description="Id of this contact.")
