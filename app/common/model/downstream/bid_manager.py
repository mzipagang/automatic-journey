from enum import IntEnum
from typing import List, Any, Optional, Union, Annotated, Literal

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.common.model.campaign_types import (
    InternalCampaignType,
    BidManagerCampaignType,
    serialize_campaign_type,
    parse_campaign_type
)


# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/entity/SuggestedBid.java
class SuggestedBid(BaseModel):
    lowest_bid: Optional[float] = None
    highest_bid: Optional[float] = None

class Suggestion(BaseModel):
    id: str
    bid_information: Optional[SuggestedBid] = None

class SuggestionsResponse(BaseModel):
    suggestions: List[Suggestion] = []

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/entity/Recommendation.java
class Recommendation(BaseModel):
    id: str
    use_base_bid: Optional[bool] = None
    bid_amount: Optional[float] = None
    suggested_bid: Optional[SuggestedBid] = None

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/entity/TOARecommendation.java
class TOARecommendation(Recommendation):
    department: Optional[str] = None
    commodity: Optional[str] = None
    sub_commodity: Optional[str] = None
    type: Optional[str] = None

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/entity/PLARecommendation.java
class PLARecommendation(Recommendation):
    name: Optional[str] = None
    department: Optional[str] = None
    commodity: Optional[str] = None
    sub_commodity: Optional[str] = None

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/entity/BidRange.java
class BidRange(BaseModel):
    minimum_value: Optional[float] = None
    maximum_value: Optional[float] = None

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/entity/Bid.java
class Bid(BaseModel):
    id: str
    bid_amount: Optional[float] = None
    additionalProperties: Optional[dict[str, Any]] = None

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/dto/RecommendationsResponseData.java
class RecommendationsResponseData(BaseModel):
    type: Optional[str] = None
    bidReferenceId: str
    pla_recommendations: Optional[List[PLARecommendation]] = Field(default=[])
    pla_bid_range: Optional[BidRange] = None
    toa_recommendations: Optional[List[TOARecommendation]] = Field(default=[])
    bid: List[Bid] = Field(default=[])
    default_bid: float = Field(default=0.0)

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/dto/BidRecommendationResponseMultipleData.java
class BidRecommendationResponseMultipleData(BaseModel):
    found: List[RecommendationsResponseData] = Field(default=[])
    notFound: List[str] = Field(default=[])

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/dto/BidRecommendationResponseMultiple.java
class BidRecommendationResponseMultiple(BaseModel):
    data: BidRecommendationResponseMultipleData

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/dto/BidsResponseData.java#L15
class BidsResponseData(BaseModel):
    id: str
    type: InternalCampaignType
    bids: List[Bid]
    default_bid: float = Field(default=0.0)

    @field_validator("type", mode="before")
    @classmethod
    def validate_upstream_campaign_type(cls, value: Any) -> InternalCampaignType | None:
        return parse_campaign_type(value, BidManagerCampaignType)

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/dto/MultipleBidsResponseData.java#L13
class MultipleBidsResponseData(BaseModel):
    found: List[BidsResponseData] = Field(default=[], description="list of bids that were found")
    notFound: List[str] = Field(default=[], description='List of bids that were not found.')


# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/dto/MultipleBidsResponse.java#L12
class MultipleBidsResponse(BaseModel):
    data: MultipleBidsResponseData

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/dto/ValidationRequestDTO.java#L7
class ValidateBidRequest(BaseModel):
    minimumBidAmount: Optional[float] = None
    maximumBidAmount: Optional[float] = None
    minimumBidCount: Optional[int] = None
    maximumBidCount: Optional[int] = None
    bidIdsMustHaveValidEntities: Optional[bool] = None
    brandCodes: Optional[List[str]] = None

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/modals/BidFailure.java#L12
class BidFailure(BaseModel):
    field: str
    message: str

