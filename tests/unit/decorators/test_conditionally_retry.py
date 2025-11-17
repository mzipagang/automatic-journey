from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from app.common.decorators.decorators import conditionally_retry


class TestConditionallyRetry(TestCase):
    __mock_retry_predicate: MagicMock
    __mock_func: MagicMock
    __mock_logger: MagicMock

    def setUp(self):
        self.__mock_retry_predicate = MagicMock()
        self.__mock_func = MagicMock()
        self.__mock_logger = MagicMock()

    @patch(
        'app.common.services.harness_service.HarnessService.fetch_multivariate_flag',
        return_value={'enabled': True, 'pause_seconds': 1, 'max_retries': 3})
    def test__harness_flag_on__should_call(
            self,
            mock_fetch_multivariate_flag: MagicMock):

        self.__mock_func.side_effect = [Exception('error'), 'success']

        @conditionally_retry(
            flag_name='flag_name',
            logger=self.__mock_logger,
            retry_predicate=self.__mock_retry_predicate)
        def test_func():
            return self.__mock_func(a=1, b=2, c=3)

        test_func()

        self.__mock_func.assert_has_calls([call(a=1, b=2, c=3), call(a=1, b=2, c=3)])

        self.assertEqual(2, self.__mock_func.call_count)
        self.assertEqual(2, self.__mock_logger.log.call_count)

        mock_fetch_multivariate_flag.assert_called_once_with(flag_name='flag_name', target_id='default')

    @patch(
        'app.common.services.harness_service.HarnessService.fetch_multivariate_flag',
        return_value={'enabled': False})
    def test__harness_flag_off__should_call(
            self,
            mock_fetch_multivariate_flag: MagicMock):

        self.__mock_func.side_effect = [Exception('error'), 'success']

        @conditionally_retry(
            flag_name='flag_name',
            logger=self.__mock_logger,
            retry_predicate=self.__mock_retry_predicate)
        def test_func():
            return self.__mock_func()

        with self.assertRaises(Exception) as context:
            test_func()

        self.assertEqual('error', str(context.exception))
        self.assertEqual(1, self.__mock_func.call_count)

        self.__mock_logger.log.assert_not_called()

        mock_fetch_multivariate_flag.assert_called_once_with(flag_name='flag_name', target_id='default')

    @patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag')
    def test_harness_flag_on__should_eval_correct_config_values(self, mock_fetch_multivariate_flag: MagicMock):
        self.__mock_func.return_value = 'success'

        mock_flag: MagicMock = MagicMock()
        mock_flag.get.side_effect = [True, 1, 3]
        mock_fetch_multivariate_flag.return_value = mock_flag

        @conditionally_retry(
            flag_name='flag_name',
            logger=self.__mock_logger,
            retry_predicate=self.__mock_retry_predicate)
        def test_func():
            return self.__mock_func()

        test_func()

        mock_fetch_multivariate_flag.assert_called_once_with(flag_name='flag_name', target_id='default')
        mock_flag.get.assert_has_calls([
            call('enabled'),
            call('pause_seconds'),
            call('max_retries')
        ])


