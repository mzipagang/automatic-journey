from copy import deepcopy
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import Response

from app.common.context.context import request_context, user_context
from app.common.model.address import AdvertiserAddress, AccountAddressResponse, AccountAddress
from app.common.model.advertiser import AdvertiserType
from app.common.services.address_service import AdvertiserAddressService
from tests.unit.services.constants import FETCH_ADDRESSES_RESPONSE_JSON, SIMPLE_CONFIG


class TestAddressService(IsolatedAsyncioTestCase):
    __mock_config_service: MagicMock
    __mock_ent_service: AsyncMock
    __mock_lookup_service: AsyncMock

    def setUp(self) -> None:
        self.__mock_config_service = MagicMock()
        self.__mock_ent_service = AsyncMock()
        self.__mock_lookup_service = AsyncMock()
        self.__mock_config_service.get_current_config.return_value = deepcopy(SIMPLE_CONFIG)

        FastAPICache.init(backend=InMemoryBackend(), prefix="test")

        self.subject = AdvertiserAddressService(
            config_service=self.__mock_config_service,
            ent_service=self.__mock_ent_service,
            lookup_service=self.__mock_lookup_service,
        )


    @pytest.mark.asyncio
    async def test_get_and_cache_addresses_by_account__should_succeed(self):
        user_context.set({"username": "test"})
        request_context.set({"path": "/test"})
        self.__mock_ent_service.get_addresses_by_account.return_value = AccountAddressResponse(
            data=[AccountAddress(
                cityTown='Atlanta',
                stateProvince='GA',
                postalCode='30313-2420',
                countryCode='US',
                addressLines=['1 Coca Cola Plz NW', ''],
                status="Verified",
            )],
        )
        self.__mock_lookup_service.get_address_short_id_by_long_id_batch.return_value = [123]
        expected = [
            AdvertiserAddress(id=123, companyName='account_name', addressLine1='1 Coca Cola Plz NW', addressLine2='',
                              city='Atlanta', state='GA', postalCode='30313-2420', country='US',
                              addressType=AdvertiserType.CPG, active=True)]

        actual = await self.subject.get_and_cache_addresses_by_account(
            account_id='abc123',
            account_name="account_name",
            advertiser_type=AdvertiserType.CPG)

        self.assertEqual(expected, actual)

        self.__mock_ent_service.get_addresses_by_account.assert_called_once_with('abc123')


    @pytest.mark.asyncio
    async def test_cache_corporate_address_by_internal_account_id__should_succeed(self):
        user_context.set({"username": "test"})
        request_context.set({"path": "/test"})

        addresses = [
            AccountAddress(
                id='addr_123',
                cityTown='Atlanta',
                stateProvince='GA',
                postalCode='30313-2420',
                countryCode='US',
                addressLines=['1 Coca Cola Plz NW', ''],
                addressType='CORPORATE',
                status='Verified',
            ),
            AccountAddress(
                id='addr_456',
                cityTown='New York',
                stateProvince='NY',
                postalCode='10001',
                countryCode='US',
                addressLines=['123 Main St', ''],
                addressType='BILLING',
                status='Verified',
            )
        ]

        await self.subject.cache_corporate_address_by_internal_account_id(
            addresses=addresses,
            internal_account_id='internal_abc123'
        )

        self.__mock_lookup_service.set_address_long_id_by_account_long_id.assert_called_once_with(
            'addr_123',
            'internal_abc123'
        )
