"""프로덕션 환경(Railway) PlayAuto 자동 동기화 활성화 (자동 실행)"""
import requests
import json
import sys

RAILWAY_API_URL = "https://badaauction-production.up.railway.app"

def main():
    print("=" * 70)
    print("프로덕션 환경(Railway) PlayAuto 자동 동기화 활성화")
    print("=" * 70)

    # 1. 현재 상태 확인
    print("\n[1단계] 현재 설정 확인...")
    try:
        response = requests.get(f"{RAILWAY_API_URL}/api/playauto/settings", timeout=10)
        if response.status_code == 200:
            settings = response.json()
            print(f"[OK] 현재 상태:")
            print(f"     - API Key: {settings.get('api_key_masked', 'N/A')}")
            print(f"     - 활성화: {settings.get('enabled', False)}")
            print(f"     - 자동 동기화: {settings.get('auto_sync_enabled', False)}")
            print(f"     - 동기화 주기: {settings.get('auto_sync_interval', 300)}분")
        else:
            print(f"[ERROR] 설정 조회 실패: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 연결 실패: {e}")
        sys.exit(1)

    # 2. 자동 동기화 활성화
    print("\n[2단계] 자동 동기화 활성화 중...")
    payload = {
        "api_key": "UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj",
        "email": "haeseong050321@gmail.com",
        "password": "jhs6312**",
        "api_base_url": "https://openapi.playauto.io/api",
        "enabled": True,
        "auto_sync_enabled": True,
        "auto_sync_interval": 30,
        "encrypt_credentials": False
    }

    try:
        response = requests.post(
            f"{RAILWAY_API_URL}/api/playauto/settings",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"[OK] 설정 저장 성공!")
            print(f"     - {result.get('message', 'PlayAuto 설정 완료')}")
        else:
            print(f"[ERROR] 설정 저장 실패: {response.status_code}")
            print(f"     응답: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 요청 실패: {e}")
        sys.exit(1)

    # 3. 업데이트된 설정 확인
    print("\n[3단계] 업데이트된 설정 확인...")
    try:
        response = requests.get(f"{RAILWAY_API_URL}/api/playauto/settings", timeout=10)
        if response.status_code == 200:
            settings = response.json()
            print(f"[OK] 업데이트된 설정:")
            print(f"     - 활성화: {settings.get('enabled', False)}")
            print(f"     - 자동 동기화: {settings.get('auto_sync_enabled', False)}")
            print(f"     - 동기화 주기: {settings.get('auto_sync_interval', 300)}분")
        else:
            print(f"[WARNING] 설정 재확인 실패: {response.status_code}")
    except Exception as e:
        print(f"[WARNING] 재확인 실패: {e}")

    # 4. 수동 동기화 테스트
    print("\n[4단계] 즉시 주문 수집 테스트...")
    try:
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        print(f"     기간: {start_date} ~ {end_date}")

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
            print(f"[OK] 주문 수집 완료!")
            print(f"     - 총 주문: {result.get('total', 0)}건")
            print(f"     - 동기화: {result.get('synced_count', 0)}건")
            print(f"     - 실행 시간: {result.get('execution_time', 0):.2f}초")

            if result.get('orders'):
                print(f"\n     최근 주문 {min(3, len(result.get('orders', [])))}건:")
                for i, order in enumerate(result.get('orders', [])[:3], 1):
                    print(f"     {i}. 주문번호: {order.get('order_number', 'N/A')}")
                    print(f"        마켓: {order.get('market', 'N/A')} | 고객: {order.get('customer_name', 'N/A')}")
                    print(f"        금액: {order.get('total_amount', 0):,}원")
            else:
                print(f"\n     [INFO] 수집된 주문이 없습니다")
                print(f"     (실제로 PlayAuto 계정에 주문이 없거나, 이미 동기화됨)")
        else:
            print(f"[ERROR] 주문 수집 실패: {response.status_code}")
            print(f"     응답: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")

    print("\n" + "=" * 70)
    print("[완료] 프로덕션 환경 설정 완료!")
    print("=" * 70)
    print("\n✅ 다음부터 자동으로 작동합니다:")
    print("   - 30분마다 자동 주문 수집")
    print("   - 새 주문 발견 시 실시간 알림")
    print("   - 송장 자동 업로드 (매일 오전 9시)")
    print("\n📊 모니터링:")
    print("   - 프론트엔드: https://[your-app].vercel.app/admin")
    print("   - API 상태: https://badaauction-production.up.railway.app/health")
    print("   - 스케줄러: https://badaauction-production.up.railway.app/api/scheduler/status")
    print()

if __name__ == "__main__":
    main()
