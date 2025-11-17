import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.controllers.report import (
    build_koddi_id_dict,
    build_user_koddi_id_dict,
    get_advertisers_and_id_map,
    get_report,
)
from app.common.model.advertiser import CachedAdvertiser, KoddiAdvertiser
from app.common.model.campaign_types import InternalCampaignType
from app.common.model.report import IdGroup
from app.common.view_models.report import ReportResultResponse
from app.v2.view_models.report import ReportRequestV1


class TestReport(unittest.IsolatedAsyncioTestCase):
    __mock_report_service: AsyncMock
    __mock_advertiser_service: MagicMock

    __SIMPLE_REPORT_REQUEST = ReportRequestV1(
            advertiserIds=[1],
            startDate="2025-01-01",
            metrics=["cost"],
            endDate="2021-01-31",
            dimensions=["keyword"],
            filters=[],
            sort=[],
            pagination={"offset": 0, "size": 10}
        )

    def setUp(self):
        self.__mock_report_service = AsyncMock()
        self.__mock_report_service.validate_request_report_dates = MagicMock()
        self.__mock_report_service.validate_request_filter_and_sort = MagicMock()
        self.__mock_advertiser_service = AsyncMock()
        self.__current_user = {
            'internal': False,
            'brands': ['1', '2'],
            'email': 'user@example.com.invalid',
            'is_agency': False
        }
        self.__mock_advertiser_service.get_advertiser_by_numeric_id.return_value = CachedAdvertiser(
            brandId="1",
            name="Test Advertiser",
            accountId=1,
            description="Test Description",
            active=True
        )
        self.__mock_advertiser_service.get_koddi_advertisers_for_reporting.return_value = [1]
        self.__mock_advertiser_service.get_advertisers_for_user.return_value = []

    @pytest.mark.asyncio
    async def test_gets_report_and_passes_experience_name(self):
        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[],
            data=[{}],
            totalCount=1
        )
        koddi_ids = {}
        report_request = self.__SIMPLE_REPORT_REQUEST

        await get_report(
            report_request=report_request,
            experience_name=InternalCampaignType.PLA,
            current_user=self.__current_user,
            report_service=self.__mock_report_service,
            advertiser_service=self.__mock_advertiser_service
        )

        self.__mock_report_service.request_report.assert_called_with(
            report_request,
            koddi_ids,
            InternalCampaignType.PLA
        )
    
    @pytest.mark.asyncio
    async def test_gets_report_and_passes_experience_name_toa(self):
        self.__mock_report_service.request_report.return_value = ReportResultResponse(
            headers=[],
            data=[{}],
            totalCount=1
        )
        koddi_ids = {}
        report_request = self.__SIMPLE_REPORT_REQUEST

        await get_report(
            report_request=report_request,
            experience_name=InternalCampaignType.TOA,
            current_user=self.__current_user,
            report_service=self.__mock_report_service,
            advertiser_service=self.__mock_advertiser_service
        )

        self.__mock_report_service.request_report.assert_called_with(
            report_request,
            koddi_ids,
            InternalCampaignType.TOA
        )

    @pytest.mark.asyncio
    async def test_get_advertisers_and_id_map__returns_advertisers_and_id_map(self):
        # Arrange
        advertiser_ids = [1, 2, 3]
        mock_advertisers = [
            CachedAdvertiser(
                brandId=str(id * 10),
                name="Test Advertiser",
                accountId=1,
                description="Test Description",
                active=True
            ) for id in advertiser_ids
        ]
        self.__mock_advertiser_service.get_advertisers_by_numeric_ids.return_value = mock_advertisers

        # Act
        advertisers, id_map = await get_advertisers_and_id_map(advertiser_ids, self.__mock_advertiser_service)

        # Assert
        self.assertEqual(mock_advertisers, advertisers)
        self.assertEqual({'10': 1, '20': 2, '30': 3}, id_map)

    @pytest.mark.asyncio
    def test_build_user_koddi_id_dict__non_agency_user__should_includ_agency_involved_koddi_brands(self):
        # Arrange
        koddi_advertisers = [
            KoddiAdvertiser(
                brandIds=['brand 1', 'brand 2'],
                koddiId=1,
                agencyId='1234',
                primaryBrandId='1234'
            ),
            KoddiAdvertiser(
                brandIds=['brand 2', 'brand 3'],
                koddiId=2,
                agencyId='1234',
                primaryBrandId='1234'
            ),
            KoddiAdvertiser(
                brandIds=['brand 2', 'brand 4'],
                koddiId=3,
                primaryBrandId='1234'
            )
        ]
        agency_id = None

        # Act
        user_koddi_id_map = build_user_koddi_id_dict(koddi_advertisers, agency_id)

        # Assert
        self.assertEqual({
            'brand 1': [1],
            'brand 2': [1, 2, 3],
            'brand 3': [2],
            'brand 4': [3]
        }, user_koddi_id_map)

    def test_build_user_koddi_id_dict__returns_koddi_ids_for_every_brand_with_matching_agency(self):
        # Arrange
        koddi_advertisers = [
            KoddiAdvertiser(
                brandIds=['brand 1', 'brand 2'],
                koddiId=1,
                agencyId='1234',
                primaryBrandId='1234'
            ),
            KoddiAdvertiser(
                brandIds=['brand 2', 'brand 3'],
                koddiId=2,
                agencyId='1234',
                primaryBrandId='1234'
            ),
            KoddiAdvertiser(
                brandIds=['brand 2', 'brand 4'],
                koddiId=3,
                primaryBrandId='1234'
            )
        ]
        agency_id = '1234'

        # Act
        user_koddi_id_map = build_user_koddi_id_dict(koddi_advertisers, agency_id)

        # Assert
        self.assertEqual({
            'brand 1': [1],
            'brand 2': [1, 2],
            'brand 3': [2]
        }, user_koddi_id_map)

    @pytest.mark.asyncio
    async def test_build_koddi_id_dict__returns_advertisers_by_koddi_id_map(self):
        # Arrange
        short_ids = [1, 2]
        current_user = {
            'internal': False,
            'brands': ['brand 1', 'brand 2'],
            'is_agency': True,
            'works_for': {
                'clientId': 'agency id'
            }
        }
        cached_advertisers = [
            CachedAdvertiser(
                brandId=f"brand {id}",
                name="Test Advertiser",
                accountId=1,
                description="Test Description",
                active=True
            ) for id in short_ids
        ]
        koddi_advertisers = [
            KoddiAdvertiser(
                brandIds=[f"brand {id}"],
                koddiId=id * 10,
                agencyId='agency id',
                primaryBrandId=f"brand {id}"
            ) for id in short_ids
        ]
        self.__mock_advertiser_service.get_advertisers_by_numeric_ids.return_value = cached_advertisers
        self.__mock_advertiser_service.get_advertisers_for_user.return_value = koddi_advertisers

        # Act
        advertisers_by_koddi_ids = await build_koddi_id_dict(short_ids, current_user, self.__mock_advertiser_service)

        # Assert
        self.assertEqual({
            10: [IdGroup(koddi_id=10, long_id="brand 1", short_id=1)],
            20: [IdGroup(koddi_id=20, long_id="brand 2", short_id=2)]
        }, advertisers_by_koddi_ids)