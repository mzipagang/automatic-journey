import datetime

from fastapi import HTTPException
from unittest.mock import MagicMock, patch, call

from app.common.model.campaign_types import InternalCampaignType
from app.common.model.placement import PlacementType
from app.common.model.targets import TargetAdgroupRequest
from app.v2.utils.ad_group_validations import AdGroupRequestValidator
from app.common.view_models import AdGroupStatus, Entity
from app.v2.view_models import AdGroupRequest, AdGroupV2Request, Campaign, AdGroupV2
import unittest

from tests.unit.services.constants import AD_GROUP_REQUEST
from tests.unit.v2 import CAMPAIGN


class TestAdGroupRequestValidator(unittest.TestCase):

    def setup(self):
        # Setup can be extended as needed
        self.validator = AdGroupRequestValidator()

    def test_validate_ad_group_status_valid(self):
        for status in [AdGroupStatus.DRAFT, AdGroupStatus.SCHEDULED, AdGroupStatus.ACTIVE]:
            req = MagicMock(spec=AdGroupRequest, status=status)
            # Should not raise
            AdGroupRequestValidator._AdGroupRequestValidator__validate_new_ad_group_status(req)

    def test_validate_ad_group_status_none(self):
        req = MagicMock(spec=AdGroupRequest, status=None)
        with self.assertRaises(HTTPException) as ctx:
            AdGroupRequestValidator._AdGroupRequestValidator__validate_new_ad_group_status(req)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Failed to provide a ad group status", ctx.exception.detail)

    def test_validate_ad_group_status_invalid(self):
        req = MagicMock(spec=AdGroupRequest, status=AdGroupStatus.ENDED)
        with self.assertRaises(HTTPException) as ctx:
            AdGroupRequestValidator._AdGroupRequestValidator__validate_new_ad_group_status(req)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Ad group status must be one of the following", ctx.exception.detail)

    def test_validate_day_parting_targe(self):
        day_parting_taget = TargetAdgroupRequest(
            values=[30, 40],
            type=3
        )

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator._AdGroupRequestValidator__validate_day_parting_target(day_parting_taget)

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual("Day parting value should be a valid hour, and"
                    " the second value must be greater than the first one", context.exception.detail)

    def test_validate_bid_amount_when_use_base_bid_is_false(self):
        entities = [
            Entity(
                useBaseBid=False,
                bidAmount=None,
                id=1,
                deleted=False
            )
        ]

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator._AdGroupRequestValidator__validate_bid_amount_when_use_base_bid_is_false(entities)

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual("Bid amount must be provided when useBaseBid is false", context.exception.detail)

    def test_extra_validations_invalid_status(self):
        ad_group_request = MagicMock(spec=AdGroupV2Request)
        ad_group_request.status = AdGroupStatus.ENDED
        campaign = MagicMock()
        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator._AdGroupRequestValidator__extra_validations(ad_group_request, campaign)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Cannot create ad group with ENDED, PAUSED, FAILED status")

    @patch("app.v2.utils.ad_group_validations.parse_date")
    def test_extra_validations_ad_group_invalid_start_date(self, mock_parse_date: MagicMock):
        ad_group_request = MagicMock(spec=AdGroupV2)
        ad_group_request.status = AdGroupStatus.ENDED
        ad_group_request.startDate = "2017-06-22"
        campaign = MagicMock(spec=Campaign)
        campaign.startDate = "2022-07-28"
        campaign.endDate = None
        mock_parse_date.side_effect = [
            datetime.datetime(2017, 6, 22),
            datetime.datetime(2022, 7, 28),
        ]

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator._AdGroupRequestValidator__extra_validations(ad_group_request, campaign)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Ad group start date must be after or same campaign start date")
        mock_parse_date.assert_has_calls(
            [
                call("2017-06-22"),
                call("2022-07-28")

            ]
        )

    @patch("app.v2.utils.ad_group_validations.parse_date")
    def test_extra_validations_ad_group_invalid_end_date_is_small_than_start_date(self, mock_parse_date: MagicMock):
        ad_group_request = MagicMock(spec=AdGroupV2)
        ad_group_request.status = AdGroupStatus.ENDED
        ad_group_request.startDate = "2022-07-28"
        ad_group_request.endDate = "2011-07-16"
        campaign = MagicMock(spec=Campaign)
        campaign.startDate = "2022-07-28"
        campaign.endDate = None
        mock_parse_date.side_effect = [
            datetime.datetime(2022, 7, 28),
            datetime.datetime(2022, 7, 28),
            datetime.datetime(2011, 7, 16),
        ]

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator._AdGroupRequestValidator__extra_validations(ad_group_request, campaign)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Ad group end date must be after start date")
        mock_parse_date.assert_has_calls(
            [
                call("2022-07-28"),
                call("2022-07-28"),
                call("2011-07-16")

            ]
        )

    @patch("app.v2.utils.ad_group_validations.parse_date")
    def test_extra_validations_ad_group_ad_group_end_date_bigger_than_campaign_end_date(self, mock_parse_date: MagicMock):
        ad_group_request = MagicMock(spec=AdGroupV2)
        ad_group_request.status = AdGroupStatus.ENDED
        ad_group_request.startDate = "2022-07-28"
        ad_group_request.endDate = "2022-08-01"
        campaign = MagicMock(spec=Campaign)
        campaign.startDate = "2022-07-28"
        campaign.endDate = "2022-07-31"
        mock_parse_date.side_effect = [
            datetime.datetime(2022, 7, 28),
            datetime.datetime(2022, 7, 31),
            datetime.datetime(2022, 7, 28),
            datetime.datetime(2022, 8, 1),
        ]

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator._AdGroupRequestValidator__extra_validations(ad_group_request, campaign)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Ad group end date must be before campaign end date")
        mock_parse_date.assert_has_calls(
            [call('2022-07-28'), call('2022-07-31'), call('2022-07-28'), call('2022-08-01')]
        )

    @patch("app.v2.utils.ad_group_validations.parse_date")
    def test_extra_validations_ad_group_ad_group_null_date_and_campaign_date(
            self,
            mock_parse_date
    ):
        ad_group_request = MagicMock(spec=AdGroupV2)
        ad_group_request.status = AdGroupStatus.ENDED
        ad_group_request.startDate = "2022-07-28"
        ad_group_request.endDate = None
        campaign = MagicMock(spec=Campaign)
        campaign.startDate = "2022-07-28"
        campaign.endDate = "2022-07-31"
        mock_parse_date.side_effect = [
            datetime.datetime(2022, 7, 28),
            datetime.datetime(2022, 7, 31),
            datetime.datetime(2022, 7, 28)
        ]

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator._AdGroupRequestValidator__extra_validations(ad_group_request, campaign)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Ad group end date cannot be null as Campaign endDate is not null")
        mock_parse_date.assert_has_calls(
            [call('2022-07-28'), call('2022-07-31'), call('2022-07-28')])

    def test_extra_validations_for_update_none_ad_group_id(self):
        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator.extra_validations_for_update(
                MagicMock(),
                None,
                MagicMock(),
                MagicMock()
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Ad group not found")

    def test_extra_validations_for_update_ad_group_ended(self):
        ad_group = MagicMock()
        ad_group.status = AdGroupStatus.ENDED
        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator.extra_validations_for_update(
                MagicMock(),
                ad_group,
                MagicMock(),
                MagicMock()
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Cannot update ad group with ENDED status")

    def test_extra_validations_for_update_ad_group_keyword_without_search_and_browse(self):
        ad_group = MagicMock()
        ad_group_placements = [PlacementType.BASKET_BUILDER]

        updated_ad_group_request = MagicMock()
        updated_ad_group_request.keywordBidModifiers = ["keyword1", "keyword2", "keyword3"]

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator.extra_validations_for_update(
                updated_ad_group_request,
                ad_group,
                ad_group_placements,
                MagicMock()
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Cannot add keyword targeting without the Search and Browse placement")

    def test_extra_validations_for_update_ad_group_not_carousel_head_line(self):
        ad_group = MagicMock()
        ad_group_placements = [PlacementType.BASKET_BUILDER]

        updated_ad_group_request = MagicMock()
        updated_ad_group_request.carouselHeadline = None

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator.extra_validations_for_update(
                updated_ad_group_request,
                ad_group,
                ad_group_placements,
                InternalCampaignType.CAROUSEL
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Carousel headline is required for Carousel campaigns")

    def test_extra_validations_for_update_ad_group_carousel_head_line_with_no_carousel_campaign(self):
        ad_group = MagicMock()
        ad_group_placements = [PlacementType.BASKET_BUILDER]

        updated_ad_group_request = MagicMock()
        updated_ad_group_request.carouselHeadline = "Test Head"

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator.extra_validations_for_update(
                updated_ad_group_request,
                ad_group,
                ad_group_placements,
                InternalCampaignType.PLA
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Carousel headline is not allowed for non-Carousel campaigns")

    def test_extra_validations_for_update_ad_group_invalid_transition(self):
        ad_group = MagicMock()
        ad_group_placements = [PlacementType.BASKET_BUILDER]
        ad_group.status = AdGroupStatus.SCHEDULED

        updated_ad_group_request = MagicMock()
        updated_ad_group_request.carouselHeadline = None
        updated_ad_group_request.status = AdGroupStatus.DRAFT

        with self.assertRaises(HTTPException) as context:
            AdGroupRequestValidator.extra_validations_for_update(
                updated_ad_group_request,
                ad_group,
                ad_group_placements,
                InternalCampaignType.PLA
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Cannot update ad group from SCHEDULED to DRAFT status")

class TestAdGroupRequestValidatorTargets(unittest.TestCase):
    def setUp(self):
        self.target_service = MagicMock()
        self.placement_target = MagicMock(id=1)
        self.division_target = MagicMock(id=2)
        self.day_parting_target = MagicMock(id=3)
        self.target_service.get_targets.return_value = [
            self.placement_target, self.division_target, self.day_parting_target
        ]
        self.target1 = MagicMock(type='1')
        self.target2 = MagicMock(type='2')
        self.target3 = MagicMock(type='3', values=[8, 12])
        self.ad_group_request = MagicMock(spec=AdGroupV2Request)
        self.ad_group_request.targets = [self.target1, self.target2, self.target3]
        self.validator = AdGroupRequestValidator

    def test_validate_ad_group_targets_missing_targets(self):
        self.ad_group_request.targets = []
        with self.assertRaises(HTTPException) as exc:
            AdGroupRequestValidator().validate_ad_group_targets(
                [],
                [],
                [],
                False
            )
        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn("At least one target must be provided", exc.exception.detail)

    def test_validate_ad_group_targets_success(self):
        self.ad_group_request.targets = [self.target1, self.target2, self.target3]
        AdGroupRequestValidator().validate_ad_group_targets(
            [self.target1],
            [self.target2],
            [self.target3],
            False
        )

    def test_validate_ad_group_targets_no_placement(self):
        self.ad_group_request.targets = [self.target2, self.target3]
        with self.assertRaises(HTTPException) as exc:
            AdGroupRequestValidator().validate_ad_group_targets(
                [],
                [self.target2],
                [self.target3],
                False
            )
        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn("one target of type placement must be provided", exc.exception.detail)

    def test_validate_ad_group_targets_no_division(self):
        self.ad_group_request.targets = [self.target1, self.target3]
        result = AdGroupRequestValidator().validate_ad_group_targets(
            [self.target1],
            [],
            [self.target3],
            False
        )
        self.assertEqual(None, result)

    def test_validate_ad_group_targets_for_carousel_campaign(self):
        self.ad_group_request.targets = [self.target1, self.target2, self.target3]
        AdGroupRequestValidator().validate_ad_group_targets(
            [],
            [],
            [],
            True
        )

    @patch("app.v2.utils.ad_group_validations.AdGroupRequestValidator._AdGroupRequestValidator__extra_validations")
    @patch("app.v2.utils.ad_group_validations.AdGroupRequestValidator._AdGroupRequestValidator__validate_bid_amount_when_use_base_bid_is_false")
    def test_validate_ad_group_request_single_call_campaign_without_enddate (
            self,
            mock_validate_bid_amount_when_use_base_bid_is_false: MagicMock,
            mock_extra_validations: MagicMock()
    ):
        # Arrange
        ad_group_request = AD_GROUP_REQUEST
        ad_group_request.targets = [TargetAdgroupRequest(type=1,id=1), TargetAdgroupRequest(type=2,id=1)]
        campaign = CAMPAIGN
        campaign.endDate = ""

        # Act
        AdGroupRequestValidator().validate_ad_group_request_single_call(ad_group_request,campaign)

        # Assert
        mock_extra_validations.assert_called_once_with(ad_group_request, campaign)
        mock_validate_bid_amount_when_use_base_bid_is_false.assert_called_once()
