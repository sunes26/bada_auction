#!/usr/bin/env python3
"""프로덕션 데이터베이스 카테고리 확인"""
import sys
from database.database_manager import get_database_manager

def main():
    db = get_database_manager()
    conn = db.engine.raw_connection()
    cursor = conn.cursor()

    print("=" * 80)
    print("Production Database Check")
    print("=" * 80)
    print()

    # 1. categories 테이블
    print("[1] categories table:")
    cursor.execute("SELECT COUNT(*) FROM categories")
    print(f"  Total rows: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM categories WHERE sol_cate_no IS NOT NULL")
    print(f"  With sol_cate_no: {cursor.fetchone()[0]}")

    cursor.execute("SELECT id, folder_name, level1, level2, level3, level4, sol_cate_no FROM categories WHERE sol_cate_no IS NOT NULL LIMIT 5")
    print(f"  Sample rows:")
    for row in cursor.fetchall():
        path = ' > '.join([x for x in [row[2], row[3], row[4], row[5]] if x])
        print(f"    ID: {row[0]}, path: {path}, sol_cate_no: {row[6]}")
    print()

    # 2. category_playauto_mapping 테이블
    print("[2] category_playauto_mapping table:")
    cursor.execute("SELECT COUNT(*) FROM category_playauto_mapping")
    print(f"  Total rows: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM category_playauto_mapping WHERE sol_cate_no IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"  With sol_cate_no: {count}")

    cursor.execute("SELECT id, our_category, sol_cate_no, playauto_category FROM category_playauto_mapping LIMIT 5")
    print(f"  Sample rows:")
    for row in cursor.fetchall():
        print(f"    ID: {row[0]}, our_category: {row[1]}, sol_cate_no: {row[2]}, playauto_category: {row[3]}")
    print()

    # 3. our_category 값 분포
    cursor.execute("SELECT DISTINCT our_category FROM category_playauto_mapping ORDER BY our_category LIMIT 10")
    print(f"  Sample our_category values:")
    for row in cursor.fetchall():
        print(f"    {row[0]}")
    print()

    conn.close()

if __name__ == "__main__":
    main()
