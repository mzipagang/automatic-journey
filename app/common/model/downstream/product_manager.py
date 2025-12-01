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


class ProductCategory(BaseModel):
    """
    Product category for a product selection.
    """
    type: str
    productIds: List[str]


class ProductSelection(BaseModel):
    """
    Response for getting a product selection.
    """
    id: str
    categories: List[ProductCategory]


class ProductSnapshot(BaseModel):
    """
    Response for getting a product snapshot.
    """
    id: str
    productIds: List[str]
    productGroupId: str


class CreateProductSelection(BaseModel):
    """
    Request data for creating a product selection.
    """
    categories: List[ProductCategory]

    @staticmethod
    def from_upcs(upcs: List[str]):
        return CreateProductSelection(
            categories=[ProductCategory(type="products", productIds=upcs)]
        )


class CreateProductSelectionParams(BaseModel):
    """
    Request parameters for creating a product selection.
    """
    enforceProductGroupCreationValidation: bool


class CreateProductSnapshot(BaseModel):
    """
    Request data for creating a product snapshot.
    """
    id: str
