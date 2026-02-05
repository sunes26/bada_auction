"""
플레이오토 백그라운드 작업 스케줄러

주기적 주문 수집 및 송장 업로드 자동화
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from database.db_wrapper import get_db
from .orders import fetch_and_sync_orders
from .tracking import auto_upload_tracking_from_local


# 스케줄러 인스턴스
scheduler = AsyncIOScheduler()


async def auto_fetch_orders_job():
    """주문 자동 수집 작업 (30분마다)"""
    print(f"[PLAYAUTO] 주문 자동 수집 시작: {datetime.now()}")

    try:
        # 설정 확인
        db = get_db()
        enabled = db.get_playauto_setting("enabled") == "true"
        auto_sync_enabled = db.get_playauto_setting("auto_sync_enabled") == "true"

        if not enabled or not auto_sync_enabled:
            print("[PLAYAUTO] 자동 동기화가 비활성화되어 있습니다")
            return

        # 주문 수집 및 동기화
        result = await fetch_and_sync_orders()

        if result.get("success"):
            print(f"[PLAYAUTO] 주문 수집 성공: {result.get('synced_count')}개 동기화")

            # Slack/Discord 알림 발송
            try:
                from notifications.notifier import send_notification
                send_notification(
                    'order_sync',
                    f"📦 주문 수집 완료: {result.get('synced_count', 0)}건",
                    market='전체',
                    collected_count=result.get('total', result.get('synced_count', 0)),
                    success_count=result.get('synced_count', 0),
                    fail_count=0
                )
            except Exception as e:
                print(f"[WARN] 주문 동기화 알림 발송 실패: {e}")
        else:
            print(f"[PLAYAUTO] 주문 수집 실패: {result.get('message')}")

    except Exception as e:
        print(f"[ERROR] 주문 자동 수집 중 오류: {e}")


async def auto_upload_tracking_job():
    """송장 자동 업로드 작업 (매일 오전 9시)"""
    print(f"[PLAYAUTO] 송장 자동 업로드 시작: {datetime.now()}")

    try:
        # 설정 확인
        db = get_db()
        enabled = db.get_playauto_setting("enabled") == "true"

        if not enabled:
            print("[PLAYAUTO] 플레이오토가 비활성화되어 있습니다")
            return

        # 송장 업로드 (최근 7일)
        result = await auto_upload_tracking_from_local(days=7)

        if result.get("success"):
            print(f"[PLAYAUTO] 송장 업로드 성공: {result.get('success_count')}개 업로드")
        else:
            print(f"[PLAYAUTO] 송장 업로드 실패: {result.get('message')}")

    except Exception as e:
        print(f"[ERROR] 송장 자동 업로드 중 오류: {e}")


def start_scheduler():
    """스케줄러 시작"""
    try:
        # 설정 확인
        db = get_db()
        import os

        # 환경 변수 우선, DB 설정 대체 (프로덕션 환경 대응)
        # 프로덕션 환경(ENVIRONMENT=production)이면 강제로 활성화
        is_production = os.getenv("ENVIRONMENT") == "production"

        if is_production:
            # 프로덕션에서는 무조건 활성화
            enabled = True
            auto_sync_enabled = True
            print("[PLAYAUTO] 프로덕션 환경 감지: 자동 동기화 강제 활성화")
        else:
            # 개발 환경에서는 환경 변수 또는 DB 설정 사용
            enabled = os.getenv("PLAYAUTO_ENABLED", db.get_playauto_setting("enabled")) == "true"
            auto_sync_enabled = os.getenv("PLAYAUTO_AUTO_SYNC_ENABLED", db.get_playauto_setting("auto_sync_enabled")) == "true"

        auto_sync_interval = int(db.get_playauto_setting("auto_sync_interval") or "30")

        if not enabled:
            print("[PLAYAUTO] 플레이오토가 비활성화되어 있어 스케줄러를 시작하지 않습니다")
            print(f"[PLAYAUTO] enabled={enabled}, is_production={is_production}")
            return

        # 주문 자동 수집 작업 등록 (설정된 주기마다)
        if auto_sync_enabled:
            scheduler.add_job(
                auto_fetch_orders_job,
                trigger=IntervalTrigger(minutes=auto_sync_interval),
                id="playauto_auto_fetch_orders",
                name="플레이오토 주문 자동 수집",
                replace_existing=True,
                misfire_grace_time=60
            )
            print(f"[PLAYAUTO] 주문 자동 수집 작업 등록 ({auto_sync_interval}분마다)")

        # 송장 자동 업로드 작업 등록 (매일 오전 9시)
        scheduler.add_job(
            auto_upload_tracking_job,
            trigger=CronTrigger(hour=9, minute=0),
            id="playauto_auto_upload_tracking",
            name="플레이오토 송장 자동 업로드",
            replace_existing=True,
            misfire_grace_time=300
        )
        print("[PLAYAUTO] 송장 자동 업로드 작업 등록 (매일 오전 9시)")

        # 스케줄러 시작
        scheduler.start()
        print("[PLAYAUTO] 스케줄러 시작 완료")

    except Exception as e:
        print(f"[ERROR] 스케줄러 시작 실패: {e}")


def stop_scheduler():
    """스케줄러 중지"""
    try:
        scheduler.shutdown()
        print("[PLAYAUTO] 스케줄러 중지 완료")
    except Exception as e:
        print(f"[ERROR] 스케줄러 중지 실패: {e}")


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
        print(f"[ERROR] 스케줄러 상태 조회 실패: {e}")
        return {
            "running": False,
            "jobs": [],
            "error": str(e)
        }
