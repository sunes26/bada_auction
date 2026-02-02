"""
카테고리-infoCode 매핑 관리 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.database_manager import get_database_manager
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["category-mappings"])


class CategoryInfoCodeMapping(BaseModel):
    """카테고리-infoCode 매핑 모델"""
    id: Optional[int] = None
    level1: str
    info_code: str
    info_code_name: str
    notes: Optional[str] = None


class CategoryInfoCodeMappingCreate(BaseModel):
    """카테고리-infoCode 매핑 생성 모델"""
    level1: str
    info_code: str
    info_code_name: str
    notes: Optional[str] = None


class CategoryInfoCodeMappingUpdate(BaseModel):
    """카테고리-infoCode 매핑 수정 모델"""
    info_code: str
    info_code_name: str
    notes: Optional[str] = None


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


@router.get("/category-infocode-mappings", response_model=List[CategoryInfoCodeMapping])
async def get_all_mappings():
    """
    모든 카테고리-infoCode 매핑 조회
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, level1, info_code, info_code_name, notes
            FROM category_infocode_mapping
            ORDER BY level1
        """)

        mappings = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(cursor, row)
            mappings.append({
                "id": row_dict["id"],
                "level1": row_dict["level1"],
                "info_code": row_dict["info_code"],
                "info_code_name": row_dict["info_code_name"],
                "notes": row_dict["notes"]
            })

        conn.close()

        logger.info(f"[카테고리 매핑] {len(mappings)}개 매핑 조회")
        return mappings

    except Exception as e:
        logger.error(f"[카테고리 매핑] 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category-infocode-mappings/{mapping_id}", response_model=CategoryInfoCodeMapping)
async def get_mapping(mapping_id: int):
    """
    특정 매핑 조회
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        placeholder = "?" if is_sqlite else "%s"
        cursor.execute(f"""
            SELECT id, level1, info_code, info_code_name, notes
            FROM category_infocode_mapping
            WHERE id = {placeholder}
        """, (mapping_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다")

        row_dict = dict_from_row(cursor, row)
        return {
            "id": row_dict["id"],
            "level1": row_dict["level1"],
            "info_code": row_dict["info_code"],
            "info_code_name": row_dict["info_code_name"],
            "notes": row_dict["notes"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[카테고리 매핑] 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/category-infocode-mappings", response_model=CategoryInfoCodeMapping)
async def create_mapping(mapping: CategoryInfoCodeMappingCreate):
    """
    새 매핑 추가
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        # 중복 체크
        placeholder = "?" if is_sqlite else "%s"
        cursor.execute(
            f"SELECT id FROM category_infocode_mapping WHERE level1 = {placeholder}",
            (mapping.level1,)
        )
        if cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"'{mapping.level1}' 카테고리는 이미 매핑되어 있습니다"
            )

        # 삽입
        if is_sqlite:
            cursor.execute("""
                INSERT INTO category_infocode_mapping (level1, info_code, info_code_name, notes)
                VALUES (?, ?, ?, ?)
            """, (mapping.level1, mapping.info_code, mapping.info_code_name, mapping.notes))
        else:
            cursor.execute("""
                INSERT INTO category_infocode_mapping (level1, info_code, info_code_name, notes)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (mapping.level1, mapping.info_code, mapping.info_code_name, mapping.notes))

        conn.commit()
        mapping_id = cursor.lastrowid if is_sqlite else cursor.fetchone()[0]
        conn.close()

        logger.info(f"[카테고리 매핑] 새 매핑 추가: {mapping.level1} -> {mapping.info_code}")

        return {
            "id": mapping_id,
            "level1": mapping.level1,
            "info_code": mapping.info_code,
            "info_code_name": mapping.info_code_name,
            "notes": mapping.notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[카테고리 매핑] 추가 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/category-infocode-mappings/{mapping_id}", response_model=CategoryInfoCodeMapping)
async def update_mapping(mapping_id: int, mapping: CategoryInfoCodeMappingUpdate):
    """
    매핑 수정
    """
    try:
        conn, is_sqlite = get_db_connection()
        cursor = conn.cursor()

        # 존재 여부 확인
        placeholder = "?" if is_sqlite else "%s"
        cursor.execute(
            f"SELECT level1 FROM category_infocode_mapping WHERE id = {placeholder}",
            (mapping_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다")

        level1 = row[0]

        # 업데이트
        if is_sqlite:
            cursor.execute("""
                UPDATE category_infocode_mapping
                SET info_code = ?, info_code_name = ?, notes = ?
                WHERE id = ?
            """, (mapping.info_code, mapping.info_code_name, mapping.notes, mapping_id))
        else:
            cursor.execute("""
                UPDATE category_infocode_mapping
                SET info_code = %s, info_code_name = %s, notes = %s
                WHERE id = %s
            """, (mapping.info_code, mapping.info_code_name, mapping.notes, mapping_id))

        conn.commit()
        conn.close()

        logger.info(f"[카테고리 매핑] 매핑 수정: {level1} -> {mapping.info_code}")

        return {
            "id": mapping_id,
            "level1": level1,
            "info_code": mapping.info_code,
            "info_code_name": mapping.info_code_name,
            "notes": mapping.notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[카테고리 매핑] 수정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/category-infocode-mappings/{mapping_id}")
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
            f"SELECT level1 FROM category_infocode_mapping WHERE id = {placeholder}",
            (mapping_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다")

        level1 = row[0]

        # 삭제
        cursor.execute(
            f"DELETE FROM category_infocode_mapping WHERE id = {placeholder}",
            (mapping_id,)
        )
        conn.commit()
        conn.close()

        logger.info(f"[카테고리 매핑] 매핑 삭제: {level1}")

        return {"message": f"'{level1}' 매핑이 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[카테고리 매핑] 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-infocodes")
async def get_available_infocodes():
    """
    사용 가능한 infoCode 목록 반환
    """
    infocodes = [
        {"code": "ProcessedFood2023", "name": "가공식품", "description": "즉석식품, 음료, 과자 등"},
        {"code": "Food2023", "name": "식품", "description": "일반 식품"},
        {"code": "HealthFunctionalFood2023", "name": "건강기능식품", "description": "영양제, 보충제"},
        {"code": "Cosmetic2023", "name": "화장품", "description": "스킨케어, 메이크업"},
        {"code": "Shoes2023", "name": "신발", "description": "운동화, 구두 등"},
        {"code": "Bag2023", "name": "가방", "description": "핸드백, 백팩 등"},
        {"code": "FashionItems2023", "name": "패션잡화", "description": "액세서리, 모자 등"},
        {"code": "SleepingGear2023", "name": "침구류", "description": "이불, 베개 등"},
        {"code": "Furniture2023", "name": "가구", "description": "책상, 의자 등"},
        {"code": "OfficeAppliances2023", "name": "사무용품", "description": "문구, 사무기기"},
        {"code": "OpticsAppliances2023", "name": "광학기기", "description": "카메라, 안경 등"},
        {"code": "MicroElectronics2023", "name": "소형전자기기", "description": "이어폰, 보조배터리"},
        {"code": "Navigation2023", "name": "내비게이션", "description": "GPS, 블랙박스"},
        {"code": "CarArticles2023", "name": "자동차용품", "description": "차량 액세서리"},
        {"code": "KitchenUtensils2023", "name": "주방용품", "description": "조리도구, 식기"},
        {"code": "Kids2023", "name": "아동용품", "description": "완구, 유아용품"},
        {"code": "MusicalInstrument2023", "name": "악기", "description": "기타, 피아노 등"},
        {"code": "SportsEquipment2023", "name": "스포츠용품", "description": "운동기구, 스포츠웨어"},
        {"code": "Books2023", "name": "도서", "description": "책, 잡지"},
        {"code": "GiftCard2023", "name": "상품권", "description": "기프트카드"},
        {"code": "MobileCoupon2023", "name": "모바일쿠폰", "description": "모바일 상품권"},
        {"code": "HouseHoldChemical2023", "name": "생활화학제품", "description": "세제, 방향제"},
        {"code": "Biodical2023", "name": "의료기기", "description": "혈압계, 체온계"},
        {"code": "MovieShow2023", "name": "영화/공연", "description": "티켓, 관람권"},
        {"code": "EtcService2023", "name": "기타서비스", "description": "서비스 상품"},
        {"code": "Etc2023", "name": "기타", "description": "기타 재화"}
    ]

    return infocodes
