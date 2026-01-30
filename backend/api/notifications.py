"""
Webhook 알림 설정 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from database.db import get_db
from notifications.notifier import send_notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ============= Request/Response 모델 =============

class WebhookSettingRequest(BaseModel):
    webhook_type: str  # 'slack' or 'discord'
    webhook_url: str
    enabled: bool = True
    notification_types: List[str] = ['all']  # ['margin_alert', 'rpa', 'order_sync', 'inventory'] or ['all']


class WebhookToggleRequest(BaseModel):
    enabled: bool


class TestNotificationRequest(BaseModel):
    webhook_type: str  # 'slack' or 'discord'
    notification_type: str = 'margin_alert'  # 테스트할 알림 유형


# ============= API 엔드포인트 =============

@router.post("/webhook/save")
async def save_webhook(request: WebhookSettingRequest):
    """
    Webhook 설정 저장 (INSERT or UPDATE)
    """
    try:
        # 유효성 검사
        if request.webhook_type not in ['slack', 'discord']:
            raise HTTPException(status_code=400, detail="webhook_type은 'slack' 또는 'discord'여야 합니다")

        # URL 검증
        if not request.webhook_url.startswith('https://'):
            raise HTTPException(status_code=400, detail="webhook_url은 https://로 시작해야 합니다")

        # Slack URL 검증
        if request.webhook_type == 'slack' and 'hooks.slack.com' not in request.webhook_url:
            raise HTTPException(status_code=400, detail="유효하지 않은 Slack Webhook URL입니다")

        # Discord URL 검증
        if request.webhook_type == 'discord' and 'discord.com/api/webhooks' not in request.webhook_url:
            raise HTTPException(status_code=400, detail="유효하지 않은 Discord Webhook URL입니다")

        # notification_types를 JSON 문자열로 변환
        import json
        notification_types_str = json.dumps(request.notification_types)

        # DB에 저장
        db = get_db()
        webhook_id = db.save_webhook_setting(
            webhook_type=request.webhook_type,
            webhook_url=request.webhook_url,
            enabled=request.enabled,
            notification_types=notification_types_str
        )

        return {
            "success": True,
            "message": f"{request.webhook_type.capitalize()} Webhook 설정이 저장되었습니다",
            "webhook_id": webhook_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/list")
async def list_webhooks(enabled_only: bool = False):
    """
    저장된 Webhook 목록 조회
    """
    try:
        db = get_db()
        webhooks = db.get_all_webhook_settings(enabled_only=enabled_only)

        # notification_types를 파싱
        import json
        for webhook in webhooks:
            try:
                webhook['notification_types'] = json.loads(webhook['notification_types'])
            except:
                webhook['notification_types'] = ['all']

        return {
            "success": True,
            "webhooks": webhooks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/{webhook_type}")
async def get_webhook(webhook_type: str):
    """
    특정 Webhook 설정 조회
    """
    try:
        if webhook_type not in ['slack', 'discord']:
            raise HTTPException(status_code=400, detail="webhook_type은 'slack' 또는 'discord'여야 합니다")

        db = get_db()
        webhook = db.get_webhook_setting(webhook_type)

        if not webhook:
            return {
                "success": False,
                "message": f"{webhook_type.capitalize()} Webhook 설정이 없습니다",
                "webhook": None
            }

        # notification_types 파싱
        import json
        try:
            webhook['notification_types'] = json.loads(webhook['notification_types'])
        except:
            webhook['notification_types'] = ['all']

        return {
            "success": True,
            "webhook": webhook
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/webhook/{webhook_type}/toggle")
async def toggle_webhook(webhook_type: str, request: WebhookToggleRequest):
    """
    Webhook 활성화/비활성화
    """
    try:
        if webhook_type not in ['slack', 'discord']:
            raise HTTPException(status_code=400, detail="webhook_type은 'slack' 또는 'discord'여야 합니다")

        db = get_db()

        # Webhook이 존재하는지 확인
        webhook = db.get_webhook_setting(webhook_type)
        if not webhook:
            raise HTTPException(status_code=404, detail=f"{webhook_type.capitalize()} Webhook 설정이 없습니다")

        # 활성화/비활성화
        db.toggle_webhook(webhook_type, request.enabled)

        return {
            "success": True,
            "message": f"{webhook_type.capitalize()} Webhook이 {'활성화' if request.enabled else '비활성화'}되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/webhook/{webhook_type}")
async def delete_webhook(webhook_type: str):
    """
    Webhook 설정 삭제
    """
    try:
        if webhook_type not in ['slack', 'discord']:
            raise HTTPException(status_code=400, detail="webhook_type은 'slack' 또는 'discord'여야 합니다")

        db = get_db()

        # Webhook이 존재하는지 확인
        webhook = db.get_webhook_setting(webhook_type)
        if not webhook:
            raise HTTPException(status_code=404, detail=f"{webhook_type.capitalize()} Webhook 설정이 없습니다")

        # 삭제
        db.delete_webhook_setting(webhook_type)

        return {
            "success": True,
            "message": f"{webhook_type.capitalize()} Webhook 설정이 삭제되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_notification(request: TestNotificationRequest):
    """
    테스트 알림 발송
    """
    try:
        if request.webhook_type not in ['slack', 'discord']:
            raise HTTPException(status_code=400, detail="webhook_type은 'slack' 또는 'discord'여야 합니다")

        # Webhook 설정 확인
        db = get_db()
        webhook = db.get_webhook_setting(request.webhook_type)

        if not webhook:
            raise HTTPException(status_code=404, detail=f"{request.webhook_type.capitalize()} Webhook 설정이 없습니다")

        if not webhook['enabled']:
            raise HTTPException(status_code=400, detail=f"{request.webhook_type.capitalize()} Webhook이 비활성화되어 있습니다")

        # 테스트 알림 발송
        if request.notification_type == 'margin_alert':
            result = send_notification(
                'margin_alert',
                "테스트 역마진 경고",
                product_name="테스트 상품",
                sourcing_price=15000,
                selling_price=12000,
                loss=3000
            )
        elif request.notification_type == 'rpa_success':
            result = send_notification(
                'rpa_success',
                "테스트 RPA 성공",
                order_number="TEST-001",
                source="ssg",
                status='success',
                execution_time=12.5,
                product_name="테스트 상품"
            )
        elif request.notification_type == 'rpa_failure':
            result = send_notification(
                'rpa_failure',
                "테스트 RPA 실패",
                order_number="TEST-002",
                source="ssg",
                status='failed',
                execution_time=5.3,
                product_name="테스트 상품",
                error="테스트 에러 메시지"
            )
        elif request.notification_type == 'order_sync':
            result = send_notification(
                'order_sync',
                "테스트 주문 동기화",
                market='전체',
                collected_count=10,
                success_count=8,
                fail_count=2
            )
        elif request.notification_type == 'inventory_out_of_stock':
            result = send_notification(
                'inventory_out_of_stock',
                "테스트 품절 감지",
                product_name="테스트 상품"
            )
        elif request.notification_type == 'inventory_restock':
            result = send_notification(
                'inventory_restock',
                "테스트 재입고 감지",
                product_name="테스트 상품",
                current_price=25000
            )
        elif request.notification_type == 'new_order':
            result = send_notification(
                'new_order',
                "테스트 신규 주문",
                order_number="TEST-20260125-001",
                market="coupang",
                customer_name="홍길동",
                total_amount=49900,
                items=[
                    {"product_name": "무선 마우스", "quantity": 2, "price": 15900},
                    {"product_name": "키보드", "quantity": 1, "price": 34000}
                ]
            )
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 notification_type입니다")

        if result:
            return {
                "success": True,
                "message": f"테스트 알림이 {request.webhook_type.capitalize()}으로 발송되었습니다"
            }
        else:
            raise HTTPException(status_code=500, detail="알림 발송에 실패했습니다")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_webhook_logs(limit: int = 50, webhook_type: Optional[str] = None):
    """
    Webhook 실행 로그 조회
    """
    try:
        if webhook_type and webhook_type not in ['slack', 'discord']:
            raise HTTPException(status_code=400, detail="webhook_type은 'slack' 또는 'discord'여야 합니다")

        db = get_db()
        logs = db.get_webhook_logs(limit=limit, webhook_type=webhook_type)

        return {
            "success": True,
            "logs": logs
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
