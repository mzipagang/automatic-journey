import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, call, patch, ANY, AsyncMock

import httpx
from httpx import Response

from app.common.gateways.division_gateway import DivisionGateway
from app.common.model.downstream.location_groups import LocationGroupResponseData, LocationGroupResponse, LocationGroup, \
    LocationGroupCategory
from app.common.model.division import DivisionServiceResponse


class TestDivisionGateway(IsolatedAsyncioTestCase):
    def setUp(self):
        self.__mock_async_external_http_client_service = AsyncMock()
        self.__mock_external_http_client_service = MagicMock()
        self.__mock_harness_service = MagicMock()

        self.__mock_harness_service.is_harness_flag_on.return_value = True

        self.division_gateway = DivisionGateway(self.__mock_async_external_http_client_service,
                                                self.__mock_external_http_client_service,
                                                self.__mock_harness_service)

    async def test_get_location_groups__returns_empty_response_if_ids_is_empty(self):
        expected_response = LocationGroupResponseData()
        ids = []

        result = await self.division_gateway.get_location_groups(ids)

        self.assertEqual(result, expected_response)

    async def test_get_location_groups__returns_empty_response_if_filtered_ids_is_empty(self):
        expected_response = LocationGroupResponseData()
        ids = ["", None]

        result = await self.division_gateway.get_location_groups(ids)

        self.assertEqual(result, expected_response)

    async def test_get_location_groups__batches_requests_if_there_are_more_than_50_ids(self):
        ids = [f"{location_group}" for location_group in range(1, 52)]
        batch1 = {"ids": ",".join(ids[:50])}
        batch2 = {"ids": ",".join(ids[50:])}
        self.__mock_async_external_http_client_service.get.return_value = Response(200, json={})

        await self.division_gateway.get_location_groups(ids)

        self.__mock_async_external_http_client_service.get.assert_has_calls([
            call(
                path="/location-groups/v1/",
                params=batch1,
                response_body_type="json",
                json_has_data_field=True,
                forward_client_error_response_content=True
            ),
            call(
                path="/location-groups/v1/",
                params=batch2,
                response_body_type="json",
                json_has_data_field=True,
                forward_client_error_response_content=True
            )
        ])

    async def test_get_location_groups__makes_single_request_if_there_are_less_than_50_ids(self):
        ids = [f"{location_group}" for location_group in range(1, 10)]
        batch1 = {"ids": ",".join(ids)}
        self.__mock_async_external_http_client_service.get.return_value = Response(200, json={})

        await self.division_gateway.get_location_groups(ids)

        self.__mock_async_external_http_client_service.get.assert_has_calls([
            call(
                path="/location-groups/v1/",
                params=batch1,
                response_body_type="json",
                json_has_data_field=True,
                forward_client_error_response_content=True
            )
        ])

    @patch('logging.Logger.error')
    async def test_get_location_groups__logs_error_if_there_is_a_json_decode_error(self, mock_logger_error):
        ids = [f"{location_group}" for location_group in range(1, 10)]
        expected_batch = ids
        expected_doc = ""
        self.__mock_async_external_http_client_service.get.return_value = Response(200)

        await self.division_gateway.get_location_groups(ids)

        mock_logger_error.assert_called_with(
            "JSONDecodeError - Unable to decode JSON for batch %s: %s",
            expected_batch,
            expected_doc)

    @patch('logging.Logger.error')
    async def test_get_location_groups__logs_error_if_there_is_a_validation_error(self, mock_logger_error):
        ids = [f"{location_group}" for location_group in range(1, 10)]
        expected_batch = ids
        invalid_response_data = {"found": ""}
        self.__mock_async_external_http_client_service.get.return_value = Response(
            200,
            json=invalid_response_data
        )

        await self.division_gateway.get_location_groups(ids)

        mock_logger_error.assert_called_with(
            "Response Validation Error for batch %s: %s",
            expected_batch,
            ANY)

    async def test_get_location_groups__aggregates_batch_response(self):
        ids = [f"{location_group}" for location_group in range(1, 91)]
        found_location_groups = [
            LocationGroup(id=i, categories=[
                LocationGroupCategory(type="division-banner", items=[])
            ])
            for i in ids
            if int(i) % 2 == 0
        ]
        not_found_location_groups = [
            i
            for i in ids
            if int(i) % 2 is not 0
        ]
        batch1_response = LocationGroupResponse(data=LocationGroupResponseData(
            found=found_location_groups[:25],
            notFound=not_found_location_groups[:25]
        )).model_dump_json()
        batch2_response = LocationGroupResponse(data=LocationGroupResponseData(
            found=found_location_groups[25:],
            notFound=not_found_location_groups[25:]
        )).model_dump_json()
        expected_result = LocationGroupResponseData(
            found=found_location_groups,
            notFound=not_found_location_groups
        )
        self.__mock_async_external_http_client_service.get.side_effect = [
            Response(200, content=batch1_response),
            Response(200, content=batch2_response)
        ]

        result = await self.division_gateway.get_location_groups(ids)

        self.assertEqual(result, expected_result)

    @patch('logging.Logger.info')
    async def test_get_divisions_success(self, mock_logger):
        valid_response = [
            {
                "id": "division1",
                "label": "Division 1",
                "preselected": False,
                "disabled": False,
                "flagged": False,
                "type": "division",
                "divisionNumber": "",
                "bannerCode": ""
            }
        ]
        self.__mock_async_external_http_client_service.post.return_value = Response(
            200,
            json=valid_response
        )
        expected_result = [
            DivisionServiceResponse(
                id="division1",
                label="Division 1",
                preselected=False,
                disabled=False,
                flagged=False,
                type="division",
                divisionNumber="",
                bannerCode=""
            )
        ]

        result = await self.division_gateway.get_divisions()

        self.assertEqual(result, expected_result)
        self.__mock_async_external_http_client_service.post.assert_called_once()
        mock_logger.asser_called_once()

    async def test_create_location_group_success(self):
        valid_response = {
            "id": "test_id",
            "name": "test_group",
            "categories": []
        }
        self.__mock_async_external_http_client_service.post.return_value = Response(
            200,
            json=valid_response
        )

        result = await self.division_gateway.create_location_group({"name": "test_group"})
        self.assertEqual(result, LocationGroup(**valid_response))
        self.assertIsInstance(result, LocationGroup)
        self.__mock_async_external_http_client_service.post.assert_called_once()

    async def test_create_location_group_http_400_error(self):
        self.__mock_async_external_http_client_service.post.return_value = MagicMock(
            status_code=httpx.codes.BAD_REQUEST
        )

        try:
            await self.division_gateway.create_location_group({})
        except ValueError: # Expects a json to parse into a model
            pass

        self.__mock_async_external_http_client_service.post.assert_called_once()
