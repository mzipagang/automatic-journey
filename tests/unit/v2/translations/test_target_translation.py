from copy import deepcopy
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from app.v2.model.downstream.activation_service import ActivationResponse
from app.common.model.targets import Target, TargetAdgroupRequest, TargetTypeId
from app.v2.translations.target_translation import TargetTranslation
from tests.unit.services.constants import UPDATED_ACTIVATION_RESPONSE_JSON


class TestTargetTranslation(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_lookup = AsyncMock()
        self.mock_division_service = AsyncMock()
        self.mock_placement_service = AsyncMock()

        self.target_translation = TargetTranslation(
            lookup=self.mock_lookup,
            division_service=self.mock_division_service,
            placement_service=self.mock_placement_service
        )

    async def test_division_targets_from_banners(self):
        division_banners = ["a", "b", "c"]
        expected_ids = [1, 2, 3]
        expected_results = [Target(type="2", id=id) for id in expected_ids]
        self.mock_division_service.get_division_ids_from_banners.return_value = expected_ids

        results = await self.target_translation.division_targets_from_banners(division_banners)

        self.assertEqual(expected_results, results)
        self.mock_division_service.get_division_ids_from_banners.assert_called_once_with(division_banners)

    @patch('logging.Logger.warning')
    async def test_placement_targets_from_types(self, mock_logger_warning):
        placement_types = ["Search & Browse", "Basket Builder", "Savings"]
        expected_ids = [1, 2, None]
        expected_targets = [Target(type="1", id=id) for id in expected_ids[:2]]
        self.mock_lookup.get_placement_short_ids_by_names.return_value = expected_ids

        results = await self.target_translation.placement_targets_from_types(placement_types)

        self.assertEqual(expected_targets, results)
        self.mock_lookup.get_placement_short_ids_by_names.assert_called_once_with(placement_types)
        mock_logger_warning.assert_called_once_with("Placement types missing from redis: %s", ["Savings"])

    @patch('logging.Logger.info')
    async def test_targets_from_activation(self, mock_logger_info):
        day_parting_start = 9
        day_parting_end = 17
        mock_placement_ids = [1]
        mock_division_ids = [2]
        activation_json = deepcopy(UPDATED_ACTIVATION_RESPONSE_JSON)
        activation = ActivationResponse(**activation_json.get("data"))
        activation.channel_data["placementType"] = ["Search & Browse"]
        activation.channel_data["divisionBanners"] = ["Kroger"]
        activation.channel_data["dayPartingStart"] = day_parting_start
        activation.channel_data["dayPartingEnd"] = day_parting_end
        self.mock_lookup.get_placement_short_ids_by_names.return_value = mock_placement_ids
        self.mock_division_service.get_division_ids_from_banners.return_value = mock_division_ids
        expected_targets = [
            Target(type="1", id=1),
            Target(type="2", id=2),
            Target(type="3", values=[day_parting_start, day_parting_end]),
        ]

        results = await self.target_translation.targets_from_activation(activation)

        self.assertEqual(expected_targets, results)
        self.mock_lookup.get_placement_short_ids_by_names.assert_called_once_with(["Search & Browse"])
        self.mock_division_service.get_division_ids_from_banners.assert_called_once_with(["Kroger"])
        mock_logger_info.assert_called_once_with("Getting dayparting range")


    @patch('logging.Logger.info')
    async def test_targets_from_activation_ignore_placement_dayparting_for_carousel(self, mock_logger_info):
        day_parting_start = 9
        day_parting_end = 17
        mock_placement_ids = [1]
        mock_division_ids = [2]
        activation_json = deepcopy(UPDATED_ACTIVATION_RESPONSE_JSON)
        activation_json["data"]["channel_config"]["type"] = "Promoted_Products_Carousel"
        activation = ActivationResponse(**activation_json.get("data"))
        activation.channel_data["placementType"] = ["Search & Browse PPC"]
        activation.channel_data["divisionBanners"] = ["Kroger"]
        activation.channel_data["dayPartingStart"] = day_parting_start
        activation.channel_data["dayPartingEnd"] = day_parting_end
        self.mock_lookup.get_placement_short_ids_by_names.return_value = mock_placement_ids
        self.mock_division_service.get_division_ids_from_banners.return_value = mock_division_ids
        expected_targets = [
            Target(type="2", id=2),
        ]

        results = await self.target_translation.targets_from_activation(activation)

        self.assertEqual(expected_targets, results)
        self.mock_division_service.get_division_ids_from_banners.assert_called_once_with(["Kroger"])

    async def test_build_placements(self):
        self.mock_placement_service.get_cache_placement.return_value = {
            "placementId": "test_id",
            "name": "test_name",
            "channelShortName": "test_channel",
            "minimumBidAmount": 0.5
        }
        expected_result = ['test_name']

        result = await self.target_translation.build_placements_types(
            [
                TargetAdgroupRequest(type=TargetTypeId.PLACEMENT.value, id=1)
            ]
        )

        self.assertEqual(expected_result, result)
        self.mock_placement_service.get_cache_placement.assert_called_with(1)

    def test_fetch_ad_group_targets(self):
        request_targets = [
            TargetAdgroupRequest(type=TargetTypeId.PLACEMENT.value, id=1),
            TargetAdgroupRequest(type=TargetTypeId.DIVISION.value, id=2),
            TargetAdgroupRequest(type=TargetTypeId.DAY_PARTING.value, values=[9, 17])
        ]

        expected_result = (
            [TargetAdgroupRequest(type=1, id=1)],
            [TargetAdgroupRequest(type=2, id=2)],
            [TargetAdgroupRequest(type=3, values=[9, 17])]
        )

        result = self.target_translation.fetch_ad_group_targets(request_targets, False)

        self.assertEqual(expected_result, result)
