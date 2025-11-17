from datetime import datetime as dt, timedelta

import unittest
from app.common.utils.date_utils import is_valid_startdate, add_years


class TestDateUtils(unittest.TestCase):

    def test_is_valid_start_date__valid__should_succeed(self):
        right_now = dt.now()
        tomorrow = right_now + timedelta(days=1)
        campaign_date = tomorrow
        actual = is_valid_startdate(campaign_date.strftime('%Y-%m-%d'))

        self.assertTrue(actual)

    @unittest.skip('Need to fix this test')
    def test_is_valid_start_date__valid__should_fail(self):
        yesterday = dt.now() - timedelta(1)
        campaign_date = yesterday
        actual = is_valid_startdate(campaign_date.strftime('%Y-%m-%d'))

        self.assertFalse(actual)

    def test_is_valid_start_date__invalid_date_input__should_fail(self):
        campaign_date = ""
        actual = is_valid_startdate(campaign_date)

        self.assertFalse(actual)

    def test_add_years__returns_date_offset_by_years(self):
        self.assertEqual(add_years(dt(2024,1,1), 2), dt(2026,1,1))
        self.assertEqual(add_years(dt(2024, 2, 29), 2), dt(2026, 3, 1))
        self.assertEqual(add_years(dt(2000, 2, 29), 2), dt(2002, 3, 1))
        self.assertEqual(add_years(dt(2025, 2, 28), 2), dt(2027, 2, 28))
