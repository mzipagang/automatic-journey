import json
from typing import List

from fastapi import Depends, HTTPException
from httpx import codes as httpx_codes

from app.common.gateways.ent_client_service_gateway import EntClientServiceGateway
from app.common.model.advertiser import AdvertiserType
from app.common.model.contact import AdvertiserContact, InternalContact, InternalContactType
from app.common.model.downstream.ent_client_service import Contact
from app.common.model.redis import CachedContact
from app.common.services.config_service import ConfigService
from app.common.services.http_client_service import ExternalApiHttpClientService
from app.common.services.lookup_service import LookupService
from app.common.utils import filtered_logger

logger = filtered_logger.get_logger(__name__)


class AdvertiserContactService:
    __external_api_http_client: ExternalApiHttpClientService
    __product_id: str
    ent_client_service: EntClientServiceGateway

    def __init__(
            self,
            config_service: ConfigService = Depends(ConfigService),
            lookup_service: LookupService = Depends(LookupService),
            ent_client_service: EntClientServiceGateway = Depends(EntClientServiceGateway)
    ):
        self.__product_id = config_service.get_current_config().product_id
        self.lookup_service = lookup_service
        self.ent_client_service = ent_client_service

    async def get_contacts_by_account(
            self,
            contact_type: AdvertiserType,
            client_account_id: str = None,
            agency_account_id: str = None,
            fetched_contacts: List[dict] = None,
            fetched_cpg_accounts: List[dict] = None) -> List[AdvertiserContact]:

        if fetched_contacts is None:
            fetched_contacts = await self.ent_client_service.get_contacts_by_account_upstream(
                agency_account_id=agency_account_id,
                client_account_id=client_account_id
            )

        if client_account_id is not None and fetched_cpg_accounts is None:
            return await self.__parse_contacts(contact_type, client_account_id, fetched_contacts.data)
        if fetched_cpg_accounts is not None:
            contacts = []
            for cpg_account in fetched_cpg_accounts:
                contacts += await self.__parse_contacts(contact_type, cpg_account['clientId'], fetched_contacts.data)
            return contacts

        logger.critical("get_contacts_by_account must be called with either client_account_id or fetched_cpg_accounts")
        raise HTTPException(
            status_code=500,
            detail="get_contacts_by_account must be called with either client_account_id or fetched_cpg_accounts")

    async def __parse_contacts(
        self,
        contact_type: AdvertiserType,
        client_account_id: str,
        fetched_contacts: List[Contact]
    ) -> List[AdvertiserContact]:
        contacts: list[AdvertiserContact] = []
        contacts_by_short_id: dict[int, CachedContact] = {}

        contact_long_ids = [c.contactId for c in fetched_contacts]
        short_ids = await self.lookup_service.get_contact_short_id_by_long_id_batch(
            contact_long_ids,
        )
        short_id_by_long_id: dict[str, int] = {}
        long_ids_for_missing_short_ids = []
        for contact_long_id, short_id in zip(contact_long_ids, short_ids):
            short_id_by_long_id[contact_long_id] = short_id
            if short_id is None:
                long_ids_for_missing_short_ids.append(contact_long_id)

        # Assign missing ids
        if long_ids_for_missing_short_ids:
            missing_short_ids = await self.lookup_service.set_contact_short_id_by_long_id_batch(long_ids_for_missing_short_ids)
            if None in missing_short_ids:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to assign contact ids for {long_ids_for_missing_short_ids}",
                )
            for missing_long_id, missing_short_id in zip(long_ids_for_missing_short_ids, missing_short_ids):
                short_id_by_long_id[missing_long_id] = missing_short_id

        short_ids = [short_id for short_id in short_id_by_long_id.values()]
        cached_contacts = await self.lookup_service.get_contact_details_by_short_id_batch(
            short_ids
        )
        for short_id, contact in zip(short_ids, cached_contacts):
            if contact:
                contacts_by_short_id[short_id] = contact

        to_mset: dict[int, CachedContact] = {}
        account_ids = [client_account_id]

        for contact, short_id, contact_long_id in zip(fetched_contacts, short_ids, contact_long_ids):
            cached = contacts_by_short_id.get(short_id)
            merged = sorted(set((cached.accountIds if cached and cached.accountIds else []) + account_ids))

            # build the JSON payload and enqueue for MSET
            payload = {
                "id": contact_long_id,
                "contactType": contact_type.value,
                "accountIds": merged,
            }
            to_mset[short_id] = CachedContact(**payload)

            contacts.append(AdvertiserContact(
                id=short_id,
                firstName=contact.firstName,
                lastName=contact.lastName,
                email=contact.emailAddress,
                contactType=contact_type,
                accountIds=merged,
                active=True,
            ))

        await self.lookup_service.set_contact_details_by_short_id_batch(to_mset)

        return contacts

    async def get_internal_default_contacts(self, account_id: str) -> List[InternalContact]:
        contacts = []
        default_contacts = await self.ent_client_service.get_default_contacts(
            account_id= account_id
        )

        for contact in default_contacts:
            if contact.roleType and contact.roleType.type:
                if contact.roleType.type == InternalContactType.ACCOUNT_EXECUTIVE:
                    contacts.append(InternalContact(
                        type=InternalContactType.ACCOUNT_EXECUTIVE,
                        id=contact.contactId
                    ))
                if contact.roleType.type == InternalContactType.PRIMARY_ACCOUNT_MANAGER:
                    contacts.append(InternalContact(
                        type=InternalContactType.PRIMARY_ACCOUNT_MANAGER,
                        id=contact.contactId
                    ))
            else:
                logger.critical("Contact data is not in the expected format.  Contact data: %s", contact)
        return contacts

    async def get_contact_by_numeric_id(self, contact_id: int) -> CachedContact:
        cached_contact = await self.lookup_service.get_contact_details_by_short_id(contact_id)
        if cached_contact is None:
            logger.warning("Contact ID: %s not found in cache", contact_id)
            raise HTTPException(status_code=404, detail="Contact not found")
        return cached_contact

    async def validate_address_on_agency_involved_campaign(self, contact: CachedContact, client_id: str) -> bool:
        if contact.contactType == AdvertiserType.AGENCY.value:
            return True
        if contact.accountIds and client_id in contact.accountIds:
            return True
        fresh_contacts = await self.get_contacts_by_account(AdvertiserType.CPG, client_id)
        for fresh_contact in fresh_contacts:
            if client_id in fresh_contact.accountIds:
                return True
        return False
