import json
from typing import List

from fastapi import Depends, HTTPException

from app.common.gateways.ent_client_service_gateway import EntClientServiceGateway
from app.common.gateways.koddi_sso_gateway import KoddiSSOGateway
from app.common.model.downstream.advertiser_service import (
    KoddiAdvertiserMultiBrand,
    KoddiAdvertiserMultiBrandRequest,
    KoddiBrandResponse,
)
from app.common.model.redis import CachedRedisAdvertiser
from app.common.services.lookup_service import LookupService
from app.common.model.account import InternalAccount
from app.common.model.advertiser import Advertiser, CachedAdvertiser, KoddiAdvertiser
from app.common.services.config_service import ConfigService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class AdvertiserService:
    __external_api_http_client: ExternalApiHttpClientService
    __product_id: str

    def __init__(
            self,
            config_service: ConfigService = Depends(ConfigService),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            lookup_service: LookupService = Depends(LookupService),
            koddi_sso_gateway: KoddiSSOGateway = Depends(KoddiSSOGateway),
            ent_client_service_gateway: EntClientServiceGateway = Depends(EntClientServiceGateway),
    ):
        self.__product_id = config_service.get_current_config().product_id
        self.__external_api_http_client = external_api_http_client_service
        self.lookup_service = lookup_service
        self.koddi_sso_gateway = koddi_sso_gateway
        self.ent_client_service_gateway = ent_client_service_gateway

    async def __cache_advertisers_details_by_short_id(self, advertisers_table: dict[str, tuple[int, CachedRedisAdvertiser]]) -> None:
        short_ids_to_lookup = [short_id for short_id, _ in advertisers_table.values()]
        details_by_short_id = await self.lookup_service.get_advertiser_details_by_short_ids(short_ids_to_lookup)
        missing_details_by_short_id_table = {
            int(short_id): details for
            (short_id, details), details_in_cache
            in zip(advertisers_table.values(), details_by_short_id)
            if details_in_cache is None
        }
        if missing_details_by_short_id_table:
            await self.lookup_service.set_advertiser_details_by_short_id_batch(missing_details_by_short_id_table)

    async def __cache_advertisers_by_long_id(self, advertisers_table: dict[str, tuple[int, CachedRedisAdvertiser]]) -> None:
        long_ids_without_short_ids = [long_id for long_id, (short_id, _) in advertisers_table.items() if
                                        short_id is None]

        if long_ids_without_short_ids:
            new_short_ids = await self.lookup_service.set_advertiser_short_id_by_long_id_batch(
                long_ids_without_short_ids)

            new_short_id_by_long_id_table = {long_id: new_short_id for long_id, new_short_id in
                                             zip(long_ids_without_short_ids, new_short_ids)}

            for long_id, new_short_id in new_short_id_by_long_id_table.items():
                advertisers_table[long_id] = (new_short_id, advertisers_table[long_id][1])

    async def get_advertisers(self, account: InternalAccount, account_id: int) -> List[Advertiser]:
        advertisers_response = await self.ent_client_service_gateway.get_brands(account.id)
        advertisers = [advertiser for advertiser in advertisers_response.data]
        long_advertiser_ids = [advertiser.brandId for advertiser in advertisers]
        short_advertiser_ids = await self.lookup_service.get_advertiser_short_id_by_long_id_batch(long_advertiser_ids)
        advertisers_table = {
            advertiser.brandId: (
                short_id,
                advertiser
            ) for advertiser, short_id in zip(advertisers, short_advertiser_ids)
        }
        await self.__cache_advertisers_by_long_id(advertisers_table)
        await self.__cache_advertisers_details_by_short_id(advertisers_table)
        return [
            Advertiser(
                id=short_id,
                name=advertiser.displayName,
                accountId=account_id,
                description=f"{account.name} - {advertiser.displayName}",
                active=True
            ) for short_id, advertiser in advertisers_table.values()
        ]

    async def __cache_koddi_ids_by_brands_or_agency(
            self,
            response: list[KoddiBrandResponse],
            internal_advertiser_id: str
    ) -> None:
        koddi_id_by_internal_adv = {
            internal_advertiser_id: koddi_advertiser_data.koddiId
            for koddi_advertiser_data in response
            if koddi_advertiser_data.agencyId is None
        }
        koddi_id_by_internal_adv_and_agency = {
            f'{internal_advertiser_id}:{koddi_advertiser_data.agencyId}': koddi_advertiser_data.koddiId
            for koddi_advertiser_data in response if koddi_advertiser_data.agencyId is not None
        }
        await self.lookup_service.set_koddi_advertiser_short_id_batch(koddi_id_by_internal_adv)
        await self.lookup_service.set_koddi_advertiser_short_id_batch(koddi_id_by_internal_adv_and_agency)

    async def get_koddi_advertiser_id_single_brand(
            self,
            internal_advertiser_id: str,
            internal_agency_id: str = None
    ) -> int | None:
        if internal_agency_id:
            return await self.get_koddi_advertiser_id_for_agency(
                internal_advertiser_id,
                internal_agency_id
            )

        return await self.get_koddi_advertiser_id(internal_advertiser_id)

    async def get_koddi_advertiser_id(self, internal_advertiser_id: str) -> int | None:
        cached = await self.lookup_service.get_koddi_advertiser_short_id_by_long_id(internal_advertiser_id)
        if not cached:
            response = await self.koddi_sso_gateway.get_advertisers(internal_advertiser_id)
            await self.__cache_koddi_ids_by_brands_or_agency(response, internal_advertiser_id)
            cached = await self.lookup_service.get_koddi_advertiser_short_id_by_long_id(internal_advertiser_id)
        return cached

    async def get_koddi_advertiser_id_for_agency(
            self,
            internal_advertiser_id: str,
            internal_agency_id: str
    ) -> int:
        koddi_advertiser_id = await (
            self.lookup_service.
            get_koddi_advertiser_short_id_by_long_advertiser_id_and_long_agency_id(
                internal_advertiser_id,
                internal_agency_id
            )
        )

        # If we found a cached koddi id, stop and return early
        if koddi_advertiser_id:
            return koddi_advertiser_id

        # If there's no cached koddi id, try to get an existing brand from upstream
        koddi_brand_data = await self.koddi_sso_gateway.get_advertiser_by_agency(
            internal_advertiser_id,
            internal_agency_id
        )

        # If we found koddi brand data, stop early and return
        if koddi_brand_data:
            await self.lookup_service.set_koddi_advertiser_short_id_by_long_id_and_agency_id(
                internal_advertiser_id,
                internal_agency_id,
                koddi_brand_data.koddiId
            )
            return koddi_brand_data.koddiId

        # If there's no brand upstream, create one.
        koddi_advertiser_data = await self.koddi_sso_gateway.create_advertiser_by_agency(
            internal_advertiser_id,
            internal_agency_id
        )
        await self.lookup_service.set_koddi_advertiser_short_id_by_long_id_and_agency_id(
            internal_advertiser_id,
            internal_agency_id,
            koddi_advertiser_data.id
        )

        return koddi_advertiser_data.id

    async def get_advertiser_by_numeric_id(self, advertiser_id: int) -> CachedAdvertiser:
        cached_advertiser = await self.lookup_service.get_advertiser_details_by_short_id(advertiser_id)
        if cached_advertiser is None:
            logger.warning("Advertiser ID: %s not found in cache", advertiser_id)
            raise HTTPException(status_code=404, detail="Advertiser not found")
        advertiser = json.loads(cached_advertiser.model_dump_json())
        logger.debug("Found advertiser %s", cached_advertiser.model_dump_json())
        return CachedAdvertiser(
            id=advertiser_id,
            brandId=advertiser['brandId'],
            name=advertiser['displayName'],
            accountId=0,
            description=f"{''} - {advertiser['displayName']}",
            active=True
        )

    async def get_advertisers_for_user(self) -> list[KoddiAdvertiser]:
        return await self.koddi_sso_gateway.get_advertisers_for_user()

    async def get_advertisers_by_numeric_ids(self, advertiser_ids: List[int]) -> List[CachedAdvertiser]:
        cached_advertisers = await self.lookup_service.get_advertiser_details_by_short_ids(advertiser_ids)
        if any(advertiser is None for advertiser in cached_advertisers):
            logger.warning(
                "Advertiser IDs: %s not found in cache",
                [
                    advertiser_id
                    for advertiser_id, advertiser in
                    zip(advertiser_ids, cached_advertisers) if advertiser is None
                ]
            )
            raise HTTPException(status_code=404, detail="Advertisers not found")
        logger.debug("Found advertisers %s", cached_advertisers)

        return [
            CachedAdvertiser(
                id=short_id,
                brandId=advertiser.brandId,
                name=advertiser.displayName,
                accountId=0,
                description=f"{''} - {advertiser.displayName}",
                active=True
            )
            for advertiser, short_id in zip(cached_advertisers, advertiser_ids)
        ]

    async def get_or_create_cached_advertiser_id(self, advertiser_id: str) -> int:
        cached_advertiser_id = await self.lookup_service.get_advertiser_short_id_by_long_id(advertiser_id)
        if not cached_advertiser_id:
            return await self.lookup_service.set_advertiser_short_id_by_long_id(advertiser_id)
        return cached_advertiser_id

    async def get_or_create_cached_advertiser_ids(self, advertiser_ids: List[str]) -> List[int | None]:
        cached_advertiser_ids = await self.lookup_service.get_advertiser_short_id_by_long_id_batch(advertiser_ids)
        if any(advertiser_id is None for advertiser_id in cached_advertiser_ids):
            new_ids =  await self.lookup_service.set_advertiser_short_id_by_long_id_batch(
                [
                    advertiser_id
                    for advertiser_id, cached_id
                    in zip(advertiser_ids, cached_advertiser_ids) if cached_id is None
                ]
            )
            cached_advertiser_ids = [adv_id for adv_id in cached_advertiser_ids if adv_id is not None]
            cached_advertiser_ids.extend(new_ids)
        return cached_advertiser_ids

    @staticmethod
    def __build_advertiser_multi_brand(i_advertiser_id:tuple[int,str]) -> KoddiAdvertiserMultiBrand:
        i, advertiser_id = i_advertiser_id
        return KoddiAdvertiserMultiBrand(
            brandId= advertiser_id,
            primary= i == 0,
            percentage= 1.0 if i == 0 else 0.0,
        )

    async def get_koddi_advertiser_multi_brand(
            self,
            advertiser_ids: List[str],
            internal_agency_id: str = None
    ) -> int:
        # Use single advertiser flow if there's only 1 advertiser id
        if len(advertiser_ids) == 1:
            return await self.get_koddi_advertiser_id_single_brand(
                advertiser_ids[0],
                internal_agency_id
            )

        multi_brand_advertiser = await self.koddi_sso_gateway.get_multi_brand_advertiser(
            advertiser_ids,
            internal_agency_id
        )
        if multi_brand_advertiser:
            return multi_brand_advertiser.koddiId

        payload = KoddiAdvertiserMultiBrandRequest(
            brandItemRequests=list(map(
                self.__build_advertiser_multi_brand,
                enumerate(advertiser_ids)
            )),
            agencyId=internal_agency_id,
        )
        response = await self.koddi_sso_gateway.create_multi_brand_advertiser(payload)

        return response.id
