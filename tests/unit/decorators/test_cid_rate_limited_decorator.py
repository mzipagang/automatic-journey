from unittest.async_case import IsolatedAsyncioTestCase

from typing import List
from unittest.mock import AsyncMock, MagicMock

from app.common.decorators.cid_rate_limited import cid_rate_limited
from app.common.exceptions import RateLimitExceededException


class TestCidRateLimitedDecorator(IsolatedAsyncioTestCase):
    __mock_func: AsyncMock
    __mock_redis_database_service: AsyncMock
    __mock_redis_engine: AsyncMock
    __mock_logger: MagicMock
    __mock_harness_service: MagicMock
    __mock_redis_async_client: AsyncMock

    def setUp(self):
        self.__mock_func = AsyncMock()
        self.__mock_redis_database_service = AsyncMock()
        self.__mock_logger = MagicMock()
        self.__mock_harness_service = MagicMock()
        self.__mock_redis_async_client = AsyncMock()

        self.__mock_redis_database_service.async_engine.return_value = self.__mock_redis_async_client

    async def test__harness_flag_off__should_not_apply(self):
        await self.__decorator_assertions(
            mock_return_value='test_return_value',
            redis_exists_values=[True],
            redis_get_values=[b'1'],
            mock_harness_fetch_multivariate_return_value={
                'enabled': False,
                'requests_per_minute': 10,
                'rate_limit_prefix': 'test_rate_limit_prefix'}
        )

    async def test__harness_flag_on__under_limit__should_apply_and_succeed(self):
        await self.__decorator_assertions(
            mock_return_value='test_return_value',
            redis_exists_values=[True],
            redis_get_values=[b'1'],
            mock_harness_fetch_multivariate_return_value={
                'enabled': True,
                'requests_per_minute': 10,
                'rate_limit_prefix': 'test_rate_limit_prefix'}
        )

    async def test__harness_on__limit_reached__should_throw(self):
        await self.__decorator_assertions(
            mock_return_value='test_return_value',
            redis_exists_values=[True],
            redis_get_values=[b'10'],
            mock_harness_fetch_multivariate_return_value={
                'enabled': True,
                'requests_per_minute': 10,
                'rate_limit_prefix': 'test_rate_limit_prefix'},
            expected_exception=RateLimitExceededException(client_id='default')
        )

    async def test_missing_ttl__should_still_function(self):
        self.__mock_harness_service.fetch_multivariate_flag.return_value = {
            'enabled': True,
            'requests_per_minute': 10,
            'rate_limit_prefix': 'test_rate_limit_prefix'}
        self.__mock_redis_async_client.get.return_value = b'11'

        self.__mock_redis_async_client.ttl.return_value = -1

        @cid_rate_limited(
            config_name='test_config_name',
            logger=self.__mock_logger,
            harness_service=self.__mock_harness_service,
            redis_database_service=self.__mock_redis_database_service
        )
        async def test_func():
            return 'test_return_value'

        result = await test_func()

        self.__mock_redis_async_client.set.assert_called_once()

        self.assertEqual(result, 'test_return_value')

    async def test_get_none_after_exists_true__resets_counter(self):
        # Arrange
        self.__mock_harness_service.fetch_multivariate_flag.return_value = {
            'enabled': True,
            'requests_per_minute': 10,
            'rate_limit_prefix': 'test_rate_limit_prefix'}
        self.__mock_redis_async_client.exists.return_value = True
        self.__mock_redis_async_client.get.return_value = None
        self.__mock_redis_async_client.ttl.return_value = 60


        @cid_rate_limited(
            config_name='test_config_name',
            logger=self.__mock_logger,
            harness_service=self.__mock_harness_service,
            redis_database_service=self.__mock_redis_database_service
        )
        async def test_func():
            return 'test_return_value'

        # Act
        result = await test_func()

        # Assert
        self.__mock_redis_async_client.set.assert_called_once()
        self.assertEqual(result, 'test_return_value')


    async def __decorator_assertions(
            self,
            mock_return_value: str,
            redis_exists_values: List[bool],
            redis_get_values: List[bytes],
            mock_harness_fetch_multivariate_return_value: dict,
            expected_exception: Exception = None
    ):
        self.__mock_redis_async_client.exists.side_effect = redis_exists_values
        self.__mock_redis_async_client.get.side_effect = redis_get_values
        self.__mock_redis_async_client.ttl.return_value = 60
        self.__mock_harness_service.fetch_multivariate_flag.return_value = (
            mock_harness_fetch_multivariate_return_value)

        @cid_rate_limited(
            config_name='test_config_name',
            logger=self.__mock_logger,
            harness_service=self.__mock_harness_service,
            redis_database_service=self.__mock_redis_database_service
        )
        async def test_func():
            return mock_return_value

        if expected_exception:
            with self.assertRaises(expected_exception.__class__) as context:
                await test_func()

            self.assertEqual(str(expected_exception), str(context.exception))
        else:
            result = await test_func()
            self.assertEqual(result, mock_return_value)

        self.__mock_harness_service.fetch_multivariate_flag.assert_called_once_with(
            flag_name='test_config_name', target_id='default')

        if mock_harness_fetch_multivariate_return_value.get('enabled'):
            self.__mock_redis_async_client.get.assert_called_once()
        else:
            self.__mock_redis_async_client.get.assert_not_called()
