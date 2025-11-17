from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from fastapi import HTTPException
from httpx import Response

from app.common.model.downstream.bid_modifiers import (
    BidModifierGroupRequest,
    BidModifierGroupResponse,
    KeywordBidModifiersResponse,
    KeywordsRequest,
    KeywordsResponse,
)
from app.common.gateways.keyword_bidding_gateway import KeywordBiddingGateway


class TestKeywordBiddingGateway(IsolatedAsyncioTestCase):
    def setUp(self):
        self.__mock_external_http_client_service = MagicMock()
        self.__mock_async_external_http_client_service = AsyncMock()
        self.__mock_harness_service = MagicMock()

        self.__mock_harness_service.is_harness_flag_on.return_value = True

        self.keyword_bid_modifier_gateway = KeywordBiddingGateway(
                self.__mock_async_external_http_client_service,
                self.__mock_external_http_client_service,
                self.__mock_harness_service)

    async def test_create_keyword_bid_modifier_group(self):
        payload = {
            "bid_modifier_type": "boost",
            "keyword_bid_modifiers": [
                {"keyword": "soda", "bid_modifier": 0.5},
                {"keyword": "cola", "bid_modifier": 0.6},
            ],
        }

        expected_response = {"data": {"id": "964735f0-f098-4c72-bf67-2da7e8b711d6"}, "meta": None}

        self.__mock_async_external_http_client_service.post.return_value = Response(
            200, json=expected_response
        )

        result = await self.keyword_bid_modifier_gateway.create_keyword_bid_modifier_group(
            BidModifierGroupRequest(**payload)
        )

        self.assertEqual(result, BidModifierGroupResponse(**expected_response))

    async def test_create_keyword_bid_modifier_group_400(self):
        payload = {
            "bid_modifier_type": "boost",
            "keyword_bid_modifiers": [
                {"keyword": "soda", "bid_modifier": 0.5},
                {"keyword": "cola", "bid_modifier": 0.6},
            ],
        }

        self.__mock_async_external_http_client_service.post.return_value = Response(400)
        with self.assertRaises(HTTPException) as context:
            await self.keyword_bid_modifier_gateway.create_keyword_bid_modifier_group(
                BidModifierGroupRequest(**payload)
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Failed to create keyword bid modifier group")

    async def test_create_keyword_bid_modifier_group_500(self):
        payload = {
            "bid_modifier_type": "boost",
            "keyword_bid_modifiers": [
                {"keyword": "soda", "bid_modifier": 0.5},
                {"keyword": "cola", "bid_modifier": 0.6},
            ],
        }

        self.__mock_async_external_http_client_service.post.return_value = Response(500)
        with self.assertRaises(HTTPException) as context:
            await self.keyword_bid_modifier_gateway.create_keyword_bid_modifier_group(
                BidModifierGroupRequest(**payload)
            )

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Backend service unavailable")

    async def test_get_eligible_keywords(self):
        payload = {
            "upcs": [
                "0089477100034",
                "0089477100008",
            ]
        }

        expected_response = {
            "data": [
                "crisps",
                "crunchmaster",
                "cheese crisps",
            ],
            "meta": {"size": 100},
        }

        self.__mock_async_external_http_client_service.post.return_value = Response(
            200, json=expected_response
        )

        result = await self.keyword_bid_modifier_gateway.get_eligible_keywords(KeywordsRequest(**payload))

        self.assertEqual(result, KeywordsResponse(**expected_response))

    async def test_get_eligible_keywords_400(self):
        payload = {
            "upcs": [
                "0089477100034",
                "0089477100008",
            ]
        }

        self.__mock_async_external_http_client_service.post.return_value = Response(400)
        with self.assertRaises(HTTPException) as context:
            await self.keyword_bid_modifier_gateway.get_eligible_keywords(KeywordsRequest(**payload))

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Failed to get eligible keywords")

    async def test_get_eligible_keywords_500(self):
        payload = {
            "upcs": [
                "0089477100034",
                "0089477100008",
            ]
        }

        self.__mock_async_external_http_client_service.post.return_value = Response(500)
        with self.assertRaises(HTTPException) as context:
            await self.keyword_bid_modifier_gateway.get_eligible_keywords(KeywordsRequest(**payload))

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Backend service unavailable")

    async def test_get_keyword_bid_modifier_group(self):
        keyword_bid_modifier_group_id = "964735f0-f098-4c72-bf67-2da7e8b711d6"
        expected_response = {
            "data": {
                "id": "964735f0-f098-4c72-bf67-2da7e8b711d6",
                "bid_modifier_type": "boost",
                "keyword_bid_modifiers": [
                    {"keyword": "divina", "bid_modifier": 0.8},
                    {"keyword": "pancetta", "bid_modifier": 0.75},
                ],
                "min_bid_modifier": 0.75,
                "max_bid_modifier": 0.8,
            },
            "meta": None,
        }
        self.__mock_async_external_http_client_service.get.return_value = Response(
            200, json=expected_response
        )
        result = await self.keyword_bid_modifier_gateway.get_keyword_bid_modifier_group(
            keyword_bid_modifier_group_id
        )
        self.assertEqual(result, KeywordBidModifiersResponse(**expected_response))

    async def test_get_keyword_bid_modifier_group_400(self):
        keyword_bid_modifier_group_id = "964735f0-f098-4c72-bf67-2da7e8b711d6"
        self.__mock_async_external_http_client_service.get.return_value = Response(400)
        with self.assertRaises(HTTPException) as context:
            await self.keyword_bid_modifier_gateway.get_keyword_bid_modifier_group(
                keyword_bid_modifier_group_id
            )
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Failed to get keyword bid modifier group")

    async def test_get_keyword_bid_modifier_group_500(self):
        keyword_bid_modifier_group_id = "964735f0-f098-4c72-bf67-2da7e8b711d6"
        self.__mock_async_external_http_client_service.get.return_value = Response(500)
        with self.assertRaises(HTTPException) as context:
            await self.keyword_bid_modifier_gateway.get_keyword_bid_modifier_group(
                keyword_bid_modifier_group_id
            )
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Backend service unavailable")
