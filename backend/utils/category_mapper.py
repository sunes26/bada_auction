"""
카테고리 매핑 유틸리티

우리 시스템 카테고리를 PlayAuto 카테고리 코드(sol_cate_no)로 변환
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

from typing import Optional, Dict
from database.database_manager import get_database_manager


def get_playauto_category_code(our_category: str) -> Optional[int]:
    """
    우리 카테고리를 PlayAuto 카테고리 코드로 변환

    Args:
        our_category: 우리 시스템의 카테고리 (예: "간편식 > 면 > 라면 > 라면")

    Returns:
        PlayAuto 카테고리 코드(sol_cate_no) 또는 None

    Example:
        >>> code = get_playauto_category_code("간편식 > 면 > 라면 > 라면")
        >>> print(code)  # 36060400
    """
    try:
        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        placeholder = "?" if db_manager.is_sqlite else "%s"
        cursor.execute(
            f"SELECT sol_cate_no FROM category_playauto_mapping WHERE our_category = {placeholder}",
            (our_category,)
        )

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    except Exception as e:
        print(f"[ERROR] 카테고리 매핑 조회 실패: {e}")
        return None


def get_category_mapping_info(our_category: str) -> Optional[Dict]:
    """
    카테고리 매핑 상세 정보 조회

    Args:
        our_category: 우리 시스템의 카테고리

    Returns:
        매핑 정보 딕셔너리 또는 None
        {
            'sol_cate_no': int,
            'playauto_category': str,
            'similarity': str
        }

    Example:
        >>> info = get_category_mapping_info("간편식 > 면 > 라면 > 라면")
        >>> print(info)
        {
            'sol_cate_no': 36060400,
            'playauto_category': '음료/과자/가공식품 > 라면/면류 > 컵라면',
            'similarity': '72.10%'
        }
    """
    try:
        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        placeholder = "?" if db_manager.is_sqlite else "%s"
        cursor.execute(
            f"""
            SELECT sol_cate_no, playauto_category, similarity
            FROM category_playauto_mapping
            WHERE our_category = {placeholder}
            """,
            (our_category,)
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'sol_cate_no': result[0],
                'playauto_category': result[1],
                'similarity': result[2]
            }
        return None

    except Exception as e:
        print(f"[ERROR] 카테고리 매핑 정보 조회 실패: {e}")
        return None


def get_all_category_mappings() -> list:
    """
    모든 카테고리 매핑 조회

    Returns:
        매핑 정보 리스트
    """
    try:
        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT our_category, sol_cate_no, playauto_category, similarity
            FROM category_playauto_mapping
            ORDER BY our_category
        """)

        results = cursor.fetchall()
        conn.close()

        return [
            {
                'our_category': row[0],
                'sol_cate_no': row[1],
                'playauto_category': row[2],
                'similarity': row[3]
            }
            for row in results
        ]

    except Exception as e:
        print(f"[ERROR] 카테고리 매핑 목록 조회 실패: {e}")
        return []


if __name__ == "__main__":
    # 테스트
    print("=== 카테고리 매핑 유틸리티 테스트 ===\n")

    # 테스트 1: 코드만 조회
    test_category = "간편식 > 면 > 라면 > 라면"
    code = get_playauto_category_code(test_category)
    print(f"테스트 1: {test_category}")
    print(f"  -> sol_cate_no: {code}\n")

    # 테스트 2: 상세 정보 조회
    info = get_category_mapping_info(test_category)
    print(f"테스트 2: {test_category}")
    print(f"  -> {info}\n")

    # 테스트 3: 전체 매핑 개수
    all_mappings = get_all_category_mappings()
    print(f"테스트 3: 전체 매핑 개수")
    print(f"  -> {len(all_mappings)}개\n")

    # 샘플 출력
    print("=== 샘플 매핑 (처음 5개) ===")
    for mapping in all_mappings[:5]:
        print(f"  {mapping['our_category']}")
        print(f"    -> {mapping['sol_cate_no']} ({mapping['playauto_category']}) [{mapping['similarity']}]")
