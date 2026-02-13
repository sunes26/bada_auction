"""
Database Wrapper - SQLAlchemy 기반으로 기존 db.py 인터페이스 구현
기존 API 코드 수정 없이 SQLAlchemy로 전환 가능
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .database_manager import get_database_manager
from .models import (
    MonitoredProduct, PriceHistory, StatusChange, Notification,
    Order, OrderItem, AutoOrderLog, SourcingAccount,
    PlayautoSetting, PlayautoSyncLog, MarketOrderRaw,
    WebhookSetting, WebhookLog, MySellingProduct, MarginChangeLog,
    InventoryAutoLog, Category, ProductMarketplaceCode
)


class DatabaseWrapper:
    """
    SQLAlchemy 기반 Database Wrapper
    기존 Database 클래스와 동일한 인터페이스 제공
    """

    def __init__(self):
        self.db_manager = get_database_manager()
        # SQLite와의 호환성을 위한 플래그
        self.is_postgresql = self.db_manager.is_postgresql

    def get_connection(self):
        """
        레거시 호환성: SQLite connection 대신 SQLAlchemy session 반환
        주의: context manager로 사용해야 함
        """
        return self.db_manager.get_session()

    # ========================================
    # 모니터링 상품 관련 메서드
    # ========================================

    def add_monitored_product(
        self,
        product_url: str,
        product_name: str,
        source: str,
        current_price: Optional[float] = None,
        original_price: Optional[float] = None,
        check_interval: int = 15,
        notes: Optional[str] = None
    ) -> int:
        """모니터링 상품 추가"""
        with self.db_manager.get_session() as session:
            product = MonitoredProduct(
                product_url=product_url,
                product_name=product_name,
                source=source,
                current_price=current_price,
                original_price=original_price,
                check_interval=check_interval,
                notes=notes,
                last_checked_at=datetime.now()
            )
            session.add(product)
            session.flush()
            return product.id

    def get_monitored_product(self, product_id: int) -> Optional[Dict]:
        """특정 모니터링 상품 조회"""
        with self.db_manager.get_session() as session:
            product = session.query(MonitoredProduct).filter_by(id=product_id).first()
            if product:
                return self._model_to_dict(product)
            return None

    def get_all_monitored_products(self, active_only: bool = True) -> List[Dict]:
        """모든 모니터링 상품 조회"""
        with self.db_manager.get_session() as session:
            query = session.query(MonitoredProduct)
            if active_only:
                query = query.filter_by(is_active=True)
            query = query.order_by(MonitoredProduct.created_at.desc())
            products = query.all()
            return [self._model_to_dict(p) for p in products]

    def update_product_status(
        self,
        product_id: int,
        new_status: str,
        new_price: Optional[float] = None,
        details: Optional[str] = None
    ):
        """상품 상태 업데이트"""
        with self.db_manager.get_session() as session:
            product = session.query(MonitoredProduct).filter_by(id=product_id).first()
            if not product:
                return

            old_status = product.current_status
            old_price = product.current_price

            # 상태 변경 기록
            if old_status != new_status:
                status_change = StatusChange(
                    product_id=product_id,
                    old_status=old_status,
                    new_status=new_status,
                    details=details
                )
                session.add(status_change)

                # 알림 생성
                notification = Notification(
                    product_id=product_id,
                    notification_type='status_change',
                    message=f"상태 변경: {old_status} → {new_status}"
                )
                session.add(notification)

            # 가격 변경 기록
            if new_price and new_price != old_price:
                price_history = PriceHistory(
                    product_id=product_id,
                    price=new_price,
                    original_price=None
                )
                session.add(price_history)

                # 가격 변동 알림
                if old_price:
                    change_percent = ((new_price - old_price) / old_price) * 100
                    message = f"가격 변동: {old_price:,.0f}원 → {new_price:,.0f}원 ({change_percent:+.1f}%)"
                else:
                    message = f"가격 설정: {new_price:,.0f}원"

                notification = Notification(
                    product_id=product_id,
                    notification_type='price_change',
                    message=message
                )
                session.add(notification)

            # 상품 정보 업데이트
            product.current_status = new_status
            product.last_checked_at = datetime.now()
            if new_price is not None:
                product.current_price = new_price

    def get_status_history(self, product_id: int, limit: int = 50) -> List[Dict]:
        """상태 변경 이력 조회"""
        with self.db_manager.get_session() as session:
            changes = session.query(StatusChange).filter_by(product_id=product_id)\
                .order_by(StatusChange.changed_at.desc())\
                .limit(limit).all()
            return [self._model_to_dict(c) for c in changes]

    def get_price_history(self, product_id: int, limit: int = 100) -> List[Dict]:
        """가격 변동 이력 조회"""
        with self.db_manager.get_session() as session:
            history = session.query(PriceHistory).filter_by(product_id=product_id)\
                .order_by(PriceHistory.checked_at.desc())\
                .limit(limit).all()
            return [self._model_to_dict(h) for h in history]

    def get_unread_notifications(self, limit: int = 50) -> List[Dict]:
        """읽지 않은 알림 조회"""
        with self.db_manager.get_session() as session:
            notifications = session.query(Notification, MonitoredProduct)\
                .join(MonitoredProduct)\
                .filter(Notification.is_read == False)\
                .order_by(Notification.created_at.desc())\
                .limit(limit).all()

            results = []
            for notif, product in notifications:
                notif_dict = self._model_to_dict(notif)
                notif_dict['product_name'] = product.product_name
                notif_dict['product_url'] = product.product_url
                results.append(notif_dict)
            return results

    def mark_notification_as_read(self, notification_id: int):
        """알림을 읽음으로 표시"""
        with self.db_manager.get_session() as session:
            notification = session.query(Notification).filter_by(id=notification_id).first()
            if notification:
                notification.is_read = True

    def delete_monitored_product(self, product_id: int):
        """모니터링 상품 삭제"""
        with self.db_manager.get_session() as session:
            product = session.query(MonitoredProduct).filter_by(id=product_id).first()
            if product:
                session.delete(product)

    def toggle_monitoring(self, product_id: int, is_active: bool):
        """모니터링 활성화/비활성화"""
        with self.db_manager.get_session() as session:
            product = session.query(MonitoredProduct).filter_by(id=product_id).first()
            if product:
                product.is_active = is_active

    def get_dashboard_stats(self) -> Dict:
        """대시보드 통계 조회"""
        with self.db_manager.get_session() as session:
            # 상품 통계
            from sqlalchemy import func, case

            product_stats = session.query(
                func.count(MonitoredProduct.id).label('total_products'),
                func.sum(case((MonitoredProduct.is_active == True, 1), else_=0)).label('active_products'),
                func.sum(case((MonitoredProduct.is_active == False, 1), else_=0)).label('inactive_products')
            ).first()

            # 알림 통계
            notification_stats = session.query(
                func.count(Notification.id).label('total_notifications'),
                func.sum(case((Notification.is_read == False, 1), else_=0)).label('unread_notifications'),
                func.sum(case((
                    (Notification.notification_type == 'margin_alert') & (Notification.is_read == False),
                    1
                ), else_=0)).label('margin_alerts')
            ).first()

            # 최근 가격 변동 (24시간)
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(hours=24)
            price_changed = session.query(
                func.count(func.distinct(PriceHistory.product_id))
            ).filter(PriceHistory.checked_at > yesterday).scalar()

            return {
                'total_products': product_stats.total_products or 0,
                'active_products': product_stats.active_products or 0,
                'inactive_products': product_stats.inactive_products or 0,
                'total_notifications': notification_stats.total_notifications or 0,
                'unread_notifications': notification_stats.unread_notifications or 0,
                'margin_alerts': notification_stats.margin_alerts or 0,
                'price_changed_products': price_changed or 0
            }

    # ========================================
    # Playauto 설정 관련 메서드
    # ========================================

    def save_playauto_setting(self, key: str, value: str, encrypted: bool = False, notes: Optional[str] = None):
        """플레이오토 설정 저장"""
        with self.db_manager.get_session() as session:
            setting = session.query(PlayautoSetting).filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = value
                setting.encrypted = encrypted
                setting.notes = notes
            else:
                setting = PlayautoSetting(
                    setting_key=key,
                    setting_value=value,
                    encrypted=encrypted,
                    notes=notes
                )
                session.add(setting)

    def get_playauto_setting(self, key: str) -> Optional[str]:
        """플레이오토 설정 조회"""
        with self.db_manager.get_session() as session:
            setting = session.query(PlayautoSetting).filter_by(setting_key=key).first()
            return setting.setting_value if setting else None

    def get_all_playauto_settings(self) -> List[Dict]:
        """모든 플레이오토 설정 조회"""
        with self.db_manager.get_session() as session:
            settings = session.query(PlayautoSetting).order_by(PlayautoSetting.setting_key).all()
            return [self._model_to_dict(s) for s in settings]

    def delete_playauto_setting(self, key: str) -> bool:
        """플레이오토 설정 삭제"""
        with self.db_manager.get_session() as session:
            setting = session.query(PlayautoSetting).filter_by(setting_key=key).first()
            if setting:
                session.delete(setting)
                return True
            return False

    # ========================================
    # Category 관련 메서드
    # ========================================

    def get_all_categories(self) -> List[Dict]:
        """모든 카테고리 조회"""
        with self.db_manager.get_session() as session:
            categories = session.query(Category).order_by(Category.folder_number).all()
            return [self._model_to_dict(c) for c in categories]

    # ========================================
    # 판매 상품 관련 메서드
    # ========================================

    def add_selling_product(
        self,
        product_name: str,
        selling_price: float,
        monitored_product_id: Optional[int] = None,
        sourcing_url: Optional[str] = None,
        sourcing_product_name: Optional[str] = None,
        sourcing_price: Optional[float] = None,
        sourcing_source: Optional[str] = None,
        detail_page_data: Optional[str] = None,
        category: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        original_thumbnail_url: Optional[str] = None,
        sol_cate_no: Optional[int] = None,
        playauto_product_no: Optional[str] = None,
        ol_shop_no: Optional[str] = None,
        weight: Optional[str] = None,
        keywords: Optional[str] = None,
        ship_price_type: Optional[str] = '선결제',
        ship_price: Optional[int] = 3000,
        input_type: Optional[str] = 'auto',
        notes: Optional[str] = None,
        gmk_opts: Optional[str] = None,
        coupang_opts: Optional[str] = None,
        smart_opts: Optional[str] = None
    ) -> int:
        """판매 상품 추가"""
        with self.db_manager.get_session() as session:
            product = MySellingProduct(
                product_name=product_name,
                selling_price=selling_price,
                monitored_product_id=monitored_product_id,
                sourcing_url=sourcing_url,
                sourcing_product_name=sourcing_product_name,
                sourcing_price=sourcing_price,
                sourcing_source=sourcing_source,
                detail_page_data=detail_page_data,
                category=category,
                thumbnail_url=thumbnail_url,
                original_thumbnail_url=original_thumbnail_url,
                sol_cate_no=sol_cate_no,
                playauto_product_no=playauto_product_no,
                ol_shop_no=ol_shop_no,
                weight=weight,
                keywords=keywords,
                ship_price_type=ship_price_type,
                ship_price=ship_price,
                input_type=input_type,
                notes=notes,
                gmk_opts=gmk_opts,
                coupang_opts=coupang_opts,
                smart_opts=smart_opts
            )
            session.add(product)
            session.flush()
            return product.id

    def get_selling_products(self, is_active: Optional[bool] = None, limit: int = 100) -> List[Dict]:
        """판매 상품 목록 조회 (소싱 정보 포함)"""
        with self.db_manager.get_session() as session:
            from sqlalchemy import case, func

            query = session.query(
                MySellingProduct,
                MonitoredProduct.product_name.label('monitored_product_name'),
                MonitoredProduct.product_url.label('monitored_product_url'),
                MonitoredProduct.source.label('monitored_source'),
                MonitoredProduct.current_price.label('monitored_price'),
                MonitoredProduct.current_status.label('monitored_status'),
                func.coalesce(MySellingProduct.sourcing_price, MonitoredProduct.current_price, 0).label('effective_sourcing_price')
            ).outerjoin(MonitoredProduct, MySellingProduct.monitored_product_id == MonitoredProduct.id)

            if is_active is not None:
                query = query.filter(MySellingProduct.is_active == is_active)

            query = query.order_by(MySellingProduct.created_at.desc()).limit(limit)

            results = []
            for row in query.all():
                product_dict = self._model_to_dict(row[0])
                product_dict['monitored_product_name'] = row[1]
                product_dict['monitored_product_url'] = row[2]
                product_dict['monitored_source'] = row[3]
                product_dict['monitored_price'] = float(row[4]) if row[4] else None
                product_dict['monitored_status'] = row[5]
                product_dict['effective_sourcing_price'] = float(row[6])

                # 마진 계산
                sourcing_price = product_dict['effective_sourcing_price']
                selling_price = float(product_dict['selling_price'])
                if sourcing_price > 0:
                    product_dict['margin'] = selling_price - sourcing_price
                    product_dict['margin_rate'] = ((selling_price - sourcing_price) / sourcing_price) * 100
                else:
                    product_dict['margin'] = 0
                    product_dict['margin_rate'] = 0

                results.append(product_dict)

            return results

    def search_selling_products_by_name(self, query: str, limit: int = 10) -> List[Dict]:
        """
        상품명으로 판매 상품 검색 (DB LIKE 쿼리 사용, 인메모리 필터링 대체)

        Args:
            query: 검색어
            limit: 최대 결과 수

        Returns:
            매칭된 상품 목록
        """
        with self.db_manager.get_session() as session:
            from sqlalchemy import or_, func

            # PostgreSQL/SQLite 모두 호환되는 대소문자 무시 검색
            query_pattern = f"%{query}%"

            results = session.query(
                MySellingProduct,
                MonitoredProduct.product_name.label('monitored_product_name'),
                MonitoredProduct.product_url.label('monitored_product_url'),
                MonitoredProduct.source.label('monitored_source'),
                MonitoredProduct.current_price.label('monitored_price'),
                MonitoredProduct.current_status.label('monitored_status'),
                func.coalesce(MySellingProduct.sourcing_price, MonitoredProduct.current_price, 0).label('effective_sourcing_price')
            ).outerjoin(MonitoredProduct, MySellingProduct.monitored_product_id == MonitoredProduct.id)\
             .filter(
                MySellingProduct.is_active == True,
                or_(
                    func.lower(MySellingProduct.product_name).like(func.lower(query_pattern)),
                    func.lower(MySellingProduct.sourcing_product_name).like(func.lower(query_pattern))
                )
            ).limit(limit).all()

            products = []
            for row in results:
                product_dict = self._model_to_dict(row[0])
                product_dict['monitored_product_name'] = row[1]
                product_dict['monitored_product_url'] = row[2]
                product_dict['monitored_source'] = row[3]
                product_dict['monitored_price'] = float(row[4]) if row[4] else None
                product_dict['monitored_status'] = row[5]
                product_dict['effective_sourcing_price'] = float(row[6])

                # 마진 계산
                sourcing_price = product_dict['effective_sourcing_price']
                selling_price = float(product_dict['selling_price'])
                if sourcing_price > 0:
                    product_dict['margin'] = selling_price - sourcing_price
                    product_dict['margin_rate'] = ((selling_price - sourcing_price) / sourcing_price) * 100
                else:
                    product_dict['margin'] = 0
                    product_dict['margin_rate'] = 0

                products.append(product_dict)

            return products

    def get_selling_product(self, product_id: int) -> Optional[Dict]:
        """판매 상품 상세 조회"""
        with self.db_manager.get_session() as session:
            from sqlalchemy import func

            result = session.query(
                MySellingProduct,
                MonitoredProduct.product_name.label('monitored_product_name'),
                MonitoredProduct.product_url.label('monitored_product_url'),
                MonitoredProduct.source.label('monitored_source'),
                MonitoredProduct.current_price.label('monitored_price'),
                MonitoredProduct.current_status.label('monitored_status'),
                func.coalesce(MySellingProduct.sourcing_price, MonitoredProduct.current_price, 0).label('effective_sourcing_price')
            ).outerjoin(MonitoredProduct, MySellingProduct.monitored_product_id == MonitoredProduct.id)\
             .filter(MySellingProduct.id == product_id).first()

            if not result:
                return None

            product_dict = self._model_to_dict(result[0])
            product_dict['monitored_product_name'] = result[1]
            product_dict['monitored_product_url'] = result[2]
            product_dict['monitored_source'] = result[3]
            product_dict['monitored_price'] = float(result[4]) if result[4] else None
            product_dict['monitored_status'] = result[5]
            product_dict['effective_sourcing_price'] = float(result[6])

            # 마진 계산
            sourcing_price = product_dict['effective_sourcing_price']
            selling_price = float(product_dict['selling_price'])
            if sourcing_price > 0:
                product_dict['margin'] = selling_price - sourcing_price
                product_dict['margin_rate'] = ((selling_price - sourcing_price) / sourcing_price) * 100
            else:
                product_dict['margin'] = 0
                product_dict['margin_rate'] = 0

            return product_dict

    def update_selling_product(
        self,
        product_id: int,
        product_name: Optional[str] = None,
        selling_price: Optional[float] = None,
        monitored_product_id: Optional[int] = None,
        sourcing_url: Optional[str] = None,
        sourcing_product_name: Optional[str] = None,
        sourcing_price: Optional[float] = None,
        sourcing_source: Optional[str] = None,
        detail_page_data: Optional[str] = None,
        category: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        sol_cate_no: Optional[int] = None,
        playauto_product_no: Optional[str] = None,
        ol_shop_no: Optional[str] = None,
        ol_shop_no_gmk: Optional[str] = None,
        ol_shop_no_smart: Optional[str] = None,
        ol_shop_no_coupang: Optional[str] = None,
        c_sale_cd_gmk: Optional[str] = None,
        c_sale_cd_smart: Optional[str] = None,
        c_sale_cd_coupang: Optional[str] = None,
        weight: Optional[str] = None,
        keywords: Optional[str] = None,
        target_margin_rate: Optional[float] = None,
        ship_price_type: Optional[str] = None,
        ship_price: Optional[int] = None,
        is_active: Optional[bool] = None,
        notes: Optional[str] = None,
        gmk_opts: Optional[str] = None,
        coupang_opts: Optional[str] = None,
        smart_opts: Optional[str] = None
    ):
        """판매 상품 수정"""
        with self.db_manager.get_session() as session:
            product = session.query(MySellingProduct).filter_by(id=product_id).first()
            if not product:
                return

            if product_name is not None:
                product.product_name = product_name
            if selling_price is not None:
                product.selling_price = selling_price
            if monitored_product_id is not None:
                product.monitored_product_id = monitored_product_id
            if sourcing_url is not None:
                product.sourcing_url = sourcing_url
            if sourcing_product_name is not None:
                product.sourcing_product_name = sourcing_product_name
            if sourcing_price is not None:
                product.sourcing_price = sourcing_price
            if sourcing_source is not None:
                product.sourcing_source = sourcing_source
            if detail_page_data is not None:
                product.detail_page_data = detail_page_data
            if category is not None:
                product.category = category
            if thumbnail_url is not None:
                product.thumbnail_url = thumbnail_url
            if sol_cate_no is not None:
                product.sol_cate_no = sol_cate_no
            if playauto_product_no is not None:
                product.playauto_product_no = playauto_product_no
            if ol_shop_no is not None:
                product.ol_shop_no = ol_shop_no
            if ol_shop_no_gmk is not None:
                product.ol_shop_no_gmk = ol_shop_no_gmk
            if ol_shop_no_smart is not None:
                product.ol_shop_no_smart = ol_shop_no_smart
            if ol_shop_no_coupang is not None:
                product.ol_shop_no_coupang = ol_shop_no_coupang
            if c_sale_cd_gmk is not None:
                product.c_sale_cd_gmk = c_sale_cd_gmk
            if c_sale_cd_smart is not None:
                product.c_sale_cd_smart = c_sale_cd_smart
            if c_sale_cd_coupang is not None:
                product.c_sale_cd_coupang = c_sale_cd_coupang
            if weight is not None:
                product.weight = weight
            if keywords is not None:
                product.keywords = keywords
            if target_margin_rate is not None:
                product.target_margin_rate = target_margin_rate
            if ship_price_type is not None:
                product.ship_price_type = ship_price_type
            if ship_price is not None:
                product.ship_price = ship_price
            if is_active is not None:
                product.is_active = is_active
            if notes is not None:
                product.notes = notes
            if gmk_opts is not None:
                product.gmk_opts = gmk_opts
            if coupang_opts is not None:
                product.coupang_opts = coupang_opts
            if smart_opts is not None:
                product.smart_opts = smart_opts

    def delete_selling_product(self, product_id: int):
        """판매 상품 삭제"""
        with self.db_manager.get_session() as session:
            product = session.query(MySellingProduct).filter_by(id=product_id).first()
            if product:
                session.delete(product)

    def get_margin_alert_products(self) -> List[Dict]:
        """역마진 발생 상품 목록 조회"""
        with self.db_manager.get_session() as session:
            results = session.query(MonitoredProduct, Notification)\
                .join(Notification, MonitoredProduct.id == Notification.product_id)\
                .filter(Notification.notification_type == 'margin_alert')\
                .filter(Notification.is_read == False)\
                .order_by(Notification.created_at.desc()).all()

            products = []
            for product, notification in results:
                product_dict = self._model_to_dict(product)
                product_dict['message'] = notification.message
                product_dict['alert_time'] = notification.created_at.isoformat() if notification.created_at else None
                products.append(product_dict)
            return products

    def get_margin_change_logs(self, selling_product_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """마진 변동 이력 조회"""
        with self.db_manager.get_session() as session:
            query = session.query(MarginChangeLog, MySellingProduct.product_name)\
                .join(MySellingProduct, MarginChangeLog.selling_product_id == MySellingProduct.id)

            if selling_product_id:
                query = query.filter(MarginChangeLog.selling_product_id == selling_product_id)

            query = query.order_by(MarginChangeLog.created_at.desc()).limit(limit)

            results = []
            for log, product_name in query.all():
                log_dict = self._model_to_dict(log)
                log_dict['product_name'] = product_name
                results.append(log_dict)
            return results

    def log_margin_change(
        self,
        selling_product_id: int,
        old_margin: float,
        new_margin: float,
        old_margin_rate: float,
        new_margin_rate: float,
        change_reason: str,
        old_selling_price: Optional[float] = None,
        new_selling_price: Optional[float] = None,
        old_sourcing_price: Optional[float] = None,
        new_sourcing_price: Optional[float] = None
    ) -> int:
        """마진 변동 기록"""
        with self.db_manager.get_session() as session:
            log = MarginChangeLog(
                selling_product_id=selling_product_id,
                old_margin=old_margin,
                new_margin=new_margin,
                old_margin_rate=old_margin_rate,
                new_margin_rate=new_margin_rate,
                change_reason=change_reason,
                old_selling_price=old_selling_price,
                new_selling_price=new_selling_price,
                old_sourcing_price=old_sourcing_price,
                new_sourcing_price=new_sourcing_price
            )
            session.add(log)
            session.flush()
            return log.id

    # ========================================
    # 주문 관리 메서드
    # ========================================

    def add_order(
        self,
        order_number: str,
        market: str,
        customer_name: str,
        customer_address: str,
        total_amount: float,
        customer_phone: Optional[str] = None,
        customer_zipcode: Optional[str] = None,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """주문 추가"""
        with self.db_manager.get_session() as session:
            order = Order(
                order_number=order_number,
                market=market,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_address=customer_address,
                customer_zipcode=customer_zipcode,
                total_amount=total_amount,
                payment_method=payment_method,
                notes=notes
            )
            session.add(order)
            session.flush()
            return order.id

    def add_order_item(
        self,
        order_id: int,
        product_name: str,
        product_url: str,
        source: str,
        sourcing_price: float,
        selling_price: float,
        quantity: int = 1,
        monitored_product_id: Optional[int] = None
    ) -> int:
        """주문 상품 추가"""
        profit = (selling_price - sourcing_price) * quantity

        with self.db_manager.get_session() as session:
            item = OrderItem(
                order_id=order_id,
                monitored_product_id=monitored_product_id,
                product_name=product_name,
                product_url=product_url,
                source=source,
                quantity=quantity,
                sourcing_price=sourcing_price,
                selling_price=selling_price,
                profit=profit
            )
            session.add(item)
            session.flush()
            return item.id

    def get_order(self, order_id: int) -> Optional[Dict]:
        """주문 조회"""
        with self.db_manager.get_session() as session:
            order = session.query(Order).filter_by(id=order_id).first()
            if order:
                return self._model_to_dict(order)
            return None

    def get_all_orders(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """주문 목록 조회"""
        with self.db_manager.get_session() as session:
            query = session.query(Order)

            if status:
                query = query.filter_by(order_status=status)

            query = query.order_by(Order.created_at.desc()).limit(limit)

            orders = query.all()
            return [self._model_to_dict(o) for o in orders]

    def get_order_items(self, order_id: int) -> List[Dict]:
        """주문 상품 목록 조회"""
        with self.db_manager.get_session() as session:
            items = session.query(OrderItem).filter_by(order_id=order_id).all()
            return [self._model_to_dict(i) for i in items]

    def get_order_items_batch(self, order_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        여러 주문의 상품을 한 번에 조회 (N+1 쿼리 방지)

        Args:
            order_ids: 주문 ID 목록

        Returns:
            {order_id: [item_dict, ...], ...} 형태의 딕셔너리
        """
        if not order_ids:
            return {}

        with self.db_manager.get_session() as session:
            items = session.query(OrderItem)\
                .filter(OrderItem.order_id.in_(order_ids))\
                .all()

            # order_id별로 그룹화
            result = {order_id: [] for order_id in order_ids}
            for item in items:
                result[item.order_id].append(self._model_to_dict(item))

            return result

    def get_pending_order_items(self, limit: int = 50) -> List[Dict]:
        """자동 발주 대기 중인 상품 목록 조회"""
        with self.db_manager.get_session() as session:
            results = session.query(OrderItem, Order)\
                .join(Order, OrderItem.order_id == Order.id)\
                .filter(OrderItem.rpa_status.in_(['pending', 'step1_completed', 'step3_completed', 'in_progress']))\
                .order_by(OrderItem.created_at.asc())\
                .limit(limit).all()

            items = []
            for item, order in results:
                item_dict = self._model_to_dict(item)
                item_dict['customer_name'] = order.customer_name
                item_dict['customer_phone'] = order.customer_phone
                item_dict['customer_address'] = order.customer_address
                item_dict['customer_zipcode'] = order.customer_zipcode
                item_dict['market'] = order.market
                items.append(item_dict)
            return items

    def get_auto_order_logs(self, order_item_id: int) -> List[Dict]:
        """RPA 실행 로그 조회"""
        with self.db_manager.get_session() as session:
            logs = session.query(AutoOrderLog)\
                .filter_by(order_item_id=order_item_id)\
                .order_by(AutoOrderLog.created_at.desc()).all()
            return [self._model_to_dict(log) for log in logs]

    # ========================================
    # Webhook 관련 메서드
    # ========================================

    def save_webhook_setting(
        self,
        webhook_type: str,
        webhook_url: str,
        enabled: bool = True,
        notification_types: str = 'all'
    ) -> int:
        """Webhook 설정 저장"""
        with self.db_manager.get_session() as session:
            webhook = session.query(WebhookSetting).filter_by(webhook_type=webhook_type).first()
            if webhook:
                webhook.webhook_url = webhook_url
                webhook.enabled = enabled
                webhook.notification_types = notification_types
                return webhook.id
            else:
                webhook = WebhookSetting(
                    webhook_type=webhook_type,
                    webhook_url=webhook_url,
                    enabled=enabled,
                    notification_types=notification_types
                )
                session.add(webhook)
                session.flush()
                return webhook.id

    def get_webhook_setting(self, webhook_type: str) -> Optional[Dict]:
        """특정 Webhook 설정 조회"""
        with self.db_manager.get_session() as session:
            webhook = session.query(WebhookSetting).filter_by(webhook_type=webhook_type).first()
            if webhook:
                return self._model_to_dict(webhook)
            return None

    def get_all_webhook_settings(self, enabled_only: bool = False) -> List[Dict]:
        """모든 Webhook 설정 조회"""
        with self.db_manager.get_session() as session:
            query = session.query(WebhookSetting)
            if enabled_only:
                query = query.filter_by(enabled=True)
            query = query.order_by(WebhookSetting.webhook_type)
            webhooks = query.all()
            return [self._model_to_dict(w) for w in webhooks]

    def toggle_webhook(self, webhook_type: str, enabled: bool):
        """Webhook 활성화/비활성화"""
        with self.db_manager.get_session() as session:
            webhook = session.query(WebhookSetting).filter_by(webhook_type=webhook_type).first()
            if webhook:
                webhook.enabled = enabled

    def delete_webhook_setting(self, webhook_type: str):
        """Webhook 설정 삭제"""
        with self.db_manager.get_session() as session:
            webhook = session.query(WebhookSetting).filter_by(webhook_type=webhook_type).first()
            if webhook:
                session.delete(webhook)

    def get_webhook_logs(self, limit: int = 50, webhook_type: Optional[str] = None) -> List[Dict]:
        """Webhook 로그 조회"""
        with self.db_manager.get_session() as session:
            query = session.query(WebhookLog, WebhookSetting.webhook_type)\
                .outerjoin(WebhookSetting, WebhookLog.webhook_id == WebhookSetting.id)

            if webhook_type:
                query = query.filter(WebhookSetting.webhook_type == webhook_type)

            query = query.order_by(WebhookLog.created_at.desc()).limit(limit)

            results = []
            for log, wh_type in query.all():
                log_dict = self._model_to_dict(log)
                log_dict['webhook_type'] = wh_type
                results.append(log_dict)
            return results

    def add_webhook_log(
        self,
        webhook_id: int,
        notification_type: str,
        status: str,
        message: Optional[str] = None,
        error_details: Optional[str] = None
    ):
        """Webhook 로그 추가"""
        with self.db_manager.get_session() as session:
            log = WebhookLog(
                webhook_id=webhook_id,
                notification_type=notification_type,
                status=status,
                message=message,
                error_details=error_details
            )
            session.add(log)

    # ========================================
    # 소싱 계정 관리
    # ========================================

    def add_sourcing_account(
        self,
        source: str,
        account_id: str,
        account_password: str,
        payment_method: Optional[str] = None,
        payment_info: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """소싱처 계정 추가 (비밀번호 자동 암호화)"""
        from playauto.crypto import get_crypto

        # 비밀번호 암호화
        crypto = get_crypto()
        encrypted_password = crypto.encrypt(account_password)

        with self.db_manager.get_session() as session:
            account = session.query(SourcingAccount).filter_by(source=source).first()
            if account:
                account.account_id = account_id
                account.account_password = encrypted_password
                account.payment_method = payment_method
                account.payment_info = payment_info
                account.notes = notes
                return account.id
            else:
                account = SourcingAccount(
                    source=source,
                    account_id=account_id,
                    account_password=encrypted_password,
                    payment_method=payment_method,
                    payment_info=payment_info,
                    notes=notes
                )
                session.add(account)
                session.flush()
                return account.id

    def get_all_sourcing_accounts(self) -> List[Dict]:
        """모든 소싱처 계정 조회 (비밀번호 자동 복호화)"""
        from playauto.crypto import get_crypto

        with self.db_manager.get_session() as session:
            accounts = session.query(SourcingAccount).filter_by(is_active=True).all()

            crypto = get_crypto()
            results = []
            for account in accounts:
                account_dict = self._model_to_dict(account)
                try:
                    account_dict['account_password'] = crypto.decrypt(account_dict['account_password'])
                except Exception as e:
                    print(f"[WARN] 비밀번호 복호화 실패 (평문일 수 있음): {e}")
                results.append(account_dict)
            return results

    # ========================================
    # Playauto 추가 메서드
    # ========================================

    def add_playauto_sync_log(
        self,
        sync_type: str,
        status: str,
        request_data: Optional[str] = None,
        response_data: Optional[str] = None,
        items_count: int = 0,
        success_count: int = 0,
        fail_count: int = 0,
        error_message: Optional[str] = None,
        execution_time: Optional[float] = None
    ) -> int:
        """플레이오토 동기화 로그 추가"""
        with self.db_manager.get_session() as session:
            log = PlayautoSyncLog(
                sync_type=sync_type,
                status=status,
                request_data=request_data,
                response_data=response_data,
                items_count=items_count,
                success_count=success_count,
                fail_count=fail_count,
                error_message=error_message,
                execution_time=execution_time
            )
            session.add(log)
            session.flush()
            return log.id

    def get_playauto_sync_logs(self, sync_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """플레이오토 동기화 로그 조회"""
        with self.db_manager.get_session() as session:
            query = session.query(PlayautoSyncLog)

            if sync_type:
                query = query.filter_by(sync_type=sync_type)

            query = query.order_by(PlayautoSyncLog.created_at.desc()).limit(limit)

            logs = query.all()
            return [self._model_to_dict(log) for log in logs]

    def get_playauto_stats(self) -> Dict:
        """플레이오토 통계 조회"""
        with self.db_manager.get_session() as session:
            from sqlalchemy import func
            from datetime import timedelta

            # 총 수집 주문 수
            total_orders = session.query(func.count(MarketOrderRaw.id)).scalar() or 0

            # 동기화된 주문 수
            synced_orders = session.query(func.count(MarketOrderRaw.id))\
                .filter(MarketOrderRaw.synced_to_local == True).scalar() or 0

            # 오늘 동기화 수
            yesterday = datetime.now() - timedelta(days=1)
            today_synced = session.query(func.count(PlayautoSyncLog.id))\
                .filter(PlayautoSyncLog.sync_type == 'order_fetch')\
                .filter(PlayautoSyncLog.status == 'success')\
                .filter(PlayautoSyncLog.created_at > yesterday).scalar() or 0

            # 최근 7일 추이
            week_ago = datetime.now() - timedelta(days=7)
            recent_trend_query = session.query(
                func.date(PlayautoSyncLog.created_at).label('date'),
                func.count(PlayautoSyncLog.id).label('count')
            ).filter(PlayautoSyncLog.created_at > week_ago)\
             .group_by(func.date(PlayautoSyncLog.created_at))\
             .order_by(func.date(PlayautoSyncLog.created_at).desc()).all()

            recent_trend = [{'date': str(row.date), 'count': row.count} for row in recent_trend_query]

            return {
                'total_orders': total_orders,
                'synced_orders': synced_orders,
                'uploaded_tracking': 0,  # TODO: implement if needed
                'today_synced': today_synced,
                'recent_trend': recent_trend
            }

    def get_unsynced_market_orders(self, limit: int = 100) -> List[Dict]:
        """미동기화 마켓 주문 조회"""
        with self.db_manager.get_session() as session:
            orders = session.query(MarketOrderRaw)\
                .filter_by(synced_to_local=False)\
                .order_by(MarketOrderRaw.order_date.desc())\
                .limit(limit).all()
            return [self._model_to_dict(o) for o in orders]

    def sync_playauto_order_to_local(self, order_data: Dict) -> bool:
        """
        플레이오토 주문을 로컬 DB에 동기화 (확장 필드 지원)
        - MarketOrderRaw: 원본 데이터 저장
        - Order: 주문 정보 저장 (회계용)
        - OrderItem: 주문 상품 저장 (회계용, 상품 매칭으로 sourcing_price 포함)

        Args:
            order_data: 주문 데이터 (dict 형식)

        Returns:
            성공 여부
        """
        try:
            import json

            with self.db_manager.get_session() as session:
                # 주문 ID 추출 (새 필드 우선, 레거시 필드 fallback)
                playauto_order_id = order_data.get("uniq") or order_data.get("playauto_order_id")
                if not playauto_order_id:
                    print("[WARN] 주문 ID가 없어 동기화를 건너뜁니다.")
                    return False

                # 중복 확인 (MarketOrderRaw)
                existing_raw = session.query(MarketOrderRaw).filter_by(
                    playauto_order_id=playauto_order_id
                ).first()

                # 필드 매핑
                market = order_data.get("shop_name") or order_data.get("market", "unknown")
                order_number = order_data.get("shop_ord_no") or order_data.get("order_number", "")

                # 고객 정보 추출 (receiver 객체 또는 flat 필드)
                receiver = order_data.get("receiver", {}) or {}
                customer_name = (
                    receiver.get("to_name") or
                    order_data.get("to_name") or
                    order_data.get("customer_name", "")
                )
                customer_phone = (
                    receiver.get("to_htel") or
                    receiver.get("to_tel") or
                    order_data.get("to_htel") or
                    order_data.get("customer_phone", "")
                )
                customer_addr1 = receiver.get("to_addr1") or order_data.get("to_addr1", "")
                customer_addr2 = receiver.get("to_addr2") or order_data.get("to_addr2", "")
                customer_address = f"{customer_addr1} {customer_addr2}".strip() or order_data.get("customer_address", "")
                customer_zipcode = receiver.get("to_zipcd") or order_data.get("to_zipcd") or order_data.get("customer_zipcode", "")

                # 금액 정보
                payment = order_data.get("payment", {}) or {}
                total_amount = (
                    order_data.get("sales") or
                    payment.get("pay_amt") or
                    order_data.get("total_amount", 0)
                )
                try:
                    total_amount = float(total_amount) if total_amount else 0
                except (ValueError, TypeError):
                    total_amount = 0

                # 주문 상태
                order_status = order_data.get("ord_status") or order_data.get("order_status", "pending")

                # 날짜 파싱
                order_date = None
                ord_time_str = order_data.get("ord_time") or order_data.get("order_date")
                if ord_time_str:
                    try:
                        if isinstance(ord_time_str, str):
                            order_date = datetime.strptime(ord_time_str, "%Y-%m-%d %H:%M:%S")
                        else:
                            order_date = ord_time_str
                    except Exception:
                        try:
                            order_date = datetime.fromisoformat(str(ord_time_str).replace("Z", "+00:00"))
                        except Exception:
                            order_date = datetime.now()

                if existing_raw:
                    # MarketOrderRaw 업데이트
                    existing_raw.order_status = order_status
                    existing_raw.updated_at = datetime.now()
                    existing_raw.raw_data = json.dumps(order_data, ensure_ascii=False, default=str)

                    # 기존 Order도 업데이트
                    if existing_raw.local_order_id:
                        existing_order = session.query(Order).filter_by(id=existing_raw.local_order_id).first()
                        if existing_order:
                            existing_order.order_status = order_status
                            existing_order.updated_at = datetime.now()

                    print(f"[INFO] 주문 업데이트: {playauto_order_id}")
                    return True

                # ========================================
                # 신규 주문 생성
                # ========================================

                # 1. MarketOrderRaw 생성
                new_raw_order = MarketOrderRaw(
                    playauto_order_id=playauto_order_id,
                    market=market,
                    order_number=order_number,
                    raw_data=json.dumps(order_data, ensure_ascii=False, default=str),
                    order_date=order_date,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(new_raw_order)
                session.flush()  # ID 확보

                # 2. Order 생성 (회계용)
                # order_number 중복 체크 (bundle_no로 구분)
                bundle_no = order_data.get("bundle_no", "")
                unique_order_number = f"{order_number}_{bundle_no}" if bundle_no else order_number

                existing_order = session.query(Order).filter_by(order_number=unique_order_number).first()

                if not existing_order:
                    new_order = Order(
                        order_number=unique_order_number,
                        market=market,
                        customer_name=customer_name or "고객",
                        customer_phone=customer_phone,
                        customer_address=customer_address or "주소 미입력",
                        customer_zipcode=customer_zipcode,
                        order_status=order_status,
                        total_amount=total_amount,
                        created_at=order_date or datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(new_order)
                    session.flush()  # ID 확보
                    order_id = new_order.id
                    print(f"[INFO] Order 생성: {unique_order_number} (ID: {order_id})")
                else:
                    order_id = existing_order.id
                    print(f"[INFO] 기존 Order 사용: {unique_order_number} (ID: {order_id})")

                # MarketOrderRaw와 Order 연결
                new_raw_order.local_order_id = order_id
                new_raw_order.synced_to_local = True

                # 3. OrderItem 생성 (회계용)
                shop_cd = order_data.get("shop_cd", "")
                shop_sale_no = order_data.get("shop_sale_no", "")
                product_name = order_data.get("shop_sale_name") or order_data.get("prod_name", "상품명 없음")
                quantity = order_data.get("sale_cnt") or 1
                try:
                    quantity = int(quantity)
                except (ValueError, TypeError):
                    quantity = 1

                # 상품별 판매가 계산
                selling_price = total_amount / quantity if quantity > 0 else total_amount

                # 상품 매칭으로 sourcing_price 가져오기
                sourcing_price = 0
                sourcing_source = "unknown"
                product_url = ""
                matched_product = None

                if shop_sale_no:
                    # shop_cd + shop_sale_no로 매칭
                    matched_product = self._find_product_for_order(session, shop_cd, shop_sale_no)

                if matched_product:
                    sourcing_price = float(matched_product.sourcing_price or 0)
                    sourcing_source = matched_product.sourcing_source or "unknown"
                    product_url = matched_product.sourcing_url or ""
                    print(f"[OK] 상품 매칭: {product_name} → sourcing_price={sourcing_price}")
                else:
                    # 매칭 실패시 기본값 (판매가의 70%로 추정)
                    sourcing_price = selling_price * 0.7
                    print(f"[WARN] 상품 매칭 실패: {product_name} (shop_cd={shop_cd}, shop_sale_no={shop_sale_no})")

                # 이익 계산
                profit = (selling_price - sourcing_price) * quantity

                # OrderItem 생성
                new_order_item = OrderItem(
                    order_id=order_id,
                    product_name=product_name,
                    product_url=product_url,
                    source=sourcing_source,
                    quantity=quantity,
                    sourcing_price=sourcing_price,
                    selling_price=selling_price,
                    profit=profit,
                    rpa_status="pending",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(new_order_item)

                # Order의 total_profit 업데이트
                if not existing_order:
                    new_order.total_profit = profit
                else:
                    existing_order.total_profit = (existing_order.total_profit or 0) + profit

                print(f"[INFO] OrderItem 생성: {product_name} x{quantity} (판매:{selling_price}, 매입:{sourcing_price}, 이익:{profit})")
                print(f"[OK] 신규 주문 완전 동기화: {playauto_order_id}")

                return True

        except Exception as e:
            print(f"[ERROR] 동기화 실패: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _find_product_for_order(self, session, shop_cd: str, shop_sale_no: str) -> Optional[MySellingProduct]:
        """
        주문의 shop_cd + shop_sale_no로 내 판매상품 찾기

        Args:
            session: DB 세션
            shop_cd: 쇼핑몰 코드
            shop_sale_no: 쇼핑몰 상품번호

        Returns:
            매칭된 MySellingProduct 또는 None
        """
        try:
            # 1. ProductMarketplaceCode 테이블에서 매칭 시도
            result = session.query(MySellingProduct).join(
                ProductMarketplaceCode
            ).filter(
                ProductMarketplaceCode.shop_cd == shop_cd,
                ProductMarketplaceCode.shop_sale_no == shop_sale_no
            ).first()

            if result:
                return result

            # 2. shop_sale_no만으로 매칭 시도 (shop_cd 무시)
            result = session.query(MySellingProduct).join(
                ProductMarketplaceCode
            ).filter(
                ProductMarketplaceCode.shop_sale_no == shop_sale_no
            ).first()

            if result:
                return result

            # 3. MySellingProduct의 레거시 필드로 매칭 시도
            # c_sale_cd_gmk, c_sale_cd_smart 등
            result = session.query(MySellingProduct).filter(
                (MySellingProduct.c_sale_cd_gmk == shop_sale_no) |
                (MySellingProduct.c_sale_cd_smart == shop_sale_no)
            ).first()

            return result

        except Exception as e:
            print(f"[ERROR] 상품 매칭 실패: {e}")
            return None

    # ========================================
    # 상품별 마켓 코드 관리
    # ========================================

    def upsert_marketplace_code(
        self,
        product_id: int,
        shop_cd: str,
        shop_name: Optional[str] = None,
        shop_sale_no: Optional[str] = None,
        transmitted_at: Optional[datetime] = None
    ) -> int:
        """마켓별 상품번호 저장/업데이트"""
        from .models import ProductMarketplaceCode

        with self.db_manager.get_session() as session:
            # 기존 레코드 확인
            existing = session.query(ProductMarketplaceCode).filter_by(
                product_id=product_id,
                shop_cd=shop_cd
            ).first()

            now = datetime.now()

            if existing:
                # 업데이트
                if shop_name:
                    existing.shop_name = shop_name
                existing.shop_sale_no = shop_sale_no
                if transmitted_at:
                    existing.transmitted_at = transmitted_at
                existing.last_checked_at = now
                existing.updated_at = now
                session.commit()
                return existing.id
            else:
                # 신규 생성
                new_code = ProductMarketplaceCode(
                    product_id=product_id,
                    shop_cd=shop_cd,
                    shop_name=shop_name,
                    shop_sale_no=shop_sale_no,
                    transmitted_at=transmitted_at,
                    last_checked_at=now,
                    created_at=now,
                    updated_at=now
                )
                session.add(new_code)
                session.commit()
                return new_code.id

    def get_marketplace_codes_by_product(self, product_id: int) -> List[Dict]:
        """상품의 모든 마켓 코드 조회"""
        from .models import ProductMarketplaceCode

        with self.db_manager.get_session() as session:
            codes = session.query(ProductMarketplaceCode).filter_by(
                product_id=product_id
            ).order_by(ProductMarketplaceCode.updated_at.desc()).all()

            return [self._model_to_dict(code) for code in codes]

    def get_product_by_marketplace_code(self, shop_cd: str, shop_sale_no: str) -> Optional[Dict]:
        """마켓 코드로 상품 조회 (주문 매칭용)"""
        from .models import MySellingProduct, ProductMarketplaceCode

        with self.db_manager.get_session() as session:
            result = session.query(MySellingProduct).join(
                ProductMarketplaceCode
            ).filter(
                ProductMarketplaceCode.shop_cd == shop_cd,
                ProductMarketplaceCode.shop_sale_no == shop_sale_no
            ).first()

            if result:
                product_dict = self._model_to_dict(result)
                # 마켓 코드 정보도 추가
                product_dict['shop_cd'] = shop_cd
                product_dict['shop_sale_no'] = shop_sale_no
                return product_dict
            return None

    def get_product_by_shop_sale_no(self, shop_sale_no: str) -> Optional[Dict]:
        """상품코드(shop_sale_no)만으로 상품 조회 (shop_cd 무시)"""
        from .models import MySellingProduct, ProductMarketplaceCode

        with self.db_manager.get_session() as session:
            result = session.query(MySellingProduct, ProductMarketplaceCode.shop_cd).join(
                ProductMarketplaceCode
            ).filter(
                ProductMarketplaceCode.shop_sale_no == shop_sale_no
            ).first()

            if result:
                product, shop_cd = result
                product_dict = self._model_to_dict(product)
                product_dict['shop_cd'] = shop_cd
                product_dict['shop_sale_no'] = shop_sale_no
                return product_dict
            return None

    def get_product_by_c_sale_cd(self, c_sale_cd: str) -> Optional[Dict]:
        """판매자 관리코드(c_sale_cd)로 상품 조회 (주문 매칭용)

        세 개의 채널별 c_sale_cd 필드 중 하나와 일치하는 상품을 찾습니다:
        - c_sale_cd_gmk: 지마켓/옥션용
        - c_sale_cd_smart: 스마트스토어용
        - c_sale_cd_coupang: 쿠팡용
        """
        from .models import MySellingProduct
        from sqlalchemy import or_

        with self.db_manager.get_session() as session:
            result = session.query(MySellingProduct).filter(
                or_(
                    MySellingProduct.c_sale_cd_gmk == c_sale_cd,
                    MySellingProduct.c_sale_cd_smart == c_sale_cd,
                    MySellingProduct.c_sale_cd_coupang == c_sale_cd
                )
            ).first()

            if result:
                return self._model_to_dict(result)
            return None

    def get_products_without_marketplace_codes(self, limit: int = 100) -> List[Dict]:
        """마켓 코드가 없는 상품 조회 (동기화 대상)"""
        from .models import MySellingProduct, ProductMarketplaceCode
        from sqlalchemy import and_, exists

        with self.db_manager.get_session() as session:
            # 마켓 코드가 없는 상품 쿼리
            subquery = session.query(ProductMarketplaceCode.product_id).filter(
                ProductMarketplaceCode.shop_sale_no.isnot(None)
            ).distinct().subquery()

            products = session.query(MySellingProduct).filter(
                and_(
                    MySellingProduct.ol_shop_no.isnot(None),
                    MySellingProduct.is_active == True,
                    ~MySellingProduct.id.in_(subquery)
                )
            ).limit(limit).all()

            return [self._model_to_dict(p) for p in products]

    def get_products_for_marketplace_sync(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """마켓 코드 동기화가 필요한 상품 조회 (주기적 업데이트)"""
        from .models import MySellingProduct, ProductMarketplaceCode
        from sqlalchemy import and_, or_, exists
        from datetime import timedelta

        with self.db_manager.get_session() as session:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # 마켓 코드가 없거나 오래된 상품
            subquery = session.query(ProductMarketplaceCode.product_id).filter(
                or_(
                    ProductMarketplaceCode.last_checked_at.is_(None),
                    ProductMarketplaceCode.last_checked_at < cutoff_time
                )
            ).distinct().subquery()

            products = session.query(MySellingProduct).filter(
                and_(
                    MySellingProduct.ol_shop_no.isnot(None),
                    MySellingProduct.is_active == True,
                    or_(
                        ~exists().where(ProductMarketplaceCode.product_id == MySellingProduct.id),
                        MySellingProduct.id.in_(subquery)
                    )
                )
            ).order_by(MySellingProduct.updated_at.desc()).limit(limit).all()

            return [self._model_to_dict(p) for p in products]

    def _match_order_to_product_legacy(self, order_data: Dict, playauto_order_id: str):
        """
        [DEPRECATED] 레거시 주문-상품 매칭 함수
        새로운 로직은 sync_playauto_order_to_local 내의 _find_product_for_order 사용
        """
        pass

    def migrate_raw_orders_to_accounting(self, limit: int = 100) -> Dict:
        """
        기존 MarketOrderRaw 데이터를 Order/OrderItem 테이블로 마이그레이션

        Args:
            limit: 한 번에 처리할 최대 주문 수

        Returns:
            결과 통계
        """
        import json

        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            with self.db_manager.get_session() as session:
                # 아직 동기화되지 않은 주문 조회
                raw_orders = session.query(MarketOrderRaw).filter(
                    (MarketOrderRaw.synced_to_local == False) |
                    (MarketOrderRaw.synced_to_local == None)
                ).limit(limit).all()

                stats["total"] = len(raw_orders)
                print(f"[INFO] 마이그레이션 대상: {stats['total']}건")

                for raw_order in raw_orders:
                    try:
                        # raw_data JSON 파싱
                        order_data = json.loads(raw_order.raw_data)

                        # 필드 추출
                        market = raw_order.market or order_data.get("shop_name", "unknown")
                        order_number = raw_order.order_number or order_data.get("shop_ord_no", "")
                        bundle_no = order_data.get("bundle_no", "")
                        unique_order_number = f"{order_number}_{bundle_no}" if bundle_no else order_number

                        # 이미 Order가 존재하는지 확인
                        existing_order = session.query(Order).filter_by(order_number=unique_order_number).first()
                        if existing_order:
                            # 연결만 업데이트
                            raw_order.local_order_id = existing_order.id
                            raw_order.synced_to_local = True
                            stats["skipped"] += 1
                            continue

                        # 고객 정보
                        receiver = order_data.get("receiver", {}) or {}
                        customer_name = (
                            receiver.get("to_name") or
                            order_data.get("to_name") or
                            order_data.get("customer_name", "고객")
                        )
                        customer_phone = (
                            receiver.get("to_htel") or
                            receiver.get("to_tel") or
                            order_data.get("to_htel") or
                            order_data.get("customer_phone", "")
                        )
                        customer_addr1 = receiver.get("to_addr1") or order_data.get("to_addr1", "")
                        customer_addr2 = receiver.get("to_addr2") or order_data.get("to_addr2", "")
                        customer_address = f"{customer_addr1} {customer_addr2}".strip() or order_data.get("customer_address", "주소 미입력")
                        customer_zipcode = receiver.get("to_zipcd") or order_data.get("to_zipcd", "")

                        # 금액 정보
                        payment = order_data.get("payment", {}) or {}
                        total_amount = (
                            order_data.get("sales") or
                            payment.get("pay_amt") or
                            order_data.get("total_amount", 0)
                        )
                        try:
                            total_amount = float(total_amount) if total_amount else 0
                        except:
                            total_amount = 0

                        order_status = order_data.get("ord_status") or order_data.get("order_status", "pending")

                        # Order 생성
                        new_order = Order(
                            order_number=unique_order_number,
                            market=market,
                            customer_name=customer_name or "고객",
                            customer_phone=customer_phone,
                            customer_address=customer_address,
                            customer_zipcode=customer_zipcode,
                            order_status=order_status,
                            total_amount=total_amount,
                            created_at=raw_order.order_date or raw_order.created_at,
                            updated_at=datetime.now()
                        )
                        session.add(new_order)
                        session.flush()

                        # OrderItem 생성
                        shop_cd = order_data.get("shop_cd", "")
                        shop_sale_no = order_data.get("shop_sale_no", "")
                        product_name = order_data.get("shop_sale_name") or order_data.get("prod_name", "상품명 없음")
                        quantity = order_data.get("sale_cnt") or 1
                        try:
                            quantity = int(quantity)
                        except:
                            quantity = 1

                        selling_price = total_amount / quantity if quantity > 0 else total_amount

                        # 상품 매칭
                        sourcing_price = 0
                        sourcing_source = "unknown"
                        product_url = ""

                        if shop_sale_no:
                            matched_product = self._find_product_for_order(session, shop_cd, shop_sale_no)
                            if matched_product:
                                sourcing_price = float(matched_product.sourcing_price or 0)
                                sourcing_source = matched_product.sourcing_source or "unknown"
                                product_url = matched_product.sourcing_url or ""
                            else:
                                sourcing_price = selling_price * 0.7

                        profit = (selling_price - sourcing_price) * quantity

                        new_order_item = OrderItem(
                            order_id=new_order.id,
                            product_name=product_name,
                            product_url=product_url,
                            source=sourcing_source,
                            quantity=quantity,
                            sourcing_price=sourcing_price,
                            selling_price=selling_price,
                            profit=profit,
                            rpa_status="pending",
                            created_at=raw_order.created_at,
                            updated_at=datetime.now()
                        )
                        session.add(new_order_item)

                        new_order.total_profit = profit

                        # 연결 업데이트
                        raw_order.local_order_id = new_order.id
                        raw_order.synced_to_local = True

                        stats["success"] += 1

                    except Exception as e:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "order_id": raw_order.playauto_order_id,
                            "error": str(e)
                        })
                        print(f"[ERROR] 주문 {raw_order.playauto_order_id} 마이그레이션 실패: {e}")

                # 커밋은 session context manager에서 처리됨

            print(f"[INFO] 마이그레이션 완료: 성공 {stats['success']}, 실패 {stats['failed']}, 건너뜀 {stats['skipped']}")
            return stats

        except Exception as e:
            print(f"[ERROR] 마이그레이션 실패: {e}")
            import traceback
            traceback.print_exc()
            stats["errors"].append({"error": str(e)})
            return stats

    # ========================================
    # 유틸리티 메서드
    # ========================================

    def _model_to_dict(self, model) -> Dict:
        """SQLAlchemy 모델을 딕셔너리로 변환"""
        from decimal import Decimal
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            # datetime을 문자열로 변환
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            # Decimal을 float로 변환 (JSON 직렬화 호환)
            elif isinstance(value, Decimal):
                result[column.name] = float(value)
            else:
                result[column.name] = value
        return result


# 싱글톤 인스턴스
_db_wrapper_instance = None


def get_db_wrapper() -> DatabaseWrapper:
    """Database Wrapper 인스턴스 가져오기"""
    global _db_wrapper_instance
    if _db_wrapper_instance is None:
        _db_wrapper_instance = DatabaseWrapper()
    return _db_wrapper_instance


def get_db():
    """
    레거시 호환성 함수
    환경 변수에 따라 SQLite 또는 PostgreSQL 반환
    """
    use_postgresql = os.getenv('USE_POSTGRESQL', 'false').lower() == 'true'

    if use_postgresql:
        return get_db_wrapper()
    else:
        # 기존 SQLite Database 반환
        from .db import get_db as get_sqlite_db
        return get_sqlite_db()
