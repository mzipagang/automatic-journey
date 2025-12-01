from typing import List

from fastapi import Depends

from app.common.configuration.constants import UPCS_LAST_SOLD_WITHIN_DAYS
from app.common.model.downstream.product_manager import (
    Product,
    ProductManagerMeta,
    ProductSearchResponse,
    ProductSelection,
    ProductSnapshot,
    CreateProductSelection,
    CreateProductSnapshot,
    CreateProductSelectionParams
)
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.model.shared import ListDataResponse, SingleDataResponse
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils.async_adapter import AsyncAdapter

class ProductGateway:
    __external_api_http_client: AsyncAdapter

    def __init__(
        self,
        async_external_api_http_client_service: AsyncExternalApiHttpClientService = Depends(AsyncExternalApiHttpClientService),
        external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
        harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__external_api_http_client = AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_PRODUCT,
            harness_service=harness_service
        )

    async def get_products_by_advertisers(
            self,
            advertiser_names: List[str],
            offset: int,
            page_size: int,
            last_sold_within_days: int = UPCS_LAST_SOLD_WITHIN_DAYS,
    ) -> ListDataResponse[Product, ProductManagerMeta]:
        """
        Makes a GET request to product manager to search products by advertisers
        """
        path = "/product-manager/products/search"
        response = await self.__external_api_http_client.get(
            path=path,
            params={
                "filter.brandCodes": advertiser_names,
                "filter.lastSoldWithinDays": last_sold_within_days,
                "start": offset,
                "limit": page_size
            },
            response_body_type="json",
            forward_client_error_response_content=True
        )

        return ListDataResponse[Product, ProductManagerMeta](**response.json())

    async def get_products_by_upcs(
            self,
            upcs: List[str],
            advertiser_names: List[str] = None,
            last_sold_within_days: int | None = UPCS_LAST_SOLD_WITHIN_DAYS,
    ) -> SingleDataResponse[ProductSearchResponse, ProductManagerMeta]:
        """
        Makes a POST request to product manager to search for products by UPCs
        """
        path = "/product-manager/products/search"
        request_body = {
            "upcs": upcs,
            "lastSoldWithinDays": last_sold_within_days
        }

        if advertiser_names:
            request_body["brandCodes"] = advertiser_names

        response = await self.__external_api_http_client.post(
            path=path,
            json=request_body,
            response_body_type="json",
            forward_client_error_response_content=True
        )

        return SingleDataResponse[ProductSearchResponse, ProductManagerMeta](**response.json())

    async def get_product_selection(self, product_selection_id: str) -> ProductSelection:
        path = f"/product-manager/product-selection/{product_selection_id}"
        response = await self.__external_api_http_client.get(
            path=path,
            response_body_type="json",
            forward_client_error_response_content=True
        )

        return ProductSelection(**response.json())

    async def create_product_selection(self, upcs: List[str]) -> str:
        path = "/product-manager/product-selection"
        request_body = CreateProductSelection.from_upcs(upcs)
        request_params = CreateProductSelectionParams(
            enforceProductGroupCreationValidation=True
        )

        response = await self.__external_api_http_client.post(
            path=path,
            params=request_params.model_dump(),
            json=request_body.model_dump(),
            response_body_type="json",
            forward_client_error_response_content=True
        )

        product_selection = ProductSelection(**response.json())
        return product_selection.id

    async def get_product_snapshot(self, product_snapshot_id: str) -> ProductSnapshot:
        path = f"/product-manager/snapshot/{product_snapshot_id}"
        response = await self.__external_api_http_client.get(
            path=path,
            response_body_type="json",
            forward_client_error_response_content=True
        )

        return ProductSnapshot(**response.json())

    async def create_product_snapshot(self, product_selection_id: str) -> str:
        path = "/product-manager/snapshot"
        request_body = CreateProductSnapshot(id=product_selection_id)

        response = await self.__external_api_http_client.post(
            path=path,
            json=request_body.model_dump(),
            response_body_type="json",
            forward_client_error_response_content=True
        )

        product_snapshot = ProductSnapshot(**response.json())
        return product_snapshot.id
