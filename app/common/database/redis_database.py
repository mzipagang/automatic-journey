
from typing import Any
from enum import StrEnum

import redis

from fastapi import Depends

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
    AD_GROUP = 'AD_GROUP'


class RedisDatabase:
    redis_client: redis.Redis

    def __init__(self, config_service: ConfigService = Depends(ConfigService)):
        self.config_service = config_service
        settings = self.config_service.get_current_config()
        self.redis_client = redis.Redis(host=settings.redis_host,
                                        port=settings.redis_port,
                                        db=settings.redis_db,
                                        password=settings.redis_primary_access_key
                                        if settings.redis_primary_access_key
                                        and len(settings.redis_primary_access_key) > 0
                                        else None,
                                        ssl=settings.redis_ssl,
                                        socket_keepalive=True,
                                        health_check_interval=settings.redis_health_check_interval,
                                        socket_timeout=settings.redis_socket_timeout,
                                        socket_connect_timeout=settings.redis_socket_connect_timeout)
        # Check if there are any errors initializing the redis client
        if self.redis_client is None:
            raise ValueError("Redis client is None")
        if self.redis_client.connection_pool is None:
            raise ValueError("Redis client connection pool is None")
        status = self.ping()
        if status is not True:
            logger.error("Redis Database Status: %s", status)

    def ping(self):
        try:
            self.redis_client.ping()
        except (redis.exceptions.ConnectionError, ConnectionRefusedError):
            logger.critical("Redis connection error!")
            return False
        return True

    def get(self, entity: RedisKeyTypes, key):
        # logger.info("Redis attempting to get result for key: %s type: %s", key, entity)
        result = self.redis_client.get(f"{entity}:{key}")
        if result is None:
            logger.warning("Redis get result: None for key: %s type: %s", key, entity)
            return None
        # Decode the result from bytes to string
        result = str(result, 'utf-8')
        # logger.info("Redis get result: %s for key: %s type: %s", result, key, entity)
        return result

    def set(self, entity: RedisKeyTypes, key: Any, value: Any):
        result = self.redis_client.set(f"{entity}:{key}", value)
        logger.debug("Redis set result: %s for key: %s", result, key)

    def delete(self, entity: RedisKeyTypes, key):
        self.redis_client.delete(f"{entity}:{key}")

    def exists(self, entity: RedisKeyTypes, key):
        return self.redis_client.exists(f"{entity}:{key}")

    def assign_numeric_id(self, entity: RedisKeyTypes, key):
        next_value = self.redis_client.incr(f"{entity}:id")
        self.redis_client.set(f"{entity}:{key}", next_value)
        return next_value

    def get_numeric_id(self, entity: RedisKeyTypes, text_id: str) -> str | None:
        numeric_id: str | None
        id_exists = self.exists(entity, text_id)
        if id_exists == 1:
            numeric_id = self.get(entity, text_id)
            return numeric_id
        logger.debug("Unexpected exists value: %s", id_exists)

    def cache_internal_id(self, entity: RedisKeyTypes, key: int, value: str):
        logger.debug("Redis cache_internal_id: %s for key: %s", f"{entity}:{key}", value)
        self.redis_client.set(f"{entity}:{key}", value)
