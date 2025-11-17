from typing import List, Optional

from pydantic import BaseModel

class Brand(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None

class Agency(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None

class KoddiRole(BaseModel):
    additionalProp1: Optional[str] = None
    additionalProp2: Optional[str] = None
    additionalProp3: Optional[str] = None

class UserKoddiRoleMapping(BaseModel):
    empId: Optional[str] = None
    koddiId: Optional[int] = None
    empRoles: Optional[List[str]] = None
    koddiRoles: Optional[KoddiRole] = None

class EntitiesFilter(BaseModel):
    field: Optional[str] = None
    operation: Optional[str] = None
    or_group: Optional[str] = None

class KoddiAdvertiserMultiBrand(BaseModel):
    brandId: Optional[str] = None
    primary: Optional[bool] = None
    percentage: Optional[float] = None

class KoddiAdvertiserMultiBrandRequest(BaseModel):
    brandItemRequests: Optional[List[KoddiAdvertiserMultiBrand]] = None
    agencyId: Optional[str] = None

class KoddiAdvertiserResponse(BaseModel):
    id: Optional[int] = None
    brandItemRequests: Optional[List[KoddiAdvertiserMultiBrand]] = None
    agencyId: Optional[str] = None
    brands: Optional[List[Brand]] = None
    agency: Optional[Agency] = None
    primaryBrandId: Optional[str] =None
    upcsAndSubCommodityIds: Optional[List[str]] = None
    userEmpKoddiRoleMappings : Optional[List[UserKoddiRoleMapping]] = None
    entitiesFilters: Optional[List[EntitiesFilter]] = None
    upcs: Optional[List[str]] = None
    subCommodityIds: Optional[List[str]] = None
    upcUpToDate: Optional[bool] = None
    subCommodityIdUpToDate: Optional[bool] = None

class KoddiBrandResponse(BaseModel):
    koddiId: int
    agencyId: Optional[str] = None
    brandIds: Optional[List[str]] = None
    primaryBrandId: Optional[str] = None
    percentages: Optional[float] = None
