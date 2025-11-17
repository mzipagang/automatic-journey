from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestHealthIntegration(TestCase):
    __client: TestClient

    @patch("app.common.services.http_connection_service.HttpConnectionService.__new__")
    def setUp(self, http_connection_new: MagicMock):
        from app.main import app
        self.__client = TestClient(app)

    def test_health_liveness(self):
        response = self.__client.get("/api/health/liveness")
        assert response.status_code == 200

    @patch("app.common.database.async_client.AsyncRedisClientService.ping")
    def test_health_readiness_success_response(
            self,
            mock_redis_ping: MagicMock):
        mock_redis_ping.return_value = True

        response = self.__client.get("/api/health/readiness")
        assert response.status_code == 200

    @patch("app.common.database.async_client.AsyncRedisClientService.ping")
    def test_health_readiness_error_response(
            self,
            mock_redis_ping: MagicMock):
        mock_redis_ping.return_value = False

        response = self.__client.get("/api/health/readiness")
        assert response.status_code == 503
