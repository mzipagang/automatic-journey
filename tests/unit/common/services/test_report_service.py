
from copy import deepcopy
from typing import Dict, List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from httpx import Response

from app.common.model.campaign_types import InternalCampaignType, KoddiReportExperienceType
from app.common.model.downstream.campaign_activation_service import (
    CASCampaign,
    ExternalId,
)
from app.common.model.downstream.campaign_service import CampaignsResponse
from app.common.model.report import IdGroup, MissingLookupWarning
from app.common.services.report_service import ReportService, ExperienceNameParamFactory
from app.common.view_models import KrogerError
from app.common.view_models.report import (
    Dimensions,
    Filter,
    FilterOperator,
    ReportResultHeader,
    ReportResultResponse,
    SortOrderCommon,
)
from app.v2.view_models.report import (
    DimensionsV1,
    MetricsV1,
    SortFieldV1,
    CarrouselInvalidDimensionsV1,
    ReportRequestV1
)
from app.v2.view_models.report import (
    DimensionsV2,
    MetricsV2,
    SortFieldV2,
    TOAInvalidMetricsV2,
    TOAInvalidDimensionsV2,
    CarrouselInvalidDimensionsV2,
    ReportRequestV2
)
from tests.unit.services.constants import (
    REPORT_RESPONSE_JSON,
    SIMPLE_REPORT_REQUEST,
    SIMPLE_REPORT_REQUEST_V2,
)


