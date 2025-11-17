from typing import Optional, List

from fastapi import HTTPException

from app.common.model.campaign_types import InternalCampaignType
from app.common.model.placement import PlacementType
from app.common.model.targets import TargetAdgroupRequest
from app.common.utils import filtered_logger
from app.common.utils.date_utils import parse_date
from app.common.view_models import AdGroupStatus, Entity
from app.v2.view_models import AdGroupV2Request, Campaign as CampaignV2, AdGroupV2

logger = filtered_logger.get_logger(__name__)

ALLOWED_AD_GROUP_TRANSITIONS_MAP = {
    AdGroupStatus.DRAFT.value: [AdGroupStatus.DRAFT, AdGroupStatus.SCHEDULED, AdGroupStatus.ACTIVE],
    AdGroupStatus.SCHEDULED.value: [AdGroupStatus.SCHEDULED, AdGroupStatus.ACTIVE, AdGroupStatus.PAUSED],
    AdGroupStatus.PAUSED.value: [AdGroupStatus.PAUSED, AdGroupStatus.ACTIVE],
    AdGroupStatus.ACTIVE.value: [AdGroupStatus.ACTIVE, AdGroupStatus.PAUSED],
    AdGroupStatus.UNDER_REVIEW.value: [AdGroupStatus.UNDER_REVIEW]
}

