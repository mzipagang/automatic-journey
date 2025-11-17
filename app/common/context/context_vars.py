from enum import StrEnum


class UserContextVarNames(StrEnum):
    USERNAME = "username"

class RequestContextVarNames(StrEnum):
    PATH = "path"
    PARAMS = "params"

class SecurityContextVarNames(StrEnum):
    USERNAME = "username"
    ID_TOKEN = "id_token"
