from unittest import IsolatedAsyncioTestCase

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.common.gateways.goal_gateway import GoalGateway
from app.common.model.downstream.goal import (
    GoalGroup,
    Goal,
    GoalType,
)

class TestGoalGateway(IsolatedAsyncioTestCase):
    async_mock_client: AsyncMock
    goal_gateway: GoalGateway

    def setUp(self):
        self.async_mock_client = AsyncMock()

        self.goal_gateway = GoalGateway(
            async_internal_api_http_client_service=self.async_mock_client)


    @pytest.mark.asyncio
    async def test_get_goals_calls_get_and_returns_goalgroup(self):
        response = {
            "goals": [
                {"type": "ROAS", "value": 60, "priority": 1}
            ]
        }
        expected_result = GoalGroup(**response)
        mock_response = MagicMock()
        mock_response.json.return_value = response
        self.async_mock_client.get.return_value = mock_response

        result = await self.goal_gateway.get_goals("my-goal-id")

        self.async_mock_client.get.assert_called_once()
        self.async_mock_client.get.assert_awaited_once()
        self.assertEqual(result, expected_result)


    @pytest.mark.asyncio
    async def test_create_goals_posts_payload_and_returns_goal_id(self):
        response = {"goal_id": "generated-id-42"}
        mock_response = MagicMock()
        mock_response.json.return_value = response
        self.async_mock_client.post.return_value = mock_response

        # Act
        result = await self.goal_gateway.create_goals([Goal(type=GoalType.ROAS, value=75, priority=1)])

        # Assert
        self.async_mock_client.post.assert_awaited_once()
        self.assertEqual(result, "generated-id-42")
