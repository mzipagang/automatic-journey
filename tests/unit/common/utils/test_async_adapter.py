from typing import Coroutine, Any
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from httpx import Response

from app.common.services.async_http_client_service import AsyncInternalApiHttpClientService
from app.common.services.http_client_service import InternalApiHttpClientService
from app.common.utils.async_adapter import AsyncAdapter

class TestAsyncAdapter(IsolatedAsyncioTestCase):
    def setUp(self):
        self.async_mock_fn = MagicMock()
        self.sync_mock_fn = MagicMock()
        self.mock_harness_service = MagicMock()
        self.mock_config_service = MagicMock()
        self.mock_http_connection_service = MagicMock()
        self.mock_async_http_connection_service = MagicMock()
        self.mock_sync_client = MagicMock()
        self.mock_async_client = AsyncMock()
        self.mock_http_connection_service.get_http_client.return_value = self.mock_sync_client
        self.mock_async_http_connection_service.get_http_client.return_value = self.mock_async_client
        self.async_response = Response(
            status_code=200,
            json={"type": "async response"}
        )
        self.sync_response = Response(
            status_code=200,
            json={"type": "sync response"}
        )
        self.mock_async_client.get.return_value = self.async_response
        self.mock_async_client.post.return_value = self.async_response
        self.mock_async_client.put.return_value = self.async_response
        self.mock_async_client.patch.return_value = self.async_response
        self.mock_sync_client.get.return_value = self.sync_response
        self.mock_sync_client.post.return_value = self.sync_response
        self.mock_sync_client.put.return_value = self.sync_response
        self.mock_sync_client.patch.return_value = self.sync_response
        self.sync_client = InternalApiHttpClientService(
            config_service=self.mock_config_service,
            http_connection_service=self.mock_http_connection_service
        )
        self.async_client = AsyncInternalApiHttpClientService(
            config_service=self.mock_config_service,
            http_connection_service=self.mock_async_http_connection_service
        )
        self.http_adapter = AsyncAdapter(
            sync_client=self.sync_client,
            async_client=self.async_client,
            harness_flag_name="test_flag",
            harness_target_id="test_target_id",
            harness_service=self.mock_harness_service
        )

    async def __assert_response(
            self,
            result: Coroutine[Any, Any, Response],
            expected_response: Response
    ):
        response = await result
        self.assertEqual(expected_response, response)

    async def test_async_adapter__can_adapt_http_client(self):
        self.mock_harness_service.is_harness_flag_on.return_value = True

        await self.__assert_response(
            self.http_adapter.get('/test-path'),
            self.async_response
        )
        await self.__assert_response(
            self.http_adapter.post('/test-path', json={}),
            self.async_response
        )
        await self.__assert_response(
            self.http_adapter.put('/test-path', json={}),
            self.async_response
        )
        await self.__assert_response(
            self.http_adapter.patch('/test-path', json={}),
            self.async_response
        )

        self.mock_harness_service.is_harness_flag_on.return_value = False

        await self.__assert_response(
            self.http_adapter.get('/test-path'),
            self.sync_response
        )
        await self.__assert_response(
            self.http_adapter.post('/test-path', json={}),
            self.sync_response
        )
        await self.__assert_response(
            self.http_adapter.put('/test-path', json={}),
            self.sync_response
        )
        await self.__assert_response(
            self.http_adapter.patch('/test-path', json={}),
            self.sync_response
        )
