#!/usr/bin/env python3
"""
138개 카테고리 매핑을 데이터베이스에 적용

categories 테이블과 category_playauto_mapping 테이블에
새로운 sol_cate_no를 업데이트합니다.
"""
import pandas as pd
import sys
from pathlib import Path
from database.database_manager import get_database_manager

# 경로
PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_FILE = PROJECT_ROOT / "backend" / "category_138_mapping.csv"


def load_mapping():
    """매핑 파일 로드"""
    if not MAPPING_FILE.exists():
        print(f"❌ 매핑 파일이 없습니다: {MAPPING_FILE}")
        print("먼저 map_138_categories.py를 실행하세요.")
        sys.exit(1)

    df = pd.read_csv(MAPPING_FILE, encoding='utf-8-sig')

    # new_code가 있는 것만 (매핑된 것만)
    df = df[df['new_code'].notna()].copy()

    # 딕셔너리로 변환 (category_id -> new_code)
    mapping = {}
    for _, row in df.iterrows():
        cat_id = int(row['id'])
        new_code = int(float(row['new_code']))
        mapping[cat_id] = new_code

    return mapping, df


def update_categories_table(db_manager, mapping, dry_run=True):
    """categories 테이블 업데이트"""
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    placeholder = "?" if db_manager.is_sqlite else "%s"

    try:
        if dry_run:
            print("\n🔍 DRY RUN - categories 테이블 업데이트 예정:")
            for cat_id in sorted(mapping.keys())[:10]:
                new_code = mapping[cat_id]
                # 현재 폴더 이름 조회
                cursor.execute(
                    f"SELECT folder_name FROM categories WHERE id = {placeholder}",
                    (cat_id,)
                )
                result = cursor.fetchone()
                if result:
                    folder = result[0]
                    print(f"  ID {cat_id:3d} ({folder}): sol_cate_no = {new_code}")
            if len(mapping) > 10:
                print(f"  ... 외 {len(mapping) - 10}개")
            return 0

        # 실제 업데이트
        update_count = 0
        for cat_id, new_code in mapping.items():
            # categories 테이블에는 sol_cate_no 컬럼이 없을 수 있으므로
            # 먼저 컬럼 존재 여부 확인
            if db_manager.is_sqlite:
                cursor.execute("PRAGMA table_info(categories)")
                columns = [col[1] for col in cursor.fetchall()]
            else:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='categories'
                """)
                columns = [col[0] for col in cursor.fetchall()]

            if 'sol_cate_no' not in columns:
                # 컬럼 추가
                print("  ⚠️  categories 테이블에 sol_cate_no 컬럼 추가 중...")
                if db_manager.is_sqlite:
                    cursor.execute("ALTER TABLE categories ADD COLUMN sol_cate_no INTEGER")
                else:
                    cursor.execute("ALTER TABLE categories ADD COLUMN sol_cate_no BIGINT")
                conn.commit()

            # 업데이트
            cursor.execute(
                f"UPDATE categories SET sol_cate_no = {placeholder} WHERE id = {placeholder}",
                (new_code, cat_id)
            )
            update_count += cursor.rowcount

        conn.commit()
        return update_count

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_playauto_mapping(db_manager, mapping_df, dry_run=True):
    """category_playauto_mapping 테이블 업데이트"""
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    placeholder = "?" if db_manager.is_sqlite else "%s"

    try:
        # 기존 매핑 조회
        cursor.execute("SELECT id, category_id, sol_cate_no FROM category_playauto_mapping")
        existing = cursor.fetchall()

        if dry_run:
            print("\n🔍 DRY RUN - category_playauto_mapping 테이블:")
            print(f"  현재 {len(existing)}개 매핑 존재")

            # 업데이트될 항목
            updates = []
            for row in existing:
                mapping_id, cat_id, old_code = row
                if cat_id in {int(r['id']) for _, r in mapping_df.iterrows()}:
                    new_row = mapping_df[mapping_df['id'] == cat_id].iloc[0]
                    if pd.notna(new_row['new_code']):
                        new_code = int(float(new_row['new_code']))
                        updates.append((mapping_id, cat_id, old_code, new_code))

            if updates:
                print(f"  업데이트 예정: {len(updates)}개")
                for mapping_id, cat_id, old_code, new_code in updates[:5]:
                    print(f"    ID {mapping_id}: {old_code} -> {new_code}")
                if len(updates) > 5:
                    print(f"    ... 외 {len(updates) - 5}개")

            return 0

        # 실제 업데이트
        update_count = 0
        for row in existing:
            mapping_id, cat_id, old_code = row

            # 새 코드 찾기
            matching_rows = mapping_df[mapping_df['id'] == cat_id]
            if len(matching_rows) > 0:
                new_row = matching_rows.iloc[0]
                if pd.notna(new_row['new_code']):
                    new_code = int(float(new_row['new_code']))

                    cursor.execute(
                        f"UPDATE category_playauto_mapping SET sol_cate_no = {placeholder} WHERE id = {placeholder}",
                        (new_code, mapping_id)
                    )
                    update_count += cursor.rowcount

        conn.commit()
        return update_count

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='138개 카테고리 매핑 적용')
    parser.add_argument('--apply', action='store_true', help='실제로 데이터베이스 업데이트')
    args = parser.parse_args()

    print("=" * 80)
    print("138개 카테고리 매핑 적용")
    print("=" * 80)
    print()

    # 매핑 파일 로드
    print("📂 매핑 파일 로드 중...")
    mapping, mapping_df = load_mapping()
    print(f"  ✅ {len(mapping)}개 매핑 로드")
    print()

    # 통계
    print("=" * 80)
    print("매핑 통계")
    print("=" * 80)
    high = len(mapping_df[mapping_df['confidence'] == 'high'])
    medium = len(mapping_df[mapping_df['confidence'] == 'medium'])
    low = len(mapping_df[mapping_df['confidence'] == 'low'])
    print(f"높은 신뢰도: {high}개")
    print(f"중간 신뢰도: {medium}개")
    print(f"낮은 신뢰도: {low}개")
    print(f"총 매핑:     {len(mapping)}개")
    print()

    # 데이터베이스 연결
    db_manager = get_database_manager()

    # 1. categories 테이블 업데이트
    print("=" * 80)
    print("[1/2] categories 테이블 업데이트")
    print("=" * 80)
    count = update_categories_table(db_manager, mapping, dry_run=not args.apply)
    if not args.apply:
        print()
    else:
        print(f"  ✅ {count}개 행 업데이트 완료")
        print()

    # 2. category_playauto_mapping 테이블 업데이트
    print("=" * 80)
    print("[2/2] category_playauto_mapping 테이블 업데이트")
    print("=" * 80)
    count = update_playauto_mapping(db_manager, mapping_df, dry_run=not args.apply)
    if not args.apply:
        print()
    else:
        print(f"  ✅ {count}개 행 업데이트 완료")
        print()

    if not args.apply:
        print("=" * 80)
        print("🔍 DRY RUN 모드")
        print("=" * 80)
        print()
        print("실제 업데이트를 하려면:")
        print("  python backend/apply_138_mapping.py --apply")
        print()
    else:
        print("=" * 80)
        print("✅ 업데이트 완료!")
        print("=" * 80)
        print()
        print("다음 단계:")
        print("1. PlayAuto 상품 등록 테스트")
        print("2. 카테고리 표시 정상 작동 확인")
        print()


if __name__ == "__main__":
    main()
