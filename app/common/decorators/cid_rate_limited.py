from functools import wraps
from logging import Logger
from random import randint

from app.common.context.context import client_context
from app.common.database.async_client import AsyncRedisClientService
from app.common.exceptions.predicate_exceptions import RateLimitExceededException
from app.common.services.harness_service import HarnessService


def cid_rate_limited(
        config_name: str,
        logger: Logger,
        target_identifier: str = "default",
        harness_service: HarnessService = HarnessService(),
        redis_database_service: AsyncRedisClientService = AsyncRedisClientService()):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = harness_service.fetch_multivariate_flag(
                flag_name=config_name, target_id=target_identifier)

            if config.get("enabled"):
                client_id = client_context.get().get("client_id")
                if not client_id:
                    client_id = "default"
                requests_per_minute = config.get('requests_per_minute')
                rate_limit_key = f'{config.get("rate_limit_prefix")}:{client_id}:{func.__name__}'

                redis_client = await redis_database_service.async_engine()
                current_request_count_bytes = await redis_client.get(rate_limit_key)

                if current_request_count_bytes is None:
                    current_request_count = 0
                    await redis_client.set(rate_limit_key, current_request_count, ex=60)
                else:
                    current_request_count = int(current_request_count_bytes)

                record_ttl = await redis_client.ttl(rate_limit_key)

                if record_ttl < 0:
                    logger.warning(
                        "Rate limit key %s has expired and was not deleted. Resetting.",
                        str(rate_limit_key),
                        extra={
                            "rate_limit_key": rate_limit_key,
                            "client_id": client_id,
                            "monitored_transaction": "REDIS-ERROR--LOST-TTL"
                        })

                    if current_request_count < requests_per_minute:
                        await redis_client.set(rate_limit_key, current_request_count, ex=randint(35, 57))
                    else:
                        await redis_client.set(
                            rate_limit_key, current_request_count // randint(2, 10), ex=randint(5, 23))
                        current_request_count = 0
                elif record_ttl > 60:
                    logger.warning(
                        "Rate limit key %s has an unexpected TTL of %s seconds. Resetting.",
                        str(rate_limit_key),
                        str(record_ttl),
                        extra={
                            "rate_limit_key": rate_limit_key,
                            "client_id": client_id,
                            "monitored_transaction": "REDIS-ERROR--UNEXPECTED-TTL"
                        })

                    await redis_client.set(rate_limit_key, current_request_count, ex=randint(15, 45))

                if current_request_count < requests_per_minute:
                    await redis_client.incr(rate_limit_key)
                    logger.info(f"Request count for {rate_limit_key} is {current_request_count + 1}")
                    return await func(*args, **kwargs)

                raise RateLimitExceededException(client_id=client_id)

            return await func(*args, **kwargs)
        return wrapper
    return decorator
