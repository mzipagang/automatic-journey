from copy import deepcopy
from typing import List
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.common.context.context import request_context, user_context
from app.common.model.advertiser import AdvertiserType
from app.common.model.contact import AdvertiserContact
from app.common.model.downstream.ent_client_service import Contact, WorksFor, EntClientServiceMeta
from app.common.model.redis import CachedContact
from app.common.model.shared import ListDataResponse
from app.common.services.config_service import Config
from app.common.services.contact_service import AdvertiserContactService
from tests.unit.services.constants import DEFAULT_CONTACTS_RESPONSE_JSON


class TestAdvertiserContactService(IsolatedAsyncioTestCase):
    CONTACTS = [
        {
            "contactId": "AC0N7AC71D",
            "firstName": "Orange",
            "lastName": "Juliouso",
            "emailAddress": "organie@example.com",
            "worksFor": {
                "displayName": "Bepsico",
                "clientId": "cl13n71d-008e-4591-82be-26e06b913733",
                "type": None
            },
            "address": {
                "addressLines": [
                    ""
                ],
                "cityTown": "",
                "stateProvince": "",
                "postalCode": "",
                "countryCode": ""
            }
        }]
    __mock_lookup_service: AsyncMock
    __mock_config: MagicMock
    __mock_ent_service: AsyncMock

    subject: AdvertiserContactService

    def setUp(self):
        self.__mock_lookup_service = AsyncMock()
        self.__mock_config = MagicMock()
        self.__mock_ent_service = AsyncMock()

        FastAPICache.init(backend=InMemoryBackend(), prefix="test-cache")
        self.__mock_config.get_current_config.return_value = Config(
            base_api_url='https://test.com',
            product_id='123',
            base_koddi_url='https://koddi.com',
            pte_target_id='pte_target_id')

        self.subject = AdvertiserContactService(
            config_service=self.__mock_config,
            lookup_service=self.__mock_lookup_service,
            ent_client_service=self.__mock_ent_service)

    @pytest.mark.asyncio
    async def test_get_contacts_by_account__incoming_CPG_contact(self):

        user_context.set({"username": "test_user"})
        request_context.set({"path": "/test"})
        await self.__get_contacts_by_account_assertions(
            get_contact_details_batch_return_value=[CachedContact(**{
                'id': 'AC0N7AC71D',
                'contactType': AdvertiserType.CPG.value,
                'accountIds': ['test_account_id_1']
            })],
            get_short_id_batch_return_value=[123],
            set_short_id_return_value=123,
            get_return_value= ListDataResponse[Contact,EntClientServiceMeta](
                data=[Contact(**item) for item in deepcopy(self.CONTACTS)],
                meta=EntClientServiceMeta()
            ),
            contact_type=AdvertiserType.CPG,
            account_ids=['cpg_account_id_0'],
            expected_account_ids=['cpg_account_id_0', 'test_account_id_1'],
            expected=[AdvertiserContact(id=123, firstName='Orange', lastName='Juliouso', email='organie@example.com',
                                        contactType=AdvertiserType.CPG, active=True,
                                        accountIds=['cpg_account_id_0', 'test_account_id_1'])])

    @pytest.mark.asyncio
    async def test_get_contacts_by_account__incoming_CPG_contact__no_existing_account_ids(self):
        user_context.set({"username": "test_user"})
        request_context.set({"path": "/test"})
        await self.__get_contacts_by_account_assertions(
            get_contact_details_batch_return_value=[CachedContact(**{
                'id': 'AC0N7AC71D',
                'contactType': AdvertiserType.CPG.value,
            })],
            get_short_id_batch_return_value=[123],
            set_short_id_return_value=123,
            get_return_value= ListDataResponse[Contact,EntClientServiceMeta](
                data=[Contact(**item) for item in deepcopy(self.CONTACTS)],
                meta=EntClientServiceMeta()
            ),
            contact_type=AdvertiserType.CPG,
            account_ids=['cpg_account_id_0'],
            expected_account_ids=['cpg_account_id_0'],
            expected=[AdvertiserContact(id=123, firstName='Orange', lastName='Juliouso', email='organie@example.com',
                                        contactType=AdvertiserType.CPG, active=True,
                                        accountIds=['cpg_account_id_0'])]

        )

    @pytest.mark.asyncio
    async def test_get_contacts_by_account__incoming_AGENCY_contact(self):
        user_context.set({"username": "test_user"})
        request_context.set({"path": "/test"})
        await self.__get_contacts_by_account_assertions(
            get_contact_details_batch_return_value=[CachedContact(**{
                'id': 'AC0N7AC71D',
                'contactType': AdvertiserType.AGENCY.value,
                'accountIds': ['test_account_id_1']
            })],
            get_short_id_batch_return_value=[123],
            set_short_id_return_value=123,
            get_return_value=ListDataResponse[Contact,EntClientServiceMeta](
                data=[Contact(**item) for item in deepcopy(self.CONTACTS)],
                meta=EntClientServiceMeta()
            ),
            contact_type=AdvertiserType.AGENCY,
            account_ids=['cpg_account_id_0', 'agency_account_id_1'],
            expected_account_ids=['cpg_account_id_0', 'test_account_id_1'],
            expected=[AdvertiserContact(id=123, firstName='Orange', lastName='Juliouso', email='organie@example.com',
                                        contactType=AdvertiserType.AGENCY, active=True,
                                        accountIds=['cpg_account_id_0', 'test_account_id_1'])]
        )

    @pytest.mark.asyncio
    async def test_validate_address_on_agency_involved_campaign__with_agency_contact__should_return_true(self):
        user_context.set({"username": "test_user"})
        request_context.set({"path": "/test"})
        contact = {
            "id": "0n3c0n74c71d",
            "contactType": "AGENCY",
            "accountIds": []
        }

        result = await self.subject.validate_address_on_agency_involved_campaign(contact=CachedContact(**contact), client_id='')

        self.assertEqual(result, True)

    @pytest.mark.asyncio
    async def test_validate_address_on_agency_involved_campaign__with_client_cpg_contact_and_stored_contact__true(self):
        user_context.set({"username": "test_user"})
        request_context.set({"path": "/test"})
        contact = CachedContact(**{
            "id": "0n3c0n74c71d",
            "contactType": "CPG",
            "accountIds": ["3b5c15a3-008e-4591-82be-26e06b913733"]
        })

        result = await self.subject.validate_address_on_agency_involved_campaign(
            contact=contact, client_id='3b5c15a3-008e-4591-82be-26e06b913733')

        self.assertEqual(result, True)

    @pytest.mark.asyncio
    async def test_validate_address_on_agency_involved_campaign__with_client_cpg_contact_old_stored_contact__true(self):
        user_context.set({"username": "test_user"})
        request_context.set({"path": "/test"})
        contact = CachedContact(**{
            "id": "0n3c0n74c71d",
            "contactType": "CPG",
        })
        contacts=[
            Contact(
                contactId="AC0N7AC71D",
                firstName='Orange',
                lastName="juliouso",
                emailAddress="organie@example.com",
                worksFor=WorksFor( type=AdvertiserType.CPG))
        ]

        self.__mock_ent_service.get_contacts_by_account_upstream.return_value = ListDataResponse[Contact,EntClientServiceMeta](
                data= contacts,
                meta=EntClientServiceMeta()
        )


        self.__mock_lookup_service.get_contact_short_id_by_long_id_batch.return_value = [None]
        self.__mock_lookup_service.set_contact_short_id_by_long_id_batch.return_value = [1]

        result = await self.subject.validate_address_on_agency_involved_campaign(
            contact=contact, client_id='3b5c15a3-008e-4591-82be-26e06b913733')

        self.assertEqual(result, True)

    async def test_get_internal_default_contacts__should_succeed(self):
        self.__mock_ent_service.get_default_contacts.return_value = [
            Contact(**item) for item in deepcopy(DEFAULT_CONTACTS_RESPONSE_JSON).get('data')
        ]

        contacts_count = len(DEFAULT_CONTACTS_RESPONSE_JSON['data'])

        self.__mock_lookup_service.set_contact_short_id_by_long_id.side_effect = [i for i in range(contacts_count)]

        result = await self.subject.get_internal_default_contacts("account_id")

        self.assertEqual(2, len(result))

    @patch("logging.Logger.critical")
    async def test_get_internal_default_contacts__some_contacts_bad_roleType_data__should_handle(
            self, mock_logger_critical: MagicMock):
        response_json = deepcopy(DEFAULT_CONTACTS_RESPONSE_JSON)
        response_json['data'][0]['roleType'] = None
        response_json['data'][1]['roleType'] = {
            'asdf': 'asdf',
        }
        self.__mock_ent_service.get_default_contacts.return_value = [
            Contact(**item) for item in response_json.get('data')
        ]
        contacts_count = len(response_json['data'])

        self.__mock_lookup_service.set_contact_short_id_by_long_id.side_effect = [i for i in range(contacts_count)]

        result = await self.subject.get_internal_default_contacts("account_id")

        mock_logger_critical.assert_called()

        self.assertEqual(1, len(result))

    async def __get_contacts_by_account_assertions(
            self,
            get_contact_details_batch_return_value: List[CachedContact],
            get_short_id_batch_return_value: List[int],
            set_short_id_return_value: int,
            get_return_value: ListDataResponse[Contact,EntClientServiceMeta],
            contact_type: AdvertiserType,
            account_ids: List[str],
            expected_account_ids: List[str],
            expected: List[AdvertiserContact]):

        await FastAPICache.clear()
        self.__mock_lookup_service.get_contact_short_id_by_long_id_batch.return_value = get_short_id_batch_return_value
        self.__mock_lookup_service.get_contact_details_by_short_id_batch.return_value = get_contact_details_batch_return_value
        self.__mock_lookup_service.set_contact_short_id_by_long_id.return_value = set_short_id_return_value
        self.__mock_ent_service.get_contacts_by_account_upstream.return_value = get_return_value

        result = await self.subject.get_contacts_by_account(contact_type, *account_ids)

        self.assertIsInstance(result, list)
        self.assertEqual(result, expected)

        self.__mock_lookup_service.set_contact_details_by_short_id_batch.assert_called_once_with(
            {123: CachedContact(**{
                'id': 'AC0N7AC71D',
                'contactType': contact_type.value,
                'accountIds': expected_account_ids
            })})

    async def test_get_contacts_by_account__supports_contacts_without_names(self):
        contact_type = AdvertiserType.CPG
        contact_id=1234
        short_id = 4321
        client_id="client_id"
        email="advertiser@example.com"
        expected_contacts = [AdvertiserContact(
            id=short_id,
            firstName=None,
            lastName=None,
            email=email,
            contactType=contact_type,
            active=True,
            accountIds=[client_id]
        )]
        mock_ent_client_service_response = ListDataResponse[Contact,EntClientServiceMeta](
            data=[Contact(
                contactId=f"{contact_id}",
                clientId=client_id,
                emailAddress=email
            )],
            meta=EntClientServiceMeta()
        )
        self.__mock_ent_service.get_contacts_by_account_upstream.return_value = mock_ent_client_service_response
        self.__mock_lookup_service.get_contact_short_id_by_long_id_batch.return_value = [short_id]

        results = await self.subject.get_contacts_by_account(
            contact_type,
            client_account_id=client_id,
        )

        self.assertEqual(expected_contacts, results)
        serialized_contact = results[0].model_dump()
        self.assertEqual("", serialized_contact.get('firstName'))
        self.assertEqual("", serialized_contact.get('lastName'))
