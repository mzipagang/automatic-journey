from e451_monitoring.fastapi import Observer
from fastapi import FastAPI

from app.common.middleware.clear_context_middleware import ClearContextVarsMiddleware
from app.common.middleware.deployed_version_middleware import DeployedVersionMiddleware
from app.common.middleware.request_context_middleware import RequestContextMiddleware
from app.common.middleware import TraceAugmentationMiddleware
from app.common.utils import filtered_logger
from app.common.middleware.user_info_middleware import UserInfoMiddleware

logger = filtered_logger.get_logger(__name__)


class AppAugmenter:

    @staticmethod
    def add_app_middleware(app: FastAPI):
        app.add_middleware(UserInfoMiddleware)
        app.add_middleware(RequestContextMiddleware)
        app.add_middleware(TraceAugmentationMiddleware)
        app.add_middleware(DeployedVersionMiddleware)

        # ClearContextVarsMiddleware must be last in the list of middlewares
        app.add_middleware(ClearContextVarsMiddleware)

    @staticmethod
    def monitoring_instrument_app(app: FastAPI, observer: Observer):
        custom_logger = filtered_logger.get_logger(__name__)
        observer.instrument_logging(app, logger=custom_logger)
        observer.instrument_tracing(app)
