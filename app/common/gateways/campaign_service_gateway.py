from copy import deepcopy
from enum import StrEnum
from typing import List

from app.common.model.campaign_types import InternalCampaignType
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.utils.async_adapter import AsyncAdapter
from app.common.utils.response_handler import ResponseHandlerBuilder, DefaultResponseHandler
from app.common.view_models import PatchOperation
from app.common.decorators.decorators import conditionally_retry, conditionally_execute
from app.common.exceptions.campaign_exceptions import CampaignNotPublishedException
from app.common.model.downstream.campaign_activation_service import CASCampaign
from app.common.model.downstream.campaign_service import CampaignResponse, ValidateResponse, PublishResponse, \
    CampaignSearchRequest, CampaignsResponse, Meta, Page
from app.common.model.pause_operation_type import PauseOperationType

from app.common.model.shared import InternalPublishStatus, PublishStatus
from app.common.retry.predicates import campaign_is_not_published
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger
from fastapi import Depends, HTTPException
from httpx import codes as httpx_codes, Response

from app.v2.utils.koddi_error_map import KoddiErrorMap
from app.v2.view_models import CampaignPatchRequest

logger = filtered_logger.get_logger(__name__)

class ValidationType(StrEnum):
    CREATE = "create"
    SUBMIT = "submit"
    APPROVE = "approve"


