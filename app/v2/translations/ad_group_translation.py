from datetime import datetime
from typing import List

from fastapi import Depends, HTTPException

from app.common.services.lookup_service import LookupService
from app.common.view_models import Entity, KeywordBidModifier, AdGroupStatus
from app.common.context.context import logging_extra_context
from app.v2.model.downstream.activation_service import (
    ActivationResponse,
    ActivationResponseV2,
    ActivationPayload,
    ActivationUpdatePayload
)
from app.common.model.downstream.bid_manager import ValidateBidRequest, BidEntityFailure
from app.common.model.campaign_types import (
    InternalCampaignType
)
from app.common.model.placement import PlacementType
from app.common.model.shared import (
    ActivationPublishStatus,
    ActivationWarnings,
    BudgetType,
    PublishStatus,
    UpstreamValidationWarning,
    Warnings,
    InternalBudgetType,
)
from app.common.model.targets import Target, TargetAdgroupRequest
from app.common.services.bid_manager_service import BidManagerService
from app.common.services.keyword_service import KeywordService
from app.common.utils import filtered_logger
from app.common.utils.bid_ranges import get_bid_ranges
from app.common.utils.context_tools import update_context
from app.v2.translations.target_translation import TargetTranslation
from app.v2.view_models import AdGroupFromActivation
from app.v2.view_models.ad_group import (
    AdGroupV2,
    SecretAdGroupUpdateRequest,
    AdGroupV2Request,
    AdGroupUpdateRequestV2
)

logger = filtered_logger.get_logger(__name__)

