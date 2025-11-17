import json
import unittest
from unittest.mock import patch, MagicMock

import httpx

from tests.unit.utils.openapi_utils import OpenAPIUtils


class TestOpenAPIUtils(unittest.TestCase):

    def setUp(self):
        self.api_url = "https://test.com/api"
        self.swagger_url = "https://test.com/docs"
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.token_url = "https://test.com/token"
        self.scope = "e451.api.access"
        self.openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Example API",
                "version": "1.0.0"
            },
            "paths": {}
        }

    @patch('tests.unit.utils.openapi_utils.OAuth2Client')
    def test_fetch_openapi_spec_from_endpoint_success(self, mock_oauth2_client):
        mock_client = mock_oauth2_client.return_value
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = self.openapi_spec
        response_mock.raise_for_status = MagicMock()
        mock_client.request.return_value = response_mock

        spec = OpenAPIUtils.get_openapi_spec_from_endpoint(
            self.api_url, self.client_id, self.client_secret, self.token_url, self.scope
        )
        self.assertEqual(spec, self.openapi_spec)
        mock_client.request.assert_called_with("GET", f"{self.api_url}")

    @patch('tests.unit.utils.openapi_utils.OAuth2Client')
    def test_get_openapi_spec_from_endpoint_failure(self, mock_oauth2_client):
        mock_client = mock_oauth2_client.return_value
        response_mock = MagicMock()
        response_mock.status_code = 404
        response_mock.json.return_value = None
        response_mock.raise_for_status = MagicMock()
        mock_client.request.return_value = response_mock

        spec = OpenAPIUtils.get_openapi_spec_from_endpoint(
            self.api_url, self.client_id, self.client_secret, self.token_url, self.scope
        )
        self.assertEqual(spec, None)
        mock_client.request.assert_called_with("GET", f"{self.api_url}")

    @patch('tests.unit.utils.openapi_utils.OAuth2Client')
    def test_get_openapi_spec_from_swagger_success(self, mock_oauth2_client):
        mock_client = mock_oauth2_client.return_value
        swagger_html = f'<div hidden id="oas">{json.dumps(self.openapi_spec)}</div>'
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.text = swagger_html
        response_mock.raise_for_status = MagicMock()
        mock_client.request.return_value = response_mock

        spec = OpenAPIUtils.get_openapi_spec_from_swagger(
            self.swagger_url, self.client_id, self.client_secret, self.token_url, self.scope
        )
        self.assertEqual(spec, self.openapi_spec)
        mock_client.request.assert_called_with("GET", self.swagger_url)

    @patch('tests.unit.utils.openapi_utils.OAuth2Client')
    def test_get_openapi_spec_from_swagger_failure(self, mock_oauth2_client):
        mock_client = mock_oauth2_client.return_value
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.text = "<html></html>"
        response_mock.raise_for_status = MagicMock()
        mock_client.request.return_value = response_mock

        spec = OpenAPIUtils.get_openapi_spec_from_swagger(
            self.swagger_url, self.client_id, self.client_secret, self.token_url, self.scope
        )
        self.assertEqual(spec, None)
        mock_client.request.assert_called_with("GET", self.swagger_url)

    def test_parse_openapi_spec(self):
        spec = OpenAPIUtils.parse_openapi_spec(self.openapi_spec)
        self.assertEqual(spec.spec.accessor.lookup['info']['title'], "Example API")
        self.assertEqual(spec.spec.accessor.lookup['info']['version'], "1.0.0")

    def _mock_request_side_effect(self, method, url, *args, **kwargs):
        if url == f"{self.api_url}/openapi.json":
            response_mock = MagicMock()
            response_mock.status_code = 404
            response_mock.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError("Not Found", request=None, response=response_mock))
            return response_mock
        elif url == self.swagger_url:
            response_mock = MagicMock()
            response_mock.status_code = 200
            swagger_html = f'<div hidden id="oas">{json.dumps(self.openapi_spec)}</div>'
            response_mock.text = swagger_html
            response_mock.raise_for_status = MagicMock()
            return response_mock
        response_mock = MagicMock()
        response_mock.status_code = 500
        response_mock.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Server Error", request=None, response=response_mock))
        return response_mock

    @patch('tests.unit.utils.openapi_utils.OAuth2Client')
    def test_get_openapi_spec(self, mock_oauth2_client):
        mock_client = mock_oauth2_client.return_value
        mock_client.request.side_effect = self._mock_request_side_effect

        spec = OpenAPIUtils.get_openapi_spec(
            self.api_url, self.swagger_url, self.client_id, self.client_secret, self.token_url, self.scope
        )
        self.assertEqual(spec, self.openapi_spec)