import asyncio
from collections import OrderedDict
from enum import StrEnum
from typing import List, Tuple

from fastapi import Depends, HTTPException

from app.common.gateways.campaign_service_gateway import CampaignServiceGateway
from app.common.gateways.creative_service_gateway import CreativeServiceGateway
from app.common.services.division_service import DivisionService
from app.common.services.lookup_service import LookupService
from app.common.services.target_service import TargetService
from app.common.view_models import (
    AdGroupStatus,
    EntitiesRequest,
    KeywordBidModifiersRequest,
    KeywordsResponse,
    ListResponse,
    SingleResponse,
    Entity,
    CreateEntitiesRequest,
)
from app.common.context.context import logging_extra_context
from app.common.gateways.activation_gateway import ActivationGateway
from app.v2.model.downstream.activation_service import (
    ActivationResponse,
    ActivationResponseV2,
    ActivationsQueryBody,
    ActivationStatus,
    ActivationUpdatePayload,
    ChannelData,
    ActivationPayload
)
from app.common.model.campaign_types import (
    InternalCampaignType,
)
from app.common.model.placement import PlacementType
from app.common.model.shared import (
    EntityMeta,
    KeywordsMeta,
    Meta,
    Page,
    PublishStatus,
)
from app.common.model.targets import TargetTypeId, TargetAdgroupRequest
from app.common.model.downstream.bid_manager import BidEntityFailure
from app.common.services.bid_manager_service import BidManagerService
from app.common.services.keyword_service import KeywordService
from app.common.services.placement_service import PlacementService
from app.common.utils import filtered_logger
from app.common.utils.activation_utils import ActivationPublicationUtils
from app.common.utils.bid_manager_errors import NO_KEYWORDS_FOUND
from app.common.utils.context_tools import update_context
from app.common.utils.date_utils import parse_date
from app.v2.services import CampaignService
from app.v2.translations.ad_group_translation import AdGroupTranslation
from app.v2.translations.error_translation import ErrorTranslation
from app.v2.translations.target_translation import TargetTranslation
from app.v2.utils.ad_group_validations import AdGroupRequestValidator
from app.v2.view_models import AdGroupV2Request, Campaign as CampaignV2, CreateAdGroupLegacyRequestV2
from app.v2.view_models.ad_group import AdGroupV2, AdGroupUpdateRequestV2, \
    SecretAdGroupUpdateRequest, AdGroupFromActivation

logger = filtered_logger.get_logger(__name__)

class PatchAction(StrEnum):
    APPROVE = "approve"
    PAUSE = "pause"
    UNPAUSE = "unpause"

MAP_PATCH_ACTIONS =  {
    AdGroupStatus.ACTIVE: PatchAction.APPROVE,
    AdGroupStatus.SCHEDULED: PatchAction.APPROVE,
    AdGroupStatus.PAUSED: PatchAction.PAUSE,
    AdGroupStatus.ENDED: PatchAction.UNPAUSE,
    AdGroupStatus.DRAFT: PatchAction.APPROVE,

}

