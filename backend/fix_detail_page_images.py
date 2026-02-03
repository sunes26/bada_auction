#!/usr/bin/env python3
"""
detail_page_data 내부의 이미지 URL 수정

/supabase-images/ 경로를 실제 Supabase Storage URL로 변환
"""
import os
import re
import json
from database.database_manager import get_database_manager
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
BUCKET_NAME = "product-images"


def fix_image_path(old_path):
    """로컬 경로를 Supabase Storage URL로 변환"""
    if not old_path or not old_path.startswith("/supabase-images/"):
        return old_path

    # /supabase-images/1_흰밥/Image_fx... -> cat-1/Image_fx...
    match = re.search(r'/supabase-images/(\d+)_[^/]+/(.+)', old_path)
    if not match:
        return old_path

    folder_id = match.group(1)
    filename = match.group(2)

    # URL 인코딩
    from urllib.parse import quote
    encoded_filename = quote(filename, safe='')

    # Supabase Storage URL
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/cat-{folder_id}/{encoded_filename}"


def fix_detail_page_data(detail_page_json):
    """detail_page_data JSON 내부의 이미지 경로 수정"""
    try:
        data = json.loads(detail_page_json)

        # images 객체 수정
        if 'images' in data and isinstance(data['images'], dict):
            modified = False
            for key, value in data['images'].items():
                if isinstance(value, str) and value.startswith("/supabase-images/"):
                    new_path = fix_image_path(value)
                    if new_path != value:
                        data['images'][key] = new_path
                        modified = True
                        print(f"      {key}: {value[:50]}... -> {new_path[:50]}...")

            return json.dumps(data, ensure_ascii=False), modified
        else:
            return detail_page_json, False

    except json.JSONDecodeError:
        # JSON이 아니면 그대로 반환
        return detail_page_json, False
    except Exception as e:
        print(f"      [ERROR] JSON 처리 실패: {e}")
        return detail_page_json, False


def main():
    print("=" * 80)
    print("Detail Page Data 이미지 경로 수정")
    print("=" * 80)
    print()

    if not SUPABASE_URL:
        print("[ERROR] SUPABASE_URL not set in environment")
        return

    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Bucket: {BUCKET_NAME}")
    print()

    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    placeholder = "?" if db_manager.is_sqlite else "%s"

    try:
        # my_selling_products 테이블의 detail_page_data 수정
        print("[1] Checking my_selling_products table...")
        cursor.execute("SELECT id, product_name, detail_page_data FROM my_selling_products WHERE detail_page_data IS NOT NULL")
        rows = cursor.fetchall()

        print(f"  Found {len(rows)} products with detail_page_data")
        print()

        update_count = 0
        for row in rows:
            product_id, product_name, detail_page_data = row

            if detail_page_data and "/supabase-images/" in detail_page_data:
                print(f"  Processing ID {product_id}: {product_name[:40]}...")

                new_data, modified = fix_detail_page_data(detail_page_data)

                if modified:
                    cursor.execute(
                        f"UPDATE my_selling_products SET detail_page_data = {placeholder} WHERE id = {placeholder}",
                        (new_data, product_id)
                    )
                    update_count += 1
                    print(f"    [OK] Updated")
                else:
                    print(f"    [INFO] No changes needed")

        conn.commit()
        print()
        print(f"[OK] Updated {update_count} products")
        print()

        print("=" * 80)
        print("Detail Page image fix completed!")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