class BidEntityFailure(BaseModel):
    field: str
    message: str
    entity_id: Optional[str] = None

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/IncorrectBidAmountFailureDTO.java#L8
class IncorrectBidAmountFailure(BaseModel):
    type: Literal["incorrect-bid-amount-failure"] = "incorrect-bid-amount-failure"
    bid_failures: List[BidFailure] = Field(alias="bidFailures")

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/IncorrectDefaultBidAmountFailureDTO.java#L7
class IncorrectDefaultBidAmountFailure(BaseModel):
    type: Literal["incorrect-default-bid-amount-failure"] = "incorrect-default-bid-amount-failure"
    bid_failures: BidFailure = Field(alias="bidFailures")

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/EmptyBidFailureDTO.java#L7
class EmptyBid(BaseModel):
    type: Literal["empty-bid-failure"] = "empty-bid-failure"
    bid_failure: BidFailure = Field(alias="bidFailure")

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/IncorrectBidsDTO.java#L8
class IncorrectBids(BaseModel):
    type: Literal["incorrect-bid-failure"] = "incorrect-bid-failure"
    bid_failure_list: List[BidFailure] = Field(alias="bidFailureList")

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/IncorrectMaxBidDTO.java#L8
class IncorrectMaxBid(BaseModel):
    type: Literal["incorrect-max-bid-failure"] = "incorrect-max-bid-failure"
    bid_failure_list: List[BidFailure] = Field(alias="bidFailureList")

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/IncorrectMinBidDTO.java#L8
class IncorrectMinBid(BaseModel):
    type: Literal["incorrect-min-bid-failure"] = "incorrect-min-bid-failure"
    bid_failure_list: List[BidFailure] = Field(alias="bidFailureList")

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/IncorrectMaxBidCountDTO.java#L8
class IncorrectMaxBidCount(BaseModel):
    type: Literal["incorrect-max-bid-count-failure"] = "incorrect-max-bid-count-failure"
    bid_failure_list: List[BidFailure] = Field(alias="bidFailureList")

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/service/validation/dto/IncorrectMinBidCountDTO.java#L8
class IncorrectMinBidCount(BaseModel):
    type: Literal["incorrect-min-bid-count-failure"] = "incorrect-min-bid-count-failure"
    bid_failure_list: List[BidFailure] = Field(alias="bidFailureList")

BidValidationFailure = Annotated[
    Union[
        IncorrectBidAmountFailure,
        IncorrectDefaultBidAmountFailure,
        EmptyBid,
        IncorrectBids,
        IncorrectMaxBid,
        IncorrectMinBid,
        IncorrectMaxBidCount,
        IncorrectMinBidCount
    ],
    Field(discriminator="type")
]

# https://github.com/8451LLC/map-bid-mgmt/blob/main/src/main/java/com/e451/bid_management/exception/ValidationException.java#L7
class BidValidationFailureResponse(BaseModel):
    status: str
    code: str
    message: str
    errors: List[BidValidationFailure]

class BidValidationResponse(BaseModel):
    valid: bool
    errors: Optional[List[BidValidationFailure]] = None
    invalid_upcs: Optional[List[str]] = None

class CreateBidsRequest(BaseModel):
    type: InternalCampaignType
    bids: List[Bid]
    default_bid: float = Field(default=0.0)

    @field_serializer('type')
    def serialize_type(self, campaign_type: InternalCampaignType) -> BidManagerCampaignType | None:
        return serialize_campaign_type(campaign_type, BidManagerCampaignType)

class CreateBidsResponse(BaseModel):
    id: str

class BidIdentifier(BaseModel):
    upc: str
    entity_id: str
    bid_group_id: str

class ValidatedBidIdentifiers(BaseModel):
    valid: Optional[List[BidIdentifier]] = []
    invalid: Optional[List[BidIdentifier]] = []
    errors: Optional[List[BidEntityFailure]] = []

class ValidationResponse(BaseModel):
    filtered_entities: List[Any]
    default_bid: float
    errors: List[BidEntityFailure]


class MinCarouselUpcCount(IntEnum):
    THREE_UPC = 3

# Used in bid manager service to organize caching upc lookups
class BidData(BaseModel):
    bid: Bid
    entity_id: int | None
    product: str | None