class AdGroupService:
    """
    V2 Ad Group Service
    Supports the V2 Ad Group Controller and orchestrates calls to other services and the activation gateway.
    """

    lookup: LookupService
    activation_gateway: ActivationGateway
    ad_group_translation: AdGroupTranslation
    bid_manager_service: BidManagerService
    keyword_service: KeywordService
    campaign_gateway: CampaignServiceGateway
    placement_service: PlacementService
    campaign_service: CampaignService
    target_service: TargetService
    division_service: DivisionService
    request_validator: AdGroupRequestValidator
    target_translation: TargetTranslation
    error_translation: ErrorTranslation
    __activation_publication_utils: ActivationPublicationUtils

    def __init__(
            self,
            lookup: LookupService = Depends(LookupService),
            activation_gateway: ActivationGateway = Depends(ActivationGateway),
            ad_group_translation: AdGroupTranslation = Depends(AdGroupTranslation),
            bid_manager_service: BidManagerService = Depends(BidManagerService),
            keyword_service: KeywordService = Depends(KeywordService),
            campaign_gateway: CampaignServiceGateway = Depends(CampaignServiceGateway),
            creative_gateway: CreativeServiceGateway = Depends(CreativeServiceGateway),
            placement_service: PlacementService = Depends(PlacementService),
            division_service: DivisionService = Depends(DivisionService),
            campaign_service: CampaignService = Depends(CampaignService),
            target_translation: TargetTranslation = Depends(TargetTranslation),
            error_translation: ErrorTranslation = Depends(ErrorTranslation)
    ):
        self.lookup = lookup
        self.activation_gateway = activation_gateway
        self.ad_group_translation = ad_group_translation
        self.bid_manager_service = bid_manager_service
        self.keyword_service = keyword_service
        self.campaign_gateway = campaign_gateway
        self.placement_service = placement_service
        self.campaign_service = campaign_service
        self.division_service = division_service
        self.request_validator = AdGroupRequestValidator()
        self.target_translation = target_translation
        self.error_translation = error_translation
        self.__activation_publication_utils = ActivationPublicationUtils(creative_service_gateway=creative_gateway)

    async def get_ad_group_by_id(
            self,
            ad_group_id: int
    ) -> SingleResponse[AdGroupV2]:
        """
        Get an ad group by id and return a single ad group response
        """
        update_context(context_var=logging_extra_context, ad_group_id=ad_group_id)
        activation_response = await self.__get_activation_by_ad_group_id(ad_group_id)
        short_campaign_id = await self.lookup.get_campaign_short_id_by_long_id(activation_response.data.campaign_id)
        campaign = await self.campaign_service.get_campaign_single_response_by_id(
           short_campaign_id
        )
        brand_codes = await self.__get_brand_codes_from_advertisers(campaign.data)
        return await self.__activation_to_single_ad_group_response(activation_response, brand_codes)

    async def __activation_to_single_ad_group_response(
            self,
            activation_response: ActivationResponseV2[ActivationResponse],
            brand_codes: List[str] = None
    ) -> SingleResponse[AdGroupV2]:
        ad_group_from_activation = await self.ad_group_translation.ad_group_from_activation(
            activation_response.data,
            brand_codes
        )
        ad_group = ad_group_from_activation.adGroup
        ad_group_errors = ad_group_from_activation.entityErrors
        warnings = self.ad_group_translation.warnings_from_activation_warnings(activation_response.warnings)
        errors = map(lambda x: x.model_dump(), activation_response.errors) if activation_response.errors else []
        errors = await self.ad_group_translation.adgroup_errors_map_identifier_long_id_to_short_id(list(errors))
        publish_status = self.ad_group_translation.publish_status_from_activation(activation_response.data)

        response = SingleResponse[AdGroupV2](
            data=ad_group,
            meta=EntityMeta(
                success=True,
                warnings=warnings,
                errors=errors,
                publishStatus=publish_status,
                code=None,
                message=None,
            ),
        )
        if ad_group_errors:
            response.meta.errors.extend([e.model_dump(exclude_none=True) for e in ad_group_errors])
        return response

    async def __get_activation_by_ad_group_id(self, ad_group_id: int) -> ActivationResponseV2[ActivationResponse]:
        activation_id = await self.lookup.get_adgroup_long_id_by_short_id(ad_group_id)
        if activation_id is None:
            logger.warning("Activation not found for ad_group_id: %s", ad_group_id)
            raise HTTPException(status_code=404, detail="Ad group not found")
        return await self.activation_gateway.get_activation_by_id(activation_id)

    async def __get_brand_codes_from_advertisers(self, campaign: CampaignV2) -> List[str]:
        advertiser_ids = campaign.advertiserIds
        advertiser_details = await self.lookup.get_advertiser_details_by_short_ids(
            advertiser_ids
        )
        brand_codes = [
            advertiser.displayName
            for advertiser in advertiser_details
        ]
        return brand_codes

    async def update_entities(
            self,
            ad_group_id: int,
            entities_request: EntitiesRequest
    ) -> SingleResponse[AdGroupV2]:
        activation_response = await self.__get_activation_by_ad_group_id(ad_group_id)
        if isinstance(entities_request, CreateEntitiesRequest) \
            and activation_response.data.channel_data.get("biddableEntities"):
            raise HTTPException(status_code=409, detail="Entities already exist")

        if activation_response.data.status == ActivationStatus.ENDED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update ad group with {activation_response.data.status} status"
            )

        bid_group_id = await self.bid_manager_service.update_entities(
            activation_response,
            entities_request
        )
        entity_errors = []
        short_campaign_id = await self.lookup.get_campaign_short_id_by_long_id(activation_response.data.campaign_id)
        campaign = await self.campaign_service.get_campaign_single_response_by_id(short_campaign_id)
        brand_codes = await self.__get_brand_codes_from_advertisers(campaign.data)
        if bid_group_id:
            validation_request = self.ad_group_translation.validation_request_from_activation(
                activation_response,
                brand_codes=brand_codes
            )
            entity_errors = await self.bid_manager_service.validate_bid(
                bid_group_id,
                validation_request
            )

        activation_update_payload = ActivationUpdatePayload(
            channel_data=ChannelData(
                biddableEntities=[bid_group_id] if bid_group_id else []
            )
        )

        updated_activation_response, publish_status = await self.__update_and_publish_activation(
            activation_update_payload,
            activation_response.data.id
        )

        updated_ad_group = await self.__activation_to_single_ad_group_response(
            updated_activation_response,
        )
        updated_ad_group.meta.publishStatus = publish_status
        updated_ad_group.meta.errors.extend([e.model_dump(exclude_none=True) for e in entity_errors])
        return updated_ad_group

    async def get_ad_groups_by_campaign_id(
            self,
            campaign_id: int | None,
            include_ad_group_errors: bool = False
    ) -> ListResponse[AdGroupV2]:
        if campaign_id is None:
            raise HTTPException(status_code=400, detail="Campaign ID is required")

        internal_campaign_id = await self.campaign_service.get_campaign_long_id(
            campaign_id
        )
        await self.campaign_gateway.get_campaign(internal_campaign_id)

        get_activations_params = ActivationsQueryBody(campaign_ids=[internal_campaign_id])
        activations_response = await self.activation_gateway.get_activations(get_activations_params)

        ad_groups_details = {
           item.id: int(item.metadata.short_id) for item in activations_response.data
        }
        await self.ad_group_translation.cache_ad_groups_by_short_id(ad_groups_details)
        await self.ad_group_translation.cache_ad_groups_by_long_id(ad_groups_details)

        ad_groups_info: List[AdGroupFromActivation] = await asyncio.gather(*[
            self.ad_group_translation.ad_group_from_activation(activation)
            for activation in activations_response.data
        ])
        ad_groups = [ad_group.adGroup for ad_group in ad_groups_info]
        response = ListResponse[AdGroupV2](
            data=ad_groups,
            meta=Meta(page=Page(
                offset=0,
                size=len(ad_groups),
                hasMore=False
            ))
        )

        if include_ad_group_errors:
            errors = await self.error_translation.errors_from_ad_groups_info(
                ad_groups_info=ad_groups_info,
                activations_response=activations_response
            )
            warnings = await self.error_translation.warnings_from_ad_groups_info(
                ad_groups_info=ad_groups_info,
                activations_response=activations_response
            )
            response.errors = errors
            response.warnings = warnings

        return response

    async def get_keywords_by_ad_group_id(
            self,
            ad_group_id: int
    ) -> KeywordsResponse:
        """
        Get keywords by ad group id
        """
        activation_response = await self.__get_activation_by_ad_group_id(ad_group_id)
        campaign_type = self.ad_group_translation.get_campaign_type(activation_response.data)
        if campaign_type != InternalCampaignType.PLA:
            raise HTTPException(status_code=400, detail="Ad group must be in PLA type campaign to have keyword bids")
        entities = await self.bid_manager_service.get_upcs_by_bid_group_id(
            activation_response.data.channel_data.get("biddableEntities", []),
            activation_response.data.channel_config.type,
        )
        eligible_keywords = await self.keyword_service.get_eligible_keywords_from_upcs(entities)

        size = len(eligible_keywords)
        return KeywordsResponse(
            data=list[str](eligible_keywords),
            meta=KeywordsMeta(size=size, message=NO_KEYWORDS_FOUND if size == 0 else None),
        )

    async def __apply_triggered_action(
            self,
            activation_response:ActivationResponseV2[ActivationResponse],
            internal_activation_id: str,
            action: PatchAction
    ) -> ActivationResponseV2[ActivationResponse] | None:
        logger.info("Patch activation. Action: %s with id: %s", action.value, internal_activation_id)
        if action == PatchAction.APPROVE:
            if activation_response.warnings or activation_response.errors:
                return activation_response
        method = getattr(self.activation_gateway, f"{action.value.lower()}_activation", None)
        if method:
            activation = await method(internal_activation_id)
            update_context(logging_extra_context, activation_patch_response=activation.model_dump())
            return activation
        logger.warning("Activation response of an unexpected shape.")
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action.value}")

    async def __build_bid_object(
            self,
            entities_request: List[Entity],
            campaign_type: InternalCampaignType,
            base_bid_request: float,
            placement_types: List[str],
            brand_codes: List[str]
    ) -> tuple[str | None, List[BidEntityFailure]]:
        bid_recommendations_id = await self.bid_manager_service.create_bids_from_entities(
            entities=list(OrderedDict.fromkeys(entities_request)),
            campaign_type=campaign_type,
            base_bid=base_bid_request,
        )
        if campaign_type == InternalCampaignType.CAROUSEL:
            placement_types = [PlacementType.SEARCH_AND_BROWSE_PPC.value]
        validation_request = self.bid_manager_service.build_validation_request(
            placement_types=placement_types,
            campaign_type=campaign_type,
            brand_codes=brand_codes
        )
        entity_errors = await self.bid_manager_service.validate_bid(bid_recommendations_id, validation_request)
        logger.info('Bid Recommendations ID: %s', bid_recommendations_id)
        return bid_recommendations_id, entity_errors


    async def __approve_and_publish_ad_group(
            self,
            ad_group_request_status: AdGroupStatus,
            activation: ActivationResponseV2[ActivationResponse],
            long_activation_id: str
    ) -> None:
        patch_action = MAP_PATCH_ACTIONS.get(ad_group_request_status, None)
        if ad_group_request_status == AdGroupStatus.ACTIVE and activation.data.status == ActivationStatus.PAUSED:
            # Special Case
            patch_action = PatchAction.UNPAUSE
        if not patch_action:
            logger.error(f"Unsupported ad group status to approve ad group: {ad_group_request_status.value}")
            raise HTTPException(400, f"Unsupported ad group status: {ad_group_request_status.value}")
        activation_status_result = await self.__apply_triggered_action(activation, long_activation_id, patch_action)
        logger.info(f'{ad_group_request_status}activation Result: {activation_status_result}')
        await self.__publish_activation_if_publishable(activation_response=activation_status_result)

    async def create_ad_group(
            self,
            ad_group_request: AdGroupV2Request
    ) -> SingleResponse[AdGroupV2]:
        campaign_response: SingleResponse[CampaignV2] = (
            await self.campaign_service.get_campaign_single_response_by_id(
                ad_group_request.campaignId
            )
        )
        internal_campaign_id: str = (
            await self.lookup.get_campaign_long_id_by_internal_short_id(
                ad_group_request.campaignId
            )
        )
        campaign = campaign_response.data
        campaign_type = campaign.campaignType
        if internal_campaign_id is None:
            raise HTTPException(status_code=404, detail="Failed to find campaign ID")

        ad_group_start_date = parse_date(ad_group_request.startDate)

        ad_group_end_date = None

        if ad_group_request.endDate is not None:
            ad_group_end_date = parse_date(ad_group_request.endDate)

        carousel_campaign_flow = campaign_type == InternalCampaignType.CAROUSEL

        ad_group_placement_targets, ad_group_division_targets, ad_group_day_parting_targets = self.target_translation.\
            fetch_ad_group_targets(
                ad_group_request.targets,
                carousel_campaign_flow,
            )
        self.request_validator.validate_ad_group_targets(
            ad_group_placement_targets,
            ad_group_division_targets,
            ad_group_day_parting_targets,
            carousel_campaign_flow
        )
        self.request_validator.validate_ad_group_request_single_call(
            ad_group_request,
            campaign
        )
        ad_group_placements = await self.target_translation.build_placements_types(ad_group_placement_targets)
        brand_codes = await self.__get_brand_codes_from_advertisers(campaign_response.data)

        bid_recommendations_id = None
        if isinstance(ad_group_request, CreateAdGroupLegacyRequestV2):
            bid_recommendations_id, _ = (
                await self.__build_bid_object(
                    entities_request=ad_group_request.entities,
                    campaign_type=campaign_type,
                    base_bid_request=ad_group_request.baseBid,
                    placement_types=ad_group_placements,
                    brand_codes=brand_codes
                )
            )
        location_group_id = await self.division_service.build_location_group(
            ad_group_division_targets
        )

        activation_payload: ActivationPayload = self.ad_group_translation.build_activation_payload(
            ad_group_request=ad_group_request,
            budget_type=campaign.budgetType.capitalize(),
            bid_recommendations_id=bid_recommendations_id,
            location_group_id=location_group_id,
            internal_campaign_id=internal_campaign_id,
            placements=ad_group_placements,
            campaign_type=campaign_type,
            start_date=ad_group_start_date,
            end_date=ad_group_end_date,
            day_parting_target=None \
                                if len(ad_group_day_parting_targets) == 0 \
                                else ad_group_day_parting_targets[0]
        )
        logger.info(
            "Creating activation with payload: %s", activation_payload.model_dump()
        )
        activation = await self.activation_gateway.create_activation(activation_payload)

        if activation.data.id:
            long_activation_id = activation.data.id
        else:
            raise HTTPException(status_code=500, detail="Failed to create activation")

        logger.info("Internal activation id: %s", long_activation_id)

        ad_group_id = int(activation.data.metadata.short_id)

        logger.info("Activation Id: %s", ad_group_id)

        await self.__approve_and_publish_ad_group(
            ad_group_request.status, activation, long_activation_id
        )
        response = await self.get_ad_group_by_id(ad_group_id)
        return response

    async def get_campaign_by_ad_group_id(self, ad_group_id: int) -> CampaignV2:
        """
        Get campaign by short ad group id
        TODO: optimize redis calls
        In the new campaign service v2, we should be able to get campaign by long id
        This would save us at least 2 extra redis calls, since old campaign service
        converts the short id back into a long id...

        Honestly, this should probably be a function in campaign service v2.
        """
        cached_campaign_long_id = (
            await self.lookup.get_campaign_long_id_by_short_adgroup_id(ad_group_id)
        )

        if cached_campaign_long_id is None:
            activation_response = await self.__get_activation_by_ad_group_id(
                ad_group_id
            )
            cached_campaign_long_id = activation_response.data.campaign_id
            await self.lookup.set_campaign_long_id_by_short_adgroup_id(
                ad_group_id, cached_campaign_long_id
            )

        cached_campaign_short_id = await self.lookup.get_campaign_short_id_by_long_id(
            cached_campaign_long_id
        )

        campaign_response: SingleResponse[CampaignV2] = await (self.campaign_service
            .get_campaign_single_response_by_id(
            cached_campaign_short_id
        ))
        return campaign_response.data

    async def update_ad_group(
            self,
            ad_group_id: int,
            ad_group_update_request: AdGroupUpdateRequestV2 | SecretAdGroupUpdateRequest,
    ) -> SingleResponse[AdGroupV2]:
        internal_activation_id = await self.lookup.get_adgroup_long_id_by_short_id(ad_group_id)
        if not internal_activation_id:
            raise HTTPException(404, detail="Ad group not found")
        ad_group_response: SingleResponse[AdGroupV2] = await self.get_ad_group_by_id(ad_group_id)
        campaign: CampaignV2 = await self.get_campaign_by_ad_group_id(ad_group_id)
        original_ad_group = ad_group_response.data
        campaign_type = campaign.campaignType
        location_group_id = ""
        keyword_bid_modifier_group_id = ""
        keywords_warnings = None

        if isinstance(ad_group_update_request, SecretAdGroupUpdateRequest):
            ad_group_update_request.budgetType = self.ad_group_translation.\
                set_budget_type_for_secret_ad_group(
                    ad_group_update_request
                )

        ad_group_model = self.ad_group_translation.parse_ad_group_update_request(ad_group_update_request)

        updated_ad_group = AdGroupV2.model_validate(
            original_ad_group.model_copy(
                update=ad_group_model
            ).model_dump(exclude_none=True)
        )

        updated_ad_group_dict = updated_ad_group.model_dump(exclude={"adGroupId", "campaignId"})
        has_changes = updated_ad_group_dict != original_ad_group.model_dump(exclude={"adGroupId", "campaignId"})

        if not has_changes:
            return ad_group_response

        carousel_campaign_flow = campaign_type == InternalCampaignType.CAROUSEL

        ad_group_placement_targets,ad_group_division_targets, ad_group_day_parting_targets = \
            self.target_translation.fetch_ad_group_targets(
                [TargetAdgroupRequest(**request_target.model_dump()) for request_target in updated_ad_group.targets],
                carousel_campaign_flow
            )
        self.request_validator.validate_ad_group_targets(
            ad_group_placement_targets,
            ad_group_division_targets,
            ad_group_day_parting_targets,
            carousel_campaign_flow
        )

        ad_group_placements = await self.target_translation.build_placements_types(ad_group_placement_targets)
        if ad_group_division_targets:
            location_group_id = await self.division_service.build_location_group(ad_group_division_targets)

        self.request_validator.validate_ad_group_request_single_call(
            updated_ad_group,
            campaign
        )

        self.request_validator.extra_validations_for_update(
            updated_ad_group,
            original_ad_group,
            ad_group_placements,
            campaign_type
        )

        if updated_ad_group.keywordBidModifiers:
            if updated_ad_group.keywordBidModifiers != original_ad_group.keywordBidModifiers:
                keyword_bid_modifier_group_id, keywords_warnings = await self.keyword_service.update_keywords(
                    original_ad_group,
                    updated_ad_group.keywordBidModifiers
                )

        activation_update_payload = self.ad_group_translation.build_update_activation_payload(
            updated_ad_group_dict,
            ad_group_placements,
            keyword_bid_modifier_group_id,
            location_group_id,
            ad_group_day_parting_targets,
            campaign_type
        )
        activation_response = await self.activation_gateway.update_activation(
            activation_update_payload,
            internal_activation_id
        )
        internal_activation_data = activation_response.data
        internal_activation_id = internal_activation_data.id
        logger.info("Updated activation ID: %s", internal_activation_id)
        await self.__approve_and_publish_ad_group(
            updated_ad_group.status, activation_response, internal_activation_id
        )
        response = await self.get_ad_group_by_id(ad_group_id)
        if keywords_warnings:
            response.meta.warnings.validation.extend(keywords_warnings)
        return response

    async def validate_keywords_updatable(
            self,
            ad_group_response: SingleResponse[AdGroupV2],
            campaign_type: InternalCampaignType = InternalCampaignType.PLA,
    ) -> bool:
        if campaign_type != InternalCampaignType.PLA:
            raise HTTPException(status_code=400, detail="Ad group must be in PLA type campaign to have keyword bids")

        if ad_group_response.data.status == AdGroupStatus.ENDED:
            raise HTTPException(
                status_code=400, detail=f"Cannot update/get keywords ad group with {ad_group_response.data.status} status"
            )

        # Validate Search and Browse is present
        if ad_group_response.data.targets is None or len(ad_group_response.data.targets) <= 0:
            raise HTTPException(
                status_code=400, detail="Must have Search and Browse Placement to add keyword modifiers"
            )

        contains_search_and_browse = False
        for target in ad_group_response.data.targets:
            if int(target.type) == TargetTypeId.PLACEMENT.value:
                placement = await self.placement_service.get_cache_placement(target.id)
                if placement["name"] == PlacementType.SEARCH_AND_BROWSE.value:
                    contains_search_and_browse = True
                    break

        if not contains_search_and_browse:
            raise HTTPException(
                status_code=400, detail="Must have Search and Browse Placement to add keyword modifiers"
            )

        return True

    async def update_ad_group_keyword_bid_modifiers(
            self,
            ad_group_id: int,
            keyword_bid_modifiers_request: KeywordBidModifiersRequest
    ) -> SingleResponse[AdGroupV2]:
        activation_response = await self.__get_activation_by_ad_group_id(ad_group_id)
        ad_group_response = await self.__activation_to_single_ad_group_response(activation_response)
        logger.info("Ad group: %s", ad_group_response.data)

        campaign_type = self.ad_group_translation.get_campaign_type(activation_response.data)
        await self.validate_keywords_updatable(ad_group_response, campaign_type)

        keyword_bid_modifier_group_id, warnings = await self.keyword_service.update_keywords(
            ad_group_response.data,
            keyword_bid_modifiers_request.keywordBidModifiers
        )

        activation_id = activation_response.data.id
        update_activation_payload = ActivationUpdatePayload(
            channel_data=ChannelData(
                keywordBidModifierGroup=keyword_bid_modifier_group_id
            )
        )
        updated_activation_response, publish_status = await self.__update_and_publish_activation(
            update_activation_payload,
            activation_id
        )
        campaign = await self.campaign_service.get_campaign_single_response_by_id(
            ad_group_response.data.campaignId
        )
        brand_codes = await self.__get_brand_codes_from_advertisers(campaign.data)
        updated_ad_group = await self.__activation_to_single_ad_group_response(updated_activation_response, brand_codes)
        updated_ad_group.meta.warnings.validation.extend(warnings)
        updated_ad_group.meta.publishStatus = publish_status

        return updated_ad_group

    async def __publish_activation_if_publishable(
            self,
            activation_response: ActivationResponseV2[ActivationResponse],
            ad_group_current_status=None,
            ad_group_requested_status=None) -> PublishStatus | None:

        if await self.__activation_publication_utils.activation_is_publishable(
                activation_response=activation_response,
                ad_group_current_status=ad_group_current_status,
                ad_group_requested_status=ad_group_requested_status):
            activation = activation_response.data
            try:
                published_activation = await self.activation_gateway.publish_activation(activation.id)
                logger.info("Published activation response: %s", published_activation)
                return self.ad_group_translation.publish_status_from_activation(activation)
            except HTTPException as e:
                logger.error(
                    "Activation API publishing call returned error for activation id %s: %s",
                    activation.id,
                    str(e),
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Publishing failed for activation id {activation_response.data.id} "
                           f"with error: {str(e)}",
                ) from e

        logger.info("Activation %s is not publishable; skipping publication",
                    activation_response.data.id)
        return None

    async def __update_and_publish_activation(
            self,
            update_activation_payload: ActivationUpdatePayload,
            activation_id: str
    ) -> Tuple[ActivationResponseV2[ActivationResponse], PublishStatus]:
        updated_activation_response = await self.activation_gateway.update_activation(
            update_activation_payload,
            activation_id
        )
        last_publish_action_status = await self.__publish_activation_if_publishable(
            updated_activation_response
        )

        publish_status = last_publish_action_status \
            if last_publish_action_status is not None \
            else self.ad_group_translation.publish_status_from_activation(updated_activation_response.data)

        return updated_activation_response, publish_status
