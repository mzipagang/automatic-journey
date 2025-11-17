from logging import Logger
from typing import Callable

from app.common.model.advertiser import CachedAdvertiser
from app.common.model.downstream.campaign_activation_service import CASCampaign


class CampaignFunctors:
    @staticmethod
    def campaign_has_brands(logger: Logger) -> Callable:
        def inner(campaign: CASCampaign) -> bool:
            if (
                CampaignFunctors._campaign_has_brand_keys(campaign)
                and campaign.primaryAccount.brands
            ):
                return True
            logger.warning(f"campaign {campaign.id} has no brands")
            return False
        return inner

    @staticmethod
    def campaign_has_correct_advertiser_brand_id(logger: Logger, advertiser: CachedAdvertiser) -> Callable:
        def inner(campaign: CASCampaign) -> bool:
            if (CampaignFunctors._campaign_has_brand_keys(campaign)
                    and advertiser.brandId in campaign.primaryAccount.brands):
                return True
            logger.warning(f"campaign {campaign.id} has incorrect advertiser brand id")
            return False
        return inner

    @staticmethod
    def _campaign_has_brand_keys(campaign: CASCampaign) -> bool:
        return hasattr(campaign, 'primaryAccount') and hasattr(campaign.primaryAccount, 'brands')
