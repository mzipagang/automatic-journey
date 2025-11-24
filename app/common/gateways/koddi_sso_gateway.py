from typing import List

from fastapi import Depends

from app.common.configuration.constants import KODDI_SSO_SERVICE_ENDPOINT, KODDI_SSO_SERVICE_BRANDS_PATH, \
    KODDI_SSO_SERVICE_ADVERTISERS_PATH
from app.common.decorators.locked import locked_with_params
from app.common.model.advertiser import KoddiAdvertiser
from app.common.model.configuration import LockConfig
from app.common.model.downstream.advertiser_service import KoddiAdvertiserMultiBrandRequest, KoddiAdvertiserResponse, \
    KoddiBrandResponse
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.utils.async_adapter import AsyncAdapter
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class KoddiSSOGateway:
    """KoddiSSOGateway is a class that provides methods to interact with map-koddi-sso-service.

    Raises:
        HTTPException
            If the API response indicates a server error or if the request fails.
    """
    __external_api_http_client: AsyncAdapter
    ENDPOINT = KODDI_SSO_SERVICE_ENDPOINT
    __koddi_advertisers_shim_path = KODDI_SSO_SERVICE_ADVERTISERS_PATH
    __koddi_brands_shim_path = KODDI_SSO_SERVICE_BRANDS_PATH

    def __init__(
            self,
            async_external_api_http_client_service: AsyncExternalApiHttpClientService = Depends(
                AsyncExternalApiHttpClientService),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__external_api_http_client = AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_KODDI_SSO,
            harness_service=harness_service
        )

    async def get_advertisers(self, internal_advertiser_id: str) -> list[KoddiBrandResponse]:
        response = await self.__external_api_http_client.get(
            path=self.__koddi_brands_shim_path,
            params={'filter.brandId': internal_advertiser_id},
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )
        brands = response.json().get("data", [])
        return [KoddiBrandResponse(**brand) for brand in brands]

    async def get_advertiser_by_agency(
            self,
            internal_advertiser_id: str,
            internal_agency_id: str
    ) -> KoddiBrandResponse | None:
        advertisers = await self.get_advertisers(internal_advertiser_id)
        agency_advertiser = next((
            advertiser
            for advertiser in advertisers
            if advertiser.agencyId == internal_agency_id
        ), None)

        return agency_advertiser

    @staticmethod
    def advertiser_lock_key(
            internal_advertiser_id: str,
            internal_agency_id: str | None = None,
    ) -> str:
        key = internal_advertiser_id
        if internal_agency_id is not None:
            key = f"{key}:{internal_agency_id}"
        return key

    @locked_with_params(
        advertiser_lock_key,
        logger,
        LockConfig(enabled=True, lock_prefix="lock_koddi_advertiser_creation", expire_seconds=100),
        lock_config_name=HarnessFeatureFlags.KODDI_ADVERTISER_CREATION_LOCK
    )
    async def create_advertiser_by_agency(
            self,
            internal_advertiser_id: str,
            internal_agency_id: str
    ) -> KoddiAdvertiserResponse:
        response = await self.__external_api_http_client.post(
            path=self.__koddi_brands_shim_path,
            json={
                "brandItemRequests": [{
                    "brandId": internal_advertiser_id,
                    "primary": True,
                    "percentage": 1
                }],
                "agencyId": internal_agency_id
            },
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )

        return KoddiAdvertiserResponse(**response.json().get('data', {}))

    async def get_advertisers_for_user(self) -> list[KoddiAdvertiser]:
        response = await self.__external_api_http_client.get(
            path=self.__koddi_advertisers_shim_path,
            response_body_type="json",
            json_has_data_field=True)

        koddi_advertisers = response.json().get('data', [])
        return [
            KoddiAdvertiser(**advertiser)
            for advertiser in koddi_advertisers
            if advertiser.get('koddiId') is not None
        ]

    @staticmethod
    def multi_brand_lock_key(
            advertiser_multi_brand_request: KoddiAdvertiserMultiBrandRequest
    ) -> str:
        brand_ids = [brand.brandId for brand in advertiser_multi_brand_request.brandItemRequests]
        key = ",".join(brand_ids)
        agency_id = advertiser_multi_brand_request.agencyId
        if agency_id is not None:
            key = f"{key}:{agency_id}"
        return key

    @locked_with_params(
        multi_brand_lock_key,
        logger,
        LockConfig(enabled=True, lock_prefix="lock_koddi_advertiser_creation", expire_seconds=100),
        lock_config_name=HarnessFeatureFlags.KODDI_ADVERTISER_CREATION_LOCK
    )
    async def create_multi_brand_advertiser(
            self,
            advertiser_multi_brand_request: KoddiAdvertiserMultiBrandRequest
    ) -> KoddiAdvertiserResponse:
        response = await self.__external_api_http_client.post(
            path=self.__koddi_brands_shim_path,
            json=advertiser_multi_brand_request.model_dump(),
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )

        return KoddiAdvertiserResponse(**response.json().get("data"))

    async def get_multi_brand_advertiser(
            self,
            advertiser_ids: List[str],
            internal_agency_id: str | None = None
    ) -> KoddiBrandResponse | None:
        params = {
            'filter.brandId': advertiser_ids,
        }
        if internal_agency_id is not None:
            params['filter.agencyId'] = internal_agency_id
        response = await self.__external_api_http_client.get(
            path=self.__koddi_brands_shim_path,
            params=params,
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )
        brands = response.json().get("data", [])
        koddi_brands = [KoddiBrandResponse(**brand) for brand in brands]
        koddi_brand = next((
            brand
            for brand in koddi_brands
            if brand.agencyId == internal_agency_id
        ), None)

        return koddi_brand