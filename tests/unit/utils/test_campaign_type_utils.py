from unittest import TestCase

import pytest

from app.common.model.shared import BidManagerCampaignType, CampaignType, InternalCampaignType
from app.common.utils.campaign_type_utils import (
    bid_type_matches_campaign_type,
    is_carousel_campaign,
    is_pla_campaign,
    to_bid_manager_campaign_type,
    to_campaign_service_campaign_type,
    to_external_campaign_type,
)


class TestCampaignTypeUtils(TestCase):
    def test_to_bid_manager_campaign_type(self):
        self.assertEqual(to_bid_manager_campaign_type("CAROUSEL"), BidManagerCampaignType.CAROUSEL)
        self.assertEqual(to_bid_manager_campaign_type("PPC"), BidManagerCampaignType.CAROUSEL)
        self.assertEqual(to_bid_manager_campaign_type("PLA"), BidManagerCampaignType.PLA)
        self.assertEqual(to_bid_manager_campaign_type("TOA"), BidManagerCampaignType.TOA)
        self.assertEqual(to_bid_manager_campaign_type("PROMOTED_PRODUCTS_CAROUSEL"), BidManagerCampaignType.CAROUSEL)
        self.assertEqual(to_bid_manager_campaign_type("Promoted_Products_Carousel"), BidManagerCampaignType.CAROUSEL)
        self.assertEqual(to_bid_manager_campaign_type("ppc"), BidManagerCampaignType.CAROUSEL)
        self.assertTrue(isinstance(to_bid_manager_campaign_type("ppc"), BidManagerCampaignType))
        
        with pytest.raises(ValueError, match="'OTHER' is not a valid InternalCampaignType"):
            to_bid_manager_campaign_type("OTHER")

    def test_is_carousel_campaign(self):
        self.assertTrue(is_carousel_campaign(InternalCampaignType.CAROUSEL))
        self.assertFalse(is_carousel_campaign(InternalCampaignType.PLA))
        self.assertFalse(is_carousel_campaign(InternalCampaignType.TOA))
        self.assertTrue(is_carousel_campaign(InternalCampaignType.CS_CAROUSEL))
        self.assertTrue(is_carousel_campaign(InternalCampaignType.BM_CAROUSEL))
        self.assertTrue(is_carousel_campaign(InternalCampaignType.IN_CAROUSEL))

    def test_is_pla_campaign(self):
        self.assertFalse(is_pla_campaign(CampaignType.CAROUSEL))
        self.assertTrue(is_pla_campaign(CampaignType.PLA))
        self.assertFalse(is_pla_campaign(CampaignType.TOA))


    def test_bid_type_matches_campaign_type(self):
        self.assertTrue(bid_type_matches_campaign_type("PPC", "CAROUSEL"))
        self.assertTrue(bid_type_matches_campaign_type("TOA", "TOA"))
        self.assertFalse(bid_type_matches_campaign_type("PLA", "TOA"))
        self.assertFalse(bid_type_matches_campaign_type("TOA", "PLA"))
        self.assertTrue(bid_type_matches_campaign_type("PLA", "PLA"))
        with pytest.raises(ValueError, match="'OTHER' is not a valid InternalCampaignType"):
            bid_type_matches_campaign_type("PLA", "OTHER")

        with pytest.raises(ValueError, match="'OTHER' is not a valid BidManagerCampaignType"):
            bid_type_matches_campaign_type("OTHER", "PLA")

    def test_to_campaign_service_campaign_type(self):
        self.assertEqual(to_campaign_service_campaign_type(CampaignType.CAROUSEL), InternalCampaignType.CS_CAROUSEL)
        self.assertEqual(to_campaign_service_campaign_type(CampaignType.PLA), InternalCampaignType.PLA)
        self.assertEqual(to_campaign_service_campaign_type(CampaignType.TOA), InternalCampaignType.TOA)
        self.assertTrue(isinstance(to_campaign_service_campaign_type(CampaignType.PLA), InternalCampaignType))

    def test_to_external_campaign_type(self):
        self.assertEqual(to_external_campaign_type("PROMOTED_PRODUCTS_CAROUSEL"), CampaignType.CAROUSEL)
        self.assertEqual(to_external_campaign_type("Promoted_Products_Carousel"), CampaignType.CAROUSEL)
        self.assertEqual(to_external_campaign_type("ppc"), CampaignType.CAROUSEL)
        self.assertEqual(to_external_campaign_type("PLA"), CampaignType.PLA)
        self.assertEqual(to_external_campaign_type("TOA"), CampaignType.TOA)
        self.assertEqual(to_external_campaign_type("pla"), CampaignType.PLA)
        self.assertEqual(to_external_campaign_type("carousel"), CampaignType.CAROUSEL)
        self.assertTrue(isinstance(to_external_campaign_type("pla"), CampaignType))
        with pytest.raises(ValueError, match="'OTHER' is not a valid InternalCampaignType"):
            to_external_campaign_type("OTHER")
