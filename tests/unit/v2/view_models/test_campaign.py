import unittest
from unittest import TestCase

from app.common.model.campaign_types import InternalCampaignType, CampaignType
from app.v2.view_models import Campaign


class TestCampaign(TestCase):
    def test_campaign__campaign_type_validator(self):
        pla_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="pla"
        )
        toa_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="toa"
        )
        carousel_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="carousel"
        )
        invalid_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="invalid"
        )

        self.assertEqual(InternalCampaignType.PLA, pla_campaign.campaignType)
        self.assertEqual(InternalCampaignType.TOA, toa_campaign.campaignType)
        self.assertEqual(InternalCampaignType.CAROUSEL, carousel_campaign.campaignType)
        self.assertEqual(InternalCampaignType.UNSUPPORTED, invalid_campaign.campaignType)

    def test_campaign__campaign_type_serializer(self):
        pla_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="pla"
        ).model_dump()
        toa_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="toa"
        ).model_dump()
        carousel_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="carousel"
        ).model_dump()
        invalid_campaign = Campaign(
            id=1234,
            accountId=1234,
            advertiserIds=[1234],
            campaignType="invalid"
        ).model_dump()

        self.assertEqual(
            CampaignType.PLA,
            pla_campaign.get("campaignType")
        )
        self.assertEqual(
            CampaignType.TOA,
            toa_campaign.get("campaignType")
        )
        self.assertEqual(
            CampaignType.CAROUSEL,
            carousel_campaign.get("campaignType")
        )
        self.assertIsNone(invalid_campaign.get("campaignType"))