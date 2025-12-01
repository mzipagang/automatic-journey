import json
from typing import List

from fastapi import Depends, HTTPException
from httpx import codes as httpx_codes

from app.common.context.context import logging_extra_context
from app.common.decorators.decorators import conditionally_retry, async_conditionally_execute
from app.common.exceptions import ActivationLockedException, AdGroupNotPublishedException
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.async_http_client_service import AsyncInternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.utils.async_adapter import AsyncAdapter
from app.v2.model.downstream.activation_service import (
    ActivationsQueryBody,
    ActivationPayload,
    ActivationResponse,
    ActivationUpdatePayload,
    ActivationResponseV2,
    Validation,
)
from app.common.retry.predicates import activation_is_locked, ad_group_is_not_published
from app.common.services.http_client_service import InternalApiHttpClientService
from app.common.utils import filtered_logger
from app.common.utils.context_tools import update_context

logger = filtered_logger.get_logger(__name__)

class ActivationGateway:
    __internal_api_http_client: AsyncAdapter
    ACTIVATION_ENDPOINT = "/media/media-mgmt-activation/api/v2/activation"

    def __init__(
        self,
        async_internal_api_http_client_service: AsyncInternalApiHttpClientService = Depends(AsyncInternalApiHttpClientService),
        internal_api_http_client_service: InternalApiHttpClientService = Depends(InternalApiHttpClientService),
        harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__internal_api_http_client = AsyncAdapter(
            internal_api_http_client_service,
            async_internal_api_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_ACTIVATION,
            harness_service=harness_service
        )


    async def get_activation_by_id(self, activation_id: str) -> ActivationResponseV2[ActivationResponse]:
        path = f"{self.ACTIVATION_ENDPOINT}/{activation_id}"
        response = await self.__internal_api_http_client.get(
            path=path,
            response_body_type="json",
            forward_client_error_response_content=True
        )
        return ActivationResponseV2[ActivationResponse](**response.json())

    async def get_activations(self, query_body: ActivationsQueryBody) -> ActivationResponseV2[List[ActivationResponse]]:
        response = await self.__internal_api_http_client.get(
            path=self.ACTIVATION_ENDPOINT,
            params=query_body.model_dump(exclude_none=True),
            response_body_type="json",
            forward_client_error_response_content=True
        )

        activations = response.json()

        return ActivationResponseV2[List[ActivationResponse]](**activations)

    async def create_activation(self, activation_payload: ActivationPayload) -> ActivationResponseV2[ActivationResponse]:
        response = await self.__internal_api_http_client.post(
            path=self.ACTIVATION_ENDPOINT,
            json=activation_payload.model_dump(exclude_none=True),
            response_body_type="json",
            forward_client_error_response_content=True
        )
        return ActivationResponseV2[ActivationResponse](**response.json())

    async def update_activation(self, payload: ActivationUpdatePayload, internal_activation_id: str) -> ActivationResponseV2[ActivationResponse]:
        logger.info("Updating activation with payload: %s", payload)

        path = f"{self.ACTIVATION_ENDPOINT}/{internal_activation_id}"
        response = await self.__upstream_patch(
            activation_id=internal_activation_id,
            path=path,
            json_request_body=payload.model_dump(exclude_none=True),
            response_body_type='json',
            forward_client_error_response_content=True
        )

        update_context(logging_extra_context, activation_update_response=response.json())

        if "id" in response.json()["data"]:
            internal_activation_json = response.json()
            return ActivationResponseV2[ActivationResponse](**internal_activation_json)

        logger.warning('Activation %s update response was of unexpected shape.', internal_activation_id)
        error_message = "Failed to update activation"
        raise HTTPException(status_code=500, detail=f"Failed to update activation: {error_message}")

    async def publish_activation(self, internal_activation_id: str) -> ActivationResponse:
        response = await self.__upstream_patch(
            activation_id=internal_activation_id,
            response_body_type="json",
            path = f"{self.ACTIVATION_ENDPOINT}/{internal_activation_id}/publish"
        )

        if response.status_code == httpx_codes.OK:
            response_json = response.json()
            logger.info("Published activation response: %s", response_json)
            await self.wait_for_adgroup_publication_status_to_settle(internal_activation_id)
            return ActivationResponse(**response_json)

        logger.error(
            "Activation API publishing call returned error %s: for id: %s",
            response.status_code,
            internal_activation_id,
        )

        raise HTTPException(
            status_code=400,
            detail=f"Publishing failed for activation id {internal_activation_id} "
                   f"with error: {json.dumps(response.json())}",
        )

    async def validate_activation(self, internal_activation_id: str) -> bool:
        path = f"{self.ACTIVATION_ENDPOINT}/{internal_activation_id}/validate"
        response = await self.__internal_api_http_client.get(
            path=path,
            response_body_type="json"
        )

        response_json = response.json()
        validation = Validation(**response_json)

        logger.info("Activation ID: %s is Valid: %s", internal_activation_id, validation.valid)
        if validation.valid:
            return True

        if validation.errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "msg": "Failed to validate activation",
                    "loc": validation.errors,
                },
            )

        raise HTTPException(status_code=400, detail="Failed to validate activation")

    async def approve_activation(self, activation_id: str) -> ActivationResponseV2[ActivationResponse]:
        path = f"{self.ACTIVATION_ENDPOINT}/{activation_id}/approve"
        return await self.__apply_action_patch(path)

    async def pause_activation(self, activation_id: str) -> ActivationResponseV2[ActivationResponse]:
        path = f"{self.ACTIVATION_ENDPOINT}/{activation_id}/pause"
        return await self.__apply_action_patch(path)

    async def unpause_activation(self, activation_id: str) -> ActivationResponseV2[ActivationResponse]:
        path = f"{self.ACTIVATION_ENDPOINT}/{activation_id}/unpause"
        return await self.__apply_action_patch(path)

    @conditionally_retry(
        flag_name=HarnessFeatureFlags.LOCKED_ACTIVATION_FETCH_RETRY,
        logger=logger,
        retry_predicate=activation_is_locked)
    async def __get_activation_and_check_unlocked(self, activation_id: str) -> ActivationResponseV2[ActivationResponse]:
        activation = await self.get_activation_by_id(activation_id)
        if activation.data.metadata.is_locked:
            logger.info("Activation %s is locked", activation_id)
            raise ActivationLockedException()
        return activation

    async def __apply_action_patch(self, path: str) -> ActivationResponseV2[ActivationResponse]:
        response = await self.__internal_api_http_client.patch(
            path=path,
            response_body_type='json',
            forward_client_error_response_content=True
        )

        response_json = response.json()
        update_context(logging_extra_context, activation_patch_response=response_json)
        return ActivationResponseV2[ActivationResponse](**{"data": response_json})

    async def __upstream_patch(
            self,
            activation_id: str,
            path: str,
            json_request_body: dict = None,
            response_body_type: str | None = None,
            json_has_data_field: bool = False,
            forward_client_error_response_content: bool = False):
        update_context(logging_extra_context, activation_id=activation_id)

        logger.info("Ensuring activation is not locked")
        # Fetch to ensure not locked.
        activation_data = await self.__get_activation_and_check_unlocked(activation_id)

        update_context(logging_extra_context, activation_data=activation_data)
        logger.info("Activation is not locked upstream. Proceeding with patch")

        result = await self.__internal_api_http_client.patch(
            path=path,
            json=json_request_body,
            response_body_type=response_body_type,
            json_has_data_field=json_has_data_field,
            forward_client_error_response_content=forward_client_error_response_content
        )

        update_context(logging_extra_context, result=result.json())
        logger.info("Activation patch completed.")

        return result


    @async_conditionally_execute(flag_name=HarnessFeatureFlags.CHECK_ADGROUP_PUBLICATION_STATUS)
    @conditionally_retry(
        flag_name=HarnessFeatureFlags.UNPUBLISHED_ADGROUP_FETCH_RETRY,
        logger=logger,
        retry_predicate=ad_group_is_not_published)
    async def wait_for_adgroup_publication_status_to_settle(self, activation_id: str):
        logger.info("Fetching adgroup until publication is settled...")
        # activation here is the adgroup activation from activation service.
        activation = await self.get_activation_by_id(activation_id)
        # if unpublished_data is present, it means the adgroup is not yet published
        is_pending = activation.data.unpublished_data
        errors = activation.errors
        if not errors and is_pending:
            logger.info("Adgroup %s is not yet published, re-fetching...", activation_id)
            raise AdGroupNotPublishedException