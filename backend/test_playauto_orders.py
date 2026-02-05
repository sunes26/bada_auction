"""PlayAuto 주문 수집 테스트"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# .env.local 로드
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

# 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from playauto.auth import load_api_credentials, fetch_token, get_api_base_url
from playauto.client import PlayautoClient
from playauto.orders import PlayautoOrdersAPI, fetch_and_sync_orders
from database.db_wrapper import get_db


async def test_playauto_connection():
    """PlayAuto API 연결 테스트"""
    print("=" * 60)
    print("PlayAuto API 연결 테스트")
    print("=" * 60)

    try:
        # 1. 자격 증명 로드
        print("\n[1] 자격 증명 로드...")
        api_key, email, password = load_api_credentials()
        base_url = get_api_base_url()

        print(f"[OK] API Key: {api_key[:20]}...")
        print(f"[OK] Email: {email}")
        print(f"[OK] Base URL: {base_url}")

        # 2. 토큰 발급
        print("\n[2] 토큰 발급 시도...")
        token, sol_no = fetch_token(api_key, email, password, base_url)
        print(f"[OK] Token: {token[:30]}...")
        print(f"[OK] Sol No: {sol_no}")

        # 3. 주문 수집 테스트
        print("\n[3] 주문 수집 테스트 (최근 7일)...")
        orders_api = PlayautoOrdersAPI()

        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        print(f"   기간: {start_date} ~ {end_date}")

        result = await orders_api.fetch_orders(
            start_date=start_date,
            end_date=end_date,
            limit=100
        )

        print(f"[OK] 주문 수집 결과:")
        print(f"   - 성공: {result.get('success')}")
        print(f"   - 총 주문: {result.get('total', 0)}건")
        print(f"   - 수집된 주문: {len(result.get('orders', []))}건")

        if result.get('orders'):
            print(f"\n   최근 3개 주문:")
            for i, order in enumerate(result.get('orders', [])[:3], 1):
                print(f"   {i}. 주문번호: {order.get('order_number', 'N/A')}")
                print(f"      마켓: {order.get('market', 'N/A')}")
                print(f"      고객: {order.get('customer_name', 'N/A')}")
                print(f"      금액: {order.get('total_amount', 0):,}원")

        # 4. 로컬 DB 주문 확인
        print("\n[4] 로컬 DB 주문 확인...")
        db = get_db()
        conn = db.get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        print(f"[OK] 로컬 DB 주문: {count}건")

        if count > 0:
            cursor2 = conn.execute("""
                SELECT order_number, market, customer_name, created_at
                FROM orders
                ORDER BY created_at DESC
                LIMIT 3
            """)
            print(f"\n   최근 3개 주문:")
            for i, row in enumerate(cursor2.fetchall(), 1):
                print(f"   {i}. 주문번호: {row[0]}")
                print(f"      마켓: {row[1]}")
                print(f"      고객: {row[2]}")
                print(f"      생성일: {row[3]}")

        conn.close()

        # 5. PlayAuto 설정 확인
        print("\n[5] PlayAuto 설정 확인...")
        enabled = db.get_playauto_setting("enabled") == "true"
        auto_sync_enabled = db.get_playauto_setting("auto_sync_enabled") == "true"
        auto_sync_interval = db.get_playauto_setting("auto_sync_interval") or "30"

        print(f"[OK] PlayAuto 활성화: {enabled}")
        print(f"[OK] 자동 동기화: {auto_sync_enabled}")
        print(f"[OK] 동기화 주기: {auto_sync_interval}분")

        if not auto_sync_enabled:
            print("\n[WARNING] 자동 동기화가 비활성화되어 있습니다!")
            print("   실시간 주문을 받으려면 자동 동기화를 활성화하세요.")

        print("\n" + "=" * 60)
        print("[OK] 모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_playauto_connection())
