from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.common.context.context import user_context, security_context, client_context, logging_extra_context
from app.common.context.context_vars import UserContextVarNames, SecurityContextVarNames
from app.common.utils.context_tools import update_context
from app.common.utils.filtered_logger import get_logger
from app.common.utils.jwt import parse_token_for_username
from app.common.utils.token_tools import parse_token_for_client_id, get_auth_header

logger = get_logger(__name__)


class UserInfoMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        __ignore_endpoints = ["/api/health/liveness", "/api/health/readiness", "/metrics"]

        if request.url.path in __ignore_endpoints:
            response = await call_next(request)
            return response
        username = 'Unset2-no-auth-header'
        if auth_header := get_auth_header(request):
            try:
                auth_header_parts = auth_header.split(" ")
                if len(auth_header_parts) == 2:
                    username = parse_token_for_username(auth_header_parts[1])
                    client_id = parse_token_for_client_id(auth_header_parts[1])
                    security_context.set({
                        SecurityContextVarNames.USERNAME.value: username,
                        SecurityContextVarNames.ID_TOKEN.value: auth_header_parts[1]
                    })
                    client_context.set({"client_id": client_id})
                    update_context(logging_extra_context, client_id=client_id)
                else:
                    username = "Unset2-no-token-found"
            except AttributeError as err:
                logger.error("Failed to parse token: %s", err)
        else:
            logger.warning("Authorization header not found in request",
                           extra={
                               "monitored_transaction": "NO-AUTH-HEADER-NON-HEALTH-REQUEST",
                               "request_path": request.url.path})
        user_context.set({UserContextVarNames.USERNAME.value: username})
        response = await call_next(request)
        return response
