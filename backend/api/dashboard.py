"""
통합 대시보드 API
여러 API 호출을 하나로 통합하여 성능 최적화
"""
from fastapi import APIRouter, HTTPException
from database.database_manager import get_database_manager
from logger import get_logger
from utils.cache import async_cached

logger = get_logger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/all")
@async_cached(ttl=30)  # 30초 캐싱
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
        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        # Boolean 쿼리 (PostgreSQL과 SQLite 호환)
        # PostgreSQL: TRUE/FALSE, SQLite: 1/0
        is_true = "TRUE" if not db_manager.is_sqlite else "1"

        # 1. RPA 통계 (기존 /api/orders/rpa/stats)
        # 참고: rpa_orders 테이블이 없을 수 있음 (사용하지 않는 기능)
        try:
            # 먼저 테이블 존재 여부 확인
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'rpa_orders'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if table_exists:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN status = '대기' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = '완료' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = '실패' THEN 1 ELSE 0 END) as failed
                    FROM rpa_orders
                """)
                rpa_row = cursor.fetchone()
                rpa_stats = {
                    "total": int(rpa_row[0] or 0),
                    "pending": int(rpa_row[1] or 0),
                    "completed": int(rpa_row[2] or 0),
                    "failed": int(rpa_row[3] or 0)
                }
            else:
                rpa_stats = {"total": 0, "pending": 0, "completed": 0, "failed": 0}
        except Exception as e:
            logger.warning(f"[대시보드] RPA 통계 조회 실패: {e}")
            conn.rollback()  # 트랜잭션 롤백하여 다음 쿼리 실행 가능하게
            rpa_stats = {"total": 0, "pending": 0, "completed": 0, "failed": 0}

        # 2. PlayAuto 통계 (기존 /api/playauto/stats)
        try:
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_products,
                    SUM(CASE WHEN is_active = {is_true} THEN 1 ELSE 0 END) as active_products
                FROM my_selling_products
                WHERE playauto_product_no IS NOT NULL
            """)
            playauto_row = cursor.fetchone()
            playauto_stats = {
                "total_products": int(playauto_row[0] or 0),
                "active_products": int(playauto_row[1] or 0)
            }
        except Exception as e:
            logger.warning(f"[대시보드] PlayAuto 통계 조회 실패: {e}")
            conn.rollback()  # 트랜잭션 롤백
            playauto_stats = {"total_products": 0, "active_products": 0}

        # 3. 모니터링 통계 (기존 /api/monitor/dashboard/stats)
        try:
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active = {is_true} THEN 1 ELSE 0 END) as active,
                    0 as margin_issues
                FROM monitored_products
            """)
            monitor_row = cursor.fetchone()
            monitor_stats = {
                "total": int(monitor_row[0] or 0),
                "active": int(monitor_row[1] or 0),
                "margin_issues": int(monitor_row[2] or 0)
            }
        except Exception as e:
            logger.warning(f"[대시보드] 모니터링 통계 조회 실패: {e}")
            conn.rollback()  # 트랜잭션 롤백
            monitor_stats = {"total": 0, "active": 0, "margin_issues": 0}

        # 4. 최근 주문 목록 (limit 10)
        try:
            cursor.execute("""
                SELECT id, order_number, market, customer_name, total_amount,
                       order_status, created_at, updated_at
                FROM orders
                ORDER BY created_at DESC
                LIMIT 10
            """)

            # Row를 dict로 변환 (안전한 방식 - cursor.description 사용)
            columns = [col[0] for col in cursor.description]
            recent_orders = []
            for row in cursor.fetchall():
                order_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # datetime을 문자열로 변환
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    order_dict[col] = value
                recent_orders.append(order_dict)
        except Exception as e:
            logger.warning(f"[대시보드] 최근 주문 조회 실패: {e}")
            conn.rollback()  # 트랜잭션 롤백
            recent_orders = []

        # 5. 전체 주문 통계 (with items, limit 50)
        try:
            cursor.execute("""
                SELECT o.id, o.order_number, o.market, o.customer_name,
                       o.total_amount, o.order_status, o.created_at, o.updated_at,
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
                    # datetime을 문자열로 변환
                    created_at = row[6]
                    if hasattr(created_at, 'isoformat'):
                        created_at = created_at.isoformat()
                    updated_at = row[7]
                    if hasattr(updated_at, 'isoformat'):
                        updated_at = updated_at.isoformat()

                    orders_dict[order_id] = {
                        "id": row[0],
                        "order_number": row[1],
                        "market": row[2],
                        "customer_name": row[3],
                        "total_amount": float(row[4]) if row[4] else 0,
                        "status": row[5],
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "items": []
                    }

                # 아이템 추가
                if row[8]:  # item_id가 있으면
                    orders_dict[order_id]["items"].append({
                        "id": row[8],
                        "product_name": row[9],
                        "quantity": int(row[10]) if row[10] else 0,
                        "sourcing_price": float(row[11]) if row[11] else 0,
                        "selling_price": float(row[12]) if row[12] else 0
                    })

            all_orders = list(orders_dict.values())
        except Exception as e:
            logger.warning(f"[대시보드] 전체 주문 조회 실패: {e}")
            conn.rollback()  # 트랜잭션 롤백
            all_orders = []

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
        logger.exception(e)  # 전체 스택 트레이스 출력
        raise HTTPException(status_code=500, detail=str(e))
