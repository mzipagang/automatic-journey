from json import dumps
from json import JSONDecodeError
from typing import Awaitable
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from fastapi import FastAPI
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from app.v2.middleware.ad_group_discriminator_middleware import AdGroupDiscriminatorMiddleware
from tests.unit.middleware.test_trace_augmentation_middleware import AwaitableMock


class TestAdGroupDiscriminatorMiddleware(IsolatedAsyncioTestCase):
    @staticmethod
    def call_next(a: Request) -> Awaitable[Response]:
        return AwaitableMock()
    @staticmethod
    def request_body_builder(body_content: dict):
        async def body():
            return dumps(body_content)
        return body

    def setUp(self):
        self.__mock_app = MagicMock(spec=FastAPI)

    async def test_middleware__should_identify_legacy_request(self):
        middleware = AdGroupDiscriminatorMiddleware(app=self.__mock_app)

        request = MagicMock(
            spec=Request,
            url=MagicMock(
                spec=URL,
                path="/v2/ad_groups"),
            method="POST",
            body=self.request_body_builder({'baseBid': {}, 'entities': {}}))

        await middleware.dispatch(request, call_next=self.call_next)

        self.assertEqual(
            request._body,
            dumps({'baseBid': {}, 'entities': {}, 'requestType': 'legacy'}).encode(encoding='UTF-8'))
    async def test_middleware__should_identify_incomplete_legacy_request__entities(self):
        middleware = AdGroupDiscriminatorMiddleware(app=self.__mock_app)

        request = MagicMock(
            spec=Request,
            url=MagicMock(
                spec=URL,
                path="/v2/ad_groups"),
            method="POST",
            body=self.request_body_builder({'entities': {}}))

        await middleware.dispatch(request, call_next=self.call_next)

        self.assertEqual(
            request._body,
            dumps({'entities': {}, 'requestType': 'legacy'}).encode(encoding='UTF-8'))

    async def test_middleware__should_identify_incomplete_legacy_request__baseBid(self):
        middleware = AdGroupDiscriminatorMiddleware(app=self.__mock_app)

        request = MagicMock(
            spec=Request,
            url=MagicMock(
                spec=URL,
                path="/v2/ad_groups"),
            method="POST",
            body=self.request_body_builder({'baseBid': {}}))

        await middleware.dispatch(request, call_next=self.call_next)

        self.assertEqual(
            request._body,
            dumps({'baseBid': {}, 'requestType': 'legacy'}).encode(encoding='UTF-8'))

    async def test_middleware__should_identify_updated_request(self):
        middleware = AdGroupDiscriminatorMiddleware(app=self.__mock_app)

        request = MagicMock(
            spec=Request,
            url=MagicMock(
                spec=URL,
                path="/v2/ad_groups"),
            method="POST",
            body=self.request_body_builder({}))

        await middleware.dispatch(request, call_next=self.call_next)

        self.assertEqual(
            request._body,
            dumps({'requestType': 'updated'}).encode(encoding='UTF-8'))

    async def test_middleware__should_identify_non_json_body_and_raise(self):
        def bad_body_builder():
            async def doit():
                return "notjson"
            return doit
        middleware = AdGroupDiscriminatorMiddleware(app=self.__mock_app)

        request = MagicMock(
            spec=Request,
            url=MagicMock(
                spec=URL,
                path="/v2/ad_groups"),
            method="POST",
            body=bad_body_builder())

        with self.assertRaises(JSONDecodeError):
            await middleware.dispatch(request, call_next=self.call_next)
