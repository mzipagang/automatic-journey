from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import Response

from app.common.context.context import user_context
from app.common.model.account import InternalAccount
from app.common.services.account_service import AccountService


class TestAccountService(IsolatedAsyncioTestCase):
    __mock_ent_service: AsyncMock
    __mock_lookup_service: AsyncMock

    subject: AccountService

    def setUp(self):
        FastAPICache.init(backend=InMemoryBackend(), prefix="test")
        self.__mock_ent_service = AsyncMock()
        self.__mock_lookup_service = AsyncMock()
        self.__mock_http_client_service = MagicMock()

        self.subject = AccountService(ent_service=self.__mock_ent_service, lookup=self.__mock_lookup_service)

    @pytest.mark.asyncio
    async def test_get_accounts_addresses_and_contacts__should_succeed(self):
        user_context.set({"username": "test"})
        self.__mock_http_client_service.get.return_value = Response(
            status_code=200,
            json={}
        )

        await self.subject.get_accounts_addresses_and_contacts()

        self.__mock_ent_service.get_accounts_addresses_and_contacts.assert_called_once()

    @patch('logging.Logger.info')
    async def test_parse_accounts_data__empty_fetched_accounts__should_succeed_and_log(
            self,
            mock_logger_info: MagicMock):

        await self.subject.parse_accounts_data(fetched_accounts=[])

        self.__mock_lookup_service.get_account_short_id_by_long_id_batch.assert_called_once_with([])

        mock_logger_info.assert_called_once_with("fetched_accounts is empty")

    @pytest.mark.asyncio
    async def test_get_account_by_id__should_succeed(self):
        self.__mock_lookup_service.get_account_long_id_by_short_id.return_value = "abc123"
        expected = InternalAccount(
            id="abc123",
            name="test display name",
            active=True
        )
        self.__mock_ent_service.get_account_by_internal_id_upstream.return_value = expected

        actual = await self.subject.get_account_by_id(account_id=123)

        self.__mock_lookup_service.get_account_long_id_by_short_id.assert_called_once_with(123)
        self.assertEqual(expected, actual)

    @pytest.mark.asyncio
    async def test_save_uncached_accounts(self):
        # Arrange}
        short_accounts_ids = [1, None, 3, 4, None]
        accounts_to_lookup = ["account1", "account2", "account3", "account4", "account5"]
        accounts_to_cache = [
            {"id": None, "internal_long_id": "account2", "name": "Account 2", "active": True},
            {"id": None, "internal_long_id": "account5", "name": "Account 5", "active": True}
        ]

        self.__mock_lookup_service.set_account_short_ids_by_long_ids.return_value = [6, 7]  # Simulating new short IDs for uncached accounts

        # Act
        await self.subject._AccountService__save_uncached_accounts(
            short_accounts_ids=short_accounts_ids,
            accounts_to_lookup=accounts_to_lookup,
            accounts_to_cache=accounts_to_cache
        )

        # Assert
        self.__mock_lookup_service.set_account_short_ids_by_long_ids.assert_called_once_with(
            ["account2", "account5"]
        )
        self.__mock_lookup_service.set_account_long_id_by_short_id_batch.assert_called_once_with(
            {"account2": 6, "account5": 7}
        )

    @pytest.mark.asyncio
    async def test_get_or_create_cached_account_id(self):
        # Arrange
        account_id = "account123"
        self.__mock_lookup_service.get_account_short_id_by_long_id.return_value = None
        self.__mock_lookup_service.set_account_short_id_by_long_id.return_value = 42

        # Act
        result = await self.subject.get_or_create_cached_account_id(account_id)

        # Assert
        self.assertEqual(42, result)
        self.__mock_lookup_service.get_account_short_id_by_long_id.assert_called_once_with(account_id)
        self.__mock_lookup_service.set_account_short_id_by_long_id.assert_called_once_with(account_id)

    @pytest.mark.asyncio
    @patch('logging.Logger.error')
    async def test_get_or_create_cached_account_id_error_saving_account(self, mock_logger_error: MagicMock):
        # Arrange
        account_id = "account123"
        self.__mock_lookup_service.get_account_short_id_by_long_id.return_value = None
        self.__mock_lookup_service.set_account_short_id_by_long_id.return_value = None

        # Act
        with self.assertRaises(HTTPException) as context:
            await self.subject.get_or_create_cached_account_id(account_id)

        # Assert
        self.assertEqual(500, context.exception.status_code)
        self.assertEqual("Failed to assign numeric id", context.exception.detail)
        mock_logger_error.assert_called_with("Failed to assign numeric id for account ID %s", account_id)

    @pytest.mark.asyncio
    @patch('logging.Logger.error')
    async def test_get_account_by_numeric_id_cached_is_None(self, mock_logger_error: MagicMock):
        # Arrange
        account_id = 123
        self.__mock_lookup_service.get_account_long_id_by_short_id.return_value = None

        # Act
        with self.assertRaises(HTTPException) as context:
            await self.subject.get_account_by_numeric_id(account_id)

        # Assert
        self.assertEqual(404, context.exception.status_code)
        self.assertEqual("Account not found", context.exception.detail)
        self.__mock_lookup_service.get_account_long_id_by_short_id.assert_called_once_with(account_id)
        mock_logger_error.assert_called_with("Account ID: %s not found in cache", account_id)