class AdGroupTranslation:
    bid_manager_service: BidManagerService
    lookup: LookupService
    target_translation: TargetTranslation
    keyword_service: KeywordService

    def __init__(
            self,
            bid_manager_service: BidManagerService = Depends(BidManagerService),
            lookup: LookupService = Depends(LookupService),
            target_translation: TargetTranslation = Depends(TargetTranslation),
            keyword_service: KeywordService = Depends(KeywordService)
    ):
        self.bid_manager_service = bid_manager_service
        self.lookup = lookup
        self.target_translation = target_translation
        self.keyword_service = keyword_service

    async def ad_group_from_activation(self, activation: ActivationResponse, brand_codes: list[str]=None) -> AdGroupFromActivation:
        validation_response = await self.bid_manager_service.get_valid_entries(activation, brand_codes)
        entities = validation_response.filtered_entities
        base_bid = validation_response.default_bid
        entities_errors = validation_response.errors
        targets = await self.target_translation.targets_from_activation(activation)
        keyword_bid_modifier_group_id = activation.channel_data.get("keywordBidModifierGroup")
        keyword_bid_modifiers = await self.keyword_service.get_bid_modifiers(keyword_bid_modifier_group_id)
        budget_type = self.__determine_budget_type(activation)
        is_archived = activation.metadata.is_archived

        ad_group = await self.__create_ad_group(
            activation,
            budget_type,
            base_bid,
            entities,
            targets,
            keyword_bid_modifiers,
            is_archived,
        )
        return AdGroupFromActivation[AdGroupV2](adGroup=ad_group, entityErrors=entities_errors)

    @staticmethod
    def __determine_budget_type(activation: ActivationResponse) -> BudgetType | None:
        if channel_data := activation.channel_data:
            budget_type_upstream = channel_data.get("budgetType")
            budget_type = budget_type_upstream.upper() if budget_type_upstream else None
            if budget_type == 'CUSTOM':
                budget_type = 'LIFETIME'
            return budget_type
        return None

    async def __create_ad_group(
            self,
            activation: ActivationResponse,
            budget_type: BudgetType | None,
            base_bid: float,
            entities: List[Entity],
            targets: List[Target],
            keyword_bid_modifiers: List[KeywordBidModifier],
            is_archived: bool
    ) -> AdGroupV2:
        ad_group_id = await self.lookup.get_adgroup_short_id_by_long_id(activation.id)
        campaign_id = await self.lookup.get_campaign_short_id_by_long_id(activation.campaign_id)

        update_context(
            context_var=logging_extra_context,
            ad_group_id=ad_group_id,
            campaign_id=campaign_id,
            activation_id=activation.id)
        channel_data = activation.channel_data

        if channel_data is not None:
            return AdGroupV2(
                adGroupId=ad_group_id,
                campaignId=campaign_id,
                name=channel_data.get("name"),
                startDate=channel_data.get("startDate"),
                endDate=channel_data.get("endDate"),
                budgetType=budget_type,
                budgetAmount=channel_data.get("budgetAmount"),
                status=AdGroupStatus(activation.status.value.upper()),
                baseBid=base_bid,
                entities=entities,
                targets=targets,
                keywordBidModifiers=keyword_bid_modifiers,
                isArchived=is_archived,
                carouselHeadline=channel_data.get("carouselHeadline"),
                carouselSubtext=channel_data.get("carouselSubtext")
            )

        logger.warning(
            "Bad upstream ad group data.", extra={
                "monitored_transaction": "BAD-UPSTREAM-AD-GROUP-DATA",
                "upstream_ad_group_data": activation
            })

        raise HTTPException(
            status_code=500, detail="Bad upstream ad group data. Please contact support if problem persists.")

    @staticmethod
    def warnings_from_activation_warnings(activation_warnings: List[ActivationWarnings]) -> Warnings:
        """
        Converts activation warnings to view model warnings
        """
        validation_warnings = (
            list(
                map(
                    UpstreamValidationWarning.from_upstream_activation_validations,
                    activation_warnings,
                )
            )
            if activation_warnings
            else []
        )
        return Warnings(validation=validation_warnings)

    @staticmethod
    def publish_status_from_activation(activation: ActivationResponse) -> PublishStatus:
        """
        Extracts the publish status from an activation
        """
        if (
                not activation.unpublished_data
                and activation.metadata.last_publish_result == ActivationPublishStatus.SUCCESS
        ):
            publish_status = PublishStatus.PUBLISHED
        elif (
                activation.unpublished_data
                and activation.metadata.last_publish_result == ActivationPublishStatus.FAILURE
        ):
            publish_status = PublishStatus.FAILED
        elif activation.unpublished_data:
            publish_status = PublishStatus.PENDING
        else:
            publish_status = PublishStatus.EMPTY

        return publish_status

    @staticmethod
    def get_campaign_type(activation: ActivationResponse) -> InternalCampaignType:
        return activation.channel_config.type

    @staticmethod
    def validation_request_from_activation(
            activation_response: ActivationResponseV2[ActivationResponse],
            brand_codes: List[str]
    ) -> ValidateBidRequest:
        activation_id = activation_response.data.id
        activation_config = activation_response.included.configuration_by_activation.get(activation_id)
        min_price = activation_config.biddableEntities.min_bid_amount
        max_price = activation_config.biddableEntities.max_bid_amount
        validation_request = ValidateBidRequest(
            minimumBidAmount=min_price,
            maximumBidAmount=max_price,
            bidIdsMustHaveValidEntities=True,
            brandCodes=brand_codes
        )

        campaign_type = AdGroupTranslation.get_campaign_type(activation_response.data)
        if campaign_type == InternalCampaignType.CAROUSEL:
            carousel_validation = (
                get_bid_ranges()
                .get(InternalCampaignType.CAROUSEL, {})
                .get(PlacementType.SEARCH_AND_BROWSE_PPC)
            )
            validation_request.minimumBidCount = carousel_validation.minimumBidCount
            validation_request.maximumBidCount = carousel_validation.maximumBidCount

        return validation_request

    @staticmethod
    def set_budget_type_for_secret_ad_group(ad_group_request: SecretAdGroupUpdateRequest) -> InternalBudgetType | BudgetType:
        budget_type = ad_group_request.budgetType.upper()
        if budget_type == BudgetType.LIFETIME:
            return InternalBudgetType.CUSTOM.capitalize()
        return ad_group_request.budgetType

    @staticmethod
    def parse_ad_group_update_request(ad_group_update_request: AdGroupUpdateRequestV2) -> dict:
        targets = ad_group_update_request.targets
        keywords = ad_group_update_request.keywordBidModifiers
        ad_group_model = ad_group_update_request.model_dump(exclude_unset=True)
        if targets:
            ad_group_model["targets"] = targets
        if keywords:
            ad_group_model["keywordBidModifiers"] = keywords
        return ad_group_model

    @staticmethod
    def build_activation_payload(
            ad_group_request: AdGroupV2Request,
            budget_type: str,
            bid_recommendations_id: str | None,
            location_group_id: str,
            internal_campaign_id: str,
            placements: List[str],
            campaign_type: InternalCampaignType,
            start_date: datetime,
            end_date: datetime | None = None,
            day_parting_target: TargetAdgroupRequest | None = None
    ) -> ActivationPayload:
        if campaign_type == InternalCampaignType.CAROUSEL:
            placements = [PlacementType.SEARCH_AND_BROWSE_PPC]
        payload = {
            "channel_data": {
                "carouselHeadline": ad_group_request.carouselHeadline,
                "name": ad_group_request.name,
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d") if end_date is not None else None,
                "alwaysOn": not end_date,
                "budgetType": (
                    InternalBudgetType.CUSTOM.capitalize()
                    if budget_type == BudgetType.LIFETIME
                    else budget_type.capitalize()
                ),
                "budgetAmount": ad_group_request.budgetAmount,
                "divisionBanners": [
                    location_group_id
                ],
                "placementType": placements
            },
            "channel_config": {
                "type": campaign_type,
                "version": "1"
            },
            "campaign_id": internal_campaign_id
        }
        if bid_recommendations_id:
            payload['channel_data']['biddableEntities'] = [bid_recommendations_id]
        if day_parting_target is not None:
            payload["channel_data"]["dayPartingStart"] = int(day_parting_target.values[0])
            payload["channel_data"]["dayPartingEnd"] = int(day_parting_target.values[1])

        if ad_group_request.carouselSubtext:
            payload["channel_data"]["carouselSubtext"] = ad_group_request.carouselSubtext

        return ActivationPayload(**payload)


    @staticmethod
    def build_update_activation_payload(
            updated_ad_group_dict: dict,
            ad_group_placements: list[str],
            keyword_bid_modifier_group_id: str,
            location_group_id: str,
            ad_group_day_parting_targets: list[TargetAdgroupRequest],
            campaign_type: InternalCampaignType
    ) -> ActivationUpdatePayload:
        updated_ad_group_dict.update({"alwaysOn": updated_ad_group_dict["endDate"] is None})
        if campaign_type == InternalCampaignType.CAROUSEL:
            updated_ad_group_dict["placementType"] = [PlacementType.SEARCH_AND_BROWSE_PPC]
        elif ad_group_placements:
            updated_ad_group_dict["placementType"] = ad_group_placements

        if keyword_bid_modifier_group_id:
            updated_ad_group_dict["keywordBidModifierGroup"] = keyword_bid_modifier_group_id
        if ad_group_day_parting_targets:
            updated_ad_group_dict["dayPartingStart"] = int(ad_group_day_parting_targets[0].values[0])
            updated_ad_group_dict["dayPartingEnd"] = int(ad_group_day_parting_targets[0].values[1])
        # TODO: What happens if you created the ad group with dayParting can it be removed or just modified?
        if location_group_id:
            updated_ad_group_dict["divisionBanners"] = [location_group_id]

        payload = {
            "channel_data": updated_ad_group_dict
        }
        updated_ad_group_dict["budgetType"] = updated_ad_group_dict["budgetType"].capitalize()
        activation_update_payload = ActivationUpdatePayload(**payload)
        return  activation_update_payload

    async def adgroup_errors_map_identifier_long_id_to_short_id(self, ad_group_errors: list):
        """
        Maps the identifier of ad group errors from long id to short id.
        eg: error = {'code': 'biddableEntities', 'reason': 'Bid management is incomplete or has an error',
             'datetime': {'value': '2025-08-11T10:54:55.127000', 'timezone': 'UTC'}, 'field_name': 'biddableEntities',
             'identifier': '6899cbfd701775392bd53efa'}
        """
        lst_long_ids = set([error.get("identifier") for error in ad_group_errors if error.get("identifier")])
        if not lst_long_ids:
            return ad_group_errors
        lst_short_ids = await self.lookup.get_adgroup_short_id_by_long_id_batch(lst_long_ids)

        mapped_ids = dict(zip(lst_long_ids, lst_short_ids))

        for error in ad_group_errors:
            identifier = error.get("identifier")
            if not identifier:
                continue
            short_id = mapped_ids.get(identifier)
            if short_id:
                error["identifier"] = short_id
            else:
                logger.error(
                f"Failed to map identifier {identifier} to short id",
                     extra= {
                         "monitored_transaction": "AD-GROUP-ERRORS-MAP-IDENTIFIER-LONG-ID-TO-SHORT-ID",
                     }
                )

        return ad_group_errors

    async def cache_ad_groups_by_short_id(self,  ad_group_details:dict[str, int] ) -> None:
        short_ids_to_lookup = [str(short_id) for long_id, short_id in ad_group_details.items()]
        cached_long_ids = set(await self.lookup.get_adgroup_long_id_by_short_id_batch(short_ids_to_lookup) or [])
        missing_short_ids = {short_id : long_id for long_id, short_id in ad_group_details.items() if long_id not in cached_long_ids }

        if missing_short_ids:
            await self.lookup.set_adgroup_long_id_by_short_id_batch(missing_short_ids)


    async def cache_ad_groups_by_long_id(self,  ad_group_details:dict[str, int]):
        long_ids_to_lookup = [long_id for long_id, short_id in ad_group_details.items()]
        cached_short_ids = set(await self.lookup.get_adgroup_short_id_by_long_id_batch(long_ids_to_lookup) or [])
        missing_long_ids = {long_id: short_id for long_id, short_id in ad_group_details.items() if short_id not in cached_short_ids }

        if missing_long_ids:
            await self.lookup.set_adgroup_short_id_by_long_id_batch(missing_long_ids)
