from enum import StrEnum


class TokenType(StrEnum):
    KONG_ID_TOKEN = "kong_id_token"
    KONG_API_TOKEN = "kong_api_token"
    KODDI_ID_TOKEN = "koddi_id_token"
    UNKNOWN_TOKEN = "unknown_token"
