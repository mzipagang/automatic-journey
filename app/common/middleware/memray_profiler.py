import uuid
import memray
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


#https://kroger.atlassian.net/wiki/spaces/8451KPMME/pages/386499282/Discovery+UCM-15645+Collect+memray+profiling+data+for+endpoints+with+high+memory+usage
#https://github.com/8451LLC/map-onsite-apis/pull/847
class MemrayMiddleware(BaseHTTPMiddleware):
    """
    Middleware to profile each request using Memray and save the profile to a unique file.
    Note: This middleware is kept for reference and is not actively used in the application. Can be used in future if needed.
    """
    async def dispatch(self, request: Request, call_next):
        # Generate unique filename per request
        profile_id = str(uuid.uuid4())
        filename = f"memray_report_{profile_id}.bin"

        # Start Memray profiling
        with memray.Tracker(filename, native_traces=True, trace_python_allocators=True):
            response = await call_next(request)

        # You can also attach profile file path in headers for debugging
        response.headers["X-Memray-Profile"] = filename
        return response
