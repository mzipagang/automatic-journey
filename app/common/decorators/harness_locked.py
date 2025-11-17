from functools import wraps
from logging import Logger

from redis.exceptions import ConnectionError, TimeoutError
from redis.asyncio.lock import Lock

from app.common.database.async_client import AsyncRedisClientService, SERVICE_UNAVAILABLE_EXCEPTION, \
    SERVICE_TIMEOUT_EXCEPTION
from app.common.services.harness_service import HarnessService


def locked(
        lock_config_name: str,
        logger: Logger,
        entity_id_name: str | int,
        target_identifier: str = "default",
        harness_service: HarnessService = HarnessService(),
        redis_database: AsyncRedisClientService = AsyncRedisClientService()):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            lock_config = harness_service.fetch_multivariate_flag(
                flag_name=lock_config_name, target_id=target_identifier)

            if lock_config.get("enabled"):
                lock_expire = lock_config.get('expire')
                entity_id = kwargs.get(entity_id_name)
                lock_name = f'{lock_config.get("lock_prefix")}:{entity_id_name}:{entity_id}'

                redis_client = await redis_database.async_engine()

                logger.info("Acquiring lock: %s", lock_name)
                try:
                    async with Lock(redis_client, lock_name, lock_expire, blocking=True):
                        logger.info("Lock acquired: %s", lock_name)
                        try:
                            return await func(*args, **kwargs)
                        except Exception as err:
                            logger.error(f"Error occurred while executing function {func.__name__} with error: {err}")
                            raise
                        finally:
                            logger.info("Releasing lock: %s", lock_name)
                except (ConnectionError, ConnectionRefusedError) as e:
                    logger.critical("Redis connection error!",
                        extra={
                            "monitored_transaction": {
                                'name': 'REDIS-CONNECTION',
                                'method': 'harness_locked.locked',
                                'error': str(e)
                            }
                        }
                    )
                    raise SERVICE_UNAVAILABLE_EXCEPTION from e
                except TimeoutError as e:
                    logger.critical("Redis timeout error!",
                        extra={
                            "monitored_transaction": {
                                'name': 'REDIS-TIMEOUT',
                                'method': 'harness_locked.locked',
                                'error': str(e)
                            }
                        }
                    )
                    raise SERVICE_TIMEOUT_EXCEPTION from e

            return await func(*args, **kwargs)
        return wrapper
    return decorator