class TestReportService(IsolatedAsyncioTestCase):
    __mock_ad_group_service: AsyncMock
    __mock_lookup_service: AsyncMock
    __mock_internal_http_client_service: MagicMock
    __mock_koddi_http_client_service: MagicMock
    __mock_campaign_gateway: MagicMock

    __subject: ReportService

    def setUp(self) -> None:
        self.__mock_ad_group_service = AsyncMock()
        self.__mock_lookup_service = AsyncMock()
        self.__mock_internal_http_client_service = MagicMock()
        self.__mock_koddi_http_client_service = MagicMock()
        self.__mock_async_koddi_http_client_service = AsyncMock()
        self.__test_experience_name = InternalCampaignType.PLA
        self.__mock_campaign_gateway = AsyncMock()
        self.__mock_translation = AsyncMock()
        self.__mock_harness_service = MagicMock()
        self.__mock_harness_service.is_harness_flag_on.return_value = False

        self.__mock_translation.build_missing_lookup_warnings = MagicMock(return_value=[])
        self.__mock_translation.build_advertiser_translation = MagicMock()

        self.__subject = ReportService(
            koddi_http_client_service=self.__mock_koddi_http_client_service,
            async_koddi_http_client_service=self.__mock_async_koddi_http_client_service,
            lookup_service=self.__mock_lookup_service,
            campaign_gateway=self.__mock_campaign_gateway,
            translation=self.__mock_translation,
            harness_service=self.__mock_harness_service,
        )

    def __mock_translations(
        self,
        ad_group: Dict[int, int] = {},
        advertiser: Dict[int, int] = {},
        campaign: Dict[int, int] = {},
        upc: Dict[str, int] = {},
    ):
        self.__mock_translation.build_ad_group_translation.return_value = ad_group
        self.__mock_translation.build_campaign_translation.return_value = campaign
        self.__mock_translation.build_upc_translation.return_value = upc
        self.__mock_translation.build_advertiser_translation = MagicMock(return_value=advertiser)

    # ReportService.request_report tests
    @patch("logging.Logger.error")
    async def test_request_report__should_use_koddi_http_client(self, mock_logger_error: MagicMock):
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=500, json={"error": "Internal Server Error"}
        )

        report_request = deepcopy(SIMPLE_REPORT_REQUEST)

        with self.assertRaises(HTTPException) as context:
            await self.__subject.request_report(
                report_request=report_request,
                koddi_brand_ids={},
                experience_name=self.__test_experience_name,
            )

        self.__mock_koddi_http_client_service.post.assert_called_once_with(
            path="/console/v2/report/targeting",
            json={
                "advertiser_ids": [],
                "currency_code": "USD",
                "dimensions": ["campaign_id", "hour"],
                "end_date": "2025-03-30",
                "filters": [
                    {"field": "experience_name", "operation": "=", "value": [KoddiReportExperienceType.PLA]},
                ],
                "metrics": ["clicks", "win_rate", "hours_live"],
                "pagination": {"count": 100, "start": 0},
                "sort": [{"field": "clicks", "order": "DESC"}],
                "start_date": "2024-01-01",
            },
            response_body_type="json",
            forward_client_error_response_content=True,
        )

        mock_logger_error.assert_called_once()
        self.assertEqual("Reporting server unavailable. Try again later.", context.exception.detail)

    async def test_request_report__filters_are_remapped_to_koddi_filters(self):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        all_input_operators = [
            "EQUALS",
            "NOT_EQUALS",
            "GREATER_THAN",
            "GREATER_THAN_OR_EQUAL",
            "LESS_THAN",
            "LESS_THAN_OR_EQUAL",
            "LIKE_IN",
            "NOT_IN",
            "IS_NULL",
            "NOT_NULL",
            "NOT_LIKE",
            "BETWEEN",
        ]
        all_output_operators = [
            "=",
            "!=",
            ">",
            ">=",
            "<",
            "<=",
            "LIKE IN",
            "NOT IN",
            "IS NULL",
            "NOT NULL",
            "NOT LIKE",
            "BETWEEN",
        ]
        report_request.filters = list(
            map(lambda op: Filter(field="", values=[], operator=op), all_input_operators)
        )
        expected_output_filters = list(
            map(lambda op: {"field": "", "value": [], "operation": op}, all_output_operators)
        )
        expected_output_filters.append(
            {"field": "experience_name", "operation": "=", "value": [KoddiReportExperienceType.PLA]}
        )
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=500, json={"error": "Internal Server Error"}
        )

        # Act
        with self.assertRaises(HTTPException) as context:
            await self.__subject.request_report(
                report_request=report_request,
                koddi_brand_ids={},
                experience_name=self.__test_experience_name,
            )

        # Assert
        self.__mock_koddi_http_client_service.post.assert_called_once_with(
            path="/console/v2/report/targeting",
            json={
                "advertiser_ids": [],
                "currency_code": "USD",
                "dimensions": ["campaign_id", "hour"],
                "end_date": "2025-03-30",
                "filters": expected_output_filters,
                "metrics": ["clicks", "win_rate", "hours_live"],
                "pagination": {"count": 100, "start": 0},
                "sort": [{"field": "clicks", "order": "DESC"}],
                "start_date": "2024-01-01",
            },
            response_body_type="json",
            forward_client_error_response_content=True,
        )

    async def test_request_report__responds_with_server_unavailable_if_error_response_is_none(self):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=500, json={"code": 123, "error": None}
        )

        # Act
        with self.assertRaises(HTTPException) as context:
            await self.__subject.request_report(
                report_request=report_request,
                koddi_brand_ids={},
                experience_name=self.__test_experience_name,
            )

        # Assert
        self.assertEqual("Reporting server unavailable. Try again later.", context.exception.detail)

    async def test_request_report__responds_with_result_data_if_successful(self):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        expected_response = ReportResultResponse(
            headers=[
                ReportResultHeader(
                    name="campaign_id", type="number", title="Campaign ID (INTERNAL)"
                ),
                ReportResultHeader(name="clicks", type="number", title="Clicks"),
                ReportResultHeader(name="win_rate", type="percentage", title="Win Rate %"),
                ReportResultHeader(name="hours_live", type="percentage", title="Time Live"),
                ReportResultHeader(name="hour", type="decimal", title="Hour"),
            ],
            data=[
                {
                    "campaign_id": 1,
                    "clicks": 0,
                    "hour": 3,
                    "hours_live": 0.96258851,
                    "win_rate": 0.00046119,
                }
            ],
            totalCount=1,
        )
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(campaign={1234567: 1})

        # Act
        response = await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids={},
            experience_name=self.__test_experience_name,
        )

        # Assert
        self.assertEqual(expected_response, response)

    async def test_request_report__converts_koddi_advertiser_to_internal_brand_id(self):
        # Arrange
        koddi_advertiser_id = 1234
        internal_advertiser_id = 5467
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_request.dimensions.append(Dimensions.ADVERTISER_ID)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"][0]["advertiser_id"] = koddi_advertiser_id
        koddi_brand_ids = {
            koddi_advertiser_id: [
                IdGroup(koddi_id=koddi_advertiser_id, short_id=internal_advertiser_id)
            ]
        }
        expected_response = ReportResultResponse(
            headers=[
                ReportResultHeader(
                    name="campaign_id", type="number", title="Campaign ID (INTERNAL)"
                ),
                ReportResultHeader(name="clicks", type="number", title="Clicks"),
                ReportResultHeader(name="win_rate", type="percentage", title="Win Rate %"),
                ReportResultHeader(name="hours_live", type="percentage", title="Time Live"),
                ReportResultHeader(name="hour", type="decimal", title="Hour"),
            ],
            data=[
                {
                    "campaign_id": 1,
                    "advertiser_id": internal_advertiser_id,
                    "advertiser_ids": [internal_advertiser_id],
                    "clicks": 0,
                    "hour": 3,
                    "hours_live": 0.96258851,
                    "win_rate": 0.00046119,
                }
            ],
            totalCount=1,
        )
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(
            advertiser={koddi_advertiser_id: internal_advertiser_id}, campaign={1234567: 1}
        )

        # Act
        response = await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids=koddi_brand_ids,
            experience_name=self.__test_experience_name,
        )

        # Assert
        self.assertEqual(expected_response, response)

    async def test_request_report__converts_koddi_ad_group_to_internal_ad_group(self):
        # Arrange
        koddi_ad_group_id = 1234
        internal_ad_group_id = 5467
        expected_ad_group_id = 9101
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_request.dimensions.append(Dimensions.AD_GROUP_ID)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"][0]["ad_group_id"] = koddi_ad_group_id
        expected_response = ReportResultResponse(
            headers=[
                ReportResultHeader(
                    name="campaign_id", type="number", title="Campaign ID (INTERNAL)"
                ),
                ReportResultHeader(name="clicks", type="number", title="Clicks"),
                ReportResultHeader(name="win_rate", type="percentage", title="Win Rate %"),
                ReportResultHeader(name="hours_live", type="percentage", title="Time Live"),
                ReportResultHeader(name="hour", type="decimal", title="Hour"),
            ],
            data=[
                {
                    "campaign_id": 1,
                    "ad_group_id": expected_ad_group_id,
                    "clicks": 0,
                    "hour": 3,
                    "hours_live": 0.96258851,
                    "win_rate": 0.00046119,
                }
            ],
            totalCount=1,
        )
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(
            ad_group={koddi_ad_group_id: expected_ad_group_id}, campaign={1234567: 1}
        )

        # Act
        response = await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids={},
            experience_name=self.__test_experience_name,
        )

        # Assert
        self.assertEqual(expected_response, response)

    async def test_request_report__converts_koddi_entity_id_to_internal_product_id(self):
        # Arrange
        koddi_product_id = "1234"
        internal_product_id = 5678
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_request.dimensions.append(Dimensions.ENTITY_ID)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"][0]["entity_id"] = koddi_product_id
        expected_response = ReportResultResponse(
            headers=[
                ReportResultHeader(
                    name="campaign_id", type="number", title="Campaign ID (INTERNAL)"
                ),
                ReportResultHeader(name="clicks", type="number", title="Clicks"),
                ReportResultHeader(name="win_rate", type="percentage", title="Win Rate %"),
                ReportResultHeader(name="hours_live", type="percentage", title="Time Live"),
                ReportResultHeader(name="hour", type="decimal", title="Hour"),
            ],
            data=[
                {
                    "campaign_id": 1,
                    "entity_id": internal_product_id,
                    "clicks": 0,
                    "hour": 3,
                    "hours_live": 0.96258851,
                    "win_rate": 0.00046119,
                }
            ],
            totalCount=1,
        )
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(upc={koddi_product_id: internal_product_id}, campaign={1234567: 1})

        # Act
        response = await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids={},
            experience_name=self.__test_experience_name,
        )

        # Assert
        self.assertEqual(expected_response, response)

    async def test_request_report__converts_koddi_purchased_entity_id_to_internal_product_id(self):
        # Arrange
        koddi_product_id = "1234"
        internal_product_id = 5678
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_request.dimensions.append(Dimensions.PURCHASED_ENTITY_ID)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"][0]["purchased_entity_id"] = koddi_product_id
        expected_response = ReportResultResponse(
            headers=[
                ReportResultHeader(
                    name="campaign_id", type="number", title="Campaign ID (INTERNAL)"
                ),
                ReportResultHeader(name="clicks", type="number", title="Clicks"),
                ReportResultHeader(name="win_rate", type="percentage", title="Win Rate %"),
                ReportResultHeader(name="hours_live", type="percentage", title="Time Live"),
                ReportResultHeader(name="hour", type="decimal", title="Hour"),
            ],
            data=[
                {
                    "campaign_id": 1,
                    "purchased_entity_id": internal_product_id,
                    "clicks": 0,
                    "hour": 3,
                    "hours_live": 0.96258851,
                    "win_rate": 0.00046119,
                }
            ],
            totalCount=1,
        )
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(upc={koddi_product_id: internal_product_id}, campaign={1234567: 1})

        # Act
        response = await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids={},
            experience_name=self.__test_experience_name,
        )

        # Assert
        self.assertEqual(expected_response, response)

    async def test_request_report__caches_koddi_campaign_ids(self):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"] = [
            {"campaign_id": 1234},
            {"campaign_id": 1234},
            {"campaign_id": 5678},
            {"campaign_id": 5678},
        ]
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(campaign={1234: 4321, 5678: 8765})

        # Act
        await self.__subject.request_report(report_request, {}, self.__test_experience_name)

        # Assert
        self.__mock_translation.build_campaign_translation.assert_called_with({1234, 5678})

    async def test_request_report__skips_caching_for_already_cached_campaigns(self):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"] = [{"campaign_id": 1234}, {"campaign_id": 5678}]
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )

        # Act
        await self.__subject.request_report(report_request, {}, self.__test_experience_name)

        # Assert
        self.__mock_campaign_gateway.get_campaigns_by_koddi_campaign_ids.assert_not_called()
        self.__mock_campaign_gateway.cache_koddi_campaign_ids_from_campaigns.assert_not_called()

    async def test_request_report__can_generate_reports_for_carousels(self):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )

        expected_request = {
            "advertiser_ids": [],
            "currency_code": "USD",
            "dimensions": ["campaign_id", "hour"],
            "end_date": "2025-03-30",
            "filters": [
                {
                    "field": "experience_name",
                    "operation": "=",
                    "value": [KoddiReportExperienceType.CAROUSEL],
                }
            ],
            "metrics": ["clicks", "win_rate", "hours_live"],
            "pagination": {"count": 100, "start": 0},
            "sort": [{"field": "clicks", "order": "DESC"}],
            "start_date": "2024-01-01",
        }

        await self.__subject.request_report(report_request, {}, InternalCampaignType.CAROUSEL)

        self.__mock_koddi_http_client_service.post.assert_called_with(
            path="/console/v2/report/targeting",
            json=expected_request,
            response_body_type="json",
            forward_client_error_response_content=True,
        )

    async def test_request_report__can_get_new_metrics_pla(self):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST_V2)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )

        expected_request = {
            "advertiser_ids": [],
            "currency_code": "USD",
            "dimensions": ["campaign_id", "hour"],
            "end_date": "2025-03-30",
            "filters": [
                {"field": "experience_name", "operation": "=", "value": [InternalCampaignType.PLA]}
            ],
            "metrics": [
                "clicks",
                "win_rate",
                "hours_live",
                "unique_user_conversions",
                "unique_user_impressions",
                "viewed_conversion_rate",
                "viewed_unit_price_avg",
            ],
            "pagination": {"count": 100, "start": 0},
            "sort": [{"field": "clicks", "order": "DESC"}],
            "start_date": "2024-01-01",
        }

        await self.__subject.request_report(report_request, {}, InternalCampaignType.PLA)

        self.__mock_koddi_http_client_service.post.assert_called_with(
            path="/console/v2/report/targeting",
            json=expected_request,
            response_body_type="json",
            forward_client_error_response_content=True,
        )

    async def test_request_report__can_get_new_dimensions_toa(self):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST_V2)
        report_request.dimensions.append(DimensionsV2.CREATIVE_KEY)
        report_request.dimensions.append(DimensionsV2.CREATIVE_NAME)
        report_request.dimensions.append(DimensionsV2.SEGMENT_IDS)
        report_request.dimensions.append(DimensionsV2.ENTITY_GROUP)
        report_request.dimensions.append(DimensionsV2.ENTITY_GROUP_ID)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["headers"].extend(
            [
                {"name": "creative_key", "type": "text", "title": "Creative Key"},
                {"name": "creative_name", "type": "text", "title": "Creative Name"},
                {"name": "entity_group", "type": "text", "title": "Entity Group"},
                {"name": "entity_group_id", "type": "number", "title": "Entity Group ID"},
                {"name": "segment_ids", "type": "text", "title": "Audience Segment"},
            ]
        )
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        expected_request = {
            "advertiser_ids": [],
            "currency_code": "USD",
            "dimensions": ["campaign_id", "hour", "creative_key", "creative_name", "segment_ids", "entity_group", "entity_group_id"],
            "end_date": "2025-03-30",
            "filters": [
                {"field": "experience_name", "operation": "=", "value": [InternalCampaignType.PLA]}
            ],
            "metrics": [
                "clicks",
                "win_rate",
                "hours_live",
                "unique_user_conversions",
                "unique_user_impressions",
                "viewed_conversion_rate",
                "viewed_unit_price_avg",
            ],
            "pagination": {"count": 100, "start": 0},
            "sort": [{"field": "clicks", "order": "DESC"}],
            "start_date": "2024-01-01",
        }

        await self.__subject.request_report(report_request, {}, InternalCampaignType.PLA)

        self.__mock_koddi_http_client_service.post.assert_called_with(
            path="/console/v2/report/targeting",
            json=expected_request,
            response_body_type="json",
            forward_client_error_response_content=True,
        )

    # Test ReportService.__create_filters
    async def test_create_filters__should_return_empty_list_when_no_filters(self):
        # Arrange
        filters = []
        expected_result = []

        # Act
        result = await self.__subject._ReportService__create_filters(filters)

        # Assert
        self.assertEqual(result, expected_result)

    async def test_create_filters__should_return_correct_filters(self):
        # Arrange
        filters = [
            Filter(field="field1", values=["value1"], operator="EQUALS"),
            Filter(field="field2", values=["value2"], operator="NOT_EQUALS"),
            Filter(field="field3", values=["value3"], operator="BETWEEN"),
        ]
        expected_result = [
            {"field": "field1", "operation": "=", "value": ["value1"]},
            {"field": "field2", "operation": "!=", "value": ["value2"]},
            {"field": "field3", "operation": "BETWEEN", "value": ["value3"]},
        ]

        # Act
        result = await self.__subject._ReportService__create_filters(filters)

        # Assert
        self.assertEqual(result, expected_result)

    @patch(
        "app.common.services.report_service.ReportService._ReportService__translate_internal_short_campaign_id_to_koddi_id"
    )
    async def test_create_filters_with_campaign_id__should_return_correct_filters(
        self, mock_translate_internal_short_campaign_id_to_koddi_id: AsyncMock
    ):
        # Arrange
        filters = [
            Filter(field="campaign_id", values=["value1"], operator="EQUALS"),
        ]
        expected_result = [
            {"field": "campaign_id", "operation": "=", "value": ["translated_value"]},
        ]
        mock_translate_internal_short_campaign_id_to_koddi_id.return_value = ["translated_value"]

        # Act
        result = await self.__subject._ReportService__create_filters(filters)

        # Assert
        self.assertEqual(result, expected_result)
        mock_translate_internal_short_campaign_id_to_koddi_id.assert_called_once_with(["value1"])

    async def test_translate_existing_internal_short_campaign_id_to_koddi_id__should_return_koddi_id(
        self,
    ):
        # Arrange
        short_campaign_ids = ["1234"]
        expected_koddi_id = ["5678"]
        (self.__mock_lookup_service.get_koddi_campaign_id_by_short_id_batch).return_value = (
            expected_koddi_id
        )

        # Act
        result = (
            await (
                self.__subject._ReportService__translate_internal_short_campaign_id_to_koddi_id(
                    short_campaign_ids
                )
            )
        )

        # Assert
        self.assertEqual(result, expected_koddi_id)
        self.__mock_lookup_service.get_koddi_campaign_id_by_short_id_batch.assert_called_once_with(
            short_campaign_ids
        )

    @patch(
        "app.common.services.report_service.ReportService._ReportService__search_and_save_koddi_campaign_ids"
    )
    async def test_non_existing_internal_short_campaign_id_to_koddi_id__should_return_koddi_id(
        self, mock_search_and_save_koddi_campaign_ids: AsyncMock
    ):
        # Arrange
        short_campaign_ids = ["1234", "5678"]
        expected_koddi_id = ["112233", "90123"]
        (self.__mock_lookup_service.get_koddi_campaign_id_by_short_id_batch).return_value = [
            "90123",
            None,
        ]
        mock_search_and_save_koddi_campaign_ids.return_value = ["112233"]

        # Act
        result = (
            await (
                self.__subject._ReportService__translate_internal_short_campaign_id_to_koddi_id(
                    short_campaign_ids
                )
            )
        )

        # Assert
        self.assertEqual(result, expected_koddi_id)
        self.__mock_lookup_service.get_koddi_campaign_id_by_short_id_batch.assert_called_once_with(
            short_campaign_ids
        )
        mock_search_and_save_koddi_campaign_ids.assert_called_once_with(
            short_campaign_ids, ["90123", None]
        )

    async def test_search_and_save_koddi_campaign_ids_koddi_id_not_found__should_return_empty_list(
        self,
    ):
        # Arrange
        short_campaign_ids = ["1234", "5678"]
        koddi_campaign_ids = ["90123", None]
        self.__mock_campaign_gateway.search_campaigns.return_value = CampaignsResponse(data=[])

        # Act
        result = await self.__subject._ReportService__search_and_save_koddi_campaign_ids(
            short_campaign_ids, koddi_campaign_ids
        )

        # Assert
        self.assertEqual(result, [])
        self.__mock_campaign_gateway.search_campaigns.assert_called_once()

    async def test_search_and_save_koddi_campaign_ids_one_koddi_id_not_found__should_raise_exception(
        self,
    ):
        # Arrange
        short_campaign_ids = ["1234", "5678"]
        koddi_campaign_ids = [None, None]
        self.__mock_campaign_gateway.search_campaigns.return_value = CampaignsResponse(
            data=[
                CASCampaign(
                    id="abcd-efaa-1234",
                    externalIDs=[ExternalId(id="91230", partner="KODDI_CAMPAIGN_ID")],
                )
            ]
        )

        # Act
        with self.assertRaises(HTTPException) as context:
            await self.__subject._ReportService__search_and_save_koddi_campaign_ids(
                short_campaign_ids, koddi_campaign_ids
            )

        # Assert
        self.assertEqual(
            str(context.exception), "400: Error trying to get some campaigns information"
        )
        self.__mock_campaign_gateway.search_campaigns.assert_called_once()

    async def test_search_and_save_koddi_campaign__should_return_koddi_id(self):
        # Arrange
        short_campaign_ids = ["1234", "5678"]
        koddi_campaign_ids = [None, None]
        self.__mock_campaign_gateway.search_campaigns.return_value = CampaignsResponse(
            data=[
                CASCampaign(
                    id="abcd-efaa-1234",
                    shortId="1234",
                    externalIDs=[ExternalId(id="90123", partner="KODDI_CAMPAIGN_ID")],
                ),
                CASCampaign(
                    id="abce-baca-1234",
                    shortId="5678",
                    externalIDs=[ExternalId(id="3210", partner="KODDI_CAMPAIGN_ID")],
                ),
            ]
        )

        # Act
        result = await self.__subject._ReportService__search_and_save_koddi_campaign_ids(
            short_campaign_ids, koddi_campaign_ids
        )

        # Assert
        self.assertEqual(result, ["90123", "3210"])
        self.__mock_campaign_gateway.search_campaigns.assert_called_once()

    @patch("logging.Logger.warning")
    async def test_request_report__logs_missing_id_lookups(self, mock_logger_warning):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(campaign={1234567: 1})
        mock_missing_lookup_warnings = [
            MissingLookupWarning(dimension=Dimensions.AD_GROUP_ID, ids=[12345])
        ]
        self.__mock_translation.build_missing_lookup_warnings.return_value = (
            mock_missing_lookup_warnings
        )

        # Act
        await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids={},
            experience_name=self.__test_experience_name,
        )

        # Assert
        mock_logger_warning.assert_called_with(
            "Could not convert some Koddi ids to external short ids: %s",
            [warning.model_dump() for warning in mock_missing_lookup_warnings],
        )

    def test_validate_report_filter_and_sort__raises_error_for_missing_metrics_and_dimensions(self):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_request.sort.append(SortFieldV1(field=MetricsV1.COST, order=SortOrderCommon.DESC))
        report_request.sort.append(
            SortFieldV1(field=DimensionsV1.CAMPAIGN_NAME, order=SortOrderCommon.DESC)
        )
        report_request.filters.append(
            Filter(field=MetricsV1.COST, operator=FilterOperator.GREATER_THAN, values=["0"])
        )
        report_request.filters.append(
            Filter(
                field=DimensionsV1.CAMPAIGN_NAME,
                operator=FilterOperator.EQUALS,
                values=["My cool campaign"],
            )
        )
        report_request.filters.append(
            Filter(field="bananas", operator=FilterOperator.EQUALS, values=["bananas"])
        )

        with self.assertRaises(HTTPException) as context:
            self.__subject.validate_request_filter_and_sort(report_request=report_request,experience_name=InternalCampaignType.PLA)

        self.assertIsNotNone(context)
        detail: dict = context.exception.detail
        errors: List[KrogerError] = detail["errors"]
        self.assertEqual(5, len(errors))
        self.assertEqual("filters-with-missing-metrics", errors[0].code)
        self.assertEqual("filters-with-missing-dimensions", errors[1].code)
        self.assertEqual("filters-with-invalid-values", errors[2].code)
        self.assertEqual("sorts-with-missing-metrics", errors[3].code)
        self.assertEqual("sorts-with-missing-dimensions", errors[4].code)

    def test_validate_report_filter_and_sort__raises_error_for_missing_metrics_and_dimensions_in_v2(
        self,
    ):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST_V2)
        report_request.sort.append(SortFieldV2(field=MetricsV2.COST, order=SortOrderCommon.DESC))
        report_request.sort.append(
            SortFieldV2(field=DimensionsV2.CAMPAIGN_NAME, order=SortOrderCommon.DESC)
        )
        report_request.filters.append(
            Filter(field=MetricsV2.COST, operator=FilterOperator.GREATER_THAN, values=["0"])
        )
        report_request.filters.append(
            Filter(
                field=DimensionsV2.CAMPAIGN_NAME,
                operator=FilterOperator.EQUALS,
                values=["My cool campaign"],
            )
        )
        report_request.filters.append(
            Filter(field="bananas", operator=FilterOperator.EQUALS, values=["bananas"])
        )

        with self.assertRaises(HTTPException) as context:
            self.__subject.validate_request_filter_and_sort(report_request=report_request,experience_name=InternalCampaignType.PLA)

        self.assertIsNotNone(context)
        detail: dict = context.exception.detail
        errors: List[KrogerError] = detail["errors"]
        self.assertEqual(5, len(errors))
        self.assertEqual("filters-with-missing-metrics", errors[0].code)
        self.assertEqual("filters-with-missing-dimensions", errors[1].code)
        self.assertEqual("filters-with-invalid-values", errors[2].code)
        self.assertEqual("sorts-with-missing-metrics", errors[3].code)
        self.assertEqual("sorts-with-missing-dimensions", errors[4].code)

    def test_validate_report_filter_and_sort__validates_v2_filters_for_v2_request(self):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST_V2)
        report_request.sort.append(SortFieldV2(field=MetricsV2.SHARE_OF_VOICE, order=SortOrderCommon.DESC))
        report_request.sort.append(
            SortFieldV2(field=DimensionsV2.CREATIVE_NAME, order=SortOrderCommon.DESC)
        )
        report_request.filters.append(
            Filter(field=MetricsV2.SHARE_OF_VOICE, operator=FilterOperator.GREATER_THAN, values=["0"])
        )
        report_request.filters.append(
            Filter(
                field=DimensionsV2.CREATIVE_NAME,
                operator=FilterOperator.EQUALS,
                values=["My cool video"],
            )
        )

        with self.assertRaises(HTTPException) as context:
            self.__subject.validate_request_filter_and_sort(report_request=report_request,experience_name=InternalCampaignType.PLA)

        self.assertIsNotNone(context)
        detail: dict = context.exception.detail
        errors: List[KrogerError] = detail["errors"]
        self.assertEqual(4, len(errors))
        self.assertEqual("filters-with-missing-metrics", errors[0].code)
        self.assertEqual("filters-with-missing-dimensions", errors[1].code)
        self.assertEqual("sorts-with-missing-metrics", errors[2].code)
        self.assertEqual("sorts-with-missing-dimensions", errors[3].code)

    async def test_request_report__handles_none_id_values(self):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"].append({
            "campaign_id": None,
            "entity_id": None,
            "clicks": 0,
            "hour": 4,
            "hours_live": 0.96258851,
            "win_rate": 0.00046119,
        })
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200,
            json=report_response
        )
        self.__mock_translations(
            campaign={1234567: 1}
        )
        self.__mock_translation.build_missing_lookup_warnings.return_value = []

        # Act
        result = await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids={},
            experience_name=self.__test_experience_name
        )

        # Assert
        self.assertIsNone(result.data[1]["campaign_id"])

    @patch("logging.Logger.error")
    async def test_request_report__uses_async_client_when_toggled(
            self,
            mock_logger_error
    ):
        self.__mock_harness_service.is_harness_flag_on.return_value = True
        self.__mock_async_koddi_http_client_service.post.return_value = Response(
            status_code=500, json={"error": "Internal Server Error"}
        )

        report_request = deepcopy(SIMPLE_REPORT_REQUEST)

        with self.assertRaises(HTTPException) as context:
            await self.__subject.request_report(
                report_request=report_request,
                koddi_brand_ids={},
                experience_name=self.__test_experience_name,
            )

        self.__mock_async_koddi_http_client_service.post.assert_called_once_with(
            path="/console/v2/report/targeting",
            json={
                "advertiser_ids": [],
                "currency_code": "USD",
                "dimensions": ["campaign_id", "hour"],
                "end_date": "2025-03-30",
                "filters": [
                    {"field": "experience_name", "operation": "=", "value": [KoddiReportExperienceType.PLA]}
                ],
                "metrics": ["clicks", "win_rate", "hours_live"],
                "pagination": {"count": 100, "start": 0},
                "sort": [{"field": "clicks", "order": "DESC"}],
                "start_date": "2024-01-01",
            },
            response_body_type="json",
            forward_client_error_response_content=True,
        )

        mock_logger_error.assert_called_once()
        self.assertEqual("Reporting server unavailable. Try again later.", context.exception.detail)


    def test_experience_type_carousel_v1(self):
        metrics, dimensions = ExperienceNameParamFactory.get_valid_params(
            InternalCampaignType.CAROUSEL,
            MagicMock(spec=ReportRequestV1)
        )
        self.assertEqual(metrics, set(MetricsV1))
        self.assertEqual(dimensions, set(DimensionsV1) - set(CarrouselInvalidDimensionsV1))

    def test_experience_type_pla_v1(self):
        metrics, dimensions = ExperienceNameParamFactory.get_valid_params(
            InternalCampaignType.PLA,
            MagicMock(spec=ReportRequestV1)
        )
        self.assertEqual(metrics, set(MetricsV1))
        self.assertEqual(dimensions, set(DimensionsV1))

    def test_experience_type_toa_v2(self):
        metrics, dimensions = ExperienceNameParamFactory.get_valid_params(
            InternalCampaignType.TOA,
            MagicMock(spec=ReportRequestV2)
        )
        self.assertEqual(metrics, set(MetricsV2) - set(TOAInvalidMetricsV2))
        self.assertEqual(dimensions, set(DimensionsV2) - set(TOAInvalidDimensionsV2))

    def test_experience_type_carousel_v2(self):
        metrics, dimensions = ExperienceNameParamFactory.get_valid_params(
            InternalCampaignType.CAROUSEL,
            MagicMock(spec=ReportRequestV2)
        )
        self.assertEqual(metrics, set(MetricsV2))
        self.assertEqual(dimensions, set(DimensionsV2) - set(CarrouselInvalidDimensionsV2))

    def test_experience_type_pla_v2(self):
        metrics, dimensions = ExperienceNameParamFactory.get_valid_params(
            InternalCampaignType.PLA,
            MagicMock(spec=ReportRequestV2)
        )
        self.assertEqual(metrics, set(MetricsV2))
        self.assertEqual(dimensions, set(DimensionsV2))

    def test_validate_request_filter_and_sort__raises_error_for_unavailable_metrics(self):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        # Add an invalid metric
        report_request.metrics.append("invalid_metric")
        with self.assertRaises(HTTPException) as context:
            self.__subject.validate_request_filter_and_sort(report_request=report_request,
                                                            experience_name=InternalCampaignType.PLA)
        errors = context.exception.detail["errors"]
        self.assertTrue(any(e.code == "metrics-with-invalid-values" for e in errors))


    def test_validate_request_filter_and_sort__raises_error_for_unavailable_dimensions(self):
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        # Add an invalid dimension
        report_request.dimensions.append("invalid_dimension")
        with self.assertRaises(HTTPException) as context:
            self.__subject.validate_request_filter_and_sort(report_request=report_request,
                                                            experience_name=InternalCampaignType.PLA)
        errors = context.exception.detail["errors"]
        self.assertTrue(any(e.code == "dimensions-with-invalid-values" for e in errors))

    async def test_request_report__adds_advertiser_ids_to_report_items(self):
        # Arrange
        report_request = deepcopy(SIMPLE_REPORT_REQUEST)
        report_request.dimensions.append(DimensionsV2.ADVERTISER_ID)
        koddi_advertiser_id = 4321
        report_response = deepcopy(REPORT_RESPONSE_JSON)
        report_response["result"]["data"][0]["advertiser_id"] = koddi_advertiser_id
        self.__mock_koddi_http_client_service.post.return_value = Response(
            status_code=200, json=report_response
        )
        self.__mock_translations(campaign={1234567: 1})
        self.__mock_translation.build_advertiser_translation.return_value = {
            koddi_advertiser_id: 1234
        }

        # Act
        response = await self.__subject.request_report(
            report_request=report_request,
            koddi_brand_ids={koddi_advertiser_id: [
                IdGroup(short_id=1234, koddi_id=koddi_advertiser_id),
                IdGroup(short_id=2345, koddi_id=koddi_advertiser_id),
            ]},
            experience_name=self.__test_experience_name,
        )

        # Assert
        self.assertEqual(1234, response.data[0]["advertiser_id"])
        self.assertEqual([1234, 2345], response.data[0]["advertiser_ids"])