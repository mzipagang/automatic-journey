from fastapi import APIRouter, Depends, Query, status
from fastapi_versioning import version

from app.common.decorators.requires_all_roles import requires_all_roles
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.harness_service import HarnessService
from app.common.view_models import (
    SingleResponse,
    ListResponse,
    KeywordsResponse,
    EntitiesRequest,
    KeywordBidModifiersRequest,
    AuthRole,
)
from app.common.decorators.backoff_wait_rate_limited import backoff_wait_rate_limited
from app.common.decorators.cid_rate_limited import cid_rate_limited
from app.common.decorators.harness_locked import locked
from app.v2.services.ad_group_service import AdGroupService
from app.common.services.config_service import ConfigService
from app.common.utils import filtered_logger
from app.common.utils.exceptions import CustomHTTPExceptionRoute
from app.common.utils.jwt import validate_user
from app.v2.view_models import AdGroupUpdateRequest, AdGroupV2, AdGroupV2Request, AdGroupUpdateRequestV2

logger = filtered_logger.get_logger(__name__)

router = APIRouter(
    route_class=CustomHTTPExceptionRoute,
    tags=["Ad Groups Endpoints"]
)

current_config = ConfigService().get_current_config()

### POST /media-mgmt-activation/api/v1 - Create an Ad Group

@version(2)
@router.post(
    path="/ad_groups",
    name="Create Ad Group",
    description="Create an Ad Group that are groups of UPCs that share a similar target. Read more about "
                "[Ad groups](https://mp-help.8451.com/mp-help/content/about/ad-groups.htm) in our Media Platform "
                "Learning Center.",
    status_code=status.HTTP_200_OK,
    response_model=SingleResponse[AdGroupV2],
    response_model_exclude_unset=True
)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def create_ad_group(
        ad_group_request: AdGroupV2Request,
        ad_group_service: AdGroupService = Depends(AdGroupService)
) -> SingleResponse[AdGroupV2]:
    return await ad_group_service.create_ad_group(ad_group_request)

### GET /media-mgmt-activation/api/v1 - Retrieve an Ad Group

