import logging
from copy import deepcopy
from json import JSONDecodeError
from typing import Callable, List

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from httpx import AsyncClient
from httpx import Response
from httpx import codes as httpx_codes

from app.common.configuration.constants import KODDI_SSO_SERVICE_JWT_PATH
from app.common.context.context import security_context
from app.common.context.context_vars import SecurityContextVarNames
from app.common.decorators.decorators import conditionally_retry
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.retry.predicates import koddi_token_fetch_failed_503
from app.common.services.config_service import ConfigService
from app.common.services.async_http_connection_service import AsyncHttpConnectionService
from app.common.services.http_client_service import _process_koddi_token_response
from app.common.utils import filtered_logger

oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="auth", tokenUrl="token")

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = filtered_logger.get_logger(__name__)

class AsyncHttpClientService:
    http_get: Callable
    http_post: Callable
    http_put: Callable
    http_patch: Callable
    __httpx_client: AsyncClient = None
    __base_url: str = None
    __base_parameters: dict = {
        'timeout': None
    }

    def __init__(
            self,
            headers: dict,
            base_url: str,
            httpx_client: AsyncClient):
        self.__base_url = base_url
        self.__base_parameters['headers'] = headers
        self.__httpx_client = httpx_client

        self.http_get = _VerbFunctors.get(self.__base_url, self.__httpx_client, self.__base_parameters)
        self.http_post = _VerbFunctors.post(self.__base_url, self.__httpx_client, self.__base_parameters)
        self.http_put = _VerbFunctors.put(self.__base_url, self.__httpx_client, self.__base_parameters)
        self.http_patch = _VerbFunctors.patch(self.__base_url, self.__httpx_client, self.__base_parameters)

    async def get(
            self,
            path: str,
            params: dict = None,
            response_body_type: str = None,
            json_has_data_field: bool = False,
            forward_client_error_response_content: bool = False):

        token = security_context.get().get(SecurityContextVarNames.ID_TOKEN.value)
        return await self.http_get(
            path=path,
            token=token,
            params=params,
            response_body_type=response_body_type,
            json_has_data_field=json_has_data_field,
            forward_client_error_response_content=forward_client_error_response_content)

    async def post(
            self,
            path: str,
            json: dict,
            params: dict = None,
            response_body_type: str = None,
            json_has_data_field: bool = False,
            forward_client_error_response_content: bool = False):

        token = security_context.get().get(SecurityContextVarNames.ID_TOKEN.value)
        return await self.http_post(
            path=path,
            params=params,
            token=token,
            json=json,
            response_body_type=response_body_type,
            json_has_data_field=json_has_data_field,
            forward_client_error_response_content=forward_client_error_response_content)

    async def patch(
            self,
            path: str,
            json: dict = None,
            response_body_type: str = None,
            json_has_data_field: bool = False,
            forward_client_error_response_content: bool = False):

        token = security_context.get().get(SecurityContextVarNames.ID_TOKEN.value)
        return await self.http_patch(
            path=path,
            token=token,
            json=json,
            response_body_type=response_body_type,
            json_has_data_field=json_has_data_field,
            forward_client_error_response_content=forward_client_error_response_content)

    async def put(
            self,
            path: str,
            json: dict,
            response_body_type: str = None,
            json_has_data_field: bool = False,
            forward_client_error_response_content: bool = False):

        token = security_context.get().get(SecurityContextVarNames.ID_TOKEN.value)
        return await self.http_put(
            path=path,
            token=token,
            json=json,
            response_body_type=response_body_type,
            json_has_data_field=json_has_data_field,
            forward_client_error_response_content=forward_client_error_response_content)


    async def close(self):
        await self.__httpx_client.aclose()

class AsyncInternalApiHttpClientService(AsyncHttpClientService):
    def __init__(self, config_service: ConfigService = Depends(ConfigService),
                 http_connection_service: AsyncHttpConnectionService = Depends(AsyncHttpConnectionService)):
        super().__init__(
            headers={
                'accept': 'application/json',
                'cache-control': 'no-cache',
                'content-type': 'application/json'},
            base_url=config_service.get_current_config().base_internal_api_url,
            httpx_client=http_connection_service.get_http_client())

