from unittest import TestCase
from unittest.mock import patch, MagicMock

from app.common.utils.http_request import get_consumer_source


class TestHttpRequest(TestCase):
    def test_get_consumer_source__pacvue__should_succeed(self):
        self.__get_consumer_assertions(consumer='Pacvue API Consumer', expected='API_PARTNER_PACVUE')

    def test_get_consumer_source__pacvue_sandbox__should_succeed(self):
        self.__get_consumer_assertions(consumer='Pacvue API Sandbox Consumer', expected='API_PARTNER_PACVUE')

    def test_get_consumer_source__skai__should_succeed(self):
        self.__get_consumer_assertions(consumer='Skai API Consumer', expected='API_PARTNER_SKAI')

    def test_get_consumer_source__skai_sandbox__should_succeed(self):
        self.__get_consumer_assertions(consumer='Skai API Sandbox Consumer', expected='API_PARTNER_SKAI')

    def test_get_consumer_source__commerceiq__should_succeed(self):
        self.__get_consumer_assertions(consumer='CommerceIQ API Consumer', expected='API_PARTNER_CIQ')

    def test_get_consumer_source__commerceiq_sandbox__should_succeed(self):
        self.__get_consumer_assertions(consumer='CommerceIQ API Sandbox Consumer', expected='API_PARTNER_CIQ')

    def test_get_consumer_source__pepsi__should_succeed(self):
        self.__get_consumer_assertions(consumer='Pepsi API Consumer', expected='API_PARTNER_PEPSI')

    def test_get_consumer_source__pepsi_sandbox__should_succeed(self):
        self.__get_consumer_assertions(consumer='Pepsi API Sandbox Consumer', expected='API_PARTNER_PEPSI')

    def test_get_consumer_source__flywheel__should_succeed(self):
        self.__get_consumer_assertions(consumer='Flywheel API Consumer', expected='API_PARTNER_FLYWHEEL')

    def test_get_consumer_source__flywheel_sandbox__should_succeed(self):
        self.__get_consumer_assertions(consumer='Flywheel API Sandbox Consumer', expected='API_PARTNER_FLYWHEEL')

    @patch('logging.Logger.warning')
    def test_get_consumer_source__unknown__should_succeed(self, mock_warning_logger: MagicMock):
        self.__get_consumer_assertions(consumer='Unknown API Consumer', expected='API_PARTNER__UNRECOGNIZED_CONSUMER')
        mock_warning_logger.assert_called_once_with(
            "%s does not match a known entity, defaulting to PARTNER_API__UNRECOGNIZED_CONSUMER",
            'X-Consumer-Username',
            extra={
                'monitored_transaction': 'GET-CONSUMER-SOURCE-DEFAULT',
                'consumer': 'Unknown API Consumer',
                'default_used': 'API_PARTNER__UNRECOGNIZED_CONSUMER'
            }
        )

    @patch('logging.Logger.warning')
    def test_get_consumer_source__none__should_succeed(self, mock_warning_logger: MagicMock):
        self.__get_consumer_assertions(consumer=None, expected='API_PARTNER__NO_CONSUMER')
        mock_warning_logger.assert_called_once_with(
            "%s is not set in the headers, defaulting to API_PARTNER__NO_CONSUMER",
            'X-Consumer-Username',
            extra={
                'monitored_transaction': 'GET-CONSUMER-SOURCE-DEFAULT',
                'consumer': None,
                'default_used': 'API_PARTNER__NO_CONSUMER'
            }
        )

    def __get_consumer_assertions(self, consumer, expected):
        # Act
        result = get_consumer_source(consumer)

        # Assert
        self.assertEqual(expected, result)
