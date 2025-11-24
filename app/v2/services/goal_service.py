from fastapi import Depends

from app.common.gateways.goal_gateway import GoalGateway
from app.common.model.downstream.goal import GoalGroup, Goal
from app.common.services.harness_service import HarnessService


class GoalService:
    goal_gateway: GoalGateway

    def __init__(
        self,
        goal_gateway: GoalGateway = Depends(GoalGateway),
        harness_service: HarnessService = Depends(HarnessService),
    ):
        self.goal_gateway = goal_gateway
        self.harness_service = harness_service


    async def get_goals(self, goal_id: str) -> GoalGroup:
        return await self.goal_gateway.get_goals(goal_id)


    async def create_goals(self, goals: list[Goal]) -> str:
        return await self.goal_gateway.create_goals(goals)
