"""
백엔드 API 엔드포인트 테스트 스크립트
플레이오토 관련 엔드포인트를 테스트합니다.
"""
import requests
import json
from datetime import datetime

# 백엔드 서버 URL
BASE_URL = "http://localhost:8000"

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
        print("백엔드 API 테스트 결과 요약")
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

def test_1_server_health():
    """테스트 1: 서버 헬스 체크"""
    print("\n[테스트 1] 서버 헬스 체크")
    print("-" * 80)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] 서버 응답: {data}")
            results.add_test("서버 헬스 체크", True, "서버가 정상 작동 중")
            return True
        else:
            print(f"  [FAIL] 서버 응답 코드: {response.status_code}")
            results.add_test("서버 헬스 체크", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] 서버 연결 실패: {str(e)}")
        results.add_test("서버 헬스 체크", False, str(e))
        return False

def test_2_playauto_settings():
    """테스트 2: 플레이오토 설정 조회"""
    print("\n[테스트 2] 플레이오토 설정 조회")
    print("-" * 80)

    try:
        response = requests.get(f"{BASE_URL}/api/playauto/settings", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] 설정 조회 성공")
            print(f"  [OK] API 키: {data.get('api_key_masked', 'N/A')}")
            print(f"  [OK] 활성화: {data.get('enabled', False)}")
            print(f"  [OK] 자동 동기화: {data.get('auto_sync_enabled', False)}")
            results.add_test("플레이오토 설정 조회", True, "설정 조회 성공")
            return True
        else:
            print(f"  [FAIL] 설정 조회 실패: HTTP {response.status_code}")
            results.add_test("플레이오토 설정 조회", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] 설정 조회 실패: {str(e)}")
        results.add_test("플레이오토 설정 조회", False, str(e))
        return False

def test_3_connection_test():
    """테스트 3: 플레이오토 API 연결 테스트"""
    print("\n[테스트 3] 플레이오토 API 연결 테스트")
    print("-" * 80)

    try:
        response = requests.post(f"{BASE_URL}/api/playauto/test-connection", timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] 연결 테스트 성공")
            print(f"  [OK] 연결 상태: {data.get('connected', False)}")
            print(f"  [OK] 메시지: {data.get('message', 'N/A')}")
            results.add_test("API 연결 테스트", True, "플레이오토 API 연결 성공")
            return True
        else:
            print(f"  [FAIL] 연결 테스트 실패: HTTP {response.status_code}")
            print(f"  [FAIL] 응답: {response.text}")
            results.add_test("API 연결 테스트", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] 연결 테스트 실패: {str(e)}")
        results.add_test("API 연결 테스트", False, str(e))
        return False

def test_4_carriers_list():
    """테스트 4: 택배사 목록 조회"""
    print("\n[테스트 4] 택배사 목록 조회")
    print("-" * 80)

    try:
        response = requests.get(f"{BASE_URL}/api/playauto/carriers", timeout=30)

        if response.status_code == 200:
            data = response.json()
            carriers = data.get('carriers', [])
            print(f"  [OK] 택배사 조회 성공: {len(carriers)}개")
            if carriers:
                print(f"  [OK] 첫 3개 택배사:")
                for carrier in carriers[:3]:
                    print(f"     - {carrier.get('carrier_name', 'N/A')} (코드: {carrier.get('carrier_code', 'N/A')})")
            results.add_test("택배사 목록 조회", True, f"{len(carriers)}개 택배사 조회 성공")
            return True
        else:
            print(f"  [FAIL] 택배사 조회 실패: HTTP {response.status_code}")
            results.add_test("택배사 목록 조회", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] 택배사 조회 실패: {str(e)}")
        results.add_test("택배사 목록 조회", False, str(e))
        return False

