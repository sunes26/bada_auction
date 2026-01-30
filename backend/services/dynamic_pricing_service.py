"""
동적 가격 조정 서비스

소싱가 변동 시 자동으로 판매가를 조정하여 마진율을 유지합니다.
"""

import asyncio
from typing import Dict, List
from database.db import get_db
from playauto.products import (
    PlayautoProductAPI,
    calculate_selling_price_with_margin,
    calculate_required_margin_rate
)
from logger import get_logger

logger = get_logger(__name__)


class DynamicPricingService:
    """동적 가격 조정 서비스"""

    def __init__(self, target_margin_rate: float = 50.0):
        """
        Args:
            target_margin_rate: 목표 마진율 (%, 기본값 50%)
        """
        self.target_margin_rate = target_margin_rate
        self.playauto_api = PlayautoProductAPI()
        self.db = get_db()

    async def auto_adjust_prices_on_sourcing_change(
        self,
        product_id: int,
        old_sourcing_price: float,
        new_sourcing_price: float
    ) -> Dict:
        """
        소싱가 변동 시 자동으로 판매가 조정

        Args:
            product_id: 판매 상품 ID
            old_sourcing_price: 이전 소싱가
            new_sourcing_price: 새 소싱가

        Returns:
            조정 결과
        """
        try:
            # 상품 정보 조회
            product = self.db.get_selling_product(product_id)
            if not product:
                logger.error(f"[동적가격] 상품을 찾을 수 없음: ID {product_id}")
                return {"success": False, "error": "상품을 찾을 수 없습니다"}

            product_name = product['product_name']
            current_selling_price = product['selling_price']

            # 현재 마진율 계산
            current_margin_rate = calculate_required_margin_rate(
                old_sourcing_price,
                current_selling_price
            )

            logger.info(f"[동적가격] 소싱가 변동 감지: {product_name}")
            logger.info(f"[동적가격] 이전 소싱가: {old_sourcing_price:,}원 → 새 소싱가: {new_sourcing_price:,}원")
            logger.info(f"[동적가격] 현재 판매가: {current_selling_price:,}원 (마진율 {current_margin_rate:.1f}%)")

            # 목표 마진율로 새 판매가 계산
            new_selling_price = calculate_selling_price_with_margin(
                new_sourcing_price,
                self.target_margin_rate
            )

            new_margin_rate = calculate_required_margin_rate(
                new_sourcing_price,
                new_selling_price
            )

            logger.info(f"[동적가격] 새 판매가: {new_selling_price:,}원 (마진율 {new_margin_rate:.1f}%)")

            # 판매가가 변경되었는지 확인
            if new_selling_price == current_selling_price:
                logger.info(f"[동적가격] 판매가 변경 불필요 (동일 가격)")
                return {
                    "success": True,
                    "changed": False,
                    "message": "판매가 변경 불필요"
                }

            # 로컬 DB 업데이트
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE my_selling_products
                    SET selling_price = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_selling_price, product_id))
                conn.commit()

            # 마진 변동 로그
            old_margin = current_selling_price - old_sourcing_price
            new_margin = new_selling_price - new_sourcing_price

            self.db.log_margin_change(
                selling_product_id=product_id,
                old_margin=old_margin,
                new_margin=new_margin,
                old_margin_rate=current_margin_rate,
                new_margin_rate=new_margin_rate,
                change_reason='auto_price_adjustment',
                old_selling_price=current_selling_price,
                new_selling_price=new_selling_price,
                old_sourcing_price=old_sourcing_price,
                new_sourcing_price=new_sourcing_price
            )

            logger.info(f"[동적가격] 로컬 DB 판매가 업데이트 완료: {current_selling_price:,}원 → {new_selling_price:,}원")

            # 플레이오토 상품 번호가 있으면 플레이오토 API로 가격 업데이트
            playauto_product_no = product.get('playauto_product_no')
            playauto_updated = False

            if playauto_product_no:
                try:
                    # 플레이오토 API로 판매가 업데이트
                    logger.info(f"[동적가격] 플레이오토 가격 업데이트 시작: ol_shop_no={playauto_product_no}")

                    await self.playauto_api.update_online_product_price(
                        ol_shop_no=playauto_product_no,
                        sale_price=new_selling_price
                    )

                    playauto_updated = True
                    logger.info(f"[동적가격] 플레이오토 가격 업데이트 성공")

                except Exception as e:
                    logger.error(f"[동적가격] 플레이오토 가격 업데이트 실패: {str(e)}")
                    # 플레이오토 업데이트 실패해도 로컬 DB는 업데이트되었으므로 계속 진행
            else:
                logger.warning(f"[동적가격] 플레이오토 상품 번호 없음 - 로컬 DB만 업데이트")

            return {
                "success": True,
                "changed": True,
                "product_id": product_id,
                "product_name": product_name,
                "old_selling_price": current_selling_price,
                "new_selling_price": new_selling_price,
                "old_margin_rate": round(current_margin_rate, 2),
                "new_margin_rate": round(new_margin_rate, 2),
                "playauto_updated": playauto_updated,
                "message": f"판매가 자동 조정 완료: {current_selling_price:,}원 → {new_selling_price:,}원"
            }

        except Exception as e:
            logger.error(f"[동적가격] 가격 조정 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    async def bulk_adjust_all_products(self) -> Dict:
        """
        모든 상품의 가격을 목표 마진율로 일괄 조정

        Returns:
            조정 결과
        """
        try:
            # 활성 상품 조회
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        id,
                        product_name,
                        selling_price,
                        sourcing_price,
                        playauto_product_no
                    FROM my_selling_products
                    WHERE is_active = 1
                      AND sourcing_price IS NOT NULL
                      AND sourcing_price > 0
                """)

                products = []
                for row in cursor.fetchall():
                    products.append({
                        'id': row[0],
                        'product_name': row[1],
                        'selling_price': row[2],
                        'sourcing_price': row[3],
                        'playauto_product_no': row[4]
                    })

            if not products:
                logger.info("[동적가격] 조정할 상품이 없습니다")
                return {"success": True, "adjusted_count": 0}

            logger.info(f"[동적가격] 일괄 가격 조정 시작: {len(products)}개 상품")

            adjusted_count = 0
            playauto_updates = []

            for product in products:
                # 새 판매가 계산
                new_selling_price = calculate_selling_price_with_margin(
                    product['sourcing_price'],
                    self.target_margin_rate
                )

                # 가격이 변경되었으면 업데이트
                if new_selling_price != product['selling_price']:
                    # 로컬 DB 업데이트
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE my_selling_products
                            SET selling_price = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (new_selling_price, product['id']))
                        conn.commit()

                    adjusted_count += 1
                    logger.info(
                        f"[동적가격] {product['product_name']}: "
                        f"{product['selling_price']:,}원 → {new_selling_price:,}원"
                    )

                    # 플레이오토 업데이트 목록에 추가
                    if product['playauto_product_no']:
                        playauto_updates.append({
                            "ol_shop_no": product['playauto_product_no'],
                            "sale_price": new_selling_price
                        })

            # 플레이오토 일괄 업데이트
            if playauto_updates:
                try:
                    await self.playauto_api.bulk_update_prices(playauto_updates)
                    logger.info(f"[동적가격] 플레이오토 일괄 업데이트 성공: {len(playauto_updates)}건")
                except Exception as e:
                    logger.error(f"[동적가격] 플레이오토 일괄 업데이트 실패: {str(e)}")

            logger.info(f"[동적가격] 일괄 가격 조정 완료: {adjusted_count}개 상품")

            return {
                "success": True,
                "adjusted_count": adjusted_count,
                "playauto_updated_count": len(playauto_updates)
            }

        except Exception as e:
            logger.error(f"[동적가격] 일괄 가격 조정 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
