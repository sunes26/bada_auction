"""
통합 대시보드 API
여러 API 호출을 하나로 통합하여 성능 최적화
"""
from fastapi import APIRouter, HTTPException
from database.db_wrapper import get_db
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/all")
async def get_all_dashboard_data():
    """
    대시보드에 필요한 모든 데이터를 한 번에 조회
    - RPA 통계
    - PlayAuto 통계
    - 모니터링 통계
    - 최근 주문 목록
    - 전체 주문 통계
    """
    try:
        db = get_db()
        conn = db.get_connection()

        # 1. RPA 통계 (기존 /api/orders/rpa/stats)
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = '대기' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = '완료' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = '실패' THEN 1 ELSE 0 END) as failed
            FROM rpa_orders
        """)
        rpa_row = cursor.fetchone()
        rpa_stats = {
            "total": rpa_row[0] if rpa_row else 0,
            "pending": rpa_row[1] if rpa_row else 0,
            "completed": rpa_row[2] if rpa_row else 0,
            "failed": rpa_row[3] if rpa_row else 0
        }

        # 2. PlayAuto 통계 (기존 /api/playauto/stats)
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_products,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_products
            FROM selling_products
            WHERE playauto_product_no IS NOT NULL
        """)
        playauto_row = cursor.fetchone()
        playauto_stats = {
            "total_products": playauto_row[0] if playauto_row else 0,
            "active_products": playauto_row[1] if playauto_row else 0
        }

        # 3. 모니터링 통계 (기존 /api/monitor/dashboard/stats)
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN has_margin_issue = 1 THEN 1 ELSE 0 END) as margin_issues
            FROM monitoring_products
        """)
        monitor_row = cursor.fetchone()
        monitor_stats = {
            "total": monitor_row[0] if monitor_row else 0,
            "active": monitor_row[1] if monitor_row else 0,
            "margin_issues": monitor_row[2] if monitor_row else 0
        }

        # 4. 최근 주문 목록 (limit 10)
        cursor = conn.execute("""
            SELECT id, order_number, market, customer_name, total_amount,
                   status, created_at, updated_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_orders = [dict(row) for row in cursor.fetchall()]

        # 5. 전체 주문 통계 (with items, limit 50)
        cursor = conn.execute("""
            SELECT o.id, o.order_number, o.market, o.customer_name,
                   o.total_amount, o.status, o.created_at, o.updated_at,
                   oi.id as item_id, oi.product_name, oi.quantity,
                   oi.sourcing_price, oi.selling_price
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            ORDER BY o.created_at DESC
            LIMIT 50
        """)

        # 주문과 아이템 그룹화
        orders_dict = {}
        for row in cursor.fetchall():
            order_id = row[0]
            if order_id not in orders_dict:
                orders_dict[order_id] = {
                    "id": row[0],
                    "order_number": row[1],
                    "market": row[2],
                    "customer_name": row[3],
                    "total_amount": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                    "items": []
                }

            # 아이템 추가
            if row[8]:  # item_id가 있으면
                orders_dict[order_id]["items"].append({
                    "id": row[8],
                    "product_name": row[9],
                    "quantity": row[10],
                    "sourcing_price": row[11],
                    "selling_price": row[12]
                })

        all_orders = list(orders_dict.values())

        conn.close()

        return {
            "success": True,
            "rpa_stats": rpa_stats,
            "playauto_stats": playauto_stats,
            "monitor_stats": monitor_stats,
            "recent_orders": recent_orders,
            "all_orders": all_orders
        }

    except Exception as e:
        logger.error(f"[대시보드] 통합 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
