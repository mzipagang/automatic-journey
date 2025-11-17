import unittest
from copy import deepcopy
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.common.model.campaign_types import CampaignType, InternalCampaignType
from app.common.view_models.report import ReportResultResponse, ReportResultHeader
from app.common.context.context import logging_extra_context
from app.common.model.advertiser import CachedAdvertiser
from app.v2.controllers.report import submit_report_v2
from app.v2.view_models.report import ReportRequestV2, DimensionsV2, MetricsV2


class TestReport(unittest.IsolatedAsyncioTestCase):
    __mock_report_service: AsyncMock
    __mock_advertiser_service: MagicMock

    __SIMPLE_REPORT_REQUEST = ReportRequestV2(
            advertiserIds=[1],
            startDate="2021-01-01",
            metrics=["click_through_rate", 'share_of_voice', 'opportunities'],
            endDate="2021-01-31",
            dimensions=["placement"],
            filters=[],
            sort=[],
            pagination={"offset": 0, "size": 10}
        )

    def setUp(self):
        self.__mock_report_service = AsyncMock()
        self.__mock_advertiser_service = AsyncMock()
        self.__current_user = {
            'internal': False,
            'brands': ['1', '2'],
            'email': 'user@example.com.invalid',
            'is_agency': False
        }
        self.__mock_advertiser_service.get_advertisers_by_numeric_ids.return_value = [CachedAdvertiser(
            brandId="1",
            name="Test Advertiser",
            accountId=1,
            description="Test Description",
            active=True
        )]
        self.__mock_advertiser_service.get_koddi_advertisers_for_reporting.return_value = [1]
        self.__mock_advertiser_service.get_advertisers_for_user.return_value = []

        self.__mock_report_service.validate_request_report_dates = MagicMock()
        self.__mock_report_service.validate_request_filter_and_sort = MagicMock()

    @pytest.mark.asyncio
    @patch("logging.Logger.info")
    @patch("logging.Logger.critical")
    async def test_report__should_succeed__should_log_counts(
            self,
            mock_logger_critical: MagicMock,
            mock_logger_info: MagicMock
    ):
        logging_extra_context.set({})
        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[],
            data=[{}],
            totalCount=1
        )

        report_request = self.__SIMPLE_REPORT_REQUEST

        await submit_report_v2(report_request=report_request,
                               experience_name=CampaignType.CAROUSEL,
                               current_user=self.__current_user,
                               report_service=self.__mock_report_service,
                               advertiser_service=self.__mock_advertiser_service)

        mock_logger_critical.assert_not_called()
        mock_logger_info.assert_called_with(
            'REPORT; User: %s, Koddi count: %d, Returned count: %d, '
            'Requested size: %d, Offset: %d, Advertisers: [%s]', 'user@example.com.invalid', 1, 1, 10, 0, '1')

        expected_context = {'reporting': {'advertiserIds': [1],
               'dimensions': ['placement'],
               'endDate': '2021-01-31',
               'filters': [],
               'metrics': ['click_through_rate', 'share_of_voice', 'opportunities' ],
               'pagination': {'offset': 0, 'size': 10},
               'sort': [],
               'startDate': '2021-01-01'}}
        self.assertEqual(expected_context, logging_extra_context.get())

    @pytest.mark.asyncio
    @patch("logging.Logger.info")
    @patch("logging.Logger.critical")
    async def test_report__count_mismatch_with_subsequent_offset__should_not_log_critical_count_mismatch(
            self,
            mock_logger_critical: MagicMock,
            mock_logger_info: MagicMock
    ):
        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[],
            data=[{}],
            totalCount=2
        )

        report_request = deepcopy(self.__SIMPLE_REPORT_REQUEST)
        report_request.pagination.offset = 1


        await submit_report_v2(report_request=report_request,
                               experience_name=CampaignType.CAROUSEL,
                               current_user=self.__current_user,
                               report_service=self.__mock_report_service,
                               advertiser_service=self.__mock_advertiser_service)

        mock_logger_critical.assert_not_called()
        mock_logger_info.assert_called_with('REPORT; User: %s, Koddi count: %d, Returned count: %d, '
                                            'Requested size: %d, Offset: %d, Advertisers: [%s]',
                                            'user@example.com.invalid', 2, 1, 10, 1, '1')

    @pytest.mark.asyncio
    @patch("logging.Logger.info")
    @patch("logging.Logger.critical")
    async def test_report__count_mismatch_with_subsequent_offset__should_not_log_critical_count_mismatch_another(
            self,
            mock_logger_critical: MagicMock,
            mock_logger_info: MagicMock
    ):
        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[],
            data=[{}],
            totalCount=2
        )

        report_request = deepcopy(self.__SIMPLE_REPORT_REQUEST)


        await submit_report_v2(report_request=report_request,
                               experience_name=CampaignType.PLA,
                               current_user=self.__current_user,
                               report_service=self.__mock_report_service,
                               advertiser_service=self.__mock_advertiser_service)

        mock_logger_critical.assert_called_once_with(
            'REPORT; User: %s, Koddi count: %d, Returned count: %d, Requested size: %d, Offset: %d, '
            'Advertisers: [%s]', 'user@example.com.invalid', 2, 1, 10, 0, '1')
        mock_logger_info.assert_called_with(
            'REPORT; User: %s, Koddi count: %d, Returned count: %d, Requested size: %d, Offset: %d, Advertisers: [%s]',
            'user@example.com.invalid', 2, 1, 10, 0, '1'
        )

    @pytest.mark.asyncio
    @patch("logging.Logger.warning")
    async def test_report__raises_error_if_user_does_not_have_access_to_advertisers(
            self,
            mock_logger_warning: MagicMock
    ):
        # Arrange
        advertiser_1 = CachedAdvertiser(
            brandId="1",
            name="Test Advertiser",
            accountId=1,
            description="Test Description",
            active=True
        )
        advertiser_3 = CachedAdvertiser(
            brandId="3",
            name="Test Advertiser",
            accountId=1,
            description="Test Description",
            active=True
        )
        advertisers_without_access = [advertiser_3]
        self.__mock_advertiser_service.get_advertisers_by_numeric_ids.return_value = [
            advertiser_1,
            advertiser_3
        ]
        report_request = deepcopy(self.__SIMPLE_REPORT_REQUEST)
        report_request.advertiserIds = [1, 3]

        # Act
        with self.assertRaises(HTTPException) as context:
            await submit_report_v2(report_request=report_request,
                                   experience_name=CampaignType.CAROUSEL,
                                   current_user=self.__current_user,
                                   report_service=self.__mock_report_service,
                                   advertiser_service=self.__mock_advertiser_service)

        # Assert
        mock_logger_warning.assert_has_calls([
            call("User Email: %s", self.__current_user['email']),
            call("User has access to brands: %s", self.__current_user['brands']),
            call("User requested access to brands: %s", advertisers_without_access)
        ])
        self.assertEqual(403, context.exception.status_code)
        self.assertEqual("User does not have access to advertisers", context.exception.detail["msg"])
        self.assertEqual([advertisers_without_access[0].id], context.exception.detail["advertisers"])

    @pytest.mark.asyncio
    async def test_report__report_service_called_with_koddi_map(self):
        # Arrange
        report_request = deepcopy(self.__SIMPLE_REPORT_REQUEST)
        expected_koddi_map = {}
        mock_response = ReportResultResponse(headers=[], data=[], totalCount=0)
        self.__mock_report_service.request_report.return_value = mock_response

        # Act
        await submit_report_v2(report_request=report_request,
                            current_user=self.__current_user,
                            experience_name=CampaignType.PLA,
                            report_service=self.__mock_report_service,
                            advertiser_service=self.__mock_advertiser_service)

        # Assert
        self.__mock_report_service.request_report.assert_called_with(
            report_request,
            expected_koddi_map,
            InternalCampaignType.PLA
        )

    async def test_submit_report_v2__gets_report_and_passes_experience_name(self):
        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[],
            data=[{}],
            totalCount=1
        )
        koddi_ids = {}
        report_request = self.__SIMPLE_REPORT_REQUEST

        await submit_report_v2(
            report_request=report_request,
            experience_name=CampaignType.CAROUSEL,
            current_user=self.__current_user,
            report_service=self.__mock_report_service,
            advertiser_service=self.__mock_advertiser_service
        )

        self.__mock_report_service.request_report.assert_called_with(
            report_request,
            koddi_ids,
            InternalCampaignType.CAROUSEL
        )

    async def test_submit_report_v2__gets_report_using_new_dimensions(self):
        expected_header_list = [
            ReportResultHeader(name="commodity", type="text", title="Commodity"),
            ReportResultHeader(name="brand_names", type="text", title="Brand Names"),
            ReportResultHeader(name="sub_commodity", type="text", title="Sub-Commodity"),
            ReportResultHeader(name="department", type="text", title="Department"),
        ]
        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=expected_header_list,
            data=[{}],
            totalCount=1
        )
        koddi_ids = {}
        report_request = self.__SIMPLE_REPORT_REQUEST
        report_request.dimensions = [DimensionsV2.COMMODITY.value,
                                     DimensionsV2.BRAND_NAMES.value,
                                     DimensionsV2.SUB_COMMODITY.value,
                                     DimensionsV2.DEPARTMENT.value]

        result = await submit_report_v2(
            report_request=report_request,
            experience_name=CampaignType.CAROUSEL,
            current_user=self.__current_user,
            report_service=self.__mock_report_service,
            advertiser_service=self.__mock_advertiser_service
        )

        self.__mock_report_service.request_report.assert_called_with(
            report_request,
            koddi_ids,
            InternalCampaignType.CAROUSEL
        )

        self.assertEqual(result.headers, expected_header_list)

    async def test_submit_report_v2__gets_report_using_video_carousel_metrics(self):
        koddi_ids = {}
        report_request = self.__SIMPLE_REPORT_REQUEST
        report_request.dimensions = [DimensionsV2.ADVERTISER_ID]
        report_request.metrics = [
            MetricsV2.VIDEO_COMPLETE_VIEW_RATE,
            MetricsV2.VIDEO_THIRD_QUARTILE_VIEWS
        ]

        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[
                ReportResultHeader(name="advertiser_id", type="number", title="Advertiser ID"),
                ReportResultHeader(name="video_complete_view_rate", type="percentage",
                                   title="Video Complete View Rate"),
                ReportResultHeader(name="video_third_quartile_views", type="number", title="Video Third Quartile Views"),

            ],
            data=[{
                "advertiser_id": 60,
                "video_complete_view_rate": 15,
                "video_third_quartile_views": 2
            }],
            totalCount=1
        )

        result = await submit_report_v2(
            report_request=report_request,
            experience_name=CampaignType.CAROUSEL,
            current_user=self.__current_user,
            report_service=self.__mock_report_service,
            advertiser_service=self.__mock_advertiser_service
        )

        self.__mock_report_service.request_report.assert_called_with(
            report_request,
            koddi_ids,
            InternalCampaignType.CAROUSEL
        )
        self.assertEqual(result.data[0]["video_complete_view_rate"], 15 )


    async def test_submit_report_v2__gets_report_using_video_carousel_metrics__click(self):
        koddi_ids = {}
        report_request = self.__SIMPLE_REPORT_REQUEST
        report_request.dimensions = [DimensionsV2.ADVERTISER_ID]
        report_request.metrics = [
            MetricsV2.VIDEO_STARTS,
            MetricsV2.VIDEO_PAUSES,
            MetricsV2.VIDEO_VIEW_THROUGH_RATE,
            MetricsV2.VIDEO_TOTAL_DURATION
        ]

        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[
                ReportResultHeader(name="advertiser_id", type="number", title="Advertiser ID"),
                ReportResultHeader(name="video_starts", type="number", title="Video Complete View Rate"),
                ReportResultHeader(name="video_view_through_rate", type="percentage",
                                   title="Video View Through Rate"),
                ReportResultHeader(name="video_pauses", type="number", title="Video Pauses"),
                ReportResultHeader(name="video_total_duration", type="percentage", title="Video Total Duration"),

            ],
            data=[{
                "advertiser_id": 60,
                "video_view_through_rate": 15,
                "video_pauses": 250,
                "video_starts": 213,
                "video_total_duration": 10
            }],
            totalCount=1
        )

        result = await submit_report_v2(
            report_request=report_request,
            experience_name=CampaignType.CAROUSEL,
            current_user=self.__current_user,
            report_service=self.__mock_report_service,
            advertiser_service=self.__mock_advertiser_service
        )
        self.assertEqual(result.totalCount, 1)
        self.assertEqual(len(result.headers), len(report_request.metrics)+ len(report_request.dimensions) )