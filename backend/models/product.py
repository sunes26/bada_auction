from typing import Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class ProductBase(BaseModel):
    """상품 기본 모델"""
    name: str
    price: float
    original_price: Optional[float] = None
    image_url: str
    product_url: str
    source: str  # 'traders', 'ssg', etc.
    category: str
    description: Optional[str] = None
    brand: Optional[str] = None
    in_stock: bool = True


class ProductCreate(ProductBase):
    """상품 생성 모델"""
    pass


class Product(ProductBase):
    """상품 모델 (DB 포함)"""
    id: str
    created_at: datetime
    updated_at: datetime
    margin_rate: Optional[float] = None  # 마진율 (%)
    selling_price: Optional[float] = None  # 판매가 (마진 포함)

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """상품 응답 모델"""
    products: list[Product]
    total: int
    page: int
    page_size: int
