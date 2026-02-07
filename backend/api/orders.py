"""
주문 관리 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database.db_wrapper import get_db
from database.database_manager import get_database_manager
from utils.cache import async_cached
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


# Request 모델

class CreateOrderRequest(BaseModel):
    """주문 생성 요청"""
    order_number: str
    market: str  # 'coupang', 'naver', '11st', 'gmarket' 등
    customer_name: str
    customer_phone: Optional[str] = None
    customer_address: str
    customer_zipcode: Optional[str] = None
    total_amount: float
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class CreateOrderItemRequest(BaseModel):
    """주문 상품 생성 요청"""
    product_name: str
    product_url: str  # 소싱처 URL
    source: str  # 'ssg', 'traders', '11st', 'gmarket', 'smartstore'
    quantity: int = 1
    sourcing_price: float
    selling_price: float
    monitored_product_id: Optional[int] = None


class AutoOrderRequest(BaseModel):
    """자동 발주 요청 (Deprecated)"""
    order_item_id: int
    headless: bool = True
    test_mode: bool = False


class SourcingAccountRequest(BaseModel):
    """소싱처 계정 등록 요청"""
    source: str
    account_id: str
    account_password: str
    payment_method: Optional[str] = None
    payment_info: Optional[str] = None
    notes: Optional[str] = None


# API 엔드포인트

@router.post("/create")
async def create_order(request: CreateOrderRequest):
    """
    새로운 주문 생성
    """
    try:
        db = get_db()

        # 주문 추가
        order_id = db.add_order(
            order_number=request.order_number,
            market=request.market,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            customer_address=request.customer_address,
            customer_zipcode=request.customer_zipcode,
            total_amount=request.total_amount,
            payment_method=request.payment_method,
            notes=request.notes
        )

        # 주문 상품 조회 (알림용)
        order_items = db.get_order_items(order_id)

        # 주문 생성 알림 발송
        try:
            from notifications.notifier import send_notification
            send_notification(
                notification_type="new_order",
                message=f"새로운 주문이 생성되었습니다: {request.order_number}",
                order_number=request.order_number,
                market=request.market,
                customer_name=request.customer_name,
                total_amount=request.total_amount,
                items=order_items if order_items else []
            )
        except Exception as e:
            print(f"[WARN] 주문 생성 알림 발송 실패: {e}")

        # WebSocket 실시간 알림
        try:
            from api.websocket import notify_order_created
            await notify_order_created(
                order_id=order_id,
                order_number=request.order_number,
                market=request.market,
                total_amount=request.total_amount
            )
        except Exception as e:
            print(f"[WARN] WebSocket 알림 실패: {e}")

        return {
            "success": True,
            "order_id": order_id,
            "message": "주문이 생성되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 생성 실패: {str(e)}")


@router.post("/order/{order_id}/add-item")
async def add_order_item(order_id: int, request: CreateOrderItemRequest):
    """
    주문에 상품 추가
    """
    try:
        db = get_db()

        # 주문 존재 확인
        order = db.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")

        # 주문 상품 추가
        order_item_id = db.add_order_item(
            order_id=order_id,
            product_name=request.product_name,
            product_url=request.product_url,
            source=request.source,
            sourcing_price=request.sourcing_price,
            selling_price=request.selling_price,
            quantity=request.quantity,
            monitored_product_id=request.monitored_product_id
        )

        return {
            "success": True,
            "order_item_id": order_item_id,
            "message": "주문 상품이 추가되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 추가 실패: {str(e)}")


@router.get("/list")
@async_cached(ttl=15)  # 15초 캐싱
async def get_orders(status: Optional[str] = None, limit: int = 100):
    """
    주문 목록 조회
    """
    try:
        db = get_db()
        orders = db.get_all_orders(status=status, limit=limit)

        return {
            "success": True,
            "orders": orders,
            "total": len(orders)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 조회 실패: {str(e)}")


@router.get("/with-items")
@async_cached(ttl=15)  # 15초 캐싱
async def get_orders_with_items(
    status: Optional[str] = None,
    limit: int = 50,
    page: int = 1
):
    """
    주문 목록과 주문 상품을 한번에 조회 (N+1 쿼리 방지, 서버 사이드 페이지네이션)

    Args:
        status: 주문 상태 필터 ('pending', 'processing', 'completed', 'cancelled')
        limit: 페이지당 항목 수 (기본 50)
        page: 페이지 번호 (1부터 시작)

    Returns:
        {
            "success": True,
            "orders": [...],
            "total": 100,
            "page": 1,
            "limit": 50,
            "total_pages": 2
        }
    """
    try:
        from database.database_manager import get_database_manager

        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        # Placeholder (PostgreSQL: %s, SQLite: ?)
        placeholder = "?" if db_manager.is_sqlite else "%s"

        # 전체 개수 조회
        if status:
            cursor.execute(f"SELECT COUNT(*) FROM orders WHERE order_status = {placeholder}", (status,))
        else:
            cursor.execute("SELECT COUNT(*) FROM orders")
        total_count = cursor.fetchone()[0]

        # 페이지네이션 계산
        offset = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit  # 올림 나눗셈

        # 주문 목록 조회 (LIMIT, OFFSET 적용)
        if status:
            cursor.execute(f"""
                SELECT id, order_number, market, customer_name, customer_phone,
                       customer_address, total_amount, order_status, created_at, updated_at,
                       tracking_number, order_date, sync_source, playauto_order_id
                FROM orders
                WHERE order_status = {placeholder}
                ORDER BY created_at DESC
                LIMIT {placeholder} OFFSET {placeholder}
            """, (status, limit, offset))
        else:
            cursor.execute(f"""
                SELECT id, order_number, market, customer_name, customer_phone,
                       customer_address, total_amount, order_status, created_at, updated_at,
                       tracking_number, order_date, sync_source, playauto_order_id
                FROM orders
                ORDER BY created_at DESC
                LIMIT {placeholder} OFFSET {placeholder}
            """, (limit, offset))

        # Row를 dict로 변환 (안전한 방식 - cursor.description 사용)
        columns = [col[0] for col in cursor.description]
        orders = []
        for row in cursor.fetchall():
            order_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # datetime을 문자열로 변환
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                order_dict[col] = value
            orders.append(order_dict)

        # 각 주문의 상품 조회 (N+1 쿼리 방지 - 배치 조회)
        db = get_db()
        order_ids = [order['id'] for order in orders]
        all_items = db.get_order_items_batch(order_ids)
        for order in orders:
            order['items'] = all_items.get(order['id'], [])

        conn.close()

        return {
            "success": True,
            "orders": orders,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }

    except Exception as e:
        logger.error(f"[주문] with-items 조회 실패: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"주문 조회 실패: {str(e)}")


@router.get("/order/{order_id}")
async def get_order_detail(order_id: int):
    """
    주문 상세 정보 조회
    """
    try:
        db = get_db()

        order = db.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")

        order_items = db.get_order_items(order_id)

        return {
            "success": True,
            "order": order,
            "items": order_items
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 조회 실패: {str(e)}")


@router.get("/pending-items")
async def get_pending_items(limit: int = 50):
    """
    자동 발주 대기 중인 상품 목록 조회
    """
    try:
        db = get_db()
        items = db.get_pending_order_items(limit=limit)

        return {
            "success": True,
            "items": items,
            "total": len(items)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.post("/auto-order")
async def auto_order(request: AutoOrderRequest):
    """
    RPA 자동 발주 실행 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 자동 발주 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


