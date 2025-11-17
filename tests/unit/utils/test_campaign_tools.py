import unittest

from app.v2.utils.campaign_tools import is_valid_campaign_type


class TestCampaignTypeValidation(unittest.TestCase):

    def test_valid_campaign_type_returns_true(self):
        self.assertTrue(is_valid_campaign_type("PLA"))

    def test_invalid_campaign_type_returns_false(self):
        self.assertFalse(is_valid_campaign_type("invalid campaign type"))

    def test_campaign_type_with_whitespace_returns_true(self):
        self.assertTrue(is_valid_campaign_type(" PLA "))

    def test_empty_campaign_type_returns_false(self):
        self.assertFalse(is_valid_campaign_type(""))

    def test_campaign_type_with_only_whitespace_returns_false(self):
        self.assertFalse(is_valid_campaign_type("   "))