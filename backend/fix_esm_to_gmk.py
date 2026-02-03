#!/usr/bin/env python3
"""
PlayAuto 설정에서 ESM을 GMK로 변경

ESM (간편 G마켓) → GMK (일반 G마켓)으로 변경하여
식품 등 모든 카테고리를 등록할 수 있도록 함
"""
import json
from database.database_manager import get_database_manager

def main():
    print("=" * 80)
    print("ESM → GMK 변경")
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

        modified = False
        for i, t in enumerate(templates):
            shop_cd = t.get('shop_cd', '')
            shop_name = t.get('shop_name', 'unknown')

            print(f"  Template {i+1}: [{shop_cd}] {shop_name}")

            if shop_cd in ['ESM', 'esm']:
                print(f"    [WARN] ESM 발견 -> GMK로 변경합니다")
                t['shop_cd'] = 'GMK'
                if 'shop_name' in t:
                    t['shop_name'] = t['shop_name'].replace('ESM', 'G마켓').replace('esm', 'G마켓')
                modified = True
                print(f"    [OK] 변경됨: {shop_cd} -> GMK")
            elif shop_cd in ['GMK', 'gmk']:
                print(f"    [OK] 이미 일반 G마켓입니다")
            else:
                print(f"    [INFO] 다른 채널입니다")

        print()

        if modified:
            # 업데이트
            new_value = json.dumps(templates, ensure_ascii=False)
            cursor.execute(
                f"UPDATE playauto_settings SET setting_value = {placeholder} WHERE setting_key = 'default_templates'",
                (new_value,)
            )
            conn.commit()
            print("[OK] ESM을 GMK로 변경했습니다!")
            print()
            print("변경된 설정:")
            for t in templates:
                print(f"  - [{t['shop_cd']}] {t.get('shop_name', 'unknown')}")
        else:
            print("[INFO] 변경할 ESM 채널이 없습니다.")

        print()
        print("=" * 80)
        print("완료!")
        print("=" * 80)
        print()
        print("이제 식품을 포함한 모든 카테고리를 등록할 수 있습니다.")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
