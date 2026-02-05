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


async def test_new_orders_api():
    """새로운 POST /orders API 테스트"""
    print("=" * 60)
    print("새로운 POST /orders API 테스트")
    print("=" * 60)

    try:
        orders_api = PlayautoOrdersAPI()

        # 다중 상태 필터링 테스트
        print("\n[1] 다중 상태 필터링 테스트...")
        result = await orders_api.fetch_orders(
            start_date="2026-01-01",
            end_date="2026-02-05",
            order_status=["신규주문", "출고대기"],  # 다중 상태
            start=0,
            length=100
        )

        print(f"[OK] 성공: {result.get('success')}")
        print(f"[OK] 총 주문: {result.get('total', 0)}건")

        # 묶음 주문 테스트
        print("\n[2] 묶음 주문 그룹화 테스트...")
        result2 = await orders_api.fetch_orders(
            start_date="2026-01-01",
            end_date="2026-02-05",
            bundle_yn=True,
            start=0,
            length=100
        )

        print(f"[OK] 성공: {result2.get('success')}")
        print(f"[OK] 총 주문: {result2.get('total', 0)}건")

        # 검색 테스트
        print("\n[3] 주문 검색 테스트...")
        result3 = await orders_api.fetch_orders(
            start_date="2026-01-01",
            end_date="2026-02-05",
            search_key="order_name",
            search_word="홍길동",
            start=0,
            length=100
        )

        print(f"[OK] 성공: {result3.get('success')}")
        print(f"[OK] 검색 결과: {result3.get('total', 0)}건")

        print("\n" + "=" * 60)
        print("[OK] 새 API 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()


async def test_80_fields_parsing():
    """80+ 필드 파싱 검증 테스트"""
    print("=" * 60)
    print("80+ 필드 파싱 검증 테스트")
    print("=" * 60)

    try:
        orders_api = PlayautoOrdersAPI()

        # 샘플 주문 데이터 (공식 API 응답 형식)
        sample_order = {
            "uniq": "12345678901234567890",
            "shop_name": "쿠팡",
            "shop_cd": "0001",
            "shop_ord_no": "ORD-2026-0001",
            "ord_status": "신규주문",
            "ord_time": "2026-02-05 10:30:00",
            "to_name": "홍길동",
            "to_htel": "010-1234-5678",
            "to_addr1": "서울시 강남구",
            "to_addr2": "테헤란로 123",
            "to_zipcd": "06142",
            "order_name": "김철수",
            "order_email": "test@example.com",
            "carr_name": "CJ대한통운",
            "invoice_no": "1234567890",
            "pay_amt": 50000,
            "discount_amt": 5000,
            "sales": 45000,
            "pay_method": "카드",
            "pay_time": "2026-02-05 10:31:00",
            "shop_sale_name": "테스트 상품",
            "sale_cnt": 2,
            "items": []
        }

        print("\n[1] 주문 파싱 테스트...")
        order = orders_api._parse_order(sample_order)

        # 기존 필드 검증
        print("\n[2] 기존 필드 검증...")
        assert order.playauto_order_id == "12345678901234567890", "playauto_order_id 불일치"
        assert order.market == "쿠팡", "market 불일치"
        assert order.customer_name == "홍길동", "customer_name 불일치"
        print("[OK] 기존 필드 정상")

        # 신규 필드 검증
        print("\n[3] 신규 필드 검증...")
        assert order.uniq == "12345678901234567890", "uniq 불일치"
        assert order.shop_name == "쿠팡", "shop_name 불일치"
        assert order.ord_status == "신규주문", "ord_status 불일치"
        print("[OK] 신규 필드 정상")

        # 중첩 객체 검증
        print("\n[4] 중첩 객체 검증...")
        assert order.orderer is not None, "orderer 없음"
        assert order.orderer.order_name == "김철수", "주문자명 불일치"
        assert order.orderer.order_email == "test@example.com", "이메일 불일치"

        assert order.receiver is not None, "receiver 없음"
        assert order.receiver.to_name == "홍길동", "수령인명 불일치"
        assert order.receiver.to_htel == "010-1234-5678", "휴대폰 불일치"

        assert order.delivery is not None, "delivery 없음"
        assert order.delivery.carr_name == "CJ대한통운", "택배사 불일치"

        assert order.payment is not None, "payment 없음"
        assert order.payment.pay_amt == 50000, "결제금액 불일치"
        assert order.payment.pay_method == "카드", "결제수단 불일치"

        print("[OK] 중첩 객체 정상")

        # 날짜 파싱 검증
        print("\n[5] 날짜 파싱 검증...")
        assert order.ord_time is not None, "ord_time 없음"
        assert order.payment.pay_time is not None, "pay_time 없음"
        print("[OK] 날짜 파싱 정상")

        print("\n" + "=" * 60)
        print("[OK] 80+ 필드 파싱 테스트 완료!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 검증 실패: {e}")
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()


async def test_all():
    """모든 테스트 실행"""
    print("\n\n")
    print("=" * 60)
    print("PlayAuto 주문 시스템 완전 테스트")
    print("=" * 60)
    print("\n")

    # 1. 기존 연결 테스트
    await test_playauto_connection()
    print("\n\n")

    # 2. 새 API 테스트
    await test_new_orders_api()
    print("\n\n")

    # 3. 80+ 필드 파싱 테스트
    await test_80_fields_parsing()

    print("\n\n")
    print("=" * 60)
    print("[완료] 모든 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    # 모든 테스트 실행
    asyncio.run(test_all())
