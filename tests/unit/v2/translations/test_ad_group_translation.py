from copy import deepcopy
from datetime import datetime
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.common.model.campaign_types import InternalCampaignType, CASCampaignType
from app.common.model.downstream.bid_manager import ValidationResponse
from app.common.model.placement import PlacementType
from app.common.model.targets import TargetAdgroupRequest
from app.common.view_models import AdGroupStatus, Entity
from app.v2.model.downstream.activation_service import ActivationResponse, ActivationResponseV2, ActivationPayload, \
    ActivationUpdatePayload, ChannelData
from app.common.model.shared import (
    ActivationPublishStatus,
    ActivationWarnings,
    DateTimeField,
    PublishStatus,
    UpstreamValidationWarning,
    Warnings, BudgetType, InternalBudgetType,
)
from app.v2.translations.ad_group_translation import AdGroupTranslation
from app.v2.view_models import SecretAdGroupUpdateRequest
from app.v2.view_models.ad_group import AdGroupV2, AdGroupV2Request, AdGroupUpdateRequestV2
from tests.unit.services.constants import UPDATED_ACTIVATION_RESPONSE_JSON
from tests.utils_for_testing.auto_mock import auto_mock

ADGROUP_JSON = {
    "adGroupId": 12345,
    "campaignId": 4321,
    "name": "Test Ad Group",
    "startDate": "2024-05-20",
    "endDate": "2024-06-20",
    "budgetType": "MONTHLY",
    "budgetAmount": 250,
    "status": "ACTIVE",
    "baseBid": 0.0,
    "entities": [],
    "targets": [],
    "keywordBidModifiers": [],
    "isArchived": False
}

