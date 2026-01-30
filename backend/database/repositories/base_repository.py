"""
Base Repository 클래스

모든 Repository의 기본 클래스로 공통 CRUD 로직 제공
"""
import sqlite3
from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """모든 Repository의 기본 클래스"""

    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path

    @abstractmethod
    def get_table_name(self) -> str:
        """테이블 이름 반환 (서브클래스에서 구현 필요)"""
        pass

    def get_connection(self):
        """DB 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_by_id(self, id: int) -> Optional[Dict]:
        """ID로 레코드 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.get_table_name()} WHERE id = ?", (id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """전체 레코드 조회 (페이징)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {self.get_table_name()}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """전체 레코드 수 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {self.get_table_name()}")
            return cursor.fetchone()['count']

    def delete(self, id: int) -> bool:
        """레코드 삭제"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.get_table_name()} WHERE id = ?", (id,))
            conn.commit()
            return cursor.rowcount > 0

    def exists(self, id: int) -> bool:
        """레코드 존재 여부 확인"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {self.get_table_name()} WHERE id = ? LIMIT 1", (id,))
            return cursor.fetchone() is not None