class AsyncExternalApiHttpClientService(AsyncHttpClientService):
    def __init__(self, config_service: ConfigService = Depends(ConfigService),
                 http_connection_service: AsyncHttpConnectionService = Depends(AsyncHttpConnectionService)):
        super().__init__(
            headers={
                'accept': 'application/json',
                'cache-control': 'no-cache',
                'content-type': 'application/json'},
            base_url=config_service.get_current_config().base_api_url,
            httpx_client=http_connection_service.get_http_client())




class AsyncKoddiHttpClientService:
    http_post: Callable
    __httpx_client: AsyncClient = None
    __baseParameters: dict = {
        'timeout': None,
        'headers': {}
    }
    __external_api_http_client: AsyncExternalApiHttpClientService

    def __init__(
        self,
        config_service: ConfigService = Depends(ConfigService),
        http_connection_service: AsyncHttpConnectionService = Depends(AsyncHttpConnectionService),
        external_api_http_client_service: AsyncExternalApiHttpClientService = Depends(AsyncExternalApiHttpClientService)
    ):
        self.__external_api_http_client = external_api_http_client_service
        self.__httpx_client = http_connection_service.get_http_client()

        koddi_base_url = config_service.get_current_config().base_koddi_url

        self.http_post = _VerbFunctors.post(koddi_base_url, self.__httpx_client, self.__baseParameters)

    async def post(
            self,
            path: str,
            json: dict,
            response_body_type: str = None,
            json_has_data_field: bool = False,
            forward_client_error_response_content: bool = False):

        token = await self.__get_koddi_token()
        return await self.http_post(
            token=token,
            path=path,
            json=json,
            response_body_type=response_body_type,
            json_has_data_field=json_has_data_field,
            forward_client_error_response_content=forward_client_error_response_content)

    @conditionally_retry(
        flag_name=HarnessFeatureFlags.KODDI_TOKEN_FETCH_RETRY,
        logger=logger,
        retry_predicate=koddi_token_fetch_failed_503
    )
    async def __get_koddi_token(self):
        logger.info("Requesting Koddi token")
        response = await self.__external_api_http_client.get(path=KODDI_SSO_SERVICE_JWT_PATH)
        return _process_koddi_token_response(response)

    async def close(self):
        await self.__httpx_client.aclose()

