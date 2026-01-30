"""
백업 스케줄러

매일 새벽 2시 자동 백업
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backup.backup_manager import perform_daily_backup


# 스케줄러 인스턴스
scheduler = AsyncIOScheduler()


async def daily_backup_job():
    """일일 백업 작업"""
    perform_daily_backup()


def start_scheduler():
    """백업 스케줄러 시작"""
    try:
        # 매일 새벽 2시 백업
        scheduler.add_job(
            daily_backup_job,
            trigger=CronTrigger(hour=2, minute=0),
            id="backup_daily",
            name="데이터베이스 일일 백업",
            replace_existing=True,
            misfire_grace_time=3600  # 1시간
        )

        scheduler.start()
        print("[BACKUP] 백업 스케줄러 시작 완료 (매일 새벽 2시)")

    except Exception as e:
        print(f"[BACKUP ERROR] 백업 스케줄러 시작 실패: {e}")


def stop_scheduler():
    """백업 스케줄러 중지"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            print("[BACKUP] 백업 스케줄러 중지 완료")
    except Exception as e:
        print(f"[BACKUP ERROR] 백업 스케줄러 중지 실패: {e}")


def get_scheduler_status():
    """스케줄러 상태 조회"""
    try:
        if scheduler.running:
            jobs = scheduler.get_jobs()
            return {
                "running": True,
                "jobs": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": str(job.next_run_time) if job.next_run_time else None
                    }
                    for job in jobs
                ]
            }
        else:
            return {
                "running": False,
                "jobs": []
            }
    except Exception as e:
        return {
            "running": False,
            "jobs": [],
            "error": str(e)
        }
