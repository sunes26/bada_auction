"""Railway 환경 변수 테스트"""
import requests

RAILWAY_API_URL = "https://badaauction-production.up.railway.app"

print("=" * 70)
print("Railway 환경 변수 및 디버그 테스트")
print("=" * 70)

# 1. Health check
print("\n[1] Health Check...")
try:
    response = requests.get(f"{RAILWAY_API_URL}/health", timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# 2. 스케줄러 상태
print("\n[2] 스케줄러 상태...")
try:
    response = requests.get(f"{RAILWAY_API_URL}/api/scheduler/status", timeout=10)
    data = response.json()

    playauto = data.get('schedulers', {}).get('playauto', {})
    print(f"PlayAuto Running: {playauto.get('running')}")
    print(f"PlayAuto Jobs: {len(playauto.get('jobs', []))}")

    if not playauto.get('running'):
        print("\n⚠️ PlayAuto 스케줄러가 실행되지 않았습니다!")
except Exception as e:
    print(f"Error: {e}")

# 3. PlayAuto 설정
print("\n[3] PlayAuto 설정...")
try:
    response = requests.get(f"{RAILWAY_API_URL}/api/playauto/settings", timeout=10)
    settings = response.json()
    print(f"enabled: {settings.get('enabled')}")
    print(f"auto_sync_enabled: {settings.get('auto_sync_enabled')}")
    print(f"auto_sync_interval: {settings.get('auto_sync_interval')}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("해결 방법:")
print("=" * 70)
print("\n1. Railway 대시보드 확인:")
print("   - Settings > Variables")
print("   - PLAYAUTO_ENABLED=true 있는지 확인")
print("   - PLAYAUTO_AUTO_SYNC_ENABLED=true 있는지 확인")
print("\n2. Railway 재배포 확인:")
print("   - Deployments 탭에서 최신 배포 완료 확인")
print("   - 로그에서 '[PLAYAUTO]' 메시지 확인")
print("\n3. 환경 변수 이름 정확히 확인:")
print("   - 대소문자 구분: PLAYAUTO_ENABLED (모두 대문자)")
print("   - 값: true (소문자)")
print()
