import unittest
from unittest.mock import MagicMock, patch

from app.common.services.harness_service import HarnessService


@patch('app.common.services.harness_service.HarnessService')
class TestHarnessService(unittest.TestCase):
    def test_is_harness_flag_on(self, mock_target):
        # Arrange
        flag_name = 'test_flag'
        target_id = 'test_target_id'
        mock_target.return_value = MagicMock()

        mock_client = MagicMock()
        mock_client.bool_variation.return_value = True

        service = HarnessService()

        # Act
        result = service.is_harness_flag_on(flag_name, target_id)

        # Assert
        self.assertFalse(result)