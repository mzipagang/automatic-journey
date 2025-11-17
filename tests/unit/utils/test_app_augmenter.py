from unittest import TestCase
from unittest.mock import MagicMock, patch

from app.common.middleware.deployed_version_middleware import DeployedVersionMiddleware
from app.common.middleware.user_info_middleware import UserInfoMiddleware
from app.common.utils.app_augmenter import AppAugmenter


class TestAppAugmenter(TestCase):
    @patch('os.getenv')
    def test_add_app_middleware__should_add_app_middleware(self, mock_getenv):
        mock_app = MagicMock()
        mock_getenv.return_value = 'service.version=2.0.83'

        AppAugmenter.add_app_middleware(mock_app)

        mock_app.add_middleware.assert_any_call(UserInfoMiddleware)
        mock_app.add_middleware.assert_any_call(DeployedVersionMiddleware)

    @patch('app.common.utils.filtered_logger.get_logger')
    def test_monitoring_instrument_app__should_succeed(
            self,
            mock_get_logger: MagicMock):
        mock_app = MagicMock()
        mock_observer = MagicMock()

        AppAugmenter.monitoring_instrument_app(mock_app, mock_observer)

        mock_observer.instrument_logging.assert_called()
        mock_observer.instrument_tracing.assert_called()
        mock_get_logger.assert_called()
