from functools import wraps
from typing import List, Set

from fastapi import HTTPException

from app.common.context.context import logging_extra_context
from app.common.gateways.ent_client_service_gateway import EntClientServiceGateway
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.async_http_connection_service import AsyncHttpConnectionService
from app.common.services.config_service import ConfigService
from app.common.services.harness_service import HarnessService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.services.http_connection_service import HttpConnectionService
from app.common.utils.context_tools import update_context
from app.common.view_models import AuthRole


def requires_all_roles(roles: List[AuthRole]):
    config_service: ConfigService = ConfigService()
    harness_service: HarnessService = HarnessService()
    async_http_client: AsyncExternalApiHttpClientService = AsyncExternalApiHttpClientService(
        config_service=config_service,
        http_connection_service=AsyncHttpConnectionService()
    )
    http_client: ExternalApiHttpClientService = ExternalApiHttpClientService(
        config_service=config_service,
        http_connection_service=HttpConnectionService()
    )
    ent_service: EntClientServiceGateway = EntClientServiceGateway(
        async_external_api_http_client=async_http_client,
        external_api_http_client_service=http_client,
        config_service=config_service,
        harness_service=harness_service
    )

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_roles: Set[AuthRole] = set(await ent_service.get_user_roles())
            required_roles: Set[AuthRole] = set(roles)

            matching_roles: Set[AuthRole] = user_roles & required_roles

            if len(matching_roles) != len(required_roles):
                update_context(logging_extra_context, usr_roles=matching_roles, required_roles=roles)
                raise HTTPException(status_code=403, detail="Missing authorization roles to perform this operation. Please contact support.")

            return await func(*args, **kwargs)
        return wrapper
    return decorator