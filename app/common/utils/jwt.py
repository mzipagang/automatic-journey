from typing import List

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.common.context.context import user_context
from app.common.context.context_vars import UserContextVarNames
from app.common.decorators.decorators import conditionally_execute
from app.common.gateways.ent_client_service_gateway import EntClientServiceGateway
from app.common.model.downstream.ent_client_service import ApiUserDetails, ApiUserResponse
from app.common.model.harness_feature_flags import HarnessFeatureFlags
from app.common.services.config_service import ConfigService
from app.common.services.harness_service import HarnessService
from app.common.utils import filtered_logger
from app.common.utils.token_tools import parse_token_for_username

current_config = ConfigService().get_current_config()
logger = filtered_logger.get_logger(__name__)

oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="auth", tokenUrl="token")


def __api_user_check(
        user: ApiUserDetails,
        harness_service: HarnessService
) -> bool:
    flag_on = harness_service.is_harness_flag_on(
        HarnessFeatureFlags.ALLOW_AUTH_FROM_API_CONSUMER,
        current_config.pte_target_id
    )
    return flag_on and user.consumer

async def get_user(
        harness_service: HarnessService = Depends(HarnessService),
        token: str = Depends(oauth2_scheme),
        ent_client_service: EntClientServiceGateway = Depends(EntClientServiceGateway)
) -> ApiUserResponse:
    logger.debug('get_user started')
    user = await ent_client_service.get_user()
    api_user_result = __api_user_check(user=user.data, harness_service=harness_service)
    if not api_user_result:
        await __user_identity_check(user.data, token)

    if user.data.active or api_user_result:
        return user

    logger.error("Get User Response: %s", user.model_dump())
    raise HTTPException(status_code=401, detail='Not authorized')

async def validate_user(
        user: ApiUserResponse=Depends(get_user),
        harness_service: HarnessService = Depends(HarnessService),
        ent_client_service: EntClientServiceGateway = Depends(EntClientServiceGateway),
        token: str = Depends(oauth2_scheme)
):
    permissions = await ent_client_service.get_api_access()

    is_internal = permissions.data.hasAccessToAllAccounts
    is_agency = permissions.data.worksFor.type == 'BROKER_OR_AGENCY'
    accounts = []
    brands = []
    unknown_accounts = []

    if not is_internal:
        for account in permissions.data.accountList:
            if account.type == 'BRAND':
                brands.append(account.id)
            elif account.type == 'CPG':
                accounts.append(account.id)
            else:
                unknown_accounts.append(f"{account.id} - {account.name} - {account.type}")
        if unknown_accounts:
            logger.warning("Unknown account types: %s", unknown_accounts)

    if not __api_user_check(user=user.data, harness_service=harness_service):
        await __user_identity_check(user.data, token)
        return {
            'email': user.data.email,
            'works_for': permissions.data.worksFor.model_dump(),
            'is_agency': is_agency,
            'internal': is_internal,
            'accounts': accounts,
            'brands': brands
        }

    # This is still POC-level code to discover interactions with upstream services other than
    # ID+ services. It will be refactored and moved to a more appropriate location in the future.
    system_email = f"{user.data.clientId}@8451.com"
    logger.info('user is api consumer; system email set to %s', system_email)

    return {
            'works_for': permissions.data.worksFor.model_dump(),
            'is_agency': is_agency,
            'internal': is_internal,
            'accounts': accounts,
            'brands': brands,
            'email': system_email
        }


async def validate_account(current_user: dict, account_id: int, account_service: Depends):
    if current_user['internal'] is False:
        internal_account_id = await account_service.get_account_by_numeric_id(account_id)
        if internal_account_id not in current_user['accounts']:
            logger.warning("User Email: %s; User has access to accounts: %s; User requested access to account: %s",
                           current_user['email'], current_user['accounts'], internal_account_id)
            raise HTTPException(status_code=403, detail='User does not have access to this account')
    return True


async def validate_advertiser(current_user: dict, advertiser_id: int, advertiser_service: Depends):
    if current_user['internal'] is False:
        cached_advertiser_record = await advertiser_service.get_advertiser_by_numeric_id(advertiser_id)
        if cached_advertiser_record.brandId not in current_user['brands']:
            logger.warning("User Email: %s; User has access to brands: %s; User requested access to brand: %s",
                           current_user['email'], current_user['brands'], cached_advertiser_record.brandId)
            raise HTTPException(status_code=403, detail='User does not have access to this entity.')
    return True


async def validate_advertisers(current_user: dict, advertiser_ids: List[int], advertiser_service: Depends):
    if current_user['internal'] is False:
        cached_advertiser_records = await advertiser_service.get_advertisers_by_numeric_ids(advertiser_ids)
        for cached_advertiser_record in cached_advertiser_records:
            if cached_advertiser_record.brandId not in current_user['brands']:
                logger.warning("User Email: %s; User has access to brands: %s; User requested access to brand: %s",
                               current_user['email'], current_user['brands'], cached_advertiser_record.brandId)
    return True

@conditionally_execute(flag_name=HarnessFeatureFlags.SKIP_INTERNAL_IDENTITY_CHECK,
                       default_method=lambda *args, **kwargs: False)
def __internal_user(id_token_email: str, get_user_email: str, user_context_email: str) -> bool:
    if all(
        email_address.split('@')[1] == '8451.COM'
        for email_address in [id_token_email, get_user_email, user_context_email]
    ):
        logger.info("SKIPPING CHECK FOR INTERNAL USER",
                    extra={
                        'get_user_email': get_user_email,
                        'id_token_email': id_token_email,
                        'context_email': user_context_email,
                        'monitored_transaction': 'INTERNAL-EMAIL-SKIPPING-USER-IDENTITY-CHECK'
                    })
        return True
    return False

async def noop(*args, **kwargs):
    pass
@conditionally_execute(flag_name=HarnessFeatureFlags.IDENTITY_CHECK_ENABLED, default_method=noop)
async def __user_identity_check(user: ApiUserDetails, token: str) -> None:
    try:
        id_token_email = parse_token_for_username(token=token).upper()
        get_user_email = user.email.upper()
        user_context_email = user_context.get().get(UserContextVarNames.USERNAME.value).upper()

        if not __internal_user(id_token_email, get_user_email, user_context_email):
            if not (id_token_email == get_user_email and get_user_email == user_context_email):
                logger.error(
                    "User Email: %s; User Email from token: %s; User Email from user context: %s",
                    get_user_email, id_token_email, user_context_email,
                    extra={
                        'email': get_user_email,
                        'token_email': id_token_email,
                        'context_email': user_context_email,
                        'monitored_transaction': 'EMAIL-MISMATCH'
                    }
                )
                raise HTTPException(
                    status_code=503,
                    detail='Auth call error.  Please retry.',
                    headers={"Retry-After": "5"}
                )
    except AttributeError as err:
        logger.error("Problem with user identity check: %s", err,
                     extra={'monitored_transaction': 'USER-IDENTITY-CHECK-FAILURE'})
        raise HTTPException(
            status_code=500,
            detail='Internal error.  Please retry.',
            headers={"Retry-After": "5"}
        ) from err
