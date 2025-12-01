from copy import deepcopy
from typing import List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, call, patch, AsyncMock

import pytest
from fastapi import HTTPException
from httpx import Response

from app.common.exceptions.campaign_exceptions import CampaignNotPublishedException
from app.common.gateways.campaign_service_gateway import CampaignServiceGateway, ValidationType
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.view_models import PatchOperation
from app.common.model.downstream.campaign_service import Validations, CampaignSearchRequest, CampaignResponse
from app.common.model.shared import InternalPublishStatus, PublishStatus
from tests.unit.services.constants import FETCHED_RAW_CAMPAIGNS_PAGINATED_RESPONSE


class TestCampaignServiceGateway(IsolatedAsyncioTestCase):
    TEST_CAMPAIGN_DATA_LIST = deepcopy(FETCHED_RAW_CAMPAIGNS_PAGINATED_RESPONSE['data'])

    def setUp(self):
        self.__mock_external_http_client_service = MagicMock()
        self.__mock_async_external_http_client_service = AsyncMock()
        self.__mock_harness_service = MagicMock()

        self.__mock_harness_service.is_harness_flag_on.return_value = True

        self.campaign_service_gateway = CampaignServiceGateway(self.__mock_async_external_http_client_service,
                                                               self.__mock_external_http_client_service,
                                                               self.__mock_harness_service)

    async def test_get_campaign__uses_async_client_when_toggled(self):
        self.__mock_async_external_http_client_service.get.side_effect = [HTTPException(status_code=500)]

        with self.assertRaises(HTTPException) as context:
            await self.campaign_service_gateway.get_campaign("test_campaign_id")

        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/test_campaign_id",
            response_body_type='json',
            json_has_data_field=True,
            forward_client_error_response_content=True,
        )

    def test_calculate_external_publication_status__correct_status_in_all_cases(self):
        for internal_status, expected_external_status in [
            (InternalPublishStatus.PENDING, PublishStatus.PENDING),
            (InternalPublishStatus.IN_PROGRESS, PublishStatus.PENDING),
            (InternalPublishStatus.DELIVERY_PENDING, PublishStatus.PENDING),
            (InternalPublishStatus.DELIVERY_SUCCESS, PublishStatus.PENDING),
            (InternalPublishStatus.PUBLISHED, PublishStatus.PUBLISHED),
            (InternalPublishStatus.SUCCESS, PublishStatus.PUBLISHED),
            (InternalPublishStatus.FAILED, PublishStatus.FAILED),
            (InternalPublishStatus.EMPTY, PublishStatus.EMPTY)
        ]:
            with self.subTest(internal_status=internal_status, expected_external_status=expected_external_status):
                self.__status_calculation_assertion(internal_status, expected_external_status)

    def __status_calculation_assertion(self, internal_status, expected_external_status):
        self.assertEqual(expected_external_status,
                         CampaignServiceGateway.calculate_external_publication_status(internal_status))

    async def test_get_campaign_success(self):
        mock_response = Response(
            status_code=200,
            json={"data": {
                "validations":
                    [ {"path": "string","detail": ["string"]}], "changes": [{"string": "string"}]}, "meta": {}}
        )

        self.__mock_async_external_http_client_service.get.return_value = mock_response
        response = await self.campaign_service_gateway.get_campaign("1635")

        expect_data = CampaignResponse(
            validations= [Validations(path="string", detail= ["string"])],
            changes=[{"string": "string"}]
        )

        #verifications
        self.__mock_async_external_http_client_service.get.assert_called_once_with(
                path="/map-campaign-service/v1/campaign/1635",
                response_body_type="json",
                json_has_data_field=True,
                forward_client_error_response_content=True
        )
        self.assertEqual(expect_data, response)

    async def test_get_campaign__filter_premium_placements__unpublished__should_throw(self):
        mock_response = Response(
            status_code=200,
            json={"data": {
                "unpublishedChanges": {"type": "PREMIUM_PLACEMENTS"}
            }}
        )
        self.__mock_async_external_http_client_service.get.return_value = mock_response

        with self.assertRaises(HTTPException) as context:
            await self.campaign_service_gateway.get_campaign("abc1234")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Unsupported campaign type")

    async def test_get_campaign__filter_premium_placements__published__should_throw(self):
        mock_response = Response(
            status_code=200,
            json={"data": {
                "publishedChanges": {"type": "PREMIUM_PLACEMENTS"}
            }}
        )
        self.__mock_async_external_http_client_service.get.return_value = mock_response

        with self.assertRaises(HTTPException) as context:
            await self.campaign_service_gateway.get_campaign("abc1234")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Unsupported campaign type")

    async def test_validate_campaign(self):
        mock_response = Response(
            status_code=200,
            json={"data": {"status": "VALID"}, "meta":{}}
        )
        self.__mock_async_external_http_client_service.get.return_value = mock_response
        response = await self.campaign_service_gateway.validate_campaign("1635", ValidationType.SUBMIT)

        expect_data = True

        # verifications
        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1635" \
               f"/validate?validationType=submit",
            response_body_type="json",
            forward_client_error_response_content=True
        )
        self.assertEqual(expect_data, response)

    async def test_validate_campaign_success_no_status(self):
        mock_response = Response(
            status_code=200,
            json={"data": {}, "meta": {}}
        )
        self.__mock_async_external_http_client_service.get.return_value = mock_response

        response = await self.campaign_service_gateway.validate_campaign("1459", ValidationType.SUBMIT)

        # verifications
        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1459" \
                 f"/validate?validationType=submit",
            response_body_type="json",
            forward_client_error_response_content=True
        )
        expected_data = False
        self.assertEqual(expected_data, response)

    async def test_validate_campaign_failure_Valid(self):
        mock_response = Response(
            status_code=200,
            json={"data": {"status": "NO_VALID"}, "meta": {}}
        )
        self.__mock_async_external_http_client_service.get.return_value = mock_response

        response = await self.campaign_service_gateway.validate_campaign("1888", ValidationType.SUBMIT)

        # verifications
        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1888" \
                 f"/validate?validationType=submit",
            response_body_type="json",
            forward_client_error_response_content=True
        )
        expected_data = False
        self.assertEqual(expected_data, response)

    async def test_patch_campaign(self):
        mock_response = Response(
            status_code=204,
            json={}
        )
        request: List[PatchOperation] = [ PatchOperation(op="replace", path="/primaryAccount/addresses", value=[]),
                                          PatchOperation(op="add", path="/primaryAccount/contacts", value=[]) ]

        payload =  [patch.dict() for patch in request]

        self.__mock_async_external_http_client_service.patch.return_value = mock_response
        response = await self.campaign_service_gateway.patch_campaign("1909", payload)

        expect_data = True

        # verifications
        self.__mock_async_external_http_client_service.patch.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1909",
            json=payload
        )
        self.assertEqual(expect_data, response)

    async def test_patch_campaign_failure_Bad_Request(self):
        mock_response = Response(
            status_code=400,
            json={"errors": [{
                "reason": "Bad request Message",
                "code": 0,
                "datetime": {"value": "string","timezone": "string"}}
            ]}
        )
        request: List[PatchOperation] = [PatchOperation(op="replace", path="/primaryAccount/addresses", value=[]),
                                         PatchOperation(op="add", path="/primaryAccount/contacts", value=[])]

        payload = [patch.dict() for patch in request]

        self.__mock_async_external_http_client_service.patch.return_value = mock_response
        with pytest.raises(HTTPException) as ex:
            await self.campaign_service_gateway.patch_campaign("1959", payload)

        # verifications
        expected_message = "bad request message"

        self.__mock_async_external_http_client_service.patch.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1959",
            json=payload
        )
        assert ex.value.status_code == 400
        assert ex.value.detail == expected_message

    async def test_patch_campaign_failure_Unprocessable(self):
        mock_response = Response(
            status_code=422,
            json={"errors": [{
                "reason": "custom budgets cannot be always on",
                "code": 0,
                "datetime": {"value": "string","timezone": "string"}}
            ]}
        )
        request: List[PatchOperation] = [PatchOperation(op="replace", path="/primaryAccount/addresses", value=[]),
                                         PatchOperation(op="add", path="/primaryAccount/contacts", value=[])]

        payload = [patch.dict() for patch in request]

        self.__mock_async_external_http_client_service.patch.return_value = mock_response
        with pytest.raises(HTTPException) as ex:
            await self.campaign_service_gateway.patch_campaign("1969", payload)

        # verifications
        expected_message = "Please select a daily, weekly or monthly budget for always on campaigns."
        self.__mock_async_external_http_client_service.patch.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1969",
            json=payload
        )

        assert ex.value.status_code == 422
        assert ex.value.detail == expected_message

    async def test_patch_campaign_failure_Internal_error(self):
        mock_response = Response(
            status_code=500,
            json={"errors": [{
                "reason": "string",
                "code": 0,
                "datetime": {"value": "string", "timezone": "string"}}
            ]}
        )
        request: List[PatchOperation] = [PatchOperation(op="replace", path="/primaryAccount/addresses", value=[]),
                                         PatchOperation(op="add", path="/primaryAccount/contacts", value=[])]

        payload = [patch.dict() for patch in request]

        self.__mock_async_external_http_client_service.patch.return_value = mock_response
        with pytest.raises(HTTPException) as ex:
            await self.campaign_service_gateway.patch_campaign("1976", payload)

        # verifications
        self.__mock_async_external_http_client_service.patch.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1976",
            json=payload
        )
        assert ex.value.status_code == 500
        assert ex.value.detail == 'Unable to complete request. Try again later.'

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    async def test_publish_campaign(self, mock_is_harness_flag_on: MagicMock):
        mock_response = Response(
            status_code=202,
            json={"data": { "status": "PUBLISHED",
                            "datetime": {
                                "value": "2025-02-28T19:14:50.735Z",
                                "timezone": "string"}
                            },
                  "meta": {}
                  }
        )

        self.__mock_async_external_http_client_service.post.return_value = mock_response
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json={"data": {"publishingStatus": "PUBLISHED"}}
        )
        response = await self.campaign_service_gateway.publish_campaign("1999")

        expect_data = PublishStatus.PUBLISHED

        self.__mock_async_external_http_client_service.post.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1999/publish",
            json={"fields": []},
            response_body_type='json',
            forward_client_error_response_content=True
        )

        self.assertEqual(expect_data, response)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    async def test_publish_campaign_timezone_value_absent(self, mock_is_harness_flag_on: MagicMock):
        mock_response = Response(
            status_code=202,
            json={"data": { "status": "PUBLISHED",
                            "datetime": {}
                          },
                  "meta": {}
                  }
        )

        self.__mock_async_external_http_client_service.post.return_value = mock_response
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json={"data": {"publishingStatus": "PUBLISHED"}}
        )
        response = await self.campaign_service_gateway.publish_campaign("1999")

        expect_data = PublishStatus.PUBLISHED

        self.__mock_async_external_http_client_service.post.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/1999/publish",
            json={"fields": []},
            response_body_type='json',
            forward_client_error_response_content=True
        )

        self.assertEqual(expect_data, response)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    async def test_publish_campaign_fail(self, mock_is_harness_flag_on: MagicMock):
        mock_response = Response(
            status_code=200,
            json={"data": { "status": "FAILED"},
                  "meta": {}}
        )

        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json={"data": {"publishingStatus": "FAILED"}}
        )
        self.__mock_async_external_http_client_service.post.return_value = mock_response
        response = await self.campaign_service_gateway.publish_campaign("2000")

        expect_data = PublishStatus.FAILED

        self.__mock_async_external_http_client_service.post.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/2000/publish",
            json={"fields": []},
            response_body_type='json',
            forward_client_error_response_content=True
        )

        self.assertEqual(expect_data, response)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    async def test_publish_campaign_response_none(self, mock_is_harness_flag_on: MagicMock):
        mock_response = Response(
            status_code=200,
            json={"data": None, "meta": {}}
        )
        self.__mock_async_external_http_client_service.post.return_value = mock_response
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json={"data": {"publishingStatus": "PUBLISHED"}}
        )

        campaign_id = "2000"

        with pytest.raises(CampaignNotPublishedException) as ex:
            await self.campaign_service_gateway.publish_campaign(campaign_id)

        self.assertEqual(ex.type, CampaignNotPublishedException)
        self.assertEqual(str(ex.value), str(CampaignNotPublishedException(campaign_id=campaign_id)))

        self.__mock_async_external_http_client_service.post.assert_called_once_with(
            path="/map-campaign-service/v1/campaign/2000/publish",
            json={"fields": []},
            response_body_type='json',
            forward_client_error_response_content=True
        )

    async def test_publish_campaign__campaign_has_validation_warnings__should_not_publish(self):
        self.__mock_async_external_http_client_service.post = AsyncMock()
        self.__mock_async_external_http_client_service.get.return_value = Response(
            status_code=200,
            json={"data": {
                    "validations": [{"path": "string", "detail": ["a detail"]}],
                    "publishingStatus": "PENDING"}})

        result: PublishStatus = await self.campaign_service_gateway.publish_campaign("abc123")

        self.assertEqual(PublishStatus.PENDING, result)

        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            forward_client_error_response_content=True,
            json_has_data_field=True,
            path='/map-campaign-service/v1/campaign/abc123',
            response_body_type='json')
        self.__mock_async_external_http_client_service.post.assert_not_called()


    async def test_get_campaigns(self):
        mock_response = Response(status_code=200, json={
            'data': deepcopy(self.TEST_CAMPAIGN_DATA_LIST),
            "meta":{
                "page": {
                    "hasMore": False,
                    "offset": 0,
                    "size": 3,
                    "totalCount": 3,
                    "totalPages": 1
                }
            }
        })

        requests = CampaignSearchRequest(externalPartner="KODDI_CAMPAIGN_ID",externalPartnerID=10)

        self.__mock_async_external_http_client_service.post.return_value = mock_response
        response = await self.campaign_service_gateway.get_campaigns(requests)

        expected_len = 3
        self.assertEqual(len(response), expected_len)

    async def test_get_campaigns__calls_campaign_post_and_returns_campaigns(self):
        # Arrange
        mock_response = Response(status_code=200, json={
            'data': deepcopy(self.TEST_CAMPAIGN_DATA_LIST),
            "meta": {
                "page": {
                    "hasMore": False,
                    "offset": 0,
                    "size": 3,
                    "totalCount": 3,
                    "totalPages": 1
                }
            }
        })
        campaigns_request = CampaignSearchRequest(id=["1234"])

        self.__mock_async_external_http_client_service.post.return_value = mock_response

        # Act
        results = await self.campaign_service_gateway.get_campaigns(campaigns_request)

        # Assert
        self.__mock_async_external_http_client_service.post.assert_called_once_with(
            path="/map-campaign-service/v1/campaigns",
            json=campaigns_request.model_dump(exclude_none=True, by_alias=True)
        )
        self.assertEqual(len(results), 3)

    async def test_get_campaigns__calls_campaign_post_multiple_times_and_aggregates_campaigns(self):
        # Arrange
        page_1_response = Response(status_code=200, json={
            'data': [{'id': '1234'}, {'id': '1235'}, {'id': '1236'}],
            'meta': {
                'page': {
                    "hasMore": True,
                    "offset": 0,
                    "size": 3,
                    "totalCount": 9,
                    "totalPages": 3
                }
            }
        })
        page_2_response = Response(status_code=200, json={
            'data': [{'id': '2234'}, {'id': '2235'}, {'id': '2236'}],
            'meta': {
                'page': {
                    "hasMore": True,
                    "offset": 0,
                    "size": 3,
                    "totalCount": 9,
                    "totalPages": 3
                }
            }
        })
        page_3_response = Response(status_code=200, json={
            'data': [{'id': '3234'}, {'id': '3235'}, {'id': '3236'}],
            'meta': {
                'page': {
                    "hasMore": False,
                    "offset": 0,
                    "size": 3,
                    "totalCount": 9,
                    "totalPages": 3
                }
            }
        })
        campaigns_request = CampaignSearchRequest(brandIDs=["1234"])
        campaigns_request.page_size = 3
        self.__mock_async_external_http_client_service.post.side_effect = [page_1_response, page_2_response, page_3_response]
        request_2 = deepcopy(campaigns_request)
        request_2.page_offset = 3
        request_3 = deepcopy(campaigns_request)
        request_3.page_offset = 6


        # Act
        results = await self.campaign_service_gateway.get_campaigns(campaigns_request)

        # Assert
        self.__mock_async_external_http_client_service.post.assert_has_calls([
            call(
                path="/map-campaign-service/v1/campaigns",
                json=campaigns_request.model_dump(exclude_none=True, by_alias=True)
            ),
            call(
                path="/map-campaign-service/v1/campaigns",
                json=request_2.model_dump(exclude_none=True, by_alias=True)
            ),
            call(
                path="/map-campaign-service/v1/campaigns",
                json=request_3.model_dump(exclude_none=True, by_alias=True)
            )
        ])
        self.assertEqual(len(results), 9)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag',
           return_value={"enabled": True, "max_retries": 3, "pause_seconds": 3, "expire": 60})
    async def test_get_updated_campaign_until_published__published__should_succeed(
            self,
            mock_fetch_multivariate_flag: MagicMock,
            mock_is_harness_flag_on: MagicMock):
        campaign_id = "1234abcd"

        self.__mock_async_external_http_client_service.get = AsyncMock(
            return_value=Response(status_code=200, json={'data': {'publishingStatus': 'PUBLISHED'}}))

        results = await self.campaign_service_gateway.wait_for_campaign_publication_status_to_settle(campaign_id)

        self.assertEqual(results.publishingStatus, InternalPublishStatus.PUBLISHED)

        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path=f"/map-campaign-service/v1/campaign/{campaign_id}",
            response_body_type='json',
            json_has_data_field=True,
            forward_client_error_response_content=True)

        self.__harness_retry_enabled_call_checks(flag=mock_is_harness_flag_on, multi_flag=mock_fetch_multivariate_flag)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
    @patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag',
           return_value={"enabled": True, "max_retries": 0, "pause_seconds": 3, "expire": 60})
    async def test_get_updated_campaign_until_published__not_published__should_throw(
            self,
            mock_fetch_multivariate_flag: MagicMock,
            mock_is_harness_flag_on: MagicMock):
        mock_response = Response(status_code=200, json={
            'data': {'publishingStatus': 'PENDING'},
            'meta': {
                'page': {
                    "hasMore": False,
                    "offset": 0,
                    "size": 3,
                    "totalCount": 1,
                    "totalPages": 1
                }
            }
        })
        campaign_id = "1234abcd"
        self.__mock_async_external_http_client_service.get.return_value = mock_response

        with pytest.raises(CampaignNotPublishedException) as ex:
            await self.campaign_service_gateway.wait_for_campaign_publication_status_to_settle(campaign_id)

        self.assertEqual(ex.type, CampaignNotPublishedException)
        self.assertEqual(str(ex.value), str(CampaignNotPublishedException(campaign_id=campaign_id)))
        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path=f"/map-campaign-service/v1/campaign/{campaign_id}",
            response_body_type='json',
            json_has_data_field=True,
            forward_client_error_response_content=True)

        self.__harness_retry_enabled_call_checks(flag=mock_is_harness_flag_on, multi_flag=mock_fetch_multivariate_flag)

    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=False)
    @patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag')
    async def test_get_updated_campaign_until_published__flag_off__should_not_call(
            self,
            mock_fetch_multivariate_flag: MagicMock,
            mock_is_harness_flag_on: MagicMock):
        campaign_id = "1234abcd"
        self.__mock_async_external_http_client_service.get = AsyncMock(
            return_value=Response(status_code=200, json={'data': {'publishingStatus': 'PUBLISHED'}}))

        await self.campaign_service_gateway.wait_for_campaign_publication_status_to_settle(campaign_id)

        self.__mock_async_external_http_client_service.get.assert_not_called()
        mock_fetch_multivariate_flag.assert_not_called()
        mock_is_harness_flag_on.assert_called_once_with(
            HarnessFeatureFlags.CHECK_CAMPAIGN_PUBLICATION_STATUS, 'default')

    @staticmethod
    def __harness_retry_enabled_call_checks(flag: MagicMock, multi_flag: MagicMock):
        multi_flag.assert_called_once_with(
            flag_name=HarnessFeatureFlags.UNPUBLISHED_CAMPAIGN_FETCH_RETRY,
            target_id='default')
        flag.assert_called_once_with(
            HarnessFeatureFlags.CHECK_CAMPAIGN_PUBLICATION_STATUS,'default')

    async def test_search_campaigns__returns_empty_response_on_upstream_404(self):
        mock_payload = CampaignSearchRequest()
        self.__mock_async_external_http_client_service.post.return_value = Response(
            status_code=404,
            json={"errors":[{"reason":"campaign not found","code":1,"datetime":{"value":"2025-07-10T19:30:13.182159287Z","timezone":"UTC"}}]}
        )

        response = await self.campaign_service_gateway.search_campaigns(mock_payload)

        self.assertEqual([], response.data)
        self.assertEqual(mock_payload.page_offset, response.meta.page.offset)
        self.assertEqual(mock_payload.page_size, response.meta.page.size)
        self.assertEqual(False, response.meta.page.hasMore)
        self.assertEqual(0, response.meta.page.totalPages)
        self.assertEqual(0, response.meta.page.totalCount)

    async def test_search_campaigns__logs_and_raises_client_error_on_other_4xx_response(self):
        mock_payload = CampaignSearchRequest()
        mock_request=MagicMock()
        upstream_error={"errors": [{"reason": "invalid request"}]}
        self.__mock_async_external_http_client_service.post.return_value = Response(
            status_code=400,
            json=upstream_error,
            request=mock_request
        )

        with self.assertRaises(HTTPException) as context:
            await self.campaign_service_gateway.search_campaigns(mock_payload)

        self.assertIsNotNone(context)
        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(upstream_error, context.exception.detail)

    async def test_search_campaigns__logs_and_raises_server_error_on_5xx_response(self):
        mock_payload = CampaignSearchRequest()
        mock_request = MagicMock()
        upstream_error = {"errors": [{"reason": "server error"}]}
        self.__mock_async_external_http_client_service.post.return_value = Response(
            status_code=500,
            json=upstream_error,
            request=mock_request
        )

        with self.assertRaises(HTTPException) as context:
            await self.campaign_service_gateway.search_campaigns(mock_payload)

        self.assertIsNotNone(context)
        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("Temporary service error.  Please try again.", context.exception.detail)