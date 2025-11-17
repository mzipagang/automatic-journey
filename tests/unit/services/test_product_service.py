from copy import deepcopy
from typing import List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from httpx import Response

from app.common.model.downstream.product_manager import ProductManagerMeta, ProductManagerMetaPage, Product, \
    ProductSearchResponse
from app.common.model.shared import ListDataResponse, SingleDataResponse
from app.common.model.advertiser import CachedAdvertiser
from app.common.model.downstream.bid_manager import SuggestionsResponse, Suggestion, SuggestedBid
from app.common.model.campaign_types import InternalCampaignType
from app.common.services.product_service import ProductService
from tests.unit.services.constants import (
    FETCHED_PRODUCT_PRICES_RESPONSE_JSON,
    FETCHED_RAW_PRODUCTS_RESPONSE_JSON,
    TEST_PRODUCTS, PRODUCT_MANAGER_PRODUCT,
)


class TestProductService(IsolatedAsyncioTestCase):
    __mock_external_http_client_service: MagicMock

    @staticmethod
    def __product(**kwargs):
        product_json = deepcopy(PRODUCT_MANAGER_PRODUCT)
        return Product(**{
            **product_json,
            **kwargs
        })

    def setUp(self):
        self.lookup_service = AsyncMock()
        self.mock_advertiser_service = AsyncMock()
        self.mock_bid_manager_service = AsyncMock()
        self.__mock_external_http_client_service = MagicMock()
        self.mock_product_gateway = AsyncMock()

        self.subject = ProductService(
            lookup_service=self.lookup_service,
            advertiser_service=self.mock_advertiser_service,
            external_api_http_client_service=self.__mock_external_http_client_service,
            bid_manager_service=self.mock_bid_manager_service,
            product_gateway=self.mock_product_gateway,
        )

        self.upcs = ['0001200017023', '0001200001643', '0001200012635', '0001200001756']

    async def test_get_products_by_brand__should_succeed(self):
        mock_raw_products_response = deepcopy(FETCHED_RAW_PRODUCTS_RESPONSE_JSON)
        upcs = [ product.get("upc") for product in mock_raw_products_response["data"]]
        koddi_advertiser_id = 1234
        self.mock_product_gateway.get_products_by_advertisers.return_value = ListDataResponse[Product, ProductManagerMeta](
            data=[
                self.__product(**product_json)
                for product_json in mock_raw_products_response["data"]
            ],
            meta=ProductManagerMeta(page=ProductManagerMetaPage(
                offset=0,
                size=10,
                totalSize=1,
            ))
        )
        self.__mock_external_http_client_service.post.side_effect = [
            Response(200, json=deepcopy(FETCHED_PRODUCT_PRICES_RESPONSE_JSON)), Response(404)]
        self.lookup_service.get_product_short_id_by_upc_batch.return_value = [n for n in range(len(mock_raw_products_response['data']))]

        self.mock_bid_manager_service.get_suggestions.return_value = SuggestionsResponse(
            suggestions=[
                Suggestion(id='0001200017023', bid_information=SuggestedBid(lowest_bid=0.5, highest_bid=1.0)),
                Suggestion(id='0001200001643', bid_information=SuggestedBid(lowest_bid=0.3, highest_bid=0.8))
            ]
        )
        self.mock_advertiser_service.get_koddi_advertiser_id_for_agency.return_value = koddi_advertiser_id

        expected_products = TEST_PRODUCTS
        result = await self.subject.get_products_by_brand(
            [CachedAdvertiser(brandId='123')],
            0,
            10,
            'agency_id',
            InternalCampaignType.PLA
        )

        self.mock_bid_manager_service.get_suggestions.assert_called_once_with(
            koddi_advertiser_id,
            upcs,
            InternalCampaignType.PLA
        )
        self.assertIsNotNone(result)
        self.assertEqual((expected_products, False), result)

    async def test_get_products_by_upcs__returns_product_dict(self):
        upcs = ['4011']
        products = [self.__product(upc=upc) for upc in upcs]
        get_products_response =  SingleDataResponse[ProductSearchResponse, ProductManagerMeta](
            data=ProductSearchResponse(
                validProducts=products,
                alternateProducts=[],
                invalidProducts=[],
            ),
            meta=ProductManagerMeta(page=ProductManagerMetaPage(
                offset=0,
                size=1,
                totalSize=1,
            ))
        )
        expected_response = {p.upc: p for p in products}
        self.mock_product_gateway.get_products_by_upcs.return_value = get_products_response

        result = await self.subject.get_products_by_upcs(upcs)

        self.assertEqual(expected_response, result)
        self.mock_product_gateway.get_products_by_upcs.assert_called_once_with(upcs, None)

    async def test_get_products_by_brand__skips_setting_suggested_bids_if_bid_manager_returns_404(self):
        advertiser_id = 1234
        brand_id = 'brandId'
        koddi_advertiser_id = 4321
        upc = '4011'
        entity_id = 1104

        advertiser = CachedAdvertiser(
            id=advertiser_id,
            brandId=brand_id,
            name='brandName'
        )
        products_by_advertisers_response = ListDataResponse[Product, ProductManagerMeta](
            data=[self.__product(upc=upc)],
            meta=ProductManagerMeta(page=ProductManagerMetaPage(
                offset=0,
                size=10,
                totalSize=1,
            ))
        )
        price_response = Response(status_code=200, json={
            "data": {
                "productPrices": [
                    {
                        "productId": upc,
                        "price": {
                            "average": 1.0,
                        }
                    }
                ]
            }
        })
        self.mock_advertiser_service.get_koddi_advertiser_id.return_value = koddi_advertiser_id
        self.mock_product_gateway.get_products_by_advertisers.return_value = products_by_advertisers_response
        self.lookup_service.get_product_short_id_by_upc_batch.return_value = [entity_id]
        self.__mock_external_http_client_service.post.return_value = price_response
        self.mock_bid_manager_service.get_suggestions = MagicMock(side_effect=[
            HTTPException(status_code=404, detail="No details found")
        ])

        products, has_more = await self.subject.get_products_by_brand([advertiser])

        self.assertEqual(0, products[0].minSuggestedBid)
        self.assertEqual(0, products[0].maxSuggestedBid)

    async def test_get_products_by_brand__pass_last_sold_and_koddi_id__should_use_params(self):
        from app.common.model.downstream.product_manager import Product as ProductManagerProduct

        self.mock_product_gateway.get_products_by_advertisers.return_value = AsyncMock(
            spec=ListDataResponse[Product, ProductManagerMeta],
            data=MagicMock(spec=List[ProductManagerProduct]),
            meta=MagicMock(spec=ProductManagerMeta,
                           page=MagicMock(spec=ProductManagerMeta, offset=0, size=1, totalSize=1))
        )
        advertisers: List[CachedAdvertiser] = [CachedAdvertiser(name="name")]
        await self.subject.get_products_by_brand(
            advertisers=advertisers,
            last_sold_within_days=4242,
            koddi_advertiser_id=424242,
        )

        self.mock_advertiser_service.get_koddi_advertiser_id.assert_not_called()
        self.mock_product_gateway.get_products_by_advertisers.assert_called_once_with(
            advertiser_names=['name'],
            offset=None,
            page_size=None,
            last_sold_within_days=4242
        )
