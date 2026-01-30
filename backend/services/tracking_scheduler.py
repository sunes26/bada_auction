"""
송장 업로드 스케줄러

설정된 시간에 자동으로 송장 업로드를 실행합니다.
"""

import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.db import get_db
from services.tracking_upload_service import TrackingUploadService


class TrackingScheduler:
    """송장 업로드 스케줄러"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = get_db()
        self.upload_service = TrackingUploadService()
        self.job_id = None

    def start(self):
        """스케줄러 시작"""
        try:
            # 설정 로드
            config = self._load_config()

            if config and config.get('enabled'):
                # 스케줄 등록
                self._register_schedule(config)

            # 스케줄러 시작
            if not self.scheduler.running:
                self.scheduler.start()
                print("[OK] 송장 업로드 스케줄러 시작")

        except Exception as e:
            print(f"[ERROR] 스케줄러 시작 실패: {e}")

    def stop(self):
        """스케줄러 중지"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                print("[OK] 송장 업로드 스케줄러 중지")
        except Exception as e:
            print(f"[ERROR] 스케줄러 중지 실패: {e}")

    def update_schedule(self, config: dict):
        """스케줄 업데이트"""
        try:
            # 기존 작업 제거
            if self.job_id:
                try:
                    self.scheduler.remove_job(self.job_id)
                except:
                    pass

            # 새 스케줄 등록
            if config.get('enabled'):
                self._register_schedule(config)
                print(f"[OK] 스케줄 업데이트: {config.get('schedule_time')}")
            else:
                print("[OK] 스케줄러 비활성화")

        except Exception as e:
            print(f"[ERROR] 스케줄 업데이트 실패: {e}")

    def _register_schedule(self, config: dict):
        """스케줄 등록"""
        try:
            # 시간 파싱 (HH:MM)
            schedule_time = config.get('schedule_time', '17:00')
            hour, minute = map(int, schedule_time.split(':'))

            # Cron 트리거 생성 (매일 지정 시간)
            trigger = CronTrigger(hour=hour, minute=minute)

            # 작업 등록
            self.job_id = self.scheduler.add_job(
                self._scheduled_upload,
                trigger=trigger,
                id='tracking_upload',
                replace_existing=True,
                kwargs={
                    'retry_count': config.get('retry_count', 3),
                    'notify_discord': config.get('notify_discord', False),
                    'notify_slack': config.get('notify_slack', False)
                }
            ).id

            # 다음 실행 시각 업데이트
            self._update_next_run_time()

            print(f"[OK] 스케줄 등록 완료: 매일 {schedule_time}")

        except Exception as e:
            print(f"[ERROR] 스케줄 등록 실패: {e}")
            raise

    async def _scheduled_upload(self, retry_count: int, notify_discord: bool, notify_slack: bool):
        """스케줄된 업로드 실행"""
        try:
            print(f"[INFO] 자동 송장 업로드 시작: {datetime.now()}")

            # 업로드 실행
            result = await self.upload_service.execute_upload(
                job_type='scheduled',
                retry_count=retry_count,
                notify_discord=notify_discord,
                notify_slack=notify_slack
            )

            # 마지막 실행 시각 업데이트
            self._update_last_run_time()

            print(f"[OK] 자동 송장 업로드 완료: {result}")

        except Exception as e:
            print(f"[ERROR] 자동 송장 업로드 실패: {e}")

    def _load_config(self) -> dict:
        """설정 로드"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT
                    enabled,
                    schedule_time,
                    retry_count,
                    notify_discord,
                    notify_slack
                FROM tracking_upload_scheduler
                WHERE id = 1
            """)

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'enabled': bool(row[0]),
                'schedule_time': row[1],
                'retry_count': row[2],
                'notify_discord': bool(row[3]),
                'notify_slack': bool(row[4])
            }

        except Exception as e:
            print(f"[ERROR] 설정 로드 실패: {e}")
            return None

    def _update_last_run_time(self):
        """마지막 실행 시각 업데이트"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE tracking_upload_scheduler
                SET last_run_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """)
            self.db.conn.commit()
        except Exception as e:
            print(f"[ERROR] 마지막 실행 시각 업데이트 실패: {e}")

    def _update_next_run_time(self):
        """다음 실행 시각 업데이트"""
        try:
            job = self.scheduler.get_job(self.job_id)
            if job and job.next_run_time:
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')

                cursor = self.db.conn.cursor()
                cursor.execute("""
                    UPDATE tracking_upload_scheduler
                    SET next_run_at = ?
                    WHERE id = 1
                """, (next_run,))
                self.db.conn.commit()
        except Exception as e:
            print(f"[ERROR] 다음 실행 시각 업데이트 실패: {e}")


# 전역 스케줄러 인스턴스
_tracking_scheduler = None


def get_tracking_scheduler() -> TrackingScheduler:
    """스케줄러 인스턴스 가져오기"""
    global _tracking_scheduler
    if _tracking_scheduler is None:
        _tracking_scheduler = TrackingScheduler()
    return _tracking_scheduler


def start_tracking_scheduler():
    """스케줄러 시작"""
    scheduler = get_tracking_scheduler()
    scheduler.start()


def stop_tracking_scheduler():
    """스케줄러 중지"""
    scheduler = get_tracking_scheduler()
    scheduler.stop()
