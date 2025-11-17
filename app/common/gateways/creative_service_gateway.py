import json

from httpx import codes as httpx_codes

from fastapi import Depends, HTTPException
from pydantic_core import ValidationError

from app.common.model.downstream.creative_group import CreativeAdGroupRequest, CreativeAdGroupCreateResponse
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.async_http_client_service import AsyncInternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.services.http_client_service import InternalApiHttpClientService
from app.common.utils.async_adapter import AsyncAdapter


class CreativeServiceGateway:
    __SERVICE_BASE_PATH = "/media/creative/api/v1"
    __internal_http_client: AsyncAdapter

    def __init__(
            self,
            async_internal_api_http_client: AsyncInternalApiHttpClientService = Depends(AsyncInternalApiHttpClientService),
            internal_api_http_client: InternalApiHttpClientService = Depends(InternalApiHttpClientService),
            harness_service: HarnessService = Depends(HarnessService)):

        self.__internal_http_client = AsyncAdapter(
            async_client=async_internal_api_http_client,
            sync_client=internal_api_http_client,
            harness_service=harness_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_CREATIVE)

    async def creative_group_is_ready(self, creative_entity_id: str) -> bool:
        request_path: str = f"{self.__SERVICE_BASE_PATH}/creative-designs/groups/{creative_entity_id}/most-recent-assets/status"

        response = await self.__internal_http_client.get(path=request_path)

        return httpx_codes.is_success(response.status_code)

    async def init_creative_group(self, request: CreativeAdGroupRequest, template_group_id: str) -> CreativeAdGroupCreateResponse:
        request_path: str = f"{self.__SERVICE_BASE_PATH}/creative-designs/groups?templateGroupId={template_group_id}"

        response = await self.__internal_http_client.post(path=request_path, json=request.model_dump())
        try:
            return CreativeAdGroupCreateResponse(**response.json())
        except json.decoder.JSONDecodeError:
            raise HTTPException(status_code=response.status_code, detail="Incorrect response from Creative Service")
        except ValidationError:
            raise HTTPException(status_code=500, detail="Incorrect response from Creative Service")
