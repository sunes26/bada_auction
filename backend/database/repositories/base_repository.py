"""
Base Repository 클래스

모든 Repository의 기본 클래스로 공통 CRUD 로직 제공
(PostgreSQL/SQLite 자동 선택)
"""
import os
from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """모든 Repository의 기본 클래스"""

    def __init__(self):
        # database_manager를 사용하여 PostgreSQL/SQLite 자동 선택
        from database.database_manager import get_database_manager
        self.db_manager = get_database_manager()
        self.is_postgresql = self.db_manager.is_postgresql

    @abstractmethod
    def get_table_name(self) -> str:
        """테이블 이름 반환 (서브클래스에서 구현 필요)"""
        pass

    def get_connection(self):
        """DB 연결 반환 (raw connection)"""
        return self.db_manager.engine.raw_connection()

    def get_placeholder(self) -> str:
        """SQL placeholder 반환 (PostgreSQL: %s, SQLite: ?)"""
        return "%s" if self.is_postgresql else "?"

    def get_by_id(self, id: int) -> Optional[Dict]:
        """ID로 레코드 조회"""
        placeholder = self.get_placeholder()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.get_table_name()} WHERE id = {placeholder}", (id,))
            row = cursor.fetchone()
            if row:
                # Convert to dict (works for both sqlite3.Row and psycopg2 RealDictRow)
                if hasattr(row, 'keys'):
                    return {key: row[key] for key in row.keys()}
                return dict(row)
            return None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """전체 레코드 조회 (페이징)"""
        placeholder = self.get_placeholder()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {self.get_table_name()}
                ORDER BY created_at DESC
                LIMIT {placeholder} OFFSET {placeholder}
            """, (limit, offset))
            rows = cursor.fetchall()
            # Convert to list of dicts
            result = []
            for row in rows:
                if hasattr(row, 'keys'):
                    result.append({key: row[key] for key in row.keys()})
                else:
                    result.append(dict(row))
            return result

    def count(self) -> int:
        """전체 레코드 수 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {self.get_table_name()}")
            row = cursor.fetchone()
            if hasattr(row, 'keys'):
                return row['count']
            return row[0]

    def delete(self, id: int) -> bool:
        """레코드 삭제"""
        placeholder = self.get_placeholder()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.get_table_name()} WHERE id = {placeholder}", (id,))
            conn.commit()
            return cursor.rowcount > 0

    def exists(self, id: int) -> bool:
        """레코드 존재 여부 확인"""
        placeholder = self.get_placeholder()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {self.get_table_name()} WHERE id = {placeholder} LIMIT 1", (id,))
            return cursor.fetchone() is not None
