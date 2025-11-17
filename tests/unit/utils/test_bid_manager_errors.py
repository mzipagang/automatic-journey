import unittest

from app.common.utils.bid_manager_errors import is_false_error, NO_KEYWORDS_FOUND


class TestBidManagerErrors(unittest.TestCase):
    def test_is_false_error_none(self):
        self.assertEqual(False, is_false_error(None))

    def test_is_false_error_true(self):
        self.assertEqual(True, is_false_error(NO_KEYWORDS_FOUND))

    def test_is_false_error_false(self):
        self.assertEqual(False, is_false_error("Not a false error"))
        