from fastapi import APIRouter, Depends, Query, Request, status
from fastapi_versioning import version

from app.common.decorators.requires_all_roles import requires_all_roles
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.harness_service import HarnessService
from app.common.view_models import CampaignPutRequest, ListResponse, SingleResponse, AuthRole
from app.common.decorators.backoff_wait_rate_limited import backoff_wait_rate_limited
from app.common.decorators.cid_rate_limited import cid_rate_limited
from app.common.decorators.harness_locked import locked
from app.common.model.campaign_types import CampaignType, convert_enum, InternalCampaignType
from app.common.services.advertiser_service import AdvertiserService
from app.common.utils import filtered_logger
from app.common.utils.exceptions import CustomHTTPExceptionRoute
from app.common.utils.http_request import CONSUMER_HEADER_NAME, get_consumer_source
from app.common.utils.jwt import validate_advertiser, validate_user
from app.v2.services import CampaignService
from app.v2.view_models import Campaign, CampaignRequest

logger = filtered_logger.get_logger(__name__)

router = APIRouter(
    route_class=CustomHTTPExceptionRoute,
    tags=["Campaign Endpoints"]
)

@version(2)
@router.post(
    path="/campaigns",
    name="Create a Campaign",
    description="Creates a PLA or Carousel campaign in the Media Platform. A campaign is an organized strategy used to "
                "achieve specific, actionable goals like: providing information to customers, building brand "
                "awareness, promoting a new product, or convincing customers to make a purchase. Read more "
                "about [Campaigns](https://mp-help.8451.com/mp-help/content/how-to/create-campaign.htm) in our"
                "Media Platform Learning Center.",
    response_model=SingleResponse[Campaign],
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Sample success response",
            "model": SingleResponse[Campaign]
        },
        400: {
            "description": "Sample 400 error response (startDate not set in request)",
            "content": {
                "application/json": {
                    "example": {
                        "errors": [
                            {
                                "reason": ".startDate: field required",
                                "datetime": {
                                    "value": "2025-01-09T21:17:39.886585+00:00",
                                    "timezone": "UTC"
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def create_campaign(
            request: Request, campaign_request: CampaignRequest,
            current_user: dict = Depends(validate_user),
            campaign_service: CampaignService = Depends(CampaignService)) -> SingleResponse[Campaign]:
    logger.info('Creating campaign')

    source = get_consumer_source(request.headers.get(CONSUMER_HEADER_NAME))
    return await campaign_service.create_campaign(campaign_request, current_user, source)

@version(2)
@router.get(
    path="/campaigns",
    name="Get Campaign",
    description=(
        "Retrieve a list of campaigns from the Media Platform. Read more about "
        "[Campaigns](https://mp-help.8451.com/mp-help/content/how-to/create-campaign.htm) "
        "in our Media Platform Learning Center."
    ),
    response_model=ListResponse[Campaign],
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_campaigns_by_advertiser(
    current_user: dict = Depends(validate_user),
    advertiser_id: int = Query(
        default=None,
        description="The advertiser ID to get campaigns for"
    ),
    campaign_type: CampaignType = Query(
        default=CampaignType.PLA,
        description="Type for this campaign"
    ),
    offset: int = Query(
        default=0,
        description="The offset of the page to return"
    ),
    size: int = Query(
        default=10,
        description="The number of results per page"
    ),
    campaign_service: CampaignService = Depends(CampaignService),
    advertiser_service: AdvertiserService = Depends(AdvertiserService),
) -> ListResponse[Campaign]:
    logger.info('Getting campaigns')

    await validate_advertiser(current_user, advertiser_id, advertiser_service)

    advertiser = await advertiser_service.get_advertiser_by_numeric_id(advertiser_id)
    return await campaign_service.get_campaigns_paginated_by_external_advertiser(
        advertiser,
        convert_enum(campaign_type, InternalCampaignType),
        offset,
        size,
    )

@version(2)
@router.get(
    path="/campaigns/{campaign_id}",
    name="Get Campaign by ID",
    description=(
        "Get a campaign from the Media Platform by ID. Read more about "
        "[Campaigns](https://mp-help.8451.com/mp-help/content/how-to/create-campaign.htm) "
        "in our Media Platform Learning Center."
    ),
    response_model=SingleResponse[Campaign],
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger,
)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_campaign_by_id(
    campaign_id: int,
    include_ad_groups: bool = Query(
        default=False,
        alias="include.adgroups",
        description=(
            "If true, returns the ad groups associated with this campaign as an array."
        ),
    ),
    include_ad_group_errors: bool = Query(default=False, description="Include Ad Group errors in the response"),
    campaign_service: CampaignService = Depends(CampaignService),
    harness_service: HarnessService = Depends(HarnessService)
) -> SingleResponse[Campaign]:
    logger.info('Getting campaign by ID: %s', campaign_id)
    include_errors_enabled = harness_service.is_harness_flag_on(
        HarnessFeatureFlags.INCLUDE_AD_GROUP_ERRORS,
        "default"
    )
    include_errors = include_errors_enabled and include_ad_group_errors

    return await campaign_service.get_campaign_single_response_by_id(
        campaign_id=campaign_id,
        include_ad_groups=include_ad_groups,
        include_ad_group_errors=include_errors
    )

@version(2)
@router.put(
    path="/campaigns/{campaign_id}",
    name="Update Campaign",
    description=(
        "Update a campaign in the Media Platform. Read more about "
        "[Campaigns](https://mp-help.8451.com/mp-help/content/how-to/create-campaign.htm) "
        "in our Media Platform Learning Center."
    ),
    response_model=SingleResponse[Campaign],
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@locked(
    lock_config_name=HarnessFeatureFlags.UPDATE_CAMPAIGN_LOCK_CONFIG,
    entity_id_name="campaign_id",
    logger=logger
)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def update_campaign(
        request: Request,
        campaign_id: int,
        campaign_request: CampaignPutRequest,
        current_user: dict = Depends(validate_user),
        campaign_service: CampaignService = Depends(CampaignService)
) -> SingleResponse[Campaign]:
    logger.info('Updating campaign')

    source = get_consumer_source(request.headers.get(CONSUMER_HEADER_NAME))
    return await campaign_service.update_campaign(campaign_id, campaign_request, current_user, source)