@router.get("/item/{order_item_id}/logs")
async def get_order_item_logs(order_item_id: int):
    """
    주문 상품의 RPA 실행 로그 조회
    """
    try:
        db = get_db()
        logs = db.get_auto_order_logs(order_item_id)

        return {
            "success": True,
            "logs": logs,
            "total": len(logs)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 조회 실패: {str(e)}")


@router.post("/sourcing-account")
async def register_sourcing_account(request: SourcingAccountRequest):
    """
    소싱처 계정 등록
    """
    try:
        db = get_db()

        # 계정 추가 (보안 주의: 실제 운영에서는 비밀번호 암호화 필수!)
        account_id = db.add_sourcing_account(
            source=request.source,
            account_id=request.account_id,
            account_password=request.account_password,
            payment_method=request.payment_method,
            payment_info=request.payment_info,
            notes=request.notes
        )

        return {
            "success": True,
            "message": f"{request.source} 계정이 등록되었습니다.",
            "account_id": account_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계정 등록 실패: {str(e)}")


@router.get("/sourcing-accounts")
async def get_sourcing_accounts():
    """
    등록된 소싱처 계정 목록 조회
    """
    try:
        db = get_db()
        accounts = db.get_all_sourcing_accounts()

        # 비밀번호 마스킹
        for account in accounts:
            if account.get('account_password'):
                account['account_password'] = '****'
            if account.get('payment_info'):
                account['payment_info'] = '****'

        return {
            "success": True,
            "accounts": accounts,
            "total": len(accounts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/rpa/stats")
@async_cached(ttl=60)  # 1분 캐싱
async def get_rpa_stats():
    """
    RPA 통계 조회
    """
    try:
        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        try:
            # 총 실행 횟수
            cursor.execute("SELECT COUNT(*) FROM auto_order_logs")
            total_executions = cursor.fetchone()[0]

            # 성공/실패 횟수
            cursor.execute("SELECT COUNT(*) FROM auto_order_logs WHERE status = 'success'")
            successful_executions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM auto_order_logs WHERE status = 'failed'")
            failed_executions = cursor.fetchone()[0]

            # 평균 실행 시간
            cursor.execute("SELECT AVG(execution_time) FROM auto_order_logs WHERE status = 'success'")
            avg_execution_time = cursor.fetchone()[0] or 0

            # 오늘 실행 횟수
            if db_manager.is_sqlite:
                cursor.execute("""
                    SELECT COUNT(*) FROM auto_order_logs
                    WHERE DATE(created_at) = DATE('now')
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM auto_order_logs
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
            today_executions = cursor.fetchone()[0]

            # 성공률 계산
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

            return {
                "success": True,
                "stats": {
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "failed_executions": failed_executions,
                    "success_rate": round(success_rate, 1),
                    "avg_execution_time": round(avg_execution_time, 1),
                    "today_executions": today_executions
                }
            }
        finally:
            conn.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/rpa/stats/by-source")
@async_cached(ttl=60)  # 1분 캐싱
async def get_rpa_stats_by_source():
    """
    소싱처별 RPA 통계 조회
    """
    try:
        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        try:
            # 소싱처별 통계
            cursor.execute("""
                SELECT
                    source,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    AVG(CASE WHEN status = 'success' THEN execution_time ELSE NULL END) as avg_time
                FROM auto_order_logs
                GROUP BY source
                ORDER BY total DESC
            """)

            rows = cursor.fetchall()

            stats = []
            for row in rows:
                source, total, success_count, failed_count, avg_time = row
                success_rate = (success_count / total * 100) if total > 0 else 0

                stats.append({
                    "source": source,
                    "total_executions": total,
                    "successful_executions": success_count,
                    "failed_executions": failed_count,
                    "success_rate": round(success_rate, 1),
                    "avg_execution_time": round(avg_time, 1) if avg_time else 0
                })

            return {
                "success": True,
                "stats": stats
            }
        finally:
            conn.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/rpa/history")
async def get_rpa_history(limit: int = 50, status: Optional[str] = None):
    """
    RPA 실행 내역 조회
    """
    try:
        db = get_db()

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 쿼리 작성
            query = """
                SELECT
                    l.id,
                    l.order_item_id,
                    l.source,
                    l.action,
                    l.status,
                    l.message,
                    l.error_details,
                    l.execution_time,
                    l.created_at,
                    oi.product_name,
                    oi.product_url,
                    o.order_number,
                    o.customer_name
                FROM auto_order_logs l
                LEFT JOIN order_items oi ON l.order_item_id = oi.id
                LEFT JOIN orders o ON oi.order_id = o.id
            """

            params = []
            if status:
                query += " WHERE l.status = ?"
                params.append(status)

            query += " ORDER BY l.created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "order_item_id": row[1],
                "source": row[2],
                "action": row[3],
                "status": row[4],
                "message": row[5],
                "error_details": row[6],
                "execution_time": row[7],
                "created_at": row[8],
                "product_name": row[9],
                "product_url": row[10],
                "order_number": row[11],
                "customer_name": row[12]
            })

        return {
            "success": True,
            "history": history,
            "total": len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실행 내역 조회 실패: {str(e)}")


@router.get("/rpa/daily-stats")
@async_cached(ttl=300)  # 5분 캐싱 (일별 통계는 덜 자주 변경됨)
async def get_daily_rpa_stats(days: int = 7):
    """
    일별 RPA 실행 통계 (최근 N일)
    """
    try:
        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        try:
            # 일별 통계
            placeholder = "?" if db_manager.is_sqlite else "%s"
            if db_manager.is_sqlite:
                query = f"""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                    FROM auto_order_logs
                    WHERE created_at >= DATE('now', '-' || {placeholder} || ' days')
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """
            else:
                query = f"""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                    FROM auto_order_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '{placeholder} days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """
                # PostgreSQL은 다른 방식으로 처리
                query = f"""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                    FROM auto_order_logs
                    WHERE created_at >= CURRENT_DATE - ({placeholder} || ' days')::INTERVAL
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """

            cursor.execute(query, (days,))
            rows = cursor.fetchall()

            daily_stats = []
            for row in rows:
                date, total, success_count, failed_count = row
                success_rate = (success_count / total * 100) if total > 0 else 0

                daily_stats.append({
                    "date": str(date) if date else None,
                    "total_executions": total,
                    "successful_executions": success_count,
                    "failed_executions": failed_count,
                    "success_rate": round(success_rate, 1)
                })

            return {
                "success": True,
                "daily_stats": daily_stats
            }
        finally:
            conn.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일별 통계 조회 실패: {str(e)}")


# RPA 관련 함수는 제거되었습니다.
# 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요.


# ============================================
# 반자동 RPA 엔드포인트 (Deprecated)
# ============================================

@router.post("/browser/start")
async def start_browser():
    """
    브라우저 시작 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 브라우저 관리 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


@router.post("/browser/stop")
async def stop_browser():
    """
    브라우저 중지 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 브라우저 관리 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


@router.get("/browser/status")
async def get_browser_status():
    """
    브라우저 상태 조회 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 브라우저 관리 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


@router.post("/semi-auto/step1")
async def semi_auto_step1():
    """
    Step 1: 상품 페이지 열기 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 반자동 발주 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


@router.post("/semi-auto/step3")
async def semi_auto_step3():
    """
    Step 3: 배송지 자동 입력 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 반자동 발주 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


@router.post("/semi-auto/step4")
async def semi_auto_step4():
    """
    Step 4: 송장번호 추출 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 반자동 발주 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


# ============================================
# 송장번호 자동 조회 엔드포인트 (Deprecated)
# ============================================

@router.post("/fetch-tracking/{order_item_id}")
async def fetch_tracking(order_item_id: int):
    """
    송장번호 조회 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 송장번호 조회 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


@router.post("/fetch-all-tracking")
async def fetch_all_tracking(limit: int = 10):
    """
    송장번호 일괄 조회 (Deprecated)
    """
    raise HTTPException(
        status_code=410,
        detail="RPA 송장번호 조회 기능은 제거되었습니다. 플레이오토 자동 주문 수집 기능(/api/playauto)을 사용하세요."
    )


# ============================================
# 주문 삭제 엔드포인트
# ============================================

@router.delete("/{order_id}")
async def delete_order(order_id: int):
    """
    주문 삭제 (주문 상품도 함께 삭제됨)
    """
    try:
        db = get_db()

        # 주문 존재 확인
        order = db.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")

        # 주문 상품 먼저 삭제
        with db.get_connection() as conn:
            # order_items 삭제
            conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))

            # auto_order_logs 삭제 (order_item_id가 외래키로 연결된 경우)
            conn.execute("""
                DELETE FROM auto_order_logs
                WHERE order_item_id IN (
                    SELECT id FROM order_items WHERE order_id = ?
                )
            """, (order_id,))

            # 주문 삭제
            conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            conn.commit()

        return {
            "success": True,
            "message": f"주문 #{order['order_number']}이(가) 삭제되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 삭제 실패: {str(e)}")
