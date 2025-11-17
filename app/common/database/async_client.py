from dataclasses import dataclass
from enum import StrEnum
from typing import Any, List, Dict

from fastapi import HTTPException, status
from redis.asyncio import client as redis_async_client
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError
from app.common.services.config_service import ConfigService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

class RedisKeyTypes(StrEnum):
    CONTACT = 'CONTACT'
    ADDRESS = 'ADDRESS'
    ACCOUNT = 'ACCOUNT'
    ADVERTISER = 'ADVERTISER'
    KODDI_ADVERTISER = 'KODDI_ADVERTISER'
    DIVISION = 'DIVISION'
    PLACEMENT = 'PLACEMENT'
    PRODUCT = 'PRODUCT'
    CAMPAIGN = 'CAMPAIGN'
    CAMPAIGN_KODDI = 'CAMPAIGN:KODDI'
    AD_GROUP = 'AD_GROUP'
    AD_GROUP_KODDI = 'AD_GROUP:KODDI'

SERVICE_TIMEOUT_EXCEPTION = HTTPException(
    status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="The upstream service did not respond in time. Please try again later")

SERVICE_UNAVAILABLE_EXCEPTION = HTTPException(
    status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="The cache service is currently unavailable. Please try again later"
)

class SingletonDBManager(type):
    _instances = {}

    def __call__(cls):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__()
        return cls._instances[cls]


