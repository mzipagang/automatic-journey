import json
from pathlib import Path
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from httpx import Response

from app.common.gateways.creative_service_gateway import CreativeServiceGateway
from app.common.model.downstream.creative_group import CreativeAdGroupRequest, CreativeAdGroupCreateResponse

TEMPLATE_GROUP_ID = "CAROUSEL_VIDEO"

class TestCreativeServiceGateway(IsolatedAsyncioTestCase):
    __mock_async_internal_api_http_client: AsyncMock
    __mock_internal_api_http_client: MagicMock
    __mock_harness_service: MagicMock

    __subject: CreativeServiceGateway

    @patch("app.common.utils.async_adapter.__new__")
    async def asyncSetUp(self, mock_async_adapter_new: MagicMock):
        self.__mock_async_internal_api_http_client = AsyncMock()
        self.__mock_internal_api_http_client = MagicMock()
        self.__mock_harness_service = MagicMock()

        mock_async_adapter_new.return_value = self.__mock_async_internal_api_http_client

        self.__subject = CreativeServiceGateway(
            async_internal_api_http_client=self.__mock_async_internal_api_http_client,
            internal_api_http_client=self.__mock_internal_api_http_client,
            harness_service=self.__mock_harness_service)

    async def test_creative_group_is_ready__is_ready__should_return_true(self):
        self.__mock_async_internal_api_http_client.get.return_value = Response(status_code=200)

        result: bool = await self.__subject.creative_group_is_ready(creative_entity_id="abc-123")

        self.assertTrue(result)

    async def test_creative_group_is_ready__is_not_ready__should_return_false(self):
        self.__mock_async_internal_api_http_client.get.return_value = Response(status_code=404)

        result: bool = await self.__subject.creative_group_is_ready(creative_entity_id="abc-123")

        self.assertFalse(result)

    async def test_init_creative_group(self):
        with open(f"{Path(__file__).parent.parent}/utils/json_files/creative_group_creation_response.json", 'r') as f:
            expected_response = json.loads(f.read())
            expected_response_parsed = CreativeAdGroupCreateResponse(**expected_response)
        with open(f"{Path(__file__).parent.parent}/utils/json_files/creative_group_request.json", 'r') as f:
            request_body = CreativeAdGroupRequest(**json.loads(f.read()))
        self.__mock_async_internal_api_http_client.post.return_value = Response(
            status_code=200,
            json=expected_response
        )
        result = await self.__subject.init_creative_group(request_body, TEMPLATE_GROUP_ID)

        self.assertEqual(result, expected_response_parsed)

    async def test_init_creative_group_exception(self):
        with open(f"{Path(__file__).parent.parent}/utils/json_files/creative_group_request.json", 'r') as f:
            request_body = CreativeAdGroupRequest(**json.loads(f.read()))
        self.__mock_async_internal_api_http_client.post.return_value = Response(
            status_code=500,
        )
        with self.assertRaises(HTTPException) as context:
             await self.__subject.init_creative_group(request_body, TEMPLATE_GROUP_ID)
        self.assertEqual(str(context.exception.detail), "Incorrect response from Creative Service")
        self.assertEqual(str(context.exception.status_code), "500")