from fastapi import Depends, HTTPException
from httpx import codes as httpx_codes

from app.common.model.campaign_types import InternalCampaignType, convert_enum, CASCampaignType
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.utils.async_adapter import AsyncAdapter
from app.common.view_models import WorkflowActions
from app.common.model.downstream.workflow import InitializeCampaignResponse
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class WorkflowGateway:
    """WorkflowGateway is a class that provides methods to interact with the Workflow API.

    Raises:
        HTTPException
            If the API response indicates a server error or if the request fails.
    """
    __external_api_http_client: AsyncAdapter
    ENDPOINT = "/map-workflow-gateway"

    def __init__(
            self,
            async_external_api_http_client_service: AsyncExternalApiHttpClientService = Depends(
                AsyncExternalApiHttpClientService),
            external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
            harness_service: HarnessService = Depends(HarnessService),
    ):
        self.__external_api_http_client = AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client_service,
            harness_flag_name=HarnessFeatureFlags.ASYNC_WORKFLOW,
            harness_service=harness_service
        )

    async def set_workflow_campaign_status(self, internal_campaign_id: str, action: WorkflowActions) -> bool:
        logger.info("Setting workflow status to summary for campaign: %s", internal_campaign_id)
        if action == WorkflowActions.CAMPAIGN_CREATE:
            payload = {
                "workflowAction": {
                    "id": "/campaignSummary#navigate",
                    "type": "execute",
                    "name": "Summary",
                    "route": "/campaignSummary"
                }
            }
        else:
            return False

        response = await self.__external_api_http_client.post(
            path=f"{self.ENDPOINT}/campaign/{internal_campaign_id}/action",
            json=payload,
        )
        if response.status_code == httpx_codes.INTERNAL_SERVER_ERROR:
            logger.error('Workflow API call returned error %s: %s', response.status_code, response.content)
            raise HTTPException(status_code=500, detail="Backend service unavailable")

        if response.status_code == httpx_codes.OK:
            return True

        raise HTTPException(status_code=400, detail="Failed to update campaign workflow status")

    async def initialize_campaign(
            self,
            campaign_type: InternalCampaignType
    ) -> InitializeCampaignResponse:
        response = await self.__external_api_http_client.post(
            path=f"{self.ENDPOINT}/campaign/initialize",
            json={"type": f"{convert_enum(campaign_type, CASCampaignType)}"},
            response_body_type='json',
            forward_client_error_response_content=True
        )
        return InitializeCampaignResponse(**response.json())
