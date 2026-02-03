#!/usr/bin/env python3
"""
수동 매핑 적용 스크립트

manual_mapping_template.xlsx에서 매핑을 읽어서
데이터베이스에 적용합니다.
"""
import pandas as pd
import sys
from pathlib import Path
from database.database_manager import get_database_manager

MAPPING_FILE = Path(__file__).parent / "manual_mapping_template.xlsx"
CATEGORY_FILE = Path(__file__).parent.parent / "category.xlsx"


def load_manual_mapping():
    """수동 매핑 파일 로드"""
    if not MAPPING_FILE.exists():
        print(f"Error: {MAPPING_FILE} not found")
        print("Run: python prepare_manual_mapping.py first")
        sys.exit(1)

    df = pd.read_excel(MAPPING_FILE, sheet_name='카테고리 매핑', engine='openpyxl')

    # new_code가 있는 것만 필터링
    df = df[df['new_code'].notna()].copy()
    df = df[df['new_code'] != ''].copy()

    # 딕셔너리로 변환
    mapping = {}
    for _, row in df.iterrows():
        cat_id = int(row['ID'])
        new_code = int(float(row['new_code']))
        mapping[cat_id] = new_code

    return mapping, df


def update_database(mapping, dry_run=True):
    """데이터베이스 업데이트"""
    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    placeholder = "?" if db_manager.is_sqlite else "%s"

    try:
        # 1. categories 테이블에 sol_cate_no 컬럼 추가 (없으면)
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
            print("Adding sol_cate_no column to categories table...")
            if db_manager.is_sqlite:
                cursor.execute("ALTER TABLE categories ADD COLUMN sol_cate_no INTEGER")
            else:
                cursor.execute("ALTER TABLE categories ADD COLUMN sol_cate_no BIGINT")
            conn.commit()

        if dry_run:
            print("\nDRY RUN - categories table:")
            for cat_id in sorted(mapping.keys())[:10]:
                new_code = mapping[cat_id]
                cursor.execute(
                    f"SELECT folder_name FROM categories WHERE id = {placeholder}",
                    (cat_id,)
                )
                result = cursor.fetchone()
                if result:
                    print(f"  ID {cat_id:3d} ({result[0]}): sol_cate_no = {new_code}")
            if len(mapping) > 10:
                print(f"  ... and {len(mapping) - 10} more")
            return 0

        # 실제 업데이트
        print("\nUpdating categories table...")
        update_count = 0
        for cat_id, new_code in mapping.items():
            cursor.execute(
                f"UPDATE categories SET sol_cate_no = {placeholder} WHERE id = {placeholder}",
                (new_code, cat_id)
            )
            update_count += cursor.rowcount

        # 2. category_playauto_mapping 테이블 업데이트
        print("Updating category_playauto_mapping table...")
        cursor.execute("SELECT id, our_category FROM category_playauto_mapping")
        existing = cursor.fetchall()

        mapping_update_count = 0
        for row in existing:
            mapping_id, cat_id = row
            if cat_id in mapping:
                new_code = mapping[cat_id]
                cursor.execute(
                    f"UPDATE category_playauto_mapping SET sol_cate_no = {placeholder} WHERE id = {placeholder}",
                    (new_code, mapping_id)
                )
                mapping_update_count += cursor.rowcount

        # 3. playauto_category 컬럼 업데이트 (카테고리명)
        print("Updating playauto_category names...")
        category_df = pd.read_excel(CATEGORY_FILE, engine='openpyxl')
        category_df.columns = ['code', 'classification', 'name']
        code_to_name = {int(row['code']): row['name'] for _, row in category_df.iterrows()}

        cursor.execute("SELECT DISTINCT sol_cate_no FROM category_playauto_mapping WHERE sol_cate_no IS NOT NULL")
        used_codes = [row[0] for row in cursor.fetchall()]

        name_update_count = 0
        for code in used_codes:
            if code in code_to_name:
                new_name = code_to_name[code]
                cursor.execute(
                    f"UPDATE category_playauto_mapping SET playauto_category = {placeholder} WHERE sol_cate_no = {placeholder}",
                    (new_name, code)
                )
                name_update_count += cursor.rowcount

        conn.commit()

        print(f"\nUpdated:")
        print(f"  categories: {update_count} rows")
        print(f"  category_playauto_mapping sol_cate_no: {mapping_update_count} rows")
        print(f"  category_playauto_mapping playauto_category: {name_update_count} rows")

        return update_count + mapping_update_count

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Apply manual category mapping')
    parser.add_argument('--apply', action='store_true', help='Actually update database')
    args = parser.parse_args()

    print("=" * 80)
    print("Manual Category Mapping Application")
    print("=" * 80)
    print()

    # Load mapping
    print("Loading manual mapping...")
    mapping, df = load_manual_mapping()
    print(f"  Loaded: {len(mapping)} mappings")
    print()

    if len(mapping) == 0:
        print("No mappings found in the file.")
        print("Please fill in the 'new_code' column in manual_mapping_template.xlsx")
        sys.exit(1)

    # Statistics
    print("=" * 80)
    print("Statistics")
    print("=" * 80)
    priority = len(df[df['우선순위'] != ''])
    total = len(df)
    print(f"Priority mappings: {priority}")
    print(f"Total mappings: {total}")
    print()

    # Update
    update_database(mapping, dry_run=not args.apply)

    if not args.apply:
        print("\n" + "=" * 80)
        print("DRY RUN MODE")
        print("=" * 80)
        print("\nTo actually apply:")
        print("  python apply_manual_mapping.py --apply")
    else:
        print("\n" + "=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print("\nCategory codes have been updated.")
        print("Next steps:")
        print("1. Test PlayAuto product registration")
        print("2. Verify category display")


if __name__ == "__main__":
    main()
