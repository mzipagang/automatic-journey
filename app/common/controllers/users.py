from fastapi import APIRouter, Depends, status, Request
from fastapi_versioning import version

from app.common.decorators.decorators import disable_if_flag_on
from app.common.model.downstream.ent_client_service import ApiUserResponse
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.v2.model.user import User
from app.common.utils.jwt import validate_user, get_user
from app.common.utils.exceptions import CustomHTTPExceptionRoute

from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

router = APIRouter(
    route_class=CustomHTTPExceptionRoute,
    tags=["Current User Endpoints"]
)

@version(2)
@router.get(path="/users/me",
            name="Current user information",
            dependencies=[Depends(validate_user)],
            status_code=status.HTTP_200_OK
            )
@disable_if_flag_on(
    HarnessFeatureFlags.DISABLE_V1,
    message="endpoint deprecated, please use v2/me instead"
)
async def get_users_me(
        request: Request,
        current_user: ApiUserResponse=Depends(get_user)
) -> User:
    logger.info("Getting current user information")
    user = User(**current_user.data.model_dump())
    user.organization = current_user.data.worksFor.name
    return user
