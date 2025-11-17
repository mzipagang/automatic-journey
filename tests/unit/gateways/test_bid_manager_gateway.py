from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, call, patch, ANY, AsyncMock

from fastapi import HTTPException
from httpx import Response
from pydantic import ValidationError

from app.common.gateways.bid_manager_gateway import BidManagerGateway
from app.common.model.campaign_types import InternalCampaignType, BidManagerCampaignType
from app.common.model.downstream.bid_manager import MultipleBidsResponseData, BidsResponseData, Bid, ValidateBidRequest, \
    CreateBidsRequest, MultipleBidsResponse, SuggestionsResponse, Suggestion, SuggestedBid, BidValidationResponse


class TestBidManagerGateway(IsolatedAsyncioTestCase):
    def setUp(self):
        self.__mock_external_http_client_service = MagicMock()
        self.__mock_async_external_http_client_service = AsyncMock()
        self.__mock_harness_service = MagicMock()
        self.bid_manager_gateway = BidManagerGateway(self.__mock_async_external_http_client_service,
                                                     self.__mock_external_http_client_service,
                                                     self.__mock_harness_service)

    async def test_get_bids__uses_async_client_toggle(self):
        self.__mock_harness_service.is_harness_flag_on.return_value = True
        ids = ["1","2","3","4","5"]
        batch1 = {"ids": ",".join(ids)}

        self.__mock_async_external_http_client_service.get.return_value = Response(200, json={})

        await self.bid_manager_gateway.get_bids(ids)

        self.__mock_async_external_http_client_service.get.assert_called_once_with(
            path="/bid-manager/v1/bids",
            params=batch1,
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )

    async def test_get_bids__returns_empty_response_if_ids_is_empty(self):
        expected_response = MultipleBidsResponseData()
        ids = []

        result = await self.bid_manager_gateway.get_bids(ids)

        self.assertEqual(result, expected_response)

    async def test_get_bids__returns_empty_response_if_filtered_ids_is_empty(self):
        expected_response = MultipleBidsResponseData()
        ids = ["", None]

        result = await self.bid_manager_gateway.get_bids(ids)

        self.assertEqual(result, expected_response)

    async def test_get_bids__batches_requests_if_there_are_more_than_50_ids(self):
        ids = [f"{bid_id}" for bid_id in range(1, 52)]
        batch1 = {"ids": ",".join(ids[:50])}
        batch2 = {"ids": ",".join(ids[50:])}
        self.__mock_async_external_http_client_service.get.return_value = Response(200, json={})

        await self.bid_manager_gateway.get_bids(ids)

        self.__mock_async_external_http_client_service.get.assert_has_calls([
            call(
                path="/bid-manager/v1/bids",
                params=batch1,
                response_body_type="json",
                json_has_data_field=True,
                forward_client_error_response_content=True
            ),
            call(
                path="/bid-manager/v1/bids",
                params=batch2,
                response_body_type="json",
                json_has_data_field=True,
                forward_client_error_response_content=True
            )
        ])

    async def test_get_bids__makes_single_request_if_there_are_less_than_50_ids(self):
        ids = [f"{bid_id}" for bid_id in range(1, 10)]
        batch1 = {"ids": ",".join(ids)}
        self.__mock_async_external_http_client_service.get.return_value = Response(200, json={})

        await self.bid_manager_gateway.get_bids(ids)

        self.__mock_async_external_http_client_service.get.assert_has_calls([
            call(
                path="/bid-manager/v1/bids",
                params=batch1,
                response_body_type="json",
                json_has_data_field=True,
                forward_client_error_response_content=True
            )
        ])

    @patch('logging.Logger.error')
    async def test_get_bids__logs_error_if_there_is_a_json_decode_error(self, mock_logger_error):
        ids = [f"{bid_id}" for bid_id in range(1, 10)]
        expected_batch = ids
        expected_doc = ""
        self.__mock_async_external_http_client_service.get.return_value = Response(200)

        await self.bid_manager_gateway.get_bids(ids)

        mock_logger_error.assert_called_with(
            "JSONDecodeError - Unable to decode JSON for batch %s: %s",
            expected_batch,
            expected_doc)

    @patch('logging.Logger.error')
    async def test_get_bids__logs_error_if_there_is_a_validation_error(self, mock_logger_error):
        ids = [f"{bid_id}" for bid_id in range(1, 10)]
        expected_batch = ids
        invalid_response_data = {"found": ""}
        self.__mock_async_external_http_client_service.get.return_value = Response(
            200,
            json=invalid_response_data
        )

        await self.bid_manager_gateway.get_bids(ids)

        mock_logger_error.assert_called_with(
            "Response Validation Error for batch %s: %s",
            expected_batch,
            ANY)

    async def test_get_bids__aggregates_batch_response(self):
        ids = [f"{bid_id}" for bid_id in range(1, 91)]
        found_bids = [
            BidsResponseData(id=i, type="PLA", bids=[Bid(id="4011")])
            for i in ids
            if int(i) % 2 == 0
        ]
        not_found_bids = [
            i
            for i in ids
            if int(i) % 2 is not 0
        ]
        batch1_response = MultipleBidsResponse(data=MultipleBidsResponseData(
            found=found_bids[:25],
            notFound=not_found_bids[:25]
        )).model_dump_json()
        batch2_response = MultipleBidsResponse(data=MultipleBidsResponseData(
            found=found_bids[25:],
            notFound=not_found_bids[25:]
        )).model_dump_json()
        expected_result = MultipleBidsResponseData(
            found=found_bids,
            notFound=not_found_bids
        )
        self.__mock_async_external_http_client_service.get.side_effect = [
            Response(200, content=batch1_response),
            Response(200, content=batch2_response)
        ]

        result = await self.bid_manager_gateway.get_bids(ids)

        self.assertEqual(result, expected_result)


    async def test_validate_bid__returns_result_for_success(self):
        biddable_entity_id = "1234"
        bid_request = ValidateBidRequest(
            minimumBidAmount=0,
            maximumBidAmount=1,
            minimumBidCount=1,
            maximumBidCount=10,
            bidIdsMustHaveValidEntities=True
        )
        self.__mock_async_external_http_client_service.post.return_value = Response(200, json={})

        result = await self.bid_manager_gateway.validate_bid(biddable_entity_id, bid_request)

        self.assertTrue(result.valid)
        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/bid-manager/v1/bids/1234/validate",
            response_body_type="json",
            forward_client_error_response_content=True,
            json={
                "bidIdsMustHaveValidEntities": True,
                "maximumBidAmount": 1.0,
                "maximumBidCount": 10,
                "minimumBidAmount": 0.0,
                "minimumBidCount": 1
            }
        )

    async def test_validate_bid__bad_bid_id__returns_no_invalid_upcs_and_invalid(self):
        result = await self.bid_manager_gateway.validate_bid('', ValidateBidRequest())

        self.assertEqual(result, BidValidationResponse(valid=False, invalid_upcs=None))

    async def test_validate_bid__returns_result_for_validation_failure(self):
        biddable_entity_id = "1234"
        bid_request = ValidateBidRequest(
            minimumBidAmount=0.1,
            maximumBidAmount=1,
            bidIdsMustHaveValidEntities=True
        )
        invalid_response_json = {
            "status": "error",
            "code": "422",
            "message": "Invalid Bids",
            "errors": [
                {
                    "type": "incorrect-bid-failure",
                    "bidFailureList": [
                        {"field": "UPC", "message": "4011 - Invalid UPC"},
                        {"field": "UPC", "message": "9876 - Invalid UPC"},
                    ]
                },
                {
                    "type": "incorrect-min-bid-failure",
                    "bidFailureList": [
                        {"field": "Bid Amount", "message": "2345 - 0.1 - Bid amount is less than min bid amount."}
                    ]
                }
            ]
        }
        self.__mock_async_external_http_client_service.post.side_effect = [
            HTTPException(
                status_code=422,
                detail=invalid_response_json
            )
        ]

        result = await self.bid_manager_gateway.validate_bid(biddable_entity_id, bid_request)

        self.assertFalse(result.valid)
        self.assertEqual(result.invalid_upcs, [])
        self.assertEqual(len(result.errors), 2)
        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/bid-manager/v1/bids/1234/validate",
            response_body_type="json",
            forward_client_error_response_content=True,
            json={
                "bidIdsMustHaveValidEntities": True,
                "maximumBidAmount": 1.0,
                "minimumBidAmount": 0.1,
            }
        )

    @patch('logging.Logger.error')
    async def test_validate_bid__raises_error_if_the_request_fails(self, mock_logger_error):
        biddable_entity_id = "1234"
        bid_request = ValidateBidRequest(
            minimumBidAmount=0.1,
            maximumBidAmount=1,
            bidIdsMustHaveValidEntities=True
        )
        self.__mock_async_external_http_client_service.post.side_effect = [
            HTTPException(
                status_code=500,
                detail="Backend service unavailable"
            )
        ]

        with self.assertRaises(HTTPException) as context:
            await self.bid_manager_gateway.validate_bid(biddable_entity_id, bid_request)

        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Backend service unavailable", context.exception.detail)
        mock_logger_error.assert_called_with(
            "Unable to process %s response from Bid Manager Validate API: %s",
            500,
            "Backend service unavailable")

    async def test_create_bids__raises_error_if_the_request_fails(self):
        create_bids_request = CreateBidsRequest(
            type="PLA",
            bids=[
                Bid(id="4011", bid_amount=0.1),
            ],
            default_bid=0)
        self.__mock_async_external_http_client_service.post.side_effect = [
            HTTPException(500, "Backend service unavailable")
        ]

        with self.assertRaises(HTTPException) as context:
            await self.bid_manager_gateway.create_bids(create_bids_request, False)

        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Backend service unavailable", context.exception.detail)
        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/bid-manager/v1/bids",
            params={"enforceBidCreationValidation": False},
            json=create_bids_request.model_dump(),
            response_body_type="json",
            forward_client_error_response_content=True
        )

    async def test_create_bids__returns_id_on_success(self):
        expected_id = "1234"
        create_bids_request = CreateBidsRequest(
            type="PLA",
            bids=[
                Bid(id="4011", bid_amount=0.1),
            ],
            default_bid=0)
        self.__mock_async_external_http_client_service.post.return_value = Response(200, json={"id": expected_id})

        result = await self.bid_manager_gateway.create_bids(create_bids_request, True)

        self.assertEqual(result, expected_id)
        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/bid-manager/v1/bids",
            params={"enforceBidCreationValidation": True},
            json=create_bids_request.model_dump(),
            response_body_type="json",
            forward_client_error_response_content=True
        )

    async def test_create_bids__serializes_type_to_bid_manager_type(self):
        expected_id = "1234"
        create_bids_request = CreateBidsRequest(
            type=InternalCampaignType.CAROUSEL,
            bids=[
                Bid(id="4011", bid_amount=0.1),
            ],
            default_bid=0)
        serialized_request = {
            "type": BidManagerCampaignType.CAROUSEL,
            "default_bid": 0.0,
            "bids": [
                { "id": "4011", "bid_amount": 0.1, "additionalProperties": None },
            ]
        }
        self.__mock_async_external_http_client_service.post.return_value = Response(
            200,
            json={"id": expected_id}
        )

        result = await self.bid_manager_gateway.create_bids(create_bids_request, True)

        self.assertEqual(result, expected_id)
        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/bid-manager/v1/bids",
            params={"enforceBidCreationValidation": True},
            json=serialized_request,
            response_body_type="json",
            forward_client_error_response_content=True
        )

    async def test_create_bids__raises_error_for_unsupported_bid_type(self):
        create_bids_request = CreateBidsRequest(
            type=InternalCampaignType.UNSUPPORTED,
            bids=[],
            default_bid=0
        )

        with self.assertRaises(HTTPException) as context:
            await self.bid_manager_gateway.create_bids(create_bids_request, True)

        self.assertIsNotNone(context)
        self.assertEqual(400, context.exception.status_code)
        self.assertEqual(
            "Cannot create bids for unsupported campaign type.",
            context.exception.detail
        )

    async def test_get_suggestions_response__calls_bid_manager_suggestions_endpoint(self):
        koddi_advertiser_id = 1234
        upcs = ["UPC1", "UPC2"]
        campaign_type = InternalCampaignType.PLA
        expected_response = SuggestionsResponse(
            suggestions=[
                Suggestion(id="UPC1", bid_information=SuggestedBid(lowest_bid=0.1, highest_bid=1.0)),
                Suggestion(id="UPC2", bid_information=SuggestedBid(lowest_bid=0.1, highest_bid=1.0)),
            ]
        )
        self.__mock_async_external_http_client_service.post.return_value = Response(
            200,
            json={"data": expected_response.model_dump() })

        response = await self.bid_manager_gateway.get_suggestions_response(koddi_advertiser_id, upcs, campaign_type)

        self.__mock_async_external_http_client_service.post.assert_called_with(
            path="/bid-manager/v2/suggestions",
            json={
                "advertiser_id": koddi_advertiser_id,
                "entities": upcs,
                "type": BidManagerCampaignType.PLA
            },
            response_body_type="json",
            forward_client_error_response_content=True
        )
        self.assertEqual(expected_response, response)

    async def test_get_suggestions_response__forwards_http_client_error(self):
        koddi_advertiser_id = 1234
        upcs = ["UPC1", "UPC2"]
        campaign_type = InternalCampaignType.PLA
        self.__mock_async_external_http_client_service.post.side_effect = HTTPException(
            status_code=400,
            detail="client error"
        )

        with self.assertRaises(HTTPException) as context:
            await self.bid_manager_gateway.get_suggestions_response(koddi_advertiser_id, upcs, campaign_type)

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual("client error", context.exception.detail)

    async def test_get_suggestions_response__raises_exception_on_malformed_response(self):
        koddi_advertiser_id = 1234
        upcs = ["UPC1", "UPC2"]
        campaign_type = InternalCampaignType.PLA
        self.__mock_async_external_http_client_service.post.return_value = Response(
            200,
            json={"data": {"suggestions": "Not a list"}}
        )

        with self.assertRaises(ValidationError) as context:
            await self.bid_manager_gateway.get_suggestions_response(koddi_advertiser_id, upcs, campaign_type)

        self.assertIsNotNone(context.exception)