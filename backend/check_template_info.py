#!/usr/bin/env python3
"""
PlayAuto 템플릿 정보 확인 (ESM 여부 포함)
"""
import json
import asyncio
from database.database_manager import get_database_manager
from playauto.client import PlayautoClient

async def main():
    print("=" * 80)
    print("PlayAuto 템플릿 정보 확인")
    print("=" * 80)
    print()

    # 1. 데이터베이스에서 템플릿 조회
    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT setting_value FROM playauto_settings WHERE setting_key = 'default_templates'")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("[ERROR] default_templates 설정이 없습니다.")
        return

    templates = json.loads(row[0])
    print(f"[1] 데이터베이스 템플릿: {len(templates)}개")
    print()

    for i, t in enumerate(templates, 1):
        print(f"템플릿 {i}:")
        print(f"  shop_cd: {t.get('shop_cd')}")
        print(f"  shop_name: {t.get('shop_name')}")
        print(f"  shop_id: {t.get('shop_id')}")
        print(f"  template_no: {t.get('template_no')}")
        print(f"  template_name: {t.get('template_name', 'N/A')}")
        print()

    # 2. PlayAuto API로 실제 shop 목록 조회
    print("[2] PlayAuto API로 shop 정보 조회 중...")
    print()
    
    try:
        client = PlayautoClient()
        
        # shop 목록 조회 API (있다면)
        endpoint = "/shops/list"
        
        result = await client.post(endpoint, {})
        
        print("Shop 목록:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"[INFO] Shop 목록 조회 불가: {e}")
        print()
        print("PlayAuto API에서 템플릿별 ESM 여부를 직접 확인할 수 없습니다.")
        print("PlayAuto 관리자 페이지에서 각 템플릿의 ESM 설정을 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())
