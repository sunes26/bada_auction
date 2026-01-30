"""
Product Service

상품 비즈니스 로직 처리
"""
from database.repositories.product_repository import ProductRepository
from typing import Dict, List
from logger import get_logger

logger = get_logger(__name__)


class ProductService:
    """상품 비즈니스 로직 처리"""

    def __init__(self):
        self.product_repo = ProductRepository()

    def check_price_change(self, product_id: int, new_price: float) -> Dict:
        """
        가격 변동 감지 및 알림 발송

        비즈니스 로직:
        1. 이전 가격 조회
        2. 변동률 계산
        3. 1% 이상 변동 시 알림 발송
        4. 가격 이력 저장

        Args:
            product_id: 상품 ID
            new_price: 새로운 가격

        Returns:
            변동 정보 딕셔너리
        """
        # 1. 이전 가격 조회
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return {"success": False, "error": "상품을 찾을 수 없습니다"}

        old_price = product['current_price']

        # 2. 변동률 계산
        price_change_percent = ((new_price - old_price) / old_price) * 100 if old_price and old_price > 0 else 0

        # 3. 1% 이상 변동 시 알림
        notification_sent = False
        if abs(price_change_percent) >= 1.0:
            notification_type = "price_increase" if price_change_percent > 0 else "price_decrease"

            try:
                # 알림 발송 (Discord/Slack)
                from notifications.notifier import send_discord_notification
                send_discord_notification(
                    notification_type=notification_type,
                    product_name=product['product_name'],
                    old_price=old_price,
                    new_price=new_price,
                    price_change_percent=price_change_percent
                )
                notification_sent = True
                logger.info(f"가격 변동 알림 발송: {product['product_name']} ({price_change_percent:+.1f}%)")
            except Exception as e:
                logger.error(f"알림 발송 실패: {e}", exc_info=True)

        # 4. 가격 업데이트 및 이력 저장
        self.product_repo.update_price(product_id, new_price)
        self.product_repo.add_price_history(product_id, new_price, "checked")

        return {
            "success": True,
            "old_price": old_price,
            "new_price": new_price,
            "price_change_percent": price_change_percent,
            "notification_sent": notification_sent
        }

    def get_products_with_margin_alerts(self, margin_threshold: float = 10.0) -> List[Dict]:
        """
        역마진 상품 목록 조회 (비즈니스 로직)

        Args:
            margin_threshold: 마진율 임계값 (기본 10%)

        Returns:
            역마진 또는 낮은 마진율 상품 목록
        """
        products = self.product_repo.get_products_with_low_margin(margin_threshold)

        # 추가 비즈니스 로직: 마진 경고 레벨 분류
        for product in products:
            margin_percent = product.get('margin_percent', 0)

            if margin_percent < 0:
                product['alert_level'] = 'critical'  # 역마진
                product['alert_message'] = '역마진 발생! 즉시 조치 필요'
            elif margin_percent < 5:
                product['alert_level'] = 'high'  # 5% 미만
                product['alert_message'] = '마진율 매우 낮음'
            else:
                product['alert_level'] = 'medium'  # 5~10%
                product['alert_message'] = '마진율 낮음'

        return products

    def check_stock_and_update(self, product_id: int, is_available: bool) -> Dict:
        """
        재고 상태 확인 및 자동 비활성화

        비즈니스 로직:
        1. 품절 시 자동 비활성화
        2. 재입고 시 알림 발송

        Args:
            product_id: 상품 ID
            is_available: 재고 가능 여부

        Returns:
            처리 결과
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return {"success": False, "error": "상품을 찾을 수 없습니다"}

        was_active = product['is_active']

        # 품절 시 자동 비활성화
        if not is_available and was_active:
            self.product_repo.update_status(product_id, False)
            logger.info(f"품절로 인한 자동 비활성화: {product['product_name']}")

            # 품절 알림
            try:
                from notifications.notifier import send_discord_notification
                send_discord_notification(
                    notification_type="out_of_stock",
                    product_name=product['product_name'],
                    product_url=product.get('product_url')
                )
            except Exception as e:
                logger.error(f"품절 알림 발송 실패: {e}")

            return {
                "success": True,
                "action": "deactivated",
                "message": "품절로 인해 자동 비활성화되었습니다"
            }

        # 재입고 시 알림 (수동 재활성화 필요)
        elif is_available and not was_active:
            logger.info(f"재입고 감지: {product['product_name']}")

            try:
                from notifications.notifier import send_discord_notification
                send_discord_notification(
                    notification_type="back_in_stock",
                    product_name=product['product_name'],
                    product_url=product.get('product_url')
                )
            except Exception as e:
                logger.error(f"재입고 알림 발송 실패: {e}")

            return {
                "success": True,
                "action": "restocked",
                "message": "재입고되었습니다. 수동으로 활성화해주세요."
            }

        return {
            "success": True,
            "action": "no_change",
            "message": "상태 변경 없음"
        }

    def get_dashboard_stats(self) -> Dict:
        """
        대시보드 통계 조회

        Returns:
            대시보드 통계 정보
        """
        all_products = self.product_repo.get_active_products()
        total_count = len(all_products)

        # 마진 통계
        margin_alerts = self.get_products_with_margin_alerts(margin_threshold=10.0)
        critical_alerts = [p for p in margin_alerts if p.get('alert_level') == 'critical']

        # 소싱처별 통계
        source_counts = {}
        for product in all_products:
            source = product.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "total_products": total_count,
            "margin_alerts": len(margin_alerts),
            "critical_alerts": len(critical_alerts),
            "source_distribution": source_counts
        }
