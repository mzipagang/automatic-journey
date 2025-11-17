from enum import StrEnum
from typing import Optional, List
from pydantic import BaseModel, Field

from app.common.model.shared import BudgetType, KeywordsMeta
from app.common.model.targets import Target


class AdGroupStatus(StrEnum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    UNDER_REVIEW = "UNDER REVIEW"

class Entity(BaseModel):
    id: int = Field(..., title="id", description="Entity id")
    useBaseBid: bool = Field(..., title="useBaseBid", description="Whether to use base bid.")
    bidAmount: Optional[float] = Field(default=None, title="bidAmount", description="Bid amount for this entity.")
    deleted: bool = Field(..., title="deleted", description="Whether this entity is deleted.")

    def __hash__(self):
        return hash((self.id, self.useBaseBid, self.bidAmount, self.deleted))

class KeywordBidModifier(BaseModel):
    keyword: str = Field(..., title="keyword", description="Keyword to modify.")
    modifier: float = Field(..., title="modifier", description="Modifier value for this keyword.")
    deleted: Optional[bool] = Field(None, title="deleted", description="Whether this keyword is deleted.")

    def __hash__(self):
        return hash((self.keyword, self.modifier, self.deleted))

class AdGroup(BaseModel):
    adGroupId: Optional[int] = Field(
        default=None,
        title="adGroupId",
        description="Id that identified the Ad Group."
    )
    campaignId: Optional[int] = Field(
        default=None,
        title="campaignId",
        description="The campaign id associated with this ad group."
    )
    name: Optional[str] = Field(
        default=None,
        title="name",
        description="The ad group name."
    )
    startDate: Optional[str] = Field(
        default="",
        title="startDate",
        description="The start date of the ad group."
    )
    endDate: Optional[str] = Field(
        default=None,
        title="endDate",
        description="The end date of the ad group. "
                    "If null the ad group is considered 'always-on' "
                    "and will stop when/if the campaign has an end date."
    )
    budgetType: BudgetType | None = Field(
        default=None,
        title="budgetType",
        description="The type of budget."
    )
    budgetAmount: Optional[float] = Field(
        default=None,
        title="budgetAmount",
        description="The budget of the ad group. The sum of all "
                    "the budgets from the ad group(s) may not exceed "
                    "the campaign budget."
    )
    status: Optional[str] = Field(
        default=None,
        title="status",
        description="The status of the ad group."
    )
    baseBid: Optional[float] = Field(
        default=None,
        title="baseBid",
        description="The base bid used for all entities that have the useBaseBid "
                    "flag as true. It must be above the highers floor price "
                    "of the placement(s) selected."
    )
    entities: List[Entity] = Field(
        ...,
        title="entities",
        description="The products to be advertised."
    )
    targets: List[Target] = Field(
        ...,
        title="targets",
        description="The target dimensions for this ad group. "
                    "Includes placements, divisions, and day "
                    "parting."
    )
    keywordBidModifiers: Optional[List[KeywordBidModifier]] = Field(
        default=None,
        title="keywordBidModifiers",
        description="Adjustments to keyword bids."
    )
    isArchived: Optional[bool] = Field(
        default=None,
        title="isArchived",
        description="Whether this ad group is archived."
    )

    def model_dump(self, *args, **kwargs):
        ad_group = super().model_dump(*args, **kwargs)
        ad_group['targets'] = [target.model_dump() for target in self.targets]
        return ad_group


class EntitiesRequest(BaseModel):
    baseBid: Optional[float] = Field(
        default=None,
        title="baseBid",
        description="The base bid used for all entities that have useBaseBid set to true."
    )
    entities: List[Entity] = Field(
        ...,
        title="entities",
        description="The products to be advertised."
    )


class KeywordBidModifiersRequest(BaseModel):
    keywordBidModifiers: List[KeywordBidModifier] = Field(
        ...,
        title="keywordBidModifiers",
        description="A list of KeywordBidModifiers."
    )


class KeywordsResponse(BaseModel):
    data: List[str] = Field(..., title="data", description="List of keywords.")
    meta: KeywordsMeta = Field(..., title="meta", description="Metadata about the list of keywords.")
