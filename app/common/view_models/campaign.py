from typing import Any, Dict, Optional
from enum import StrEnum

from pydantic import BaseModel, Field

from app.common.model.shared import BudgetType

DATE_PATTERN = r"\d{4}-\d{2}-\d{2}"


class CampaignStatus(StrEnum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    PAUSED = "PAUSED"


class PacingType(StrEnum):
    EVEN = "EVEN"
    ASAP = "ASAP"
    AHEAD = "AHEAD"


class WorkflowActions(StrEnum):
    CAMPAIGN_CREATE = "CAMPAIGN_CREATE"


class CampaignPutRequest(BaseModel):
    name: str = Field(description="The campaign name.")
    status: Optional[CampaignStatus] = Field(
        None,
        description="The status of the campaign. "
        "Can not be changed at the same time as endDate. "
        "To cancel a scheduled campaign, set the status to PAUSE "
        "and set the end date to match the start date.",
    )
    startDate: Optional[str] = Field(
        None,
        description="The start date of the campaign. "
        "Can only be changed when status is DRAFT. "
        "Can not be changed at the same time as status. "
        "Format: YYYY-MM-DD",
        pattern=DATE_PATTERN,
    )
    endDate: Optional[str] = Field(
        description="The end date of the campaign. Must be after start date. "
        "A live campaign can be stopped by setting end date to today's date. "
        'If null the campaign is considered "always-on". '
        "Cannot be null if budget type is LIFETIME",
        pattern=DATE_PATTERN,
        default="",
    )
    budgetAmount: float = Field(
        description="The total budget of the campaign. "
        "The sum of all the budgets from the ad group(s) may not exceed this number.",
        ge=1,
    )
    budgetType: Optional[BudgetType] = Field(
        None,
        description="The type of budget. Can only be changed when status is DRAFT.",
    )
    pacingType: PacingType = Field(description="The pacing for the campaign.")
    billingInsertionOrder: Optional[str] = Field(
        None,
        description="Insertion order number for this campaign. Can only be changed when status is DRAFT.",
    )
    billingPurchaseOrder: Optional[str] = Field(
        None,
        description="Purchase order number for this campaign. Can only be changed when status is DRAFT.",
    )
    billingAdditionalDetails: Optional[str] = Field(
        description="Notes that the advertiser wants to notify the billing department.",
        default=None,
    )


class PatchOperation(BaseModel):
    op: str = Field(
        title="op",
        description="The operation to perform. Must be one of: add, remove, replace.",
    )
    path: str = Field(
        title="path", description="The path to the field to modify. Must start with /."
    )
    value: Optional[Any] = Field(
        default=None, title="value", description="The value to set the field to."
    )

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return super().model_dump(*args, exclude_none=True, **kwargs)
