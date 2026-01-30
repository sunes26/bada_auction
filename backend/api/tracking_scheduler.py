"""
송장 자동 업로드 스케줄러 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from services.tracking_upload_service import TrackingUploadService
from services.tracking_scheduler import get_tracking_scheduler

router = APIRouter(prefix="/api/tracking-scheduler", tags=["Tracking Scheduler"])


# ============= Pydantic 모델 =============

class SchedulerConfigRequest(BaseModel):
    """스케줄러 설정 요청"""
    enabled: bool
    schedule_time: str  # HH:MM
    retry_count: int = 3
    notify_discord: bool = False
    notify_slack: bool = False
    discord_webhook: Optional[str] = None
    slack_webhook: Optional[str] = None


class SchedulerConfigResponse(BaseModel):
    """스케줄러 설정 응답"""
    enabled: bool
    schedule_time: str
    retry_count: int
    notify_discord: bool
    notify_slack: bool
    discord_webhook: Optional[str] = None
    slack_webhook: Optional[str] = None
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None


# ============= API 엔드포인트 =============

@router.get("/config")
async def get_scheduler_config():
    """스케줄러 설정 조회"""
    try:
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    enabled,
                    schedule_time,
                    retry_count,
                    notify_discord,
                    notify_slack,
                    discord_webhook,
                    slack_webhook,
                    last_run_at,
                    next_run_at
                FROM tracking_upload_scheduler
                WHERE id = 1
            """)

            row = cursor.fetchone()

            if not row:
                # 기본 설정 반환
                return {
                    'enabled': False,
                    'schedule_time': '17:00',
                    'retry_count': 3,
                    'notify_discord': False,
                    'notify_slack': False,
                    'discord_webhook': None,
                    'slack_webhook': None,
                    'last_run_at': None,
                    'next_run_at': None
                }

            return {
                'enabled': bool(row[0]),
                'schedule_time': row[1],
                'retry_count': row[2],
                'notify_discord': bool(row[3]),
                'notify_slack': bool(row[4]),
                'discord_webhook': row[5],
                'slack_webhook': row[6],
                'last_run_at': row[7],
                'next_run_at': row[8]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 조회 실패: {str(e)}")


@router.post("/config")
async def update_scheduler_config(config: SchedulerConfigRequest):
    """스케줄러 설정 업데이트"""
    try:
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 설정 저장
            cursor.execute("""
                UPDATE tracking_upload_scheduler
                SET
                    enabled = ?,
                    schedule_time = ?,
                    retry_count = ?,
                    notify_discord = ?,
                    notify_slack = ?,
                    discord_webhook = ?,
                    slack_webhook = ?
                WHERE id = 1
            """, (
                config.enabled,
                config.schedule_time,
                config.retry_count,
                config.notify_discord,
                config.notify_slack,
                config.discord_webhook,
                config.slack_webhook
            ))

            conn.commit()

        # 스케줄러 업데이트
        scheduler = get_tracking_scheduler()
        scheduler.update_schedule({
            'enabled': config.enabled,
            'schedule_time': config.schedule_time,
            'retry_count': config.retry_count,
            'notify_discord': config.notify_discord,
            'notify_slack': config.notify_slack
        })

        return {
            'success': True,
            'message': '스케줄러 설정이 업데이트되었습니다'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 업데이트 실패: {str(e)}")


@router.post("/execute")
async def execute_manual_upload():
    """수동 송장 업로드 실행"""
    try:
        # 설정 조회
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT retry_count, notify_discord, notify_slack
                FROM tracking_upload_scheduler
                WHERE id = 1
            """)
            row = cursor.fetchone()

            retry_count = row[0] if row else 3
            notify_discord = bool(row[1]) if row else False
            notify_slack = bool(row[2]) if row else False

        # 업로드 실행
        upload_service = TrackingUploadService()
        result = await upload_service.execute_upload(
            job_type='manual',
            retry_count=retry_count,
            notify_discord=notify_discord,
            notify_slack=notify_slack
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"송장 업로드 실패: {str(e)}")


@router.get("/jobs/recent")
async def get_recent_jobs(limit: int = 10):
    """최근 작업 목록 조회"""
    try:
        upload_service = TrackingUploadService()
        jobs = upload_service.get_recent_jobs(limit=limit)

        return {
            'success': True,
            'jobs': jobs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 목록 조회 실패: {str(e)}")


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: int):
    """작업 상태 조회"""
    try:
        upload_service = TrackingUploadService()
        job = upload_service.get_job_status(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

        return {
            'success': True,
            'job': job
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 상태 조회 실패: {str(e)}")


@router.get("/jobs/{job_id}/details")
async def get_job_details(job_id: int):
    """작업 상세 내역 조회 (개별 주문별)"""
    try:
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    order_no,
                    carrier_code,
                    tracking_number,
                    status,
                    retry_attempt,
                    error_message,
                    uploaded_at
                FROM tracking_upload_details
                WHERE job_id = ?
                ORDER BY created_at ASC
            """, (job_id,))

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            details = []
            for row in rows:
                detail = dict(zip(columns, row))
                details.append(detail)

            return {
                'success': True,
                'details': details
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상세 내역 조회 실패: {str(e)}")


@router.get("/pending-count")
async def get_pending_count():
    """업로드 대기 중인 주문 수 조회"""
    try:
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(DISTINCT o.id)
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE oi.tracking_number IS NOT NULL
                  AND oi.tracking_number != ''
                  AND (o.tracking_uploaded_at IS NULL OR o.synced_to_playauto = 0)
                  AND o.order_status NOT IN ('취소', '반품', '교환', 'cancelled', 'failed')
            """)

            count = cursor.fetchone()[0]

            return {
                'success': True,
                'pending_count': count
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대기 주문 수 조회 실패: {str(e)}")
