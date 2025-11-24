from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import Response

from app.common.context.context import user_context, request_context
from app.common.gateways.ent_client_service_gateway import EntClientServiceGateway
from app.common.model.account import InternalAccount
from app.common.model.contact import InternalContactType
from app.common.model.address import AccountAddress
from app.common.model.downstream.ent_client_service import (
    UserPermissions,
    EntClientServiceMeta,
    ProductAccess,
    Contact,
    WorksFor,
    ContactRoleGroup
)
from app.common.model.redis import CachedRedisAdvertiser
from app.common.model.shared import SingleDataResponse, ListDataResponse
from app.common.view_models import AuthRole
from tests.utils_for_testing.auto_mock import auto_mock


class TestEntClientServiceGateway(IsolatedAsyncioTestCase):
    def setUp(self):
        self.product_id = "4321"
        FastAPICache.init(backend=InMemoryBackend(), prefix="test")
        user_context.set({"username": "test"})
        request_context.set({"path": "/test", "params": {}})

        with patch("app.common.gateways.ent_client_service_gateway.AsyncExternalApiHttpClientService", new=AsyncMock()) as self.mock_http_client:
            self.mock_config_service = MagicMock()
            self.mock_config_service.get_current_config.return_value = auto_mock({
                "product_id": self.product_id,
            }, MagicMock())
            self.__mock_external_http_client_service = MagicMock()
            self.__mock_harness_service = MagicMock()

            self.__mock_harness_service.is_harness_flag_on.return_value = True

            self.ent_client_service_gateway = EntClientServiceGateway(
                async_external_api_http_client=self.mock_http_client,
                external_api_http_client_service=self.__mock_external_http_client_service,
                config_service=self.mock_config_service,
                harness_service=self.__mock_harness_service,
            )

    async def tearDown(self):
        await FastAPICache.clear()

    async def test_get_user_roles__returns_unique_roles(self):
        await self.tearDown()
        mock_response = SingleDataResponse[UserPermissions, EntClientServiceMeta](
            data=UserPermissions(permissions=[
                ProductAccess(roles=[
                    "Random role",
                    "Advertiser API"
                ]),
                ProductAccess(roles=[
                    "Advertiser API",
                    "Reporting API"
                ])
            ]),
            meta=EntClientServiceMeta()
        )
        expected_response = {
            AuthRole.OTHER_ROLE,
            AuthRole.ADVERTISER_API,
            AuthRole.REPORTING_API,
        }
        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json=mock_response.model_dump()
        )

        result = await self.ent_client_service_gateway.get_user_roles()

        self.assertEqual(expected_response, result)

    async def test_get_user_roles__returns_empty_set_if_there_are_no_permissions(self):
        await self.tearDown()
        mock_response = SingleDataResponse[UserPermissions, EntClientServiceMeta](
            data=UserPermissions(permissions=[]),
            meta=EntClientServiceMeta()
        )
        expected_response = set[AuthRole]()
        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json=mock_response.model_dump()
        )

        result = await self.ent_client_service_gateway.get_user_roles()

        self.assertEqual(expected_response, result)

    async def test_get_user_roles_cache(self):
        await self.tearDown()
        mock_response = SingleDataResponse[UserPermissions, EntClientServiceMeta](
            data=UserPermissions(permissions=[
                ProductAccess(roles=[
                    "Random role",
                    "Advertiser API"
                ]),
                ProductAccess(roles=[
                    "Advertiser API",
                    "Reporting API"
                ])
            ]),
            meta=EntClientServiceMeta()
        )

        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json=mock_response.model_dump()
        )

        # First call should set cache
        result1 = await self.ent_client_service_gateway.get_user_roles()
        # Second call should hit cache and not call the actual function again
        result2 = await self.ent_client_service_gateway.get_user_roles()

        assert result1 == result2
        assert self.mock_http_client.get.call_count == 1  # Ensure HTTP call was made only once

    @patch('logging.Logger.error')
    async def test_get_account_by_none_internal_id_upstream(
            self,
            mock_logger_error: MagicMock
    ):
        # Act
        with self.assertRaises(HTTPException) as context:
            await self.ent_client_service_gateway.get_account_by_internal_id_upstream(internal_account_id=None)

        # Assert
        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Account not found", context.exception.detail)
        mock_logger_error.assert_called_with("Supplied Internal Account ID is None")

    async def test_get_account_by_internal_id_upstream(self):
        # Arrange
        expected = InternalAccount(
            id="123",
            name="test display name",
            active=True
        )
        self.mock_http_client.get.return_value = Response(status_code=200, json={"data": {"displayName": "test display name"}})

        # Act
        actual = await self.ent_client_service_gateway.get_account_by_internal_id_upstream(internal_account_id="123")

        # Assert
        self.mock_http_client.get.assert_called_once_with(
            path="/ent-client-service/clients/v1/product/4321/clients/123",
            response_body_type="json",
            json_has_data_field=True
        )

        self.assertEqual(expected, actual)

    async def test_get_brands__makes_http_request_and_coverts_response_to_model(self):
        await self.tearDown()
        product_id = self.product_id
        account_id = "1234"
        mock_response = ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta](
            data=[
                CachedRedisAdvertiser(
                    brandId='brand1',
                    displayName="Brand One",
                    salesforceId="SF1",
                    client=None
                )
            ],
            meta=EntClientServiceMeta()
        )
        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json=mock_response.model_dump()
        )

        response = await self.ent_client_service_gateway.get_brands(account_id)

        self.mock_http_client.get.assert_called_with(
            path=f"/ent-client-service/clients/v1/product/{product_id}/clients/{account_id}/brands",
            response_body_type="json",
            json_has_data_field=True
        )
        self.assertEqual(mock_response, response)

    async def test_get_user_brands__makes_http_request_and_converts_response_to_model(self):
        await self.tearDown()
        product_id = self.product_id
        account_id = "1234"

        upstream_response = {
            "data": [
                {
                    "brandId": "brand1",
                    "displayName": "Brand One",
                    "salesforceId": "SF1",
                    "client": {"clientId": account_id}
                },
                {
                    "brandId": "brand2",
                    "displayName": "Brand Two",
                    "salesforceId": "SF2",
                    "client": {"clientId": "9999"}
                }
            ],
            "meta": {}
        }

        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json=upstream_response
        )

        response = await self.ent_client_service_gateway.get_user_brands(account_id)

        self.mock_http_client.get.assert_called_with(
            path=f"/ent-client-service/clients/v1/product/{product_id}/brands",
            response_body_type="json",
            json_has_data_field=True
        )

        expected_response = ListDataResponse[CachedRedisAdvertiser, EntClientServiceMeta](
            data=[
                CachedRedisAdvertiser(
                    brandId="brand1",
                    displayName="Brand One",
                    salesforceId="SF1",
                    client={"clientId": account_id}
                )
            ],
            meta=EntClientServiceMeta()
        )

        self.assertEqual(1, len(response.data))
        self.assertIsInstance(response.data[0], CachedRedisAdvertiser)
        self.assertEqual(expected_response.data, response.data)
        self.assertEqual(expected_response.meta, response.meta)

    async def test_get_user_brands__returns_filtered_brands(self):
        await self.tearDown()
        product_id = self.product_id
        account_id = "1234"

        mock_response = {
            "data": [
                {
                    "brandId": "brand1",
                    "displayName": "Brand One",
                    "salesforceId": "SF1",
                    "client": {"clientId": account_id}
                },
                {
                    "brandId": "brand2",
                    "displayName": "Brand Two",
                    "salesforceId": "SF2",
                    "client": {"clientId": "9999"}
                }
            ],
            "meta": {}
        }

        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json=mock_response
        )

        result = await self.ent_client_service_gateway.get_user_brands(account_id)

        self.mock_http_client.get.assert_called_with(
            path=f"/ent-client-service/clients/v1/product/{product_id}/brands",
            response_body_type="json",
            json_has_data_field=True
        )

        expected_brands = [
            CachedRedisAdvertiser(
                brandId="brand1",
                displayName="Brand One",
                salesforceId="SF1",
                client={"clientId": account_id}
            )
        ]

        self.assertEqual(expected_brands, result.data)
        self.assertIsNotNone(result.meta)

    async def test_get_addresses_by_account__makes_http_request_and_converts_response_to_model(self):
        await self.tearDown()
        product_id = self.product_id
        account_id = "1234"
        mock_addresses = [
            {
                "addressId": "addr1",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zipCode": "94105"
            },
            {
                "addressId": "addr2",
                "street": "456 Market St",
                "city": "San Francisco",
                "state": "CA",
                "zipCode": "94103"
            }
        ]

        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json={"data": {"addresses": mock_addresses}}
        )

        response = await self.ent_client_service_gateway.get_addresses_by_account(account_id)

        self.mock_http_client.get.assert_called_once_with(
            path=f"/ent-client-service/clients/v1/product/{product_id}/clients/{account_id}",
            params={
                "option.details": "Full",
                "filter.duplicateAddresses": "true"
            },
            response_body_type="json",
            json_has_data_field=True
        )
        self.assertEqual(2, len(response.data))
        self.assertIsInstance(response.data[0], AccountAddress)
        self.assertIsInstance(response.data[1], AccountAddress)

    async def test_get_contacts_by_account_upstream(self):
        # Arrange
        product_id = self.product_id
        client_account_id = "123"
        contact_one = Contact(
            contactId="1",
            firstName="Lauren",
            emailAddress="lauren@test.com",
            worksFor=WorksFor()
        )
        contact_two = Contact(
            contactId="2",
            firstName="John",
            emailAddress="john@test.com",
            worksFor=WorksFor()
        )
        expected = [contact_one, contact_two]

        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json={"data": {"contacts": [contact_one.model_dump(), contact_two.model_dump()]},
                  "meta":{"allAccountsAccess": True, "internalUser": True}}
        )

        # Act
        actual = await self.ent_client_service_gateway.get_contacts_by_account_upstream(agency_account_id="", client_account_id=client_account_id)

        # Assert
        self.mock_http_client.get.assert_called_once_with(
            path=f"/ent-client-service/clients/v1/product/{product_id}/clients/{client_account_id}/contacts",
            params={'filter.active.eq': 'true'},
            response_body_type="json",
            json_has_data_field=True
        )

        self.assertEqual(expected, actual.data)

    async def test_get_default_contacts(self):
        # Arrange
        product_id = self.product_id
        account_id = "3847362"
        contact_one = Contact(
            contactId="5",
            firstName="Lauren",
            emailAddress="lauren@test.com",
            worksFor=WorksFor(),
            roleType=ContactRoleGroup(type=InternalContactType.ACCOUNT_EXECUTIVE),
        )

        expected = [contact_one]

        self.mock_http_client.get.return_value = Response(
            status_code=200,
            json={"data": [contact_one.model_dump()]})

        # Act
        actual = await self.ent_client_service_gateway.get_default_contacts(account_id=account_id)

        # Assert
        self.mock_http_client.get.assert_called_once_with(
            path=f"/ent-client-service/clients/v1/product/{product_id}/clients/{account_id}/internal/defaults",
            response_body_type="json",
            json_has_data_field=True
        )
        self.assertEqual(expected, actual)
        self.assertEqual(actual[0].roleType, contact_one.roleType)

