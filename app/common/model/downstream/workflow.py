from typing import Optional
from pydantic import BaseModel, Field


class InitializeCampaignResponse(BaseModel):
    status: Optional[str] = Field(
        default=None,
        title="status",
        description="Status of the campaign initialization.",
    )
    businessKey: str = Field(
        title="businessKey", description="Business key of the campaign."
    )
    title: Optional[str] = Field(
        default=None, title="title", description="Title of the campaign."
    )
    header: Optional[str] = Field(
        default=None, title="header", description="Header of the campaign."
    )
