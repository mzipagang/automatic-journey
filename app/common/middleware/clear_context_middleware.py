from urllib.request import Request

from starlette.middleware.base import BaseHTTPMiddleware

from app.common.utils.context_tools import clear_all_context_vars


class ClearContextVarsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        res = await call_next(request)
        clear_all_context_vars()
        return res
