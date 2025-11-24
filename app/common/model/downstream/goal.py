from typing import Optional

from pydantic import BaseModel, Field

from app.common.model.shared import IgnoreCaseStrEnum


class GoalType(IgnoreCaseStrEnum):
    ROAS = "ROAS"


class Goal(BaseModel):
    type: Optional[GoalType] = None
    value: Optional[int] = Field(default=None, ge=1, le=75)
    priority: Optional[int] = None


class GoalGroup(BaseModel):
    goals: list[Goal]
    goal_id: Optional[str] = None


class CreateGoalsResponse(BaseModel):
    goal_id: Optional[str] = None