class AdGroupRequestValidator:
    """
    This class contains methods to validate ad group requests.
    """
    @staticmethod
    def __validate_new_ad_group_status(ad_group_request: AdGroupV2Request):
        if ad_group_request.status is None:
            raise HTTPException(status_code=400, detail="Failed to provide a ad group status")

        # Only allow DRAFT, SCHEDULED, ACTIVE statuses
        if ad_group_request.status not in [AdGroupStatus.DRAFT, AdGroupStatus.SCHEDULED, AdGroupStatus.ACTIVE]:
            raise HTTPException(
                status_code=400,
                detail="Ad group status must be one of the following: DRAFT, SCHEDULED, ACTIVE"
            )

    @staticmethod
    def __validate_day_parting_target(day_parting_target: Optional[TargetAdgroupRequest]):
        # Validate if day parting target value is valid hour
        if not 0 <= day_parting_target.values[0] < day_parting_target.values[1] < 24:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Day parting value should be a valid hour, and"
                    " the second value must be greater than the first one"
                ),
            )

    @staticmethod
    def __validate_bid_amount_when_use_base_bid_is_false(entities: List[Entity]):
        for entity in entities:
            if entity.useBaseBid is False and entity.bidAmount is None:
                raise HTTPException(status_code=400, detail="Bid amount must be provided when useBaseBid is false")

    def validate_ad_group_targets(
            self,
            ad_group_placement_targets: list[TargetAdgroupRequest],
            ad_group_division_targets: list[TargetAdgroupRequest],
            ad_group_day_parting_targets: list[TargetAdgroupRequest],
            carousel_campaign_flow: bool
    ) ->  None:
        if not any(
                (
                        ad_group_placement_targets,
                        ad_group_division_targets,
                        ad_group_day_parting_targets
                )
        ) and not carousel_campaign_flow:
            raise HTTPException(status_code=400, detail="At least one target must be provided")

        for placement_target in ad_group_placement_targets:
            if not placement_target.id:
                raise HTTPException(400, "Target of type placement must include id")

        for division_target in ad_group_division_targets:
            if not division_target.id:
                raise HTTPException(400, "Target of type division must include id")

        if len(ad_group_placement_targets) == 0 and not carousel_campaign_flow:
            raise HTTPException(status_code=400, detail="At least one target of type placement must be provided")

        if ad_group_day_parting_targets:
            if len(ad_group_day_parting_targets) > 1:
                raise HTTPException(status_code=400, detail="Only one day parting target is allowed")
            ad_group_day_parting_targets = ad_group_day_parting_targets[0]
            if not ad_group_day_parting_targets.values:
                raise HTTPException(400, "Target of type day parting must include values")
            if len(ad_group_day_parting_targets.values) != 2:
                raise HTTPException(400, "Values len should be 2 for day parting target")
            self.__validate_day_parting_target(ad_group_day_parting_targets)

    @staticmethod
    def __extra_validations(ad_group_request: AdGroupV2Request | AdGroupV2, campaign: CampaignV2):
        """
        Perform any additional validations that are specific to the ad group request.
        This method can be deleted after define the correct validation logic.
        """
        if ad_group_request.status in [AdGroupStatus.ENDED, AdGroupStatus.PAUSED, AdGroupStatus.FAILED] and isinstance(ad_group_request, AdGroupV2Request):
            # This only for new ad groups
            raise HTTPException(status_code=400, detail="Cannot create ad group with ENDED, PAUSED, FAILED status")

        # Do these operation only for new ad groups or existing ad groups that are in DRAFT or SCHEDULED status
        start_date = parse_date(ad_group_request.startDate)
        campaign_end_date = parse_date(campaign.endDate) if campaign.endDate else None
        campaign_start_date = parse_date(campaign.startDate)
        if start_date < campaign_start_date:
            raise HTTPException(status_code=400, detail="Ad group start date must be after or same campaign start date")
        if ad_group_request.endDate is not None:
            end_date = parse_date(ad_group_request.endDate)
            if end_date < start_date:
                raise HTTPException(status_code=400, detail="Ad group end date must be after start date")
            if campaign_end_date is not None and end_date > campaign_end_date:
                raise HTTPException(status_code=400, detail="Ad group end date must be before campaign end date")
        else:
            if campaign_end_date not in [None, ""]:
                raise HTTPException(status_code=400,
                                    detail="Ad group end date cannot be null as Campaign endDate is not null")

    @staticmethod
    def extra_validations_for_update(
            updated_ad_group_request: AdGroupV2,
            original_ad_group: AdGroupV2,
            ad_group_placements: list,
            campaign_type: InternalCampaignType
    ) -> None:
        """
        Perform any additional validations that are specific to the ad group update request.
        This method can be deleted after define the correct validation logic.
        """
        if original_ad_group is None:
            raise HTTPException(status_code=404, detail="Ad group not found")
        if original_ad_group.status == AdGroupStatus.ENDED:
            raise HTTPException(
                status_code=400, detail=f"Cannot update ad group with {AdGroupStatus.ENDED} status"
            )
        # Keyword compatibility
        contains_search_and_browse_in_request = False
        for placement_name in ad_group_placements:
            if placement_name == PlacementType.SEARCH_AND_BROWSE.value:
                contains_search_and_browse_in_request = True
                break
        if not contains_search_and_browse_in_request:
            if len(updated_ad_group_request.keywordBidModifiers) > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot add keyword targeting without the Search and Browse placement",
                )
        if campaign_type == InternalCampaignType.CAROUSEL and not updated_ad_group_request.carouselHeadline:
            raise HTTPException(
                status_code=400,
                detail="Carousel headline is required for Carousel campaigns"
            )
        if campaign_type != InternalCampaignType.CAROUSEL and updated_ad_group_request.carouselHeadline:
            raise HTTPException(
                status_code=400,
                detail="Carousel headline is not allowed for non-Carousel campaigns"
            )
        allowed_transitions = ALLOWED_AD_GROUP_TRANSITIONS_MAP.get(original_ad_group.status.value, [])
        if updated_ad_group_request.status not in allowed_transitions:
            raise HTTPException(status_code=400,
                                detail=f"Cannot update ad group from {original_ad_group.status} to {updated_ad_group_request.status} status")

    def validate_ad_group_request_single_call(
        self,
        ad_group_request: AdGroupV2Request | AdGroupV2,
        campaign: CampaignV2,
    ) ->  None:
        """
        Validates the ad group request in single call.
        """
        self.__extra_validations(ad_group_request, campaign)
        # Just for new adgroups
        if isinstance(ad_group_request, AdGroupV2Request):
            self.__validate_new_ad_group_status(ad_group_request)

        self.__validate_bid_amount_when_use_base_bid_is_false(ad_group_request.entities)
