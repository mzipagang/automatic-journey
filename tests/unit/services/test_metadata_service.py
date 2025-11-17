from copy import deepcopy
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.common.context.context import user_context
from app.common.model.account import AccountResponse
from app.common.model.downstream.ent_client_service import BasicClientDetails, EntClientServiceMeta
from app.common.model.shared import ListDataResponse
from app.common.services.metadata_service import MetadataService
from tests.unit.services.ent_client_service_constants import (
    ACCOUNTS_ADDRESSES_AND_CONTACTS,
)


class TestMetadataService(IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_account_service: AsyncMock = AsyncMock()
        self.mock_background_cache: MagicMock = MagicMock()
        self.mock_current_user: MagicMock = MagicMock()
        self.mock_token: MagicMock = MagicMock()

        FastAPICache.init(backend=InMemoryBackend(), prefix="test")

        self.subject = MetadataService(account_service=self.mock_account_service)

    @patch('logging.Logger.info')
    @pytest.mark.asyncio
    async def test_get_accounts_and_cache_addresses_and_contacts__should_succeed(
            self,
            mock_logger_info: MagicMock):

        user_context.set({'username': 'test_user'})
        mock_accounts = [MagicMock() for _ in range(len(ACCOUNTS_ADDRESSES_AND_CONTACTS['data']))]

        self.mock_account_service.get_accounts_addresses_and_contacts.return_value = \
            ListDataResponse[BasicClientDetails, EntClientServiceMeta](**ACCOUNTS_ADDRESSES_AND_CONTACTS)

        self.mock_account_service.parse_accounts_data.return_value = mock_accounts

        expected = AccountResponse(
            data=jsonable_encoder(mock_accounts),
            meta={"page": {"offset": 0, "size": 10, "hasMore": False}})

        result = await self.subject.get_accounts_and_cache_addresses_and_contacts(0, 10)

        self.assertEqual(expected, result)

        self.mock_account_service.parse_accounts_data.assert_called_once_with(
            fetched_accounts=[BasicClientDetails(**account) for account in ACCOUNTS_ADDRESSES_AND_CONTACTS['data']])

        mock_logger_info.assert_called_once_with("GET /accounts Getting user accounts")

