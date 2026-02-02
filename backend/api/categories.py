"""
카테고리 관리 API
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from database.db import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/categories", tags=["categories"])

class CategoryCreate(BaseModel):
    folder_number: int
    folder_name: str
    level1: str
    level2: str
    level3: str
    level4: str

class CategoryUpdate(BaseModel):
    level1: Optional[str] = None
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None

@router.get("/")
async def get_all_categories():
    """전체 카테고리 목록 조회"""
    try:
        db = get_db()
        conn = db.get_connection()
        cursor = conn.execute("""
            SELECT id, folder_number, folder_name, level1, level2, level3, level4, created_at
            FROM categories
            ORDER BY folder_number
        """)
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "categories": categories,
            "total": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/structure")
async def get_category_structure():
    """
    카테고리 계층 구조 조회 (상세페이지 생성기용)
    4단계 계층 구조로 반환
    """
    try:
        db = get_db()
        conn = db.get_connection()
        cursor = conn.execute("""
            SELECT level1, level2, level3, level4, folder_number
            FROM categories
            ORDER BY level1, level2, level3, level4
        """)
        categories = cursor.fetchall()
        conn.close()

        # 계층 구조로 변환
        structure = {}
        for cat in categories:
            level1, level2, level3, level4 = cat['level1'], cat['level2'], cat['level3'], cat['level4']

            if level1 not in structure:
                structure[level1] = {}
            if level2 not in structure[level1]:
                structure[level1][level2] = {}
            if level3 not in structure[level1][level2]:
                structure[level1][level2][level3] = []

            # 중복 방지
            if level4 not in structure[level1][level2][level3]:
                structure[level1][level2][level3].append(level4)

        return {
            "success": True,
            "structure": structure
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/levels")
async def get_category_levels(level1: Optional[str] = None, level2: Optional[str] = None, level3: Optional[str] = None):
    """
    카테고리 계층별 옵션 조회
    """
    try:
        db = get_db()
        conn = db.get_connection()

        if not level1:
            # level1 옵션 반환
            cursor = conn.execute("SELECT DISTINCT level1 FROM categories ORDER BY level1")
            result = [row['level1'] for row in cursor.fetchall()]
            conn.close()
            return {"success": True, "options": result}

        elif level1 and not level2:
            # level2 옵션 반환
            cursor = conn.execute("SELECT DISTINCT level2 FROM categories WHERE level1 = ? ORDER BY level2", (level1,))
            result = [row['level2'] for row in cursor.fetchall()]
            conn.close()
            return {"success": True, "options": result}

        elif level1 and level2 and not level3:
            # level3 옵션 반환
            cursor = conn.execute("SELECT DISTINCT level3 FROM categories WHERE level1 = ? AND level2 = ? ORDER BY level3", (level1, level2))
            result = [row['level3'] for row in cursor.fetchall()]
            conn.close()
            return {"success": True, "options": result}

        else:
            # level4 옵션 반환
            cursor = conn.execute("SELECT DISTINCT level4, folder_number FROM categories WHERE level1 = ? AND level2 = ? AND level3 = ? ORDER BY level4", (level1, level2, level3))
            result = [{"name": row['level4'], "folder_number": row['folder_number']} for row in cursor.fetchall()]
            conn.close()
            return {"success": True, "options": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_category(category: CategoryCreate):
    """새 카테고리 추가"""
    try:
        db = get_db()
        conn = db.get_connection()

        # 폴더 번호 중복 체크
        cursor = conn.execute("SELECT id FROM categories WHERE folder_number = ?", (category.folder_number,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail=f"폴더 번호 {category.folder_number}는 이미 사용 중입니다")

        conn.execute("""
            INSERT INTO categories (folder_number, folder_name, level1, level2, level3, level4)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category.folder_number, category.folder_name, category.level1, category.level2, category.level3, category.level4))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"카테고리 '{category.folder_name}'이(가) 추가되었습니다"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/next-number")
async def get_next_folder_number():
    """다음 폴더 번호 조회 (자동 증가)"""
    try:
        import os
        database_url = os.getenv('DATABASE_URL')

        # 프로덕션: PostgreSQL 직접 연결
        if database_url and os.getenv('ENVIRONMENT') == 'production':
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT MAX(folder_number) as max_num FROM categories")
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            max_number = result['max_num'] if result and result['max_num'] else 0
        else:
            # 로컬 개발: SQLite
            db = get_db()
            conn = db.get_connection()
            cursor = conn.execute("SELECT MAX(folder_number) as max_num FROM categories")
            result = cursor.fetchone()
            conn.close()

            max_number = result['max_num'] if result and result['max_num'] else 0

        next_number = max_number + 1

        return {
            "success": True,
            "next_number": next_number
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distinct-values")
async def get_distinct_category_values():
    """각 카테고리 레벨별 고유값 조회 (드롭다운용)"""
    try:
        db = get_db()
        conn = db.get_connection()

        # 각 레벨별 고유값 조회
        level1_cursor = conn.execute("SELECT DISTINCT level1 FROM categories ORDER BY level1")
        level1_values = [row['level1'] for row in level1_cursor.fetchall()]

        level2_cursor = conn.execute("SELECT DISTINCT level2 FROM categories ORDER BY level2")
        level2_values = [row['level2'] for row in level2_cursor.fetchall()]

        level3_cursor = conn.execute("SELECT DISTINCT level3 FROM categories ORDER BY level3")
        level3_values = [row['level3'] for row in level3_cursor.fetchall()]

        level4_cursor = conn.execute("SELECT DISTINCT level4 FROM categories ORDER BY level4")
        level4_values = [row['level4'] for row in level4_cursor.fetchall()]

        conn.close()

        return {
            "success": True,
            "values": {
                "level1": level1_values,
                "level2": level2_values,
                "level3": level3_values,
                "level4": level4_values
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
