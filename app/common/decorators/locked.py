import asyncio
from asyncio import locks
from functools import wraps
from logging import Logger
from typing import Callable, List

from redis.asyncio.lock import Lock

from app.common.database.async_client import AsyncRedisClientService
from app.common.model.configuration import LockConfig
from app.common.services.config_service import ConfigService
from app.common.services.harness_service import HarnessService


def locked(
    logger: Logger,
    entity_id_name: str | int,
    config_service: ConfigService = ConfigService(),
    redis_database: AsyncRedisClientService = AsyncRedisClientService(),
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            lock_config: LockConfig = (
                config_service.get_current_config().update_campaign_lock_config
                if entity_id_name == "campaign_id"
                else config_service.get_current_config().update_activation_lock_config
            )
            if lock_config.enabled:
                lock_expire = lock_config.expire_seconds
                entity_id = kwargs.get(entity_id_name)
                lock_name = f"{lock_config.lock_prefix}:{entity_id_name}:{entity_id}"

                redis_client = await redis_database.async_engine()

                logger.info("Acquiring lock: %s", lock_name)
                async with Lock(redis_client, lock_name, lock_expire, blocking=True):
                    logger.info("Lock acquired: %s", lock_name)
                    try:
                        return await func(*args, **kwargs)
                    except Exception as err:
                        logger.error(
                            f"Error occurred while executing function {func.__name__} with error: {err}"
                        )
                        raise
                    finally:
                        logger.info("Releasing lock: %s", lock_name)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def locked_with_params(
    key_builder: Callable[..., str],
    logger: Logger,
    lock_config: LockConfig = LockConfig(
        enabled=True, lock_prefix="LOCK", expire_seconds=240
    ),
    lock_config_name: str = None,
    harness_service: HarnessService = None,
    redis_database: AsyncRedisClientService = None,
):
    harness_service = harness_service or HarnessService()
    redis_database = redis_database or AsyncRedisClientService()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            harness_config = harness_service.fetch_multivariate_flag(
                flag_name=lock_config_name, target_id="default")

            if harness_config.get("enabled"):

                redis_client = await redis_database.async_engine()

                if lock_config.enabled:
                    real_args = (
                        args[1:] if args and hasattr(args[0], "__class__") else args
                    )  # skip self if exist
                    key = key_builder(*real_args, **kwargs)
                    lock_name = f"{lock_config.lock_prefix}:{key}"

                    async with Lock(
                        redis_client, lock_name, lock_config.expire_seconds, blocking=True
                    ):
                        try:
                            return await func(*args, **kwargs)
                        except Exception as err:
                            logger.error(
                                f"Error occurred while executing function {func.__name__} with error: {err}"
                            )
                            raise
                        finally:
                            logger.info("Releasing lock: %s", lock_name)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
