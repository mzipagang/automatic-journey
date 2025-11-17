import json

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from unittest.async_case import IsolatedAsyncioTestCase

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.common.model.downstream.location_groups import DivisionBannerItem
from app.common.model.redis import CachedAddress, CachedPlacement, CachedContact, CachedDivision, \
    CachedRedisAdvertiser, CachedProduct
from app.common.services.lookup_service import LookupService
from app.common.database.async_client import RedisKeyTypes
from app.common.model.division import DivisionServiceResponse


class TestLookupService(IsolatedAsyncioTestCase):
    __mock_redis_cache: AsyncMock

    def setUp(self):
        FastAPICache.init(backend=InMemoryBackend(), prefix="test")
        self.__mock_redis_cache = AsyncMock()
        self.lookup_service = LookupService(redis_cache=self.__mock_redis_cache)

    def test_str_to_model__converts_json_str_to_model(self):
        mock_model = CachedContact(id="id")
        mock_key = "mock_key"
        json_str = mock_model.model_dump_json()

        result = self.lookup_service._str_to_model(json_str, CachedContact, mock_key)

        self.assertEqual(mock_model, result)

    def test_str_to_model__returns_none_if_str_is_none(self):
        result = self.lookup_service._str_to_model(None, CachedContact, "mock_key")

        self.assertEqual(None, result)

    def test_str_to_model__returns_none_if_str_is_null(self):
        result = self.lookup_service._str_to_model("null", CachedContact, "mock_key")

        self.assertEqual(None, result)

    @patch('logging.Logger.error')
    def test_str_to_model__returns_none_and_logs_error_if_string_is_invalid_json(
            self,
            mock_logger_error
    ):
        mock_key = "mock_key"
        json_str = "invalid json"

        result = self.lookup_service._str_to_model(json_str, CachedContact, mock_key)

        self.assertEqual(None, result)
        mock_logger_error.assert_called_with(
            "Invalid json stored at %s",
            mock_key
        )

    @patch('logging.Logger.error')
    def test_str_to_model__returns_none_and_logs_error_if_model_conversion_has_unknown_error(
            self,
            mock_logger_error
    ):
        mock_key = "mock_key"
        json_str = json.dumps({})
        mock_model_class = MagicMock(side_effect=Exception("test exception"))
        mock_model_class.__name__ = "mock_model_class"

        result = self.lookup_service._str_to_model(json_str, mock_model_class, mock_key)

        self.assertEqual(None, result)
        mock_logger_error.assert_called_with(
            "Unexpected error converting json stored at %s for model %s: %s",
            mock_key,
            mock_model_class.__name__,
            'test exception',
        )

    @patch('logging.Logger.error')
    def test_str_to_model__returns_none_and_logs_error_if_model_conversion_has_value_error(
            self,
            mock_logger_error
    ):
        mock_key = "mock_key"
        json_str = json.dumps({"id": False})

        result = self.lookup_service._str_to_model(json_str, CachedContact, mock_key)

        self.assertEqual(None, result)
        mock_logger_error.assert_called_with(
            "Value error converting json stored at %s for model %s: %s",
            mock_key,
            CachedContact.__name__,
            '1 validation error for CachedContact\n'
            'id\n'
            '  Input should be a valid string [type=string_type, input_value=False, '
            'input_type=bool]\n'
            '    For further information visit '
            'https://errors.pydantic.dev/2.10/v/string_type'
        )

    @pytest.mark.asyncio
    async def test_get_campaign_short_id_by_long_id_batch(self):
        campaign_ids = ["long_id_1", "long_id_2"]
        self.__mock_redis_cache.mget.return_value = [1, None]

        result = await self.lookup_service.get_campaign_short_id_by_long_id_batch(campaign_ids)
        assert result == [1, None]
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.CAMPAIGN, campaign_ids)

    @pytest.mark.asyncio
    async def test_get_campaign_short_id_by_long_id(self):
        long_campaign_id = "long_id"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_campaign_short_id_by_long_id(long_campaign_id)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.CAMPAIGN, long_campaign_id)

    @pytest.mark.asyncio
    async def test_get_campaign_long_id_by_short_id_batch(self):
        short_ids = ["short_id_1", "short_id_2"]
        self.__mock_redis_cache.mget.return_value = ["long_id_1", None]

        result = await self.lookup_service.get_campaign_long_id_by_short_id_batch(short_ids)
        assert result == ["long_id_1", None]
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.CAMPAIGN, short_ids)

    @pytest.mark.asyncio
    async def test_get_campaign_long_id_by_short_id(self):
        short_campaign_id = 1
        self.__mock_redis_cache.get.return_value = "long_id"

        result = await self.lookup_service.get_campaign_long_id_by_short_id(short_campaign_id)
        assert result == "long_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.CAMPAIGN, short_campaign_id)

    @pytest.mark.asyncio
    async def test_get_campaign_long_id_by_internal_short_id(self):
        short_campaign_id = 1
        self.__mock_redis_cache.get.return_value = "long_id"

        result = await self.lookup_service.get_campaign_long_id_by_internal_short_id(short_campaign_id)
        assert result == "long_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.CAMPAIGN, short_campaign_id)

    @pytest.mark.asyncio
    async def test_get_campaign_long_id_by_short_adgroup_id(self):
        short_adgroup_id = 12345
        self.__mock_redis_cache.get.return_value = "long_campaign_id"

        result = await self.lookup_service.get_campaign_long_id_by_short_adgroup_id(short_adgroup_id)
        assert result == "long_campaign_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.AD_GROUP, f"{RedisKeyTypes.CAMPAIGN}:{short_adgroup_id}")

    @pytest.mark.asyncio
    async def test_get_koddi_campaign_id_by_short_id_batch(self):
        short_ids = ["short_id_1", "short_id_2"]
        self.__mock_redis_cache.mget.return_value = ["koddi_id_1", "koddi_id_2"]

        result = await self.lookup_service.get_koddi_campaign_id_by_short_id_batch(short_ids)
        assert result == ["koddi_id_1", "koddi_id_2"]
        self.__mock_redis_cache.mget.assert_called_once_with(
            RedisKeyTypes.CAMPAIGN,
            ["KODDI:short_id_1", "KODDI:short_id_2"]
        )

    @pytest.mark.asyncio
    async def test_get_campaign_long_id_by_koddi_id_batch(self):
        koddi_ids = [1234, 2345]
        long_ids = ["1234", "2345"]
        self.__mock_redis_cache.mget.return_value = long_ids

        result = await self.lookup_service.get_campaign_long_id_by_koddi_id_batch(koddi_ids)

        self.assertEqual(long_ids, result)
        self.__mock_redis_cache.mget.assert_called_once_with(
            RedisKeyTypes.CAMPAIGN_KODDI,
            koddi_ids
        )

    @pytest.mark.asyncio
    async def test_get_contact_short_id_by_long_id(self):
        long_contact_id = "long_id"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_contact_short_id_by_long_id(long_contact_id)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.CONTACT, long_contact_id)

    @pytest.mark.asyncio
    async def test_get_contact_short_id_by_long_id_batch(self):
        long_contact_ids = ["contact_1", "contact_2"]
        expected_short_ids = [101, None]
        self.__mock_redis_cache.mget.return_value = expected_short_ids

        result = await self.lookup_service.get_contact_short_id_by_long_id_batch(long_contact_ids)

        assert result == expected_short_ids
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.CONTACT, long_contact_ids)

    @pytest.mark.asyncio
    async def test_get_contact_details_by_short_id(self):
        short_contact_id = 1
        self.__mock_redis_cache.get.return_value = json.dumps({"id": "test", "contactType": "CPG"})

        result = await self.lookup_service.get_contact_details_by_short_id(short_contact_id)
        assert result == CachedContact(**{"id": "test", "contactType": "CPG"})
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.CONTACT, short_contact_id)

    @pytest.mark.asyncio
    async def test_get_contact_details_by_short_id_batch(self):
        short_ids = [1, 2, 3]
        expected_details = [CachedContact(**{"id": "1"}), CachedContact(**{"id": "2"}), CachedContact(**{"id": "3"})]

        self.__mock_redis_cache.mget.return_value = ['{"id": "1"}', '{"id": "2"}', '{"id": "3"}']

        result = await self.lookup_service.get_contact_details_by_short_id_batch(short_ids)

        assert result == expected_details
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.CONTACT, short_ids)

    @pytest.mark.asyncio
    async def test_get_address_short_id_by_long_id(self):
        long_address_id = "long_id"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_address_short_id_by_long_id(long_address_id)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.ADDRESS, long_address_id)

    @pytest.mark.asyncio
    async def test_get_address_short_id_by_long_id_batch(self):
        long_address_ids = ["address_1", "address_2", "address_3"]
        expected_short_ids = [201, None, 203]
        self.__mock_redis_cache.mget.return_value = expected_short_ids

        result = await self.lookup_service.get_address_short_id_by_long_id_batch(long_address_ids)

        assert result == expected_short_ids
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.ADDRESS, long_address_ids)

    @pytest.mark.asyncio
    async def test_get_address_details_by_short_id(self):
        short_address_id = 3
        self.__mock_redis_cache.get.return_value = json.dumps({"id": "address_details"})

        result = await self.lookup_service.get_address_details_by_short_id(short_address_id)
        assert result == CachedAddress(**{"id": "address_details"})
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.ADDRESS, short_address_id)

    @pytest.mark.asyncio
    async def test_get_address_long_id_by_account_long_id(self):
        long_account_id = "long_account_id"
        self.__mock_redis_cache.get.return_value = "long_id"

        result = await self.lookup_service.get_address_long_id_by_account_long_id(long_account_id)
        assert result == "long_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.ADDRESS, long_account_id)

    @pytest.mark.asyncio
    async def test_get_account_short_id_by_long_id(self):
        long_account_id = "long_id"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_account_short_id_by_long_id(long_account_id)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.ACCOUNT, long_account_id)

    @pytest.mark.asyncio
    async def test_get_account_long_id_by_short_id(self):
        short_account_id = 1
        self.__mock_redis_cache.get.return_value = "long_id"

        result = await self.lookup_service.get_account_long_id_by_short_id(short_account_id)
        assert result == "long_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.ACCOUNT, short_account_id)

    @pytest.mark.asyncio
    async def test_get_adgroup_short_id_by_long_id(self):
        long_adgroup_id = "long_id"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_adgroup_short_id_by_long_id(long_adgroup_id)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.AD_GROUP, long_adgroup_id)

    @pytest.mark.asyncio
    async def test_get_adgroup_long_id_by_short_id(self):
        short_adgroup_id = 1
        self.__mock_redis_cache.get.return_value = "long_id"

        result = await self.lookup_service.get_adgroup_long_id_by_short_id(short_adgroup_id)
        assert result == "long_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.AD_GROUP, short_adgroup_id)

    @pytest.mark.asyncio
    async def test_get_adgroup_short_id_by_long_id_batch(self):
        long_ids = ["1234", "2345"]
        short_ids = [12, 23]
        self.__mock_redis_cache.mget.return_value = ["12", "23"]

        result = await self.lookup_service.get_adgroup_short_id_by_long_id_batch(long_ids)

        self.assertEqual(short_ids, result)
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.AD_GROUP, long_ids)

    @pytest.mark.asyncio
    async def test_get_adgroup_long_id_by_koddi_id_batch(self):
        koddi_ids = [1234, 2345]
        long_ids = ["1234", "2345"]
        self.__mock_redis_cache.mget.return_value = long_ids

        result = await self.lookup_service.get_adgroup_long_id_by_koddi_id_batch(koddi_ids)

        self.assertEqual(long_ids, result)
        self.__mock_redis_cache.mget.assert_called_once_with(
            RedisKeyTypes.AD_GROUP_KODDI,
            koddi_ids
        )


    @pytest.mark.asyncio
    async def test_get_product_short_id_by_upc(self):
        upc = "upc"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_product_short_id_by_upc(upc)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.PRODUCT, upc)

    @pytest.mark.asyncio
    async def test_get_product_details_by_short_id(self):
        short_product_id = 1
        self.__mock_redis_cache.get.return_value = json.dumps({"upc": "test"})

        result = await self.lookup_service.get_product_details_by_short_id(short_product_id)
        assert result == CachedProduct(**{"upc": "test"})
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.PRODUCT, short_product_id)

    @pytest.mark.asyncio
    async def test_get_product_details_by_short_id_batch(self):
        short_product_ids = [1, 2]
        self.__mock_redis_cache.mget.return_value = [json.dumps({"upc": "test"}), None]

        result = await self.lookup_service.get_product_details_by_short_id_batch(short_product_ids)
        assert result == [CachedProduct(**{"upc": "test"}), None]
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.PRODUCT, short_product_ids)

    @pytest.mark.asyncio
    async def test_get_product_short_id_by_upc_batch(self):
        upcs = ["upc_1", "upc_2"]
        self.__mock_redis_cache.mget.return_value = [1, None]

        result = await self.lookup_service.get_product_short_id_by_upc_batch(upcs)
        assert result == [1, None]
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.PRODUCT, upcs)

    @pytest.mark.asyncio
    async def test_get_product_upcs_by_short_id_batch(self):
        short_product_ids = [1, 2, 3]
        mock_products = [json.dumps({"upc": "4011"}), "null", "invalid json"]
        self.__mock_redis_cache.mget.return_value = mock_products

        result = await self.lookup_service.get_product_upcs_by_short_id_batch(short_product_ids)

        self.assertEqual(["4011", None, None], result)
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.PRODUCT, short_product_ids)

    @pytest.mark.asyncio
    async def test_get_advertiser_short_id_by_long_id(self):
        long_advertiser_id = "long_id"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_advertiser_short_id_by_long_id(long_advertiser_id)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.ADVERTISER, long_advertiser_id)

    @pytest.mark.asyncio
    async def test_get_advertiser_details_by_short_id(self):
        short_advertiser_id = 1
        mock_advertiser = CachedRedisAdvertiser(brandId="test brand id")
        self.__mock_redis_cache.get.return_value = mock_advertiser.model_dump_json()

        result = await self.lookup_service.get_advertiser_details_by_short_id(short_advertiser_id)

        self.assertEqual(mock_advertiser, result)
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.ADVERTISER, short_advertiser_id)

    @pytest.mark.asyncio
    async def test_get_koddi_advertiser_short_id_by_long_id(self):
        long_advertiser_id = "long_id"
        self.__mock_redis_cache.get.return_value = "short_id"

        result = await self.lookup_service.get_koddi_advertiser_short_id_by_long_id(long_advertiser_id)
        assert result == "short_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.KODDI_ADVERTISER, long_advertiser_id)

    @pytest.mark.asyncio
    async def test_get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id(self):
        long_advertiser_id = "long_advertiser_id"
        long_agency_id = "long_agency_id"
        self.__mock_redis_cache.get.return_value = "short_id"

        result = await self.lookup_service.get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id(long_advertiser_id, long_agency_id)
        assert result == "short_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.KODDI_ADVERTISER, f"{long_advertiser_id}:{long_agency_id}")

    @pytest.mark.asyncio
    async def test_get_division_short_id_by_banner_code_and_division_number(self):
        banner_code = "banner_code"
        division_number = "1"
        self.__mock_redis_cache.get.return_value = "short_id"

        result = await self.lookup_service.get_division_short_id_by_banner_code_and_division_number(banner_code, division_number)
        assert result == "short_id"
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.DIVISION, f"{banner_code}:{division_number}")

    @pytest.mark.asyncio
    async def test_get_division_details_by_short_id(self):
        short_division_id = "1"
        mock_division = CachedDivision(id="division_id")
        self.__mock_redis_cache.get.return_value = mock_division.model_dump_json()

        result = await self.lookup_service.get_division_details_by_short_id(short_division_id)
        self.assertEqual(mock_division, result)
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.DIVISION, short_division_id)

    @pytest.mark.asyncio
    async def test_get_division_details_by_short_id_batch(self):
        short_division_ids = [1]
        mock_division = CachedDivision(id="division_id")
        self.__mock_redis_cache.mget.return_value = [mock_division.model_dump_json()]

        result = await self.lookup_service.get_division_details_by_short_id_batch(short_division_ids)
        self.assertEqual([mock_division], result)
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.DIVISION, short_division_ids)

    @pytest.mark.asyncio
    async def test_get_division_short_ids_by_division_items(self):
        division_items = [
            DivisionBannerItem(bannerCode="Kroger", divisionNumber="1"),
            DivisionBannerItem(bannerCode="Ralphs", divisionNumber="2"),
            DivisionBannerItem(bannerCode="Fred Meyer", divisionNumber="3")
        ]
        division_keys = ["Kroger:1", "Ralphs:2", "Fred Meyer:3"]
        self.__mock_redis_cache.mget.return_value = ["91", None, "wut"]
        expected_result = [91, None, None]

        result = await self.lookup_service.get_division_short_ids_by_division_items(division_items)

        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.DIVISION, division_keys)
        self.assertEqual(expected_result, result)

    @pytest.mark.asyncio
    async def test_get_placement_details_by_short_id(self):
        short_placement_id = 1
        mock_placement = CachedPlacement(
            placementId="id",
            name="name",
            channelShortName="shortName",
            minimumBidAmount=0.5
        )
        self.__mock_redis_cache.get.return_value = mock_placement.model_dump_json()

        result = await self.lookup_service.get_placement_details_by_short_id(short_placement_id)

        self.assertEqual(mock_placement, result)
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.PLACEMENT, short_placement_id)

    @pytest.mark.asyncio
    async def test_get_placement_short_id_by_id_and_name(self):
        placement_id = "id"
        placement_name = "name"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_placement_short_id_by_id_and_name(placement_id, placement_name)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.PLACEMENT, f"{placement_id}:{placement_name}")

    @pytest.mark.asyncio
    async def test_get_placement_short_id_by_name(self):
        placement_name = "name"
        self.__mock_redis_cache.get.return_value = 1

        result = await self.lookup_service.get_placement_short_id_by_name(placement_name)
        assert result == 1
        self.__mock_redis_cache.get.assert_called_once_with(RedisKeyTypes.PLACEMENT, placement_name)

    @pytest.mark.asyncio
    async def test_get_placement_short_ids_by_names(self):
        placement_names = [
            "Search & Browse",
            "Basket Builder",
            "Savings"
        ]
        self.__mock_redis_cache.mget.return_value = ["1", None, "wut"]
        expected_result = [1, None, None]

        result = await self.lookup_service.get_placement_short_ids_by_names(placement_names)

        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.PLACEMENT, placement_names)
        self.assertEqual(expected_result, result)

    @pytest.mark.asyncio
    async def test_set_campaign_short_id_by_long_id_batch(self):
        short_id_by_long_id = {
            "1234": 1234,
            "2345": 2345,
        }

        await self.lookup_service.set_campaign_short_id_by_long_id_batch(short_id_by_long_id)

        self.__mock_redis_cache.mset.assert_called_once_with({
            "CAMPAIGN:1234": 1234,
            "CAMPAIGN:2345": 2345,
        })

    @pytest.mark.asyncio
    async def test_set_campaign_long_id_by_short_id_batch(self):
        keys_with_values = {"CAMPAIGN:1": "long_id_1", "CAMPAIGN:2": "long_id_2"}
        self.__mock_redis_cache.cache_internal_id_batch.return_value = None

        await self.lookup_service.set_campaign_long_id_by_short_id_batch(keys_with_values)

        self.__mock_redis_cache.cache_internal_id_batch.assert_called_once_with(keys_with_values)

    @pytest.mark.asyncio
    async def test_set_campaign_long_id_by_koddi_id(self):
        koddi_id = "koddi_id"
        long_id = "long_id"
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_campaign_long_id_by_koddi_id(koddi_id, long_id)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.CAMPAIGN, "KODDI:koddi_id", long_id)

    @pytest.mark.asyncio
    async def test_set_campaign_long_id_by_koddi_id_batch(self):
        # Arrange
        long_id_by_koddi_id = {2345: "long_id_1", 3452: "long_id_2"}

        # Act
        await self.lookup_service.set_campaign_long_id_by_koddi_id_batch(long_id_by_koddi_id)

        # Assert
        self.__mock_redis_cache.mset.assert_called_once_with(
            {"CAMPAIGN:KODDI:2345": "long_id_1", "CAMPAIGN:KODDI:3452": "long_id_2"}
        )

    @pytest.mark.asyncio
    async def test_set_campaign_long_id_by_short_adgroup_id(self):
        short_adgroup_id = 1234
        long_campaign_id = "long_campaign_id"
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_campaign_long_id_by_short_adgroup_id(short_adgroup_id, long_campaign_id)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.AD_GROUP, f"{RedisKeyTypes.CAMPAIGN}:{short_adgroup_id}", long_campaign_id)

    @pytest.mark.asyncio
    async def test_set_address_short_id_by_long_id(self):
        long_address_id = "long_id"
        self.__mock_redis_cache.assign_numeric_id.return_value = 1

        result = await self.lookup_service.set_address_short_id_by_long_id(long_address_id)
        assert result == 1
        self.__mock_redis_cache.assign_numeric_id.assert_called_once_with(RedisKeyTypes.ADDRESS, long_address_id)

    @pytest.mark.asyncio
    async def test_set_address_details_by_short_id(self):
        short_address_id = 1
        address_details = CachedAddress(**{"id": "address_details"})
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_address_details_by_short_id(short_address_id, address_details)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.ADDRESS, short_address_id, address_details.model_dump_json())

    @pytest.mark.asyncio
    async def test_set_address_details_by_short_id_batch(self):
        address_details_by_short_id = {
            1: CachedAddress(**{"id": "123 Main St"}),
            2: CachedAddress(**{"id": "456 Elm St"}),
        }
        expected_keys = {
            f"{RedisKeyTypes.ADDRESS}:1": '{"id":"123 Main St","addressType":null}',
            f"{RedisKeyTypes.ADDRESS}:2": '{"id":"456 Elm St","addressType":null}',
        }

        await self.lookup_service.set_address_details_by_short_id_batch(address_details_by_short_id)

        self.__mock_redis_cache.mset.assert_called_once_with(expected_keys)

    @pytest.mark.asyncio
    async def test_set_address_long_id_by_account_long_id(self):
        long_account_id = "long_account_id"
        long_address_id = "long_address_id"
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_address_long_id_by_account_long_id(long_address_id, long_account_id)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.ADDRESS, long_account_id, long_address_id)

    @pytest.mark.asyncio
    async def test_set_account_short_id_by_long_id(self):
        long_account_id = "long_id"
        self.__mock_redis_cache.assign_numeric_id.return_value = 1

        result = await self.lookup_service.set_account_short_id_by_long_id(long_account_id)
        assert result == 1
        self.__mock_redis_cache.assign_numeric_id.assert_called_once_with(RedisKeyTypes.ACCOUNT, long_account_id)

    @pytest.mark.asyncio
    async def test_set_account_long_id_by_short_id(self):
        short_account_id = 1
        long_account_id = "long_id"
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_account_long_id_by_short_id(short_account_id, long_account_id)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.ACCOUNT, short_account_id, long_account_id)

    @pytest.mark.asyncio
    async def test_set_adgroup_short_id_by_long_id_batch(self):
        short_id_by_long_id = {
            "1234": 1234,
            "2345": 2345,
        }

        await self.lookup_service.set_adgroup_short_id_by_long_id_batch(short_id_by_long_id)

        self.__mock_redis_cache.mset.assert_called_once_with({
            "AD_GROUP:1234": 1234,
            "AD_GROUP:2345": 2345,
        })

    @pytest.mark.asyncio
    async def test_set_adgroup_long_id_by_koddi_id(self):
        koddi_id = "koddi_id"
        long_id = "long_id"
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_adgroup_long_id_by_koddi_id(koddi_id, long_id)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.AD_GROUP, f"KODDI:{koddi_id}", long_id)

    @pytest.mark.asyncio
    async def test_set_adgroup_long_id_by_koddi_id_batch(self):
        long_id_by_koddi_id = {
            4321: "1234",
            5432: "2345"
        }
        await self.lookup_service.set_adgroup_long_id_by_koddi_id_batch(long_id_by_koddi_id)
        self.__mock_redis_cache.mset.assert_called_once_with({
            "AD_GROUP:KODDI:4321": "1234",
            "AD_GROUP:KODDI:5432": "2345",
        })

    @pytest.mark.asyncio
    async def test_set_product_short_id_by_upc(self):
        upc = "upc"
        self.__mock_redis_cache.assign_numeric_id.return_value = 1

        result = await self.lookup_service.set_product_short_id_by_upc(upc)
        assert result == 1
        self.__mock_redis_cache.assign_numeric_id.assert_called_once_with(RedisKeyTypes.PRODUCT, upc)

    @pytest.mark.asyncio
    async def test_set_product_short_ids_by_upcs(self):
        upcs = ["upc1", "upc2"]
        expected_short_ids = [1, 2]
        self.__mock_redis_cache.assign_numeric_id_batch.return_value = expected_short_ids

        result = await self.lookup_service.set_product_short_ids_by_upcs(upcs)

        self.assertEqual(expected_short_ids, result)
        self.__mock_redis_cache.assign_numeric_id_batch.assert_called_once_with(RedisKeyTypes.PRODUCT, upcs)

    @pytest.mark.asyncio
    async def test_set_product_details_by_short_id(self):
        short_product_id = 1
        product_details = CachedProduct(**{"upc": "test"})
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_product_details_by_short_id(short_product_id, product_details)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.PRODUCT, short_product_id, product_details.model_dump_json())

    @pytest.mark.asyncio
    async def test_set_product_details_by_short_id_batch(self):
        product_details_by_short_id = {
            1234: CachedProduct(**{"upc": "test1"}),
            2345: CachedProduct(**{"upc": "test2"})
        }

        await self.lookup_service.set_product_details_by_short_id_batch(product_details_by_short_id)

        self.__mock_redis_cache.mset.assert_called_once_with({
            "PRODUCT:1234": CachedProduct(**{"upc": "test1"}).model_dump_json(),
            "PRODUCT:2345": CachedProduct(**{"upc": "test2"}).model_dump_json(),
        })

    @pytest.mark.asyncio
    async def test_set_advertiser_short_id_by_long_id(self):
        long_advertiser_id = "long_id"
        self.__mock_redis_cache.assign_numeric_id.return_value = 1

        result = await self.lookup_service.set_advertiser_short_id_by_long_id(long_advertiser_id)
        assert result == 1
        self.__mock_redis_cache.assign_numeric_id.assert_called_once_with(RedisKeyTypes.ADVERTISER, long_advertiser_id)

    @pytest.mark.asyncio
    async def test_set_advertiser_details_by_short_id(self):
        short_advertiser_id = 1
        mock_advertiser = CachedRedisAdvertiser(brandId="test brand id")
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_advertiser_details_by_short_id(short_advertiser_id, mock_advertiser)

        self.__mock_redis_cache.set.assert_called_once_with(
            RedisKeyTypes.ADVERTISER,
            short_advertiser_id,
            mock_advertiser.model_dump_json()
        )

    @pytest.mark.asyncio
    async def test_set_koddi_advertiser_short_id_by_long_id(self):
        long_advertiser_id = "long_id"
        short_id = "short_id"
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_koddi_advertiser_short_id_by_long_id(long_advertiser_id, short_id)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.KODDI_ADVERTISER, long_advertiser_id, short_id)

    @pytest.mark.asyncio
    async def test_set_koddi_advertiser_short_id_by_long_id_and_agency_id(self):
        long_advertiser_id = "long_advertiser_id"
        long_agency_id = "long_agency_id"
        short_id = "short_id"
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_koddi_advertiser_short_id_by_long_id_and_agency_id(long_advertiser_id, long_agency_id, short_id)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.KODDI_ADVERTISER, f"{long_advertiser_id}:{long_agency_id}", short_id)

    @pytest.mark.asyncio
    async def test_set_contact_short_id_by_long_id(self):
        long_contact_id = "long_id"
        self.__mock_redis_cache.assign_numeric_id.return_value = 1

        result = await self.lookup_service.set_contact_short_id_by_long_id(long_contact_id)
        assert result == 1
        self.__mock_redis_cache.assign_numeric_id.assert_called_once_with(RedisKeyTypes.CONTACT, long_contact_id)

    @pytest.mark.asyncio
    async def test_set_contact_short_ids_by_long_ids(self):
        contact_long_ids = ["long1", "long2"]
        expected_short_ids = [101, 102]
        self.__mock_redis_cache.assign_numeric_id_batch.return_value = expected_short_ids

        result = await self.lookup_service.set_contact_short_id_by_long_id_batch(contact_long_ids)

        self.assertEqual(expected_short_ids, result)
        self.__mock_redis_cache.assign_numeric_id_batch.assert_called_once_with(
            RedisKeyTypes.CONTACT, contact_long_ids
        )

    @pytest.mark.asyncio
    async def test_set_contact_details_by_short_contact_id(self):
        short_contact_id = 1
        contact_details = json.dumps({"details": "contact_details"})
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_contact_details_by_short_contact_id(short_contact_id, contact_details)

        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.CONTACT, short_contact_id, contact_details)

    @pytest.mark.asyncio
    async def test_set_contact_details_by_short_id_batch(self):
        contact_details_by_short_id = {
            1: CachedContact(**{"id": "alice@example.com"}),
            2: CachedContact(**{"id": "bob@example.com"}),
        }
        expected_keys = {
            f"{RedisKeyTypes.CONTACT}:1": '{"id":"alice@example.com","contactType":null,"accountIds":null}',
            f"{RedisKeyTypes.CONTACT}:2": '{"id":"bob@example.com","contactType":null,"accountIds":null}',
        }

        result = await self.lookup_service.set_contact_details_by_short_id_batch(contact_details_by_short_id)

        self.__mock_redis_cache.mset.assert_called_once_with(expected_keys)

    @pytest.mark.asyncio
    async def test_set_division_short_id_by_banner_code_and_division_number(self):
        banner_code = "banner_code"
        division_number = "1"
        self.__mock_redis_cache.assign_numeric_id.return_value = 1

        result = await self.lookup_service.set_division_short_id_by_banner_code_and_division_number(banner_code, division_number)
        assert result == 1
        self.__mock_redis_cache.assign_numeric_id.assert_called_once_with(RedisKeyTypes.DIVISION, f"{banner_code}:{division_number}")

    @pytest.mark.asyncio
    async def test_set_division_details_by_short_id(self):
        short_division_id = "1"
        mock_division = CachedDivision(id="division_id")
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_division_details_by_short_id(short_division_id, mock_division)

        self.__mock_redis_cache.set.assert_called_once_with(
            RedisKeyTypes.DIVISION,
            short_division_id,
            mock_division.model_dump_json()
        )

    @pytest.mark.asyncio
    async def test_set_division_short_id_by_banner_code_and_division_number_batch(self):
        short_division_id = ["testBanner:testNumber"]
        self.__mock_redis_cache.assign_numeric_id_batch.return_value = [123]

        result = await self.lookup_service.set_division_short_id_by_banner_code_and_division_number_batch(short_division_id)

        assert result == [123]
        assert self.__mock_redis_cache.assign_numeric_id_batch.call_count == 1

    @pytest.mark.asyncio
    async def test_set_division_data_by_short_id_batch(self):
        short_division_id = {
            "testBanner:testNumber": DivisionServiceResponse()
        }
        self.__mock_redis_cache.assign_numeric_id_batch.return_value = [123]

        await self.lookup_service.set_division_data_by_short_id_batch(
            short_division_id
        )

        assert self.__mock_redis_cache.mset.call_count == 1

    @pytest.mark.asyncio
    async def test_set_placement_short_id_by_id_and_name(self):
        placement_id = "id"
        placement_name = "name"
        self.__mock_redis_cache.assign_numeric_id.return_value = 1

        result = await self.lookup_service.set_placement_short_id_by_id_and_name(placement_id, placement_name)
        assert result == 1
        self.__mock_redis_cache.assign_numeric_id.assert_called_once_with(RedisKeyTypes.PLACEMENT, f"{placement_id}:{placement_name}")

    @pytest.mark.asyncio
    async def test_set_placement_details_by_short_id(self):
        short_placement_id = 1
        placement_details = CachedPlacement(
            placementId="id",
            name="name",
            channelShortName="shortName",
            minimumBidAmount=0.5
        )
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_placement_details_by_short_id(short_placement_id, placement_details)

        self.__mock_redis_cache.set.assert_called_once_with(
            RedisKeyTypes.PLACEMENT,
            short_placement_id,
            placement_details.model_dump_json()
        )

    @pytest.mark.asyncio
    async def test_set_placement_short_id_by_name(self):
        placement_name = "name"
        placement_short_id = 1
        self.__mock_redis_cache.set.return_value = None

        await self.lookup_service.set_placement_short_id_by_name(placement_name, placement_short_id)
        self.__mock_redis_cache.set.assert_called_once_with(RedisKeyTypes.PLACEMENT, placement_name, placement_short_id)

    @pytest.mark.asyncio
    async def test_set_koddi_campaign_id_by_short_id_batch(self):
        dict_koddi_campaign_ids = {"1234": "koddi_id_1", "45678":"koddi_id_2"}
        self.__mock_redis_cache.mset.return_value = None
        await  self.lookup_service.set_koddi_campaign_id_by_short_id_batch(dict_koddi_campaign_ids)
        self.__mock_redis_cache.mset.assert_called_once_with({
            "CAMPAIGN:KODDI:1234": "koddi_id_1",
            "CAMPAIGN:KODDI:45678": "koddi_id_2"
        })

    @pytest.mark.asyncio
    async def test_get_campaign_key_exists(self):
        key = 'campaign_key'
        self.__mock_redis_cache.exists.return_value = 1
        result = await self.lookup_service.get_campaign_key_exists(key)
        assert result is 1

    @pytest.mark.asyncio
    async def test_get_account_short_id_by_long_id_batch(self):
        long_account_ids = ["long_id_1", "long_id_2"]
        expected_short_ids = [101, 102]
        self.__mock_redis_cache.mget.return_value = expected_short_ids

        result = await self.lookup_service.get_account_short_id_by_long_id_batch(long_account_ids)

        assert result == expected_short_ids
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.ACCOUNT, long_account_ids)

    @pytest.mark.asyncio
    async def test_get_advertiser_short_id_by_long_id_batch(self):
        long_advertiser_ids = ["long_id_1", "long_id_2"]
        expected_short_ids = [201, 202]
        self.__mock_redis_cache.mget.return_value = expected_short_ids

        result = await self.lookup_service.get_advertiser_short_id_by_long_id_batch(long_advertiser_ids)

        assert result == expected_short_ids
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.ADVERTISER, long_advertiser_ids)

    @pytest.mark.asyncio
    async def test_get_advertiser_details_by_short_ids(self):
        short_advertiser_ids = [1, 2]
        mock_advertiser_1 = CachedRedisAdvertiser(brandId="brand1")
        mock_advertiser_2 = CachedRedisAdvertiser(brandId="brand2")
        self.__mock_redis_cache.mget.return_value = [
            mock_advertiser_1.model_dump_json(),
            mock_advertiser_2.model_dump_json()
        ]

        result = await self.lookup_service.get_advertiser_details_by_short_ids(short_advertiser_ids)

        expected_details = [mock_advertiser_1, mock_advertiser_2]
        assert result == expected_details
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.ADVERTISER, short_advertiser_ids)

    @pytest.mark.asyncio
    async def test_set_account_short_ids_by_long_ids(self):
        long_account_ids = ["long_id_1", "long_id_2"]
        expected_short_ids = [101, 102]
        self.__mock_redis_cache.assign_numeric_id_batch.return_value = expected_short_ids

        result = await self.lookup_service.set_account_short_ids_by_long_ids(long_account_ids)

        assert result == expected_short_ids
        self.__mock_redis_cache.assign_numeric_id_batch.assert_called_once_with(RedisKeyTypes.ACCOUNT, long_account_ids)

    @pytest.mark.asyncio
    async def test_set_account_long_id_by_short_id_batch(self):
        short_id_by_long_id = {
            "long_id_1": 101,
            "long_id_2": 102
        }

        await self.lookup_service.set_account_long_id_by_short_id_batch(short_id_by_long_id)

        self.__mock_redis_cache.mset.assert_called_once_with({
            "ACCOUNT:101": "long_id_1",
            "ACCOUNT:102": "long_id_2",
        })

    @pytest.mark.asyncio
    async def test_set_advertiser_details_by_short_id_batch(self):
        advertiser_details_by_short_id = {
            1: CachedRedisAdvertiser(brandId="brand1"),
            2: CachedRedisAdvertiser(brandId="brand2")
        }
        expected_keys = {
            'ADVERTISER:1': '{"brandId":"brand1","displayName":null,"salesforceId":null,"client":null}',
            'ADVERTISER:2': '{"brandId":"brand2","displayName":null,"salesforceId":null,"client":null}'
        }

        await self.lookup_service.set_advertiser_details_by_short_id_batch(advertiser_details_by_short_id)

        self.__mock_redis_cache.mset.assert_called_once_with(expected_keys)

    @pytest.mark.asyncio
    async def test_set_koddi_advertiser_short_id_batch(self):
        long_advertiser_ids = {
            "key": "koddi1",
            "key2": "koddi2"
        }

        await self.lookup_service.set_koddi_advertiser_short_id_batch(long_advertiser_ids)

        expected_data = {'KODDI_ADVERTISER:key': 'koddi1', 'KODDI_ADVERTISER:key2': 'koddi2'}
        self.__mock_redis_cache.mset.assert_called_once_with(expected_data)

    @pytest.mark.asyncio
    async def test_set_account_short_id_by_long_id_batch(self):
        long_account_ids = {
            "long_id_1":101,
            "long_id_2": 102
        }

        await self.lookup_service.set_account_short_id_by_long_id_batch(long_account_ids)

        self.__mock_redis_cache.mset.assert_called_once_with({'ACCOUNT:long_id_1': 101, 'ACCOUNT:long_id_2': 102})

    @pytest.mark.asyncio
    async def test_get_adgroup_long_id_by_short_id_batch(self):
        long_ids = ["737463728232", "343937443734"]
        short_ids = ["4637", "3763"]
        self.__mock_redis_cache.mget.return_value = ["737463728232", "343937443734"]

        result = await self.lookup_service.get_adgroup_long_id_by_short_id_batch(short_ids)

        self.assertEqual(long_ids, result)
        self.__mock_redis_cache.mget.assert_called_once_with(RedisKeyTypes.AD_GROUP, short_ids)

    @pytest.mark.asyncio
    async def test_set_adgroup_long_id_by_short_id_batch(self):
        long_id_by_short_id = {
            3800: "76329375987",
            3801: "74638283839",
        }

        await self.lookup_service.set_adgroup_long_id_by_short_id_batch(long_id_by_short_id)

        self.__mock_redis_cache.mset.assert_called_once_with({
            "AD_GROUP:3800": "76329375987",
            "AD_GROUP:3801": "74638283839",
        })