@version(2)
@router.get(
    path="/ad_groups",
    name="Get Ad Group",
    description=(
        "Retrieve a list of Ad Groups. Read more about [Ad groups]("
        "https://mp-help.8451.com/mp-help/content/about/ad-groups.htm) in our "
        "Media Platform Learning Center."
    ),
    status_code=status.HTTP_200_OK,
    response_model=ListResponse[AdGroupV2],
    response_model_exclude_unset=True
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_ad_groups_by_campaign(
        campaign_id: int = Query(default=None, description="The campaign ID to get Ad Group for"),
        include_ad_group_errors: bool = Query(default=False, description="Include Ad Group errors in the response"),
        ad_group_service: AdGroupService = Depends(AdGroupService),
        harness_service: HarnessService = Depends(HarnessService)
) -> ListResponse[AdGroupV2]:
    include_errors_enabled = harness_service.is_harness_flag_on(
        HarnessFeatureFlags.INCLUDE_AD_GROUP_ERRORS,
        "default"
    )
    include_errors = include_errors_enabled and include_ad_group_errors
    return await ad_group_service.get_ad_groups_by_campaign_id(
        campaign_id,
        include_ad_group_errors=include_errors
    )

### GET /media-mgmt-activation/api/v1 - Get an ad group by ID.

@version(2)
@router.get(
    path="/ad_groups/{ad_group_id}",
    name="Get Ad Group by ID",
    description=(
        "Retrieve an Ad Group from the Media Platform by ID. Read more about [Ad groups]("
        "https://mp-help.8451.com/mp-help/content/about/ad-groups.htm) in our Media "
        "Platform Learning Center."
    ),
    status_code=status.HTTP_200_OK,
    response_model=SingleResponse[AdGroupV2],
    response_model_exclude_unset=True
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_ad_group_by_id(
        ad_group_id: int,
        ad_group_service: AdGroupService = Depends(AdGroupService)
) -> SingleResponse[AdGroupV2]:
    ad_group_response = await ad_group_service.get_ad_group_by_id(ad_group_id)
    return ad_group_response

### PUT /media-mgmt-activation/api/v1 - Update a campaign.

@version(2)
@router.put(
    path="/ad_groups/{ad_group_id}",
    name="Update Ad Group",
    description=(
        "Update an Ad Group in the Media Platform. Read more about [Ad groups]"
        "(https://mp-help.8451.com/mp-help/content/about/ad-groups.htm) in our Media Platform Learning Center."
    ),
    dependencies=[Depends(validate_user)],
    status_code=status.HTTP_200_OK,
    response_model=SingleResponse[AdGroupV2],
    response_model_exclude_unset=True
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@locked(
    lock_config_name=HarnessFeatureFlags.UPDATE_ACTIVATION_LOCK_CONFIG,
    entity_id_name="ad_group_id",
    logger=logger)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def update_ad_group(
        ad_group_id: int,
        adgroup_request: AdGroupUpdateRequestV2,
        _: dict = Depends(validate_user),
        ad_group_service: AdGroupService = Depends(AdGroupService)
) -> SingleResponse[AdGroupV2]:
    return await ad_group_service.update_ad_group(
        ad_group_id,
        adgroup_request,
    )

@version(2)
@router.patch(
    path="/ad_groups/{ad_group_id}/entities",
    name="Update Ad Group entities",
    description=(
        "Update an Ad Group entities in the Media Platform. Read more about [Ad groups]"
        "(https://mp-help.8451.com/mp-help/content/about/ad-groups.htm) in our Media Platform Learning Center."
    ),
    dependencies=[Depends(validate_user)],
    status_code=status.HTTP_200_OK,
    response_model=SingleResponse[AdGroupV2],
    response_model_exclude_unset=True
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@locked(
    lock_config_name=HarnessFeatureFlags.UPDATE_ACTIVATION_LOCK_CONFIG,
    entity_id_name="ad_group_id",
    logger=logger)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def update_ad_group_entities(
        ad_group_id: int,
        entities_request: EntitiesRequest,
        ad_group_service: AdGroupService = Depends(AdGroupService)
) -> SingleResponse[AdGroupV2]:
    return await ad_group_service.update_entities(ad_group_id, entities_request)


@version(2)
@router.patch(
    path="/ad_groups/{ad_group_id}/keywords",
    name="Update Ad Group keyword bid modifiers",
    description=(
        "Update Ad Group keyword bid modifiers in the Media Platform. Read more about "
        "[Keyword Bid Modifier] "
        "(https://mp-help.8451.com/mp-help/content/how-to/create-pla.htm?Highlight=keyword%20bid#EnterAdGroupDetails) "
        "in our Media Platform Learning Center."
    ),
    dependencies=[Depends(validate_user)],
    status_code=status.HTTP_200_OK,
    response_model=SingleResponse[AdGroupV2],
    response_model_exclude_unset=True,
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@locked(
    lock_config_name=HarnessFeatureFlags.UPDATE_ACTIVATION_LOCK_CONFIG,
    entity_id_name="ad_group_id",
    logger=logger)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def update_ad_group_keyword_bid_modifiers(
        ad_group_id: int,
        keyword_bid_modifiers_request: KeywordBidModifiersRequest,
        ad_group_service: AdGroupService = Depends(AdGroupService)
) -> SingleResponse[AdGroupV2]:
    ad_group_response = await ad_group_service.update_ad_group_keyword_bid_modifiers(
        ad_group_id,
        keyword_bid_modifiers_request
    )

    return ad_group_response

@version(2)
@router.get(
    path="/ad_groups/{ad_group_id}/keywords",
    name="Get eligible Ad Group keywords",
    description=(
        "Get eligible adgroup keywords in the Media Platform. Read more about "
        "[Keyword Bid Modifier](https://mp-help.8451.com/mp-help/content/how-to/create-pla.htm?"
        "Highlight=keyword%20bid#EnterAdGroupDetails) in our Media Platform Learning Center."
    ),
    dependencies=[Depends(validate_user)],
    status_code=status.HTTP_200_OK,
    response_model=KeywordsResponse,
    response_model_exclude_unset=True,
)
@backoff_wait_rate_limited(
    config_name=HarnessFeatureFlags.BACKOFF_WAIT_RATE_LIMIT_CONFIG,
    rl_config_name=HarnessFeatureFlags.CID_RATE_LIMIT_CONFIG,
    rl_decorator=cid_rate_limited,
    logger=logger)
@requires_all_roles([AuthRole.ADVERTISER_API])
async def get_ad_group_eligible_keywords(
        ad_group_id: int,
        ad_group_service: AdGroupService = Depends(AdGroupService)
) -> KeywordsResponse:
    keywords_response = await ad_group_service.get_keywords_by_ad_group_id(ad_group_id)
    return keywords_response
