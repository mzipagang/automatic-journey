from pydantic.main import BaseModel

from app.common.model.request_monitor_parameters import PacingTypeRequestMonitorParameter, RequestMonitorParameter, \
    BudgetTypeRequestMonitorParameter, BudgetAmountRequestMonitorParameter
from app.common.utils.filtered_logger import get_logger

logger = get_logger(__name__)

class CampaignUpdateRequestMonitor:
    __CHANGE_MONITOR_PARAMETERS = [
        PacingTypeRequestMonitorParameter(), BudgetTypeRequestMonitorParameter(), BudgetAmountRequestMonitorParameter()]
    __FIELD_DELTA_MONITOR_PARAMETERS = []

    @staticmethod
    def monitor_request(
            request: BaseModel,
            existing_entity: BaseModel,
            account_id: int = None,
            campaign_id: int = None,
            ad_group_id: int = None):
        request_dict = request.dict()
        existing_entity_dict = existing_entity.dict()
        for monitor_parameter in CampaignUpdateRequestMonitor.__CHANGE_MONITOR_PARAMETERS:
            if CampaignUpdateRequestMonitor.__monitor_qualified(request_dict, monitor_parameter):
                if request_dict[monitor_parameter.field_name] != existing_entity_dict[monitor_parameter.field_name]:
                    CampaignUpdateRequestMonitor.__emit_monitored_change_request_log(
                        request=request_dict,
                        existing_entity=existing_entity_dict,
                        monitor_param=monitor_parameter,
                        account_id=account_id,
                        campaign_id=campaign_id,
                        ad_group_id=ad_group_id)

        for monitor_parameter in CampaignUpdateRequestMonitor.__FIELD_DELTA_MONITOR_PARAMETERS:
            if CampaignUpdateRequestMonitor.__monitor_qualified(request_dict, monitor_parameter):
                field_delta = abs(request_dict[monitor_parameter.field_name]
                                  - existing_entity_dict[monitor_parameter.field_name])
                if field_delta > monitor_parameter.field_delta_threshold:
                    CampaignUpdateRequestMonitor.__emit_monitored_change_request_log(
                        request=request_dict,
                        existing_entity=existing_entity_dict,
                        monitor_param=monitor_parameter,
                        account_id=account_id,
                        campaign_id=campaign_id,
                        ad_group_id=ad_group_id)

    @staticmethod
    def __monitor_qualified(request: dict, monitor_param: RequestMonitorParameter):
        return monitor_param.field_name in request
    @staticmethod
    def __emit_monitored_change_request_log(
            request: dict,
            existing_entity: dict,
            monitor_param: RequestMonitorParameter,
            account_id: int = None,
            campaign_id: int = None,
            ad_group_id: int = None):
        logger.info("MONITORED TRANSACTION CHANGE REQUESTED",
                    extra={
                        "field_name": monitor_param.field_name,
                        "field_type": monitor_param.field_type,
                        "monitored_transaction": monitor_param.monitored_transaction,
                        "existing_value": existing_entity[monitor_param.field_name],
                        "new_value": request[monitor_param.field_name],
                        "request": request,
                        "account_id": account_id,
                        "campaign_id": campaign_id,
                        "ad_group_id": ad_group_id
                    })
