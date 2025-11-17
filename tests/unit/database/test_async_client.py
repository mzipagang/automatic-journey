from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch, call, MagicMock

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.common.database.async_client import AsyncRedisClientService, RedisKeyTypes

MOCK_CONFIG = MagicMock()
MOCK_CONFIG.redis_host = 'localhost'
MOCK_CONFIG.redis_port = 6379
MOCK_CONFIG.redis_db = 0
MOCK_CONFIG.redis_primary_access_key = 'password'
MOCK_CONFIG.redis_ssl = False
MOCK_CONFIG.redis_socket_timeout = 10
MOCK_CONFIG.redis_socket_connect_timeout = 10
MOCK_CONFIG.redis_health_check_interval = 30

@pytest.mark.asyncio
@patch('app.common.database.async_client.ConfigService')
@patch('app.common.database.async_client.redis_async_client.Redis', new_callable=AsyncMock)
class TestAsyncRedisClient(IsolatedAsyncioTestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog
        self.async_redis_client_service = AsyncRedisClientService()
        self.async_redis_client_service.reset()

    async def test_async_engine_success(self, mock_redis, mock_config_service):
        # Arrange
        mock_config_service.return_value.get_current_config.return_value = MOCK_CONFIG

        # Act
        client = await self.async_redis_client_service.async_engine()


        # Assert
        mock_redis.assert_awaited_once_with(
            host='localhost',
            port=6379,
            db=0,
            password='password',
            ssl=False,
            health_check_interval= 30,
            socket_keepalive=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        self.assertEqual(client, mock_redis.return_value)

    async def test_mget__should_succeed(self, mock_redis: AsyncMock, mock_config_service: MagicMock):
        keys = ["key1", "key2"]
        complete_keys = [f"{RedisKeyTypes.PRODUCT}:{key}" for key in keys]
        mock_config_service.return_value.get_current_config.return_value = MOCK_CONFIG
        mock_redis.return_value.mget.return_value = [b'value1', b'value2']

        await self.async_redis_client_service.async_engine()
        result = await self.async_redis_client_service.mget(RedisKeyTypes.PRODUCT, keys)

        mock_redis.return_value.mget.assert_called_once_with(complete_keys)
        self.assertEqual(['value1', 'value2'], result)

    async def test_mget__Nones_found__should_succeed(self, mock_redis: AsyncMock, mock_config_service: MagicMock):
        keys = ["key1", "key2"]
        complete_keys = [f"{RedisKeyTypes.PRODUCT}:{key}" for key in keys]
        mock_config_service.return_value.get_current_config.return_value = MOCK_CONFIG
        mock_redis.return_value.mget.return_value = [b'value1', None]

        await self.async_redis_client_service.async_engine()
        result = await self.async_redis_client_service.mget(RedisKeyTypes.PRODUCT, keys)
        
        mock_redis.return_value.mget.assert_called_once_with(complete_keys)
        self.assertEqual(['value1', None], result)

    async def test_async_engine_mset_success(self, mock_redis, mock_config_service):
        # Arrange
        keys = {"test": "value", "test2": "value2"}
        mock_config_service.return_value.get_current_config.return_value = MOCK_CONFIG


        # Act
        await self.async_redis_client_service.async_engine()
        await self.async_redis_client_service.mset(keys)

        # Assert
        expected_call = call().mset(keys)
        self.assertIn(expected_call, mock_redis.mock_calls)

    async def test_async_engine_redis_error(self, mock_redis, mock_config_service):
        # Arrange
        mock_config = AsyncMock()
        mock_config_service.return_value.get_current_config.return_value = mock_config
        mock_redis.side_effect = RedisError

        # Act
        client = await self.async_redis_client_service.async_engine()

        # Assert
        self.assertIsNone(client)
        self.assertIn("Redis connection error!", self._caplog.text)

    async def test_assign_numeric_id_batch(self, mock_redis, mock_config_service):
        # Arrange
        mock_config_service.return_value.get_current_config.return_value = MOCK_CONFIG
        expected_result = [1, 2, 3]

        # Act
        await self.async_redis_client_service.async_engine()
        mock_redis.return_value.incr.return_value = 1
        result = await self.async_redis_client_service.assign_numeric_id_batch("TEST", ["1", "2", "3"])

        # Assert
        self.assertEqual(result, expected_result)
        mock_redis.assert_called_with = [
            call().incr('TEST:id'),
            call().incrby('TEST:id', 2),
            call().mset({'TEST:1': 1, 'TEST:2': 2, 'TEST:3': 3})
        ]

    async def test_assign_internal_id_batch(self, mock_redis, mock_config_service):
        # Arrange
        keys = {"key1": "value1", "key2": "value2"}
        mock_config_service.return_value.get_current_config.return_value = MOCK_CONFIG

        # Act
        await self.async_redis_client_service.async_engine()
        await self.async_redis_client_service.cache_internal_id_batch(keys)

        # Assert
        self.assertIn(call().mset({'key1': 'value1', 'key2': 'value2'}), mock_redis.mock_calls)

    @pytest.mark.asyncio
    async def test_ping_raises_timeout_error(self, mock_redis, mock_config_service):
        self.async_redis_client_service._async_client = AsyncMock()
        self.async_redis_client_service._async_client.ping.side_effect = RedisTimeoutError("Timeout!")

        with self.assertRaises(HTTPException) as context:
            await self.async_redis_client_service.ping()
        self.assertEqual(503, context.exception.status_code)

    @pytest.mark.asyncio
    async def test_cache_internal_id_redis_timeout_error(self, mock_redis, mock_config_service):
        service = self.async_redis_client_service
        service._async_client = AsyncMock()
        service._async_client.set.side_effect = RedisTimeoutError("Timeout")

        with patch("logging.Logger.critical") as mock_critical:
            with self.assertRaises(HTTPException) as context:
                await service.cache_internal_id("TEST", 1, "value")
            mock_critical.assert_called_once()
            self.assertEqual(503, context.exception.status_code)