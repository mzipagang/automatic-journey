from unittest import TestCase

from app.common.exceptions.campaign_exceptions import CampaignNotPublishedException
from app.common.retry.predicates import campaign_is_not_published


class TestRetryPredicates(TestCase):
    def test_campaign_is_not_published__cnp_exception__should_return_true(self):
        result = campaign_is_not_published(CampaignNotPublishedException("123"))

        self.assertTrue(result)

    def test_campaign_is_not_published__other_exception__should_return_false(self):
        result = campaign_is_not_published(Exception("Some other exception"))

        self.assertFalse(result)
