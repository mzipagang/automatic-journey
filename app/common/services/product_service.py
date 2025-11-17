import json
from typing import List, Tuple

from fastapi import Depends, HTTPException
from httpx import codes as httpx_codes

from app.common.configuration.constants import UPCS_LAST_SOLD_WITHIN_DAYS
from app.common.gateways.product_gateway import ProductGateway
from app.common.model.advertiser import CachedAdvertiser
from app.common.model.campaign_types import InternalCampaignType
from app.common.model.product import Product
from app.common.model.downstream.product_manager import Product as ProductManagerProduct
from app.common.model.redis import CachedProduct
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.bid_manager_service import BidManagerService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.services.lookup_service import LookupService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class ProductService:
    advertiser_service: AdvertiserService
    bid_manager_service: BidManagerService
    lookup_service: LookupService
    product_gateway_service: ProductGateway
    __external_api_http_client: ExternalApiHttpClientService

    def __init__(
            self,
            advertiser_service: AdvertiserService = Depends(AdvertiserService),
            bid_manager_service: BidManagerService = Depends(BidManagerService),
            lookup_service: LookupService = Depends(LookupService),
            product_gateway: ProductGateway = Depends(ProductGateway),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService)):
        """Constructor for the ProductService class"""
        self.advertiser_service = advertiser_service
        self.bid_manager_service = bid_manager_service
        self.lookup_service = lookup_service
        self.product_gateway = product_gateway
        self.__external_api_http_client = external_api_http_client_service

    async def __get_cached_product_ids_batch(self, products: list[ProductManagerProduct]) -> list[int]:
        upcs = [product.upc for product in products]
        short_ids = await self.lookup_service.get_product_short_id_by_upc_batch(upcs)

        products_and_ids_by_upcs = {}
        upcs_for_missing_ids = []

        for short_id, upc, product in zip(short_ids, upcs, products):
            products_and_ids_by_upcs[upc] = {"id": short_id, "product": CachedProduct(**product.model_dump())}
            if short_id is None:
                upcs_for_missing_ids.append(upc)

        # Assign IDs for missing
        if upcs_for_missing_ids:
            missing_short_ids = await self.lookup_service.set_product_short_ids_by_upcs(upcs_for_missing_ids)
            if None in missing_short_ids:
                raise HTTPException(status_code=500, detail=f"Failed to assign product ids for {upcs_for_missing_ids}")
            for upc, short_id in zip(upcs_for_missing_ids, missing_short_ids):
                products_and_ids_by_upcs[upc]["id"] = short_id

        to_mset: dict[int, CachedProduct] = {products_and_ids_by_upcs[upc]["id"]: products_and_ids_by_upcs[upc]["product"] for upc in upcs}
        await self.lookup_service.set_product_details_by_short_id_batch(to_mset)

        return [products_and_ids_by_upcs[upc]["id"] for upc in upcs]

    async def __fetch_and_cache_products(
            self,
            advertisers: List[CachedAdvertiser],
            last_sold_within_days: int,
            offset: int = None,
            limit: int = None):
        products_by_advertiser_response = await self.product_gateway.get_products_by_advertisers(
            advertiser_names=[advertiser.name for advertiser in advertisers],
            offset=offset,
            page_size=limit,
            last_sold_within_days=last_sold_within_days)
        response_products: List[ProductManagerProduct] = products_by_advertiser_response.data
        page_meta = products_by_advertiser_response.meta.page

        products = {}
        upcs = []
        logger.info('Products returned: %s', json.dumps([p.model_dump() for p in response_products]))

        product_ids = await self.__get_cached_product_ids_batch(response_products)

        for product_id, product in zip(product_ids, response_products):
            product_entity = Product(
                id=product_id,
                upc=product.upc,
                name=product.description,
                packshot=f"https://www.kroger.com/product/images/medium/front/{product.upc}",
                price=0.00,
                maxSuggestedBid=0.00,
                minSuggestedBid=0.00,
                brand=product.brand,
                category=product.taxonomy.commodity.name,
                subcategory=product.taxonomy.subCommodity.name,
                available=product.isValid
            )
            upcs.append(product.upc)
            products[product.upc] = product_entity

        has_more = False
        if page_meta.offset + page_meta.size < page_meta.totalSize:
            has_more = True

        return products, upcs, has_more

    def __set_product_prices_by_ids(self, upcs: List[str], products: dict):
        prices_path = "/map-price-service/latest"
        response = self.__external_api_http_client.post(prices_path, json={"productIds": upcs})

        if response.status_code == httpx_codes.INTERNAL_SERVER_ERROR:
            logger.error('Price API returned 500')
            raise HTTPException(status_code=500, detail="Backend service unavailable")
        if response.status_code == httpx_codes.OK and response.json() is not None and response.json() != []:
            logger.info('Price API returned 200')
            prices_data = response.json()["data"]["productPrices"]

            for price_data in prices_data:
                try:
                    # NOTE: Consider using str.lstrip('0') to remove leading zeros, instead of below.
                    # Better: deserialize price data in a way that its keys align with product upcs

                    # aligned_key = str(int(price_data['productId']))
                    aligned_key = price_data['productId']
                except Exception as err:
                    logger.error(f"Failed align price_data productId {price_data['productId']},"
                                    " resulting in exception: %s", err)
                    continue
                if aligned_key not in products.keys():
                    logger.error("Price data productId %s (aligned_key: %s) "
                                    "not found among keys for products: %s",
                                    price_data['productId'], aligned_key, list(products.keys()))
                product = products[aligned_key]
                if price_data['price'] is not None:
                    product.price = price_data['price']['average']

    async def __set_product_bids(
            self,
            koddi_advertiser_id: int,
            upcs: List[str],
            products: dict,
            type: InternalCampaignType
    ):
        if type not in [InternalCampaignType.PLA, InternalCampaignType.TOA]:
            # Bid manager only supports pla and toa for bid suggestions.
            # https://github.com/8451LLC/map-bid-mgmt/blob/e5d69a710fb8f56ee40f371f02b5db182cdb7f8e/src/main/java/com/e451/bid_management/dto/v2/PostSuggestionsV2Request.java#L45
            logger.debug('Bid Suggestions are not supported for %s Campaign', type)
            return

        try:
            suggestions_response = await self.bid_manager_service.get_suggestions(
                koddi_advertiser_id,
                upcs,
                type
            )
        except HTTPException as err:
            # If we don't find suggestions, skip setting bids
            if err.status_code == httpx_codes.NOT_FOUND:
                return
            else:
                raise err

        suggestions = suggestions_response.suggestions
        for suggestion in suggestions:
            product = products[suggestion.id]
            if suggestion.bid_information is not None:
                product.minSuggestedBid = suggestion.bid_information.lowest_bid
                product.maxSuggestedBid = suggestion.bid_information.highest_bid
            else:
                product.minSuggestedBid = 0.00
                product.maxSuggestedBid = 0.00

    async def get_products_by_brand(
            self,
            advertisers: List[CachedAdvertiser],
            offset: int = None,
            limit: int = None,
            agency_id: str = None,
            campaign_type: InternalCampaignType = InternalCampaignType.PLA,
            last_sold_within_days: int = UPCS_LAST_SOLD_WITHIN_DAYS,
            koddi_advertiser_id: int = None) -> Tuple[List[Product], bool]:

        if koddi_advertiser_id is None:
            if agency_id is None:
                koddi_advertiser_id = await self.advertiser_service.get_koddi_advertiser_id(advertisers[0].brandId)
            else:
                koddi_advertiser_id = await self.advertiser_service.get_koddi_advertiser_id_for_agency(
                    advertisers[0].brandId, agency_id)

        products, upcs, has_more = await self.__fetch_and_cache_products(
            advertisers=advertisers,
            last_sold_within_days=last_sold_within_days,
            offset=offset,
            limit=limit)

        if len(upcs) > 0:
            self.__set_product_prices_by_ids(upcs, products)

            await self.__set_product_bids(koddi_advertiser_id, upcs, products, campaign_type)


        # Return the products from the dictionary as a list
        return list(products.values()), has_more

    async def get_products_by_upcs(
            self,
            upcs: List[str],
            advertiser_names: List[str] = None,
    ) -> dict[str, ProductManagerProduct]:
        response = await self.product_gateway.get_products_by_upcs(upcs, advertiser_names)
        valid_products = {product.upc: product for product in response.data.validProducts}
        return valid_products