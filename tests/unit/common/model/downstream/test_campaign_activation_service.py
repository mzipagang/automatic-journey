from unittest import TestCase

from app.common.model.downstream.campaign_activation_service import CASCampaign, ExternalId


class TestCampaignActivationService(TestCase):
    def test_get_koddi_advertiser_id__id_present__should_succeed(self):
        subject: CASCampaign = CASCampaign(externalIDs=[
            ExternalId(id=1, partner="KODDI_ADVERTISER_ID"),
            ExternalId(id=1, partner="KODDI_CAMPAIGN_ID")
        ])

        self.assertEqual(subject.get_koddi_advertiser_id(), 1)

    def test_get_koddi_advertiser_id__id_value_not_set__should_return_none(self):
        subject: CASCampaign = CASCampaign(externalIDs=[
            ExternalId(partner="KODDI_ADVERTISER_ID"),
            ExternalId(id=1, partner="KODDI_CAMPAIGN_ID")
        ])

        self.assertIsNone(subject.get_koddi_advertiser_id())

    def test_get_koddi_advertiser_id__id_not_present__should_return_none(self):
        subject: CASCampaign = CASCampaign(externalIDs=[
            ExternalId(id=1, partner="KODDI_CAMPAIGN_ID")
        ])

        self.assertIsNone(subject.get_koddi_advertiser_id())

    def test_get_koddi_advertiser_id__external_ids_empty_list__should_return_none(self):
        subject: CASCampaign = CASCampaign(externalIDs=[])

        self.assertIsNone(subject.get_koddi_advertiser_id())

    def test_get_koddi_advertiser_id__external_ids_missing__should_return_none(self):
        subject: CASCampaign = CASCampaign()

        self.assertIsNone(subject.get_koddi_advertiser_id())
