from typing import List

from redis.exceptions import ConnectionError, TimeoutError

from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from app.common.decorators.harness_locked import locked

class TestLocked(IsolatedAsyncioTestCase):
    __mock_func: MagicMock
    __mock_logger: MagicMock
    __mock_redis_database: AsyncMock

    def setUp(self):
        self.__mock_func = MagicMock()
        self.__mock_logger = MagicMock()
        self.__mock_redis_database = AsyncMock()

    async def test__harness_flag_on__should_call(self):

        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[True],
            mock_fetch_multivariate_return_value={
                'enabled': True, 'lock_prefix': 'test_lock_prefix', 'lock_wait_seconds': 1, 'lock_max_retries': 3}
        )

    async def test__harness_flag_on__first_lock_acquire_failed__should_call_twice(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[False, True],
            mock_fetch_multivariate_return_value={
                'enabled': True, 'lock_prefix': 'test_lock_prefix', 'lock_wait_seconds': 1, 'lock_max_retries': 3}
        )

    async def test__harness_flag_off__should_await_decorated_function(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[False],
            mock_fetch_multivariate_return_value={'enabled': False}
        )

    async def test__harness_flag_on__redis_connection_error(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[True],
            raise_lock_error=ConnectionError("Redis Connection Error"),
            mock_fetch_multivariate_return_value={
                'enabled': True, 'lock_prefix': 'test_lock_prefix', 'lock_wait_seconds': 1, 'lock_max_retries': 3}
        )

    async def test__harness_flag_on__redis_timeout_error(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[True],
            raise_lock_error=TimeoutError("Redis Timeout Error"),
            mock_fetch_multivariate_return_value={
                'enabled': True, 'lock_prefix': 'test_lock_prefix', 'lock_wait_seconds': 1, 'lock_max_retries': 3}
        )

    @patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag')
    @patch('redis.asyncio.lock.Lock.__new__', return_value=AsyncMock())
    async def __locked_method_assertions(
            self,
            mock_redis_lock_new: AsyncMock,
            mock_fetch_multivariate_flag: MagicMock,
            mock_func_return_value: str,
            mock_lock_acquire_side_effect: List[bool],
            mock_fetch_multivariate_return_value: dict,
            raise_lock_error = None,
    ):
        enabled = mock_fetch_multivariate_return_value.get('enabled', False)
        self.__mock_func.return_value = mock_func_return_value

        mock_lock: AsyncMock = AsyncMock()
        if raise_lock_error:
            mock_redis_lock_new.side_effect = [raise_lock_error]
        else:
            mock_lock.acquire.side_effect = mock_lock_acquire_side_effect
            mock_redis_lock_new.return_value = mock_lock

        mock_fetch_multivariate_flag.return_value = mock_fetch_multivariate_return_value

        @locked(
            lock_config_name='lock_config_name',
            logger=self.__mock_logger,
            entity_id_name='entity_id_name',
            redis_database=self.__mock_redis_database)
        async def test_func(entity_id_name: int):
            return self.__mock_func(abc=entity_id_name)

        if raise_lock_error:
            with self.assertRaises(Exception):
                await test_func(entity_id_name=1)
                self.__mock_func.assert_not_called_once_with(abc=1)
            if isinstance(raise_lock_error, TimeoutError):
                self.__mock_logger.critical.assert_called_with('Redis timeout error!', extra={
                    'monitored_transaction': {'name': 'REDIS-TIMEOUT', 'method': 'harness_locked.locked',
                                              'error': 'Redis Timeout Error'}})
            elif isinstance(raise_lock_error, ConnectionError):
                self.__mock_logger.critical.assert_called_with('Redis connection error!', extra={
                    'monitored_transaction': {'name': 'REDIS-CONNECTION', 'method': 'harness_locked.locked',
                                              'error': 'Redis Connection Error'}})
        else:
            result = await test_func(entity_id_name=1)
            self.__mock_func.assert_called_once_with(abc=1)
            self.assertEqual(result, mock_func_return_value)

        mock_fetch_multivariate_flag.assert_called_once_with(flag_name='lock_config_name', target_id='default')

        if enabled:
            mock_redis_lock_new.assert_called_once()
            self.__mock_redis_database.async_engine.assert_called_once()
        else:
            mock_redis_lock_new.assert_not_called()
            self.__mock_redis_database.async_engine.assert_not_called()
