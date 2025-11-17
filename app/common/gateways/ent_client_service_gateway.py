from typing import List, Set
from fastapi import Depends, HTTPException
from fastapi_cache.decorator import cache

from app.common.cache.coders import PydanticCoderFactory
from app.common.cache.key_builders import(
    account_address_and_contacts_key_builder,
    account_by_internal_id_key_builder,
    user_roles_key_builder,
    get_advertisers_upstream_key_builder,
    get_user__upstream_key_builder_c2,
    validate_user__upstream_key_builder,
    get_addresses_by_account__upstream_key_builder,
    get_contacts_by_id_upstream_key_builder
)
from app.common.decorators.decorators import conditional_cache
from app.common.model.account import InternalAccount
from app.common.model.address import AccountAddress, AccountAddressResponse
from app.common.model.downstream.ent_client_service import(
    BasicClientDetails,
    UserPermissions,
    EntClientServiceMeta,
    ProductAccess,
    ApiUserResponse,
    ApiAccessResponse,
    Contact
)
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.model.redis import CachedRedisAdvertiser
from app.common.model.shared import SingleDataResponse, ListDataResponse
from app.common.services.async_http_client_service import AsyncExternalApiHttpClientService
from app.common.services.harness_service import HarnessService
from app.common.utils.async_adapter import AsyncAdapter
from app.common.view_models import AuthRole
from app.common.services.config_service import ConfigService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)

