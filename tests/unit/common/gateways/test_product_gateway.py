from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from httpx import Response

from app.common.configuration.constants import UPCS_LAST_SOLD_WITHIN_DAYS
from app.common.gateways.product_gateway import ProductGateway
from app.common.model.downstream.product_manager import ProductManagerMeta, ProductManagerMetaPage, Product, Taxonomy, \
    Restrictions, TaxonomyProperties, ProductSearchResponse
from app.common.model.shared import ListDataResponse, SingleDataResponse


class TestProductGateway(IsolatedAsyncioTestCase):
    def setUp(self):
        self.__mock_external_http_client_service = MagicMock()
        self.__mock_async_external_http_client_service = AsyncMock()
        self.__mock_harness_service = MagicMock()

        self.__mock_harness_service.is_harness_flag_on.return_value = True

        self.product_gateway = ProductGateway(
            async_external_api_http_client_service=self.__mock_async_external_http_client_service,
            external_api_http_client_service=self.__mock_external_http_client_service,
            harness_service=self.__mock_harness_service,
        )
        self.mock_product = Product(
            upc="0000000004011",
            description="",
            isValid=True,
            brand="",
            quantity="",
            taxonomy=Taxonomy(
                department=TaxonomyProperties(
                    id="id",
                    name="name"
                ),
                commodity=TaxonomyProperties(
                    id="id",
                    name="name"
                ),
                subCommodity=TaxonomyProperties(
                    id="id",
                    name="name"
                )
            ),
            restrictions=Restrictions(
                prohibited=False,
                sensitive=False,
                notRestricted=False,
                notFound=False
            ),
            lastSoldDate="2025-05-12"
        )

    async def test_get_products_by_advertisers__returns_products(self):
        advertiser_names = ['brandName']
        offset = 0
        page_size = 10
        expected_result = ListDataResponse[Product, ProductManagerMeta](
            data=[self.mock_product],
            meta=ProductManagerMeta(
                page=ProductManagerMetaPage(
                    offset=offset,
                    size=page_size,
                    totalSize=1
                )
            )
        )
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json=expected_result.model_dump()
        )

        result = await self.product_gateway.get_products_by_advertisers(
            advertiser_names,
            offset,
            page_size
        )

        self.assertEqual(expected_result, result)
        self.__mock_async_external_http_client_service.get.assert_called_with(
            path="/product-manager/products/search",
            params={
                "filter.brandCodes": advertiser_names,
                "filter.lastSoldWithinDays": UPCS_LAST_SOLD_WITHIN_DAYS,
                "start": offset,
                "limit": page_size
            },
            response_body_type="json",
            forward_client_error_response_content=True
        )

    async def test_get_products_by_upcs__returns_products(self):
        advertiser_names = ['brandName']
        upcs = ["0000000004011"]
        expected_result = SingleDataResponse[ProductSearchResponse, ProductManagerMeta](
            data=ProductSearchResponse(
                validProducts=[self.mock_product],
                alternateProducts=[],
                invalidProducts=[]
            ),
            meta=ProductManagerMeta(
                page=ProductManagerMetaPage(
                    offset=0,
                    size=10,
                    totalSize=1
                )
            )
        )
        self.__mock_async_external_http_client_service.post.return_value = Response(
            status_code=200,
            json=expected_result.model_dump()
        )

        result = await self.product_gateway.get_products_by_upcs(upcs, advertiser_names)

        self.assertEqual(expected_result, result)
        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/product-manager/products/search",
            json={
                "upcs": upcs,
                "brandCodes": advertiser_names,
                "lastSoldWithinDays": UPCS_LAST_SOLD_WITHIN_DAYS
            },
            response_body_type="json",
            forward_client_error_response_content=True
        )

    async def test_get_products_by_upcs__advertisers_is_optional(self):
        upcs = ["0000000004011"]
        expected_result = SingleDataResponse[ProductSearchResponse, ProductManagerMeta](
            data=ProductSearchResponse(
                validProducts=[self.mock_product],
                alternateProducts=[],
                invalidProducts=[]
            ),
            meta=ProductManagerMeta(
                page=ProductManagerMetaPage(
                    offset=0,
                    size=10,
                    totalSize=1
                )
            )
        )
        self.__mock_async_external_http_client_service.post.return_value = Response(
            status_code=200,
            json=expected_result.model_dump()
        )

        result = await self.product_gateway.get_products_by_upcs(upcs)

        self.assertEqual(expected_result, result)
        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/product-manager/products/search",
            json={
                "upcs": upcs,
                "lastSoldWithinDays": UPCS_LAST_SOLD_WITHIN_DAYS
            },
            response_body_type="json",
            forward_client_error_response_content=True
        )