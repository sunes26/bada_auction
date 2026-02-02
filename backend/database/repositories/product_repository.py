"""
Product Repository

상품 관련 DB 접근 전용 클래스

⚠️ WARNING: This repository is currently NOT USED in production code.
All methods use SQLite-style placeholders (?) that need to be updated
to use self.get_placeholder() for PostgreSQL compatibility when this
class is actually used.
"""
from .base_repository import BaseRepository
from typing import Optional, List, Dict
from datetime import datetime


class ProductRepository(BaseRepository):
    """
    상품 관련 DB 접근 전용 클래스

    ⚠️ NOT CURRENTLY USED - placeholder (?) needs PostgreSQL compatibility fixes
    """

    def get_table_name(self) -> str:
        return "monitored_products"

    def create(self, product_data: Dict) -> int:
        """
        상품 생성

        Args:
            product_data: 상품 정보 딕셔너리

        Returns:
            생성된 상품 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO monitored_products (
                    source, product_url, product_name, sourcing_product_name,
                    current_price, selling_price, category, thumbnail,
                    is_active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_data.get('source'),
                product_data.get('product_url'),
                product_data.get('product_name'),
                product_data.get('sourcing_product_name'),
                product_data.get('current_price'),
                product_data.get('selling_price'),
                product_data.get('category'),
                product_data.get('thumbnail'),
                product_data.get('is_active', True),
                datetime.now()
            ))
            conn.commit()
            return cursor.lastrowid

    def update_price(self, product_id: int, new_price: float) -> bool:
        """
        상품 가격 업데이트

        Args:
            product_id: 상품 ID
            new_price: 새로운 가격

        Returns:
            업데이트 성공 여부
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE monitored_products
                SET current_price = ?, last_checked = ?, updated_at = ?
                WHERE id = ?
            """, (new_price, datetime.now(), datetime.now(), product_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_status(self, product_id: int, is_active: bool) -> bool:
        """
        상품 활성화 상태 업데이트

        Args:
            product_id: 상품 ID
            is_active: 활성화 여부

        Returns:
            업데이트 성공 여부
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE monitored_products
                SET is_active = ?, updated_at = ?
                WHERE id = ?
            """, (is_active, datetime.now(), product_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_active_products(self) -> List[Dict]:
        """활성 상품만 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM monitored_products
                WHERE is_active = 1
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_by_source(self, source: str) -> List[Dict]:
        """
        소싱처별 상품 조회

        Args:
            source: 소싱처 (ssg, 11st, gmarket 등)

        Returns:
            상품 목록
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM monitored_products
                WHERE source = ?
                ORDER BY created_at DESC
            """, (source,))
            return [dict(row) for row in cursor.fetchall()]

    def search(self, keyword: str) -> List[Dict]:
        """
        상품명으로 검색

        Args:
            keyword: 검색 키워드

        Returns:
            검색 결과 목록
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM monitored_products
                WHERE product_name LIKE ? OR sourcing_product_name LIKE ?
                ORDER BY created_at DESC
            """, (f'%{keyword}%', f'%{keyword}%'))
            return [dict(row) for row in cursor.fetchall()]

    def get_price_history(self, product_id: int, limit: int = 30) -> List[Dict]:
        """
        가격 이력 조회

        Args:
            product_id: 상품 ID
            limit: 조회 개수

        Returns:
            가격 이력 목록
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM price_history
                WHERE product_id = ?
                ORDER BY checked_at DESC
                LIMIT ?
            """, (product_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def add_price_history(self, product_id: int, price: float, status: str):
        """
        가격 이력 추가

        Args:
            product_id: 상품 ID
            price: 가격
            status: 상태 (available, out_of_stock 등)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO price_history (product_id, price, status, checked_at)
                VALUES (?, ?, ?, ?)
            """, (product_id, price, status, datetime.now()))
            conn.commit()

    def get_products_with_low_margin(self, margin_threshold: float = 10.0) -> List[Dict]:
        """
        낮은 마진율 상품 조회 (역마진 포함)

        Args:
            margin_threshold: 마진율 임계값 (기본 10%)

        Returns:
            낮은 마진율 상품 목록
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT *,
                    (selling_price - current_price) as margin,
                    CASE
                        WHEN selling_price > 0 THEN ((selling_price - current_price) / selling_price * 100)
                        ELSE 0
                    END as margin_percent
                FROM monitored_products
                WHERE is_active = 1
                    AND current_price IS NOT NULL
                    AND selling_price IS NOT NULL
                HAVING margin_percent < ?
                ORDER BY margin_percent ASC
            """, (margin_threshold,))
            return [dict(row) for row in cursor.fetchall()]
