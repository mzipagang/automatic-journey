from datetime import datetime as dt, timedelta

import unittest

import pytest

from app.common.utils.date_utils import is_valid_startdate, add_years
from unittest.mock import patch
from zoneinfo import ZoneInfo
from datetime import datetime

from app.common.utils.date_utils import is_not_valid_time_frame_create_campaign_today

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


class TestIsNotValidTimeFrameCreateCampaignToday(unittest.TestCase):
    class DummyRequest:
        def __init__(self, start_date: str):
            self._json = {"startDate": start_date}

    class DummyDateTime(datetime):
        fixed_dt = datetime(2025, 1, 15, 20, 0, 0, tzinfo=ZoneInfo("America/New_York"))

        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return cls.fixed_dt.astimezone(tz)
            return cls.fixed_dt

    @pytest.mark.skip('Need to fix this test')
    def test_returns_true_within_cutoff_window(self):
        start_date = self.DummyDateTime.fixed_dt.date().strftime("%Y-%m-%d")
        req = self.DummyRequest(start_date)
        with patch("app.common.utils.date_utils.datetime", self.DummyDateTime):
            self.assertTrue(is_not_valid_time_frame_create_campaign_today(req))

    def test_returns_false_before_cutoff(self):
        class EarlyDateTime(self.DummyDateTime):
            fixed_dt = datetime(2025, 1, 15, 19, 59, 59, tzinfo=ZoneInfo("America/New_York"))

        start_date = EarlyDateTime.fixed_dt.date().strftime("%Y/%m/%d")
        req = self.DummyRequest(start_date)
        with patch("app.common.utils.date_utils.datetime", EarlyDateTime):
            self.assertFalse(is_not_valid_time_frame_create_campaign_today(req))

    def test_returns_false_different_start_date(self):
        start_date = "2025/01/16"
        req = self.DummyRequest(start_date)
        with patch("app.common.utils.date_utils.datetime", self.DummyDateTime):
            self.assertFalse(is_not_valid_time_frame_create_campaign_today(req))