import logging
from functools import wraps

from tenacity import retry, wait_fixed, stop_after_attempt, before_sleep_log, after_log, retry_if_exception

from app.common.model.configuration import RetryConfig
from app.common.services.config_service import ConfigService

"""
    IMPORTANT: Recommend to use this decorator only on async functions.
    If the wrapped function is synchronous, the retries will block other calls.
"""
def fixed_interval_retry(
        logger: logging.Logger,
        retry_predicate: callable = lambda *args, **kwargs: None,
        config_service: ConfigService = ConfigService()):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_config: RetryConfig = config_service.get_current_config().backoff_wait_rate_limit_config
            pause_seconds = retry_config.pause_seconds
            max_retries = retry_config.max_retries
            retry_decorator = retry(
                reraise=True,
                wait=wait_fixed(pause_seconds),
                stop=stop_after_attempt(max_retries),
                before_sleep=before_sleep_log(logger, logging.INFO),
                after=after_log(logger, logging.INFO),
                retry=retry_if_exception(retry_predicate)
            )
            return retry_decorator(func)(*args, **kwargs)
        return wrapper
    return decorator
