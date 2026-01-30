"""
플레이오토 API 종합 테스트 스크립트
각 기능별로 테스트를 진행하고 결과를 출력합니다.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from playauto.client import PlayautoClient
from playauto.auth import get_or_fetch_token, load_api_credentials
from playauto.orders import PlayautoOrdersAPI
from playauto.carriers import PlayautoCarriersAPI
from dotenv import load_dotenv
import os

# 환경 변수 로드
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_test(self, name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        print("\n" + "="*80)
        print("테스트 결과 요약")
        print("="*80)
        for test in self.tests:
            status = "[PASS]" if test["passed"] else "[FAIL]"
            print(f"{status} | {test['name']}")
            if test["message"]:
                print(f"       {test['message']}")
        print("="*80)
        print(f"총 {len(self.tests)}개 테스트 중 {self.passed}개 통과, {self.failed}개 실패")
        print("="*80)

results = TestResults()

async def test_1_environment_variables():
    """테스트 1: 환경 변수 확인"""
    print("\n[테스트 1] 환경 변수 확인")
    print("-" * 80)

    required_vars = [
        'PLAYAUTO_API_KEY',
        'PLAYAUTO_EMAIL',
        'PLAYAUTO_PASSWORD',
        'PLAYAUTO_API_URL',
        'PLAYAUTO_SOLUTION_KEY'
    ]

    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 보안을 위해 일부만 표시
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"  [OK] {var}: {display_value}")
        else:
            print(f"  [FAIL] {var}: 없음")
            all_present = False

    if all_present:
        results.add_test("환경 변수 확인", True, "모든 필수 환경 변수가 설정됨")
    else:
        results.add_test("환경 변수 확인", False, "일부 환경 변수가 누락됨")

    return all_present

async def test_2_authentication():
    """테스트 2: 플레이오토 인증"""
    print("\n[테스트 2] 플레이오토 인증 테스트")
    print("-" * 80)

    try:
        token, sol_no = get_or_fetch_token()

        if token:
            print(f"  [OK] 인증 성공")
            print(f"  [OK] 토큰: {token[:20]}...")
            print(f"  [OK] 솔루션 번호: {sol_no}")
            results.add_test("인증", True, "토큰 발급 성공")
            return True
        else:
            print(f"  [FAIL] 인증 실패: 토큰이 None")
            results.add_test("인증", False, "토큰이 None으로 반환됨")
            return False
    except Exception as e:
        print(f"  [FAIL] 인증 실패: {str(e)}")
        results.add_test("인증", False, str(e))
        return False

async def test_3_client_initialization():
    """테스트 3: PlayautoClient 초기화"""
    print("\n[테스트 3] PlayautoClient 초기화 테스트")
    print("-" * 80)

    try:
        client = PlayautoClient()
        print(f"  [OK] 클라이언트 생성 성공")
        print(f"  [OK] API URL: {client.base_url}")
        results.add_test("클라이언트 초기화", True, "PlayautoClient 생성 성공")
        return client
    except Exception as e:
        print(f"  [FAIL] 클라이언트 생성 실패: {str(e)}")
        results.add_test("클라이언트 초기화", False, str(e))
        return None

async def test_4_carriers_list():
    """테스트 4: 택배사 목록 조회"""
    print("\n[테스트 4] 택배사 목록 조회 테스트")
    print("-" * 80)

    try:
        carriers_api = PlayautoCarriersAPI()
        carrier_list = await carriers_api.get_carriers()

        if carrier_list:
            print(f"  [OK] 택배사 조회 성공: {len(carrier_list)}개")
            print(f"  [OK] 첫 3개 택배사:")
            for carrier in carrier_list[:3]:
                print(f"     - {carrier.get('carrier_name', 'N/A')} (코드: {carrier.get('carrier_code', 'N/A')})")
            results.add_test("택배사 목록 조회", True, f"{len(carrier_list)}개 택배사 조회 성공")
            return True
        else:
            print(f"  [FAIL] 택배사 목록이 비어있음")
            results.add_test("택배사 목록 조회", False, "택배사 목록이 비어있음")
            return False
    except Exception as e:
        print(f"  [FAIL] 택배사 조회 실패: {str(e)}")
        results.add_test("택배사 목록 조회", False, str(e))
        return False

async def test_5_order_list():
    """테스트 5: 주문 목록 조회"""
    print("\n[테스트 5] 주문 목록 조회 테스트")
    print("-" * 80)

    try:
        orders_api = PlayautoOrdersAPI()

        # 최근 7일간의 주문 조회
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        print(f"  조회 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        response = await orders_api.fetch_orders(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        orders = response.get('orders', [])

        if orders is not None:
            print(f"  [OK] 주문 조회 성공: {len(orders)}개")
            if len(orders) > 0:
                print(f"  [OK] 첫 번째 주문 정보:")
                first_order = orders[0]
                print(f"     - 주문번호: {first_order.get('order_no', 'N/A')}")
                print(f"     - 상태: {first_order.get('status', 'N/A')}")
                print(f"     - 쇼핑몰: {first_order.get('shop_name', 'N/A')}")
            results.add_test("주문 목록 조회", True, f"{len(orders)}개 주문 조회 성공")
            return orders
        else:
            print(f"  [FAIL] 주문 목록 조회 실패")
            results.add_test("주문 목록 조회", False, "주문 목록이 None으로 반환됨")
            return None
    except Exception as e:
        print(f"  [FAIL] 주문 조회 실패: {str(e)}")
        results.add_test("주문 목록 조회", False, str(e))
        return None

async def test_6_order_detail(orders):
    """테스트 6: 주문 상세 정보 조회"""
    print("\n[테스트 6] 주문 상세 정보 조회 테스트")
    print("-" * 80)

    if not orders or len(orders) == 0:
        print(f"  [SKIP] 주문이 없어 상세 조회 테스트 건너뜀")
        results.add_test("주문 상세 조회", True, "주문이 없어 테스트 건너뜀")
        return

    try:
        orders_api = PlayautoOrdersAPI()
        first_order = orders[0]
        order_id = first_order.get('unliq')  # playauto order ID

        print(f"  테스트 주문 ID: {order_id}")

        detail = await orders_api.get_order_detail(order_id)

        if detail:
            print(f"  [OK] 주문 상세 조회 성공")
            print(f"  [OK] 상세 정보: {detail}")
            results.add_test("주문 상세 조회", True, f"주문 ID {order_id} 상세 조회 성공")
        else:
            print(f"  [FAIL] 주문 상세 조회 실패")
            results.add_test("주문 상세 조회", False, "상세 정보가 None으로 반환됨")
    except Exception as e:
        print(f"  [FAIL] 주문 상세 조회 실패: {str(e)}")
        results.add_test("주문 상세 조회", False, str(e))

async def test_7_order_status_filter():
    """테스트 7: 주문 상태별 필터링"""
    print("\n[테스트 7] 주문 상태별 필터링 테스트")
    print("-" * 80)

    try:
        orders_api = PlayautoOrdersAPI()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # 신규 주문만 조회
        response = await orders_api.fetch_orders(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            order_status='new'
        )

        orders = response.get('orders', [])

        if orders is not None:
            print(f"  [OK] 신규 주문 필터링 성공: {len(orders)}개")
            results.add_test("주문 상태 필터링", True, f"신규 주문 {len(orders)}개 조회")
        else:
            print(f"  [FAIL] 주문 필터링 실패")
            results.add_test("주문 상태 필터링", False, "필터링 결과가 None")
    except Exception as e:
        print(f"  [FAIL] 주문 필터링 실패: {str(e)}")
        results.add_test("주문 상태 필터링", False, str(e))

async def main():
    """메인 테스트 실행"""
    print("="*80)
    print("플레이오토 API 종합 테스트 시작")
    print("="*80)
    print(f"테스트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 환경 변수 확인
    env_ok = await test_1_environment_variables()
    if not env_ok:
        print("\n❌ 환경 변수가 설정되지 않아 테스트를 중단합니다.")
        results.print_summary()
        return

    # 인증 테스트
    auth_ok = await test_2_authentication()
    if not auth_ok:
        print("\n❌ 인증에 실패하여 테스트를 중단합니다.")
        results.print_summary()
        return

    # 클라이언트 초기화
    client = await test_3_client_initialization()
    if not client:
        print("\n❌ 클라이언트 초기화 실패")
        results.print_summary()
        return

    # 택배사 목록 조회
    await test_4_carriers_list()

    # 주문 목록 조회
    orders = await test_5_order_list()

    # 주문 상세 조회
    await test_6_order_detail(orders)

    # 주문 필터링
    await test_7_order_status_filter()

    # 결과 요약 출력
    results.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
