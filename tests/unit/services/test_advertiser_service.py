from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import Response

from app.common.context.context import request_context, user_context
from app.common.model.account import InternalAccount
from app.common.model.advertiser import Advertiser, CachedAdvertiser, KoddiAdvertiser
from app.common.model.downstream.advertiser_service import (
    KoddiAdvertiserMultiBrandRequest,
    KoddiAdvertiserMultiBrand,
    KoddiAdvertiserResponse,
    KoddiBrandResponse,
)
from app.common.model.downstream.ent_client_service import EntClientServiceMeta
from app.common.model.redis import CachedRedisAdvertiser
from app.common.model.shared import ListDataResponse
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.config_service import Config
from tests.utils_for_testing.auto_mock import auto_mock


def update_advertisers_table(table: dict):
    table["brand1"] = (1, CachedRedisAdvertiser(brandId='brand1', displayName='Brand One', salesforceId='SF1', client=None))

class TestAdvertiserService(IsolatedAsyncioTestCase):
    __mock_config_service: MagicMock
    __mock_redis_cache: AsyncMock
    __mock_external_http_client_service: MagicMock

    __subject: AdvertiserService

    def setUp(self) -> None:
        self.__mock_config_service = MagicMock()
        self.__lookup_service = AsyncMock()
        self.__mock_external_http_client_service = MagicMock()
        self.mock_koddi_sso_gateway = AsyncMock()
        self.mock_ent_client_service_gateway = AsyncMock()

        FastAPICache.init(backend=InMemoryBackend(), prefix="test")

        self.__mock_config_service.get_current_config.return_value = Config(
            base_api_url="https://api-url.com.invalid",
            base_koddi_url="https://koddi-url.com.invalid",
            pte_target_id="pte_target_id",
            product_id="product_id")

        self.__subject = AdvertiserService(
            config_service=self.__mock_config_service,
            lookup_service=self.__lookup_service,
            external_api_http_client_service=self.__mock_external_http_client_service,
            koddi_sso_gateway=self.mock_koddi_sso_gateway,
            ent_client_service_gateway=self.mock_ent_client_service_gateway,
        )

    async def test_get_advertisers_for_user__returns_koddi_advertisers(self):
        response_data = [
            KoddiAdvertiser(**{"brandIds": ["1234"], "koddiId": 4321, "agencyId": "2345", "primaryBrandId": "1234"}),
            KoddiAdvertiser(**{"brandIds": ["5678"], "koddiId": 8765, "agencyId": "2345", "primaryBrandId": "5678"})
        ]
        self.mock_koddi_sso_gateway.get_advertisers_for_user.return_value = response_data

        response = await self.__subject.get_advertisers_for_user()
        self.assertEqual(2, len(response))
        self.assertEqual("1234", response[0].brandIds[0])
        self.assertEqual(4321, response[0].koddiId)
        self.assertEqual("2345", response[0].agencyId)
        self.assertEqual("1234", response[0].primaryBrandId)
        self.assertEqual("5678", response[1].brandIds[0])
        self.assertEqual(8765, response[1].koddiId)
        self.assertEqual("2345", response[1].agencyId)
        self.assertEqual("5678", response[1].primaryBrandId)

    @pytest.mark.asyncio
    async def test__cache_advertisers_by_long_id(self):
        # Act
        advertisers_to_lookup = ["brand1", "brand2", "brand3"]
        advertisers_table = {
            "brand1": (5, CachedRedisAdvertiser(
                brandId="brand1",
                displayName="Brand One",
                salesforceId="SF1",
                client=None
            )),
            "brand3": (None, CachedRedisAdvertiser(
                brandId="brand3",
                displayName="Brand Three",
                salesforceId="SF3",
                client=None
            ))
        }

        # Act
        await self.__subject._AdvertiserService__cache_advertisers_by_long_id(
           advertisers_table
        )

        # Assert
        self.__lookup_service.set_advertiser_short_id_by_long_id_batch.assert_called_once_with(
            ["brand3"],
        )

    @pytest.mark.asyncio
    async def test__cache_advertisers_details_by_short_id(self):
        # Act
        advertisers_to_lookup = ["brand1", "brand2", "brand3"]
        advertisers_table = {
            "brand1": (5, CachedRedisAdvertiser(
                brandId="brand1",
                displayName="Brand One",
                salesforceId="SF1",
                client=None
            )),
            "brand3": (3, CachedRedisAdvertiser(
                brandId="brand3",
                displayName="Brand Three",
                salesforceId="SF3",
                client=None
            ))
        }

        self.__lookup_service.get_advertiser_details_by_short_ids.return_value = [
            None, None
        ]

        # Act
        await self.__subject._AdvertiserService__cache_advertisers_details_by_short_id(
            advertisers_table
        )

        # Assert
        self.__lookup_service.get_advertiser_details_by_short_ids.assert_called_once_with(
            [5, 3]
        )
        self.__lookup_service.set_advertiser_details_by_short_id_batch.assert_called_once_with(
            {
                3: CachedRedisAdvertiser(brandId='brand3', displayName='Brand Three', salesforceId='SF3', client=None),
                5: CachedRedisAdvertiser(brandId='brand1', displayName='Brand One', salesforceId='SF1', client=None),
            }
        )

    @patch('app.common.services.advertiser_service.AdvertiserService._AdvertiserService__cache_advertisers_by_long_id', new_callable=AsyncMock, side_effect=update_advertisers_table)
    @patch('app.common.services.advertiser_service.AdvertiserService._AdvertiserService__cache_advertisers_details_by_short_id',
           new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_get_advertisers(
            self,
            mock_get_advertisers_details_by_short_id: AsyncMock,
            mock_cache_advertisers_by_long_id: AsyncMock,
    ):
        # Arrange
        internal_account = InternalAccount(
            id="abc123",
            name="Test Account"
        )
        account_id = 1
        self.mock_ent_client_service_gateway.get_brands.return_value = ListDataResponse(
            data=[
                CachedRedisAdvertiser(
                    brandId='brand1',
                    displayName="Brand One",
                    salesforceId="SF1",
                    client=None
                )
            ],
            meta=EntClientServiceMeta()
        )
        self.__lookup_service.get_advertiser_short_id_by_long_id_batch.return_value = [None]
        expected_result = [
            Advertiser(
                id=1,
                name="Brand One",
                accountId=account_id,
                description="Test Account - Brand One",
                active=True
            )
        ]

        # Act
        result = await self.__subject.get_advertisers(
            account=internal_account,
            account_id=account_id
        )

        # Assert
        self.assertEqual(expected_result, result)
        self.mock_ent_client_service_gateway.get_brands.assert_called_once_with(
            internal_account.id
        )
        self.__lookup_service.get_advertiser_short_id_by_long_id_batch.assert_called_once_with(
            ["brand1"]
        )
        mock_get_advertisers_details_by_short_id.assert_called_once()
        mock_cache_advertisers_by_long_id.assert_called_once()

    async def test__cache_koddi_ids_by_brands_or_agency(self):
        # Arrange
        upstream_response = [
            KoddiBrandResponse(**{
                "koddiId": 56,
                "agencyId": "agency1",
            }),
            KoddiBrandResponse(**{
                "koddiId": 78,
                "agencyId": None,
            })
        ]

        # Act
        await self.__subject._AdvertiserService__cache_koddi_ids_by_brands_or_agency(
            upstream_response,
            "brand1"
        )

        # Assert
        self.__lookup_service.set_koddi_advertiser_short_id_batch.assert_called_with(
            {'brand1:agency1': 56}
        )

    @patch(
        'app.common.services.advertiser_service.AdvertiserService._AdvertiserService__cache_koddi_ids_by_brands_or_agency',
        new_callable=AsyncMock
    )
    @pytest.mark.asyncio
    async def test_get_koddi_advertiser_id(
            self,
            mock_cache_koddi_ids_by_brands_or_agency: AsyncMock,
    ):
        # Arrange
        internal_advertiser_id = "brand1"
        expected_koddi_id = 56

        self.__lookup_service.get_koddi_advertiser_short_id_by_long_id.side_effect = [None, expected_koddi_id]
        self.mock_koddi_sso_gateway.get_advertisers.return_value = [
            KoddiBrandResponse(**{
                "koddiId": 56,
                "agencyId": "agency1",
            }),
            KoddiBrandResponse(**{
                "koddiId": 78,
                "agencyId": None,
            })
        ]

        # Act
        result = await self.__subject.get_koddi_advertiser_id(
            internal_advertiser_id
        )

        # Assert
        self.assertEqual(expected_koddi_id, result)
        self.__lookup_service.get_koddi_advertiser_short_id_by_long_id.assert_called_with(
            internal_advertiser_id
        )
        self.mock_koddi_sso_gateway.get_advertisers.assert_called_once_with(internal_advertiser_id)
        mock_cache_koddi_ids_by_brands_or_agency.assert_called_once_with(
        [KoddiBrandResponse(**{'koddiId': 56, 'agencyId': 'agency1'}),
                KoddiBrandResponse(**{'koddiId': 78, 'agencyId': None})],
            "brand1"
        )

    async def test_get_koddi_advertiser_id_for_agency_no_cached(self):
        # Arrange
        internal_advertiser_id = "brand1"
        internal_agency_id = "agency1"

        self.__lookup_service.get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id. \
            return_value = None

        self.mock_koddi_sso_gateway.get_advertiser_by_agency.return_value = KoddiBrandResponse(**{
                "koddiId": 123
        })

        # Act
        result = await self.__subject.get_koddi_advertiser_id_for_agency(
            internal_advertiser_id,
            internal_agency_id
        )

        # Assert
        self.assertEqual(123, result)
        self.__lookup_service.get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id. \
            assert_called_once_with('brand1', 'agency1')
        self.__lookup_service.set_koddi_advertiser_short_id_by_long_id_and_agency_id. \
            assert_called_once_with('brand1', 'agency1', 123)
        self.mock_koddi_sso_gateway.get_advertiser_by_agency.assert_called_once_with('brand1', 'agency1')

    async def test_get_koddi_advertiser_id_for_agency_cached(self):
        # Arrange
        internal_advertiser_id = "brand1"
        internal_agency_id = "agency1"

        self.__lookup_service.get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id. \
            return_value = 123


        # Act
        result = await self.__subject.get_koddi_advertiser_id_for_agency(
            internal_advertiser_id,
            internal_agency_id
        )

        # Assert
        self.assertEqual(123, result)
        self.__lookup_service.get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id. \
            assert_called_once_with('brand1', 'agency1')

    async def test_get_koddi_advertiser_id_for_agency__creates_upstream_koddi_advertiser(self):
        advertiser_id = "1234"
        agency_id = "4567"
        koddi_id = 9876
        (
            self.__lookup_service
            .get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id
            .return_value
        ) = None
        self.mock_koddi_sso_gateway.get_advertiser_by_agency.return_value = None
        self.mock_koddi_sso_gateway.create_advertiser_by_agency.return_value = (
            KoddiAdvertiserResponse(id=koddi_id)
        )

        created_koddi_id = await self.__subject.get_koddi_advertiser_id_for_agency(
            advertiser_id,
            agency_id
        )

        self.assertEqual(koddi_id, created_koddi_id)
        (
            self.__lookup_service
            .get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id
            .assert_called_once_with(advertiser_id, agency_id)
        )
        self.mock_koddi_sso_gateway.get_advertiser_by_agency.assert_called_once_with(
            advertiser_id,
            agency_id
        )
        self.mock_koddi_sso_gateway.create_advertiser_by_agency.assert_called_once_with(
            advertiser_id,
            agency_id
        )
        (
            self.__lookup_service
            .set_koddi_advertiser_short_id_by_long_id_and_agency_id
            .assert_called_once_with(
                advertiser_id,
                agency_id,
                koddi_id
            )
        )


    @patch('logging.Logger.warning')
    async def test_get_advertiser_by_numeric_id_no_cached(self, mock_logger_warning: MagicMock):
        # Arrange
        advertiser_id = 123
        self.__lookup_service.get_advertiser_details_by_short_id.return_value = None

        # Act
        with self.assertRaises(HTTPException) as context:
            await self.__subject.get_advertiser_by_numeric_id(advertiser_id)

        # Assert
        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Advertiser not found", context.exception.detail)
        self.__lookup_service.get_advertiser_details_by_short_id.assert_called_once_with(advertiser_id)
        mock_logger_warning.assert_called_once_with("Advertiser ID: %s not found in cache", advertiser_id)

    @patch('logging.Logger.debug')
    async def test_get_advertiser_by_numeric_id_cached(self, mock_logger_debug: MagicMock):
        # Arrange
        advertiser_id = 123
        self.__lookup_service.get_advertiser_details_by_short_id.return_value = CachedRedisAdvertiser(
            brandId="brand123",
            displayName="Brand Name",
            salesforceId="SF123",
            client=None
        )

        expected = CachedAdvertiser(
            id=advertiser_id,
            brandId="brand123",
            name="Brand Name",
            accountId=0,
            description=" - Brand Name",
            active=True
        )

        # Act
        result = await self.__subject.get_advertiser_by_numeric_id(advertiser_id)

        # Assert
        self.assertEqual(expected, result)
        self.__lookup_service.get_advertiser_details_by_short_id.assert_called_once_with(advertiser_id)
        mock_logger_debug.assert_called_once_with(
            "Found advertiser %s",
            '{"brandId":"brand123","displayName":"Brand '
            'Name","salesforceId":"SF123","client":null}'
        )

    @patch('logging.Logger.warning')
    async def test_get_advertisers_by_numeric_ids_no_cached(self, mock_logger_warning: MagicMock):
        # Arrange
        advertiser_ids = [123, 456]
        self.__lookup_service.get_advertiser_details_by_short_ids.return_value = [
            MagicMock(),
            None
        ]

        # Act
        with self.assertRaises(HTTPException) as context:
            await self.__subject.get_advertisers_by_numeric_ids(advertiser_ids)

        # Assert
        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Advertisers not found", context.exception.detail)
        self.__lookup_service.get_advertiser_details_by_short_ids.assert_called_once_with(advertiser_ids)
        mock_logger_warning.assert_called_once_with(
            "Advertiser IDs: %s not found in cache", [456]
        )

    async def test_get_advertisers_by_numeric_ids_cached(self):
        # Arrange
        advertiser_ids = [123]
        self.__lookup_service.get_advertiser_details_by_short_ids.return_value = [
            CachedRedisAdvertiser(
                brandId="brand123",
                displayName="Brand One",
                salesforceId="SF123",
                client=None
            )
        ]
        expected = [
            CachedAdvertiser(
                id=123,
                brandId="brand123",
                name="Brand One",
                accountId=0,
                description=" - Brand One",
                active=True
            )
        ]

        # Act
        result = await self.__subject.get_advertisers_by_numeric_ids(advertiser_ids)

        # Assert
        self.assertEqual(expected, result)
        self.__lookup_service.get_advertiser_details_by_short_ids.assert_called_once_with(advertiser_ids)

    async def test_get_or_create_cached_advertiser_id_no_cached(self):
        # Arrange
        internal_advertiser_id = "brand1"
        self.__lookup_service.get_advertiser_short_id_by_long_id.return_value = None
        self.__lookup_service.set_advertiser_short_id_by_long_id.return_value = 123

        # Act
        result = await self.__subject.get_or_create_cached_advertiser_id(internal_advertiser_id)

        # Assert
        self.assertEqual(123, result)
        self.__lookup_service.get_advertiser_short_id_by_long_id.assert_called_once_with(internal_advertiser_id)
        self.__lookup_service.set_advertiser_short_id_by_long_id.assert_called_once_with(internal_advertiser_id)

    async def test_get_or_create_cached_advertiser_id_cached(self):
        # Arrange
        internal_advertiser_id = "brand1"
        self.__lookup_service.get_advertiser_short_id_by_long_id.return_value = 123

        # Act
        result = await self.__subject.get_or_create_cached_advertiser_id(internal_advertiser_id)

        # Assert
        self.assertEqual(123, result)
        self.__lookup_service.get_advertiser_short_id_by_long_id.assert_called_once_with(internal_advertiser_id)

    async def test_get_or_create_cached_advertiser_ids(self):
        # Arrange
        internal_advertiser_ids = ["brand1", "brand2"]
        self.__lookup_service.get_advertiser_short_id_by_long_id_batch.return_value = [None, None]
        self.__lookup_service.set_advertiser_short_id_by_long_id_batch.return_value = [123, 456]

        # Act
        result = await self.__subject.get_or_create_cached_advertiser_ids(internal_advertiser_ids)

        # Assert
        self.assertEqual([123, 456], result)
        self.__lookup_service.get_advertiser_short_id_by_long_id_batch.assert_called_once_with(internal_advertiser_ids)
        self.__lookup_service.set_advertiser_short_id_by_long_id_batch.assert_called_once_with(internal_advertiser_ids)

    async def test_get_koddi_advertiser_single_brand_with_agency(self):
        # Arrange
        internal_advertisers_ids = ["brandMain"]
        internal_agency_id = "agency1"
        koddi_advertiser_id = 1234
        lookup_fn = (
            self
            .__lookup_service
            .get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id
        )
        lookup_fn.return_value = koddi_advertiser_id

        # Act
        result = await self.__subject.get_koddi_advertiser_multi_brand(
            internal_advertisers_ids,
            internal_agency_id
        )

        # Assert
        self.assertEqual(koddi_advertiser_id, result)
        lookup_fn.assert_called_once_with(internal_advertisers_ids[0], internal_agency_id)

    async def test_get_koddi_advertiser_multi_brand_whit_agency(self):
        # Arrange
        internal_advertisers_ids = ["brand1", "brand2"]
        internal_agency_id = "agency1"
        self.mock_koddi_sso_gateway.get_multi_brand_advertiser.return_value = None
        self.mock_koddi_sso_gateway.create_multi_brand_advertiser.return_value = KoddiAdvertiserResponse(id=1293)

        # Act
        result = await self.__subject.get_koddi_advertiser_multi_brand(
                internal_advertisers_ids,
                internal_agency_id
        )

        # Assert
        self.assertEqual(1293, result)
        self.mock_koddi_sso_gateway.create_multi_brand_advertiser.assert_called_once_with(KoddiAdvertiserMultiBrandRequest(
            brandItemRequests=[
                KoddiAdvertiserMultiBrand(brandId="brand1",primary=True,percentage=1.0),
                KoddiAdvertiserMultiBrand(brandId="brand2",primary=False,percentage=0.0)
            ],
            agencyId="agency1"
        ))

    async def test_get_koddi_advertiser_multi_brand_whitout_agency(self):
        # Arrange
        internal_advertisers_ids = ["brand11", "brand22", "brand33"]
        internal_agency_id = None
        self.mock_koddi_sso_gateway.get_multi_brand_advertiser.return_value = None
        self.mock_koddi_sso_gateway.create_multi_brand_advertiser.return_value = KoddiAdvertiserResponse(id=1287)

        # Act
        result = await self.__subject.get_koddi_advertiser_multi_brand(
            internal_advertisers_ids,
            internal_agency_id
        )

        # Assert
        self.assertEqual(1287, result)
        self.mock_koddi_sso_gateway.create_multi_brand_advertiser.assert_called_once_with(KoddiAdvertiserMultiBrandRequest(
            brandItemRequests=[
                KoddiAdvertiserMultiBrand(brandId="brand11", primary=True, percentage=1.0),
                KoddiAdvertiserMultiBrand(brandId="brand22", primary=False, percentage=0.0),
                KoddiAdvertiserMultiBrand(brandId="brand33", primary=False, percentage=0.0)
            ],
            agencyId=None
        ))

    async def test_get_koddi_advertiser_multi_brand__returns_koddi_id_early_if_exists(self):
        internal_advertisers_ids = ["brand1", "brand2"]
        internal_agency_id = "agency1"
        koddi_id = 1234
        self.mock_koddi_sso_gateway.get_multi_brand_advertiser.return_value = auto_mock({
            "koddiId": koddi_id
        }, MagicMock(spec=KoddiBrandResponse))

        result = await self.__subject.get_koddi_advertiser_multi_brand(
            internal_advertisers_ids,
            internal_agency_id
        )

        self.assertEqual(koddi_id, result)

    async def test_get_koddi_advertiser_id_single_brand__gets_id_for_advertiser_with_agency(self):
        advertiser_id = "1234"
        agency_id = "4567"
        koddi_id = 9874
        (
            self.__lookup_service
            .get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id
            .return_value
        ) = koddi_id

        koddi_id_result = await self.__subject.get_koddi_advertiser_id_single_brand(
            advertiser_id,
            agency_id
        )

        self.assertEqual(koddi_id, koddi_id_result)
        (
            self.__lookup_service
            .get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id
            .assert_called_once_with(advertiser_id, agency_id)
        )

    async def test_get_koddi_advertiser_id_single_brand__gets_id_for_advertiser_without_agency(self):
        advertiser_id = "1234"
        koddi_id = 9874
        (
            self.__lookup_service
            .get_koddi_advertiser_short_id_by_long_id
            .return_value
        ) = koddi_id

        koddi_id_result = await self.__subject.get_koddi_advertiser_id_single_brand(
            advertiser_id,
            None
        )

        self.assertEqual(koddi_id, koddi_id_result)
        (
            self.__lookup_service
            .get_koddi_advertiser_short_id_by_long_id
            .assert_called_once_with(advertiser_id)
        )