from collections import OrderedDict
from typing import List

from fastapi import Depends

from app.common.services.lookup_service import LookupService
from app.common.services.placement_service import PlacementService
from app.common.services.target_service import TargetService
from app.v2.model.downstream.activation_service import ActivationResponse
from app.common.model.shared import InternalCampaignType
from app.common.model.targets import Target, TargetAdgroupRequest
from app.common.services.division_service import DivisionService
from app.common.utils import filtered_logger
from app.common.utils.campaign_type_utils import is_carousel_campaign

logger = filtered_logger.get_logger(__name__)

class TargetTranslation:
    lookup: LookupService
    division_service: DivisionService
    placement_service: PlacementService

    def __init__(
            self,
            lookup: LookupService = Depends(LookupService),
            division_service: DivisionService = Depends(DivisionService),
            placement_service: PlacementService = Depends(PlacementService)
    ):
        self.lookup = lookup
        self.division_service = division_service
        self.placement_service = placement_service

    async def targets_from_activation(self, activation: ActivationResponse) -> List[Target]:
        """
        Extracts the targets from an activation.
        """
        targets = []
        placement_type: List[str] = []
        division_banners: List[str] = (
            activation.channel_data.get("divisionBanners", []) if activation.channel_data else []
        )
        day_parting_start = None
        day_parting_end = None

        carousel_campaign_flow = (
            is_carousel_campaign(InternalCampaignType(activation.channel_config.type))
            if activation.channel_config
            else False
        )

        if not carousel_campaign_flow and activation.channel_data:
            placement_type: List[str] = (
                activation.channel_data.get("placementType", [])
            )
            day_parting_start = activation.channel_data.get('dayPartingStart')
            day_parting_end = activation.channel_data.get('dayPartingEnd')

        if placement_type:
            targets += await self.placement_targets_from_types(placement_type)

        if division_banners:
            targets += await self.division_targets_from_banners(division_banners)

        has_day_parting = day_parting_start is not None and day_parting_end is not None

        if has_day_parting:
            logger.info("Getting dayparting range")
            targets.append(
                Target(
                    values=[
                        int(day_parting_start),
                        int(day_parting_end)
                    ],
                    type="3",
                )
            )

        return targets

    async def placement_targets_from_types(self, placement_types: List[str]) -> List[Target]:
        """
        Converts a list of placement types to a list of targets.
        """
        placement_ids = await self.lookup.get_placement_short_ids_by_names(placement_types)
        placement_targets = []
        missing_placement_types = []
        for index, placement_id in enumerate(placement_ids):
            if placement_id is None:
                missing_placement_types.append(placement_types[index])
            else:
                placement_target = Target(type="1", id=placement_id)
                placement_targets.append(placement_target)

        if missing_placement_types:
            logger.warning("Placement types missing from redis: %s", missing_placement_types)

        return placement_targets

    async def division_targets_from_banners(self, division_banners: List[str]) -> List[Target]:
        """
        Converts a list of division banners to a list of targets.
        """
        division_ids = await self.division_service.get_division_ids_from_banners(division_banners)
        return [Target(type="2", id=division_id) for division_id in division_ids]

    @staticmethod
    def fetch_ad_group_targets(
            request_targets: list[TargetAdgroupRequest],
            carousel_campaign_flow: bool
    ) -> tuple[list[TargetAdgroupRequest], list[TargetAdgroupRequest], list[TargetAdgroupRequest]]:
        placement_target, division_target, day_parting_target = TargetService().get_targets()
        ad_group_placement_targets = []
        ad_group_division_targets = []
        ad_group_day_parting_targets = []
        type_to_list_map = {
            placement_target.id: ad_group_placement_targets,
            division_target.id: ad_group_division_targets,
            day_parting_target.id: ad_group_day_parting_targets
        }
        for target in request_targets:
            target_type = int(target.type)
            if target_type not in type_to_list_map:
                continue
            if target_type == day_parting_target.id and carousel_campaign_flow:
                continue
            type_to_list_map[target_type].append(target)
        return (
            list(OrderedDict.fromkeys(ad_group_placement_targets)),
            list(OrderedDict.fromkeys(ad_group_division_targets)),
            list(OrderedDict.fromkeys(ad_group_day_parting_targets))
        )

    async def build_placements_types(
            self,
            ad_group_placement_targets: List[TargetAdgroupRequest] | List[Target]
    ) -> list[str] :
        placement_types = []
        for target in ad_group_placement_targets:
            # TODO once we have replace with MGET operation
            placement = await self.placement_service.get_cache_placement(target.id)
            placement_types.append(placement["name"])
        return placement_types