def test_5_orders_list():
    """테스트 5: 주문 목록 조회"""
    print("\n[테스트 5] 주문 목록 조회")
    print("-" * 80)

    try:
        # 최근 7일간의 주문 조회
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        params = {
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "page": 1,
            "limit": 10
        }

        print(f"  조회 기간: {params['start_date']} ~ {params['end_date']}")

        response = requests.get(f"{BASE_URL}/api/playauto/orders", params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            print(f"  [OK] 주문 조회 성공: {len(orders)}개")
            print(f"  [OK] 총 주문 수: {data.get('total', 0)}개")

            if orders:
                print(f"  [OK] 첫 번째 주문:")
                first_order = orders[0]
                print(f"     - 주문번호: {first_order.get('order_no', 'N/A')}")
                print(f"     - 쇼핑몰: {first_order.get('shop_name', 'N/A')}")
                print(f"     - 상태: {first_order.get('order_status', 'N/A')}")

            results.add_test("주문 목록 조회", True, f"{len(orders)}개 주문 조회 성공")
            return orders
        else:
            print(f"  [FAIL] 주문 조회 실패: HTTP {response.status_code}")
            print(f"  [FAIL] 응답: {response.text}")
            results.add_test("주문 목록 조회", False, f"HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  [FAIL] 주문 조회 실패: {str(e)}")
        results.add_test("주문 목록 조회", False, str(e))
        return None

def test_6_stats():
    """테스트 6: 플레이오토 통계 조회"""
    print("\n[테스트 6] 플레이오토 통계 조회")
    print("-" * 80)

    try:
        response = requests.get(f"{BASE_URL}/api/playauto/stats", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] 통계 조회 성공")
            print(f"  [OK] 총 주문 수: {data.get('total_orders', 0)}")
            print(f"  [OK] 신규 주문: {data.get('new_orders', 0)}")
            print(f"  [OK] 발송 완료: {data.get('shipped_orders', 0)}")
            print(f"  [OK] 마지막 동기화: {data.get('last_sync_time', 'N/A')}")
            results.add_test("통계 조회", True, "통계 조회 성공")
            return True
        else:
            print(f"  [FAIL] 통계 조회 실패: HTTP {response.status_code}")
            results.add_test("통계 조회", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] 통계 조회 실패: {str(e)}")
        results.add_test("통계 조회", False, str(e))
        return False

def test_7_sync_logs():
    """테스트 7: 동기화 로그 조회"""
    print("\n[테스트 7] 동기화 로그 조회")
    print("-" * 80)

    try:
        response = requests.get(f"{BASE_URL}/api/playauto/sync-logs?limit=5", timeout=10)

        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            print(f"  [OK] 로그 조회 성공: {len(logs)}개")

            if logs:
                print(f"  [OK] 최근 로그:")
                for log in logs[:3]:
                    print(f"     - {log.get('created_at', 'N/A')}: {log.get('status', 'N/A')} ({log.get('orders_synced', 0)}개 주문)")

            results.add_test("동기화 로그 조회", True, f"{len(logs)}개 로그 조회 성공")
            return True
        else:
            print(f"  [FAIL] 로그 조회 실패: HTTP {response.status_code}")
            results.add_test("동기화 로그 조회", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] 로그 조회 실패: {str(e)}")
        results.add_test("동기화 로그 조회", False, str(e))
        return False

def main():
    """메인 테스트 실행"""
    print("="*80)
    print("백엔드 API 엔드포인트 테스트 시작")
    print("="*80)
    print(f"백엔드 서버: {BASE_URL}")
    print(f"테스트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 서버 헬스 체크
    server_ok = test_1_server_health()
    if not server_ok:
        print("\n❌ 서버가 실행 중이지 않습니다. 서버를 먼저 시작해주세요.")
        results.print_summary()
        return

    # 플레이오토 설정 조회
    test_2_playauto_settings()

    # API 연결 테스트
    test_3_connection_test()

    # 택배사 목록 조회
    test_4_carriers_list()

    # 주문 목록 조회
    orders = test_5_orders_list()

    # 통계 조회
    test_6_stats()

    # 동기화 로그 조회
    test_7_sync_logs()

    # 결과 요약 출력
    results.print_summary()

if __name__ == "__main__":
    main()
