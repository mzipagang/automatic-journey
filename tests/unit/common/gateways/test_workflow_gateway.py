from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from httpx import Response

from app.common.gateways.workflow_gateway import WorkflowGateway
from app.common.model.shared import InternalCampaignType
from app.common.view_models import WorkflowActions


class TestWorkflowGateway(IsolatedAsyncioTestCase):
    async_mock_client: AsyncMock
    sync_mock_client: MagicMock
    mock_harness_service: MagicMock
    workflow_gateway: WorkflowGateway

    def setUp(self):
        self.async_mock_client = AsyncMock()
        self.sync_mock_client = MagicMock()
        self.mock_harness_service = MagicMock()

        self.mock_harness_service.is_harness_flag_on.return_value = True

        self.workflow_gateway = WorkflowGateway(
            async_external_api_http_client_service=self.async_mock_client,
            external_api_http_client_service=self.sync_mock_client,
            harness_service=self.mock_harness_service
        )

    async def test_set_workflow_campaign_status__returns_false_if_action_is_not_create(self):
        result = await self.workflow_gateway.set_workflow_campaign_status(
            "1234",
            "invalid action"
        )

        self.assertFalse(result)

    async def test_set_workflow_campaign_status__makes_upstream_request(self):
        campaign_id = "1234"
        self.async_mock_client.post.return_value = Response(status_code=200)

        result = await self.workflow_gateway.set_workflow_campaign_status(
            campaign_id,
            WorkflowActions.CAMPAIGN_CREATE
        )

        self.assertTrue(result)
        self.async_mock_client.post.assert_called_once_with(
            path=f"/map-workflow-gateway/campaign/{campaign_id}/action",
            json={
                "workflowAction": {
                    "id": "/campaignSummary#navigate",
                    "type": "execute",
                    "name": "Summary",
                    "route": "/campaignSummary"
                }
            }
        )

    async def test_set_workflow_campaign_status__raises_server_error(self):
        campaign_id = "1234"
        self.async_mock_client.post.return_value = Response(
            status_code=500,
            json={}
        )

        with self.assertRaises(HTTPException) as context:
            await self.workflow_gateway.set_workflow_campaign_status(
                campaign_id,
                WorkflowActions.CAMPAIGN_CREATE
            )

        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Backend service unavailable", context.exception.detail)

    async def test_set_workflow_campaign_status__raises_client_error(self):
        campaign_id = "1234"
        self.async_mock_client.post.return_value = Response(status_code=404)

        with self.assertRaises(HTTPException) as context:
            await self.workflow_gateway.set_workflow_campaign_status(
                campaign_id,
                WorkflowActions.CAMPAIGN_CREATE
            )

        self.assertEqual(400, context.exception.status_code)
        self.assertEqual("Failed to update campaign workflow status", context.exception.detail)

    async def test_initialize_campaign__makes_upstream_request(self):
        campaign_type = InternalCampaignType.CAROUSEL
        campaign_id = "1234"
        self.async_mock_client.post.return_value = Response(
            status_code=200,
            json={"businessKey": campaign_id}
        )

        response = await self.workflow_gateway.initialize_campaign(campaign_type)

        self.async_mock_client.post.assert_called_with(
            path="/map-workflow-gateway/campaign/initialize",
            json={"type": "Promoted_Products_Carousel"},
            response_body_type='json',
            forward_client_error_response_content=True
        )
        self.assertEqual(campaign_id, response.businessKey)