"""
WebSocket 실시간 알림 시스템
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from datetime import datetime
import json
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket 연결 관리"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """새 WebSocket 연결"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 연결: 총 {len(self.active_connections)}개")

    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket 연결 해제: 남은 {len(self.active_connections)}개")

    async def broadcast(self, message: Dict[str, Any]):
        """모든 연결에 메시지 전송"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.append(connection)

        # 실패한 연결 제거
        for connection in disconnected:
            self.disconnect(connection)


# 전역 연결 관리자
manager = ConnectionManager()


@router.websocket("/notifications")
async def websocket_endpoint(websocket: WebSocket):
    """
    실시간 알림 WebSocket 엔드포인트

    클라이언트 연결: ws://localhost:8000/ws/notifications
    """
    await manager.connect(websocket)

    try:
        while True:
            # 클라이언트로부터 메시지 수신 (연결 유지용)
            data = await websocket.receive_text()
            logger.debug(f"WebSocket 메시지 수신: {data}")

            # ping 응답
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket 정상 종료")
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        manager.disconnect(websocket)


async def notify_order_created(order_id: int, order_number: str, market: str, total_amount: float):
    """새 주문 알림"""
    message = {
        "type": "order_created",
        "data": {
            "order_id": order_id,
            "order_number": order_number,
            "market": market,
            "total_amount": total_amount
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message)
    logger.info(f"[WebSocket] 주문 생성 알림: {order_number}")


async def notify_order_updated(order_id: int, order_number: str, status: str):
    """주문 상태 변경 알림"""
    message = {
        "type": "order_updated",
        "data": {
            "order_id": order_id,
            "order_number": order_number,
            "status": status
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message)
    logger.info(f"[WebSocket] 주문 상태 변경 알림: {order_number} → {status}")


async def notify_tracking_uploaded(order_id: int, order_number: str, tracking_number: str):
    """송장 번호 업로드 알림"""
    message = {
        "type": "tracking_uploaded",
        "data": {
            "order_id": order_id,
            "order_number": order_number,
            "tracking_number": tracking_number
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message)
    logger.info(f"[WebSocket] 송장 업로드 알림: {order_number} → {tracking_number}")


async def notify_product_registered(product_id: int, product_name: str, market: str):
    """상품 등록 알림"""
    message = {
        "type": "product_registered",
        "data": {
            "product_id": product_id,
            "product_name": product_name,
            "market": market
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message)
    logger.info(f"[WebSocket] 상품 등록 알림: {product_name} → {market}")


async def notify_price_alert(product_name: str, old_price: float, new_price: float, margin: float):
    """가격 변동/역마진 알림"""
    message = {
        "type": "price_alert",
        "data": {
            "product_name": product_name,
            "old_price": old_price,
            "new_price": new_price,
            "margin": margin
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message)
    logger.info(f"[WebSocket] 가격 알림: {product_name} {old_price:,}원 → {new_price:,}원")