class CampaignServiceGateway:

    def __init__(
            self,
            async_external_api_http_client_service: AsyncExternalApiHttpClientService = Depends(AsyncExternalApiHttpClientService),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__external_api_http_client = AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_CAMPAIGN,
            harness_service=harness_service
        )
        self.__backend_service_error_message = "Unable to complete request. Try again later."
        self.campaign_search_response_handler = ResponseHandlerBuilder()\
            .handle_data(CampaignsResponse)\
            .handle_status(404, self.__empty_campaign)\
            .append_handler(DefaultResponseHandler)\
            .build()

    @staticmethod
    def __empty_campaign(response: Response, payload: CampaignSearchRequest) -> CampaignsResponse:
        return CampaignsResponse(
            data=[],
            meta=Meta(
                page=Page(
                    offset=payload.page_offset,
                    size=payload.page_size,
                    hasMore=False,
                    totalPages=0,
                    totalCount=0
                )
            )
        )

    @staticmethod
    def calculate_external_publication_status(internal_publication_status: InternalPublishStatus) -> PublishStatus:
        if internal_publication_status in [
            InternalPublishStatus.PENDING,
            InternalPublishStatus.IN_PROGRESS,
            InternalPublishStatus.DELIVERY_PENDING,
            InternalPublishStatus.DELIVERY_SUCCESS
        ]:
            return PublishStatus.PENDING

        if internal_publication_status == InternalPublishStatus.SUCCESS:
            return PublishStatus.PUBLISHED

        return PublishStatus(internal_publication_status.value)

    @staticmethod
    def __filter_campaign_types(campaign_response: CampaignResponse) -> None:
        unsupported_campaign_types = {InternalCampaignType.UNSUPPORTED}
        campaign_dict = campaign_response.model_dump(exclude_unset=True, exclude_none=True)

        included_types = {
            campaign_dict.get("publishedChanges", {}).get("type"),
            campaign_dict.get("unpublishedChanges", {}).get("type"),
        }

        if unsupported_campaign_types.intersection(included_types):
            raise HTTPException(status_code=400, detail="Unsupported campaign type")

    async def get_campaign(self, internal_campaign_id: str) -> CampaignResponse:
        path = f"/map-campaign-service/v1/campaign/{internal_campaign_id}"
        logger.debug("Calling Campaign Service API with url %s", path)
        response = await self.__external_api_http_client.get(
            path=path,
            response_body_type='json',
            json_has_data_field=True,
            forward_client_error_response_content=True)

        campaign_response = CampaignResponse(**response.json().get("data"))
        self.__filter_campaign_types(campaign_response)

        return campaign_response

    async def noop(*args, **kwargs):
        pass
    @conditionally_execute(flag_name=HarnessFeatureFlags.CHECK_CAMPAIGN_PUBLICATION_STATUS, default_method=noop)
    @conditionally_retry(
        flag_name=HarnessFeatureFlags.UNPUBLISHED_CAMPAIGN_FETCH_RETRY,
        logger=logger,
        retry_predicate=campaign_is_not_published)
    async def wait_for_campaign_publication_status_to_settle(self, internal_campaign_id: str) -> CampaignResponse:
        logger.info("Fetching campaign until publication is settled...")
        campaign = await self.get_campaign(internal_campaign_id)
        publication_status = self.calculate_external_publication_status(
            InternalPublishStatus(campaign.publishingStatus))
        if publication_status not in [PublishStatus.PUBLISHED, PublishStatus.FAILED, PublishStatus.EMPTY]:
            logger.info("Campaign %s is not yet published, re-fetching...", internal_campaign_id)
            raise CampaignNotPublishedException(campaign_id=internal_campaign_id)
        return campaign


    async def validate_campaign(self, internal_campaign_id: str, validation_type: ValidationType) -> bool:

        logger.debug("Validating campaign submit with id: %s and validation_type: %s", internal_campaign_id, validation_type.value)
        path = f"/map-campaign-service/v1/campaign/{internal_campaign_id}" \
               f"/validate?validationType={validation_type.value}"

        response = await self.__external_api_http_client.get(
            path=path,
            response_body_type='json',
            forward_client_error_response_content=True)

        response_object = ValidateResponse(**response.json().get("data"))

        if response_object.status != "VALID":
            return False

        return True

    async def patch_campaign(self, internal_campaign_id: str, payload: dict) -> bool:
        path = f"/map-campaign-service/v1/campaign/{internal_campaign_id}"

        logger.info('Updating campaign %s with payload: %s url: %s', internal_campaign_id,
                    payload, path)

        response = await self.__external_api_http_client.patch(
            path=path,
            json=payload,
        )

        logger.info(
            "Response from Campaign Service patch: %s - content: %s",
            response.status_code,
            response.content)

        # this includes all 2xx response codes
        if response.is_success:
            return True

        detail = ""
        response_json = response.json()
        if response.status_code == httpx_codes.BAD_REQUEST and response_json.get("errors") is not None:
            for error in response_json.get("errors"):
                detail += KoddiErrorMap.remap(error["reason"].lower())

        if response.status_code == httpx_codes.UNPROCESSABLE_ENTITY and response_json.get("errors") is not None:
            for error in response_json.get("errors"):
                detail += KoddiErrorMap.remap(error.get("reason").lower())

        raise HTTPException(
            status_code=response.status_code, detail=detail or self.__backend_service_error_message )

    async def patch_contacts_and_addresses(self, internal_campaign_id: str, patch_request: CampaignPatchRequest) -> bool:

        map_campaigns_url = f"/map-campaign-service/v1/campaign/{internal_campaign_id}"

        payload = [
            PatchOperation(op="replace", path="/primaryAccount/addresses", value=patch_request.addressList),
            PatchOperation(op="add", path="/primaryAccount/contacts", value=patch_request.contactList)
        ]

        patch_payload = [patch.dict() for patch in payload]

        logger.info('Updating campaign contacts %s with payload: %s', internal_campaign_id, patch_payload)

        response = await self.__external_api_http_client.patch(path=map_campaigns_url, json=patch_payload)

        if response.is_success:
            return True
        logger.error(
            "Error creating campaign code: %s - content: %s", response.status_code, response.content)
        raise HTTPException(status_code=500, detail=self.__backend_service_error_message)

    async def pause_or_unpause_campaign(self, internal_campaign_id: str, operation: PauseOperationType) -> None:
        path = f"/map-campaign-service/v1/campaign/{internal_campaign_id}/{operation.value}"

        response = await self.__external_api_http_client.patch(
            path=path,
            forward_client_error_response_content=True)

        logger.info(
            "Response from Campaign Service pause: %s - content: %s",
            response.status_code,
            response.content)

        if not response.is_success:
            raise HTTPException(
                status_code=response.status_code, detail="Unable to complete request. Try again later.")

        await self.wait_for_campaign_publication_status_to_settle(internal_campaign_id)

    async def publish_campaign(self, internal_campaign_id: str) -> PublishStatus:
        path = f"/map-campaign-service/v1/campaign/{internal_campaign_id}/publish"

        internal_campaign: CampaignResponse = await self.get_campaign(internal_campaign_id=internal_campaign_id)

        if internal_campaign.validations:
            logger.warning("Campaign %s has validation warnings: %s",
                           internal_campaign_id,
                           internal_campaign.validations)
            return self.calculate_external_publication_status(
                InternalPublishStatus(internal_campaign.publishingStatus))

        response = await self.__external_api_http_client.post(
            path=path,
            json={"fields": []},
            forward_client_error_response_content=True)
        logger.debug("Called Publishing Service with url %s", path)

        data = response.json().get("data")
        if data is None:
            raise CampaignNotPublishedException(campaign_id=internal_campaign_id)

        response_object = PublishResponse(**data)

        if not response_object.status:
            logger.error('Error Publishing Campaign %s: %s', response.status_code, response.content)
            return PublishStatus.FAILED

        await self.wait_for_campaign_publication_status_to_settle(internal_campaign_id)
        campaign = await self.get_campaign(internal_campaign_id)

        logger.info(
            "Scheduled Publish Campaign %s: %s",
            internal_campaign_id,
            campaign.publishingStatus,
        )
        return self.calculate_external_publication_status(campaign.publishingStatus)


    async def search_campaigns(self, payload: CampaignSearchRequest) -> CampaignsResponse:
        path = "/map-campaign-service/v1/campaigns"

        response = await self.__external_api_http_client.post(
            path=path,
            json=payload.model_dump(exclude_none=True, by_alias=True)
        )

        return self.campaign_search_response_handler.handle_response(response, payload)

    async def get_campaigns(
            self,
            get_campaigns_request: CampaignSearchRequest
    ) -> List[CASCampaign]:
        campaigns = []
        page_size = get_campaigns_request.page_size
        page_number = 0
        response = await self.search_campaigns(get_campaigns_request)
        campaigns.extend(response.data)

        while response.meta.page.hasMore:
            page_number += 1
            next_page_request = deepcopy(get_campaigns_request)
            next_page_request.page_offset = page_size * page_number
            response = await self.search_campaigns(next_page_request)
            campaigns.extend(response.data)

        return campaigns
