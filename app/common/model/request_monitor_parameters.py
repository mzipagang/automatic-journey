from typing import Optional

from pydantic import Field
from pydantic.main import BaseModel

from app.common.view_models import PacingType
from app.common.model.shared import BudgetType


class RequestMonitorParameter(BaseModel):
    field_name: str = Field(
        title="field_name", description="Name of the field to monitor"
    )
    field_type: type = Field(
        title="field_type", description="Type of the field to monitor"
    )
    monitored_transaction: str = Field(
        title="monitored_transaction", description="Transaction to monitor"
    )

    def __init__(self, field_name: str, field_type: type, monitored_transaction: str):
        super().__init__(
            field_name=field_name,
            field_type=field_type,
            monitored_transaction=monitored_transaction,
        )
        self.field_name = field_name
        self.field_type = field_type
        self.monitored_transaction = monitored_transaction


class FieldDeltaRequestMonitorParameter(RequestMonitorParameter):
    field_delta_threshold: Optional[float] = Field(
        default=None,
        title="field_delta_threshold",
        description="Threshold for field delta",
    )
    field_percentage_delta_threshold: Optional[float] = Field(
        default=None,
        title="field_percentage_delta_threshold",
        description="Threshold for field percentage delta",
    )

    def __init__(
        self,
        field_name: str,
        field_type: type,
        monitored_transaction: str,
        field_delta_threshold: float,
    ):
        super().__init__(
            field_name=field_name,
            field_type=field_type,
            monitored_transaction=monitored_transaction,
        )
        self.field_delta_threshold = field_delta_threshold


class BudgetAmountRequestMonitorParameter(RequestMonitorParameter):
    def __init__(self):
        super().__init__(
            field_name="budgetAmount",
            field_type=float,
            monitored_transaction="BUDGET-AMOUNT-CHANGE-REQUESTED",
        )


class BudgetAmountDeltaRequestMonitorParameter(FieldDeltaRequestMonitorParameter):
    def __init__(self):
        super().__init__(
            field_name="budgetAmount",
            field_type=float,
            monitored_transaction="BUDGET-AMOUNT-CHANGE-DELTA-REQUESTED",
            field_delta_threshold=0.1,
        )


class BudgetTypeRequestMonitorParameter(RequestMonitorParameter):
    def __init__(self):
        super().__init__(
            field_name="budgetType",
            field_type=BudgetType,
            monitored_transaction="BUDGET-TYPE-CHANGE-REQUESTED",
        )


class PacingTypeRequestMonitorParameter(RequestMonitorParameter):
    def __init__(self):
        super().__init__(
            field_name="pacingType",
            field_type=PacingType,
            monitored_transaction="PACING-TYPE-CHANGE-REQUESTED",
        )
