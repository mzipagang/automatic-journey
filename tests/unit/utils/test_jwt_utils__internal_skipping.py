from fastapi.exceptions import HTTPException
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, call, AsyncMock

import pytest

from app.common.context.context import user_context
from app.common.model.downstream.ent_client_service import ApiUserResponse, \
    ApiAccessResponse, WorksFor
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.utils.jwt import validate_user
from tests.utils_for_testing.utils import encode_dict_as_jwt


@patch('app.common.services.harness_service.HarnessService.is_harness_flag_on', return_value=True)
@patch('app.common.services.harness_service.HarnessService.fetch_multivariate_flag',
       return_value={'enabled': False, 'ttl': 0})
@patch('app.common.utils.jwt.__api_user_check')
@patch('logging.Logger.error')
class TestJwtUtilsInternalSkipping(IsolatedAsyncioTestCase):
    __mock_internal_http_client_service: MagicMock
    __mock_config_service: MagicMock
    __mock_harness_service: MagicMock

    def setUp(self):
        self.__mock_internal_http_client_service = MagicMock()
        self.__mock_config_service = MagicMock()
        self.__mock_ent_client_service = AsyncMock()
        self.__mock_harness_service = MagicMock()

    async def __8451_users_assertions(
            self,
            mock_error_logger: MagicMock,
            mock_api_user_check: MagicMock,

    ):

        pass

    @pytest.mark.asyncio
    async def test_validate_user__8451_user__should_skip_user_identity_check(
            self,
            mock_error_logger: MagicMock,
            mock_api_user_check: MagicMock,
            mock_harness_fetch_multi: MagicMock,
            mock_harness_service_flag_on: MagicMock):

        mock_api_user_check.return_value = False
        user_context.set({'username': 'u84579@8451.com'})
        token = encode_dict_as_jwt({'login': 'u84579@8451.com'})


        self.__mock_harness_service.is_harness_flag_on.return_value = True
        self.__mock_ent_client_service.get_api_access.return_value = ApiAccessResponse(
            **{
                'data': {
                    'email': 'a_user@8451.com',
                    'worksFor': {'clientId': None, 'displayName': None, 'type': 'INTERNAL'},
                    'is_agency': False,
                    'internal': True,
                    'accounts': [],
                    'brands': [],
                    'hasAccessToAllAccounts': True
            }})

        expected: dict = {
            'email': 'a_user@8451.com',
            'works_for': {'clientId': None, 'displayName': None, 'type': 'INTERNAL'},
            'is_agency': False,
            'internal': True,
            'accounts': [],
            'brands': []
        }

        result = await validate_user(
            user=ApiUserResponse(**{"data":{'email': 'a_user@8451.com'}}),
            harness_service=self.__mock_harness_service,
            ent_client_service=self.__mock_ent_client_service,
            token=token)

        self.assertEqual(expected, result)

        mock_error_logger.assert_not_called()
        mock_harness_service_flag_on.assert_has_calls(
            [call(HarnessFeatureFlags.IDENTITY_CHECK_ENABLED, 'default')]
        )


    @pytest.mark.asyncio
    async def test_validate_user__8451_user__non_8451_token_user__should_fail(
            self,
            mock_error_logger: MagicMock,
            mock_api_user_check: MagicMock,
            mock_harness_fetch_multi: MagicMock,
            mock_harness_service_flag_on: MagicMock
    ):
        mock_api_user_check.return_value = False
        user_context.set({'username': 'non_8451_user@2037.com'})
        token = encode_dict_as_jwt({'login': 'non_8451_user@2037.com'})

        self.__mock_harness_service.is_harness_flag_on.return_value = True

        with self.assertRaises(HTTPException) as context:
            await validate_user(
                user=ApiUserResponse(**{"data":{'email': 'n8456@8451.com'}}),
                harness_service=self.__mock_harness_service,
                ent_client_service=self.__mock_ent_client_service,
                token=token)

        self.assertEqual('Auth call error.  Please retry.', context.exception.detail)
        self.assertEqual(503, context.exception.status_code)
        self.assertEqual({'Retry-After': '5'}, context.exception.headers)

        mock_error_logger.assert_has_calls(
            [call('User Email: %s; User Email from token: %s; User Email from user context: %s',
                  'N8456@8451.COM', 'NON_8451_USER@2037.COM', 'NON_8451_USER@2037.COM',
                    extra={
                        'email': 'N8456@8451.COM',
                        'token_email': 'NON_8451_USER@2037.COM',
                        'context_email': 'NON_8451_USER@2037.COM',
                        'monitored_transaction': 'EMAIL-MISMATCH'
                    })]
        )

        mock_harness_service_flag_on.assert_has_calls(
            [call(HarnessFeatureFlags.IDENTITY_CHECK_ENABLED, 'default')]
        )