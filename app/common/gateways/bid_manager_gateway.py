import json
from typing import List

import httpx
from fastapi import Depends, HTTPException
from pydantic import ValidationError

from app.common.model.campaign_types import (
    InternalCampaignType,
    convert_enum,
    BidManagerCampaignType
)
from app.common.model.downstream.bid_manager import (
    BidValidationFailureResponse,
    BidValidationResponse,
    CreateBidsRequest,
    CreateBidsResponse,
    IncorrectBids,
    MultipleBidsResponse,
    MultipleBidsResponseData,
    SuggestionsResponse,
    ValidateBidRequest,
)
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.utils.async_adapter import AsyncAdapter

logger = filtered_logger.get_logger(__name__)

# Implements downstream calls to bid management
class BidManagerGateway:
    __external_api_http_client: AsyncAdapter

    def __init__(
            self,
            async_external_api_http_client: AsyncExternalApiHttpClientService = Depends(AsyncExternalApiHttpClientService),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__external_api_http_client =  AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client,
            harness_flag_name=HarnessFeatureFlags.ASYNC_BID_MANAGER,
            harness_service=harness_service
        )


    async def __get_bids_response(self, ids: List[str]) -> MultipleBidsResponseData:
        query_params = {"ids": ",".join(ids)}
        path = "/bid-manager/v1/bids"
        response = await self.__external_api_http_client.get(
            path=path,
            params=query_params,
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )
        response_json = response.json()
        return MultipleBidsResponse(**response_json).data


    async def __validate_bid_response(
            self,
            bid_entity_id: str,
            validate_bid_request: ValidateBidRequest
    ) -> BidValidationResponse:
        path = f"/bid-manager/v1/bids/{bid_entity_id}/validate"
        try:
            await self.__external_api_http_client.post(
                path=path,
                json=validate_bid_request.model_dump(exclude_unset=True),
                response_body_type="json",
                forward_client_error_response_content=True
            )

            return BidValidationResponse(valid=True)
        except HTTPException as e:
            if e.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
                bid_validation_failure = BidValidationFailureResponse(**e.detail)
                return self.__build_bid_validation_response_from_error_response(bid_validation_failure)

            logger.error(
                "Unable to process %s response from Bid Manager Validate API: %s",
                e.status_code,
                e.detail,
            )
            raise e

    @staticmethod
    def __build_bid_validation_response_from_error_response(
            bid_validation_failure: BidValidationFailureResponse
    ) -> BidValidationResponse:
        """allowed_errors = [
            "incorrect-min-bid-failure"
            "incorrect-bid-failure",
            "incorrect-max-bid-failure"
        ]
        invalid_upc_errors: List[IncorrectBids] = [
            error
            for error in bid_validation_failure.errors
            if error.type in allowed_errors
        ]
        invalid_upcs = []
        for error in invalid_upc_errors:
            for failure in error.bid_failure_list:
                upc, match, reason = failure.message.partition(" ")
                if upc.isdigit():
                    invalid_upcs.append(upc)"""
        # TODO: return the invalid upcs when discovery task finishes
        return BidValidationResponse(valid=False, errors=bid_validation_failure.errors, invalid_upcs=[])

    async def get_suggestions_response(
            self,
            koddi_advertiser_id: int,
            upcs: List[str],
            type: InternalCampaignType
    ) -> SuggestionsResponse:
        path = "/bid-manager/v2/suggestions"
        response = await self.__external_api_http_client.post(
            path=path,
            json={
                "advertiser_id": koddi_advertiser_id,
                "entities": upcs,
                "type": convert_enum(type, BidManagerCampaignType)
            },
            response_body_type="json",
            forward_client_error_response_content=True
        )

        return SuggestionsResponse(**response.json().get("data", {}))

    async def get_bids(self, ids: List[str]) -> MultipleBidsResponseData:
        response = MultipleBidsResponseData()
        # Stop early if there are no ids
        if not ids:
            return response

        # Filter out falsy ids (empty strings, none, ect)
        filtered_ids = [i for i in ids if i]

        # Stop early if no ids left after filtering
        if not filtered_ids:
            return response

        # Create batches of 50 ids
        # Bid management can only support up to 50 ids at a time
        batches = [filtered_ids[i:i + 50] for i in range(0, len(filtered_ids), 50)]

        for batch in batches:
            try:
                bids_response = await self.__get_bids_response(batch)
                response.found.extend(bids_response.found)
                response.notFound.extend(bids_response.notFound)
            except json.JSONDecodeError as ex:
                logger.error("JSONDecodeError - Unable to decode JSON for batch %s: %s", batch, ex.doc)
                continue
            except ValidationError as ex:
                logger.error(
                    "Response Validation Error for batch %s: %s",
                    batch, str(ex)
                )
                continue

        return response

    async def validate_bid(self, bid_entity_id: str, validate_bid_request: ValidateBidRequest) -> BidValidationResponse:
        if bid_entity_id:
            result = await self.__validate_bid_response(
                bid_entity_id,
                validate_bid_request
            )
            return result
        return BidValidationResponse(valid=False, invalid_upcs=None)

    async def create_bids(
            self,
            create_bids_request: CreateBidsRequest,
            enforce_validation: bool
    ) -> str:
        if create_bids_request.type == InternalCampaignType.UNSUPPORTED:
            raise HTTPException(
                status_code=httpx.codes.BAD_REQUEST,
                detail="Cannot create bids for unsupported campaign type."
            )
        logger.info("Creating Bids with payload: %s", create_bids_request.model_dump())
        path = "/bid-manager/v1/bids"
        response = await self.__external_api_http_client.post(
            path=path,
            params={"enforceBidCreationValidation": enforce_validation},
            json=create_bids_request.model_dump(),
            response_body_type="json",
            forward_client_error_response_content=True
        )

        response_json = response.json()
        create_bids_response = CreateBidsResponse(**response_json)
        return create_bids_response.id
