# Model classes for json returned by redis
from typing import List, Optional

from pydantic import BaseModel

from app.common.model.advertiser import AdvertiserType
from app.common.model.division import DivisionServiceResponse
from app.common.model.downstream.product_manager import Taxonomy, Product


class CachedContact(BaseModel):
    """
    Model for Contact serialized json in redis.
    Key: CONTACT:{contact short id}
    Stored in redis with contact short id as the key
    """
    id: Optional[str] = None
    contactType: Optional[AdvertiserType] = None
    accountIds: Optional[List[str]] = None

class CachedAddress(BaseModel):
    """
    Model for Address serialized json in redis.
    Key: ADDRESS:{address short id}
    """
    id: Optional[str] = None
    addressType: Optional[AdvertiserType] = None

class CachedProduct(Product):
    """
    Model for Product serialized json in redis.
    Key: PRODUCT:{entity id}
    """
    upc: Optional[str] = None
    description: Optional[str] = None
    isValid: bool = False
    brand: Optional[str] = None
    taxonomy: Optional[Taxonomy] = None

class CachedAdvertiserClient(BaseModel):
    """
    Model for client inside CachedAdvertiser.
    """
    clientId: Optional[str] = None
    displayName: Optional[str] = None
    salesforceId: Optional[str] = None
    companyType: Optional[str] = None
    nonBillableClient: bool = False
    nonBillable: bool = False

class CachedRedisAdvertiser(BaseModel):
    """
    Model for Advertiser serialized json in redis.
    Key: ADVERTISER:{advertiser short id}
    """
    brandId: Optional[str] = None
    displayName: Optional[str] = None
    salesforceId: Optional[str] = None
    client: Optional[CachedAdvertiserClient] = None

class CachedDivision(DivisionServiceResponse):
    """
    Model for Division serialized json in redis.
    Key: DIVISION:{division short id}
    """
    id: Optional[str] = None
    label: Optional[str] = None
    preselected: bool = False
    disabled: bool = False
    flagged: bool = False
    type: Optional[str] = None
    divisionNumber: Optional[str] = None
    bannerCode: Optional[str] = None

class CachedPlacement(BaseModel):
    """
    Model for Placement serialized json in redis.
    Key: PLACEMENT:{placement short id}
    """
    placementId: Optional[str] = None
    name: Optional[str] = None
    channelShortName: Optional[str] = None
    minimumBidAmount: Optional[float] = None