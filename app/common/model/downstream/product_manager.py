from typing import List, Optional

from pydantic import BaseModel

class TaxonomyProperties(BaseModel):
    id: str
    name: str

class Taxonomy(BaseModel):
    department: TaxonomyProperties
    commodity: TaxonomyProperties
    subCommodity: TaxonomyProperties

class Restrictions(BaseModel):
    prohibited: bool
    sensitive: bool
    notRestricted: bool
    notFound: bool

class Product(BaseModel):
    upc: str
    description: str
    isValid: bool
    brand: str
    quantity: Optional[str] = None
    taxonomy: Taxonomy
    restrictions: Optional[Restrictions] = None
    lastSoldDate: Optional[str] = None

class ProductSearchResponse(BaseModel):
    validProducts: List[Product]
    alternateProducts: Optional[List[Product]] = None
    invalidProducts: List[str]

class ProductManagerMetaPage(BaseModel):
    offset: int
    size: int
    totalSize: int

class ProductManagerMeta(BaseModel):
    page: ProductManagerMetaPage