@dataclass
class AsyncRedisClientService(metaclass=SingletonDBManager):
    def __init__(self):
        self._async_client = None

    async def async_engine(self):
        try:
            config_service = ConfigService()
            current_config = config_service.get_current_config()

            if self._async_client is None:
                self._async_client = await redis_async_client.Redis(
                    host=current_config.redis_host,
                    port=current_config.redis_port,
                    db=current_config.redis_db,
                    password=current_config.redis_primary_access_key,
                    ssl=current_config.redis_ssl,
                    socket_keepalive= True,
                    health_check_interval=current_config.redis_health_check_interval,
                    socket_timeout=current_config.redis_socket_timeout,
                    socket_connect_timeout=current_config.redis_socket_connect_timeout
                )
            return self._async_client
        except RedisError:
            logger.critical("Redis connection error!")

    async def get_client(self):
        try:
            await self.ping()
        except (RedisConnectionError, ConnectionRefusedError) as e:
            logger.critical("Redis connection error!",
                            extra={
                                "monitored_transaction": {
                                    'name': 'REDIS-CONNECTION',
                                    'method': 'AsyncRedisClientService.get_client',
                                    'error': str(e)
                                }
                            }
                        )
            raise SERVICE_UNAVAILABLE_EXCEPTION from e
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis ping timeout error",
                            extra={
                                "monitored_transaction": {
                                    'name': 'REDIS-TIMEOUT',
                                    'method': 'AsyncRedisClientService.get_client',
                                    'error': str(e)
                                }
                            }
                            )
            raise SERVICE_TIMEOUT_EXCEPTION from e
        return self._async_client

    async def ping(self):
        try:
            await self._async_client.ping()
            return True
        except (RedisConnectionError, ConnectionRefusedError) as e:
            logger.critical("AsyncRedisClientService: Redis ping connection error!",
                            extra={
                                "monitored_transaction": {
                                    'name': 'REDIS-CONNECTION',
                                    'method': 'AsyncRedisClientService.ping',
                                    'error': str(e)
                                }
                            }
                            )
            raise SERVICE_UNAVAILABLE_EXCEPTION from e
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis ping timeout error",
                            extra={
                                "monitored_transaction": {
                                    'name': 'REDIS-TIMEOUT',
                                    'method': 'AsyncRedisClientService.ping',
                                    'error': str(e)
                                }
                            }
                            )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def close(self):
        await self._async_client.aclose()

    def reset(self):
        self._async_client = None

    async def get(self, entity: RedisKeyTypes, key):
        try:
            result = await self._async_client.get(f"{entity}:{key}")
            # Decode the result from bytes to string
            if result is not None:
                result = str(result, 'utf-8')
        except RedisConnectionError as e:
            logger.critical("AsyncRedisClientService: Redis get connection error.",
                             extra={
                                 "monitored_transaction": {
                                     'name': 'REDIS-CONNECTION',
                                     'method': 'AsyncRedisClientService.get',
                                     'entity': entity,
                                     'key': key,
                                     'error': str(e)
                                }
                             }
                         )
            raise SERVICE_UNAVAILABLE_EXCEPTION from e
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis get timeout error.",
                             extra={
                                 "monitored_transaction": {
                                     'name': 'REDIS-TIMEOUT',
                                     'method': 'AsyncRedisClientService.get',
                                     'entity': entity,
                                     'key': key,
                                     'error': str(e)
                                }
                             }
                         )
            raise SERVICE_TIMEOUT_EXCEPTION from e
        if result is None:
            logger.warning("Redis get result: None",
                            extra = {
                                "monitored_transaction": {
                                    'name': 'REDIS-TIMEOUT',
                                    'method': 'AsyncRedisClientService.get',
                                    'entity': entity,
                                    'key': key
                                }
                            }
                        )
            return None
        return result

    async def mget(self, entity: RedisKeyTypes, keys: List[str|int]) -> List[str|None]:
        if not keys:
            return []
        complete_keys = [f"{entity}:{key}" for key in keys]
        try:
            result = await self._async_client.mget(complete_keys)
            decoded_results = []
            for key in result:
                if key is None:
                    decoded_results.append(None)
                    continue
                decoded_results.append(str(key, "utf-8"))
            return decoded_results
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis mget timeout error",
                            extra={
                                "monitored_transaction": {
                                    'name': 'REDIS-TIMEOUT',
                                    'method': 'AsyncRedisClientService.mget',
                                    'error': str(e)
                                }
                            }
                        )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def mset(self, keys: Dict[str, Any]):
        if not keys:
            return
        try:
            result = await self._async_client.mset(keys)
            logger.debug("Redis set result: %s for keys: %s", result, keys)
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis mset timeout error",
                         extra={
                             "monitored_transaction": {
                                 'name': 'REDIS-TIMEOUT',
                                 'method': 'AsyncRedisClientService.mset',
                                 'keys': keys,
                                 'error': str(e)
                             }
                         }
                    )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def set(self, entity: RedisKeyTypes, key: Any, value: Any):
        try:
            result = await self._async_client.set(f"{entity}:{key}", value)
            logger.debug("Redis set result: %s for key: %s", result, key)
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis set timeout error ",
                        extra = {
                            "monitored_transaction": {
                                'name': 'REDIS-TIMEOUT',
                                'method': 'AsyncRedisClientService.set',
                                'key': key,
                                'error': str(e)
                            }
                        }
                    )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def delete(self, entity: RedisKeyTypes, key):
        try:
            await self._async_client.delete(f"{entity}:{key}")
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis delete timeout error",
                         extra={
                             "monitored_transaction": {
                                 'name': 'REDIS-TIMEOUT',
                                 'method': 'AsyncRedisClientService.delete',
                                 'key': key,
                                 'error': str(e)
                             }
                         }
                         )
            raise SERVICE_TIMEOUT_EXCEPTION from e


    async def exists(self, entity: RedisKeyTypes, key):
        try:
            result = await self._async_client.exists(f"{entity}:{key}")
            return result
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis exists timeout error",
                         extra={
                             "monitored_transaction": {
                                 'name': 'REDIS-TIMEOUT',
                                 'method': 'AsyncRedisClientService.exists',
                                 'key': key,
                                 'error': str(e)
                             }
                         }
                         )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def assign_numeric_id(self, entity: RedisKeyTypes, key):
        try:
            next_value = await self._async_client.incr(f"{entity}:id")
            await self._async_client.set(f"{entity}:{key}", next_value)
            return next_value
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis assign_numeric_id timeout error",
                         extra={
                             "monitored_transaction": {
                                 'name': 'REDIS-TIMEOUT',
                                 'method': 'AsyncRedisClientService.assign_numeric_id',
                                 'key': key,
                                 'error': str(e)
                             }
                         }
                         )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def assign_numeric_id_batch(self, entity: RedisKeyTypes, keys: List[str]) -> List[int]:
        if not keys:
            return []
        try:
            beginning_value = await self._async_client.incr(f"{entity}:id")
            await self._async_client.incrby(f"{entity}:id", len(keys) - 1)
            keys = {f"{entity}:{key}": beginning_value + i  for i, key in enumerate(keys)}
            await self._async_client.mset(keys)
            return list(keys.values())
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis assign_numeric_id_batch timeout error",
                         extra={
                             "monitored_transaction": {
                                 'name': 'REDIS-TIMEOUT',
                                 'method': 'AsyncRedisClientService.assign_numeric_id_batch',
                                 'keys': keys,
                                 'error': str(e)
                             }
                         }
                         )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def get_numeric_id(self, entity: RedisKeyTypes, text_id: str) -> str | None:
        numeric_id: str | None
        numeric_id = await self.get(entity, text_id)
        return numeric_id

    async def cache_internal_id(self, entity: RedisKeyTypes, key: int, value: str):
        try:
            logger.debug("Redis cache_internal_id: %s for key: %s", f"{entity}:{key}", value)
            await self._async_client.set(f"{entity}:{key}", value)
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis cache_internal_id timeout error",
                         extra={
                             "monitored_transaction": {
                                 'name': 'REDIS-TIMEOUT',
                                 'method': 'AsyncRedisClientService.cache_internal_id',
                                 'key': key,
                                 'error': str(e)
                             }
                         }
                         )
            raise SERVICE_TIMEOUT_EXCEPTION from e

    async def cache_internal_id_batch(self, keys_with_values: Dict):
        try:
            logger.debug("Redis cache_internal_id_batch for key and values: %s", keys_with_values)
            await self._async_client.mset(keys_with_values)
        except RedisTimeoutError as e:
            logger.critical("AsyncRedisClientService: Redis cache_internal_id_batch timeout error",
                         extra={
                             "monitored_transaction": {
                                 'name': 'REDIS-TIMEOUT',
                                 'method': 'AsyncRedisClientService.cache_internal_id_batch',
                                 'keys': keys_with_values,
                                 'error': str(e)
                             }
                         }
                         )
            raise SERVICE_TIMEOUT_EXCEPTION from e
