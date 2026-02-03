#!/usr/bin/env python3
import json
import asyncio
from database.database_manager import get_database_manager
from playauto.client import PlayautoClient

async def check_template(template_no):
    """템플릿 상세 정보 조회"""
    client = PlayautoClient()
    
    # 템플릿 조회 API
    endpoints_to_try = [
        f"/templates/{template_no}",
        f"/templates/detail/{template_no}",
        "/templates/info",
    ]
    
    for endpoint in endpoints_to_try:
        try:
            if endpoint == "/templates/info":
                result = await client.post(endpoint, {"template_no": template_no})
            else:
                result = await client.get(endpoint)
            
            if result.get("response"):
                print(f"  API: {endpoint}")
                print(f"  응답: {json.dumps(result, indent=4, ensure_ascii=False)[:500]}")
                return result
        except:
            pass
    
    print(f"  [INFO] 템플릿 {template_no} 상세 조회 불가")
    return None

async def main():
    # DB에서 템플릿 정보 가져오기
    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM playauto_settings WHERE setting_key = 'default_templates'")
    row = cursor.fetchone()
    conn.close()
    
    templates = json.loads(row[0])
    
    print("=" * 80)
    print("각 템플릿 상세 정보 확인")
    print("=" * 80)
    print()
    
    for i, t in enumerate(templates, 1):
        print(f"[{i}] shop_cd: {t.get('shop_cd')}, template_no: {t.get('template_no')}")
        await check_template(t.get('template_no'))
        print()

if __name__ == "__main__":
    asyncio.run(main())
