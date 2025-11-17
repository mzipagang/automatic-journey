import logging
from functools import wraps
from logging import Logger

from tenacity import retry, wait_fixed, stop_after_attempt, before_sleep_log, after_log
from tenacity.asyncio import retry_if_exception

from app.common.retry.predicates import rate_limit_exceeded
from app.common.services.harness_service import HarnessService

def backoff_wait_rate_limited(
        config_name: str,
        rl_config_name: str,
        rl_decorator: callable,
        logger: Logger,
        target_identifier: str = "default",
        harness_service: HarnessService = HarnessService()):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = harness_service.fetch_multivariate_flag(
                flag_name=config_name, target_id=target_identifier)

            if config.get("enabled"):
                pause_seconds = config.get('pause_seconds')
                max_retries = config.get('max_retries')

                rate_limit_decorator = rl_decorator(
                    config_name=rl_config_name,
                    logger=logger,
                    target_identifier=target_identifier,
                    harness_service=harness_service
                ) (func)

                retry_decorator = retry(
                    reraise=True,
                    wait=wait_fixed(pause_seconds),
                    stop=stop_after_attempt(max_retries),
                    before_sleep=before_sleep_log(logger, logging.INFO),
                    after=after_log(logger, logging.INFO),
                    retry=retry_if_exception(rate_limit_exceeded)
                )

                return await retry_decorator(rate_limit_decorator)(*args, **kwargs)

            return await rl_decorator(
                config_name=rl_config_name,
                logger=logger,
                target_identifier=target_identifier,
                harness_service=harness_service
            )(func)(*args, **kwargs)
        return wrapper
    return decorator
