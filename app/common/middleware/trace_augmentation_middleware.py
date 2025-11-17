from ddtrace import tracer
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.utils.token_tools import parse_token_for_client_id


class TraceAugmentationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        if auth_header := request.headers.get("Authorization"):
            auth_header_parts = auth_header.split(" ")
            if len(auth_header_parts) == 2:
                client_id = parse_token_for_client_id(auth_header_parts[1])
                with tracer.trace("web.request") as span:
                    span.set_tag("http.client_id", client_id)
        return await call_next(request)
