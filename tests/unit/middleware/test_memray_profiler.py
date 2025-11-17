import sys
import types
import unittest
import asyncio
from unittest.mock import patch
from starlette.requests import Request
from starlette.responses import Response

# Provide a dummy memray module so the middleware can be imported without the real dependency
if 'memray' not in sys.modules:
    dummy = types.ModuleType('memray')
    class DummyTracker:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
    dummy.Tracker = DummyTracker
    sys.modules['memray'] = dummy

from app.common.middleware.memray_profiler import MemrayMiddleware


class TestMemrayMiddleware(unittest.TestCase):
    def test_dispatch_sets_header_and_calls_tracker(self):
        async def app(scope, receive, send):
            pass

        middleware = MemrayMiddleware(app)

        async def call_next(request):
            return Response("OK", media_type="text/plain")

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 123),
        }
        request = Request(scope)

        with patch('app.common.middleware.memray_profiler.memray.Tracker') as tracker_cls, \
             patch('app.common.middleware.memray_profiler.uuid.uuid4', return_value='abc123'):
            tracker_obj = tracker_cls.return_value
            tracker_obj.__enter__.return_value = tracker_obj
            tracker_obj.__exit__.return_value = False

            response = asyncio.run(middleware.dispatch(request, call_next))

        expected_filename = "memray_report_abc123.bin"
        self.assertEqual(response.headers.get("X-Memray-Profile"), expected_filename)
        tracker_cls.assert_called_once_with(expected_filename, native_traces=True, trace_python_allocators=True)