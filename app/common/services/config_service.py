from functools import lru_cache
from pydantic_settings import BaseSettings

from app.common.model.configuration import CacheConfig, LockConfig, RetryConfig, RateLimitConfig

class _Settings(BaseSettings):
    # Environment variables in lower case go here for easy access
    env: str = ""
    redis_host: str = ""
    redis_port: int = ""
    redis_db: int = ""
    redis_primary_access_key: str = ""
    redis_ssl: bool = ""
    redis_socket_timeout: int = 30
    redis_socket_connect_timeout: int = 10
    redis_health_check_interval: int = 30
    harness_api_key: str = ""
    api_validator_client_id: str = ""
    api_validator_client_secret: str = ""
    root_cert_pem_path: str = ""


@lru_cache()
def _get_settings():
    return _Settings()


class Config:
    base_api_url: str
    base_internal_api_url: str
    base_koddi_url: str
    product_id: str
    pte_target_id: str
    # Any variables from _Settings go here and must match exact
    env: str
    redis_host: str
    redis_port: int
    redis_db: int
    redis_primary_access_key: str
    redis_ssl: bool
    redis_socket_timeout: int
    redis_socket_connect_timeout: int
    redis_health_check_interval: int
    http_client_timeout_seconds: int
    harness_api_key: str
    root_cert_pem_path: str
    general_cache_config: CacheConfig = CacheConfig(ttl=300)
    backoff_wait_rate_limit_config: RetryConfig = RetryConfig(pause_seconds=15, max_retries=15)
    general_cid_rate_limit_config: RateLimitConfig = RateLimitConfig(
        requests_per_minute=120, rate_limit_prefix='kap_api_rate_limit_v3')
    locked_activation_fetch_retry_config: RetryConfig = RetryConfig(
        pause_seconds=5, max_retries=5, expire_seconds=60)
    unpublished_campaign_fetch_retry_config: RetryConfig = RetryConfig(
        pause_seconds=3, max_retries=3, expire_seconds=60)
    update_activation_lock_config: LockConfig = LockConfig(
        lock_prefix='activation_lock_v3', expire_seconds=240)
    update_campaign_lock_config: LockConfig = LockConfig(
        lock_prefix='campaign_lock_v2', expire_seconds=240)


    def __init__(self,
                 base_api_url,
                 base_koddi_url,
                 product_id,
                 pte_target_id,
                 http_client_timeout_seconds: int = 120,
                 base_internal_api_url: str = None):
        self.base_api_url = base_api_url
        self.base_koddi_url = base_koddi_url
        self.product_id = product_id
        self.pte_target_id = pte_target_id
        self.http_client_timeout_seconds = http_client_timeout_seconds
        self.base_internal_api_url = base_internal_api_url



class ConfigService:
    _self = None
    _settings: _Settings
    _config_env_map = {
        'local': Config(
            base_api_url='https://api-dev.8451.com',
            base_internal_api_url='https://api-internal-dev.8451.com',
            base_koddi_url='https://kroger.uat.az.koddi.io',
            product_id='38508d58-0168-4b8b-8f3c-a18755946fc8',
            pte_target_id='S-1-274987414-3557449386-1015311416-1200660600-636360092-939006429',
            http_client_timeout_seconds=5
        ),
        'dev': Config(
            base_api_url='https://api-dev.8451.com',
            base_internal_api_url='https://api-internal-dev.8451.com',
            base_koddi_url='https://kroger.uat.az.koddi.io',
            product_id='38508d58-0168-4b8b-8f3c-a18755946fc8',
            pte_target_id='S-1-274987414-3557449386-1015311416-1200660600-636360092-939006429',
            http_client_timeout_seconds=20
        ),
        'tst': Config(
            base_api_url='https://api-tst.8451.com',
            base_internal_api_url='https://api-internal-tst.8451.com',
            base_koddi_url='https://kroger.uat.az.koddi.io',
            product_id='38508d58-0168-4b8b-8f3c-a18755946fc8',
            pte_target_id='CHANGEME',
            http_client_timeout_seconds=20
        ),
        'stg': Config(
            base_api_url='https://api-stg.8451.com',
            base_internal_api_url='https://api-internal-stg.8451.com',
            base_koddi_url='https://kroger.uat.az.koddi.io',
            product_id='38508d58-0168-4b8b-8f3c-a18755946fc8',
            pte_target_id='CHANGEME',
            http_client_timeout_seconds=120
        ),
        'prd': Config(
            base_api_url='https://api.8451.com',
            base_internal_api_url='https://api-internal.8451.com',
            base_koddi_url='https://kroger.prod.az.koddi.io',
            product_id='38508d58-0168-4b8b-8f3c-a18755946fc8',
            pte_target_id='CHANGEME',
            http_client_timeout_seconds=120
        )
    }

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
            cls._self._settings = _get_settings()
        return cls._self

    def clear_config(self):
        self._self = None

    def get_current_config(self) -> Config:
        current_config = self._config_env_map[self._settings.env]
        current_config.__dict__.update(self._settings.__dict__)
        return current_config
