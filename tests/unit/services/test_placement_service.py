import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from app.common.database.async_client import RedisKeyTypes
from app.common.services.placement_service import PlacementService


class TestPlacementService(IsolatedAsyncioTestCase):
    __mock_internal_http_client_service: MagicMock

    def setUp(self):
        self.mock_config_service = MagicMock()
        self.mock_redis_cache = AsyncMock()
        self.__mock_internal_http_client_service = MagicMock()

        self.placement_service = PlacementService(
            config_service=self.mock_config_service,
            redis_cache=self.mock_redis_cache,
            external_api_http_client_service=self.__mock_internal_http_client_service
        )

    async def test_get_cache_placement(self):
        placement_id = "123"
        cached_data = '{"id": 123, "name": "Test Placement"}'
        self.mock_redis_cache.get.return_value = cached_data

        result = await self.placement_service.get_cache_placement(placement_id)

        self.assertEqual(result, json.loads(cached_data))
        self.mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.PLACEMENT, placement_id)

    async def test_get_placements__should_raise_value_error_if_base_api_url_is_none(self):
        self.mock_config_service.get_current_config.return_value = MagicMock(base_api_url=None)

        with self.assertRaises(ValueError) as context:
            await self.placement_service.get_placements()

        self.assertEqual(str(context.exception), "API url is not found")

    async def test_get_placements__should_return_placements_on_success(self):
        self.mock_redis_cache.get.side_effect = [None, None, None]
        self.mock_redis_cache.assign_numeric_id.side_effect = [1, 2, 3]

        placements = await self.placement_service.get_placements()

        self.assertEqual(len(placements), 3)
        self.assertEqual(placements[0].id, 1)
        self.assertEqual(placements[0].name, "Search & Browse")
        self.assertEqual(placements[0].priceFloor, 0.5)
        self.assertEqual(placements[1].id, 2)
        self.assertEqual(placements[1].name, "Basket Builder")
        self.assertEqual(placements[1].priceFloor, 0.6)
        self.assertEqual(placements[2].id, 3)
        self.assertEqual(placements[2].name, "Savings")
        self.assertEqual(placements[2].priceFloor, 0.3)
