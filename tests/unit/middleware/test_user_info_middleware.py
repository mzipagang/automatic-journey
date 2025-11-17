from typing import Awaitable
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock
from app.common.context.context import user_context

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.common.middleware.user_info_middleware import UserInfoMiddleware


class TestUserInfoMiddleware(IsolatedAsyncioTestCase):
    __TEST_TOKEN = ('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3O'
                    'DkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dp'
                    'biI6InRlc3RAZW1haWwuY29tIn0.ahNow0G6kDZUiQ2FwnNEDCvhmcJ6Binc95E2O8FE5i4')
    __mock_app: MagicMock

    def setUp(self):
        self.__mock_app = MagicMock()

    @pytest.mark.asyncio
    async def test_dispatch__should_add_username_to_context(
            self):
        user_info_middleware = UserInfoMiddleware(app=self.__mock_app)

        request = MagicMock(
            headers={'Authorization': f'Bearer {self.__TEST_TOKEN}'},
            url=MagicMock(path='/a/real/path')
        )

        await user_info_middleware.dispatch(request, call_next)

        self.assertEqual({'username': 'test@email.com'}, user_context.get())

    @pytest.mark.asyncio
    async def test_dispatch__liveness_endpoint__should_not_add_username_to_context(
            self):
        await self.__no_context_update_for_skipped_endpoint_assertion('/api/health/liveness')

    @pytest.mark.asyncio
    async def test_dispatch__readiness_endpoint__should_not_add_username_to_context(
            self):
        await self.__no_context_update_for_skipped_endpoint_assertion('/api/health/readiness')

    async def __no_context_update_for_skipped_endpoint_assertion(self, path: str):
        user_info_middleware = UserInfoMiddleware(app=self.__mock_app)
        user_context.set('abcdefg12345')

        request = MagicMock(
            headers={'Authorization': f'Bearer {self.__TEST_TOKEN}'},
            url=MagicMock(path=path)
        )

        await user_info_middleware.dispatch(request, call_next)

        self.assertEqual('abcdefg12345', user_context.get())


def call_next(a: Request) -> Awaitable[Response]:
    return AwaitableMock()


class AwaitableMock(Awaitable):
    def __await__(self):
        return iter([])



