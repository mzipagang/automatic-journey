import json

from fastapi import Depends, HTTPException

from app.common.database.async_client import AsyncRedisClientService, RedisKeyTypes
from app.common.model.placement import Placement
from app.common.services.config_service import ConfigService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

get_placements_response = json.loads('''[
    {
        "placementId": "01100",
        "name": "Search & Browse",
        "channelShortName": "PLA",
        "minimumBidAmount": 0.5
    },
    {
        "placementId": "01200",
        "name": "Basket Builder",
        "channelShortName": "PLA",
        "minimumBidAmount": 0.6
    },
    {
        "placementId": "01300",
        "name": "Savings",
        "channelShortName": "PLA",
        "minimumBidAmount": 0.3
    }
]''')

class PlacementService:
    config_service: ConfigService
    redis_cache: AsyncRedisClientService
    __external_api_http_client: ExternalApiHttpClientService

    def __init__(self,
                 config_service: ConfigService = Depends(ConfigService),
                 redis_cache: AsyncRedisClientService = Depends(AsyncRedisClientService),
                 external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService)
                 ):
        self.config_service = config_service
        self.redis_cache = redis_cache
        self.__external_api_http_client = external_api_http_client_service

    async def get_cache_placement(self, placement_id):
        return json.loads(await self.redis_cache.get(RedisKeyTypes.PLACEMENT, placement_id))

    async def get_placements(self):
        config = self.config_service.get_current_config()
        if config.base_api_url is None:
            raise ValueError("API url is not found")

        placements = []
        for placement in get_placements_response:
            placement_id: int
            placement_key = f"{placement['placementId']}:{placement['name']}"

            placement_id = await self.redis_cache.get(RedisKeyTypes.PLACEMENT, placement_key)
            if not placement_id:
                placement_id = await self.redis_cache.assign_numeric_id(RedisKeyTypes.PLACEMENT, placement_key)

            if placement_id is None:
                raise HTTPException(
                    status_code=500, detail="Failed to assign placement id"
                )

            # Cache the inverse lookups

            # As it comes from the activation service with just the name
            await self.redis_cache.set(
                RedisKeyTypes.PLACEMENT,
                f'{placement["name"]}',
                f"{placement_id}",
            )

            await self.redis_cache.set(
                RedisKeyTypes.PLACEMENT, f"{placement_id}", json.dumps(placement)
            )

            placements.append(Placement(
                id=placement_id,
                name=placement['name'],
                description=placement['name'] + ' ' + placement['channelShortName'],
                active=True,
                priceFloor=placement['minimumBidAmount']))

        return placements
