"""
Repository 패턴 구현

DB 접근 로직을 Repository로 분리하여 관심사 분리
"""
from .base_repository import BaseRepository
from .product_repository import ProductRepository

__all__ = ['BaseRepository', 'ProductRepository']
