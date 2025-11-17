# https://api.8451.com/media/bid-modifiers/docs#/
from typing import List, Optional

from pydantic import BaseModel, Field


class KeywordBidModifier(BaseModel):
    keyword: str = Field(title="keyword", description="The keyword to be modified.")
    bid_modifier: float = Field(
        title="bid_modifier",
        description="The amount of boost for the keyword."
    )

class KeywordBidModifiersData(BaseModel):
    id: str = Field(title="id", description="The id of the bid modifier.")
    bid_modifier_type: str = Field(
        title="bid_modifier_type",
        description="The type of the bid modifier."
    )
    keyword_bid_modifiers: List[KeywordBidModifier] = Field(
        title="keyword_bid_modifiers",
        description="List of keyword bid modifiers."
    )
    min_bid_modifier: float = Field(title="min_bid_modifier", description="The minimum boost.")
    max_bid_modifier: float = Field(title="max_bid_modifier", description="The maximum boost.")

class KeywordBidModifiersMeta(BaseModel):
    size: int = Field(title="size", description="The number of items in the response.")


class KeywordBidModifiersResponse(BaseModel):
    data: KeywordBidModifiersData = Field(
        title="data",
        description="List of keyword bid modifiers."
    )
    meta: Optional[KeywordBidModifiersMeta] = Field(
        default=None,
        title="meta",
        description="Response metadata."
    )


class KeywordsRequest(BaseModel):
    upcs: List[str] = Field(title="upcs", description="List of UPCs.")

class KeywordsResponse(BaseModel):
    data: List[str] = Field(title="data", description="List of keywords.")

class BidModifierGroupRequest(BaseModel):
    bid_modifier_type: str = Field(
        title="bid_modifier_type",
        description="The type of the bid modifier."
    )
    keyword_bid_modifiers: List[KeywordBidModifier] = Field(
        title="keyword_bid_modifiers",
        description="List of keyword bid modifiers."
    )

class BidModifierGroupId(BaseModel):
    id: str = Field(title="id", description="The id of the bid modifier group.")

class BidModifierGroupResponse(BaseModel):
    data: BidModifierGroupId = Field(title="data", description="Id of the bid modifier group.")
    meta: Optional[KeywordBidModifiersMeta] = Field(
        default=None,
        title="meta",
        description="The number of items in the response."
    )
