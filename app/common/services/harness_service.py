import logging

from featureflags.client import CfClient
from featureflags.config import Config
from featureflags.evaluations.auth_target import Target

from app.common.services.config_service import ConfigService
from app.common.utils import filtered_logger

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = filtered_logger.get_logger(__name__)


class HarnessService:
    config_service: ConfigService
    client: CfClient

    _self = None

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)

            cls._self.config_service = ConfigService()
            cls._self.config = cls._self.config_service.get_current_config()
            # Create a Feature Flag Client

            if cls._self.config.root_cert_pem_path is None:
                cls._self.client = CfClient(cls._self.config.harness_api_key)
            else:
                pem_file_path = cls._self.config.root_cert_pem_path
                cls._self.client = CfClient(
                    cls._self.config.harness_api_key,
                    config=Config(tls_trusted_cas_file=pem_file_path))
            # Block the thread until all flag configuration has been loaded into the cache.
            cls._self.client.wait_for_initialization()
        return cls._self

    def is_harness_flag_on(self, flag_name: str, target_id: str) -> bool:
        # Create a target (different targets can get different results based on rules.
        # This include a custom attribute 'location')
        target = Target(
            identifier=target_id,
        )

        return self.client.bool_variation(flag_name, target, False)

    def fetch_multivariate_flag(self, flag_name: str, target_id: str) -> dict:
        target = Target(
            identifier=target_id,
        )

        return self.client.json_variation(flag_name, target, {"enabled": False, "ttl": 0})

    def close(self) -> None:
        self.client.close()
