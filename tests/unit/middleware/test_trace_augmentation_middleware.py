from typing import Awaitable
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from app.common.middleware.trace_augmentation_middleware import TraceAugmentationMiddleware
from tests.utils_for_testing.utils import encode_dict_as_jwt


class TestTraceAugmentationMiddleware(IsolatedAsyncioTestCase):
    __test_token: str

    __mock_app: MagicMock

    def setUp(self):
        self.__test_token = encode_dict_as_jwt({"cid": "1234567890", "login": "test@login.invalid"})
        self.__mock_app = MagicMock()

    @patch('ddtrace.Tracer.trace')
    async def test_dispatch__should_add_client_id_to_span(
            self,
            mock_trace: MagicMock
    ):
        trace_augmentation_middleware = TraceAugmentationMiddleware(app=self.__mock_app)

        request = MagicMock(
            headers={'Authorization': f'Bearer {self.__test_token}'},
            url=MagicMock(path='/a/real/path')
        )

        await trace_augmentation_middleware.dispatch(request, call_next)

        mock_trace.assert_called_once_with("web.request")
        self.assertEqual(("http.client_id", '1234567890'), mock_trace.mock_calls[2].args)

    @patch('ddtrace.Tracer.trace')
    async def test_dispatch__no_cid_in_token__should_add_None_as_cid(
            self,
            mock_trace: MagicMock
    ):
        trace_augmentation_middleware = TraceAugmentationMiddleware(app=self.__mock_app)

        request = MagicMock(
            headers={'Authorization': f'Bearer {encode_dict_as_jwt({"login": "test2@login.invalid"})}'},
            url=MagicMock(path='/a/real/path')
        )

        await trace_augmentation_middleware.dispatch(request, call_next)

        self.assertEqual(("http.client_id", None), mock_trace.mock_calls[2].args)





def call_next(a: Request):
    return AwaitableMock()

class AwaitableMock(Awaitable):
    def __await__(self):
        return iter([])
