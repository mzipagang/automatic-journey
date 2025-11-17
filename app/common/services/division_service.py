from typing import List

from fastapi import Depends

from app.common.gateways.division_gateway import DivisionGateway
from app.common.model.downstream.location_groups import DivisionBannerItem
from app.common.model.division import DivisionData
from app.common.services.lookup_service import LookupService
from app.common.model.division import Division
from app.common.model.targets import TargetAdgroupRequest
from app.common.services.config_service import ConfigService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class DivisionService:
    config_service: ConfigService
    division_gateway: DivisionGateway
    lookup: LookupService

    def __init__(
            self,
            config_service: ConfigService = Depends(ConfigService),
            division_gateway: DivisionGateway = Depends(DivisionGateway),
            lookup: LookupService = Depends(LookupService),
    ):
        self.config_service = config_service
        self.division_gateway = division_gateway
        self.lookup = lookup

    async def get_divisions(self) -> List[Division]:
        divisions = await self.division_gateway.get_divisions()
        division_items = [DivisionBannerItem(
            bannerCode=division.bannerCode,
            divisionNumber=division.divisionNumber
        ) for division in divisions]
        division_ids = await self.lookup.get_division_short_ids_by_division_items(division_items)
        division_data = {
            f"{division_item.bannerCode}:{division_item.divisionNumber}": DivisionData(
                division_id=division_id,
                division=division_item
            )
            for division_item, division_id in zip(divisions, division_ids)
        }
        missing_divisions_keys = [
            division_key
            for division_key, division_value  in division_data.items()
            if division_value.division_id is None
        ]
        if missing_divisions_keys:
            await self.bind_division_banner_and_number_to_id(missing_divisions_keys, division_data)
        return [
            Division(
                id=division_info.division_id,
                name=division_info.division.label,
                active=True
                # TODO:review this, is not used and what is the impact of remove or use the flag get from divisions endpoint
            )
            for _, division_info in division_data.items()
        ]

    async def bind_division_banner_and_number_to_id(
            self,
            missing_divisions_keys: list[str],
            division_data: dict[str, DivisionData]
    ):
        generated_division_ids = await (self.lookup.
         set_division_short_id_by_banner_code_and_division_number_batch(
            missing_divisions_keys
        ))
        divisions_to_cache = {}
        for generated_id, missing_division_key in zip(generated_division_ids, missing_divisions_keys):
            divisions_to_cache[str(generated_id)] = division_data.get(missing_division_key).division
            division_data[missing_division_key].division_id = generated_id
        await self.lookup.set_division_data_by_short_id_batch(divisions_to_cache)

    async def get_location_group_payload(self, division_ids: List[int]):
        divisions = await self.lookup.get_division_details_by_short_id_batch(division_ids)
        items = [
            {
                "divisionNumber": division.divisionNumber,
                "bannerCode": division.bannerCode,
            }
            for division in divisions
            if division is not None
        ]
        payload = {
            "categories": [{
                "items": items,
                "type": "division-banner"
            }]
        }
        return payload

    async def build_location_group(self, ad_group_division_targets: List[TargetAdgroupRequest]) -> str:
        if len(ad_group_division_targets) == 0:
            # If no division targets are provided, we will use all divisions
            divisions = await self.get_divisions()
            division_ids = [division.id for division in divisions]
        else:
            division_ids = [target.id for target in ad_group_division_targets]
        location_group = await self.get_location_group_payload(division_ids)
        logger.info('Location Group: %s', location_group)
        location_group_id = (await self.division_gateway.create_location_group(location_group)).id
        logger.info('Location Group Id: %s', location_group_id)
        return location_group_id

    async def get_division_ids_from_banners(self, division_banners: List[str]) -> List[int]:
        """
        Handles converting division banners into a list of division short ids.
        """
        location_groups = await self.division_gateway.get_location_groups(division_banners)
        if location_groups.notFound:
            logger.warning('Location Groups not found for %s', location_groups.notFound)

        division_items = []
        for location_group in location_groups.found:
            for category in location_group.categories:
                if category.type != "division-banner":
                    continue
                for division_item in category.items:
                    division_items.append(division_item)

        division_ids = await self.lookup.get_division_short_ids_by_division_items(division_items)
        filtered_division_ids = []
        missing_division_items = []
        for index, division_id in enumerate(division_ids):
            if division_id is None:
                missing_division_items.append(division_items[index])
            else:
                filtered_division_ids.append(division_id)

        if missing_division_items:
            logger.warning('Divisions missing from redis cache: %s', missing_division_items)

        return filtered_division_ids
