#!/usr/bin/env python3
"""
PlayAuto 설정에서 ESM 템플릿을 사용하는 A006 (옥션) 채널 제거

A006 템플릿 2235971이 ESM 모드로 설정되어 있어
식품 등 대부분의 카테고리를 등록할 수 없음
"""
import json
from database.database_manager import get_database_manager

def main():
    print("=" * 80)
    print("ESM 템플릿 제거 (A006 옥션)")
    print("=" * 80)
    print()

    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    placeholder = "?" if db_manager.is_sqlite else "%s"

    try:
        # 현재 설정 조회
        cursor.execute("SELECT setting_value FROM playauto_settings WHERE setting_key = 'default_templates'")
        row = cursor.fetchone()

        if not row:
            print("[INFO] default_templates 설정이 없습니다.")
            return

        templates = json.loads(row[0])
        print(f"[1] 현재 템플릿: {len(templates)}개")
        print()

        # 기존 템플릿 출력
        for i, t in enumerate(templates):
            shop_cd = t.get('shop_cd', '')
            shop_name = t.get('shop_name', 'unknown')
            template_no = t.get('template_no', 'N/A')
            print(f"  Template {i+1}: [{shop_cd}] {shop_name} (템플릿 번호: {template_no})")

        print()

        # A006 제거
        original_count = len(templates)
        filtered_templates = [
            t for t in templates
            if t.get('shop_cd') not in ['A006']
        ]
        removed_count = original_count - len(filtered_templates)

        if removed_count > 0:
            # 업데이트
            new_value = json.dumps(filtered_templates, ensure_ascii=False)
            cursor.execute(
                f"UPDATE playauto_settings SET setting_value = {placeholder} WHERE setting_key = 'default_templates'",
                (new_value,)
            )
            conn.commit()
            print(f"[OK] A006 (옥션) ESM 템플릿을 제거했습니다!")
            print()
            print("남은 템플릿:")
            for i, t in enumerate(filtered_templates):
                shop_cd = t.get('shop_cd', '')
                shop_name = t.get('shop_name', 'unknown')
                template_no = t.get('template_no', 'N/A')
                print(f"  {i+1}. [{shop_cd}] {shop_name} (템플릿 번호: {template_no})")
        else:
            print("[INFO] A006 템플릿이 없습니다. 제거할 것이 없습니다.")

        print()
        print("=" * 80)
        print("완료!")
        print("=" * 80)
        print()
        print("이제 네이버(A001)와 스마트스토어(A077)로 상품이 등록됩니다.")
        print("식품을 포함한 모든 카테고리를 등록할 수 있습니다.")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
