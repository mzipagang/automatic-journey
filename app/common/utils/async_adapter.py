from typing import TypeVar

from httpx import Response

from app.common.services.async_http_client_service import AsyncHttpClientService, AsyncKoddiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.services.http_client_service import HttpClientService, KoddiHttpClientService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

T = TypeVar("T", bound=HttpClientService | KoddiHttpClientService)
U = TypeVar("U", bound=AsyncHttpClientService | AsyncKoddiHttpClientService)

class AsyncAdapter:
    def __init__(
            self,
            sync_client: T,
            async_client: U,
            harness_flag_name: str,
            harness_service: HarnessService,
            harness_target_id: str = "default"
    ):
        self.__sync_client = sync_client
        self.__async_client = async_client
        self.__harness_flag_name = harness_flag_name
        self.__harness_target_id = harness_target_id
        self.__harness_service = harness_service

    async def __async_toggle(
            self,
            sync_fn,
            async_fn,
            args,
            kwargs
    ):
        enabled = self.__harness_service.is_harness_flag_on(
            self.__harness_flag_name,
            self.__harness_target_id
        )

        if enabled:
            return await async_fn(*args, **kwargs)

        return sync_fn(*args, **kwargs)

    async def get(self, *args, **kwargs) -> Response:
        return await self.__async_toggle(
            self.__sync_client.get,
            self.__async_client.get,
            args,
            kwargs
        )

    async def post(self, *args, **kwargs) -> Response:
        return await self.__async_toggle(
            self.__sync_client.post,
            self.__async_client.post,
            args,
            kwargs
        )

    async def put(self, *args, **kwargs) -> Response:
        return await self.__async_toggle(
            self.__sync_client.put,
            self.__async_client.put,
            args,
            kwargs
        )

    async def patch(self, *args, **kwargs) -> Response:
        return await self.__async_toggle(
            self.__sync_client.patch,
            self.__async_client.patch,
            args,
            kwargs
        )