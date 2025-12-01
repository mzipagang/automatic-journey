from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import json
class AdGroupDiscriminatorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/v2/ad_groups" and request.method == "POST":
            body = await request.body()
            data = json.loads(body)
            if "baseBid" in data or "entities" in data:
                data["requestType"] = "legacy"
            else:
                data["requestType"] = "updated"
            request._body = json.dumps(data).encode()
        response = await call_next(request)
        return response
