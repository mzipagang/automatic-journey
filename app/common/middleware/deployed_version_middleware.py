import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.common.utils.filtered_logger import get_logger

logger = get_logger(__name__)

class DeployedVersionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        try:
            otel_attr = os.getenv("OTEL_RESOURCE_ATTRIBUTES", '')
            attrs = dict(item.split("=", 1) for item in otel_attr.split(",") if "=" in item)
            self.DEPLOYED_VERSION = attrs.get("service.version", 'unknown')
        except Exception:
            logger.error("Failed to get deployed version from OTEL_RESOURCE_ATTRIBUTES")

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Deployed-Version"] = self.DEPLOYED_VERSION
        return response

