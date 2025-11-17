import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, call, patch

from fastapi import HTTPException

from app.common.model.downstream.location_groups import LocationGroupResponseData, LocationGroup, \
    LocationGroupCategory, DivisionBannerItem
from app.common.model.division import Division, DivisionServiceResponse
from app.common.model.redis import CachedDivision
from app.common.model.targets import TargetAdgroupRequest
from app.common.services.config_service import Config
from app.common.services.division_service import DivisionService


class TestDivisionService(IsolatedAsyncioTestCase):
    __mock_config_service: MagicMock
    __mock_internal_http_client_service: MagicMock

    def setUp(self):
        self.__mock_config_service = MagicMock()
        self.__mock_internal_http_client_service = MagicMock()
        self.__mock_division_gateway = AsyncMock()
        self.__mock_lookup = AsyncMock()

        self.__mock_config_service.get_current_config.return_value = Config(
            base_api_url='http://test.com.invalid',
            product_id='123',
            base_koddi_url='http://koddi.com.invalid'
            , pte_target_id='pte_target_id'
        )

        self.division_service = DivisionService(
            config_service=self.__mock_config_service,
            division_gateway=self.__mock_division_gateway,
            lookup=self.__mock_lookup
        )

    async def test_get_divisions_success(self):
        self.division_service.division_gateway.get_divisions.return_value = [
            DivisionServiceResponse(
                id="123",
                label="test division"
            )
        ]
        self.__mock_lookup.get_division_short_ids_by_division_items.return_value = [123]

        divisions = await self.division_service.get_divisions()
        self.assertEqual(len(divisions), 1)
        assert isinstance(divisions[0], Division)
        self.assertEqual(divisions[0].id, 123)
        self.assertEqual(divisions[0].name, 'test division')
        self.assertTrue(divisions[0].active)

        self.__mock_lookup.get_division_short_ids_by_division_items.assert_called_once()
        self.__mock_lookup.get_division_short_ids_by_division_items.assert_called_once()

    async def test_get_location_group_payload(self):
        division_ids = [1, 2, 3]
        self.__mock_lookup.get_division_details_by_short_id_batch.return_value = [
            CachedDivision(divisionNumber="1", bannerCode="banner1"),
            CachedDivision(divisionNumber="2", bannerCode="banner2"),
            CachedDivision(divisionNumber="3", bannerCode="banner3"),
        ]

        expected_payload = {
            "categories": [{
                "items": [
                    {"divisionNumber": "1", "bannerCode": "banner1"},
                    {"divisionNumber": "2", "bannerCode": "banner2"},
                    {"divisionNumber": "3", "bannerCode": "banner3"},
                ],
                "type": "division-banner"
            }]
        }

        payload = await self.division_service.get_location_group_payload(division_ids)

        self.assertEqual(payload, expected_payload)
        self.assertEqual(self.__mock_lookup.get_division_details_by_short_id_batch.call_count, 1)
        self.__mock_lookup.get_division_details_by_short_id_batch.assert_has_calls([
            call([1, 2, 3]),
        ])
        self.__mock_lookup.get_division_details_by_short_id_batch.assert_any_call([1, 2, 3])

    async def test_build_location_group_error_in_gateway(self):
        self.division_service.division_gateway.create_location_group.side_effect = HTTPException(
            status_code=400, detail="Failed to create location group")

        try:
            await self.division_service.build_location_group([])

        except HTTPException as ex:
            self.assertEqual(ex.status_code, 400)
            self.assertEqual(ex.detail, "Failed to create location group")

    async def test_build_location_group_empty_ad_group_division_targets(self):
        self.division_service.get_location_group_payload = AsyncMock()
        self.division_service.get_divisions = AsyncMock()

        self.division_service.get_divisions.return_value = [Division(id=1, name='division1', active=True),
                                                            Division(id=2, name='division2', active=True)]
        self.division_service.get_location_group_payload.return_value = {"categories": [{"items": [
            {"divisionNumber": "1", "bannerCode": "banner1"}, {"divisionNumber": "2", "bannerCode": "banner2"}],
                                                                                         "type": "division-banner"}]}
        self.division_service.division_gateway.create_location_group.return_value = LocationGroup(
            id="test_id",
            categories=[]
        )

        result = await self.division_service.build_location_group([])

        self.assertEqual("test_id", result)
        self.division_service.get_divisions.assert_called()
        self.division_service.get_divisions.assert_called()
        self.division_service.get_location_group_payload.assert_called_once_with([1, 2])
        self.division_service.division_gateway.create_location_group.assert_called_once()

    async def test_build_location_group_non_empty_ad_group_division_targets(self):
        self.division_service.get_location_group_payload = AsyncMock()
        self.division_service.get_location_group_payload.return_value = {"categories": [{"items": [
            {"divisionNumber": "1", "bannerCode": "banner1"}, {"divisionNumber": "2", "bannerCode": "banner2"}],
                                                                                         "type": "division-banner"}]}
        self.division_service.division_gateway.create_location_group.return_value = LocationGroup(id="test_id", categories=[])

        result = await self.division_service.build_location_group(
            [TargetAdgroupRequest(id=1, name='target1', type=1), TargetAdgroupRequest(id=2, name='target2', type=2)])

        self.assertEqual("test_id", result)
        self.division_service.get_location_group_payload.assert_called_once_with([1, 2])
        self.division_service.division_gateway.create_location_group.assert_called_once()
        self.division_service.division_gateway.create_location_group.assert_called_once_with(
            self.division_service.get_location_group_payload.return_value)

    async def test_get_division_ids_from_banners__returns_division_ids_from_banners(self):
        division_banners = ["a", "b", "c"]
        division_banner_items = [
            DivisionBannerItem(bannerCode="code", divisionNumber="1"),
            DivisionBannerItem(bannerCode="code", divisionNumber="2"),
            DivisionBannerItem(bannerCode="code", divisionNumber="3"),
        ]
        mock_location_groups = LocationGroupResponseData(found=[
            LocationGroup(id="1", categories=[
                LocationGroupCategory(type="division-banner", items=[
                    division_banner_items[0]
                ])
            ]),
            LocationGroup(id="2", categories=[
                LocationGroupCategory(type="division-banner", items=[
                    division_banner_items[1]
                ])
            ]),
            LocationGroup(id="3", categories=[
                LocationGroupCategory(type="division-banner", items=[
                    division_banner_items[2]
                ])
            ]),
        ])
        mock_division_ids = [91, 92, 93]
        self.__mock_division_gateway.get_location_groups.return_value = mock_location_groups
        self.__mock_lookup.get_division_short_ids_by_division_items.return_value = mock_division_ids

        result = await self.division_service.get_division_ids_from_banners(division_banners)

        self.assertEqual(mock_division_ids, result)
        self.__mock_division_gateway.get_location_groups.assert_called_once_with(division_banners)
        self.__mock_lookup.get_division_short_ids_by_division_items.assert_called_once_with(division_banner_items)

    @patch("logging.Logger.warning")
    async def test_get_division_ids_from_banners__handles_missing_division_ids(self, mock_logger_warning):
        division_banners = ["a", "b", "c", "d"]
        division_banner_items = [
            DivisionBannerItem(bannerCode="code", divisionNumber="1"),
            DivisionBannerItem(bannerCode="code", divisionNumber="2"),
            DivisionBannerItem(bannerCode="code", divisionNumber="3"),
        ]
        mock_location_groups = LocationGroupResponseData(
            found=[
                LocationGroup(id="1", categories=[
                    LocationGroupCategory(type="division-banner", items=[
                        division_banner_items[0]
                    ])
                ]),
                LocationGroup(id="2", categories=[
                    LocationGroupCategory(type="division-banner", items=[
                        division_banner_items[1]
                    ])
                ]),
                LocationGroup(id="3", categories=[
                    LocationGroupCategory(type="invalid-type", items=[
                        division_banner_items[2]
                    ])
                ]),
            ],
            notFound=["d"]
        )
        mock_division_ids = [91, None]
        self.__mock_division_gateway.get_location_groups.return_value = mock_location_groups
        self.__mock_lookup.get_division_short_ids_by_division_items.return_value = mock_division_ids

        result = await self.division_service.get_division_ids_from_banners(division_banners)

        self.assertEqual([91], result)
        self.__mock_division_gateway.get_location_groups.assert_called_once_with(division_banners)
        self.__mock_lookup.get_division_short_ids_by_division_items.assert_called_once_with(
            division_banner_items[:2]
        )
        mock_logger_warning.assert_has_calls([
            call('Location Groups not found for %s', mock_location_groups.notFound),
            call('Divisions missing from redis cache: %s', [division_banner_items[1]])
        ])

    async def test_get_divisions_not_saved_in_redis(self):
        self.division_service.division_gateway.get_divisions.return_value = [
            DivisionServiceResponse(
                id="123",
                label="test division",
                bannerCode="test code",
                divisionNumber="test number",
            )
        ]
        self.__mock_lookup.get_division_short_ids_by_division_items.return_value = [None]
        self.__mock_lookup.set_division_short_id_by_banner_code_and_division_number_batch.return_value = [123]

        divisions = await self.division_service.get_divisions()
        self.assertEqual(len(divisions), 1)
        assert isinstance(divisions[0], Division)
        self.assertEqual(divisions[0].id, 123)
        self.assertEqual(divisions[0].name, 'test division')
        self.assertTrue(divisions[0].active)
        self.division_service.division_gateway.get_divisions.assert_called_once()
        self.__mock_lookup.get_division_short_ids_by_division_items.assert_called_once()
