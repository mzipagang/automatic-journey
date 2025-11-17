from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from app.common.model.account import AccountResponse
from app.common.model.downstream.ent_client_service import BasicClientDetails
from app.common.model.shared import Page, Meta
from app.common.services.account_service import AccountService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class MetadataService:
    __account_service: AccountService

    def __init__(self, account_service: AccountService = Depends(AccountService)):
        self.__account_service = account_service

    async def get_accounts_and_cache_addresses_and_contacts(self, offset: int, size: int):
        logger.info("GET /accounts Getting user accounts")
        response = await self.__account_service.get_accounts_addresses_and_contacts()
        accounts = await self.__account_service.parse_accounts_data(fetched_accounts=response.data)

        if accounts is None:
            raise HTTPException(status_code=404, detail="Accounts not found")

        has_more = len(accounts) > offset + size

        return AccountResponse(
            data=jsonable_encoder(accounts[offset:offset + size]),
            meta=Meta(**{
                "page": Page(**{
                    "offset": offset,
                    "size": size,
                    "hasMore": has_more
                })
            })
        )
