import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import HTTPException

from app.common.model.downstream.bid_modifiers import KeywordBidModifiersResponse, KeywordsResponse, \
    BidModifierGroupResponse, BidModifierGroupId
from app.common.view_models import KeywordBidModifier, Entity
from app.common.model.shared import UpstreamValidationWarning
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.services.keyword_service import KeywordService


class TestKeywordService(unittest.IsolatedAsyncioTestCase):
    __internal_http_client_service: ExternalApiHttpClientService
    mock_keyword_bidding_gateway: MagicMock

    def setUp(self):
        self.__internal_http_client_service = MagicMock()
        self.mock_keyword_bidding_gateway = AsyncMock()
        self.mock_lookup = AsyncMock()

        self.keyword_service = KeywordService(
            external_api_http_client_service=self.__internal_http_client_service,
            keyword_bidding_gateway=self.mock_keyword_bidding_gateway,
            lookup=self.mock_lookup,
        )

    async def test_create_keyword_bid_modifier_group_success(self):
        self.mock_keyword_bidding_gateway.create_keyword_bid_modifier_group.return_value = MagicMock(
            is_success=True, is_server_error=False, data=MagicMock(id="1")
        )

        result = await self.keyword_service.create_keyword_bid_modifier_group({
            "bid_modifier_type": "boost",
            "keyword_bid_modifiers": [{"keyword": "example", "bid_modifier": 1.2}]
        })

        self.assertEqual(result, "1")

    async def test_create_keyword_bid_modifier_group_400(self):
        self.mock_keyword_bidding_gateway.create_keyword_bid_modifier_group.side_effect = HTTPException(
            status_code=400, detail="Failed to create keyword bid modifier group"
        )

        with self.assertRaises(HTTPException) as context:
            await self.keyword_service.create_keyword_bid_modifier_group({
                "bid_modifier_type": "boost",
                "keyword_bid_modifiers": [{"keyword": "example", "bid_modifier": 1.2}]
            })

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Failed to create keyword bid modifier group")

    async def test_get_eligible_keywords_from_upcs_success(self):
        self.mock_keyword_bidding_gateway.get_eligible_keywords.return_value = MagicMock(data=["eggs", "butter", "milk"])

        result = await self.keyword_service.get_eligible_keywords_from_upcs(["001", "002"])
        expected_result = {"eggs", "butter", "milk"}
        self.assertSetEqual(result, expected_result)

    async def test_get_eligible_keywords_from_upcs_500(self):
        self.mock_keyword_bidding_gateway.get_eligible_keywords.side_effect = HTTPException(
            status_code=500, detail="Backend service unavailable"
        )

        with self.assertRaises(HTTPException) as context:
            await self.keyword_service.get_eligible_keywords_from_upcs(["001", "002"])

        self.assertEqual(context.exception.status_code, 500)

    @patch('logging.Logger.warning')
    async def test_get_eligible_keywords_from_upcs__raises_400_on_empty_upcs(self, mock_logger):
        with self.assertRaises(HTTPException) as context:
            await self.keyword_service.get_eligible_keywords_from_upcs([])

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Cannot get keywords without UPCs")
        mock_logger.assert_called_once_with("Cannot get keywords without UPCs")

    @patch('logging.Logger.warning')
    async def test_get_eligible_keywords_from_upcs__returns_empty_error(self, mock_logger):
        self.mock_keyword_bidding_gateway.get_eligible_keywords.side_effect = HTTPException(
            status_code=500, detail="No keywords found for the given UPCs"
        )

        with self.assertRaises(HTTPException) as context:
            await self.keyword_service.get_eligible_keywords_from_upcs(["001", "002"])

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "No keywords found for the given UPCs")

    @patch('logging.Logger.warning')
    async def test_get_eligible_keywords_from_upcs__returns_empty_array(self, mock_logger):
        self.mock_keyword_bidding_gateway.get_eligible_keywords.return_value = MagicMock(data=[])

        result = await self.keyword_service.get_eligible_keywords_from_upcs(["001", "002"])
        expected_result = []
        self.assertEqual(result, expected_result)

    @patch('logging.Logger.warning')
    async def test_get_eligible_keywords_from_upcs__returns_none(self, mock_logger):
        self.mock_keyword_bidding_gateway.get_eligible_keywords.return_value = MagicMock(data=None)

        result = await self.keyword_service.get_eligible_keywords_from_upcs(["001", "002"])
        expected_result = []
        self.assertEqual(result, expected_result)

    async def test_get_bid_modifiers__returns_empty_list_if_id_is_none(self):
        bid_modifier_id = None

        result = await self.keyword_service.get_bid_modifiers(bid_modifier_id)

        self.assertEqual(result, [])

    async def test_get_bid_modifiers__converts_downstream_bid_modifiers_to_view_models(self):
        response_json = {
                "data": {
                    "id": "1234",
                    "bid_modifier_type": "keyword",
                    "keyword_bid_modifiers": [
                        {"keyword": "soda", "bid_modifier": 0.5},
                        {"keyword": "cola", "bid_modifier": 0.6},
                    ],
                    "min_bid_modifier": 0.5,
                    "max_bid_modifier": 1.0
                },
                "meta": {"size": 2}
            }
        bid_modifier_id = "1234"
        expected_response = [
            KeywordBidModifier(keyword="soda", modifier=0.5, deleted=False),
            KeywordBidModifier(keyword="cola", modifier=0.6, deleted=False)
        ]
        # self.__internal_http_client_service.get.return_value = downstream_response
        self.mock_keyword_bidding_gateway.get_keyword_bid_modifier_group.return_value = KeywordBidModifiersResponse(**response_json)

        result = await self.keyword_service.get_bid_modifiers(bid_modifier_id)

        self.assertEqual(expected_response, result)
        self.mock_keyword_bidding_gateway.get_keyword_bid_modifier_group.assert_called_once_with(bid_modifier_id)

    def test_get_keyword_bid_modifier_group_payload(self):
        keyword_bid_modifiers = [
            KeywordBidModifier(keyword="soda", modifier=0.5),
            KeywordBidModifier(keyword="cola", modifier=0.6)
        ]
        expected_payload = {
            "bid_modifier_type": "boost",
            "keyword_bid_modifiers": (
                {"keyword": "soda", "bid_modifier": 0.5},
                {"keyword": "cola", "bid_modifier": 0.6}
            )
        }

        result = self.keyword_service.get_keyword_bid_modifier_group_payload(keyword_bid_modifiers)
        self.assertEqual(result, expected_payload)

    async def test_build_keyword_bid_modifier_group(self):
        keyword_bid_modifiers = [
            KeywordBidModifier(keyword="soda", modifier=0.5),
            KeywordBidModifier(keyword="cola", modifier=0.6)
        ]
        self.keyword_service.get_keyword_bid_modifier_group_payload = MagicMock(return_value={})
        self.keyword_service.create_keyword_bid_modifier_group = AsyncMock(return_value="1234")

        result = await self.keyword_service.build_keyword_bid_modifier_group(keyword_bid_modifiers)
        self.assertEqual(result, "1234")
        self.keyword_service.get_keyword_bid_modifier_group_payload.assert_called_once_with(keyword_bid_modifiers)
        self.keyword_service.create_keyword_bid_modifier_group.assert_called_once_with({})

    def test_merge_keywords__merges_lists_of_keywords(self):
        prev_keywords = [
            KeywordBidModifier(keyword="a", modifier=0.1, deleted=False),
            KeywordBidModifier(keyword="b", modifier=0.2, deleted=False),
            KeywordBidModifier(keyword="c", modifier=0.3, deleted=False),
        ]
        next_keywords = [
            KeywordBidModifier(keyword="a", modifier=0.5, deleted=False),
            KeywordBidModifier(keyword="b", modifier=0.5, deleted=True),
            KeywordBidModifier(keyword="d", modifier=0.5, deleted=False),
        ]
        expected_keywords = [
            KeywordBidModifier(keyword="c", modifier=0.3, deleted=False),
            KeywordBidModifier(keyword="a", modifier=0.5, deleted=False),
            KeywordBidModifier(keyword="d", modifier=0.5, deleted=False),
        ]

        result = self.keyword_service.merge_keywords(
            prev_keywords,
            next_keywords
        )

        self.assertEqual(expected_keywords, result)

    async def test_validate_keyword_targeting__validates_keywords(self):
        upcs = ["4011", "4012"]
        keyword_modifiers = [
            KeywordBidModifier(keyword="banana", modifier=0.1, deleted=False),
            KeywordBidModifier(keyword="orange", modifier=0.1, deleted=False),
            KeywordBidModifier(keyword="fruit", modifier=-0.1, deleted=False),
            KeywordBidModifier(keyword="everything", modifier=0.1, deleted=False),
            KeywordBidModifier(keyword="banana", modifier=0.1, deleted=False),
            KeywordBidModifier(keyword="melon", modifier=200, deleted=False),
        ]
        budget = 100
        mock_keywords = KeywordsResponse(data=[
            'banana',
            'orange',
            'fruit',
            'melon'
        ])
        self.mock_keyword_bidding_gateway.get_eligible_keywords.return_value = mock_keywords
        expected_warnings = [UpstreamValidationWarning(
            detail=[
                'Bid amount for "fruit" must be greater than zero',
                '"everything" is not an allowed keyword, ignoring this keyword',
                'Cannot have duplicate keywords (banana), ignoring this keyword',
                'Bid amount for "melon" cannot be greater than or equal to the budget amount'
            ],
            path="data.keywordBidModifiers"
        )]

        warnings = await self.keyword_service.validate_keyword_targeting(
            upcs,
            keyword_modifiers,
            budget
        )

        self.assertEqual(expected_warnings, warnings)

    async def test_validate_keyword_targeting__limits_keywords_to_100(self):
        upcs = ["4011", "4012"]
        keyword_modifiers = [
            KeywordBidModifier(keyword=f"keyword-{index}", modifier=0.1, deleted=False)
            for index in range(101)
        ]
        budget = 100

        with self.assertRaises(HTTPException) as context:
            await self.keyword_service.validate_keyword_targeting(upcs, keyword_modifiers, budget)

        self.assertIsNotNone(context)
        self.assertEqual(400, context.exception.status_code)
        self.assertEqual("Cannot have more than 100 keywords", context.exception.detail)

    async def test_update_keywords__returns_none_if_there_are_no_keywords(self):
        current_keyword_bid_modifiers = []
        ad_group_entities = [
            Entity(
                id=1,
                useBaseBid=False,
                bidAmount=0.1,
                deleted=False
            )
        ]
        ad_group_budget = 100
        ad_group = MagicMock()
        ad_group.keywordBidModifiers = current_keyword_bid_modifiers
        ad_group.entities = ad_group_entities
        ad_group.budgetAmount = ad_group_budget
        keyword_modifier_updates = [
            KeywordBidModifier(keyword="random keyword", modifier=0.1, deleted=False)
        ]
        mock_upcs = ["4011", "4012"]
        mock_keywords = KeywordsResponse(data=[
            'banana',
            'orange',
            'fruit',
            'melon'
        ])
        mock_bid_group_id = "bid_group_id"
        mock_create_response = BidModifierGroupResponse(
            data=BidModifierGroupId(id=mock_bid_group_id)
        )
        expected_warnings = [UpstreamValidationWarning(
            detail=['"random keyword" is not an allowed keyword, ignoring this keyword'],
            path="data.keywordBidModifiers"
        )]
        self.mock_lookup.get_product_upcs_by_short_id_batch.return_value = mock_upcs
        self.mock_keyword_bidding_gateway.get_eligible_keywords.return_value = mock_keywords
        self.mock_keyword_bidding_gateway.create_keyword_bid_modifier_group.return_value = mock_create_response

        bid_group_id_response, warnings = await self.keyword_service.update_keywords(
            ad_group,
            keyword_modifier_updates
        )

        self.assertIsNone(bid_group_id_response)
        self.assertEqual(expected_warnings, warnings)

    async def test_update_keywords__creates_new_bid_group(self):
        current_keyword_bid_modifiers = [
            KeywordBidModifier(keyword="banana", modifier=0.1, deleted=False),
            KeywordBidModifier(keyword="orange", modifier=0.1, deleted=False)
        ]
        ad_group_entities = [
            Entity(
                id=1,
                useBaseBid=False,
                bidAmount=0.1,
                deleted=False
            )
        ]
        ad_group_budget = 100
        ad_group = MagicMock()
        ad_group.keywordBidModifiers = current_keyword_bid_modifiers
        ad_group.entities = ad_group_entities
        ad_group.budgetAmount = ad_group_budget
        keyword_modifier_updates = [
            KeywordBidModifier(keyword="random keyword", modifier=0.1, deleted=False),
            KeywordBidModifier(keyword="banana", modifier=0.2, deleted=False)
        ]
        mock_upcs = ["4011"]
        mock_keywords = KeywordsResponse(data=[
            'banana',
            'orange',
            'fruit',
            'melon'
        ])
        mock_bid_group_id = "bid_group_id"
        mock_create_response = BidModifierGroupResponse(
            data=BidModifierGroupId(id=mock_bid_group_id)
        )
        expected_warnings = [UpstreamValidationWarning(
            detail=['"random keyword" is not an allowed keyword, ignoring this keyword'],
            path="data.keywordBidModifiers"
        )]
        self.mock_lookup.get_product_upcs_by_short_id_batch.return_value = mock_upcs
        self.mock_keyword_bidding_gateway.get_eligible_keywords.return_value = mock_keywords
        self.mock_keyword_bidding_gateway.create_keyword_bid_modifier_group.return_value = mock_create_response

        bid_group_id_response, warnings = await self.keyword_service.update_keywords(
            ad_group,
            keyword_modifier_updates
        )

        self.assertEqual(mock_bid_group_id, bid_group_id_response)
        self.assertEqual(expected_warnings, warnings)
        self.mock_lookup.get_product_upcs_by_short_id_batch.assert_called_once_with([1])