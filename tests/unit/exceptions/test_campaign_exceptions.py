from unittest import TestCase

from app.common.exceptions.campaign_exceptions import CampaignNotPublishedException


class TestCampaignExceptions(TestCase):
    def test_campaign_not_published_exception(self):
        campaign_id = "test_campaign_id"

        exception = CampaignNotPublishedException(campaign_id=campaign_id)

        self.assertIsInstance(exception, CampaignNotPublishedException)
        self.assertEqual(campaign_id, exception.campaign_id)
        self.assertEqual(f"Campaign with ID {campaign_id} is not yet published.", str(exception))
