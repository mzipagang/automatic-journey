from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.common.context.context import request_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:

        ordered_params = dict(sorted(request.query_params.items()))

        request_context.set({
            'path': request.url.path,
            'params': ordered_params
        })
        return await call_next(request)
