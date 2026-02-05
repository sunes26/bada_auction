"""프로덕션 DB에 PlayAuto 설정을 직접 업데이트"""
import os
import sys
from pathlib import Path

# Railway 프로덕션 환경 변수 설정
os.environ['USE_POSTGRESQL'] = 'true'
os.environ['DATABASE_URL'] = 'postgresql://postgres.spkeunlwkrqkdwunkufy:jhs631200!!@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres'

sys.path.insert(0, str(Path(__file__).parent))

from database.db_wrapper import get_db

def update_settings():
    """PlayAuto 설정 업데이트"""
    print("=" * 60)
    print("프로덕션 DB PlayAuto 설정 업데이트")
    print("=" * 60)

    try:
        db = get_db()

        print("\n[현재 설정]")
        print(f"enabled: {db.get_playauto_setting('enabled')}")
        print(f"auto_sync_enabled: {db.get_playauto_setting('auto_sync_enabled')}")
        print(f"auto_sync_interval: {db.get_playauto_setting('auto_sync_interval')}")

        print("\n[설정 업데이트 중...]")

        # 1. PlayAuto 활성화
        db.save_playauto_setting('enabled', 'true', notes='PlayAuto 활성화 (프로덕션)')
        print("[OK] enabled = true")

        # 2. 자동 동기화 활성화
        db.save_playauto_setting('auto_sync_enabled', 'true', notes='자동 동기화 활성화 (프로덕션)')
        print("[OK] auto_sync_enabled = true")

        # 3. 동기화 주기
        db.save_playauto_setting('auto_sync_interval', '30', notes='30분마다 주문 수집')
        print("[OK] auto_sync_interval = 30")

        print("\n[업데이트 완료]")
        print(f"enabled: {db.get_playauto_setting('enabled')}")
        print(f"auto_sync_enabled: {db.get_playauto_setting('auto_sync_enabled')}")
        print(f"auto_sync_interval: {db.get_playauto_setting('auto_sync_interval')}")

        print("\n" + "=" * 60)
        print("[성공] 설정 업데이트 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. Railway 서버 재시작 (Redeploy)")
        print("2. 스케줄러 상태 확인")
        print("3. 30분 후 자동 주문 수집 확인")
        print()

        return True

    except Exception as e:
        print(f"\n[ERROR] 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_settings()
