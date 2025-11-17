from typing import List
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from app.common.decorators.locked import locked
from app.common.model.configuration import LockConfig
from app.common.services.config_service import Config


class TestLocked(IsolatedAsyncioTestCase):
    __mock_func: MagicMock
    __mock_logger: MagicMock
    __mock_redis_database: AsyncMock

    def setUp(self):
        self.__mock_func = MagicMock()
        self.__mock_logger = MagicMock()
        self.__mock_redis_database = AsyncMock()

    async def test__update_activation_lock_config__should_lock(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[True],
            mock_update_activation_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="activation"),
            mock_update_campaign_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="campaign"),
            entity_id_name='adgroup_id',
        )

    async def test__update_activation_lock_config__should_not_lock(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[True],
            mock_update_activation_lock_config=LockConfig(enabled=False, expire_seconds=45, lock_prefix="activation"),
            mock_update_campaign_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="campaign"),
            entity_id_name='adgroup_id',
        )

    async def test__update_campaign_lock_config__should_lock(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[True],
            mock_update_activation_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="activation"),
            mock_update_campaign_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="campaign"),
            entity_id_name='campaign_id',
        )

    async def test__update_campaign_lock_config__should_not_lock(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[True],
            mock_update_activation_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="activation"),
            mock_update_campaign_lock_config=LockConfig(enabled=False, expire_seconds=45, lock_prefix="campaign"),
            entity_id_name='campaign_id',
        )

    async def test__update_activation_lock_config__first_lock_acquire_failed__should_call_twice(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[False, True],
            mock_update_activation_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="activation"),
            mock_update_campaign_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="campaign"),
            entity_id_name='adgroup_id',
        )

    async def test__update_campaign_lock_config__first_lock_acquire_failed__should_call_twice(self):
        await self.__locked_method_assertions(
            mock_func_return_value='success',
            mock_lock_acquire_side_effect=[False, True],
            mock_update_activation_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="activation"),
            mock_update_campaign_lock_config=LockConfig(enabled=True, expire_seconds=45, lock_prefix="campaign"),
            entity_id_name='campaign_id',
        )

    @patch('app.common.services.config_service.ConfigService.get_current_config')
    @patch('redis.asyncio.lock.Lock.__new__', return_value=AsyncMock())
    async def __locked_method_assertions(
            self,
            mock_redis_lock_new: AsyncMock,
            mock_get_current_config: MagicMock,
            mock_func_return_value: str,
            mock_lock_acquire_side_effect: List[bool],
            mock_update_activation_lock_config: LockConfig,
            mock_update_campaign_lock_config: LockConfig,
            entity_id_name: str,
    ):
        enabled = mock_update_campaign_lock_config.enabled if entity_id_name == 'campaign_id' else mock_update_activation_lock_config.enabled

        config = Config("", "", "", "")
        config.update_activation_lock_config = mock_update_activation_lock_config
        config.update_campaign_lock_config = mock_update_campaign_lock_config
        mock_get_current_config.return_value = config

        self.__mock_func.return_value = mock_func_return_value

        mock_lock: MagicMock = MagicMock()
        mock_lock.acquire.side_effect = mock_lock_acquire_side_effect
        mock_redis_lock_new.return_value = mock_lock


        @locked(
            logger=self.__mock_logger,
            entity_id_name=entity_id_name,
            redis_database=self.__mock_redis_database)
        async def test_func(adgroupId: str, campaign_id: str):
            return self.__mock_func(adgroupId, campaign_id)

        result = await test_func("test_adgroupId", "test_campaign_id")

        self.__mock_func.assert_called_once_with("test_adgroupId", "test_campaign_id")


        if enabled:
            mock_redis_lock_new.assert_called_once()
            self.__mock_redis_database.async_engine.assert_called_once()
        else:
            mock_redis_lock_new.assert_not_called()
            self.__mock_redis_database.async_engine.assert_not_called()

        self.assertEqual(result, mock_func_return_value)