class EntClientServiceGateway:
    __http_client: AsyncAdapter
    __product_id: str


    def __init__(
        self,
        async_external_api_http_client: AsyncExternalApiHttpClientService = Depends(AsyncExternalApiHttpClientService),
        external_api_http_client_service: ExternalApiHttpClientService = Depends(ExternalApiHttpClientService),
        harness_service: HarnessService = Depends(HarnessService),
        config_service: ConfigService = Depends(ConfigService),
    ):
        self.__http_client = AsyncAdapter(
            external_api_http_client_service,
            async_external_api_http_client,
            harness_flag_name=HarnessFeatureFlags.ASYNC_ENT_CLIENT,
            harness_service=harness_service
        )
        self.__product_id = config_service.get_current_config().product_id

    @cache(
        expire=20,
        namespace="user",
        key_builder=user_roles_key_builder
    )
    async def _get_user_info_http_request(self):
        path: str = f"/ent-client-service/users/v1/userInfo"
        # Make a GET request to fetch user info
        response = (await self.__http_client.get(
            path=path,
            params={"option.productId": self.__product_id},
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True
        )).json()

        return response

    async def get_user_roles(self) -> Set[AuthRole]:
        # Build the API path with the current product ID
        response = await self._get_user_info_http_request()

        user_info = SingleDataResponse[UserPermissions, EntClientServiceMeta](**response)

        permissions: List[ProductAccess] | None = user_info.data and user_info.data.permissions
        if not permissions:
            return set[AuthRole]()

        # Collect unique roles from all permissions
        roles_set = {
            AuthRole(role)
            for permission in permissions
            for role in permission.roles
        }

        # Return the list of unique AuthRole objects
        return roles_set

    @conditional_cache(
        key_builder=account_address_and_contacts_key_builder,
        coder=PydanticCoderFactory.build(ListDataResponse[BasicClientDetails, EntClientServiceMeta])
    )
    async def get_accounts_addresses_and_contacts(self) -> ListDataResponse[BasicClientDetails, EntClientServiceMeta]:
        path = f"/ent-client-service/clients/v1/product/{self.__product_id}/clients"
        params = {
            "option.details": "Full",
            "option.includeContacts": "true",
            "filter.duplicateAddresses": "true"
        }

        response = await self.__http_client.get(path=path, params=params, response_body_type="json")
        return ListDataResponse[BasicClientDetails, EntClientServiceMeta](**response.json())

    @conditional_cache(
        key_builder=get_addresses_by_account__upstream_key_builder,
        coder=PydanticCoderFactory.build(AccountAddressResponse)
    )
    async def get_addresses_by_account(self, account_id: str) -> AccountAddressResponse:
        path = f"/ent-client-service/clients/v1/product/{self.__product_id}/clients/{account_id}"
        params = {
            "option.details": "Full",
            "filter.duplicateAddresses": "true"
        }

        logger.debug("Accounts URL: %s", path)

        response = await self.__http_client.get(path=path, params=params, response_body_type="json",
                                                       json_has_data_field=True)
        addresses = response.json().get('data', {}).get('addresses', [])
        return AccountAddressResponse(
            data=[AccountAddress(**address) for address in addresses]
        )

    @conditional_cache(
        key_builder=account_by_internal_id_key_builder,
        coder=PydanticCoderFactory.build(InternalAccount)
    )
    async def get_account_by_internal_id_upstream(self, internal_account_id: str) -> InternalAccount:
        if internal_account_id is None:
            logger.error("Supplied Internal Account ID is None")
            raise HTTPException(status_code=404, detail="Account not found")

        path = f"/ent-client-service/clients/v1/product/{self.__product_id}/clients/{internal_account_id}"

        response = await self.__http_client.get(path=path, response_body_type="json", json_has_data_field=True)

        data = response.json()['data']
        return InternalAccount(
            id=internal_account_id,
            name=data['displayName'],
            active=True
        )

    @conditional_cache(
        key_builder=get_advertisers_upstream_key_builder,
        coder=PydanticCoderFactory.build(
            ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta]
        )
    )
    async def get_brands(
            self,
            account_id: str
    ) -> ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta]:
        path = f"/ent-client-service/clients/v1/product/{self.__product_id}/clients/{account_id}/brands"
        response = await self.__http_client.get(
            path=path,
            response_body_type="json",
            json_has_data_field=True
        )

        return ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta](**response.json())

    @conditional_cache(
        key_builder=get_user__upstream_key_builder_c2,
        coder=PydanticCoderFactory.build(ApiUserResponse)
    )
    async def get_user(self) -> ApiUserResponse:
        response = await self.__http_client.get(
            path='/ent-client-service/users/v1/me',
            response_body_type="json",
            json_has_data_field=True,
            forward_client_error_response_content=True)
        return ApiUserResponse(**response.json())

    @conditional_cache(
        key_builder=validate_user__upstream_key_builder,
        coder=PydanticCoderFactory.build(ApiAccessResponse)
    )
    async def get_api_access(
            self,
    ) -> ApiAccessResponse:
        response = await self.__http_client.get(
            path=f"/ent-client-service/users/v1/me/product/{self.__product_id}/permission/apiAccess",
            response_body_type="json",
            json_has_data_field=True)
        return ApiAccessResponse(**response.json())

    @conditional_cache(
        key_builder=get_contacts_by_id_upstream_key_builder,
        coder=PydanticCoderFactory.build(ListDataResponse[Contact, EntClientServiceMeta])
    )
    async def get_contacts_by_account_upstream(
            self, agency_account_id: str, client_account_id: str) -> ListDataResponse[Contact, EntClientServiceMeta]:

        path = f"/ent-client-service/clients/v1/product/{self.__product_id}" \
               f"/clients/{agency_account_id if agency_account_id else client_account_id}/contacts"
        params = {'filter.active.eq': 'true'}

        logger.info("Contacts path: %s; with params: %s", path, params)
        response = await self.__http_client.get(
            path=path,
            params=params,
            response_body_type="json",
            json_has_data_field=True
        )

        unwrap_response_data = {
            "data":response.json().get('data', {}).get('contacts', []),
            "meta": response.json().get('meta')
        }

        return  ListDataResponse[Contact,EntClientServiceMeta](**unwrap_response_data)

    async def get_default_contacts(self, account_id: str) -> List[Contact]:
        path = f"/ent-client-service/clients/v1/product/{self.__product_id}" \
               f"/clients/{account_id}/internal/defaults"

        logger.debug("Internal default contacts path: %s", path)

        response = await self.__http_client.get(
            path=path,
            response_body_type="json",
            json_has_data_field=True
        )

        response_data = response.json().get('data')
        return [Contact(**item) for item in response_data]
