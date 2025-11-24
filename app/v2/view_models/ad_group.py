from typing import Any, List, Optional
from pydantic import Field, BaseModel, ConfigDict

from app.common.model.downstream.bid_manager import BidEntityFailure
from app.common.model.shared import BudgetType
from app.common.view_models import Entity, AdGroupStatus, KeywordBidModifier
from app.common.model.targets import TargetAdgroupRequest, Target


class AdGroupV2(BaseModel):
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
    status: Optional[AdGroupStatus] = Field(
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
    entities: Optional[List[Entity]] = Field(
        default=[],
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
    carouselHeadline: Optional[str] = Field(
        default=None,
        title="carouselHeadline",
        description="This headline is displayed above the product "
                    "cards to differentiate your Carousel from other listings"
    )
    carouselSubtext: Optional[str] = Field(
        default=None,
        title="carouselSubtext",
        description="Add subtext to carousel ad group."
    )

class AdGroupRequest(BaseModel):
    campaignId: int = Field(
        default=0,
        title="campaignId",
        description="The campaign id associated with this ad group."
    )
    name: str = Field(
        default="",
        min_length=1,
        title="name",
        description="The ad group name."
    )
    startDate: str = Field(..., title="startDate", description="The start date of the ad group.")
    endDate: Optional[str] = Field(
        default="",
        title="endDate",
        description="The end date of the ad group. "
                    "If null the ad group is considered 'always-on' "
                    "and will stop when/if the campaign has an end date."
    )
    budgetAmount: float = Field(
        default=0.0,
        title="budgetAmount",
        description="The budget of the ad group. The sum of all "
                    "the budgets from the ad group(s) may not exceed "
                    "the campaign budget."
    )
    status: AdGroupStatus = Field(..., title="status", description="The status of the ad group.")
    baseBid: float = Field(
        default=0.0,
        title="baseBid",
        description="The base bid used for all entities that have the useBaseBid "
                    "flag as true. It must be above the highers floor price "
                    "of the placement(s) selected."
    )
    entities: List[Entity] = Field(..., title="entities", description="The products to be advertised.")
    targets: List[TargetAdgroupRequest] = Field(
        ...,
        title="targets",
        description="The target dimensions for this ad group. "
                    "Includes placements, divisions, and day "
                    "parting."
    )
    carouselHeadline: Optional[str] = Field(
        default=None,
        title="headline",
        description="This headline is displayed above the product "
                    "cards to differentiate your Carousel from other listings"
    )

class AdGroupUpdateRequest(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        title="name",
        description="The ad group name."
    )
    startDate: Optional[str] = Field(
        default=None,
        title="startDate",
        description="The start date of the ad group."
    )
    endDate: Optional[str] = Field(
        default="",
        title="endDate",
        description="The end date of the ad group. "
                    "If null the ad group is considered 'always-on' "
                    "and will stop when/if the campaign has an end date."
    )
    budgetAmount: Optional[float] = Field(
        default=None,
        title="budgetAmount",
        description="The budget of the ad group. The sum of all "
                    "the budgets from the ad group(s) may not exceed "
                    "the campaign budget."
    )
    status: Optional[AdGroupStatus] = Field(
        default=None,
        title="status",
        description="The status of the ad group."
    )
    targets: Optional[List[TargetAdgroupRequest]] = Field(
        default=None,
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
    model_config = ConfigDict(extra="forbid")
    carouselHeadline: Optional[str] = Field(
        default=None,
        title="headline",
        description="This headline is displayed above the product "
                    "cards to differentiate your Carousel from other listings"
    )

class AdGroupUpdateRequestV2(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        title="name",
        description="The ad group name."
    )
    startDate: Optional[str] = Field(
        default=None,
        title="startDate",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="The start date of the ad group."
    )
    endDate: Optional[str] = Field(
        default="",
        title="endDate",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="The end date of the ad group. "
                    "If null the ad group is considered 'always-on' "
                    "and will stop when/if the campaign has an end date."
    )
    budgetAmount: Optional[float] = Field(
        default=None,
        title="budgetAmount",
        gt=0,
        description="The budget of the ad group. The sum of all "
                    "the budgets from the ad group(s) may not exceed "
                    "the campaign budget."
    )
    status: Optional[AdGroupStatus] = Field(
        default=None,
        title="status",
        description="The status of the ad group."
    )
    targets: Optional[List[TargetAdgroupRequest]] = Field(
        default=None,
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
    carouselHeadline: Optional[str] = Field(
        default=None,
        title="headline",
        description="This headline is displayed above the product "
                    "cards to differentiate your Carousel from other listings"
    )
    carouselSubtext: Optional[str] = Field(
        default=None,
        title="carouselSubtext",
        description="Add subtext to carousel ad group."
    )
    model_config = ConfigDict(extra="forbid")

class AdGroupV2Request(BaseModel):
    campaignId: int = Field(
        ...,
        title="campaignId",
        description="The campaign id associated with this ad group."
    )
    name: str = Field(
        ...,
        min_length=1,
        title="name",
        description="The ad group name."
    )
    startDate: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        title="startDate",
        description="The start date of the ad group."
    )
    endDate: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        title="endDate",
        description="The end date of the ad group. "
                    "If null the ad group is considered 'always-on' "
                    "and will stop when/if the campaign has an end date."
    )
    budgetAmount: float = Field(
        default=...,
        gt=0,
        title="budgetAmount",
        description="The budget of the ad group. The sum of all "
                    "the budgets from the ad group(s) may not exceed "
                    "the campaign budget."
    )
    status: AdGroupStatus = Field(..., title="status", description="The status of the ad group.")
    baseBid: float = Field(
        default=0.0,
        title="baseBid",
        description="The base bid used for all entities that have the useBaseBid "
                    "flag as true. It must be above the highers floor price "
                    "of the placement(s) selected."
    )
    entities: Optional[List[Entity]] = Field(
        default=[],
        title="entities",
        description="The products to be advertised."
    )
    targets: List[TargetAdgroupRequest] = Field(
        ...,
        title="targets",
        min_length=1,
        description="The target dimensions for this ad group. "
                    "Includes placements, divisions, and day "
                    "parting."
    )
    carouselHeadline: Optional[str] = Field(
        default=None,
        title="headline",
        description="This headline is displayed above the product "
                    "cards to differentiate your Carousel from other listings"
    )
    carouselSubtext: Optional[str] = Field(
        default=None,
        title="carouselSubtext",
        description="Add subtext to carousel ad group."
    )

class AdGroupV2Response[T](BaseModel):
    data: T = Field(title="data", description="The data for the ad group.")
    carouselHeadline: Optional[str] = Field(
        default=None,
        title="carouselHeadline",
        description="This headline is displayed above the product "
                    "cards to differentiate your Carousel from other listings"
    )
    meta: Optional[Any] = Field(
        default=None, title="meta", description="Metadata for the adgroup."
    )

class SecretAdGroupUpdateRequest(AdGroupUpdateRequestV2):
    budgetType: BudgetType = Field(..., description="The type of budget.")

class AdGroupFromActivation[T](BaseModel):
    adGroup: T = Field(title="adgroup", description="The ad group data.")
    entityErrors: List[BidEntityFailure] = Field(title="entityErrors", description="The entity errors for the ad group.")
