from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest
from fastapi import HTTPException

from app.common.context.context import user_context
from app.common.model.advertiser import CachedAdvertiser
from app.common.model.downstream.ent_client_service import ApiUserResponse, \
    ApiAccessResponse, WorksFor
from app.common.services.config_service import Config
from app.common.services.harness_service import HarnessService
from app.common.utils.jwt import get_user, validate_account, validate_advertiser, validate_user

class TestUtilsJwt(IsolatedAsyncioTestCase):
    __mock_internal_http_client_service: MagicMock
    __mock_config_service: MagicMock
    __mock_account_service: MagicMock
    __mock_harness_service: Mock
    __mock_ent_client_service: AsyncMock


    def setUp(self):
        self.__mock_internal_http_client_service = MagicMock()
        self.__mock_config_service = MagicMock()
        self.__mock_account_service = AsyncMock()
        self.__mock_harness_service = Mock(spec=HarnessService)
        self.__mock_ent_client_service = AsyncMock()

        self.__mock_harness_service.is_harness_flag_on.return_value = True
        self.__mock_harness_service.fetch_multivariate_flag.return_value = {'enabled': False, 'ttl': 0}

        self.__mock_config_service.return_value = Config(
            base_api_url='https://api-dev.8451.com.invalid',
            base_koddi_url='https://kroger.uat.az.koddi.io.invalid',
            product_id='abc-123',
            pte_target_id='def-456-invalid')

    @pytest.mark.asyncio
    async def test_get_user__should_return_expected_format(self):
        response = ApiUserResponse(**{
            'data': {'active': True}
        })
        self.__mock_ent_client_service.get_user.return_value = response

        result = await get_user(
            harness_service=self.__mock_harness_service,
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                             'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                             'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q',
            ent_client_service=self.__mock_ent_client_service
        )

        self.assertEqual(response, result)
        self.__mock_ent_client_service.get_user.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_get_user__token_email_mismatch__should_raise_503(self):
        await self.__get_user_email_mismatch_assertions(
            user_context_email="not_abc@123.invalid",
            get_user_email="not_abc@123.invalid",
            token_email="abc@123.invalid",
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                  'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                  'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q')

    @pytest.mark.asyncio
    async def test_get_user__context_email_mismatch__should_raise_503(self):
        await self.__get_user_email_mismatch_assertions(
            user_context_email="not_abc@123.invalid",
            get_user_email="abc@123.invalid",
            token_email="abc@123.invalid",
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                  'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                  'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q')

    @pytest.mark.asyncio
    async def test_get_user__get_user_email_mismatch__should_raise_503(self):
        await self.__get_user_email_mismatch_assertions(
            user_context_email="abc@123.invalid",
            get_user_email="not_abc@123.invalid",
            token_email="abc@123.invalid",
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                  'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                  'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q')


    @patch('logging.Logger.error')
    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on')
    async def __get_user_email_mismatch_assertions(
            self,
            mock_is_harness_flag_on: MagicMock,
            mock_error_logger: MagicMock,
            user_context_email: str,
            get_user_email: str,
            token_email: str,
            token: str,
    ):
        mock_is_harness_flag_on.return_value = True
        user_context.set({'username': user_context_email})
        self.__mock_ent_client_service.get_user.return_value = ApiUserResponse(
            **{'data': {'active': True, 'email': get_user_email}}
        )

        with self.assertRaises(HTTPException) as context:
            await get_user(
                harness_service=self.__mock_harness_service,
                token=token,
                ent_client_service=self.__mock_ent_client_service
            )
            foo = "bar"

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual('Auth call error.  Please retry.', context.exception.detail)

        user_context_email_upper = user_context_email.upper()
        get_user_email_upper = get_user_email.upper()
        token_email_upper = token_email.upper()

        mock_error_logger.assert_has_calls([call(
            'User Email: %s; User Email from token: %s; User Email from user context: %s',
            get_user_email_upper, token_email_upper, user_context_email_upper,
            extra={
                'email': get_user_email_upper,
                'token_email': token_email_upper,
                'context_email': user_context_email_upper,
                'monitored_transaction': 'EMAIL-MISMATCH'})])

    @pytest.mark.asyncio
    async def test_get_user__user_inactive__raises_http_exception_status_401(self):
        response = ApiUserResponse(**{"data": {'active': False, 'email': 'abc@example.invalid'}})
        self.__mock_ent_client_service.get_user.return_value = response

        await self.__raises_401_assertions(
            expected_logged_message="Get User Response: %s",
            expected_logged_response_content=response.model_dump())

    @pytest.mark.asyncio
    async def test_get_user__data_missing__raises_http_exception_status_401(self):
        response = ApiUserResponse(**{'data': {}})
        self.__mock_ent_client_service.get_user.return_value = response

        await self.__raises_401_assertions(
            expected_logged_message="Get User Response: %s",
            expected_logged_response_content=response.model_dump())


    @pytest.mark.asyncio
    async def test_validate_user__external_user__should_succeed(self):
        user_context.set({'username': 'abc@123.invalid'})
        client_id="1234"

        self.__mock_ent_client_service.get_api_access.return_value = ApiAccessResponse(
            **{
                "data": {
                    'hasAccessToAllAccounts': False,
                    'worksFor': {
                        "clientId": client_id,
                        "displayName": "Agency Name",
                        'type': 'BROKER_OR_AGENCY'
                    },
                    'accountList': [
                        {'type': 'BRAND', 'id': "test_account_id"},
                        {'type': 'CPG', 'id': "test_account_id_2"},
                        {'type': 'UNKNOWN', 'id': "test_account_id_3", 'name': 'Unknown'}
                    ]
                }
            })

        expected: dict = {
            'email': 'abc@123.invalid',
            'works_for': {
                "clientId": client_id,
                "displayName": "Agency Name",
                'type': 'BROKER_OR_AGENCY'
            },
            'is_agency': True,
            'internal': False,
            'accounts': ["test_account_id_2"],
            'brands': ["test_account_id"]
        }

        result = await validate_user(
            user=ApiUserResponse(**{"data":{'email': 'abc@123.invalid'}}),
            harness_service=self.__mock_harness_service,
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                         'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                         'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q',
            ent_client_service=self.__mock_ent_client_service
        )

        self.assertEqual(expected, result)
        self.assertEqual(client_id, result['works_for']['clientId'])

    @pytest.mark.asyncio
    async def test_validate_user__internal_user__should_succeed(self):
        user_context.set({'username': 'internal@8451.com.invalid'})

        self.__mock_ent_client_service.get_api_access.return_value = ApiAccessResponse(
            **{
                'data': {
                    'hasAccessToAllAccounts': True,
                    'worksFor': {'type': 'INTERNAL'},
                    'accountList': [
                        {'type': 'BRAND', 'id': "test_account_id_1"},
                        {'type': 'CPG', 'id': "test_account_id_2"},
                        {'type': 'UNKNOWN', 'id': "test_account_id_3", 'name': 'Unknown'}
                    ]
                }
            })

        expected: dict = {
            'email': 'internal@8451.com.invalid',
            'works_for': {'clientId': None, 'displayName': None, 'type': 'INTERNAL'},
            'is_agency': False,
            'internal': True,
            'accounts': [],
            'brands': []
        }

        result = await validate_user(
            user=ApiUserResponse(**{"data": {'email': 'internal@8451.com.invalid'}}),
            harness_service=self.__mock_harness_service,
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaW'
                  'F0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImludGVybmFsQDg0NTEuY29tLmludmFsaWQifQ.VwXFPDkJhoTGD96J5h-tHPeY'
                  'mJUqPixDfv-3IARz9js',
            ent_client_service=self.__mock_ent_client_service
        )

        self.assertEqual(expected, result)


    @pytest.mark.asyncio
    async def test_validate_user__token_email_mismatch__raises_http_exception_status_503(self):
        await self.__user_identity_check_error_assertions(
            context_email_address="not_abc@123.invalid",
            get_user_email_address="not_abc@123.invalid",
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                  'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                  'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q')


    @pytest.mark.asyncio
    async def test_validate_user__context_email__get_upstream_mismatch__should_raise_http_exception_status_503(self):
        await self.__user_identity_check_error_assertions(
            context_email_address="not_abc@123.invalid",
            get_user_email_address="abc@123.invalid",
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                             'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                             'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q')


    @pytest.mark.asyncio
    async def test_validate_user__context_email__get_user_mismatch__should_raise_http_exception_status_503(self):
        await self.__user_identity_check_error_assertions(
            context_email_address="abc@123.invalid",
            get_user_email_address="not_abc@123.invalid",
            token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                  'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                  'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q')


    @patch('logging.Logger.error')
    @patch('app.common.services.harness_service.HarnessService.is_harness_flag_on')
    @pytest.mark.asyncio
    async def __user_identity_check_error_assertions(
            self,
            mock_is_harness_flag_on: MagicMock,
            mock_error_logger: MagicMock,
            context_email_address: str,
            get_user_email_address: str,
            token: str):

        mock_is_harness_flag_on.return_value = True
        user_context.set({'username': context_email_address})

        self.__mock_ent_client_service.get_api_access.return_value = ApiAccessResponse(
            **{
                'data': {
                    'hasAccessToAllAccounts': False,
                    'worksFor': {'type': 'BROKER_OR_AGENCY'},
                    'accountList': [
                        {'type': 'BRAND', 'id': "test_account"},
                        {'type': 'CPG', 'id': "test_account_2"},
                        {'type': 'UNKNOWN', 'id': "test_account_3", 'name': 'Unknown'}
                    ]
                }
            })

        with self.assertRaises(HTTPException) as context:
            await validate_user(
                user=ApiUserResponse(**{"data":{'email': get_user_email_address}}),
                harness_service=self.__mock_harness_service,
                token=token,
                ent_client_service=self.__mock_ent_client_service
            )

        self.assertEqual(503, context.exception.status_code)
        self.assertEqual("Auth call error.  Please retry.", context.exception.detail)

        mock_error_logger.assert_called()



    async def test_validate_account__internal_user__should_succeed(self):
        result = await validate_account(
            current_user={'internal': True}, account_id=1, account_service=self.__mock_account_service)

        self.__mock_account_service.get_account_by_numeric_id.assert_not_called()

        self.assertTrue(result)
    #
    async def test_validate_account__external_user__should_succeed(self):
        self.__mock_account_service.get_account_by_numeric_id.return_value = 1

        result = await validate_account(
            current_user={'internal': False, 'accounts': [1]}, account_id=1, account_service=self.__mock_account_service
        )

        self.__mock_account_service.get_account_by_numeric_id.assert_called_once_with(1)

        self.assertTrue(result)


    @patch('logging.Logger.warning')
    async def test_validate_account__external_user__account_not_in_user_accounts__raises_http_exception_status_403(
        self, mock_warning_logger: MagicMock
    ):
        self.__mock_account_service.get_account_by_numeric_id.return_value = 2

        with self.assertRaises(HTTPException) as context:
            await validate_account(
                current_user={'email': 'abc@invalid.com', 'internal': False, 'accounts': [1]},
                account_id=2,
                account_service=self.__mock_account_service,
            )

        expected_logger_args = (
            'User Email: %s; User has access to accounts: %s; User requested access to account: %s',
            'abc@invalid.com',
            [1],
            2,
        )
        mock_warning_logger.assert_called_once_with(*expected_logger_args)

        self.assertEqual(403, context.exception.status_code)
        self.assertEqual('User does not have access to this account', context.exception.detail)

    async def test_validate_advertiser__internal_user__should_succeed(self):
        result = await validate_advertiser(
            current_user={'internal': True}, advertiser_id=1, advertiser_service=self.__mock_account_service)

        self.__mock_account_service.get_account_by_numeric_id.assert_not_called()

        self.assertTrue(result)

    async def test_validate_advertiser__external_user__should_succeed(self):
        self.__mock_account_service.get_advertiser_by_numeric_id.return_value = CachedAdvertiser(
            brandId='abc123', name='Test', accountId=1, description='Test', active=True)

        result = await validate_advertiser(
            current_user={'internal': False, 'brands': ['abc123'], 'email': 'abc@123.invalid'},
            advertiser_id=1,
            advertiser_service=self.__mock_account_service)

        self.__mock_account_service.get_advertiser_by_numeric_id.assert_called_once_with(1)

        self.assertTrue(result)

    @patch('logging.Logger.warning')
    async def test_validate_advertiser__external_user__advertiser_not_in_user_brands__raises_http_exception_status_403(
        self, mock_warning_logger: MagicMock
    ):
        self.__mock_account_service.get_advertiser_by_numeric_id.return_value = CachedAdvertiser(
            brandId='abc123', name='Test', accountId=1, description='Test', active=True
        )

        with self.assertRaises(HTTPException) as context:
            await validate_advertiser(
                current_user={'email': 'abc@invalid.com', 'internal': False, 'brands': ['123abc']},
                advertiser_id=2,
                advertiser_service=self.__mock_account_service,
            )

        expected_logger_args = (
            'User Email: %s; User has access to brands: %s; User requested access to brand: %s',
            'abc@invalid.com',
            ['123abc'],
            'abc123',
        )
        expected_exception_detail = 'User does not have access to this entity.'

        mock_warning_logger.assert_called_once_with(*expected_logger_args)

        self.assertEqual(403, context.exception.status_code)
        self.assertEqual(expected_exception_detail, context.exception.detail)

    @patch('logging.Logger.error')
    @patch('app.common.utils.jwt.__user_identity_check', new_callable=AsyncMock)
    async def __raises_401_assertions(
            self,
            mock__user_identity_check: AsyncMock,
            mock_error_logger: MagicMock,
            expected_logged_message: str,
            expected_logged_response_content: dict):
        with self.assertRaises(HTTPException) as context:
            await get_user(
                harness_service=self.__mock_harness_service,
                token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g'
                             'RG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJsb2dpbiI6ImFiY0AxMjMuaW52YWxpZCJ9.qrFRMKPk_DS69Xn'
                             'J6XGk01OaUS_YGLNkKZ_mk6qxF0Q',
                ent_client_service=self.__mock_ent_client_service
            )
        mock_error_logger.assert_called_once_with(expected_logged_message, expected_logged_response_content)
        self.assertEqual(401, context.exception.status_code)
        self.assertEqual("Not authorized", context.exception.detail)

    @patch('logging.Logger.warning')
    def __raises_403_assertions(
            self,
            mock_warning_logger: MagicMock,
            function_under_test: callable,
            expected_exception_detail: str,
            expected_logger_args: tuple):
        with self.assertRaises(HTTPException) as context:
            function_under_test()

        mock_warning_logger.assert_called_once_with(*expected_logger_args)

        self.assertEqual(403, context.exception.status_code)
        self.assertEqual(expected_exception_detail, context.exception.detail)