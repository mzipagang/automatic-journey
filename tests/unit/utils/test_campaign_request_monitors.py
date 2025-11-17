from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, MagicMock

from app.common.view_models import (
    CampaignPutRequest,
    PacingType,
)
from app.v2.view_models import Campaign
from app.common.model.shared import BudgetType
from app.common.utils.campaign_request_monitors import CampaignUpdateRequestMonitor

@patch('logging.Logger.info')
class TestCampaignRequestMonitors(TestCase):
    __BASE_CAMPAIGN_PUT_REQUEST = CampaignPutRequest(
            name="Test Campaign",
            status="ACTIVE",
            startDate="2021-01-01",
            budgetAmount=100.0,
            budgetType="DAILY",
            pacingType="EVEN",
            billingInsertionOrder="IO123",
            billingPurchaseOrder="PO123",
            billingadditionalDetails="Additional Details"
        )

    __BASE_CAMPAIGN_ENTITY = Campaign(
        id=123,
        name="Test Campaign",
        status="ACTIVE",
        startDate="2021-01-01",
        endDate="2021-01-31",
        budgetAmount=100.0,
        budgetType="DAILY",
        pacingType="EVEN",
        accountId=1,
        advertiserIds=[2],
        billingInsertionOrder="IO123",
        billingPurchaseOrder="PO123",
        billingContactId=3,
        billingAddressId=4)

    def test_monitor_request__pacing_change__should_emit(self, mock_info_logger: MagicMock):
        existing_entity = deepcopy(self.__BASE_CAMPAIGN_ENTITY)
        request = deepcopy(self.__BASE_CAMPAIGN_PUT_REQUEST)

        request.pacingType = "ASAP"

        CampaignUpdateRequestMonitor.monitor_request(
            request=request,
            existing_entity=existing_entity,
            account_id=1,
            campaign_id=123)

        mock_info_logger.assert_called_once_with(
            "MONITORED TRANSACTION CHANGE REQUESTED",
            extra={
                "field_name": "pacingType",
                "field_type": PacingType,
                "monitored_transaction": "PACING-TYPE-CHANGE-REQUESTED",
                "existing_value": "EVEN",
                "new_value": "ASAP",
                "request": request.dict(),
                "account_id": 1,
                "campaign_id": 123,
                "ad_group_id": None
            }
        )

    def test_monitor_request__budget_amount_change__should_emit(self, mock_info_logger: MagicMock):
        existing_entity = deepcopy(self.__BASE_CAMPAIGN_ENTITY)
        request = deepcopy(self.__BASE_CAMPAIGN_PUT_REQUEST)

        request.budgetAmount = 200.0

        CampaignUpdateRequestMonitor.monitor_request(
            request=request,
            existing_entity=existing_entity,
            account_id=1,
            campaign_id=123)

        mock_info_logger.assert_called_once_with(
            "MONITORED TRANSACTION CHANGE REQUESTED",
            extra={
                "field_name": "budgetAmount",
                "field_type": float,
                "monitored_transaction": "BUDGET-AMOUNT-CHANGE-REQUESTED",
                "existing_value": 100.0,
                "new_value": 200.0,
                "request": request.dict(),
                "account_id": 1,
                "campaign_id": 123,
                "ad_group_id": None
            }
        )

    def test_monitor_request__budget_type_change__should_emit(self, mock_info_logger):
        existing_entity = deepcopy(self.__BASE_CAMPAIGN_ENTITY)
        request = deepcopy(self.__BASE_CAMPAIGN_PUT_REQUEST)

        request.budgetType = "LIFETIME"

        CampaignUpdateRequestMonitor.monitor_request(
            request=request,
            existing_entity=existing_entity,
            account_id=1,
            campaign_id=123)

        mock_info_logger.assert_called_once_with(
            "MONITORED TRANSACTION CHANGE REQUESTED",
            extra={
                "field_name": "budgetType",
                "field_type": BudgetType,
                "monitored_transaction": "BUDGET-TYPE-CHANGE-REQUESTED",
                "existing_value": "DAILY",
                "new_value": "LIFETIME",
                "request": request.dict(),
                "account_id": 1,
                "campaign_id": 123,
                "ad_group_id": None
            }
        )