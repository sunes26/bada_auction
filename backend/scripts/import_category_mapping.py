#!/usr/bin/env python3
"""
카테고리 매핑 DB 입력 스크립트

CSV 파일의 카테고리 매핑 데이터를 PostgreSQL DB에 입력합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

import pandas as pd
from database.database_manager import get_database_manager

def create_mapping_table():
    """카테고리 매핑 테이블 생성"""
    print("[1/4] 카테고리 매핑 테이블 생성 중...")

    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    # 테이블 생성 (SQLite와 PostgreSQL 호환)
    if db_manager.is_sqlite:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_playauto_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                our_category TEXT NOT NULL UNIQUE,
                sol_cate_no INTEGER NOT NULL,
                playauto_category TEXT,
                similarity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_playauto_mapping (
                id SERIAL PRIMARY KEY,
                our_category TEXT NOT NULL UNIQUE,
                sol_cate_no INTEGER NOT NULL,
                playauto_category TEXT,
                similarity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # 인덱스 생성
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_playauto_mapping_our_category
        ON category_playauto_mapping(our_category)
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("[OK] 테이블 생성 완료")


def import_csv_to_db(csv_path: str):
    """CSV 데이터를 DB에 입력"""
    print(f"[2/4] CSV 파일 로드 중... ({csv_path})")

    # CSV 로드
    df = pd.read_csv(csv_path)
    print(f"[OK] {len(df)}개 카테고리 로드 완료")

    print("[3/4] DB에 데이터 입력 중...")

    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    # 기존 데이터 삭제
    cursor.execute("DELETE FROM category_playauto_mapping")
    print("  - 기존 데이터 삭제 완료")

    # SQL 플레이스홀더 결정 (SQLite는 ?, PostgreSQL은 %s)
    placeholder = "?" if db_manager.is_sqlite else "%s"

    # 새 데이터 입력
    success_count = 0
    for idx, row in df.iterrows():
        try:
            cursor.execute(f"""
                INSERT INTO category_playauto_mapping
                (our_category, sol_cate_no, playauto_category, similarity)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (
                row['our_category'],
                int(row['sol_cate_no']),
                row['playauto_category'],
                row['similarity']
            ))
            success_count += 1
        except Exception as e:
            print(f"  [WARN] 입력 실패: {row['our_category']} - {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"[OK] {success_count}개 카테고리 입력 완료")


def verify_data():
    """입력된 데이터 확인"""
    print("[4/4] 입력된 데이터 확인 중...")

    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    # 총 개수
    cursor.execute("SELECT COUNT(*) FROM category_playauto_mapping")
    total_count = cursor.fetchone()[0]
    print(f"[OK] 총 {total_count}개 매핑 데이터 확인")

    # 샘플 데이터
    print("\n=== 샘플 데이터 (처음 5개) ===")
    cursor.execute("""
        SELECT our_category, sol_cate_no, playauto_category
        FROM category_playauto_mapping
        ORDER BY id
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"  {row[0]:<50} -> {row[1]} ({row[2]})")

    cursor.close()
    conn.close()

    print()


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("카테고리 매핑 DB 입력 스크립트")
    print("=" * 80)
    print()

    csv_path = project_root / "backend" / "category_mapping_result.csv"

    if not csv_path.exists():
        print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_path}")
        return False

    try:
        # 1. 테이블 생성
        create_mapping_table()
        print()

        # 2. CSV 데이터 입력
        import_csv_to_db(str(csv_path))
        print()

        # 3. 데이터 확인
        verify_data()

        print("=" * 80)
        print("[SUCCESS] 카테고리 매핑 데이터 입력 완료!")
        print("=" * 80)
        print()
        print("다음 단계:")
        print("  1. 상품 등록 시 자동으로 매핑된 sol_cate_no 사용")
        print("  2. 관리자 페이지에서 매핑 관리 기능 추가 (선택)")
        print()

        return True

    except Exception as e:
        print(f"[ERROR] 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
