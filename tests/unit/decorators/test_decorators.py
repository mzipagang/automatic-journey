from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.common.cache.coders import PydanticCoderFactory
from app.common.decorators.decorators import feature_flag, conditional_cache
from app.common.model.redis import CachedRedisAdvertiser


class TestFeatureFlagDecorator(IsolatedAsyncioTestCase):

    @patch('app.common.decorators.decorators.HarnessService')
    async def test_feature_flag_enabled(self, mock_harness_service: MagicMock):
        # Arrange
        feature_name = 'test_feature'
        target_identifier = 'test_target'
        mock_harness_service.is_harness_flag_on.return_value = True

        @feature_flag(feature_name, target_identifier, harness_service=mock_harness_service)
        async def test_function():
            return 'Feature enabled'

        # Act
        result = await test_function()

        # Assert
        self.assertEqual(result, 'Feature enabled')

    @patch('app.common.decorators.decorators.HarnessService')
    async def test_feature_flag_disabled(self, mock_harness_service: MagicMock):
        # Arrange
        feature_name = 'test_feature'
        target_identifier = 'test_target'
        mock_harness_service.is_harness_flag_on.return_value = False

        @feature_flag(feature_name, target_identifier, harness_service=mock_harness_service)
        async def test_function():
            return 'Feature enabled'

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await test_function()

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, f"Feature {feature_name} is disabled on this environment.")

    async def test_conditional_cache__calls_cache_when_enabled(self):
        FastAPICache.init(backend=InMemoryBackend(), prefix="test")
        mock_key_builder = MagicMock()
        mock_harness_service = MagicMock()
        mock_upstream = MagicMock()
        mock_response = CachedRedisAdvertiser(
            brandId="1234",
            displayName="Brand",
            salesforceId="SF01",
            client=None
        )
        mock_coder = PydanticCoderFactory[CachedRedisAdvertiser].build(CachedRedisAdvertiser)
        @conditional_cache(
            key_builder=mock_key_builder,
            harness_service=mock_harness_service,
            coder=mock_coder,
        )
        async def test_fn(*args, **kwargs):
            mock_upstream()
            return mock_response

        mock_key_builder.return_value = "mock_key"
        mock_harness_service.fetch_multivariate_flag.return_value = {
            "enabled": True,
            "ttl": 100
        }
        enabled_result = await test_fn("args", kv="args")

        self.assertEqual(mock_response, enabled_result)
        mock_harness_service.fetch_multivariate_flag.assert_called_with(
            "kpa_cache_config",
            "default"
        )
        mock_key_builder.assert_called()
        mock_upstream.assert_called_once()
        mock_upstream.reset_mock()

        cached_result = await test_fn("args", kv="args")
        self.assertEqual(mock_response, cached_result)
        mock_upstream.assert_not_called()

        # Clean up after the test
        FastAPICache.reset()