class _VerbFunctors:
    @staticmethod
    def get(base_url: str, httpx_client: AsyncClient, base_params: dict):
        async def __internal(path: str,
                       token: str,
                       params: dict = None,
                       response_body_type=None,
                       json_has_data_field=False,
                       forward_client_error_response_content=False):

            get_base_params = _VerbFunctors.__safely_inject_auth_param(token, base_params)

            response = await httpx_client.get(f"{base_url}{path}", params=params, **get_base_params)

            return _VerbFunctors.__handle_response(
                response,
                response_body_type,
                json_has_data_field,
                forward_client_error_response_content)

        return __internal

    @staticmethod
    def post(base_url: str, httpx_client: AsyncClient, base_params: dict):
        async def __internal(
                token: str,
                path: str,
                       params: dict = None,
                       json: dict = None,
                       response_body_type=None,
                       json_has_data_field=False,
                       forward_client_error_response_content=False):

            post_base_params = _VerbFunctors.__safely_inject_auth_param(token, base_params)

            response = await httpx_client.post(
                url=f"{base_url}{path}", params=params, json=json, **post_base_params)


            return _VerbFunctors.__handle_response(
                response,
                response_body_type,
                json_has_data_field,
                forward_client_error_response_content)

        return __internal

    @staticmethod
    def put(base_url: str, httpx_client: AsyncClient, base_params: dict):
        async def __internal(path: str,
                       token: str,
                       json: dict = None,
                       response_body_type=None,
                       json_has_data_field=False,
                       forward_client_error_response_content=False):

            put_base_params = _VerbFunctors.__safely_inject_auth_param(token, base_params)

            response = await httpx_client.put(f"{base_url}{path}", json=json, **put_base_params)

            return _VerbFunctors.__handle_response(
                response,
                response_body_type,
                json_has_data_field,
                forward_client_error_response_content)

        return __internal

    @staticmethod
    def patch(base_url: str, httpx_client: AsyncClient, base_params: dict):
        async def __internal(path: str,
                       token: str,
                       json: dict | List[dict] = None,
                       response_body_type=None,
                       json_has_data_field=False,
                       forward_client_error_response_content=False):

            patch_base_params = _VerbFunctors.__safely_inject_auth_param(token, base_params)

            response = await httpx_client.patch(f"{base_url}{path}", json=json, **patch_base_params)

            return _VerbFunctors.__handle_response(
                response,
                response_body_type,
                json_has_data_field,
                forward_client_error_response_content)

        return __internal

    @staticmethod
    def __handle_response(response: Response,
                          response_body_type: str = None,
                          json_has_data_field: bool = False,
                          forward_client_error_response_content=False) -> Response | None:
        if response_body_type is None:
            return response
        if response_body_type == 'json':
            return _VerbFunctors.__process_json_response(
                response=response,
                json_has_data_field=json_has_data_field,
                forward_client_error_response_content=forward_client_error_response_content)

    @staticmethod
    def __process_json_response(response: Response,
                                json_has_data_field: bool = False,
                                forward_client_error_response_content=False) -> Response | None:
        if httpx_codes.is_success(response.status_code):
            try:
                json = response.json()
            except JSONDecodeError:
                json = None

            if json is not None and (not json_has_data_field or 'data' in json):
                return response

            _log_and_raise_on_upstream_error(
                response=response,
                info="Malformed response",
                path=response.url.path)

        elif httpx_codes.is_server_error(response.status_code):
            _log_and_raise_on_upstream_error(
                response=response,
                info="Error service response",
                path=response.url.path)

        elif httpx_codes.is_client_error(response.status_code):
            _log_and_raise_on_client_error(
                response=response,
                info="Error client response",
                path=response.url.path,
                forward_client_error_response_content=forward_client_error_response_content)

        else:
            logger.error(
                "Upstream service error from %s. Code: %s - Response: %s",
                response.url,
                response.status_code,
                response.content)
            raise HTTPException(status_code=500, detail="Unexpected error processing JSON response")

    @staticmethod
    def __safely_inject_auth_param(token: str, base_params: dict) -> dict:
        new_base_params = deepcopy(base_params)
        new_base_params['headers']['Authorization'] = f'Bearer {token}'

        return new_base_params

def _log_and_raise_on_upstream_error(response: Response, info: str, path: str):
    logger.error(
        "%s at %s",
        info,
        path,
        extra={
            'monitored_transaction': 'HTTP-UPSTREAM-ERROR--SERVICE-ERROR-RESPONSE',
            'response': response.content,
            'response_code': response.status_code
        }
    )
    raise HTTPException(
        status_code=503,
        detail="Temporary service error.  Please try again.",
        headers={"Retry-After": "5"})

def _log_and_raise_on_client_error(
        response: Response,
        info: str,
        path: str,
        forward_client_error_response_content=False):
    logger.warning(
        "%s at %s",
        info,
        path,
        extra={
            'monitored_transaction': 'HTTP-UPSTREAM-ERROR--CLIENT-ERROR-RESPONSE',
            'response': response.content,
            'response_code': response.status_code
        }
    )
    if forward_client_error_response_content:
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                detail_content = response.json()
            except JSONDecodeError:
                detail_content = response.text
        else:
            detail_content = response.text
        raise HTTPException(status_code=response.status_code, detail=detail_content)
    raise HTTPException(status_code=response.status_code)
