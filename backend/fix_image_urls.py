#!/usr/bin/env python3
"""
잘못된 이미지 URL 수정

/supabase-images/ 경로를 실제 Supabase Storage URL로 변환
"""
import os
import re
from database.database_manager import get_database_manager
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
BUCKET_NAME = "product-images"


def fix_image_url(old_url):
    """로컬 경로를 Supabase Storage URL로 변환"""
    if not old_url or not old_url.startswith("/supabase-images/"):
        return old_url

    # /supabase-images/1_흰밥/Image_fx...
    # -> https://.../storage/v1/object/public/product-images/cat-1/Image_fx...

    # 폴더 ID 추출 (1_흰밥 -> 1)
    match = re.search(r'/supabase-images/(\d+)_[^/]+/(.+)', old_url)
    if not match:
        print(f"[WARN] Cannot parse URL: {old_url}")
        return old_url

    folder_id = match.group(1)
    filename = match.group(2)

    # URL 인코딩 (공백, 특수문자 처리)
    from urllib.parse import quote
    encoded_filename = quote(filename, safe='')

    # 새 URL 생성
    new_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/cat-{folder_id}/{encoded_filename}"

    return new_url


def main():
    print("=" * 80)
    print("이미지 URL 수정")
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
        # 1. my_selling_products 테이블
        print("[1] Checking my_selling_products table...")
        cursor.execute("SELECT id, product_name, thumbnail_url FROM my_selling_products")
        rows = cursor.fetchall()

        update_count = 0
        for row in rows:
            product_id, product_name, thumbnail_url = row

            if thumbnail_url and thumbnail_url.startswith("/supabase-images/"):
                new_url = fix_image_url(thumbnail_url)

                if new_url != thumbnail_url:
                    cursor.execute(
                        f"UPDATE my_selling_products SET thumbnail_url = {placeholder} WHERE id = {placeholder}",
                        (new_url, product_id)
                    )
                    update_count += 1
                    print(f"  ✓ ID {product_id} ({product_name[:30]}...)")
                    print(f"    Old: {thumbnail_url[:80]}...")
                    print(f"    New: {new_url[:80]}...")

        conn.commit()
        print(f"\n[OK] Updated {update_count} rows in my_selling_products")
        print()

        # 2. monitored_products 테이블도 확인 (있다면)
        try:
            print("[2] Checking monitored_products table...")
            cursor.execute("SELECT COUNT(*) FROM monitored_products")
            count = cursor.fetchone()[0]

            if count > 0:
                cursor.execute("SELECT id, product_name, product_url FROM monitored_products")
                rows = cursor.fetchall()

                update_count = 0
                for row in rows:
                    product_id, product_name, product_url = row

                    if product_url and product_url.startswith("/supabase-images/"):
                        new_url = fix_image_url(product_url)

                        if new_url != product_url:
                            cursor.execute(
                                f"UPDATE monitored_products SET product_url = {placeholder} WHERE id = {placeholder}",
                                (new_url, product_id)
                            )
                            update_count += 1
                            print(f"  ✓ ID {product_id} ({product_name[:30]}...)")

                conn.commit()
                print(f"\n[OK] Updated {update_count} rows in monitored_products")
        except Exception as e:
            print(f"[INFO] monitored_products check skipped: {e}")

        print()
        print("=" * 80)
        print("Image URL fix completed!")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
