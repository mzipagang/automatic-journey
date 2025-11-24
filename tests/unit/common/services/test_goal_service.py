from unittest import IsolatedAsyncioTestCase

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.v2.services.goal_service import GoalService
from app.common.gateways.goal_gateway import GoalGateway
from app.common.model.downstream.goal import GoalGroup, Goal, GoalType


class TestGoalService(IsolatedAsyncioTestCase):
    mock_goal_gateway: MagicMock
    mock_harness_service: MagicMock
    service: GoalService

    def setUp(self):
        self.mock_goal_gateway = MagicMock(spec=GoalGateway)
        self.mock_goal_gateway.get_goals = AsyncMock()
        self.mock_goal_gateway.create_goals = AsyncMock()

        self.mock_harness_service = MagicMock()
        self.mock_harness_service.is_harness_flag_on.return_value = True

        self.service = GoalService(
            goal_gateway=self.mock_goal_gateway,
            harness_service=self.mock_harness_service,
        )

    async def test_init_uses_injected_services(self):
        self.assertIs(self.service.goal_gateway, self.mock_goal_gateway)
        self.assertIs(self.service.harness_service, self.mock_harness_service)

    @pytest.mark.asyncio
    async def test_get_goals_delegates_and_returns_goalgroup(self):
        expected = GoalGroup(goals=[Goal(type=GoalType.ROAS, value=18, priority=1)])
        self.mock_goal_gateway.get_goals.return_value = expected

        result = await self.service.get_goals("my-goal-id")

        self.mock_goal_gateway.get_goals.assert_awaited_once()
        self.assertEqual(result, expected)


    @pytest.mark.asyncio
    async def test_create_goals_delegates_and_returns_goal_id(self):
        expected_id = "generated-id-42"
        self.mock_goal_gateway.create_goals.return_value = expected_id

        result = await self.service.create_goals([Goal(type=GoalType.ROAS, value=25, priority=1)])

        self.mock_goal_gateway.create_goals.assert_awaited_once()
        self.assertEqual(result, expected_id)
