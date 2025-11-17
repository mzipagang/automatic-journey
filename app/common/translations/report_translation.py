from copy import deepcopy
from typing import Set, Dict, Tuple, List, Callable, Coroutine, Any, Iterable

from fastapi import Depends, HTTPException
from httpx import codes as httpx_codes

from app.common.gateways.campaign_service_gateway import CampaignServiceGateway
from app.common.model.report import IdGroup, MissingLookupWarning, UniqueReportIds, ExternalIdByKoddiId
from app.common.services.lookup_service import LookupService
from app.common.view_models.report import Dimensions
from app.common.gateways.activation_gateway import ActivationGateway
from app.v2.model.downstream.activation_service import ActivationsQueryBody
from app.common.model.downstream.bid_manager import Bid
from app.common.model.downstream.campaign_service import CampaignSearchRequest
from app.common.services.bid_manager_service import BidManagerService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

class ReportTranslation:
    lookup: LookupService
    activation_gateway: ActivationGateway
    campaign_gateway: CampaignServiceGateway
    bid_manager_service: BidManagerService

    def __init__(
            self,
            lookup: LookupService = Depends(LookupService),
            activation_gateway: ActivationGateway = Depends(ActivationGateway),
            campaign_gateway: CampaignServiceGateway = Depends(CampaignServiceGateway),
            bid_manager_service: BidManagerService = Depends(BidManagerService),
    ):
        self.lookup = lookup
        self.activation_gateway = activation_gateway
        self.campaign_gateway = campaign_gateway
        self.bid_manager_service = bid_manager_service

    async def build_translation(
            self,
            koddi_ids: Set[int],
            lookup_long_id_by_koddi_id: Callable[[List[int]], Coroutine[Any, Any, List[str | None]]],
            lookup_short_id_by_long_id: Callable[[List[str]], Coroutine[Any, Any, List[int | None]]],
            cache_long_id_by_koddi_id: Callable[[Dict[int, str]], Coroutine[Any, Any, None]],
            cache_short_id_by_long_id: Callable[[Dict[str, int]], Coroutine[Any, Any, None]],
            handle_missing_long_ids: Callable[[List[int], Dict[int, IdGroup]], Coroutine[Any, Any, Dict[int, IdGroup]]],
            handle_missing_short_ids: Callable[[List[int], Dict[int, IdGroup]], Coroutine[Any, Any, Dict[int, IdGroup]]],
    ) -> Dict[int, int]:
        """
        Handles building a dictionary mapping koddi ids to short ids
        Args:
            koddi_ids: A unique set of koddi ids
            lookup_long_id_by_koddi_id: batch lookup function to get long ids by koddi id
            lookup_short_id_by_long_id: batch lookup function to get short ids by long id
            cache_long_id_by_koddi_id: batch lookup function to set long ids by koddi id
            cache_short_id_by_long_id: batch lookup function to set short ids by long id
            handle_missing_long_ids: function to fetch and return missing long ids
            handle_missing_short_ids: function to fetch and return missing short ids

        Returns:
            A dictionary mapping koddi ids to short ids

        """
        current_ids = await self.__get_current_ids(
            koddi_ids,
            lookup_long_id_by_koddi_id,
            lookup_short_id_by_long_id
        )
        id_groups_by_koddi_id = self.__get_id_groups_by_koddi_id(current_ids)

        id_groups_by_koddi_id = await self.__fetch_missing_ids(
            id_groups_by_koddi_id,
            handle_missing_long_ids,
            handle_missing_short_ids
        )

        await self.__cache_missing_ids(
            current_ids,
            id_groups_by_koddi_id,
            cache_long_id_by_koddi_id,
            cache_short_id_by_long_id
        )

        return {
            koddi_id: id_group.short_id
            for koddi_id, id_group in id_groups_by_koddi_id.items()
            if koddi_id and id_group.short_id
        }

    async def build_ad_group_translation(
            self,
            koddi_ad_group_ids: Set[int],
    ) -> Dict[int, int]:
        return await self.build_translation(
            koddi_ad_group_ids,
            self.lookup.get_adgroup_long_id_by_koddi_id_batch,
            self.lookup.get_adgroup_short_id_by_long_id_batch,
            self.lookup.set_adgroup_long_id_by_koddi_id_batch,
            self.lookup.set_adgroup_short_id_by_long_id_batch,
            self.handle_missing_ad_group_long_ids,
            self.handle_missing_ad_group_short_ids
        )

    async def build_campaign_translation(
            self,
            koddi_campaign_ids: Set[int],
    ) -> Dict[int, int]:
        return await self.build_translation(
            koddi_campaign_ids,
            self.lookup.get_campaign_long_id_by_koddi_id_batch,
            self.lookup.get_campaign_short_id_by_long_id_batch,
            self.lookup.set_campaign_long_id_by_koddi_id_batch,
            self.lookup.set_campaign_short_id_by_long_id_batch,
            self.handle_missing_campaign_ids,
            self.handle_missing_campaign_ids
        )

    @staticmethod
    def build_advertiser_translation(
            koddi_advertiser_ids: Set[int],
            koddi_brand_ids: Dict[int, List[IdGroup]]
    ) -> Dict[int, int]:
        short_id_by_koddi_id = {}
        for koddi_id in koddi_advertiser_ids:
            id_groups = koddi_brand_ids.get(koddi_id)
            short_id = id_groups[0].short_id if id_groups and len(id_groups) > 0 else None
            if short_id:
                short_id_by_koddi_id[koddi_id] = short_id

        return short_id_by_koddi_id

    async def build_upc_translation(
            self,
            upcs: Set[str],
    ) -> Dict[str, int]:
        temp_bids = [
            Bid(id=upc)
            for upc in upcs
            if upc is not None
        ]
        bid_entities = await self.bid_manager_service.bind_bids_to_entity_ids(temp_bids)
        return {
            bid.id: entity_id
            for bid, entity_id in bid_entities
            if bid.id and entity_id
        }

    async def handle_missing_ad_group_long_ids(
            self,
            koddi_ids_missing_long_id: List[int],
            id_groups_by_koddi_id: Dict[int, IdGroup]
    ) -> Dict[int, IdGroup]:
        # Get activations for the koddi ids
        # Activation service does not currently have a search endpoint where we can pass in a list of koddi ids
        id_groups = {}
        for koddi_id in koddi_ids_missing_long_id:
            try:
                activation_response = await self.activation_gateway.get_activations(
                    ActivationsQueryBody(koddi_id=f"{koddi_id}")
                )
            except HTTPException as e:
                if e.status_code == httpx_codes.NOT_FOUND:
                    continue
                raise e

            if not activation_response.data or len(activation_response.data) == 0:
                continue
            activation = activation_response.data[0]
            id_groups[koddi_id] = IdGroup(
                koddi_id=koddi_id,
                long_id=activation.id,
                short_id=activation.metadata.short_id,
                data=activation
            )

        return id_groups

    async def handle_missing_ad_group_short_ids(
            self,
            koddi_ids_missing_short_id: List[int],
            id_groups_by_koddi_id: Dict[int, IdGroup]
    ) -> Dict[int, IdGroup]:
        # Get activations for long ids missing short ids
        long_ids_to_fetch = [
            id_groups_by_koddi_id.get(koddi_id).long_id
            for koddi_id in koddi_ids_missing_short_id
            if id_groups_by_koddi_id.get(koddi_id).long_id
        ]
        if not long_ids_to_fetch:
            return {}
        try:
            activation_response = await self.activation_gateway.get_activations(
                ActivationsQueryBody(ids=long_ids_to_fetch)
            )
        except HTTPException as e:
            if e.status_code == httpx_codes.NOT_FOUND:
                return {}
            raise e
        id_groups = {}
        for activation in activation_response.data:
            koddi_id = activation.metadata.externalIDs.get("KODDI")
            id_groups[koddi_id] = IdGroup(
                koddi_id=koddi_id,
                long_id=activation.id,
                short_id=activation.metadata.short_id,
                data=activation
            )

        return id_groups

    async def handle_missing_campaign_ids(
            self,
            koddi_ids_missing_id: List[int],
            id_groups_by_koddi_id: Dict[int, IdGroup],
    ) -> Dict[int, IdGroup]:
        try:
            campaigns_response = await self.campaign_gateway.search_campaigns(CampaignSearchRequest(
                externalPartner="KODDI_CAMPAIGN_ID",
                externalPartnerIDs=koddi_ids_missing_id
            ))
        except HTTPException as e:
            if e.status_code == httpx_codes.NOT_FOUND:
                return {}
            raise e
        id_groups = {}
        for campaign in campaigns_response.data:
            # Get the koddi id from the campaign's external ids
            koddi_external_id = next((
                externalId for externalId in campaign.externalIDs
                if externalId.partner == "KODDI_CAMPAIGN_ID"
            ), None)
            if koddi_external_id is None:
                continue
            koddi_id = koddi_external_id.id
            id_groups[koddi_id] = IdGroup(
                koddi_id=koddi_id,
                long_id=campaign.id,
                short_id=campaign.shortId,
                data=campaign
            )

        return id_groups

    async def __get_current_ids(
            self,
            koddi_ids: Set[int],
            lookup_long_id_by_koddi_id: Callable[[List[int]], Coroutine[Any, Any, List[str | None]]],
            lookup_short_id_by_long_id: Callable[[List[str]], Coroutine[Any, Any, List[int | None]]]
    ) -> List[Tuple[int, str | None, int | None]]:
        koddi_ids = list(koddi_ids)
        long_ids = await lookup_long_id_by_koddi_id(koddi_ids)
        short_ids = await lookup_short_id_by_long_id(long_ids)

        return list(zip(koddi_ids, long_ids, short_ids))

    @staticmethod
    def __get_id_groups_by_koddi_id(
            ids: List[Tuple[int, str | None, int | None]]
    ) -> Dict[int, IdGroup]:
        return {
            koddi_id: IdGroup(
                koddi_id=koddi_id,
                long_id=long_id,
                short_id=short_id
            )
            for koddi_id, long_id, short_id in ids
        }

    @staticmethod
    async def __cache_missing_ids(
            current_ids: List[Tuple[int, str | None, int | None]],
            id_groups_by_koddi_id: Dict[int, IdGroup],
            cache_long_id_by_koddi_id_batch: Callable[[Dict[int, str]], Coroutine[Any, Any, None]],
            cache_short_id_by_long_id_batch: Callable[[Dict[str, int]], Coroutine[Any, Any, None]],
    ):
        # For items that need to be cached, create lists of key values to cache
        long_ids_to_cache: list[tuple[int, str]] = []
        short_ids_to_cache: list[tuple[str, int]] = []
        for koddi_id, cached_long_id, cached_short_id in current_ids:
            id_group = id_groups_by_koddi_id.get(koddi_id)
            if cached_long_id is None and id_group.long_id:
                long_ids_to_cache.append((koddi_id, id_group.long_id))
            if cached_short_id is None and id_group.short_id and id_group.long_id:
                short_ids_to_cache.append((id_group.long_id, id_group.short_id))

        # Bind koddi_id -> long_id
        if long_ids_to_cache:
            await cache_long_id_by_koddi_id_batch({
                koddi_id: long_id
                for koddi_id, long_id in long_ids_to_cache
            })

        # Bind long_id -> short_id
        if short_ids_to_cache:
            await cache_short_id_by_long_id_batch({
                long_id: short_id
                for long_id, short_id in short_ids_to_cache
            })

    @staticmethod
    async def __fetch_missing_ids(
        id_groups_by_koddi_id: Dict[int, IdGroup],
        handle_missing_long_ids: Callable[[List[int], Dict[int, IdGroup]], Coroutine[Any, Any, Dict[int, IdGroup]]],
        handle_missing_short_ids: Callable[[List[int], Dict[int, IdGroup]], Coroutine[Any, Any, Dict[int, IdGroup]]],
    ) -> Dict[int, IdGroup]:
        # Get koddi ids that are missing long ids
        koddi_ids_missing_long_id = [
            koddi_id
            for koddi_id, id_group in id_groups_by_koddi_id.items()
            if not id_group.long_id
        ]
        if koddi_ids_missing_long_id:
            ids_to_update = await handle_missing_long_ids(
                koddi_ids_missing_long_id,
                deepcopy(id_groups_by_koddi_id)
            )

            id_groups_by_koddi_id = {
                **id_groups_by_koddi_id,
                **ids_to_update,
            }

        # Get koddi ids that are missing short ids
        koddi_ids_missing_short_id = [
            koddi_id
            for koddi_id, id_group in id_groups_by_koddi_id.items()
            if not id_group.short_id
        ]
        if koddi_ids_missing_short_id:
            ids_to_update = await handle_missing_short_ids(
                koddi_ids_missing_short_id,
                deepcopy(id_groups_by_koddi_id)
            )
            id_groups_by_koddi_id = {
                **id_groups_by_koddi_id,
                **ids_to_update,
            }

        return id_groups_by_koddi_id

    def build_missing_lookup_warnings(
            self,
            unique_response_ids: UniqueReportIds,
            external_ids: ExternalIdByKoddiId
    ) -> List[MissingLookupWarning]:
        missing_lookup_warnings = []

        missing_lookup_warnings.extend(self.__build_lookup_warning(
            Dimensions.ADVERTISER_ID,
            unique_response_ids.advertiser_ids,
            external_ids.advertiser
        ))

        missing_lookup_warnings.extend(self.__build_lookup_warning(
            Dimensions.AD_GROUP_ID,
            unique_response_ids.ad_group_ids,
            external_ids.ad_group
        ))

        missing_lookup_warnings.extend(self.__build_lookup_warning(
            Dimensions.CAMPAIGN_ID,
            unique_response_ids.campaign_ids,
            external_ids.campaign
        ))

        missing_lookup_warnings.extend(self.__build_lookup_warning(
            Dimensions.ENTITY_ID,
            unique_response_ids.upcs,
            external_ids.upc
        ))

        return missing_lookup_warnings

    @staticmethod
    def __build_lookup_warning(
            dimension: Dimensions,
            keys: Iterable,
            lookup: Dict,
    ) -> List[MissingLookupWarning]:
        missing_keys = [key for key in keys if key not in lookup]

        if not missing_keys:
            return []

        return [MissingLookupWarning(
            dimension=dimension,
            ids=missing_keys
        )]
