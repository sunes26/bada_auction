"""로컬 환경에서 PlayAuto 스케줄러 테스트"""
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("로컬 PlayAuto 스케줄러 테스트")
print("=" * 60)

# 환경 변수 로드
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env.local'
if env_path.exists():
    load_dotenv(env_path)
    print(f"\n[OK] .env.local 로드 완료")
else:
    print(f"\n[WARNING] .env.local 없음")

# DB 초기화
from database.db_wrapper import get_db
db = get_db()
print(f"[OK] 데이터베이스 초기화 완료")

# 스케줄러 시작
print("\n" + "=" * 60)
print("스케줄러 시작 중...")
print("=" * 60)

from playauto.scheduler import start_scheduler, get_scheduler_status

try:
    start_scheduler()
    print("\n[OK] 스케줄러 시작 완료")

    # 잠시 대기
    import time
    time.sleep(1)

    # 상태 확인
    print("\n" + "=" * 60)
    print("스케줄러 상태 확인")
    print("=" * 60)

    status = get_scheduler_status()

    print(f"\n[상태]")
    print(f"Running: {status.get('running')}")
    print(f"Jobs: {len(status.get('jobs', []))}")

    if status.get('jobs'):
        print(f"\n[등록된 작업]")
        for i, job in enumerate(status.get('jobs', []), 1):
            print(f"{i}. {job.get('name')}")
            print(f"   ID: {job.get('id')}")
            print(f"   다음 실행: {job.get('next_run_time')}")
    else:
        print("\n[WARNING] 등록된 작업이 없습니다!")

    # 결과 판정
    print("\n" + "=" * 60)
    if status.get('running') and len(status.get('jobs', [])) > 0:
        print("[SUCCESS] 로컬 환경에서 정상 작동!")
        print("=" * 60)
        print("\n다음 체크:")
        print("1. running이 true인지 확인 ✅")
        print("2. jobs에 2개 작업이 있는지 확인 ✅")
        print("   - playauto_auto_fetch_orders")
        print("   - playauto_auto_upload_tracking")
        exit(0)
    else:
        print("[FAILED] 스케줄러가 제대로 시작되지 않았습니다!")
        print("=" * 60)
        exit(1)

except Exception as e:
    print(f"\n[ERROR] 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    # 스케줄러 중지
    from playauto.scheduler import stop_scheduler
    try:
        stop_scheduler()
        print("\n[OK] 스케줄러 중지 완료")
    except:
        pass
