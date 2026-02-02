"""
데이터베이스 자동 백업 시스템

매일 새벽 2시 자동 백업 및 7일 이상 된 백업 삭제
(SQLite 전용 - PostgreSQL은 Supabase 대시보드에서 백업)
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path


# 백업 디렉토리 경로
BACKEND_DIR = Path(__file__).parent.parent
BACKUPS_DIR = BACKEND_DIR / 'backups'
DB_FILE = BACKEND_DIR / 'monitoring.db'

# PostgreSQL 사용 여부 확인
USE_POSTGRESQL = os.getenv('USE_POSTGRESQL', 'false').lower() == 'true'


def ensure_backup_directory():
    """백업 디렉토리 생성"""
    BACKUPS_DIR.mkdir(exist_ok=True)
    print(f"[BACKUP] 백업 디렉토리: {BACKUPS_DIR}")


def backup_database():
    """
    데이터베이스 백업 수행
    (SQLite만 지원 - PostgreSQL은 Supabase에서 자동 백업)

    Returns:
        bool: 백업 성공 여부
    """
    try:
        # PostgreSQL 사용 중이면 백업 건너뛰기
        if USE_POSTGRESQL:
            print("[BACKUP] PostgreSQL 사용 중 - 백업 건너뜀 (Supabase에서 자동 백업)")
            return True

        # 백업 디렉토리 확인
        ensure_backup_directory()

        # DB 파일 존재 확인
        if not DB_FILE.exists():
            print(f"[BACKUP] 데이터베이스 파일이 없습니다: {DB_FILE}")
            return False

        # 백업 파일명 생성 (monitoring_2026-01-24_02-00-00.db)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f"monitoring_{timestamp}.db"
        backup_path = BACKUPS_DIR / backup_filename

        # 파일 복사
        shutil.copy2(DB_FILE, backup_path)

        # 파일 크기 확인
        file_size = backup_path.stat().st_size / (1024 * 1024)  # MB

        print(f"[BACKUP] 백업 성공: {backup_filename} ({file_size:.2f} MB)")

        return True

    except Exception as e:
        print(f"[BACKUP ERROR] 백업 실패: {str(e)}")
        return False


def cleanup_old_backups(days: int = 7):
    """
    오래된 백업 파일 삭제

    Args:
        days: 보관 기간 (일)

    Returns:
        int: 삭제된 파일 수
    """
    try:
        # 백업 디렉토리 확인
        if not BACKUPS_DIR.exists():
            return 0

        # 삭제 기준 날짜
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        # 백업 파일 조회
        for backup_file in BACKUPS_DIR.glob('monitoring_*.db'):
            # 파일 수정 시간 확인
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

            # 오래된 파일 삭제
            if file_mtime < cutoff_date:
                print(f"[BACKUP] 오래된 백업 삭제: {backup_file.name} (생성일: {file_mtime.strftime('%Y-%m-%d')})")
                backup_file.unlink()
                deleted_count += 1

        if deleted_count > 0:
            print(f"[BACKUP] {deleted_count}개의 오래된 백업 파일 삭제 완료")

        return deleted_count

    except Exception as e:
        print(f"[BACKUP ERROR] 백업 정리 실패: {str(e)}")
        return 0


def get_backup_status():
    """
    백업 상태 조회

    Returns:
        dict: 백업 정보
    """
    try:
        ensure_backup_directory()

        # 백업 파일 목록
        backups = []
        total_size = 0

        for backup_file in sorted(BACKUPS_DIR.glob('monitoring_*.db'), reverse=True):
            file_stat = backup_file.stat()
            file_size = file_stat.st_size / (1024 * 1024)  # MB
            total_size += file_size

            backups.append({
                "filename": backup_file.name,
                "created_at": datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "size_mb": round(file_size, 2)
            })

        return {
            "backup_count": len(backups),
            "total_size_mb": round(total_size, 2),
            "latest_backup": backups[0] if backups else None,
            "backups": backups[:10]  # 최근 10개만
        }

    except Exception as e:
        return {
            "backup_count": 0,
            "total_size_mb": 0,
            "latest_backup": None,
            "backups": [],
            "error": str(e)
        }


def perform_daily_backup():
    """
    일일 백업 작업 (스케줄러용)

    - 데이터베이스 백업
    - 7일 이상 된 백업 삭제
    """
    print(f"\n[BACKUP] ===== 일일 백업 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")

    # 백업 수행
    success = backup_database()

    if success:
        # 오래된 백업 삭제
        deleted = cleanup_old_backups(days=7)

        # 상태 조회
        status = get_backup_status()
        print(f"[BACKUP] 현재 백업 파일 수: {status['backup_count']}개")
        print(f"[BACKUP] 전체 백업 크기: {status['total_size_mb']} MB")

    print(f"[BACKUP] ===== 일일 백업 완료 =====\n")

    return success


if __name__ == "__main__":
    # 테스트 실행
    print("=== 백업 시스템 테스트 ===\n")

    # 백업 수행
    print("1. 백업 수행")
    perform_daily_backup()

    print("\n2. 백업 상태 조회")
    status = get_backup_status()
    print(f"백업 파일 수: {status['backup_count']}")
    print(f"전체 크기: {status['total_size_mb']} MB")
    if status['latest_backup']:
        print(f"최근 백업: {status['latest_backup']['filename']}")
