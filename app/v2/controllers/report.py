from typing_extensions import Annotated
from fastapi import APIRouter, Depends, status, Path
from fastapi_versioning import version

from app.common.controllers.report import get_report
from app.common.decorators.backoff_wait_rate_limited import backoff_wait_rate_limited
from app.common.decorators.cid_rate_limited import cid_rate_limited
from app.common.decorators.requires_all_roles import requires_all_roles
from app.common.model.campaign_types import CampaignType, convert_enum, InternalCampaignType
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.advertiser_service import AdvertiserService
from app.common.services.report_service import ReportService
from app.common.utils import filtered_logger
from app.common.utils.exceptions import CustomHTTPExceptionRoute
from app.common.utils.jwt import validate_user
from app.common.view_models import AuthRole
from app.common.view_models.report import (
    ReportResultResponse,
)
from app.v2.view_models.report import ReportRequestV2

logger = filtered_logger.get_logger(__name__)

router = APIRouter(
    route_class=CustomHTTPExceptionRoute,
    tags=["Reporting Endpoints"]
)

@version(2)
@router.post(
    path="/report/{experience_name}",
    name="Submit Reporting",
    description=(
        "Submit a report for Product Listing Ads. Read more about [Reports]"
        "(https://mp-help.8451.com/mp-help/content/how-to/build-reports.htm) "
        "in our Media Platform Learning Center."
    ),
    status_code=status.HTTP_200_OK,
    response_model=ReportResultResponse,
    response_model_exclude_none=True
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
async def submit_report_v2(
        report_request: ReportRequestV2,
        experience_name: Annotated[
            CampaignType,
            Path(description="Case insensitive. Possible values are 'pla', 'toa' and 'carousel'")
        ],
        current_user=Depends(validate_user),
        report_service: ReportService = Depends(ReportService),
        advertiser_service: AdvertiserService = Depends(AdvertiserService)
) -> ReportResultResponse:
    """
    Report v2 with experience name in path parameter
    """
    return await get_report(
        report_request=report_request,
        experience_name=convert_enum(experience_name, InternalCampaignType),
        current_user=current_user,
        report_service=report_service,
        advertiser_service=advertiser_service
    )



