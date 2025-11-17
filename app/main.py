from contextlib import asynccontextmanager

from e451_monitoring.fastapi import Observer
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_versioning import VersionedFastAPI
from prometheus_client import Counter

from app.common.controllers import metadata, jwt, users
from app.v2.controllers import(
    campaign as campaign_v2,
    ad_groups as ad_groups_v2,
    report as report_v2
)
from app.common.database.async_client import AsyncRedisClientService
from app.common.services.config_service import ConfigService
from app.common.services.harness_service import HarnessService
from app.common.services.http_connection_service import HttpConnectionService
from app.common.utils import filtered_logger
from app.common.utils.app_augmenter import AppAugmenter

observer = Observer().setup()
logger = filtered_logger.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI,
                   harness_service: HarnessService = HarnessService(),
                   http_connection_service: HttpConnectionService = HttpConnectionService(),
                   config_service: ConfigService = ConfigService(),
                   async_redis_client_service: AsyncRedisClientService = AsyncRedisClientService()):
    # This will be called when the application starts
    async_redis_client = await async_redis_client_service.async_engine()
    FastAPICache.init(backend=RedisBackend(async_redis_client), prefix="kap-api-fastapi-cache")
    yield
    # This will be called when the application stops
    http_connection_service.close()
    await async_redis_client.close()
    config_service.clear_config()
    harness_service.close()

app = FastAPI(title="Kroger Ad Platform API",
              description="Read more about KAP API in our Media Platform "
                          "[Learning Center](https://mp-help.8451.com/mp-help/content/about/apis.htm).",
              contact={
                  "name": "84.51",
                  "url": "https://www.8451.com",
                  "email": "UCM_Onsite_Partnerships_DL@8451.com",
              })

# Only include the jwt router if we are in the lower environments
current_config = ConfigService().get_current_config()
if current_config.env in ['local', 'dev', 'tst']:
    app.include_router(jwt.router)

# Include routers
app.include_router(metadata.router)
app.include_router(campaign_v2.router)
app.include_router(ad_groups_v2.router)
app.include_router(report_v2.router)
app.include_router(users.router)

app = VersionedFastAPI(app,
                       version_format='{major}',
                       prefix_format='/v{major}',
                       lifespan=lifespan)

AppAugmenter.monitoring_instrument_app(app, observer)
AppAugmenter.add_app_middleware(app)

# Example usage of a custom Counter
APP_VISITS = Counter(
    "app_visits",
    "Number of times the docs were visited",
    ["framework", "type"],
)


# Redirect the root route to the /docs
@app.get('/')
async def homepage():
    return RedirectResponse(url="/v1/docs")


@app.get('/v{version}')
@app.get('/api/v{version}')
async def api_doc(version: str):
    # Add to custom counter
    APP_VISITS.labels(framework="FastAPI", type="example").inc()
    return RedirectResponse(url=f"/v{version}/docs")


# API Health
@app.get("/api/health/liveness")
def get_liveness_status():
    return Response(status_code=status.HTTP_200_OK)


# API Health
@app.get("/api/health/readiness")
async def get_readiness_status(redis_cache=Depends(AsyncRedisClientService)):
    try:
        database_status = await redis_cache.ping()
        if database_status:
            return Response(status_code=status.HTTP_200_OK)
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exception:
        logger.exception(exception)
        raise HTTPException(status_code=503) from exception
