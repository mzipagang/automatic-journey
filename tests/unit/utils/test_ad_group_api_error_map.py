import unittest

from app.common.utils.ad_group_api_error_map import AdGroupApiErrorMap


class TestAdGroupApiErrorMap(unittest.TestCase):
    def test_get_error_message__key_found__should_succeed(self):
        # Arrange
        error_message = 'activation is locked while publishing'

        # Act
        result = AdGroupApiErrorMap.get_error_message(error_message)

        # Assert
        self.assertEqual(result, 'Ad Group is locked while publishing')

    def test_get_error_message__key_not_found__should_log_critical(self):
        # Arrange
        error_message = 'unknown error'

        # Act
        with self.assertLogs() as cm:
            AdGroupApiErrorMap.get_error_message(error_message)

        # Assert
        self.assertRegex(cm.output[0], '.*Error message not found in error map: unknown error.*')
