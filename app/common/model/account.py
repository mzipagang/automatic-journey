from typing import List

from pydantic import BaseModel, Field

from app.common.model.shared import Meta


class InternalAccount(BaseModel):
    id: str = Field("", description="Internal Account ID number.")
    name: str = Field("", description="Name of the Internal Account.")
    active: bool = Field(True, description="Is the Internal Account active, True/False.")


class Account(BaseModel):
    id: int = Field("", title="id", description="Account ID number.")
    name: str = Field("", title="name", description="Name of the Account.")
    active: bool = Field(True, title="active", description="Is the Account active, True/False.")


class AccountResponse(BaseModel):
    data: List[Account] = Field(title="data", description="List of Accounts.")
    meta: Meta = Field(title="meta", description="Response metadata.")
