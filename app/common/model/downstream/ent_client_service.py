from typing import List, Optional

from pydantic import BaseModel

# https://github.com/8451LLC/ent-client-service/blob/main/src/main/java/com/effo/client/dto/BasicClientDetailsDto.java#L12
class BasicClientDetails(BaseModel):
    clientId: Optional[str] = None
    displayName: Optional[str] = None
    salesforceId: Optional[str] = None
    type: Optional[str] = None
    companyType: Optional[str] = None

# https://github.com/8451LLC/ent-client-service/blob/main/src/main/java/com/effo/client/dto/ProductAccessDto.java#L13
class ProductAccess(BaseModel):
    client: Optional[BasicClientDetails] = None
    roles: Optional[List[str]] = []
    permissions: Optional[List[str]] = []

# https://github.com/8451LLC/ent-client-service/blob/main/src/main/java/com/effo/client/dto/UserPermissionsDto.java#L13
class UserPermissions(BaseModel):
    userId: Optional[str] = None
    permissions: Optional[List[ProductAccess]] = []

# https://github.com/8451LLC/ent-client-service/blob/main/src/main/java/com/effo/client/dto/PaginationMetaDto.java#L13
class PaginationMeta(BaseModel):
    totalCount: Optional[int] = 0
    offset: Optional[int] = 0
    size: Optional[int] = 0

# https://github.com/8451LLC/ent-client-service/blob/main/src/main/java/com/effo/client/dto/WorksForDto.java#L11
class WorksFor(BaseModel):
    displayName: Optional[str] = None
    clientId: Optional[str] = None
    type: Optional[str] = None

class WorksFoAccount(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None

# https://github.com/8451LLC/ent-client-service/blob/main/src/main/java/com/effo/client/dto/AuthDto.java#L19
class Auth(BaseModel):
    clientId: Optional[str] = None
    displayName: Optional[str] = None
    internalUser: Optional[bool] = False
    personId: Optional[str] = None
    worksFor: Optional[WorksFor] = None

# https://github.com/8451LLC/ent-client-service/blob/main/src/main/java/com/effo/client/dto/MetaDto.java#L16
class EntClientServiceMeta(BaseModel):
    page: Optional[PaginationMeta] = None
    auth: Optional[Auth] = None
    allAccountsAccess: Optional[bool] = False
    internalUser: Optional[bool] = False

class ApiUserDetails(BaseModel):
    id: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    jobArea: Optional[str] = None
    active: Optional[bool] = None
    uniqueId: Optional[str] = None
    consumer: Optional[dict] = None
    clientId: Optional[str] = None
    worksFor: Optional[WorksFoAccount] = None

class ApiUserResponse(BaseModel):
    data: Optional[ApiUserDetails] = None
    meta: Optional[EntClientServiceMeta] = None

class AccountListItem(BaseModel):
    type: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None

class ApiAccessDetails(BaseModel):
    worksFor: Optional[WorksFor] = None
    hasAccessToAllAccounts: Optional[bool] = None
    accountList: Optional[list[AccountListItem]] = None

class ApiAccessResponse(BaseModel):
    data: Optional[ApiAccessDetails] = None
    meta: Optional[EntClientServiceMeta] = None


class Address(BaseModel):
    addressLines: Optional[List[str]] = []
    cityTown: Optional[str] = None
    stateProvince: Optional[str] = None
    postalCode: Optional[str] = None
    countryCode: Optional[str] = None

class ContactRoleGroup(BaseModel):
    type: Optional[str] = None
    displayName: Optional[str] = None

class Contact(BaseModel):
    contactId: Optional[str] = None
    clientId: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    emailAddress: Optional[str] = None
    worksFor: Optional[WorksFor] = None
    address: Optional[Address] = None
    roleType: Optional[ContactRoleGroup] = None
