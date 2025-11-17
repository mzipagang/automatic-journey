from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi_versioning import version

from app.common.decorators.decorators import disable_if_flag_on
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.v2.model.user import User
from app.common.utils.jwt import oauth2_scheme, get_user
from app.common.utils.exceptions import CustomHTTPExceptionRoute

router = APIRouter(
    route_class=CustomHTTPExceptionRoute,
    tags=["Debug Auth"],
)


@version(2)
@router.get(path="/jwt",
            name="JWT Endpoint",
            description="This endpoint will return your JWT.",
            status_code=status.HTTP_200_OK
            )
@disable_if_flag_on(
    HarnessFeatureFlags.DISABLE_V1,
    message="endpoint deprecated, please use v2/jwt instead",
)
async def read_token(request: Request, token: str = Depends(oauth2_scheme)):
    return {"access_token": token}


@version(2)
@router.get(path="/jwt/claims",
            name="JWT Claim Reading Endpoint",
            description="This endpoint will show what claims your JWT has.",
            status_code=status.HTTP_200_OK
            )
@disable_if_flag_on(
    HarnessFeatureFlags.DISABLE_V1,
    message="endpoint deprecated, please use v2/jwt/claims instead"
)
async def read_claims(request: Request, current_user: User = Depends(get_user)):
    return current_user
