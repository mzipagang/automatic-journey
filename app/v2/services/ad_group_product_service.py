from typing import Dict, Any, List, Tuple

from fastapi import Depends

from app.common.configuration.constants import UPCS_LAST_SOLD_WITHIN_DAYS
from app.common.gateways.activation_gateway import ActivationGateway
from app.common.gateways.campaign_service_gateway import CampaignServiceGateway
from app.common.model.advertiser import CachedAdvertiser
from app.common.model.downstream.campaign_activation_service import CASCampaign
from app.common.model.downstream.campaign_service import CampaignResponse
from app.common.model.shared import Meta, Page
from app.common.model.product import ProductResponse, Product
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.lookup_service import LookupService
from app.common.services.product_service import ProductService
from app.v2.model.downstream.activation_service import ActivationResponseV2, ActivationResponse


class AdGroupProductService:

    def __init__(
            self,
            lookup: LookupService = Depends(LookupService),
            activation_gateway: ActivationGateway = Depends(ActivationGateway),
            campaign_gateway: CampaignServiceGateway = Depends(CampaignServiceGateway),
            advertiser_service: AdvertiserService = Depends(AdvertiserService),
            product_service: ProductService = Depends(ProductService)) -> None:
        self.__lookup = lookup
        self.__activation_gateway = activation_gateway
        self.__campaign_gateway = campaign_gateway
        self.__advertiser_service = advertiser_service
        self.__product_service = product_service

    async def get_products_by_ad_group(
            self,
            current_user: Dict[str, Any],
            ad_group_id: int,
            offset: int, page_size: int) -> ProductResponse:

        activation_id: str = await self.__lookup.get_adgroup_long_id_by_short_id(ad_group_id)
        activation_response: ActivationResponseV2[ActivationResponse] = \
            await self.__activation_gateway.get_activation_by_id(activation_id)

        campaign_long_id: str = activation_response.data.campaign_id
        campaign_data: CampaignResponse = await self.__campaign_gateway.get_campaign(campaign_long_id)

        campaign: CASCampaign = campaign_data.publishedChanges if campaign_data.publishedChanges \
            else campaign_data.unpublishedChanges

        koddi_advertiser_id: int = campaign.get_koddi_advertiser_id()
        brand_ids: List[str] = campaign.primaryAccount.brands

        advertiser_ids: List[int] = await self.__lookup.get_advertiser_short_id_by_long_id_batch(brand_ids)
        advertisers: List[CachedAdvertiser] = await self.__advertiser_service.get_advertisers_by_numeric_ids(
            advertiser_ids)

        agency_id: str = current_user.get('works_for', {}).get('clientId') if current_user.get('is_agency') else None

        try:
            last_sold_within_days = int(
                activation_response.included.configuration_by_activation[activation_id]
                .biddableEntities.last_sold_within_days
            )
        except (KeyError, AttributeError, TypeError, ValueError):
            last_sold_within_days = UPCS_LAST_SOLD_WITHIN_DAYS

        response: Tuple[List[Product], bool] = await self.__product_service.get_products_by_brand(
            advertisers=advertisers,
            offset=offset,
            limit=page_size,
            agency_id=agency_id,
            last_sold_within_days=last_sold_within_days,
            koddi_advertiser_id=koddi_advertiser_id)

        return ProductResponse(
            data=response[0],
            meta=Meta(
                page=Page(
                    offset=offset,
                    size=page_size,
                    hasMore=response[1])))
