from jwt import decode

from app.common.model.attribute_types.token_type import TokenType
from app.common.utils.filtered_logger import get_logger

logger = get_logger(__name__)

def get_auth_header(request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        return auth_header
    return ""

def parse_token_for_client_id(token: str) -> str | None:
    decoded_token: dict = __decode_token(token=token)
    try:
        token_type: TokenType = __determine_token_type(token=token)

        if token_type == TokenType.KONG_ID_TOKEN:
            return decoded_token.get("cid")
        if token_type == TokenType.KODDI_ID_TOKEN:
            return decoded_token.get("cid")
        if token_type == TokenType.KONG_API_TOKEN:
            return decoded_token.get("cid")

        raise AttributeError("Token type not recognized")
    except Exception as err:
        logger.warning(
            "Failed to parse token for client ID: %s",
            err,
            extra={
                'monitored_transaction': 'FAILED-PARSE-TOKEN-FOR-CLIENT-ID',
                'claims': decoded_token
            }
        )
        return None

def parse_token_for_username(token: str) -> str | None:
    decoded_token: dict = __decode_token(token=token)
    try:
        token_type: TokenType = __determine_token_type(token=token)

        if token_type == TokenType.KONG_ID_TOKEN:
            return decoded_token.get("login")
        if token_type == TokenType.KODDI_ID_TOKEN:
            koddi_email = decoded_token.get("email")
            address_top_level_domain = koddi_email.split('.')[-1]
            if '+' in address_top_level_domain:
                return koddi_email[:-4]
            return koddi_email
        if token_type == TokenType.KONG_API_TOKEN:
            return decoded_token.get("cid") + "@8451.com"

        raise AttributeError("Token type not recognized")
    except Exception as err:
        logger.warning(
            "Failed to parse token for username: %s",
            err,
            extra={
                'monitored_transaction': 'FAILED-PARSE-TOKEN-FOR-USERNAME',
                'claims': decoded_token
            }
        )
        return None

def __determine_token_type(token: str) -> TokenType:
    decoded_token = __decode_token(token)

    login_claim = decoded_token.get("login")
    email_claim = decoded_token.get("email")
    cid_claim = decoded_token.get("cid")

    if login_claim:
        return TokenType.KONG_ID_TOKEN
    if email_claim:
        return TokenType.KODDI_ID_TOKEN
    if cid_claim:
        return TokenType.KONG_API_TOKEN

    logger.warning("Token type not recognized",
                   extra={
                       'monitored_transaction': 'UNKNOWN-TOKEN-TYPE',
                       'claims': decoded_token
                   })

    return TokenType.UNKNOWN_TOKEN

def __decode_token(token: str) -> dict:
    try:
        return decode(token, options={"verify_signature": False}, algorithms=["HS256"])
    except Exception as encountered_exception:
        logger.error("Failed to decode token: %s", encountered_exception)
        return {}
