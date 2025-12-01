import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from fastapi.exceptions import RequestValidationError
from httpx import TransportError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.utils.exceptions import (
    create_custom_route_handler,
    generate_error_reason_from_validation_error,
)


class TestExceptions(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_original_route_handler = AsyncMock()
        self.mock_route_handler = create_custom_route_handler(self.mock_original_route_handler)

    async def test_custom_route_handler__calls_original_route_handler(self):
        mock_request = MagicMock()
        await self.mock_route_handler(mock_request)
        self.mock_original_route_handler.assert_called_once_with(mock_request)

    async def test_custom_route_handler__converts_starlette_http_exception(self):
        mock_request = MagicMock()
        expected_result = b'{"detail":[{"msg":"Test Exception"}]}'
        self.mock_original_route_handler.side_effect = [StarletteHTTPException(
            status_code=400,
            detail="Test Exception"
        )]

        result = await self.mock_route_handler(mock_request)

        self.assertEqual(400, result.status_code)
        self.assertEqual(expected_result, result.body)

    async def test_custom_route_handler__converts_transport_error(self):
        mock_request = MagicMock()
        expected_result = b'{"detail":[{"msg":"Network Error Occured, Please retry!"}]}'
        self.mock_original_route_handler.side_effect = [TransportError(message="Ignored Message")]

        result = await self.mock_route_handler(mock_request)

        self.assertEqual(504, result.status_code)
        self.assertEqual(expected_result, result.body)

    async def test_custom_route_handler__converts_request_validation_error(self):
        mock_request = MagicMock()
        self.mock_original_route_handler.side_effect = [RequestValidationError(
            errors=[{"loc": ["body", "example"], "msg": "example message"}]
        )]

        result = await self.mock_route_handler(mock_request)
        contents = json.loads(result.body)

        self.assertEqual(400, result.status_code)
        self.assertEqual(".example: example message", contents["errors"][0]["reason"])

    async def test_custom_route_handler__raises_unhandled_exception(self):
        mock_request = MagicMock()
        exception_message = "Internal Server Error"
        self.mock_original_route_handler.side_effect = [Exception(exception_message)]

        exception_result = None
        try:
            await self.mock_route_handler(mock_request)
            self.assertTrue(False, "No exception raised")
        except Exception as e:
            exception_result = e

        self.assertIsNotNone(exception_result)
        self.assertEqual(exception_message, exception_result.args[0])

    def test_generate_error_reason_from_validation_error__converts_string_path_parts(self):
        mock_error = {"loc": ["body", "with", "a", "long", "path"], "msg": "example message"}
        expected_message = ".with.a.long.path: example message"

        reason = generate_error_reason_from_validation_error(mock_error)

        self.assertEqual(expected_message, reason)

    def test_generate_error_reason_from_validation_error__converts_integer_path_parts(self):
        mock_error = {"loc": ["body", "map", 4, 2], "msg": "example message"}
        expected_message = ".map[4][2]: example message"

        reason = generate_error_reason_from_validation_error(mock_error)

        self.assertEqual(expected_message, reason)
