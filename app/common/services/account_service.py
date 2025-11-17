from typing import List

from fastapi import Depends, HTTPException

from app.common.gateways.ent_client_service_gateway import EntClientServiceGateway
from app.common.model.account import Account, InternalAccount
from app.common.model.downstream.ent_client_service import BasicClientDetails, EntClientServiceMeta
from app.common.model.shared import ListDataResponse
from app.common.services.lookup_service import LookupService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class AccountService:
    ent_service: EntClientServiceGateway
    lookup: LookupService

    def __init__(
        self,
        ent_service: EntClientServiceGateway = Depends(EntClientServiceGateway),
        lookup: LookupService = Depends(LookupService)
    ):
        """Constructor for the ProductService class"""
        self.ent_service = ent_service
        self.lookup = lookup

    async def __save_uncached_accounts(
            self,
            short_accounts_ids: List[int],
            accounts_to_lookup: List[str],
            accounts_to_cache: List[dict]
    ) -> None:
        if any(short_id is None for short_id in short_accounts_ids):
            client_ids_to_save = [
                long_id for long_id, short_id in
                zip(accounts_to_lookup, short_accounts_ids) if short_id is None
            ]
            new_short_accounts_ids = await self.lookup.set_account_short_ids_by_long_ids(client_ids_to_save)
            dict_to_save = {}
            for account, new_short_id in zip(accounts_to_cache, new_short_accounts_ids):
                account["id"]=str(new_short_id)
                dict_to_save[account["internal_long_id"]] = new_short_id
            await self.lookup.set_account_long_id_by_short_id_batch(dict_to_save)

    async def get_accounts_addresses_and_contacts(self) -> ListDataResponse[BasicClientDetails, EntClientServiceMeta]:
        return await self.ent_service.get_accounts_addresses_and_contacts()

    async def parse_accounts_data(
            self,
            fetched_accounts: List[BasicClientDetails]
    ) -> List[Account]:
        if len(fetched_accounts) == 0:
            logger.info("fetched_accounts is empty")

        accounts_to_lookup = [account.clientId for account in fetched_accounts]
        short_accounts_ids = await self.lookup.get_account_short_id_by_long_id_batch(accounts_to_lookup)
        accounts_to_cache = [
            {
                "id": None,
                "internal_long_id": account.clientId,
                "name": account.displayName,
                "active":True
            }
            for short_id, account in zip(short_accounts_ids, fetched_accounts) if short_id is None
        ]
        accounts_cached = [
            {
                "id": short_id,
                "internal_long_id": account.clientId,
                "name": account.displayName,
                "active": True
            }
            for short_id, account in zip(short_accounts_ids, fetched_accounts) if short_id is not None
        ]
        await self.__save_uncached_accounts(short_accounts_ids, accounts_to_lookup, accounts_to_cache)
        accounts_cached.extend(accounts_to_cache)
        return [Account(**account) for account in accounts_cached]

    async def get_account_by_internal_id(self, internal_account_id: str) -> InternalAccount:
        return await self.ent_service.get_account_by_internal_id_upstream(internal_account_id)

    async def get_account_by_id(self, account_id: int) -> InternalAccount:
        internal_account_id = await self.get_account_by_numeric_id(account_id)
        return await self.get_account_by_internal_id(internal_account_id)

    async def get_or_create_cached_account_id(self, account_id: str) -> int:
        cached_account_id: int
        cached_account_id = await self.lookup.get_account_short_id_by_long_id(account_id)
        if cached_account_id is None:
            cached_account_id = await self.lookup.set_account_short_id_by_long_id(account_id)
        if not cached_account_id:
            logger.error("Failed to assign numeric id for account ID %s", account_id)
            raise HTTPException(status_code=500, detail="Failed to assign numeric id")
        return cached_account_id

    async def get_account_by_numeric_id(self, account_id: int) -> str:
        cached_account = await self.lookup.get_account_long_id_by_short_id(account_id)
        if cached_account is None:
            logger.error("Account ID: %s not found in cache", account_id)
            raise HTTPException(status_code=404, detail="Account not found")
        return cached_account
