from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, call

from fastapi import HTTPException

from app.common.model.report import IdGroup, UniqueReportIds, ExternalIdByKoddiId, MissingLookupWarning
from app.common.translations.report_translation import ReportTranslation
from app.common.view_models.report import Dimensions
from app.v2.model.downstream.activation_service import ActivationsQueryBody
from app.common.model.downstream.bid_manager import Bid
from app.common.model.downstream.campaign_service import CampaignSearchRequest
from tests.utils_for_testing.auto_mock import auto_mock


class TestReportTranslation(IsolatedAsyncioTestCase):
    mock_lookup: AsyncMock
    mock_activation_gateway: AsyncMock
    mock_campaign_gateway: AsyncMock
    mock_bid_manager_service: AsyncMock

    def setUp(self):
        self.mock_lookup = AsyncMock()
        self.mock_activation_gateway = AsyncMock()
        self.mock_campaign_gateway = AsyncMock()
        self.mock_bid_manager_service = AsyncMock()

        self.report_translation = ReportTranslation(
            lookup = self.mock_lookup,
            activation_gateway = self.mock_activation_gateway,
            campaign_gateway = self.mock_campaign_gateway,
            bid_manager_service = self.mock_bid_manager_service,
        )

    async def test_build_translation__calls_functions_to_build_translation(self):
        # Arrange
        koddi_ids = [1234, 2345]
        long_ids = ["1234", None]
        short_ids = [4321, None]
        expected_short_id_by_koddi_id = {
            1234: 4321,
            2345: 5432
        }
        lookup_long_id_by_koddi_id = AsyncMock(return_value=long_ids)
        lookup_short_id_by_long_id = AsyncMock(return_value=short_ids)
        cache_long_id_by_koddi_id = AsyncMock()
        cache_short_id_by_long_id = AsyncMock()
        def mock_handle_missing_long_ids(missing_ids, id_groups_by_koddi_id):
            return {2345: IdGroup(koddi_id=2345, long_id="2345")}
        def mock_handle_missing_short_ids(missing_ids, id_groups_by_koddi_id):
            return {2345: IdGroup(koddi_id=2345, long_id="2345", short_id=5432)}
        handle_missing_long_ids = AsyncMock(side_effect=mock_handle_missing_long_ids)
        handle_missing_short_ids = AsyncMock(side_effect=mock_handle_missing_short_ids)

        # Act
        result = await self.report_translation.build_translation(
            koddi_ids,
            lookup_long_id_by_koddi_id,
            lookup_short_id_by_long_id,
            cache_long_id_by_koddi_id,
            cache_short_id_by_long_id,
            handle_missing_long_ids,
            handle_missing_short_ids
        )

        # Assert
        self.assertEqual(expected_short_id_by_koddi_id, result)
        lookup_long_id_by_koddi_id.assert_called_with(koddi_ids)
        lookup_short_id_by_long_id.assert_called_with(long_ids)
        handle_missing_long_ids.assert_called_with(
            [2345],
            {
                1234: IdGroup(koddi_id=1234, long_id="1234", short_id=4321, data=None),
                2345: IdGroup(koddi_id=2345, long_id=None, short_id=None, data=None)
            }
        )
        handle_missing_short_ids.assert_called_with(
            [2345],
            {
                1234: IdGroup(koddi_id=1234, long_id="1234", short_id=4321, data=None),
                2345: IdGroup(koddi_id=2345, long_id="2345", short_id=None, data=None)
            }
        )
        cache_long_id_by_koddi_id.assert_called_with({2345: "2345"})
        cache_short_id_by_long_id.assert_called_with({"2345": 5432})

    async def test_build_adgroup_translation__returns_mapping_when_everything_is_cached(self):
        # Arrange
        koddi_ad_group_ids = [1234, 2345]
        long_ids = ["1234", "2345"]
        short_ids = [4321, 5432]
        self.mock_lookup.get_adgroup_long_id_by_koddi_id_batch.return_value = long_ids
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = short_ids
        expected_mapping = {
            1234: 4321,
            2345: 5432
        }

        # Act
        result = await self.report_translation.build_ad_group_translation(koddi_ad_group_ids)

        # Assert
        self.assertEqual(expected_mapping, result)
        self.mock_lookup.get_adgroup_long_id_by_koddi_id_batch.assert_called_with(koddi_ad_group_ids)
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.assert_called_with(long_ids)
        self.mock_lookup.set_adgroup_long_id_by_koddi_id_batch.assert_not_called()
        self.mock_lookup.set_adgroup_short_id_by_long_id_batch.assert_not_called()

    async def test_build_adgroup_translation__fetches_adgroups_and_returns_mapping_when_everything_is_not_cached(self):
        # Arrange
        koddi_ad_group_ids = [1234, 2345, 3456]
        long_ids = ["1234", None, None]
        short_ids = [4321, None, None]
        mock_koddi_external_ids = MagicMock()
        mock_koddi_external_ids.get.side_effect = [
            2345,
            3456
        ]
        self.mock_lookup.get_adgroup_long_id_by_koddi_id_batch.return_value = long_ids
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.return_value = short_ids
        self.mock_activation_gateway.get_activations.side_effect = [
            auto_mock({
                "data": [{
                    "id": "2345",
                    "metadata": {"short_id": None}
                }],
            }, MagicMock()),
            auto_mock({
                "data": [{
                    "id": "3456",
                    "metadata": {"short_id": None}
                }],
            }, MagicMock()),
            auto_mock({
                "data": [
                    {
                        "id": "2345",
                        "metadata": {
                            "short_id": 5432,
                            "externalIDs": mock_koddi_external_ids
                        },
                    },
                    {
                        "id": "3456",
                        "metadata": {
                            "short_id": 6543,
                            "externalIDs": mock_koddi_external_ids
                        },
                    }
                ],
            }, MagicMock()),
        ]
        expected_mapping = {
            1234: 4321,
            2345: 5432,
            3456: 6543
        }

        # Act
        result = await self.report_translation.build_ad_group_translation(koddi_ad_group_ids)

        # Assert
        self.assertEqual(expected_mapping, result)
        self.mock_lookup.get_adgroup_long_id_by_koddi_id_batch.assert_called_with(koddi_ad_group_ids)
        self.mock_lookup.get_adgroup_short_id_by_long_id_batch.assert_called_with(long_ids)
        self.mock_lookup.set_adgroup_long_id_by_koddi_id_batch.assert_called_with({
            2345: "2345",
            3456: "3456"
        })
        self.mock_lookup.set_adgroup_short_id_by_long_id_batch.assert_called_with({
            "2345": 5432,
            "3456": 6543
        })
        self.mock_activation_gateway.get_activations.assert_has_calls([
            call(ActivationsQueryBody(koddi_id="2345")),
            call(ActivationsQueryBody(koddi_id="3456")),
            call(ActivationsQueryBody(ids=["2345", "3456"])),
        ])

    async def test_build_campaign_translation__fetches_campaigns_and_returns_mapping_when_everything_is_not_cached(self):
        # Arrange
        koddi_campaign_ids = [1234, 2345]
        long_ids = [None, None]
        short_ids = [None, None]
        expected_result = {
            1234: 4321,
            2345: 5432
        }
        self.mock_lookup.get_campaign_long_id_by_koddi_id_batch.return_value = long_ids
        self.mock_lookup.get_campaign_short_id_by_long_id_batch.return_value = short_ids
        self.mock_campaign_gateway.search_campaigns.side_effect = [
            auto_mock({
                "data": [
                    {
                        "id": "1234",
                        "shortId": 4321,
                        "externalIDs": [{
                            "id": 1234,
                            "partner": "KODDI_CAMPAIGN_ID"
                        }],
                    },
                    {
                        "id": "2345",
                        "shortId": 5432,
                        "externalIDs": [{
                            "id": 2345,
                            "partner": "KODDI_CAMPAIGN_ID"
                        }],
                    },
                ],
            }, MagicMock()),
        ]

        # Act
        result = await self.report_translation.build_campaign_translation(koddi_campaign_ids)

        # Assert
        self.assertEqual(expected_result, result)
        self.mock_lookup.get_campaign_long_id_by_koddi_id_batch.assert_called_with(koddi_campaign_ids)
        self.mock_lookup.get_campaign_short_id_by_long_id_batch.assert_called_with(long_ids)
        self.mock_lookup.set_campaign_long_id_by_koddi_id_batch.assert_called_with({
            1234: "1234",
            2345: "2345"
        })
        self.mock_lookup.set_campaign_short_id_by_long_id_batch.assert_called_with({
            "1234": 4321,
            "2345": 5432
        })
        self.mock_campaign_gateway.search_campaigns.assert_called_with(CampaignSearchRequest(
            externalPartner="KODDI_CAMPAIGN_ID",
            externalPartnerIDs=koddi_campaign_ids
        ))

    def test_build_advertiser_translation__builds_translation_from_koddi_id_dict(self):
        koddi_advertiser_ids = [1234, 2345]
        koddi_brand_ids = {
            1234: [
                IdGroup(koddi_id=1234, short_id=4321),
            ],
            2345: [
                IdGroup(koddi_id=2345, short_id=5432),
            ]
        }
        expected_result = {
            1234: 4321,
            2345: 5432
        }

        result = self.report_translation.build_advertiser_translation(koddi_advertiser_ids, koddi_brand_ids)

        self.assertEqual(expected_result, result)

    async def test_build_upc_translation__builds_translation_using_bid_manager(self):
        koddi_upcs = ["4011", "4012"]
        expected_result = {
            "4011": 1234,
            "4012": 2345
        }
        self.mock_bid_manager_service.bind_bids_to_entity_ids.return_value = [
            (Bid(id="4011"), 1234),
            (Bid(id="4012"), 2345),
        ]

        result = await self.report_translation.build_upc_translation(koddi_upcs)

        self.assertEqual(expected_result, result)
        self.mock_bid_manager_service.bind_bids_to_entity_ids.assert_called_with([
            Bid(id="4011"),
            Bid(id="4012")
        ])

    async def test_build_upc_translation__handles_none_upcs(self):
        koddi_upcs = ["4011", None]
        expected_result = {
            "4011": 1234
        }
        self.mock_bid_manager_service.bind_bids_to_entity_ids.return_value = [
            (Bid(id="4011"), 1234)
        ]

        result = await self.report_translation.build_upc_translation(koddi_upcs)

        self.assertEqual(expected_result, result)
        self.mock_bid_manager_service.bind_bids_to_entity_ids.assert_called_with([
            Bid(id="4011")
        ])

    async def test_handle_missing_ad_group_long_ids__handles_404(self):
        koddi_ids = [1234, 2345]
        self.mock_activation_gateway.get_activations.side_effect = [
            HTTPException(status_code=404),
            HTTPException(status_code=404)
        ]

        result = await self.report_translation.handle_missing_ad_group_long_ids(
            koddi_ids,
            {}
        )

        self.assertEqual({}, result)
        self.mock_activation_gateway.get_activations.assert_has_calls([
            call(ActivationsQueryBody(koddi_id=f"{koddi_ids[0]}")),
            call(ActivationsQueryBody(koddi_id=f"{koddi_ids[1]}"))
        ])

    async def test_handle_missing_ad_group_short_ids__handles_404(self):
        koddi_ids = [1234, 2345]
        long_ids = ["1234", "2345"]
        id_groups = {
            koddi_id: IdGroup(koddi_id=koddi_id, long_id=long_id)
            for koddi_id, long_id in zip(koddi_ids, long_ids)
        }
        self.mock_activation_gateway.get_activations.side_effect = [
            HTTPException(status_code=404)
        ]

        result = await self.report_translation.handle_missing_ad_group_short_ids(
            koddi_ids,
            id_groups
        )

        self.assertEqual({}, result)
        self.mock_activation_gateway.get_activations.assert_called_with(
            ActivationsQueryBody(ids=long_ids),
        )

    async def test_handle_missing_ad_group_short_ids__skips_calling_activation_service_if_there_are_no_ids(self):
        id_groups = {
            1234: IdGroup(koddi_id=1234),
        }

        result = await self.report_translation.handle_missing_ad_group_short_ids([1234], id_groups)

        self.assertEqual({}, result)
        self.mock_activation_gateway.get_activations.assert_not_called()

    async def test_handle_missing_campaign_ids__handles_404(self):
        koddi_ids = [1234, 2345]
        self.mock_campaign_gateway.search_campaigns.side_effect = [
            HTTPException(status_code=404)
        ]

        result = await self.report_translation.handle_missing_campaign_ids(
            koddi_ids,
            {}
        )

        self.assertEqual({}, result)
        self.mock_campaign_gateway.search_campaigns.assert_called_with(
            CampaignSearchRequest(
                externalPartner="KODDI_CAMPAIGN_ID",
                externalPartnerIDs=koddi_ids
            )
        )

    def test_build_missing_lookup_warnings__builds_warnings_from_missing_lookups(self):
        unique_ids = UniqueReportIds(
            advertiser_ids={1234},
            ad_group_ids={2345},
            campaign_ids={3456},
            upcs={"4011"}
        )
        lookups = ExternalIdByKoddiId()
        expected_warnings = [
            MissingLookupWarning(
                dimension=Dimensions.ADVERTISER_ID,
                ids=[1234]
            ),
            MissingLookupWarning(
                dimension=Dimensions.AD_GROUP_ID,
                ids=[2345]
            ),
            MissingLookupWarning(
                dimension=Dimensions.CAMPAIGN_ID,
                ids=[3456]
            ),
            MissingLookupWarning(
                dimension=Dimensions.ENTITY_ID,
                ids=["4011"]
            ),
        ]
        warnings = self.report_translation.build_missing_lookup_warnings(
            unique_ids,
            lookups
        )

        self.assertEqual(expected_warnings, warnings)