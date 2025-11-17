from datetime import timedelta
from unittest import TestCase
from unittest.mock import MagicMock, patch

from app.common.services.http_connection_service import HttpConnectionService


class TestHttpConnectionService(TestCase):
    @patch('app.common.services.http_connection_service.HttpConnectionService.__new__')
    @patch('app.common.services.http_connection_service.ConfigService')
    def test_new__timeout_passed__should_refresh_http_client(
            self,
            mock_config_service: MagicMock,
            mock_httpx_client_new: MagicMock):
        mock_http_client = MagicMock()
        mock_httpx_client_new.return_value = mock_http_client
        mock_config_service.return_value.get_current_config.return_value.http_client_timeout_seconds = 120

        http_connection_service = HttpConnectionService()

        first_http_client = http_connection_service.get_http_client()

        self.assertNotEqual(mock_http_client, first_http_client)

    @patch('app.common.services.http_connection_service.logger')
    def test_log_response__success_response__should_not_log(self, mock_logger: MagicMock):
        response = MagicMock()
        response.is_success = True

        HttpConnectionService._HttpConnectionService__log_response(response)

        mock_logger.info.assert_not_called()

    @patch('app.common.services.http_connection_service.logger')
    def test_log_response__failure_response__should_log_request_and_response(self, mock_logger: MagicMock):
        response = MagicMock()
        response.is_success = False
        response.status_code = 500
        response.url = 'http://example.com'
        response.read.return_value = 'Error'
        request = MagicMock()
        request.method = 'GET'
        request.url = 'http://example.com'
        response.request = request
        response.elapsed = timedelta(seconds=2)

        HttpConnectionService._HttpConnectionService__log_response(response)

        mock_logger.info.assert_any_call('My HTTP Request: %s %s', 'GET', 'http://example.com')
        mock_logger.info.assert_any_call(
            'My HTTP Response: %d %s %s',
            500,
            'http://example.com',
            'Error',
            extra={
                "downstream_duration": 2,
                "downstream_url": "http://example.com"
            }
        )
