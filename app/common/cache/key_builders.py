from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.common.context.context import user_context, request_context
from app.common.context.context_vars import RequestContextVarNames, UserContextVarNames
from app.common.utils.filtered_logger import get_logger

logger = get_logger(__name__)

def user_roles_key_builder(
        func, namespace: str="", request: Request = None, response: Response = None, *args, **kwargs) -> str:
    __use_arguments("user_roles_key_builder",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)
    username = __prep_user_context_key_substring()
    return f"{namespace}:roles:{username}"

def account_address_and_contacts_key_builder(
        func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs) -> str:

    __use_arguments("account_address_and_contacts_key_builder",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)

    username = __prep_user_context_key_substring()
    return ":".join([
        namespace,
        username,
        "account_address_and_contacts"])


def account_by_internal_id_key_builder(
        func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs) -> str:

    __use_arguments("account_by_internal_id_key_builder",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)
    username = __prep_user_context_key_substring()
    incoming_request_path = request_context.get().get(RequestContextVarNames.PATH.value)
    params_string = __prep_request_params_key_substring()

    return ":".join([
        namespace,
        incoming_request_path,
        params_string,
        username,
        "account_by_internal_id"])


def get_advertisers_upstream_key_builder(
        func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs) -> str:

    __use_arguments("get_advertisers_upstream_key_builder",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)

    username = __prep_user_context_key_substring()
    incoming_request_path = request_context.get().get(RequestContextVarNames.PATH.value)
    params_string = __prep_request_params_key_substring()

    return ":".join([
        namespace,
        incoming_request_path,
        params_string,
        username,
        "get_advertisers_upstream"])


def get_contacts_by_id_upstream_key_builder(
        func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs) -> str:

    __use_arguments("get_contacts_by_id_upstream_key_builder",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)

    username = __prep_user_context_key_substring()
    incoming_request_path = request_context.get().get(RequestContextVarNames.PATH.value)
    params_string = __prep_request_params_key_substring()

    return ":".join([
        namespace,
        incoming_request_path,
        params_string,
        username,
        "get_contacts_by_id_upstream"])


def get_addresses_by_account__upstream_key_builder(
        func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs) -> str:

    __use_arguments("get_addresses_by_account__upstream_key_builder",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)

    username = __prep_user_context_key_substring()
    incoming_request_path = request_context.get().get(RequestContextVarNames.PATH.value)
    params_string = __prep_request_params_key_substring()

    return ":".join([
        namespace,
        incoming_request_path,
        params_string,
        username,
        "get_addresses_by_account__upstream"]
)


def validate_user__upstream_key_builder(
        func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs) -> str:

    __use_arguments("validate_user__upstream_key_builder",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)

    username = __prep_user_context_key_substring()

    return ":".join([
        namespace,
        username,
        "validate_user__upstream"])


def get_user__upstream_key_builder_c2(
        func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs) -> str:

    __use_arguments("get_user__upstream_key_builder_c2",
                    *args,
                    func=func,
                    namespace=namespace,
                    request=request,
                    response=response,
                    **kwargs)

    username = __prep_user_context_key_substring()

    return ":".join([
        namespace,
        username,
        "get_user__upstream_c2"])


def __prep_user_context_key_substring() -> str:
    if the_user_context := user_context.get():
        if the_user := the_user_context.get(UserContextVarNames.USERNAME.value):
            return the_user
        logger.error(
                "Username is empty during cache key generation",
                extra={
                    "tracked_error_transaction": "cache_key_generation__empty_username",
                    "error_context": {
                        "key_builder_name": "get_advertisers_upstream_key_builder",
                        "user_context": the_user_context
                    }
                })
    else:
        logger.error(
            "User context is empty during cache key generation",
            extra={
                "tracked_error_transaction": "cache_key_generation__empty_user_context",
                "error_context": {
                    "key_builder_name": "get_advertisers_upstream_key_builder",
                    "user_context": the_user_context
                }
            })

    raise HTTPException(status_code=503, detail="C-K-G_ERROR.  Please retry.", headers={"Retry-After": "5"})


def __prep_request_params_key_substring() -> str:
    the_request_context = request_context.get()
    sorted_params = sorted(the_request_context.get(RequestContextVarNames.PARAMS.value).items())
    params_string = "--".join(f"{k}-{v}" for k, v in sorted_params)

    return params_string

def __use_arguments(*args, **kwargs) -> None:
    logger.debug("%s", " ".join([str(arg) for arg in args]), extra={**kwargs})
