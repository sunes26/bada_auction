"""프로덕션 환경(Railway) PlayAuto 자동 동기화 활성화"""
import requests
import json

RAILWAY_API_URL = "https://badaauction-production.up.railway.app"

def check_production_status():
    """프로덕션 PlayAuto 상태 확인"""
    print("=" * 70)
    print("프로덕션 환경(Railway) PlayAuto 상태 확인")
    print("=" * 70)

    try:
        # 1. Health Check
        print("\n[1] Railway 서버 상태...")
        response = requests.get(f"{RAILWAY_API_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 서버 정상 작동")
            print(f"     - 데이터베이스: {data.get('database')}")
            print(f"     - 환경: {'production' if data.get('environment') == 'true' else 'development'}")
        else:
            print(f"[ERROR] 서버 응답 실패: {response.status_code}")
            return False

        # 2. PlayAuto 설정 확인
        print("\n[2] PlayAuto 현재 설정...")
        response = requests.get(f"{RAILWAY_API_URL}/api/playauto/settings", timeout=10)
        if response.status_code == 200:
            settings = response.json()
            print(f"     - API Key: {settings.get('api_key_masked', 'N/A')}")
            print(f"     - 활성화: {settings.get('enabled', False)}")
            print(f"     - 자동 동기화: {settings.get('auto_sync_enabled', False)}")
            print(f"     - 동기화 주기: {settings.get('auto_sync_interval', 'N/A')}분")
            print(f"     - 마지막 동기화: {settings.get('last_sync_at', 'N/A')}")

            if not settings.get('enabled') or not settings.get('auto_sync_enabled'):
                print("\n[WARNING] PlayAuto 자동 동기화가 비활성화되어 있습니다!")
                return settings
            else:
                print("\n[OK] PlayAuto 자동 동기화가 활성화되어 있습니다!")
                return settings
        else:
            print(f"[ERROR] 설정 조회 실패: {response.status_code}")
            return None

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        return None

def enable_production_sync():
    """프로덕션 환경 자동 동기화 활성화"""
    print("\n" + "=" * 70)
    print("프로덕션 환경 자동 동기화 활성화")
    print("=" * 70)

    # Railway 환경 변수에서 API 키 로드 (Railway에 이미 설정되어 있어야 함)
    payload = {
        "api_key": "UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj",  # Railway 환경변수에서
        "email": "haeseong050321@gmail.com",
        "password": "jhs6312**",
        "api_base_url": "https://openapi.playauto.io/api",
        "enabled": True,
        "auto_sync_enabled": True,
        "auto_sync_interval": 30,
        "encrypt_credentials": False
    }

    try:
        print("\n[설정 전송 중...]")
        response = requests.post(
            f"{RAILWAY_API_URL}/api/playauto/settings",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n[OK] 설정 저장 성공!")
            print(f"     - {result.get('message', 'PlayAuto 설정 완료')}")
            print(f"     - API Key: {result.get('api_key_masked', 'N/A')}")
            return True
        else:
            print(f"\n[ERROR] 설정 저장 실패: {response.status_code}")
            print(f"     응답: {response.text}")
            return False

    except Exception as e:
        print(f"\n[ERROR] 요청 실패: {e}")
        return False

def test_manual_sync():
    """수동 주문 동기화 테스트"""
    print("\n" + "=" * 70)
    print("수동 주문 동기화 테스트")
    print("=" * 70)

    try:
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        print(f"\n[주문 수집 중...] 기간: {start_date} ~ {end_date}")

        response = requests.get(
            f"{RAILWAY_API_URL}/api/playauto/orders",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "auto_sync": "true",
                "limit": 100
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n[OK] 주문 수집 성공!")
            print(f"     - 성공: {result.get('success', False)}")
            print(f"     - 총 주문: {result.get('total', 0)}건")
            print(f"     - 동기화: {result.get('synced_count', 0)}건")
            print(f"     - 실행 시간: {result.get('execution_time', 'N/A')}초")

            if result.get('orders'):
                print(f"\n     최근 주문:")
                for i, order in enumerate(result.get('orders', [])[:3], 1):
                    print(f"     {i}. {order.get('order_number', 'N/A')} | "
                          f"{order.get('market', 'N/A')} | "
                          f"{order.get('customer_name', 'N/A')}")
            else:
                print(f"\n     [INFO] 수집된 주문이 없습니다 (실제로 PlayAuto에 주문이 없음)")

            return True
        else:
            print(f"\n[ERROR] 주문 수집 실패: {response.status_code}")
            print(f"     응답: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"\n[ERROR] 요청 실패: {e}")
        return False

if __name__ == "__main__":
    print("\n프로덕션 환경(Railway) 체크 시작...\n")

    # 1. 현재 상태 확인
    settings = check_production_status()

    if settings is None:
        print("\n[ERROR] 프로덕션 서버에 연결할 수 없습니다!")
        exit(1)

    # 2. 비활성화되어 있으면 활성화
    if not settings.get('enabled') or not settings.get('auto_sync_enabled'):
        print("\n자동 동기화를 활성화하시겠습니까? (y/n): ", end='')
        choice = input().strip().lower()

        if choice == 'y':
            success = enable_production_sync()

            if success:
                print("\n" + "=" * 70)
                print("[OK] 프로덕션 환경 설정 완료!")
                print("=" * 70)
                print("\n다음 단계:")
                print("1. ✅ Railway 서버가 자동으로 재시작됩니다 (약 2-3분 소요)")
                print("2. ✅ 30분마다 자동으로 주문이 수집됩니다")
                print("3. 📊 Railway 로그 확인:")
                print("   https://railway.app/project/[your-project]/deployments")
                print("4. 🔍 스케줄러 상태 확인:")
                print("   https://badaauction-production.up.railway.app/api/scheduler/status")
                print()

                # 3. 수동 동기화 테스트
                print("\n즉시 주문을 수집 테스트하시겠습니까? (y/n): ", end='')
                test_choice = input().strip().lower()

                if test_choice == 'y':
                    test_manual_sync()
        else:
            print("\n[INFO] 활성화가 취소되었습니다.")
    else:
        print("\n[OK] 이미 활성화되어 있습니다. 수동 동기화 테스트를 하시겠습니까? (y/n): ", end='')
        test_choice = input().strip().lower()

        if test_choice == 'y':
            test_manual_sync()

    print("\n완료!\n")
