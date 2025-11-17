import unittest

from app.common.model.campaign_types import InternalCampaignType, CASCampaignType
from app.v2.model.downstream.activation_service import ChannelConfig


class TestActivationService(unittest.TestCase):
    def test_channel_config_validation(self):
        pla_config = ChannelConfig(type="pla", version="1")
        toa_config = ChannelConfig(type="toa", version="1")
        carousel_config = ChannelConfig(type="Promoted_Products_Carousel", version="1")
        unsupported_config = ChannelConfig(type="invalid", version="1")

        self.assertEqual(InternalCampaignType.PLA, pla_config.type)
        self.assertEqual(InternalCampaignType.TOA, toa_config.type)
        self.assertEqual(InternalCampaignType.CAROUSEL, carousel_config.type)
        self.assertEqual(InternalCampaignType.UNSUPPORTED, unsupported_config.type)

    def test_channel_config_serialization(self):
        pla_config = ChannelConfig(
            type=InternalCampaignType.PLA,
            version="1"
        ).model_dump()
        toa_config = ChannelConfig(
            type=InternalCampaignType.TOA,
            version="1"
        ).model_dump()
        carousel_config = ChannelConfig(
            type=InternalCampaignType.CAROUSEL,
            version="1"
        ).model_dump()
        unsupported_config = ChannelConfig(
            type=InternalCampaignType.UNSUPPORTED,
            version="1"
        ).model_dump()

        self.assertEqual(CASCampaignType.PLA, pla_config.get("type"))
        self.assertEqual(CASCampaignType.TOA, toa_config.get("type"))
        self.assertEqual(CASCampaignType.CAROUSEL, carousel_config.get("type"))
        self.assertEqual(CASCampaignType.UNSUPPORTED, unsupported_config.get("type"))
