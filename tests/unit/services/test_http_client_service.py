import json
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException
from httpx import Request, Response

from app.common.configuration.constants import KODDI_SSO_SERVICE_JWT_PATH
from app.common.context.context import user_context, security_context
from app.common.services.config_service import Config
from app.common.services.http_client_service import KoddiHttpClientService, ExternalApiHttpClientService, HttpClientService


class TestHttpClientService(unittest.TestCase):
    __mock_external_api_http_client_service: MagicMock
    __subject_external_api_client: HttpClientService

    __test_token = ('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0'
                    'IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69XnJ6XGk01OaUS_YGLNkKZ_mk6qxF0Q')

    def setUp(self):
        self.mock_config_service = MagicMock()
        self.mock_oauth2_scheme = MagicMock()
        self.mock_http_connection_service = MagicMock()
        self.mock_httpx_client = MagicMock()
        self.__mock_external_api_http_client_service = MagicMock()
        self.__mock_external_api_http_client_service.get.return_value = Response(
            status_code=200, content=self.__test_token
        )

        user_context.set({'username': 'abc@123.invalid'})
        security_context.set({'username': 'test-user', 'id_token': self.__test_token})

        self.mock_config_service.get_current_config.return_value = Config(
            base_api_url='https://api.com.invalid',
            base_koddi_url='https://koddi.com.invalid',
            product_id='product_id',
            pte_target_id='pte_target_id')

        self.__subject_external_api_client = ExternalApiHttpClientService(config_service=self.mock_config_service,
                                                                          http_connection_service=self.mock_http_connection_service)

        self.subject_koddi_client = KoddiHttpClientService(
            config_service=self.mock_config_service,
            http_connection_service=self.mock_http_connection_service,
            external_api_http_client_service=self.__mock_external_api_http_client_service)

    def test_internal_get__should_succeed(self):
        self.__subject_external_api_client.get('/path')

        expected_args = 'https://api.com.invalid/path'
        expected_kwargs = {
            'params': None,
            'headers': {
                'Authorization': f'Bearer {self.__test_token}',
                'accept': 'application/json',
                'cache-control': 'no-cache',
                'content-type': 'application/json',
            },
            'timeout': None
        }

        self.mock_http_connection_service.get_http_client().get.assert_called_once_with(
            expected_args, **expected_kwargs)

    def test_internal_post__should_succeed(self):
        self.__subject_external_api_client.post('/path', json={'key': 'value'})

        self.mock_http_connection_service.get_http_client().post.assert_called_once_with(
            url='https://api.com.invalid/path',
            json={'key': 'value'},
            params=None,
            headers={
                'Authorization': f'Bearer {self.__test_token}',
                'accept': 'application/json',
                'cache-control': 'no-cache',
                'content-type': 'application/json',
            },
            timeout=None)

    def test_internal_put__should_succeed(self):
        self.__subject_external_api_client.put('/path', json={'key': 'value'})

        self.mock_http_connection_service.get_http_client().put.assert_called_once_with(
            'https://api.com.invalid/path',
            json={'key': 'value'},
            headers={
                'Authorization': f'Bearer {self.__test_token}',
                'accept': 'application/json',
                'cache-control': 'no-cache',
                'content-type': 'application/json',
            },
            timeout=None)

    def test_internal_patch__should_succeed(self):
        self.__subject_external_api_client.patch('/path', json={'key': 'value'})

        self.mock_http_connection_service.get_http_client().patch.assert_called_once_with(
            'https://api.com.invalid/path',
            json={'key': 'value'},
            headers={
                'Authorization': f'Bearer {self.__test_token}',
                'accept': 'application/json',
                'cache-control': 'no-cache',
                'content-type': 'application/json',
            },
            timeout=None)

    def test_internal_close__should_succeed(self):
        self.__subject_external_api_client.close()

        self.mock_http_connection_service.get_http_client().close.assert_called_once()


    def test_koddi_post__should_succeed(self):
        self.subject_koddi_client.post('/path', json={'key': 'value'})

        self.mock_http_connection_service.get_http_client().post.assert_called_once_with(
            url='https://koddi.com.invalid/path',
            json={'key': 'value'},
            params=None,
            headers={
                'Authorization': f'Bearer {self.__test_token}',
            },
            timeout=None)

        self.__mock_external_api_http_client_service.get.assert_called_once_with(
            path=KODDI_SSO_SERVICE_JWT_PATH)

    def test_koddi_close__should_succeed(self):
        self.subject_koddi_client.close()

        self.mock_http_connection_service.get_http_client().close.assert_called_once()

    def test_get__returns_response_if_response_requires_json(self):
        response = Response(status_code=200, json={'key': 'value'})
        self.mock_http_connection_service.get_http_client().get.return_value = response

        result = self.__subject_external_api_client.get(path='/path', response_body_type='json')

        self.assertEqual(response, result)

    def test_get__returns_response_if_response_is_json_and_has_required_data_field(self):
        response = Response(status_code=200, json={'data': 'value'})
        self.mock_http_connection_service.get_http_client().get.return_value = response

        result = self.__subject_external_api_client.get(path='/path', response_body_type='json', json_has_data_field=True)

        self.assertEqual(response, result)

    def test_get__logs_and_raises_server_error_if_json_does_not_exist(self):
        request = Request(url='https://example.com/test', method='GET')
        response = Response(status_code=200, request=request)
        expected_status_code = 503
        expected_message = "Temporary service error.  Please try again."
        self.mock_http_connection_service.get_http_client().get.return_value = response

        exception = None
        try:
            self.__subject_external_api_client.get(path='/path', response_body_type='json')
        except HTTPException as e:
            exception = e

        self.assertIsNotNone(exception)
        self.assertEqual(expected_status_code, exception.status_code)
        self.assertEqual(expected_message, exception.detail)

    def test_get__logs_and_raises_server_error_if_required_data_does_not_exist(self):
        request = Request(url='https://example.com/test', method='GET')
        response = Response(status_code=200, request=request, json={'key': 'value'})
        expected_status_code = 503
        expected_message = "Temporary service error.  Please try again."
        self.mock_http_connection_service.get_http_client().get.return_value = response

        exception = None
        try:
            self.__subject_external_api_client.get(path='/path', response_body_type='json', json_has_data_field=True)
        except HTTPException as e:
            exception = e

        self.assertIsNotNone(exception)
        self.assertEqual(expected_status_code, exception.status_code)
        self.assertEqual(expected_message, exception.detail)

    def test_get__logs_and_raises_server_error_if_response_has_5xx_status(self):
        request = Request(url='https://example.com/test', method='GET')
        response = Response(status_code=500, request=request)
        expected_status_code = 503
        expected_message = "Temporary service error.  Please try again."
        self.mock_http_connection_service.get_http_client().get.return_value = response

        exception = None
        try:
            self.__subject_external_api_client.get(path='/path', response_body_type='json')
        except HTTPException as e:
            exception = e

        self.assertIsNotNone(exception)
        self.assertEqual(expected_status_code, exception.status_code)
        self.assertEqual(expected_message, exception.detail)

    def test_get__logs_and_raises_client_error_if_response_has_4xx_status(self):
        expected_status_code = 422
        expected_content = "passthrough content"
        request = Request(url='https://example.com/test', method='GET')
        response = Response(status_code=expected_status_code, request=request, text=expected_content)
        self.mock_http_connection_service.get_http_client().get.return_value = response

        exception = None
        try:
            self.__subject_external_api_client.get(
                path='/path',
                response_body_type='json',
                forward_client_error_response_content=True)
        except HTTPException as e:
            exception = e

        self.assertIsNotNone(exception)
        self.assertEqual(expected_status_code, exception.status_code)
        self.assertEqual(expected_content, exception.detail)

    def test_get__logs_and_raises_client_error_if_response_has_4xx_status_and_json_body(self):
        expected_status_code = 422
        expected_content = {
            "status": "validationError",
            "code": "422",
            "message": "Bid amount validation failed",
            "errors": [
                {
                    "type": "incorrect-bid-amount-failure",
                    "bidFailures": [
                        {
                            "field": "bidAmount",
                            "message": "0081162002254 - Bid amount must be greater than 0."
                        }
                    ]
                }
            ]
        }
        json_str = json.dumps(expected_content)
        content = json_str.encode('utf-8')
        request = Request(url='https://example.com/test', method='GET')
        response = Response(
            status_code=expected_status_code,
            request=request,
            content=content,
            headers={
                "Content-Type": "application/json",
            }
        )
        self.mock_http_connection_service.get_http_client().get.return_value = response

        exception = None
        try:
            self.__subject_external_api_client.get(
                path='/path',
                response_body_type='json',
                forward_client_error_response_content=True)
        except HTTPException as e:
            exception = e

        self.assertIsNotNone(exception)
        self.assertEqual(expected_status_code, exception.status_code)
        self.assertEqual(expected_content, exception.detail)

    def test_get__logs_and_raises_server_error_if_response_is_outside_of_normal_range(self):
        # Currently this happens on 1xx and 3xx requests, as well as any unusual statuses outside the 5xx range.
        request = Request(url='https://example.com/test', method='GET')
        response = Response(status_code=100, request=request)
        expected_status_code = 500
        expected_message = "Unexpected error processing JSON response"
        self.mock_http_connection_service.get_http_client().get.return_value = response

        exception = None
        try:
            self.__subject_external_api_client.get(path='/path', response_body_type='json')
        except HTTPException as e:
            exception = e

        self.assertIsNotNone(exception)
        self.assertEqual(expected_status_code, exception.status_code)
        self.assertEqual(expected_message, exception.detail)

    def test_get__returns_response_if_body_type_is_none(self):
        request = Request(url='https://example.com/test', method='GET')
        response = Response(status_code=200, request=request)
        self.mock_http_connection_service.get_http_client().get.return_value = response

        result = self.__subject_external_api_client.get(path='/path')

        self.assertEqual(response, result)

    def test_get__returns_response_if_body_type_is_json(self):
        request = Request(url='https://example.com/test', method='GET')
        response = Response(status_code=200, request=request, json={'key': 'value'})
        self.mock_http_connection_service.get_http_client().get.return_value = response

        result = self.__subject_external_api_client.get(path='/path', response_body_type='json')

        self.assertEqual(response, result)