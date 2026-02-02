"""
카테고리-PlayAuto 매핑 관리 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.database_manager import get_database_manager
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["category-playauto-mappings"])


class CategoryPlayautoMapping(BaseModel):
    """카테고리-PlayAuto 매핑 모델"""
    id: Optional[int] = None
    our_category: str
    sol_cate_no: int
    playauto_category: Optional[str] = None
    similarity: Optional[str] = None


class CategoryPlayautoMappingCreate(BaseModel):
    """카테고리-PlayAuto 매핑 생성 모델"""
    our_category: str
    sol_cate_no: int
    playauto_category: Optional[str] = None
    similarity: Optional[str] = None


class CategoryPlayautoMappingUpdate(BaseModel):
    """카테고리-PlayAuto 매핑 수정 모델"""
    sol_cate_no: int
    playauto_category: Optional[str] = None
    similarity: Optional[str] = None


def get_db_connection():
    """DB 연결 (SQLite 및 PostgreSQL 지원)"""
    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    return conn, db_manager.is_sqlite


def dict_from_row(cursor, row):
    """DB row를 dict로 변환"""
    if row is None:
        return None
    return {cursor.description[i][0]: row[i] for i in range(len(cursor.description))}


@router.get("/category-playauto-mappings", response_model=List[CategoryPlayautoMapping])
async def get_all_mappings():
    """
    모든 카테고리-PlayAuto 매핑 조회
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, our_category, sol_cate_no, playauto_category, similarity
            FROM category_playauto_mapping
            ORDER BY our_category
        """)

        mappings = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(cursor, row)
            mappings.append({
                "id": row_dict["id"],
                "our_category": row_dict["our_category"],
                "sol_cate_no": row_dict["sol_cate_no"],
                "playauto_category": row_dict["playauto_category"],
                "similarity": row_dict["similarity"]
            })

        conn.close()

        logger.info(f"[PlayAuto 카테고리 매핑] {len(mappings)}개 매핑 조회")
        return mappings

    except Exception as e:
        logger.error(f"[PlayAuto 카테고리 매핑] 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category-playauto-mappings/{mapping_id}", response_model=CategoryPlayautoMapping)
async def get_mapping(mapping_id: int):
    """
    특정 매핑 조회
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        placeholder = "?" if is_sqlite else "%s"
        cursor.execute(f"""
            SELECT id, our_category, sol_cate_no, playauto_category, similarity
            FROM category_playauto_mapping
            WHERE id = {placeholder}
        """, (mapping_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다")

        row_dict = dict_from_row(cursor, row)
        return {
            "id": row_dict["id"],
            "our_category": row_dict["our_category"],
            "sol_cate_no": row_dict["sol_cate_no"],
            "playauto_category": row_dict["playauto_category"],
            "similarity": row_dict["similarity"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PlayAuto 카테고리 매핑] 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/category-playauto-mappings", response_model=CategoryPlayautoMapping)
async def create_mapping(mapping: CategoryPlayautoMappingCreate):
    """
    새 매핑 추가
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        # 중복 체크
        placeholder = "?" if is_sqlite else "%s"
        cursor.execute(
            f"SELECT id FROM category_playauto_mapping WHERE our_category = {placeholder}",
            (mapping.our_category,)
        )
        if cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"'{mapping.our_category}' 카테고리는 이미 매핑되어 있습니다"
            )

        # 삽입
        if is_sqlite:
            cursor.execute("""
                INSERT INTO category_playauto_mapping
                (our_category, sol_cate_no, playauto_category, similarity)
                VALUES (?, ?, ?, ?)
            """, (mapping.our_category, mapping.sol_cate_no,
                  mapping.playauto_category, mapping.similarity))
        else:
            cursor.execute("""
                INSERT INTO category_playauto_mapping
                (our_category, sol_cate_no, playauto_category, similarity)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (mapping.our_category, mapping.sol_cate_no,
                  mapping.playauto_category, mapping.similarity))

        conn.commit()
        mapping_id = cursor.lastrowid if is_sqlite else cursor.fetchone()[0]
        conn.close()

        logger.info(f"[PlayAuto 카테고리 매핑] 새 매핑 추가: {mapping.our_category} -> {mapping.sol_cate_no}")

        return {
            "id": mapping_id,
            "our_category": mapping.our_category,
            "sol_cate_no": mapping.sol_cate_no,
            "playauto_category": mapping.playauto_category,
            "similarity": mapping.similarity
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PlayAuto 카테고리 매핑] 추가 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/category-playauto-mappings/{mapping_id}", response_model=CategoryPlayautoMapping)
async def update_mapping(mapping_id: int, mapping: CategoryPlayautoMappingUpdate):
    """
    매핑 수정
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        # 존재 여부 확인
        placeholder = "?" if is_sqlite else "%s"
        cursor.execute(
            f"SELECT our_category FROM category_playauto_mapping WHERE id = {placeholder}",
            (mapping_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다")

        our_category = row[0]

        # 업데이트
        if is_sqlite:
            cursor.execute("""
                UPDATE category_playauto_mapping
                SET sol_cate_no = ?, playauto_category = ?, similarity = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (mapping.sol_cate_no, mapping.playauto_category,
                  mapping.similarity, mapping_id))
        else:
            cursor.execute("""
                UPDATE category_playauto_mapping
                SET sol_cate_no = %s, playauto_category = %s, similarity = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (mapping.sol_cate_no, mapping.playauto_category,
                  mapping.similarity, mapping_id))

        conn.commit()
        conn.close()

        logger.info(f"[PlayAuto 카테고리 매핑] 매핑 수정: {our_category} -> {mapping.sol_cate_no}")

        return {
            "id": mapping_id,
            "our_category": our_category,
            "sol_cate_no": mapping.sol_cate_no,
            "playauto_category": mapping.playauto_category,
            "similarity": mapping.similarity
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PlayAuto 카테고리 매핑] 수정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/category-playauto-mappings/{mapping_id}")
async def delete_mapping(mapping_id: int):
    """
    매핑 삭제
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        # 존재 여부 확인
        placeholder = "?" if is_sqlite else "%s"
        cursor.execute(
            f"SELECT our_category FROM category_playauto_mapping WHERE id = {placeholder}",
            (mapping_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다")

        our_category = row[0]

        # 삭제
        cursor.execute(
            f"DELETE FROM category_playauto_mapping WHERE id = {placeholder}",
            (mapping_id,)
        )
        conn.commit()
        conn.close()

        logger.info(f"[PlayAuto 카테고리 매핑] 매핑 삭제: {our_category}")

        return {"message": f"'{our_category}' 매핑이 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PlayAuto 카테고리 매핑] 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
