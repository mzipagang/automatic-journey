from enum import Enum, StrEnum
from typing import List, Optional

from pydantic import Field, BaseModel, field_validator, model_validator

from app.common.model.shared import Meta
from typing_extensions import Annotated


class TargetTypeId(Enum):
    PLACEMENT = 1
    DIVISION = 2
    DAY_PARTING = 3

class TargetTypes(StrEnum):
    HOUR = 'HOUR'
    DIVISION = 'DIVISION'
    PLACEMENTS = 'PLACEMENTS'


class Target(BaseModel):
    type: str | int = Field(
        title="type",
        description="Type id of the adgroup target. "
                    "1 - Placement, "
                    "2 - Division, "
                    "3 - Day Parting"
    )
    id: Optional[int] = Field(
        default=None,
        title="id",
        description="Id to use for the adgroup target. "
                    "For placement targets, this should be the placement id. "
                    "For division targets, this should be division id."
    )
    values: Optional[List[int]] = Field(
        default=None,
        title="values",
        description="Values to use for the adgroup target. "
                    "For day parting targets, this should be a list of two values, "
                    "which are start and end hours (1 - 24) in the EST timezone."
    )


    def model_dump(self, *args, **kwargs):
        # Override the model_dump method to exclude 'values' if it is None
        target_dict = super().model_dump(*args,**kwargs)
        if target_dict.get('values') is None:
            target_dict.pop('values')
        return target_dict

# types:
# 1 - Placement
# 2 - Division
# 3 - Day Parting

# 1 needs ID, which is placement ID
# 2 needs ID, which is division ID
# 3 needs array of values (two values), which are start and end hours DO NOT USE YET
class TargetAdgroupRequest(BaseModel):
    type: int | str = Field(
        ...,
        title="type",
        description="Type id of the adgroup target. "
                    "1 - Placement, "
                    "2 - Division, "
                    "3 - Day Parting"
    )
    id: Optional[int] = Field(
        default=None,
        title="id",
        description="Id to use for the adgroup target. "
                    "For placement targets, this should be the placement id. "
                    "For division targets, this should be division id."
    )
    values: Optional[List[int]] = Field(
        default=None,
        strict=True,
        title="values",
        description="Values to use for the adgroup target. "
                    "For day parting targets, this should be a list of two values, "
                    "which are start and end hours (1 - 24) in the EST timezone."
    )

    # TODO: Do this or replace type: int in the field definition
    @model_validator(mode="after")
    def targets_validations(self):
        if isinstance(self.type, str):
            if not self.type.isdigit():
                raise ValueError("Type must be a valid numeric string")
        if self.values is not None and len(set(self.values)) != 2:
            raise ValueError('Values must contain exactly 2 unique items')
        return self

    def __hash__(self):
        serialized_values = None
        if self.values is not None:
            serialized_values = ", ".join(list(map(str, self.values)))
        return hash((self.type, self.id, serialized_values))

class TargetResponse(BaseModel):
    data: List[Target] = Field(title="data", description="List of Targets.")
    meta: Meta = Field(title="meta", description="Response metadata.")
