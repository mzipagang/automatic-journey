import json
from typing import List

from fastapi import Depends, HTTPException

from app.common.cache.key_builders import get_addresses_by_account__upstream_key_builder
from app.common.decorators.decorators import conditional_cache
from app.common.gateways.ent_client_service_gateway import EntClientServiceGateway
from app.common.model.address import AdvertiserAddress, AccountAddress
from app.common.model.advertiser import AdvertiserType
from app.common.model.redis import CachedAddress
from app.common.services.config_service import ConfigService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.services.lookup_service import LookupService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class AdvertiserAddressService:
    __product_id: str

    def __init__(self,
                 config_service: ConfigService = Depends(ConfigService),
                 ent_service: EntClientServiceGateway = Depends(EntClientServiceGateway),
                 lookup_service: LookupService = Depends(LookupService)):
        """Constructor for the AddressService class"""
        self.__product_id = config_service.get_current_config().product_id
        self.ent_service = ent_service
        self.lookup_service = lookup_service

    async def get_and_cache_addresses_by_account(
            self,
            account_id: str,
            account_name: str,
            advertiser_type: AdvertiserType) -> List[AdvertiserAddress]:

        fetched_addresses = await self.ent_service.get_addresses_by_account(account_id)

        addresses = await self.__parse_and_cache_addresses(fetched_addresses.data, account_id, account_name, advertiser_type)
        return addresses

    async def get_address_by_numeric_id(self, address_id: int) -> CachedAddress:
        cached_address = await self.lookup_service.get_address_details_by_short_id(address_id)
        if cached_address is None:
            logger.error("Address ID: %s not found in cache", address_id)
            raise HTTPException(status_code=404, detail="Address not found")
        return cached_address

    async def set_corporate_address_by_internal_account_id(self, internal_account_id: str, address_id: str):
        await self.lookup_service.set_address_long_id_by_account_long_id(address_id, internal_account_id)

    async def get_corporate_address_by_internal_account_id(self, internal_account_id: str) -> str:
        cached_corporate_address = await self.lookup_service.get_address_long_id_by_account_long_id(internal_account_id)
        if cached_corporate_address is None:
            logger.error("Corporate Address ID: %s not found in cache", internal_account_id)
            raise HTTPException(status_code=404, detail="Address not found")
        return cached_corporate_address

    async def cache_corporate_address_by_internal_account_id(
            self,
            addresses: List[AccountAddress],
            internal_account_id: str
    ):
        for addr in addresses:
            if addr.addressType == "CORPORATE":
                await self.set_corporate_address_by_internal_account_id(internal_account_id, addr.id)
                if addr.status != "Verified":
                    logger.warning("Address type is CORPORATE and status is not Verified!!!")

    async def __parse_and_cache_addresses(
            self,
            fetched_addresses: List[AccountAddress],
            internal_account_id: str,
            account_name: str,
            advertiser_type: AdvertiserType
    ) -> List[AdvertiserAddress]:
        addresses: List[AdvertiserAddress] = []

        await self.cache_corporate_address_by_internal_account_id(fetched_addresses, internal_account_id)

        verified = [addr for addr in fetched_addresses if addr.status == "Verified"]
        if not verified:
            return []

        address_ids = [addr.id for addr in verified]
        cached_address_ids = await self.lookup_service.get_address_short_id_by_long_id_batch(address_ids)

        to_mset: dict[int, CachedAddress] = {}

        for addr, address_id, aid in zip(verified, address_ids, cached_address_ids):
            if aid is None:
                aid = await self.lookup_service.set_address_short_id_by_long_id(address_id)
                if aid is None:
                    raise HTTPException(status_code=500, detail=f"Failed to assign address id {address_id}")

            payload = CachedAddress(**{
                "id": address_id,
                "addressType": advertiser_type.value,
            })
            to_mset[aid] = payload

            lines = addr.addressLines
            addr1 = lines[0] if len(lines) > 0 else ""
            addr2 = lines[1] if len(lines) > 1 else ""

            addresses.append(AdvertiserAddress(
                id=aid,
                companyName=account_name,
                addressLine1=addr1,
                addressLine2=addr2,
                city=addr.cityTown,
                state=addr.stateProvince,
                postalCode=addr.postalCode,
                country=addr.countryCode,
                addressType=advertiser_type,
                active=True,
            ))

        await self.lookup_service.set_address_details_by_short_id_batch(to_mset)

        return addresses
