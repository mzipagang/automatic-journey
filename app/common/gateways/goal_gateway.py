from fastapi import Depends

from app.common.model.downstream.goal import GoalGroup, Goal, CreateGoalsResponse
from app.common.services.async_http_client_service import AsyncInternalApiHttpClientService


class GoalGateway:
    GOAL_ENDPOINT = "/media/media-mgmt-activation/api/v2/goal"

    def __init__(
        self,
        async_internal_api_http_client_service: AsyncInternalApiHttpClientService = Depends(AsyncInternalApiHttpClientService),
    ):
        self.async_internal_api_http_client_service = async_internal_api_http_client_service

    async def get_goals(self, goal_id: str) -> GoalGroup:
        path = f"{self.GOAL_ENDPOINT}/{goal_id}"
        response = await self.async_internal_api_http_client_service.get(
            path=path,
            response_body_type="json",
            forward_client_error_response_content=True,
        )
        return GoalGroup(**response.json())

    async def create_goals(self, goals: list[Goal]) -> str:
        create_goals_request = {"goals": [goal.model_dump() for goal in goals]}
        response = await self.async_internal_api_http_client_service.post(
            path=self.GOAL_ENDPOINT,
            json=create_goals_request,
            response_body_type="json",
            forward_client_error_response_content=True,
        )

        goals_response = CreateGoalsResponse(**response.json())

        return goals_response.goal_id
