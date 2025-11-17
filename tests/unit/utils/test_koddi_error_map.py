import unittest

import pytest

from app.v2.utils.koddi_error_map import KoddiErrorMap


class TestKoddiErrorMap(unittest.TestCase):
    def test_remap_message_in_map(self):
        original_message = "custom budgets cannot be always on"
        expected_message = "Please select a daily, weekly or monthly budget for always on campaigns."
        self.assertEqual(KoddiErrorMap.remap(original_message), expected_message)

    def test_remap_message_not_in_map(self):
        original_message = "test message"
        expected_message = "test message"
        self.assertEqual(KoddiErrorMap.remap(original_message), expected_message)

    def test_remap_message_not_valid(self):
        original_message = {"a": "b"}
        expected_message = "Cannot remap message of type: {type(original_message)}"

        with pytest.raises(TypeError) as error:
            KoddiErrorMap.remap(original_message)

        assert str(error.value) == expected_message
        