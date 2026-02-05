"""PlayAuto 자동 동기화 활성화"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db_wrapper import get_db

def enable_playauto_sync():
    """PlayAuto 자동 동기화 활성화"""
    db = get_db()

    print("=" * 60)
    print("PlayAuto 자동 동기화 활성화")
    print("=" * 60)

    # 현재 설정 확인
    print("\n[현재 설정]")
    print(f"PlayAuto 활성화: {db.get_playauto_setting('enabled')}")
    print(f"자동 동기화: {db.get_playauto_setting('auto_sync_enabled')}")
    print(f"동기화 주기: {db.get_playauto_setting('auto_sync_interval')}분")

    # 설정 업데이트
    print("\n[설정 업데이트 중...]")

    # 1. PlayAuto 활성화
    db.save_playauto_setting('enabled', 'true', notes='PlayAuto 활성화')
    print("[OK] PlayAuto 활성화: True")

    # 2. 자동 동기화 활성화
    db.save_playauto_setting('auto_sync_enabled', 'true', notes='자동 주문 동기화 활성화')
    print("[OK] 자동 동기화: True")

    # 3. 동기화 주기 설정 (30분)
    db.save_playauto_setting('auto_sync_interval', '30', notes='30분마다 주문 수집')
    print("[OK] 동기화 주기: 30분")

    # 업데이트된 설정 확인
    print("\n[업데이트된 설정]")
    print(f"PlayAuto 활성화: {db.get_playauto_setting('enabled')}")
    print(f"자동 동기화: {db.get_playauto_setting('auto_sync_enabled')}")
    print(f"동기화 주기: {db.get_playauto_setting('auto_sync_interval')}분")

    print("\n" + "=" * 60)
    print("[OK] PlayAuto 자동 동기화가 활성화되었습니다!")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. 백엔드 서버를 재시작하세요: python main.py")
    print("2. 30분마다 자동으로 주문이 수집됩니다")
    print("3. 또는 관리자 페이지에서 '수동 동기화' 버튼을 눌러 즉시 수집하세요")
    print()

if __name__ == "__main__":
    enable_playauto_sync()