class TestAdGroupTranslation(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_bid_manager_service = AsyncMock()
        self.mock_lookup = AsyncMock()
        self.mock_target_translation = AsyncMock()
        self.mock_keyword_service = AsyncMock()

        self.ad_group_translation = AdGroupTranslation(
            bid_manager_service=self.mock_bid_manager_service,
            lookup=self.mock_lookup,
            target_translation=self.mock_target_translation,
            keyword_service=self.mock_keyword_service
        )


    @staticmethod
    def __activation(**kwargs) -> ActivationResponse:
        activation_json = deepcopy(UPDATED_ACTIVATION_RESPONSE_JSON.get("data"))
        merged_channel_data = {
            **activation_json.get("channel_data", {}),
            **kwargs.get("channel_data", {})
        }
        merged_channel_config = {
            **activation_json.get("channel_config", {}),
            **kwargs.get("channel_config", {})
        }
        merged_metadata = {
            **activation_json.get("metadata", {}),
            **kwargs.get("metadata", {})
        }
        return ActivationResponse(**{
            **activation_json,
            **kwargs,
            "channel_data": merged_channel_data,
            "channel_config": merged_channel_config,
            "metadata": merged_metadata
        })

    @staticmethod
    def __adgroup(**kwargs) -> AdGroupV2:
        adgroup_json = deepcopy(ADGROUP_JSON)
        return AdGroupV2(**{
            **adgroup_json,
            **kwargs
        })

    async def test_ad_group_from_activation__builds_an_ad_group_from_activation(self):
        keyword_bid_modifier_id = "1234"
        entities = []
        base_bid = 0.0
        targets = []
        keyword_modifiers = []
        ad_group_id = 12345
        campaign_id = 4321
        activation = self.__activation(**{
            "channel_data": {
                "keywordBidModifierGroup": keyword_bid_modifier_id
            }
        })
        expected_response = self.__adgroup()
        self.mock_bid_manager_service.get_valid_entries.return_value = ValidationResponse(
            filtered_entities=entities,
            default_bid=base_bid,
            errors=[]
        )
        self.mock_target_translation.targets_from_activation.return_value = targets
        self.mock_keyword_service.get_bid_modifiers.return_value = keyword_modifiers
        self.mock_lookup.get_adgroup_short_id_by_long_id.return_value=ad_group_id
        self.mock_lookup.get_campaign_short_id_by_long_id.return_value=campaign_id

        response = await self.ad_group_translation.ad_group_from_activation(activation)

        self.assertEqual(expected_response, response.adGroup)
        self.mock_bid_manager_service.get_valid_entries.assert_called_once_with(activation, None)
        self.mock_target_translation.targets_from_activation.assert_called_once_with(activation)
        self.mock_keyword_service.get_bid_modifiers.assert_called_once_with(keyword_bid_modifier_id)

    async def test_ad_group_from_activation__sets_carousel_headline(self):
        keyword_bid_modifier_id = "1234"
        entities = []
        base_bid = 0.0
        targets = []
        keyword_modifiers = []
        ad_group_id = 12345
        campaign_id = 4321
        mock_headline = "Cool Carousel Headline"
        activation = self.__activation(**{
            "channel_data": {
                "keywordBidModifierGroup": keyword_bid_modifier_id,
                "carouselHeadline": mock_headline
            }
        })
        expected_response = self.__adgroup(carouselHeadline=mock_headline)
        self.mock_bid_manager_service.get_valid_entries.return_value = ValidationResponse(
            filtered_entities=entities,
            default_bid=base_bid,
            errors=[]
        )
        self.mock_target_translation.targets_from_activation.return_value = targets
        self.mock_keyword_service.get_bid_modifiers.return_value = keyword_modifiers
        self.mock_lookup.get_adgroup_short_id_by_long_id.return_value = ad_group_id
        self.mock_lookup.get_campaign_short_id_by_long_id.return_value = campaign_id

        response = await self.ad_group_translation.ad_group_from_activation(activation)

        self.assertEqual(expected_response, response.adGroup)
        self.mock_bid_manager_service.get_valid_entries.assert_called_once_with(activation, None)
        self.mock_target_translation.targets_from_activation.assert_called_once_with(activation)
        self.mock_keyword_service.get_bid_modifiers.assert_called_once_with(keyword_bid_modifier_id)

    def test_warnings_from_activation_warnings__returns_empty_warning_if_given_no_warnings(self):
        activation_warnings = []
        expected_warnings = Warnings(validation=[])

        response = self.ad_group_translation.warnings_from_activation_warnings(activation_warnings)

        self.assertEqual(expected_warnings, response)

    def test_warnings_from_activation_warnings__converts_activation_warnings_to_warnings(self):
        warning = ActivationWarnings(
            code="code",
            reason="reason",
            datetime=DateTimeField(value="2025-04-07", timezone="UTC"),
            field_name="field_name",
            identifier="identifier"
        )
        activation_warnings = [warning]
        expected_warnings = Warnings(validation=[
            UpstreamValidationWarning(
                detail=[warning.reason],
                path=warning.field_name
            )
        ])

        response = self.ad_group_translation.warnings_from_activation_warnings(activation_warnings)

        self.assertEqual(expected_warnings, response)

    def test_publish_status_from_activation__converts_activation_to_publish_status(self):
        activation_1 = self.__activation(**{
            "unpublished_data": {},
            "metadata": {
                "last_publish_result": ActivationPublishStatus.SUCCESS
            }
        })
        expected_result_1 = PublishStatus.PUBLISHED

        activation_2 = self.__activation(**{
            "unpublished_data": {
                "some_key": "some_value"
            },
            "metadata": {
                "last_publish_result": ActivationPublishStatus.FAILURE
            }
        })
        expected_result_2 = PublishStatus.FAILED

        activation_3 = self.__activation(**{
            "unpublished_data": {
                "some_key": "some_value"
            },
            "metadata": {
                "last_publish_result": ActivationPublishStatus.SUCCESS
            }
        })
        expected_result_3 = PublishStatus.PENDING

        activation_4 = self.__activation(**{
            "unpublished_data": {},
            "metadata": {
                "last_publish_result": ActivationPublishStatus.FAILURE
            }
        })
        expected_result_4 = PublishStatus.EMPTY

        result_1 = self.ad_group_translation.publish_status_from_activation(activation_1)
        result_2 = self.ad_group_translation.publish_status_from_activation(activation_2)
        result_3 = self.ad_group_translation.publish_status_from_activation(activation_3)
        result_4 = self.ad_group_translation.publish_status_from_activation(activation_4)

        self.assertEqual(expected_result_1, result_1)
        self.assertEqual(expected_result_2, result_2)
        self.assertEqual(expected_result_3, result_3)
        self.assertEqual(expected_result_4, result_4)

    def test_get_campaign_type(self):
        activation_1 = self.__activation(**{"channel_config": {"type": "invalid"}})
        activation_2 = self.__activation(**{"channel_config": {"type": CASCampaignType.PLA.lower()}})
        activation_3 = self.__activation(**{"channel_config": {"type": CASCampaignType.TOA.lower()}})
        activation_4 = self.__activation(**{"channel_config": {"type": CASCampaignType.CAROUSEL.lower()}})

        result_1 = self.ad_group_translation.get_campaign_type(activation_1)
        result_2 = self.ad_group_translation.get_campaign_type(activation_2)
        result_3 = self.ad_group_translation.get_campaign_type(activation_3)
        result_4 = self.ad_group_translation.get_campaign_type(activation_4)

        self.assertEqual(InternalCampaignType.UNSUPPORTED, result_1)
        self.assertEqual(InternalCampaignType.PLA, result_2)
        self.assertEqual(InternalCampaignType.TOA, result_3)
        self.assertEqual(InternalCampaignType.CAROUSEL, result_4)

    def test_validation_request_from_activation__creates_validation_request_from_activation(self):
        min_bid = 0.6
        max_bid = 50
        mock_activation_json = {
            "data": {
                "id": "activation_id",
                "channel_config": {
                    "type": "PLA"
                }
            },
            "included": MagicMock()
        }
        bid_range_json = {
            "biddableEntities": {
                "min_bid_amount": min_bid,
                "max_bid_amount": max_bid,
            }
        }
        mock_activation = auto_mock(
            mock_activation_json,
            MagicMock(spec=ActivationResponseV2[ActivationResponse])
        )
        mock_activation.included.configuration_by_activation.get.return_value = auto_mock(
            bid_range_json,
            MagicMock()
        )

        validate_bid_request = self.ad_group_translation.validation_request_from_activation(mock_activation, brand_codes=[])

        self.assertEqual(min_bid, validate_bid_request.minimumBidAmount)
        self.assertEqual(max_bid, validate_bid_request.maximumBidAmount)
        self.assertTrue(validate_bid_request.bidIdsMustHaveValidEntities)

    def test_validation_request_from_activation__creates_validation_request_with_count_validations_for_carousel(self):
        min_bid = 0.6
        max_bid = 50
        mock_activation_json = {
            "data": {
                "id": "activation_id",
                "channel_config": {
                    "type": InternalCampaignType.CAROUSEL
                }
            },
            "included": MagicMock()
        }
        bid_range_json = {
            "biddableEntities": {
                "min_bid_amount": min_bid,
                "max_bid_amount": max_bid,
            }
        }
        mock_activation = auto_mock(
            mock_activation_json,
            MagicMock(spec=ActivationResponseV2[ActivationResponse])
        )
        mock_activation.included.configuration_by_activation.get.return_value = auto_mock(
            bid_range_json,
            MagicMock()
        )

        validate_bid_request = self.ad_group_translation.validation_request_from_activation(mock_activation, brand_codes=[])

        self.assertEqual(min_bid, validate_bid_request.minimumBidAmount)
        self.assertEqual(max_bid, validate_bid_request.maximumBidAmount)
        self.assertTrue(validate_bid_request.bidIdsMustHaveValidEntities)
        self.assertEqual(3, validate_bid_request.minimumBidCount)
        self.assertEqual(32, validate_bid_request.maximumBidCount)

    def test_build_activation_payload(self):
        ad_group_request = AdGroupV2Request(
                name="Test Adgroup",
                campaignId=123,
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[TargetAdgroupRequest(type=1, values=[1, 2])],
                carouselHeadline=None
        )
        budget_type = "test_budget_type"
        bid_recommendations_id = "test_bid_recommendations_id"
        location_group_id = "test_location_group_id"
        internal_campaign_id = "test_internal_campaign_id"
        placements = []
        campaign_type = InternalCampaignType.PLA
        start_date = datetime(2017, 6, 22)
        expected_response = ActivationPayload(**{
            "channel_data": {
                "carouselHeadline": None,
                "name": "Test Adgroup",
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": None,
                "alwaysOn": True,
                "budgetType": budget_type.capitalize(),
                "budgetAmount": 250,
                "biddableEntities": [
                    bid_recommendations_id
                ],
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
        })

        # Act
        response = self.ad_group_translation.build_activation_payload(
            ad_group_request,
            budget_type,
            bid_recommendations_id,
            location_group_id,
            internal_campaign_id,
            placements,
            campaign_type,
            start_date
        )

        # Assert
        self.assertEqual(expected_response, response)

    def test_determine_budget_type(self):
        # Arrange
        activation = self.__activation(**{
            "channel_data":{"budgetType": "CUSTOM"}
        })
        expected_result = "LIFETIME"

        # Act
        result = self.ad_group_translation._AdGroupTranslation__determine_budget_type(activation)

        # Assert
        self.assertEqual(expected_result, result)

    @patch("app.common.utils.context_tools")
    async def test_create_ad_group_fails(self, mock_context_tools):
        # Arrange
        mock_activation = MagicMock(spec=ActivationResponse)
        mock_activation.channel_data = None
        mock_activation.id = "test_id"
        mock_activation.campaign_id = "test_id"

        with self.assertRaises(HTTPException) as context:
            # Act
            await self.ad_group_translation._AdGroupTranslation__create_ad_group(
                mock_activation,
                None,
                0.0,
                [],
                [],
                [],
                False
            )

        # Assert
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Bad upstream ad group data. Please contact support if problem persists.")

    def test_set_budget_type_for_secret_ad_group_lifetime(self):
        # Arrange
        ad_group_request = MagicMock(spec=SecretAdGroupUpdateRequest)
        ad_group_request.budgetType = BudgetType.LIFETIME

        # Act
        result = self.ad_group_translation.set_budget_type_for_secret_ad_group(ad_group_request)

        # Assert
        self.assertEqual(result, "Custom")

    def test_set_budget_type_for_secret_ad_group(self):
        # Arrange
        ad_group_request = MagicMock(spec=SecretAdGroupUpdateRequest)
        ad_group_request.budgetType = "TEST"

        # Act
        self.ad_group_translation.set_budget_type_for_secret_ad_group(ad_group_request)

        # Assert
        self.assertEqual(ad_group_request.budgetType, "TEST")

    def test_parse_ad_group_update_request(self):
        # Arrange
        ad_group_update_request = MagicMock(spec=AdGroupUpdateRequestV2)
        ad_group_update_request.targets =[MagicMock]
        ad_group_update_request.keywordBidModifiers = [MagicMock]
        ad_group_update_request.model_dump.return_value = {}

        # Act
        result = self.ad_group_translation.parse_ad_group_update_request(ad_group_update_request)

        # Assert
        self.assertEqual(result, {
            "keywordBidModifiers": ad_group_update_request.keywordBidModifiers,
            "targets": ad_group_update_request.targets,
        })

    def test_build_update_activation_payload(self):
        # Arrange
        updated_ad_group_dict = {
            "endDate": "2024-06-20",
            "budgetType": InternalBudgetType.MONTHLY,
        }
        ad_group_placements = ["test_placement"]
        keyword_bid_modifier_group_id = "test_keyword_bid_modifier_group_id"
        location_group_id = "test_location_group_id"
        ad_group_day_parting_targets = [MagicMock(values=[0, 1])]
        campaign_type = InternalCampaignType.PLA
        expected_result = ActivationUpdatePayload(
            channel_data=ChannelData(
                carouselHeadline=None,
                name=None,
                startDate=None,
                endDate='2024-06-20',
                alwaysOn=False,
                budgetType='Monthly',
                budgetAmount=None,
                biddableEntities=None,
                keywordBidModifierGroup='test_keyword_bid_modifier_group_id',
                divisionBanners=['test_location_group_id'],
                placementType=['test_placement'],
                dayPartingStart=0,
                dayPartingEnd=1
            )
        )

        # Act
        result = self.ad_group_translation.build_update_activation_payload(
            updated_ad_group_dict,
            ad_group_placements,
            keyword_bid_modifier_group_id,
            location_group_id,
            ad_group_day_parting_targets,
            campaign_type
        )

        # Assert
        self.assertEqual(result, expected_result)

    def test_build_update_activation_carousel_payload(self):
        # Arrange
        updated_ad_group_dict = {
            "endDate": "2024-06-20",
            "budgetType": InternalBudgetType.MONTHLY,
        }
        ad_group_placements = ["test_placement"]
        keyword_bid_modifier_group_id = "test_keyword_bid_modifier_group_id"
        location_group_id = "test_location_group_id"
        ad_group_day_parting_targets = [MagicMock(values=[0, 1])]
        campaign_type = InternalCampaignType.CAROUSEL
        expected_result = ActivationUpdatePayload(
            channel_data=ChannelData(
                carouselHeadline=None,
                name=None,
                startDate=None,
                endDate='2024-06-20',
                alwaysOn=False,
                budgetType='Monthly',
                budgetAmount=None,
                biddableEntities=None,
                keywordBidModifierGroup='test_keyword_bid_modifier_group_id',
                divisionBanners=['test_location_group_id'],
                placementType=[PlacementType.SEARCH_AND_BROWSE_PPC],
                dayPartingStart=0,
                dayPartingEnd=1
            )
        )

        # Act
        result = self.ad_group_translation.build_update_activation_payload(
            updated_ad_group_dict,
            ad_group_placements,
            keyword_bid_modifier_group_id,
            location_group_id,
            ad_group_day_parting_targets,
            campaign_type
        )

        # Assert
        self.assertEqual(result, expected_result)

    async def test_adgroup_errors_map_identifier_long_id_to_short_id(self):
        # Arrange
        ad_group_id_1 = "12345"
        ad_group_id_2 = "54321"
        ad_group_short_ids = [ad_group_id_1, ad_group_id_2]
        ad_group_long_ids = ["6899cbfd701775392bd53efa", "78899cbfd705392bd53e"]
        ad_group_errors = [
            {'code': 'biddableEntities', 'reason': 'Bid management is incomplete or has an error',
             'datetime': {'value': '2025-08-11T10:54:55.127000', 'timezone': 'UTC'},
             'field_name': 'biddableEntities',
             'identifier': ad_group_long_ids[0]
            },
            {'code': 'biddableEntities', 'reason': 'Bid management is incomplete or has an error',
             'datetime': {'value': '2025-08-12T10:54:55.127000', 'timezone': 'UTC'},
             'field_name': 'biddableEntities',
             'identifier': ad_group_long_ids[1]
            }
        ]
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = ad_group_short_ids

        # Act
        result = await self.ad_group_translation.adgroup_errors_map_identifier_long_id_to_short_id(ad_group_errors)
        self.assertEqual(sorted([e['identifier'] for e in result]), sorted(ad_group_short_ids))

    async def test_adgroup_errors_map_identifier_long_id_to_short_id_single_error(self):
        # Arrange
        ad_group_id_1 = "12345"
        ad_group_short_ids = [ad_group_id_1]
        ad_group_long_ids = ["6899cbfd701775392bd53efa"]
        ad_group_errors = [
            {'code': 'biddableEntities', 'reason': 'Bid management is incomplete or has an error',
             'datetime': {'value': '2025-08-11T10:54:55.127000', 'timezone': 'UTC'},
             'field_name': 'biddableEntities',
             'identifier': ad_group_long_ids[0]
            }
        ]
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = ad_group_short_ids

        # Act
        result = await self.ad_group_translation.adgroup_errors_map_identifier_long_id_to_short_id(ad_group_errors)
        self.assertEqual(sorted([e['identifier'] for e in result]), sorted(ad_group_short_ids))

    async def test_adgroup_errors_map_identifier_long_id_to_short_id_identifier_not_present(self):
        # Arrange
        ad_group_id_1 = "12345"
        ad_group_id_2 = "54321"
        ad_group_short_ids = [ad_group_id_1, ad_group_id_2]
        ad_group_long_ids = ["6899cbfd701775392bd53efa", "78899cbfd705392bd53e"]
        ad_group_errors = [
            {'code': 'biddableEntities', 'reason': 'Bid management is incomplete or has an error',
             'datetime': {'value': '2025-08-11T10:54:55.127000', 'timezone': 'UTC'},
             'field_name': 'biddableEntities',
             },
            {'code': 'biddableEntities', 'reason': 'Bid management is incomplete or has an error',
             'datetime': {'value': '2025-08-12T10:54:55.127000', 'timezone': 'UTC'},
             'field_name': 'biddableEntities',
             }
        ]

        # Act
        result = await self.ad_group_translation.adgroup_errors_map_identifier_long_id_to_short_id(ad_group_errors)
        assert result is not None
        self.assertEqual(result, ad_group_errors)

    @patch("app.v2.translations.ad_group_translation.logger")
    async def test_adgroup_errors_map_identifier_long_id_to_short_id_no_short_id_found(self, mocked_logger):
        # Arrange
        ad_group_id_1 = "12345"
        ad_group_short_ids = [None]
        ad_group_long_ids = ["6899cbfd701775392bd53efa"]
        ad_group_errors = [
            {'code': 'biddableEntities', 'reason': 'Bid management is incomplete or has an error',
             'datetime': {'value': '2025-08-11T10:54:55.127000', 'timezone': 'UTC'},
             'field_name': 'biddableEntities',
             'identifier': ad_group_long_ids[0]
             }
        ]
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = ad_group_short_ids

        # Act
        result = await self.ad_group_translation.adgroup_errors_map_identifier_long_id_to_short_id(ad_group_errors)
        self.assertEqual(result, ad_group_errors)
        mocked_logger.error.assert_called_once_with(
            f"Failed to map identifier 6899cbfd701775392bd53efa to short id",
            extra={
                "monitored_transaction": "AD-GROUP-ERRORS-MAP-IDENTIFIER-LONG-ID-TO-SHORT-ID",
            }
        )

    def test_build_activation_payload_carousel_subtext(self):
        ad_group_request = AdGroupV2Request(
                name="Test Adgroup",
                campaignId=123,
                startDate="2024-05-20",
                endDate="2024-06-20",
                budgetAmount=250,
                status=AdGroupStatus.DRAFT,
                baseBid=2.50,
                entities=[Entity(id=1, useBaseBid=False, bidAmount=0.3, deleted=False)],
                targets=[TargetAdgroupRequest(type=1, values=[1, 2])],
                carouselHeadline="This carousel headline",
                carouselSubtext="This is carousel subtext"
        )
        budget_type = "test_budget_type"
        bid_recommendations_id = "test_bid_recommendations_id"
        location_group_id = "test_location_group_id"
        internal_campaign_id = "test_internal_campaign_id"
        placements = ['Search & Browse PPC']
        campaign_type = InternalCampaignType.CAROUSEL
        start_date = datetime(2017, 6, 22)
        expected_response = ActivationPayload(**{
            "channel_data": {
                "carouselHeadline":"This carousel headline",
                "carouselSubtext":"This is carousel subtext",
                "name": "Test Adgroup",
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": None,
                "alwaysOn": True,
                "budgetType": budget_type.capitalize(),
                "budgetAmount": 250,
                "biddableEntities": [
                    bid_recommendations_id
                ],
                "divisionBanners": [
                    location_group_id
                ],
                "placementType": placements
            },
            "channel_config": {
                "type": "Promoted_Products_Carousel",
                "version": "1"
            },
            "campaign_id": internal_campaign_id
        })

        # Act
        response = self.ad_group_translation.build_activation_payload(
            ad_group_request,
            budget_type,
            bid_recommendations_id,
            location_group_id,
            internal_campaign_id,
            placements,
            campaign_type,
            start_date
        )

        # Assert
        self.assertEqual(expected_response, response)

    @pytest.mark.asyncio
    async def test__cache_ad_groups_by_short_id(self):
        # Arrange
        ad_group_details = {"456653976864547879": 3652, "7059573365222567": 3653}
        self.mock_lookup.get_adgroup_long_id_by_short_id_batch.return_value = ["7059573365222567"]

        # Act
        await self.ad_group_translation.cache_ad_groups_by_short_id(ad_group_details)
        # Assert
        self.mock_lookup.set_adgroup_long_id_by_short_id_batch.assert_awaited_once_with({3652: "456653976864547879"})

    @pytest.mark.asyncio
    async def test__cache_ad_groups_by_long_id(self):
        # Arrange
        ad_group_details = {"38938309382733029": 5746}
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = None

        # Act
        await self.ad_group_translation.cache_ad_groups_by_long_id(ad_group_details)
        # Assert
        self.mock_lookup.set_adgroup_short_id_by_long_id_batch.assert_awaited_once_with({"38938309382733029": 5746})

    @pytest.mark.asyncio
    async def test__cache_ad_groups_by_long_id_cached(self):
        ad_group_details = {"38938309382733029": 5746, "277736282788910292": 5747}
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = [5746,5747]

        # Act
        await self.ad_group_translation.cache_ad_groups_by_long_id(ad_group_details)
        # Assert
        self.mock_lookup.set_adgroup_short_id_by_long_id_batch.assert_not_awaited()