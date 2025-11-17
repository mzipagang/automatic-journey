from typing import List

from pydantic import BaseModel, Field

from app.common.model.shared import Meta


class Product(BaseModel):
    id: int = Field(default=0, title="id", description='Id of the product.')
    upc: str = Field(default=None, title="upc", description='UPC of the product.')
    name: str = Field(default=None, title="name", description='Name of the product.')
    packshot: str = Field(default=None, title="packshot", description='Default image URL of the product.')
    price: float = Field(default=None, title="price", description='Price of the product.')
    maxSuggestedBid: float = Field(default=None, title="maxSuggestedBid", description='Max suggested bid for the product.')
    minSuggestedBid: float = Field(default=None, title="minSuggestedBid", description='Min suggested bid for the product.')
    brand: str = Field(default=None, title="brand", description='Brand name of the product.')
    category: str = Field(default=None, title="category", description='Category of the product.')
    subcategory: str = Field(default=None, title="subcategory", description='Subcategory of the product.')
    available: bool = Field(default=None, title="available", description='Whether the product is available.')


class ProductResponse(BaseModel):
    data: List[Product] = Field(title="data", description="List of Products.")
    meta: Meta = Field(title="meta", description="Response metadata.")
