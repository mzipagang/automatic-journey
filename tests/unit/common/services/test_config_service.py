from unittest import TestCase

from app.common.services.config_service import ConfigService, Config


class TestConfigService(TestCase):
    def test_init__should_contain_migrated_config(self):
        subject: Config = ConfigService().get_current_config()

        self.assertIsInstance(subject, Config)
        self.assertIsNotNone(subject.general_cache_config)
        self.assertIsNotNone(subject.backoff_wait_rate_limit_config)
        self.assertIsNotNone(subject.general_cid_rate_limit_config)
        self.assertIsNotNone(subject.locked_activation_fetch_retry_config)
        self.assertIsNotNone(subject.unpublished_campaign_fetch_retry_config)
        self.assertIsNotNone(subject.update_campaign_lock_config)
        self.assertIsNotNone(subject.update_campaign_lock_config)
