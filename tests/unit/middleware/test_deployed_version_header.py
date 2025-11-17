import asyncio

from app.common.middleware.deployed_version_middleware import DeployedVersionMiddleware


class TestDeployedVersionMiddleware:
    def test_deployed_version_header(self):
        async def app():
            pass
        middleware = DeployedVersionMiddleware(app)

        async def call_next(request):
            class DummyResponse:
                def __init__(self):
                    self.headers = {}
            return DummyResponse()

        class DummyRequest:
            pass

        request = DummyRequest()
        response = asyncio.run(middleware.dispatch(request, call_next))

        assert "X-Deployed-Version" in response.headers
        assert response.headers["X-Deployed-Version"] is not None
        assert response.headers["X-Deployed-Version"] != ''



    def test_deployed_version_header_from_environ(self):
        import os

        # Set environment variable for testing
        os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.version=test_version"

        print("environ 1", os.environ)

        async def app():
            pass
        middleware = DeployedVersionMiddleware(app)

        async def call_next(request):
            class DummyResponse:
                def __init__(self):
                    self.headers = {}
            return DummyResponse()

        class DummyRequest:
            pass

        request = DummyRequest()
        response = asyncio.run(middleware.dispatch(request, call_next))

        assert response.headers["X-Deployed-Version"] == "test_version"

        # Clean up environment variable
        del os.environ["OTEL_RESOURCE_ATTRIBUTES"]

