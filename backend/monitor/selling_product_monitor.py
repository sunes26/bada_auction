"""
판매 상품 소싱가 자동 모니터링

내 판매 상품(my_selling_products)의 소싱가를 주기적으로 체크하여 업데이트합니다.
"""

import asyncio
from datetime import datetime
from database.db_wrapper import get_db
from monitor.product_monitor import ProductMonitor
from logger import get_logger

logger = get_logger(__name__)


async def update_selling_products_sourcing_price():
    """
    판매 상품의 소싱가를 자동으로 업데이트
    소싱 URL이 있는 모든 활성 상품을 체크합니다.
    """
    logger.info(f"\n[SELLING_MONITOR] ===== 판매 상품 소싱가 업데이트 시작: {datetime.now()} =====")

    try:
        db = get_db()

        # 소싱 URL이 있는 활성 판매 상품 조회
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    product_name,
                    sourcing_url,
                    sourcing_source,
                    sourcing_price,
                    selling_price
                FROM my_selling_products
                WHERE is_active = 1
                  AND sourcing_url IS NOT NULL
                  AND sourcing_url != ''
                ORDER BY updated_at ASC
                LIMIT 50
            """)

            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row[0],
                    'product_name': row[1],
                    'sourcing_url': row[2],
                    'sourcing_source': row[3],
                    'sourcing_price': row[4],
                    'selling_price': row[5]
                })

        if not products:
            logger.info("[SELLING_MONITOR] 소싱 URL이 있는 활성 판매 상품이 없습니다")
            return

        logger.info(f"[SELLING_MONITOR] 체크할 상품 수: {len(products)}개")

        # 모니터 인스턴스 생성
        monitor = ProductMonitor()

        success_count = 0
        updated_count = 0
        error_count = 0

        # 각 상품 체크
        for product in products:
            product_id = product['id']
            product_name = product['product_name']
            sourcing_url = product['sourcing_url']
            source = product['sourcing_source']
            old_price = product['sourcing_price']

            try:
                logger.info(f"[SELLING_MONITOR] 체크 중: ID#{product_id} - {product_name[:40]}...")

                # 상품 상태 및 가격 체크
                result = monitor.check_product_status(
                    product_url=sourcing_url,
                    source=source or 'unknown'
                )

                new_price = result.get('price')

                if new_price and new_price > 0:
                    # 가격이 변경되었으면 업데이트
                    if old_price != new_price:
                        logger.info(f"[SELLING_MONITOR] 가격 변동 감지: {old_price}원 → {new_price}원")

                        # DB 업데이트
                        with db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE my_selling_products
                                SET sourcing_price = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (new_price, product_id))
                            conn.commit()

                        # 마진 변동 로그 기록
                        selling_price = product['selling_price']
                        old_margin = selling_price - (old_price or 0)
                        new_margin = selling_price - new_price
                        old_margin_rate = ((selling_price - (old_price or 0)) / (old_price or 1)) * 100 if old_price else 0
                        new_margin_rate = ((selling_price - new_price) / new_price) * 100 if new_price else 0

                        db.log_margin_change(
                            selling_product_id=product_id,
                            old_margin=old_margin,
                            new_margin=new_margin,
                            old_margin_rate=old_margin_rate,
                            new_margin_rate=new_margin_rate,
                            change_reason='sourcing_price_updated',
                            old_selling_price=selling_price,
                            new_selling_price=selling_price,
                            old_sourcing_price=old_price,
                            new_sourcing_price=new_price
                        )

                        updated_count += 1
                        logger.info(f"[OK] ID#{product_id}: 소싱가 업데이트 완료 ({old_price}원 → {new_price}원)")
                    else:
                        logger.info(f"[OK] ID#{product_id}: 가격 변동 없음 ({new_price}원)")

                    success_count += 1
                else:
                    logger.warning(f"[WARN] ID#{product_id}: 가격 정보를 가져올 수 없습니다")
                    error_count += 1

                # 각 상품 체크 사이에 지연 (서버 부하 방지)
                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"[ERROR] ID#{product_id} 체크 실패: {str(e)}")
                error_count += 1

        logger.info(f"\n[SELLING_MONITOR] ===== 소싱가 업데이트 완료: 성공 {success_count}건, 업데이트 {updated_count}건, 실패 {error_count}건 =====\n")

        # 업데이트된 항목이 있으면 알림
        if updated_count > 0:
            logger.info(f"[SELLING_MONITOR] 💡 {updated_count}개 상품의 소싱가가 업데이트되었습니다!")

    except Exception as e:
        logger.error(f"[ERROR] 판매 상품 소싱가 업데이트 중 오류: {e}")
        import traceback
        traceback.print_exc()


async def check_margin_alerts():
    """
    마진 경고 체크
    소싱가 변동으로 인한 역마진 또는 낮은 마진 경고
    """
    try:
        db = get_db()

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 역마진 또는 마진율 10% 미만 상품 조회
            cursor.execute("""
                SELECT
                    id,
                    product_name,
                    selling_price,
                    sourcing_price,
                    selling_price - sourcing_price as margin,
                    ((selling_price - sourcing_price) / sourcing_price * 100) as margin_rate
                FROM my_selling_products
                WHERE is_active = 1
                  AND sourcing_price IS NOT NULL
                  AND (
                      selling_price < sourcing_price  -- 역마진
                      OR ((selling_price - sourcing_price) / sourcing_price * 100) < 10  -- 마진 10% 미만
                  )
            """)

            alerts = []
            for row in cursor.fetchall():
                product_id, product_name, selling_price, sourcing_price, margin, margin_rate = row

                if selling_price < sourcing_price:
                    alert_type = "역마진"
                    message = f"⚠️ [{product_name}] 역마진 발생! 판매가({selling_price:,}원) < 소싱가({sourcing_price:,}원), 손실: {abs(margin):,}원"
                else:
                    alert_type = "낮은 마진"
                    message = f"💡 [{product_name}] 마진 부족! 현재 마진율: {margin_rate:.1f}% (최소 10% 권장)"

                alerts.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'type': alert_type,
                    'message': message
                })

            if alerts:
                logger.warning(f"\n[SELLING_MONITOR] ===== 마진 경고 {len(alerts)}건 =====")
                for alert in alerts:
                    logger.warning(f"  - {alert['message']}")
                logger.warning("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"[ERROR] 마진 경고 체크 중 오류: {e}")
