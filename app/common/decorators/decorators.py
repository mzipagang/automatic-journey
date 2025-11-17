import logging
from functools import wraps
from typing import Optional, Type

from fastapi import HTTPException
from fastapi_cache import Coder
from fastapi_cache.decorator import cache
from tenacity import stop_after_attempt, wait_fixed, before_sleep_log, after_log, retry, retry_if_exception

from app.common.services.harness_service import HarnessService


def feature_flag(feature_name,
                 target_identifier="default",
                 harness_service: HarnessService = HarnessService()):
    """
    Decorator that checks if a feature flag is enabled for a given target identifier.
    
    Args:
        feature_name (str): The name of the feature flag.
        target_identifier (str, optional): The identifier of the target. Defaults to "default".
        harness_service (HarnessService, optional): The HarnessService instance used to check the flag. 
            Defaults to Depends(HarnessService).
    
    Returns:
        function: The decorated function.
    
    Raises:
        HTTPException: If the feature flag is disabled on the current environment.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if harness_service.is_harness_flag_on(feature_name, target_identifier):
                return await func(*args, **kwargs)
            raise HTTPException(
                status_code=403,
                detail=f"Feature {feature_name} is disabled on this environment."
            )
        return wrapper
    return decorator

def conditionally_execute(flag_name: str, default_method: callable = lambda *args, **kwargs: None,
                          harness_service: HarnessService = HarnessService(), target_identifier: str = "default"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if harness_service.is_harness_flag_on(flag_name, target_identifier):
                return func(*args, **kwargs)
            return default_method(*args, **kwargs)
        return wrapper
    return decorator

def async_conditionally_execute(flag_name: str, default_method: callable = lambda *args, **kwargs: None,
                          harness_service: HarnessService = HarnessService(), target_identifier: str = "default"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if harness_service.is_harness_flag_on(flag_name, target_identifier):
                return await func(*args, **kwargs)
            return default_method(*args, **kwargs)
        return wrapper
    return decorator

def conditional_cache(
        key_builder: callable,
        target_identifier: str = "default",
        feature_name: str = "kpa_cache_config",
        harness_service: HarnessService = HarnessService(),
        coder: Optional[Type[Coder]] = None,
):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            flag: dict = harness_service.fetch_multivariate_flag(feature_name, target_identifier)
            if flag['enabled']:
                ttl = flag['ttl']
                return await cache(
                    expire=ttl,
                    key_builder=key_builder,
                    coder=coder,
                )(func)(*args, **kwargs)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def conditionally_retry(
        flag_name: str,
        logger: logging.Logger,
        retry_predicate: callable = lambda *args, **kwargs: None,
        target_identifier: str = "default",
        harness_service: HarnessService = HarnessService()):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            flag: dict = harness_service.fetch_multivariate_flag(
                flag_name=flag_name, target_id=target_identifier)
            if flag.get('enabled'):
                pause_seconds = flag.get('pause_seconds')
                max_retries = flag.get('max_retries')
                retry_decorator = retry(
                    reraise=True,
                    wait=wait_fixed(pause_seconds),
                    stop=stop_after_attempt(max_retries),
                    before_sleep=before_sleep_log(logger, logging.INFO),
                    after=after_log(logger, logging.INFO),
                    retry=retry_if_exception(retry_predicate)
                )
                return retry_decorator(func)(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def disable_if_flag_on(
        flag_name: str,
        message: str = "",
        harness_service: HarnessService = HarnessService(),
        target_identifier: str = "default"
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Added this validation cause in some cases the @version decorator
            # is used in the same method for v2 and v1
            request = kwargs.get("request")
            path = "v1"
            if request:
                path = request.url.path
            if harness_service.is_harness_flag_on(flag_name, target_identifier) and "v1" in path:
                    raise HTTPException(status_code=404, detail=message)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
