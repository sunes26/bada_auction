"""
스케줄러 상태 조회 API
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status():
    """
    모든 스케줄러의 실행 상태 조회

    Returns:
        {
            "success": True,
            "schedulers": {
                "playauto": {
                    "running": True,
                    "jobs": [
                        {
                            "id": "playauto_auto_fetch_orders",
                            "name": "플레이오토 주문 자동 수집",
                            "next_run": "2026-01-24 22:00:00"
                        },
                        ...
                    ]
                },
                "monitoring": {
                    "running": True,
                    "jobs": [
                        {
                            "id": "monitor_auto_check_products",
                            "name": "상품 자동 모니터링 체크",
                            "next_run": "2026-01-24 21:49:00"
                        }
                    ]
                }
            }
        }
    """
    try:
        from playauto.scheduler import get_scheduler_status as get_playauto_status
        from monitor.scheduler import get_scheduler_status as get_monitor_status
        from backup.scheduler import get_scheduler_status as get_backup_status

        # 플레이오토 스케줄러 상태
        playauto_status = get_playauto_status()

        # 모니터링 스케줄러 상태
        monitor_status = get_monitor_status()

        # 백업 스케줄러 상태
        backup_status = get_backup_status()

        return {
            "success": True,
            "schedulers": {
                "playauto": playauto_status,
                "monitoring": monitor_status,
                "backup": backup_status
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 상태 조회 실패: {str(e)}")


@router.post("/monitoring/restart")
async def restart_monitoring_scheduler():
    """
    모니터링 스케줄러 재시작

    Returns:
        {
            "success": True,
            "message": "모니터링 스케줄러가 재시작되었습니다."
        }
    """
    try:
        from monitor.scheduler import stop_scheduler, start_scheduler

        # 기존 스케줄러 중지
        stop_scheduler()

        # 새로 시작
        start_scheduler()

        return {
            "success": True,
            "message": "모니터링 스케줄러가 재시작되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 재시작 실패: {str(e)}")


@router.post("/playauto/restart")
async def restart_playauto_scheduler():
    """
    플레이오토 스케줄러 재시작

    Returns:
        {
            "success": True,
            "message": "플레이오토 스케줄러가 재시작되었습니다."
        }
    """
    try:
        from playauto.scheduler import stop_scheduler, start_scheduler

        # 기존 스케줄러 중지
        stop_scheduler()

        # 새로 시작
        start_scheduler()

        return {
            "success": True,
            "message": "플레이오토 스케줄러가 재시작되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 재시작 실패: {str(e)}")


@router.get("/backup/status")
async def get_backup_status():
    """
    백업 상태 조회

    Returns:
        {
            "success": True,
            "backup_count": 5,
            "total_size_mb": 25.4,
            "latest_backup": {
                "filename": "monitoring_2026-01-24_02-00-00.db",
                "created_at": "2026-01-24 02:00:00",
                "size_mb": 5.2
            },
            "backups": [...]
        }
    """
    try:
        from backup.backup_manager import get_backup_status as get_status

        status = get_status()

        return {
            "success": True,
            **status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백업 상태 조회 실패: {str(e)}")


@router.post("/backup/now")
async def trigger_backup_now():
    """
    즉시 백업 수행

    Returns:
        {
            "success": True,
            "message": "백업이 완료되었습니다.",
            "backup_info": {...}
        }
    """
    try:
        from backup.backup_manager import backup_database, get_backup_status

        # 백업 수행
        success = backup_database()

        if not success:
            raise HTTPException(status_code=500, detail="백업 수행 실패")

        # 백업 상태 조회
        status = get_backup_status()

        return {
            "success": True,
            "message": "백업이 완료되었습니다.",
            "backup_info": status.get("latest_backup")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백업 수행 실패: {str(e)}")
