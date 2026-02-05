"""프로덕션 환경 PlayAuto 설정 확인 및 수정"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env.local 로드 (DATABASE_URL 확인용)
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

# PostgreSQL 사용 강제
os.environ['USE_POSTGRESQL'] = 'true'

sys.path.insert(0, str(Path(__file__).parent))

from database.db_wrapper import get_db

def check_production_settings():
    """프로덕션 PlayAuto 설정 확인"""

    print("=" * 60)
    print("프로덕션 환경 PlayAuto 설정 확인")
    print("=" * 60)

    try:
        db = get_db()

        # 데이터베이스 타입 확인
        conn = db.get_connection()
        print(f"\n[데이터베이스 타입]")

        # PostgreSQL인지 확인
        try:
            # SQLAlchemy Session 객체인 경우
            if hasattr(conn, 'execute'):
                result = conn.execute("SELECT version()").fetchone()
                if result and 'PostgreSQL' in str(result[0]):
                    print(f"[OK] PostgreSQL 연결됨")
                    print(f"     버전: {result[0][:50]}...")
                else:
                    print(f"[WARNING] SQLite 사용 중 - 프로덕션에서는 PostgreSQL을 사용해야 합니다!")
        except Exception as e:
            print(f"[ERROR] 데이터베이스 확인 실패: {e}")

        # PlayAuto 설정 확인
        print(f"\n[PlayAuto 설정]")
        enabled = db.get_playauto_setting("enabled")
        auto_sync_enabled = db.get_playauto_setting("auto_sync_enabled")
        auto_sync_interval = db.get_playauto_setting("auto_sync_interval")

        print(f"PlayAuto 활성화: {enabled}")
        print(f"자동 동기화: {auto_sync_enabled}")
        print(f"동기화 주기: {auto_sync_interval}분")

        # 환경 변수 확인
        print(f"\n[환경 변수]")
        print(f"USE_POSTGRESQL: {os.getenv('USE_POSTGRESQL')}")
        print(f"DATABASE_URL: {'설정됨' if os.getenv('DATABASE_URL') else '없음'}")
        print(f"PLAYAUTO_API_KEY: {'설정됨' if os.getenv('PLAYAUTO_API_KEY') else '없음'}")
        print(f"PLAYAUTO_SOLUTION_KEY: {'설정됨' if os.getenv('PLAYAUTO_SOLUTION_KEY') else '없음'}")

        # 주문 데이터 확인
        print(f"\n[주문 데이터]")
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM orders")
            count = cursor.fetchone()[0]
            print(f"총 주문: {count}건")

            if count > 0:
                cursor2 = conn.execute("""
                    SELECT order_number, market, customer_name, created_at
                    FROM orders
                    ORDER BY created_at DESC
                    LIMIT 3
                """)
                print(f"\n최근 3개 주문:")
                for row in cursor2.fetchall():
                    print(f"  - {row[0]} | {row[1]} | {row[2]} | {row[3]}")
        except Exception as e:
            print(f"[ERROR] 주문 데이터 조회 실패: {e}")

        # 동기화 로그 확인
        print(f"\n[동기화 로그]")
        try:
            logs = db.get_playauto_sync_logs(limit=3)
            if logs:
                print(f"최근 3개 로그:")
                for log in logs:
                    print(f"  - {log.get('created_at')} | {log.get('status')} | {log.get('items_count')}건")
            else:
                print("동기화 로그 없음")
        except Exception as e:
            print(f"[ERROR] 로그 조회 실패: {e}")

        print("\n" + "=" * 60)

        # 활성화 여부 확인
        if enabled != "true" or auto_sync_enabled != "true":
            print("[WARNING] PlayAuto 자동 동기화가 비활성화되어 있습니다!")
            print("=" * 60)
            return False
        else:
            print("[OK] PlayAuto 설정 정상")
            print("=" * 60)
            return True

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def enable_production_sync():
    """프로덕션 환경 자동 동기화 활성화"""

    print("\n" + "=" * 60)
    print("프로덕션 환경 자동 동기화 활성화")
    print("=" * 60)

    try:
        db = get_db()

        # 설정 업데이트
        print("\n[설정 업데이트]")
        db.save_playauto_setting('enabled', 'true', notes='PlayAuto 활성화 (프로덕션)')
        print("[OK] PlayAuto 활성화")

        db.save_playauto_setting('auto_sync_enabled', 'true', notes='자동 동기화 활성화 (프로덕션)')
        print("[OK] 자동 동기화 활성화")

        db.save_playauto_setting('auto_sync_interval', '30', notes='30분마다 주문 수집 (프로덕션)')
        print("[OK] 동기화 주기: 30분")

        print("\n" + "=" * 60)
        print("[OK] 프로덕션 환경 설정 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. Railway 서버가 자동으로 재시작됩니다")
        print("2. 30분마다 자동으로 주문이 수집됩니다")
        print("3. Railway 로그에서 'PlayAuto 스케줄러 시작' 확인")
        print("4. 또는 API 엔드포인트로 수동 동기화:")
        print("   curl -X GET https://badaauction-production.up.railway.app/api/playauto/orders?auto_sync=true")
        print()

        return True

    except Exception as e:
        print(f"\n[ERROR] 설정 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n프로덕션 환경 체크 시작...\n")

    # 1. 현재 설정 확인
    is_ok = check_production_settings()

    # 2. 비활성화되어 있으면 활성화
    if not is_ok:
        print("\n자동 동기화를 활성화하시겠습니까? (y/n): ", end='')
        choice = input().strip().lower()

        if choice == 'y':
            enable_production_sync()
        else:
            print("\n[INFO] 활성화가 취소되었습니다.")

    print()
