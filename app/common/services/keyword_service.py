from typing import List, Tuple

from fastapi import Depends, HTTPException

from app.common.model.downstream.bid_modifiers import KeywordsRequest, BidModifierGroupRequest
from app.common.services.lookup_service import LookupService
from app.common.view_models import KeywordBidModifier
from app.common.gateways.keyword_bidding_gateway import KeywordBiddingGateway
from app.common.model.shared import UpstreamValidationWarning
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger
from app.v2.view_models.ad_group import AdGroupV2

logger = filtered_logger.get_logger(__name__)


class KeywordService:
    __external_api_http_client: ExternalApiHttpClientService
    keyword_bidding_gateway: KeywordBiddingGateway
    lookup: LookupService

    def __init__(
            self,
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            keyword_bidding_gateway: KeywordBiddingGateway = Depends(KeywordBiddingGateway),
            lookup: LookupService = Depends(LookupService),
    ):
        self.__external_api_http_client = external_api_http_client_service
        self.keyword_bidding_gateway = keyword_bidding_gateway
        self.lookup = lookup

    @staticmethod
    def get_keyword_bid_modifier_group_payload(keyword_bid_modifiers: List[KeywordBidModifier]):
        payload = {
            "bid_modifier_type": "boost",
            "keyword_bid_modifiers": list[dict]
        }

        keyword_bid_modifiers_payload = []
        for keyword_bid_modifier in keyword_bid_modifiers:
            keyword_bid_modifiers_payload.append({
                "keyword": keyword_bid_modifier.keyword,
                "bid_modifier": keyword_bid_modifier.modifier
            })

        payload["keyword_bid_modifiers"] = tuple(keyword_bid_modifiers_payload)

        return payload

    async def create_keyword_bid_modifier_group(self, payload: dict) -> str:
        response = await self.keyword_bidding_gateway.create_keyword_bid_modifier_group(BidModifierGroupRequest(**payload))

        if response.data and response.data.id:
            return response.data.id

        raise HTTPException(status_code=400, detail="Failed to create keyword bid modifier group")

    async def build_keyword_bid_modifier_group(self, ad_group_keyword_bid_modifiers: List[KeywordBidModifier]) -> str:
        keyword_bid_modifier_group = self.get_keyword_bid_modifier_group_payload(ad_group_keyword_bid_modifiers)
        logger.info('Keyword Bid Modifier Group: %s', keyword_bid_modifier_group)
        keyword_bid_modifier_group_id = await self.create_keyword_bid_modifier_group(keyword_bid_modifier_group)
        logger.info('Keyword Bid Modifier Group Id: %s', keyword_bid_modifier_group_id)
        return keyword_bid_modifier_group_id

    async def get_eligible_keywords_from_upcs(self, upcs: list) -> set[str]:
        logger.info("Getting eligible keywords")
        if len(upcs) == 0:
            logger.warning("Cannot get keywords without UPCs")
            raise HTTPException(status_code=400, detail="Cannot get keywords without UPCs")

        keywords_request = KeywordsRequest(upcs=upcs)

        try:
            response = await self.keyword_bidding_gateway.get_eligible_keywords(keywords_request)
            if response.data:
                return set(response.data)
            return []
        except HTTPException as e:
            logger.error("Failed to get eligible keywords: %s", e.detail)
            raise e

    async def get_bid_modifiers(self, keyword_bid_modifier_group_id: str | None) -> List[KeywordBidModifier]:
        """
        Get a list of keyword bid modifiers with the given keyword_bid_modifier_group_id
        """
        if keyword_bid_modifier_group_id is None:
            return []

        keyword_bid_modifier_group_response = (
            await self.keyword_bidding_gateway.get_keyword_bid_modifier_group(
                keyword_bid_modifier_group_id
            )
        )
        bid_modifiers = keyword_bid_modifier_group_response.data.keyword_bid_modifiers

        return [
            KeywordBidModifier(
                keyword=bid_modifier.keyword,
                modifier=bid_modifier.bid_modifier,
                deleted=False
            )
            for bid_modifier in bid_modifiers
        ]

    async def get_keyword_bid_modifiers(self, keyword_bid_modifier_group_id: str):
        logger.info("Getting data of keyword bid modifier group: %s", keyword_bid_modifier_group_id)
        try:
            keyword_bid_modifier_group_response = await self.keyword_bidding_gateway.get_keyword_bid_modifier_group(
                keyword_bid_modifier_group_id
            )

            if keyword_bid_modifier_group_response.data is not None:
                logger.info("Received Keyword Bid Modifier Group: %s", keyword_bid_modifier_group_response.data)
                return [
                    KeywordBidModifier(
                        keyword=bid_modifier.keyword,
                        modifier=bid_modifier.bid_modifier,
                    )
                    for bid_modifier in keyword_bid_modifier_group_response.data.keyword_bid_modifiers
                ]

            logger.error("Unprocessable keyword bid modifier group %s", keyword_bid_modifier_group_id)
            raise KeyError("targets-type")
        except KeyError as ex:
            logger.warning("KeyError Exception while parsing keywordBidModifierGroup id: %s", str(ex))
            raise KeyError("targets") from ex

    async def update_keywords(
            self,
            ad_group: AdGroupV2,
            keyword_bid_modifier_updates: List[KeywordBidModifier]
    ) -> Tuple[str | None, List[UpstreamValidationWarning]]:
        keyword_modifiers = self.merge_keywords(
            ad_group.keywordBidModifiers or [],
            keyword_bid_modifier_updates
        )
        entity_ids = [entity.id for entity in ad_group.entities]
        upcs = await self.lookup.get_product_upcs_by_short_id_batch(entity_ids)
        validation_warnings = await self.validate_keyword_targeting(
            upcs,
            keyword_modifiers,
            ad_group.budgetAmount
        )
        if not keyword_modifiers:
            return None, validation_warnings

        keyword_bid_modifier_group_id = await self.build_keyword_bid_modifier_group(keyword_modifiers)
        return keyword_bid_modifier_group_id, validation_warnings

    @staticmethod
    def merge_keywords(
            prev_keywords: List[KeywordBidModifier],
            next_keywords: List[KeywordBidModifier]
    ) -> List[KeywordBidModifier]:
        existing_modifiers_by_keyword = {modifier.keyword: modifier for modifier in prev_keywords}
        new_modifiers: List[KeywordBidModifier] = []
        for modifier in next_keywords:
            existing_modifier = existing_modifiers_by_keyword.get(modifier.keyword, None)
            if existing_modifier in prev_keywords:
                prev_keywords.remove(existing_modifier)
            if modifier.deleted:
                continue
            new_modifiers.append(modifier)

        return prev_keywords + new_modifiers

    async def validate_keyword_targeting(
            self,
            upcs: list[str],
            keyword_modifiers: list[KeywordBidModifier],
            budget: float
    ) -> List[UpstreamValidationWarning]:
        if len(keyword_modifiers) > 100:
            raise HTTPException(status_code=400, detail="Cannot have more than 100 keywords")

        allowed_keywords = await self.get_eligible_keywords_from_upcs(upcs)
        seen_keywords = set()
        warnings = []
        details = []
        for modifier in keyword_modifiers[:]:
            keyword = modifier.keyword
            if keyword in seen_keywords:
                details.append(f"Cannot have duplicate keywords ({keyword}), ignoring this keyword")
                keyword_modifiers.remove(modifier)
                continue
            seen_keywords.add(keyword)

            if keyword not in allowed_keywords:
                details.append(f"\"{keyword}\" is not an allowed keyword, ignoring this keyword")
                keyword_modifiers.remove(modifier)
                continue

            if modifier.modifier <= 0:
                details.append(f"Bid amount for \"{keyword}\" must be greater than zero")
                keyword_modifiers.remove(modifier)
                continue

            if modifier.modifier >= budget:
                details.append(f"Bid amount for \"{keyword}\" cannot be greater than or equal to the budget amount")
                keyword_modifiers.remove(modifier)
                continue

        if details:
            warnings.append(UpstreamValidationWarning(
                detail=details,
                path="data.keywordBidModifiers"
            ))

        return warnings