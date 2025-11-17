from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from app.common.decorators.fixed_interval_retry import fixed_interval_retry
from app.common.model.configuration import RetryConfig
from app.common.services.config_service import Config


class TestFixedIntervalRetry(TestCase):
    __mock_retry_predicate: MagicMock
    __mock_func: MagicMock
    __mock_logger: MagicMock

    def setUp(self):
        self.__mock_retry_predicate = MagicMock()
        self.__mock_func = MagicMock()
        self.__mock_logger = MagicMock()

    @patch('app.common.services.config_service.ConfigService.get_current_config')
    def test__retry_config__should_call(
            self,
            mock_get_current_config):
        config = Config("", "", "", "")
        config.backoff_wait_rate_limit_config = RetryConfig(pause_seconds=1, max_retries=3)
        mock_get_current_config.return_value = config

        self.__mock_func.side_effect = [Exception('error'), 'success']

        @fixed_interval_retry(
            logger=self.__mock_logger,
            retry_predicate=self.__mock_retry_predicate)
        def test_func():
            return self.__mock_func(a=1, b=2, c=3)

        test_func()

        self.__mock_func.assert_has_calls([call(a=1, b=2, c=3), call(a=1, b=2, c=3)])

        self.assertEqual(2, self.__mock_func.call_count)
        self.assertEqual(2, self.__mock_logger.log.call_count)

        mock_get_current_config.assert_called_once()
