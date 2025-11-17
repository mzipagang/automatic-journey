import asyncio
import time
from datetime import timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from httpx import Response

from app.common.services.async_http_connection_service import AsyncHttpConnectionService

class TestAsyncHttpConnectionService(IsolatedAsyncioTestCase):

    def setUp(self):
        self.MOCK_CONFIG = MagicMock()
        self.MOCK_CONFIG.redis_host = 'localhost'
        self.MOCK_CONFIG.redis_port = 6379
        self.MOCK_CONFIG.redis_db = 0
        self.MOCK_CONFIG.redis_primary_access_key = 'password'
        self.MOCK_CONFIG.redis_ssl = False
        self.MOCK_CONFIG.redis_socket_timeout = 10
        self.MOCK_CONFIG.redis_socket_connect_timeout = 10
        self.MOCK_CONFIG.redis_health_check_interval = 30

    @patch('app.common.services.async_http_connection_service.ConfigService')
    async def test_new__timeout_passed__should_refresh_http_client(self, mock_config_service):
        mock_config_service.return_value.get_current_config.return_value = self.MOCK_CONFIG
        state = {
            "connection_id": "conn-1",
        }
        expected = {"connection_id": state["connection_id"]}
        AsyncHttpConnectionService._self = None
        with patch("app.common.services.async_http_connection_service.AsyncClient",
                   new_callable=MagicMock) as mock_async_client_class:

            mock_client_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected
            mock_client_instance.get.return_value = mock_response
            mock_async_client_class.return_value = mock_client_instance

            mock_config_service.return_value.get_current_config.return_value.http_client_timeout_seconds = 0.5
            http_service = AsyncHttpConnectionService()
            http_client = http_service.get_http_client()

            r1 = await http_client.get("https://example.com")
            result1 = r1.json()

            await asyncio.sleep(0.3)

            # Before the timeout expires, the connection_id should remain the same
            r2 = await http_client.get("https://example.com")
            result2 = r2.json()
            assert result1['connection_id'] == result2['connection_id']

            await asyncio.sleep(0.6)

            state["connection_id"] = "conn-2"
            expected = {"connection_id": state["connection_id"]}
            mock_response.json.return_value = expected

            # After the timeout expires, a new connection should be created using the same client
            r3 = await http_client.get("https://example.com")
            result3 = r3.json()
            assert result3['connection_id'] != result1['connection_id']

    @patch('app.common.services.async_http_connection_service.logger')
    async def test_log_response__success_response__should_not_log(self, mock_logger: MagicMock):
        response = MagicMock()
        response.is_success = True

        await AsyncHttpConnectionService._AsyncHttpConnectionService__log_response(response)

        mock_logger.info.assert_not_called()

    @patch('app.common.services.async_http_connection_service.logger')
    async def test_log_response__failure_response__should_log_request_and_response(self, mock_logger: MagicMock):
        mock_request = MagicMock()
        mock_request.url = 'http://example.com'
        mock_request.method = 'GET'
        response = Response(
            status_code=500,
            request=mock_request,
            content='Error',
        )
        response._elapsed = timedelta(seconds=2)

        await AsyncHttpConnectionService._AsyncHttpConnectionService__log_response(response)

        mock_logger.info.assert_any_call('My HTTP Request: %s %s', 'GET', 'http://example.com')
        mock_logger.info.assert_any_call(
            'My HTTP Response: %d %s %s',
            500,
            'http://example.com',
            b'Error',
            extra={
                "downstream_duration": 2,
                "downstream_url": "http://example.com"
            }
        )
