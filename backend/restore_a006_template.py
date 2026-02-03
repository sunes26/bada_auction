#!/usr/bin/env python3
"""
A006 (옥션) 템플릿 복구
"""
import json
from database.database_manager import get_database_manager

def main():
    print("=" * 80)
    print("A006 템플릿 복구")
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
            print("[ERROR] default_templates 설정이 없습니다.")
            return

        templates = json.loads(row[0])
        print(f"현재 템플릿: {len(templates)}개")
        for t in templates:
            print(f"  - [{t.get('shop_cd')}] {t.get('shop_name')}")
        print()

        # A006이 이미 있는지 확인
        has_a006 = any(t.get('shop_cd') == 'A006' for t in templates)
        
        if has_a006:
            print("[INFO] A006 템플릿이 이미 존재합니다.")
            return

        # A006 추가
        a006_template = {
            "shop_cd": "A006",
            "shop_name": "옥션",
            "shop_id": "oceancode",
            "template_no": 2235971,
            "template_name": "옥션"
        }
        
        templates.append(a006_template)
        
        # 업데이트
        new_value = json.dumps(templates, ensure_ascii=False)
        cursor.execute(
            f"UPDATE playauto_settings SET setting_value = {placeholder} WHERE setting_key = 'default_templates'",
            (new_value,)
        )
        conn.commit()
        
        print("[OK] A006 템플릿을 추가했습니다!")
        print()
        print("현재 템플릿:")
        for i, t in enumerate(templates, 1):
            print(f"  {i}. [{t.get('shop_cd')}] {t.get('shop_name')} (템플릿: {t.get('template_no')})")
        
        print()
        print("=" * 80)
        print("이제 상품 등록 테스트를 해보세요!")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
