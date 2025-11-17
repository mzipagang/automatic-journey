from unittest import TestCase
from unittest.mock import MagicMock

from fastapi import HTTPException
from httpx import Response, Request

from app.common.model.downstream.bid_manager import CreateBidsResponse
from app.common.utils.response_handler import ResponseHandlerBuilder, ResponseHandler, DefaultResponseHandler


class TestResponseHandler(TestCase):
    @staticmethod
    def __mock_response(**kwargs):
        mock_url = "https://api-stg.8451.com/media/pla"
        default_request = Request(method="GET", url=mock_url)
        default_args = {
            "status_code": 200,
            "content": "success",
            "request": default_request
        }
        return Response(**{
            **default_args,
            **kwargs
        })
    def test_response_handler__starts_with_default_handler(self):
        builder = ResponseHandlerBuilder()
        handler = builder.build()
        mock_response = self.__mock_response()

        with self.assertRaises(HTTPException) as context:
            handler.handle_response(mock_response, None)


        self.assertEqual([], handler.handlers)
        self.assertEqual(ResponseHandler.unhandled_response, handler.default_handler)
        self.assertIsNotNone(context)
        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Unexpected error processing response", context.exception.detail)

    def test_response_handler__uses_unhandled_response_if_default_is_none(self):
        builder = ResponseHandlerBuilder()
        handler = builder.handle_default(None).build()
        mock_response = self.__mock_response()

        with self.assertRaises(HTTPException) as context:
            handler.handle_response(mock_response, None)

        self.assertEqual([], handler.handlers)
        self.assertIsNotNone(context)
        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Unexpected error processing response", context.exception.detail)

    def test_response_handler__handles_condition(self):
        mock_predicate = MagicMock(return_value=True)
        mock_handler = MagicMock(return_value=True)
        builder = ResponseHandlerBuilder()
        handler = builder.handle_condition(mock_predicate, mock_handler).build()
        mock_response = self.__mock_response()
        mock_extra = MagicMock()

        result = handler.handle_response(mock_response, mock_extra)

        self.assertTrue(result)
        mock_predicate.assert_called_once_with(mock_response, mock_extra)
        mock_handler.assert_called_once_with(mock_response, mock_extra)

    def test_response_handler__handles_status(self):
        mock_handler = MagicMock(return_value=True)
        builder = ResponseHandlerBuilder()
        handler = builder.handle_status(200, mock_handler).build()
        mock_response = self.__mock_response()
        mock_extra = MagicMock()

        result = handler.handle_response(mock_response, mock_extra)

        self.assertTrue(result)
        mock_handler.assert_called_once_with(mock_response, mock_extra)

    def test_response_handler__uses_default_handler(self):
        mock_status_handler = MagicMock(return_value="status")
        mock_default_handler = MagicMock(return_value="default")
        handler = ResponseHandlerBuilder()\
            .handle_status(400, mock_status_handler) \
            .handle_default(mock_default_handler)\
            .build()
        mock_response = self.__mock_response()
        mock_extra = MagicMock()

        result = handler.handle_response(mock_response, mock_extra)

        self.assertEqual("default", result)
        mock_status_handler.assert_not_called()
        mock_default_handler.assert_called_once_with(mock_response, mock_extra)

    def test_response_handler__handles_success(self):
        mock_handler = MagicMock(return_value=True)
        handler = ResponseHandlerBuilder()\
            .handle_success(mock_handler)\
            .build()
        mock_response = self.__mock_response()
        mock_extra = MagicMock()

        result = handler.handle_response(mock_response, mock_extra)

        self.assertTrue(result)
        mock_handler.assert_called_once_with(mock_response, mock_extra)

    def test_response_handler__handles_client_error(self):
        mock_handler = MagicMock(return_value=True)
        handler = ResponseHandlerBuilder()\
            .handle_client_error(mock_handler)\
            .build()
        mock_response = self.__mock_response(status_code=404)
        mock_extra = MagicMock()

        result = handler.handle_response(mock_response, mock_extra)

        self.assertTrue(result)
        mock_handler.assert_called_once_with(mock_response, mock_extra)

    def test_response_handler__handles_server_error(self):
        mock_handler = MagicMock(return_value=True)
        handler = ResponseHandlerBuilder()\
            .handle_server_error(mock_handler)\
            .build()
        mock_response = self.__mock_response(status_code=504)
        mock_extra = MagicMock()

        result = handler.handle_response(mock_response, mock_extra)

        self.assertTrue(result)
        mock_handler.assert_called_once_with(mock_response, mock_extra)

    def test_response_handler__handles_response_data(self):
        handler = ResponseHandlerBuilder()\
            .handle_data(CreateBidsResponse)\
            .build()
        mock_data = CreateBidsResponse(id="1234")
        mock_response = self.__mock_response(content=mock_data.model_dump_json())
        mock_extra = MagicMock()

        result = handler.handle_response(mock_response, mock_extra)

        self.assertEqual(mock_data, result)

    def test_response_handler__handles_response_with_appended_handler(self):
        handler = ResponseHandlerBuilder() \
            .handle_data(CreateBidsResponse)\
            .append_handler(DefaultResponseHandler)\
            .build()
        mock_data = CreateBidsResponse(id="1234")
        mock_data_response = self.__mock_response(content=mock_data.model_dump_json())
        mock_client_error_response = self.__mock_response(status_code=404)
        mock_server_error_response = self.__mock_response(status_code=500)
        mock_unhandled_response = self.__mock_response(status_code=302)
        mock_extra = MagicMock()

        data_result = handler.handle_response(mock_data_response, mock_extra)

        with self.assertRaises(HTTPException) as client_error:
            handler.handle_response(mock_client_error_response, mock_extra)

        with self.assertRaises(HTTPException) as server_error:
            handler.handle_response(mock_server_error_response, mock_extra)

        with self.assertRaises(HTTPException) as unhandled_error:
            handler.handle_response(mock_unhandled_response, mock_extra)

        self.assertEqual(mock_data, data_result)
        self.assertIsNotNone(client_error)
        self.assertIsNotNone(server_error)
        self.assertIsNotNone(unhandled_error)

        self.assertEqual(404, client_error.exception.status_code)
        self.assertEqual(503, server_error.exception.status_code)
        self.assertEqual(500, unhandled_error.exception.status_code)