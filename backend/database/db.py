"""
데이터베이스 초기화 및 연결 관리
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class Database:
    """SQLite 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """데이터베이스 초기화"""
        # 스키마 파일 읽기
        schema_path = Path(__file__).parent / "schema.sql"

        with sqlite3.connect(self.db_path) as conn:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
                conn.executescript(schema)
            conn.commit()

            # 플레이오토 관련 컬럼 마이그레이션
            self._migrate_playauto_columns(conn)

            # 성능 최적화 인덱스 생성
            self._create_performance_indexes(conn)

        print(f"[OK] 데이터베이스 초기화 완료: {self.db_path}")

    def _migrate_playauto_columns(self, conn):
        """플레이오토 관련 컬럼 추가 (마이그레이션)"""
        try:
            # orders 테이블에 컬럼 추가
            columns_to_add = [
                ("playauto_order_id", "TEXT"),
                ("synced_to_playauto", "BOOLEAN DEFAULT FALSE"),
                ("tracking_uploaded_at", "DATETIME")
            ]

            # 현재 컬럼 목록 확인
            cursor = conn.execute("PRAGMA table_info(orders)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # 없는 컬럼만 추가
            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        conn.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
                        print(f"[OK] orders 테이블에 '{col_name}' 컬럼 추가")
                    except sqlite3.Error as e:
                        print(f"[WARN] '{col_name}' 컬럼 추가 실패 (이미 존재할 수 있음): {e}")

            conn.commit()
        except Exception as e:
            print(f"[WARN] 플레이오토 컬럼 마이그레이션 실패: {e}")

    def _create_performance_indexes(self, conn):
        """성능 최적화를 위한 인덱스 생성 (마이그레이션)"""
        try:
            indexes = [
                # 주문 조회 최적화
                "CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number)",
                # 송장번호 조회 최적화
                "CREATE INDEX IF NOT EXISTS idx_order_items_tracking ON order_items(tracking_number)",
                # 알림 복합 조회 최적화
                "CREATE INDEX IF NOT EXISTS idx_notifications_product_type ON notifications(product_id, notification_type, created_at DESC)"
            ]

            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                except sqlite3.Error as e:
                    # 인덱스가 이미 존재하는 경우 무시
                    pass

            conn.commit()
            print(f"[OK] 성능 최적화 인덱스 생성 완료")
        except Exception as e:
            print(f"[WARN] 인덱스 생성 실패: {e}")

    def get_connection(self):
        """데이터베이스 연결 생성"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn

    # 모니터링 상품 관련 메서드

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
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO monitored_products
                (product_url, product_name, source, current_price, original_price, check_interval, notes, last_checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_url, product_name, source, current_price, original_price, check_interval, notes, datetime.now()))
            conn.commit()
            return cursor.lastrowid

    def get_monitored_product(self, product_id: int) -> Optional[Dict]:
        """특정 모니터링 상품 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM monitored_products WHERE id = ?
            """, (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_monitored_products(self, active_only: bool = True) -> List[Dict]:
        """모든 모니터링 상품 조회"""
        with self.get_connection() as conn:
            query = "SELECT * FROM monitored_products"
            if active_only:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def update_product_status(
        self,
        product_id: int,
        new_status: str,
        new_price: Optional[float] = None,
        details: Optional[str] = None
    ):
        """상품 상태 업데이트 및 역마진 방어"""
        with self.get_connection() as conn:
            # 현재 상태 가져오기
            cursor = conn.execute(
                "SELECT current_status, current_price, notes, product_name FROM monitored_products WHERE id = ?",
                (product_id,)
            )
            row = cursor.fetchone()

            if not row:
                return

            old_status = row['current_status']
            old_price = row['current_price']
            notes = row['notes'] or ''
            product_name = row['product_name']

            # 상태 변경 기록
            if old_status != new_status:
                conn.execute("""
                    INSERT INTO status_changes (product_id, old_status, new_status, details)
                    VALUES (?, ?, ?, ?)
                """, (product_id, old_status, new_status, details))

                # 알림 생성
                message = f"상태 변경: {old_status} → {new_status}"
                conn.execute("""
                    INSERT INTO notifications (product_id, notification_type, message)
                    VALUES (?, 'status_change', ?)
                """, (product_id, message))

                # 자동 재고 관리 (품절 자동 비활성화, 재입고 알림)
                try:
                    from inventory.auto_manager import check_and_update_inventory
                    check_and_update_inventory(
                        product_id=product_id,
                        old_status=old_status,
                        new_status=new_status,
                        product_name=product_name,
                        current_price=new_price
                    )
                except Exception as e:
                    print(f"[WARN] 자동 재고 관리 실패: {e}")

            # 가격 변경 기록 및 역마진 방어
            if new_price and new_price != old_price:
                conn.execute("""
                    INSERT INTO price_history (product_id, price, original_price)
                    VALUES (?, ?, ?)
                """, (product_id, new_price, None))

                # 가격 변동 알림
                if old_price:
                    change_percent = ((new_price - old_price) / old_price) * 100
                    message = f"가격 변동: {old_price:,.0f}원 → {new_price:,.0f}원 ({change_percent:+.1f}%)"
                else:
                    change_percent = 0
                    message = f"가격 설정: {new_price:,.0f}원"

                conn.execute("""
                    INSERT INTO notifications (product_id, notification_type, message)
                    VALUES (?, 'price_change', ?)
                """, (product_id, message))

                # Slack/Discord 가격 변동 알림 발송 (변동이 있을 때만)
                if old_price and abs(change_percent) >= 1.0:  # 1% 이상 변동 시에만
                    try:
                        from notifications.notifier import send_notification
                        send_notification(
                            'price_change',
                            message,
                            product_name=product_name,
                            old_price=old_price,
                            new_price=new_price,
                            change_percent=change_percent
                        )
                    except Exception as e:
                        print(f"[WARN] 가격 변동 알림 발송 실패: {e}")

                # 🛡️ 역마진 방어 로직
                # notes에서 판매가 추출 (예: "판매가: 15,900원 (30% 마진)")
                import re
                selling_price_match = re.search(r'판매가:\s*([0-9,]+)원', notes)

                if selling_price_match and new_price:
                    selling_price = float(selling_price_match.group(1).replace(',', ''))

                    # 50% 마진 권장 판매가
                    recommended_selling_price = new_price * 1.5

                    # 최소 10% 마진 (순이익 보장)
                    min_selling_price = new_price * 1.1

                    # Case 1: 역마진 발생 (판매가 < 소싱가)
                    if selling_price < new_price:
                        margin_loss = new_price - selling_price
                        message = f"⚠️ 역마진 발생! 소싱가({new_price:,.0f}원)가 판매가({selling_price:,.0f}원)보다 높습니다. 손실: {margin_loss:,.0f}원"
                        conn.execute("""
                            INSERT INTO notifications (product_id, notification_type, message)
                            VALUES (?, 'margin_alert', ?)
                        """, (product_id, message))

                        # Slack/Discord 알림 발송
                        try:
                            from notifications.notifier import send_notification
                            send_notification(
                                'margin_alert',
                                message,
                                product_name=product_name,
                                sourcing_price=new_price,
                                selling_price=selling_price,
                                loss=margin_loss
                            )
                        except Exception as e:
                            print(f"[WARN] 역마진 알림 발송 실패: {e}")

                    # Case 2: 최소 마진 미달 (10% 미만)
                    elif selling_price < min_selling_price:
                        current_margin_percent = ((selling_price - new_price) / new_price) * 100
                        message = f"⚠️ 마진 부족! 현재 마진 {current_margin_percent:.1f}% (최소 10% 필요). 권장 판매가: {min_selling_price:,.0f}원 이상"
                        conn.execute("""
                            INSERT INTO notifications (product_id, notification_type, message)
                            VALUES (?, 'margin_alert', ?)
                        """, (product_id, message))

                        # Slack/Discord 알림 발송
                        try:
                            from notifications.notifier import send_notification
                            margin_loss = min_selling_price - selling_price
                            send_notification(
                                'margin_alert',
                                message,
                                product_name=product_name,
                                sourcing_price=new_price,
                                selling_price=selling_price,
                                loss=margin_loss
                            )
                        except Exception as e:
                            print(f"[WARN] 마진 부족 알림 발송 실패: {e}")

                    # Case 3: 권장 마진(50%) 미달 (10~50% 사이)
                    elif selling_price < recommended_selling_price:
                        current_margin_percent = ((selling_price - new_price) / new_price) * 100
                        message = f"💡 마진 최적화 가능! 현재 마진 {current_margin_percent:.1f}% → 50% 마진 권장 판매가: {recommended_selling_price:,.0f}원"
                        conn.execute("""
                            INSERT INTO notifications (product_id, notification_type, message)
                            VALUES (?, 'margin_warning', ?)
                        """, (product_id, message))

            # 상품 정보 업데이트
            update_query = """
                UPDATE monitored_products
                SET current_status = ?, last_checked_at = ?, updated_at = ?
            """
            params = [new_status, datetime.now(), datetime.now()]

            if new_price is not None:
                update_query += ", current_price = ?"
                params.append(new_price)

            update_query += " WHERE id = ?"
            params.append(product_id)

            conn.execute(update_query, params)
            conn.commit()

    def get_status_history(self, product_id: int, limit: int = 50) -> List[Dict]:
        """상태 변경 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM status_changes
                WHERE product_id = ?
                ORDER BY changed_at DESC
                LIMIT ?
            """, (product_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_price_history(self, product_id: int, limit: int = 100) -> List[Dict]:
        """가격 변동 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM price_history
                WHERE product_id = ?
                ORDER BY checked_at DESC
                LIMIT ?
            """, (product_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_unread_notifications(self, limit: int = 50) -> List[Dict]:
        """읽지 않은 알림 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT n.*, p.product_name, p.product_url
                FROM notifications n
                JOIN monitored_products p ON n.product_id = p.id
                WHERE n.is_read = FALSE
                ORDER BY n.created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_notification_as_read(self, notification_id: int):
        """알림을 읽음으로 표시"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE notifications SET is_read = TRUE WHERE id = ?
            """, (notification_id,))
            conn.commit()

    def delete_monitored_product(self, product_id: int):
        """모니터링 상품 삭제"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM monitored_products WHERE id = ?", (product_id,))
            conn.commit()

    def toggle_monitoring(self, product_id: int, is_active: bool):
        """모니터링 활성화/비활성화"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE monitored_products SET is_active = ?, updated_at = ?
                WHERE id = ?
            """, (is_active, datetime.now(), product_id))
            conn.commit()

    def get_dashboard_stats(self) -> Dict:
        """대시보드 통계 조회"""
        with self.get_connection() as conn:
            # 상품 통계
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_products,
                    SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_products,
                    SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as inactive_products
                FROM monitored_products
            """)
            product_stats = dict(cursor.fetchone())

            # 알림 통계
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_notifications,
                    SUM(CASE WHEN is_read = FALSE THEN 1 ELSE 0 END) as unread_notifications,
                    SUM(CASE WHEN notification_type = 'margin_alert' AND is_read = FALSE THEN 1 ELSE 0 END) as margin_alerts,
                    SUM(CASE WHEN created_at > datetime('now', '-24 hours') THEN 1 ELSE 0 END) as recent_notifications
                FROM notifications
            """)
            notification_stats = dict(cursor.fetchone())

            # 최근 가격 변동 통계 (24시간)
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT product_id) as price_changed_products
                FROM price_history
                WHERE checked_at > datetime('now', '-24 hours')
            """)
            price_stats = dict(cursor.fetchone())

            return {
                **product_stats,
                **notification_stats,
                **price_stats
            }

    def get_margin_alert_products(self) -> List[Dict]:
        """역마진 발생 상품 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT p.*, n.message, n.created_at as alert_time
                FROM monitored_products p
                JOIN notifications n ON p.id = n.product_id
                WHERE n.notification_type = 'margin_alert'
                AND n.is_read = FALSE
                ORDER BY n.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # ========================================
    # 주문 관리 메서드 (RPA 자동 발주)
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
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO orders
                (order_number, market, customer_name, customer_phone, customer_address,
                 customer_zipcode, total_amount, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_number, market, customer_name, customer_phone, customer_address,
                  customer_zipcode, total_amount, payment_method, notes))
            conn.commit()
            return cursor.lastrowid

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

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO order_items
                (order_id, monitored_product_id, product_name, product_url, source,
                 quantity, sourcing_price, selling_price, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, monitored_product_id, product_name, product_url, source,
                  quantity, sourcing_price, selling_price, profit))
            conn.commit()
            return cursor.lastrowid

    def get_order(self, order_id: int) -> Optional[Dict]:
        """주문 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_orders(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """주문 목록 조회"""
        with self.get_connection() as conn:
            query = "SELECT * FROM orders"
            params = []

            if status:
                query += " WHERE order_status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_order_items(self, order_id: int) -> List[Dict]:
        """주문 상품 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM order_items WHERE order_id = ?
            """, (order_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_order_items(self, limit: int = 50) -> List[Dict]:
        """자동 발주 대기 중인 상품 목록 조회 (진행 중인 모든 상품 포함)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT oi.*, o.customer_name, o.customer_phone, o.customer_address,
                       o.customer_zipcode, o.market
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE oi.rpa_status IN ('pending', 'step1_completed', 'step3_completed', 'in_progress')
                ORDER BY oi.created_at ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_order_status(self, order_id: int, status: str):
        """주문 상태 업데이트"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE orders
                SET order_status = ?, updated_at = ?
                WHERE id = ?
            """, (status, datetime.now(), order_id))

            if status == 'completed':
                conn.execute("""
                    UPDATE orders
                    SET completed_at = ?
                    WHERE id = ?
                """, (datetime.now(), order_id))

            conn.commit()

    def update_order_item_status(
        self,
        order_item_id: int,
        rpa_status: str,
        tracking_number: Optional[str] = None
    ):
        """주문 상품 RPA 상태 업데이트"""
        with self.get_connection() as conn:
            update_query = """
                UPDATE order_items
                SET rpa_status = ?, updated_at = ?
            """
            params = [rpa_status, datetime.now()]

            if tracking_number:
                update_query += ", tracking_number = ?"
                params.append(tracking_number)

            update_query += " WHERE id = ?"
            params.append(order_item_id)

            conn.execute(update_query, params)
            conn.commit()

    def add_auto_order_log(
        self,
        order_item_id: int,
        source: str,
        action: str,
        status: str,
        message: Optional[str] = None,
        error_details: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        execution_time: Optional[float] = None
    ):
        """RPA 실행 로그 추가"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO auto_order_logs
                (order_item_id, source, action, status, message, error_details,
                 screenshot_path, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_item_id, source, action, status, message, error_details,
                  screenshot_path, execution_time))
            conn.commit()

    def get_auto_order_logs(self, order_item_id: int) -> List[Dict]:
        """RPA 실행 로그 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM auto_order_logs
                WHERE order_item_id = ?
                ORDER BY created_at DESC
            """, (order_item_id,))
            return [dict(row) for row in cursor.fetchall()]

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

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO sourcing_accounts
                (source, account_id, account_password, payment_method, payment_info, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (source, account_id, encrypted_password, payment_method, payment_info, notes, datetime.now()))
            conn.commit()
            return cursor.lastrowid

    def get_sourcing_account(self, source: str) -> Optional[Dict]:
        """소싱처 계정 조회 (비밀번호 자동 복호화)"""
        from playauto.crypto import get_crypto

        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM sourcing_accounts WHERE source = ? AND is_active = TRUE
            """, (source,))
            row = cursor.fetchone()

            if row:
                account = dict(row)
                # 비밀번호 복호화
                try:
                    crypto = get_crypto()
                    account['account_password'] = crypto.decrypt(account['account_password'])
                except Exception as e:
                    # 복호화 실패 시 (평문 비밀번호일 수 있음)
                    print(f"[WARN] 비밀번호 복호화 실패 (평문일 수 있음): {e}")
                return account
            return None

    def get_all_sourcing_accounts(self) -> List[Dict]:
        """모든 소싱처 계정 조회 (비밀번호 자동 복호화)"""
        from playauto.crypto import get_crypto

        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM sourcing_accounts WHERE is_active = TRUE
            """)
            accounts = [dict(row) for row in cursor.fetchall()]

            # 모든 계정의 비밀번호 복호화
            crypto = get_crypto()
            for account in accounts:
                try:
                    account['account_password'] = crypto.decrypt(account['account_password'])
                except Exception as e:
                    # 복호화 실패 시 (평문 비밀번호일 수 있음)
                    print(f"[WARN] 비밀번호 복호화 실패 (평문일 수 있음): {e}")

            return accounts

    # ========================================
    # 플레이오토 API 통합 메서드
    # ========================================

    def save_playauto_setting(self, key: str, value: str, encrypted: bool = False, notes: Optional[str] = None):
        """플레이오토 설정 저장"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO playauto_settings
                (setting_key, setting_value, encrypted, updated_at, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value, encrypted, datetime.now(), notes))
            conn.commit()

    def get_playauto_setting(self, key: str) -> Optional[str]:
        """플레이오토 설정 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT setting_value FROM playauto_settings WHERE setting_key = ?
            """, (key,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_all_playauto_settings(self) -> List[Dict]:
        """모든 플레이오토 설정 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM playauto_settings ORDER BY setting_key
            """)
            return [dict(row) for row in cursor.fetchall()]

    def add_market_order_raw(
        self,
        playauto_order_id: str,
        market: str,
        order_number: str,
        raw_data: str,
        order_date: Optional[datetime] = None
    ) -> int:
        """마켓 주문 원본 저장"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO market_orders_raw
                (playauto_order_id, market, order_number, raw_data, order_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (playauto_order_id, market, order_number, raw_data, order_date, datetime.now()))
            conn.commit()
            return cursor.lastrowid

    def get_unsynced_market_orders(self, limit: int = 100) -> List[Dict]:
        """미동기화 마켓 주문 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM market_orders_raw
                WHERE synced_to_local = FALSE
                ORDER BY order_date DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_market_order_synced(self, playauto_order_id: str, local_order_id: int):
        """마켓 주문 동기화 완료 표시"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE market_orders_raw
                SET synced_to_local = TRUE, local_order_id = ?, updated_at = ?
                WHERE playauto_order_id = ?
            """, (local_order_id, datetime.now(), playauto_order_id))
            conn.commit()

    def sync_playauto_order_to_local(self, playauto_order_data: Dict) -> int:
        """플레이오토 주문을 로컬 DB에 동기화"""
        import json

        # 주문 기본 정보 추출
        playauto_order_id = playauto_order_data.get('playauto_order_id')
        market = playauto_order_data.get('market', 'unknown')
        order_number = playauto_order_data.get('order_number')
        customer_name = playauto_order_data.get('customer_name')
        customer_phone = playauto_order_data.get('customer_phone')
        customer_address = playauto_order_data.get('customer_address')
        customer_zipcode = playauto_order_data.get('customer_zipcode')
        total_amount = playauto_order_data.get('total_amount', 0)
        order_date = playauto_order_data.get('order_date')

        with self.get_connection() as conn:
            # 1. 마켓 주문 원본 저장
            conn.execute("""
                INSERT OR REPLACE INTO market_orders_raw
                (playauto_order_id, market, order_number, raw_data, order_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (playauto_order_id, market, order_number, json.dumps(playauto_order_data, ensure_ascii=False), order_date, datetime.now()))

            # 2. 로컬 주문 테이블에 추가
            cursor = conn.execute("""
                INSERT INTO orders
                (order_number, market, customer_name, customer_phone, customer_address,
                 customer_zipcode, total_amount, playauto_order_id, synced_to_playauto, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE, ?)
            """, (order_number, market, customer_name, customer_phone, customer_address,
                  customer_zipcode, total_amount, playauto_order_id, f"플레이오토 자동 수집: {datetime.now()}"))

            local_order_id = cursor.lastrowid

            # 3. 주문 상품 추가 (있는 경우)
            items = playauto_order_data.get('items', [])
            for item in items:
                product_name = item.get('product_name', 'Unknown')
                product_url = item.get('product_url', '')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0)

                conn.execute("""
                    INSERT INTO order_items
                    (order_id, product_name, product_url, source, quantity,
                     sourcing_price, selling_price, profit, rpa_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """, (local_order_id, product_name, product_url, market, quantity,
                      price, price, 0))

            # 4. 마켓 주문을 동기화 완료로 표시
            conn.execute("""
                UPDATE market_orders_raw
                SET synced_to_local = TRUE, local_order_id = ?, updated_at = ?
                WHERE playauto_order_id = ?
            """, (local_order_id, datetime.now(), playauto_order_id))

            conn.commit()
            return local_order_id

    def get_completed_orders_with_tracking(self, days: int = 7) -> List[Dict]:
        """송장번호가 있는 완료 주문 조회 (최근 N일)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT o.*, oi.tracking_number
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.order_status = 'completed'
                AND oi.tracking_number IS NOT NULL
                AND oi.tracking_number != ''
                AND (o.tracking_uploaded_at IS NULL OR o.synced_to_playauto = FALSE)
                AND o.created_at > datetime('now', '-' || ? || ' days')
                ORDER BY o.created_at DESC
            """, (days,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_tracking_uploaded(self, order_id: int):
        """송장 업로드 완료 표시"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE orders
                SET tracking_uploaded_at = ?, synced_to_playauto = TRUE, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), datetime.now(), order_id))
            conn.commit()

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
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO playauto_sync_logs
                (sync_type, status, request_data, response_data, items_count,
                 success_count, fail_count, error_message, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sync_type, status, request_data, response_data, items_count,
                  success_count, fail_count, error_message, execution_time))
            conn.commit()
            return cursor.lastrowid

    def get_playauto_sync_logs(self, sync_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """플레이오토 동기화 로그 조회"""
        with self.get_connection() as conn:
            query = "SELECT * FROM playauto_sync_logs"
            params = []

            if sync_type:
                query += " WHERE sync_type = ?"
                params.append(sync_type)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_playauto_stats(self) -> Dict:
        """플레이오토 통계 조회"""
        with self.get_connection() as conn:
            # 총 수집 주문 수
            cursor = conn.execute("""
                SELECT COUNT(*) as total_orders FROM market_orders_raw
            """)
            total_orders = cursor.fetchone()[0]

            # 동기화된 주문 수
            cursor = conn.execute("""
                SELECT COUNT(*) as synced_orders FROM market_orders_raw
                WHERE synced_to_local = TRUE
            """)
            synced_orders = cursor.fetchone()[0]

            # 총 업로드 송장 수
            cursor = conn.execute("""
                SELECT COUNT(*) as uploaded_tracking FROM orders
                WHERE tracking_uploaded_at IS NOT NULL
            """)
            uploaded_tracking = cursor.fetchone()[0]

            # 오늘 동기화 수
            cursor = conn.execute("""
                SELECT COUNT(*) as today_synced FROM playauto_sync_logs
                WHERE sync_type = 'order_fetch'
                AND status = 'success'
                AND created_at > datetime('now', '-1 day')
            """)
            today_synced = cursor.fetchone()[0]

            # 최근 7일 추이
            cursor = conn.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM playauto_sync_logs
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            recent_trend = [dict(row) for row in cursor.fetchall()]

            return {
                'total_orders': total_orders,
                'synced_orders': synced_orders,
                'uploaded_tracking': uploaded_tracking,
                'today_synced': today_synced,
                'recent_trend': recent_trend
            }

    # ============= Webhook 설정 관리 =============

    def save_webhook_setting(
        self,
        webhook_type: str,
        webhook_url: str,
        enabled: bool = True,
        notification_types: str = 'all'
    ) -> int:
        """Webhook 설정 저장 (INSERT or UPDATE)"""
        with self.get_connection() as conn:
            # 기존 설정이 있는지 확인
            cursor = conn.execute("""
                SELECT id FROM webhook_settings WHERE webhook_type = ?
            """, (webhook_type,))
            existing = cursor.fetchone()

            if existing:
                # UPDATE
                conn.execute("""
                    UPDATE webhook_settings
                    SET webhook_url = ?, enabled = ?, notification_types = ?, updated_at = ?
                    WHERE webhook_type = ?
                """, (webhook_url, enabled, notification_types, datetime.now(), webhook_type))
                conn.commit()
                return existing[0]
            else:
                # INSERT
                cursor = conn.execute("""
                    INSERT INTO webhook_settings (webhook_type, webhook_url, enabled, notification_types)
                    VALUES (?, ?, ?, ?)
                """, (webhook_type, webhook_url, enabled, notification_types))
                conn.commit()
                return cursor.lastrowid

    def get_webhook_setting(self, webhook_type: str) -> Optional[Dict]:
        """특정 Webhook 설정 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM webhook_settings WHERE webhook_type = ?
            """, (webhook_type,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_webhook_settings(self, enabled_only: bool = False) -> List[Dict]:
        """모든 Webhook 설정 조회"""
        with self.get_connection() as conn:
            query = "SELECT * FROM webhook_settings"
            if enabled_only:
                query += " WHERE enabled = TRUE"
            query += " ORDER BY webhook_type"

            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def toggle_webhook(self, webhook_type: str, enabled: bool):
        """Webhook 활성화/비활성화"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE webhook_settings
                SET enabled = ?, updated_at = ?
                WHERE webhook_type = ?
            """, (enabled, datetime.now(), webhook_type))
            conn.commit()

    def delete_webhook_setting(self, webhook_type: str):
        """Webhook 설정 삭제"""
        with self.get_connection() as conn:
            conn.execute("""
                DELETE FROM webhook_settings WHERE webhook_type = ?
            """, (webhook_type,))
            conn.commit()

    # ============= Webhook 로그 관리 =============

    def add_webhook_log(
        self,
        webhook_id: Optional[int],
        notification_type: str,
        status: str,
        message: Optional[str] = None,
        error_details: Optional[str] = None
    ) -> int:
        """Webhook 실행 로그 추가"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO webhook_logs
                (webhook_id, notification_type, status, message, error_details)
                VALUES (?, ?, ?, ?, ?)
            """, (webhook_id, notification_type, status, message, error_details))
            conn.commit()
            return cursor.lastrowid

    def get_webhook_logs(self, limit: int = 50, webhook_type: Optional[str] = None) -> List[Dict]:
        """Webhook 로그 조회"""
        with self.get_connection() as conn:
            if webhook_type:
                cursor = conn.execute("""
                    SELECT wl.*, ws.webhook_type
                    FROM webhook_logs wl
                    LEFT JOIN webhook_settings ws ON wl.webhook_id = ws.id
                    WHERE ws.webhook_type = ?
                    ORDER BY wl.created_at DESC
                    LIMIT ?
                """, (webhook_type, limit))
            else:
                cursor = conn.execute("""
                    SELECT wl.*, ws.webhook_type
                    FROM webhook_logs wl
                    LEFT JOIN webhook_settings ws ON wl.webhook_id = ws.id
                    ORDER BY wl.created_at DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ============= 자동 재고 관리 로그 =============

    def add_inventory_auto_log(
        self,
        product_id: int,
        action: str,
        old_status: Optional[str],
        new_status: Optional[str],
        is_active_before: Optional[bool] = None,
        is_active_after: Optional[bool] = None
    ) -> int:
        """자동 재고 관리 로그 추가"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO inventory_auto_logs
                (product_id, action, old_status, new_status, is_active_before, is_active_after)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, action, old_status, new_status, is_active_before, is_active_after))
            conn.commit()
            return cursor.lastrowid

    def get_inventory_auto_logs(self, product_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """자동 재고 관리 로그 조회"""
        with self.get_connection() as conn:
            if product_id:
                cursor = conn.execute("""
                    SELECT ial.*, mp.product_name
                    FROM inventory_auto_logs ial
                    JOIN monitored_products mp ON ial.product_id = mp.id
                    WHERE ial.product_id = ?
                    ORDER BY ial.created_at DESC
                    LIMIT ?
                """, (product_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT ial.*, mp.product_name
                    FROM inventory_auto_logs ial
                    JOIN monitored_products mp ON ial.product_id = mp.id
                    ORDER BY ial.created_at DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_product_active_status(self, product_id: int, is_active: bool):
        """상품 모니터링 활성화 상태 변경"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE monitored_products
                SET is_active = ?, updated_at = ?
                WHERE id = ?
            """, (is_active, datetime.now(), product_id))
            conn.commit()

    # ========================================
    # 내 판매 상품 관리
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
        notes: Optional[str] = None
    ) -> int:
        """판매 상품 추가"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO my_selling_products
                (product_name, selling_price, monitored_product_id, sourcing_url, sourcing_product_name,
                 sourcing_price, sourcing_source, detail_page_data, category, thumbnail_url, original_thumbnail_url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_name, selling_price, monitored_product_id, sourcing_url, sourcing_product_name,
                  sourcing_price, sourcing_source, detail_page_data, category, thumbnail_url, original_thumbnail_url, notes))
            conn.commit()
            return cursor.lastrowid

    def get_selling_products(self, is_active: Optional[bool] = None, limit: int = 100) -> List[Dict]:
        """판매 상품 목록 조회 (소싱 정보 포함)"""
        with self.get_connection() as conn:
            query = """
                SELECT
                    sp.*,
                    mp.product_name as monitored_product_name,
                    mp.product_url as monitored_product_url,
                    mp.source as monitored_source,
                    mp.current_price as monitored_price,
                    mp.current_status as monitored_status,
                    COALESCE(sp.sourcing_price, mp.current_price, 0) as effective_sourcing_price,
                    (sp.selling_price - COALESCE(sp.sourcing_price, mp.current_price, 0)) as margin,
                    CASE
                        WHEN COALESCE(sp.sourcing_price, mp.current_price, 0) > 0 THEN
                            ((sp.selling_price - COALESCE(sp.sourcing_price, mp.current_price, 0)) /
                             COALESCE(sp.sourcing_price, mp.current_price) * 100)
                        ELSE 0
                    END as margin_rate
                FROM my_selling_products sp
                LEFT JOIN monitored_products mp ON sp.monitored_product_id = mp.id
            """

            params = []
            if is_active is not None:
                query += " WHERE sp.is_active = ?"
                params.append(is_active)

            query += " ORDER BY sp.created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                product = dict(row)
                # Convert SQLite integer booleans to Python booleans
                if 'is_active' in product:
                    product['is_active'] = bool(product['is_active'])
                results.append(product)
            return results

    def get_selling_product(self, product_id: int) -> Optional[Dict]:
        """판매 상품 상세 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    sp.*,
                    mp.product_name as monitored_product_name,
                    mp.product_url as monitored_product_url,
                    mp.source as monitored_source,
                    mp.current_price as monitored_price,
                    mp.current_status as monitored_status,
                    COALESCE(sp.sourcing_price, mp.current_price, 0) as effective_sourcing_price,
                    (sp.selling_price - COALESCE(sp.sourcing_price, mp.current_price, 0)) as margin,
                    CASE
                        WHEN COALESCE(sp.sourcing_price, mp.current_price, 0) > 0 THEN
                            ((sp.selling_price - COALESCE(sp.sourcing_price, mp.current_price, 0)) /
                             COALESCE(sp.sourcing_price, mp.current_price) * 100)
                        ELSE 0
                    END as margin_rate
                FROM my_selling_products sp
                LEFT JOIN monitored_products mp ON sp.monitored_product_id = mp.id
                WHERE sp.id = ?
            """, (product_id,))
            row = cursor.fetchone()
            if row:
                product = dict(row)
                # Convert SQLite integer booleans to Python booleans
                if 'is_active' in product:
                    product['is_active'] = bool(product['is_active'])
                return product
            return None

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
        is_active: Optional[bool] = None,
        notes: Optional[str] = None
    ):
        """판매 상품 수정 (마진 변동 자동 기록)"""
        # 기존 데이터 조회
        old_product = self.get_selling_product(product_id)
        if not old_product:
            return

        with self.get_connection() as conn:
            updates = []
            params = []

            if product_name is not None:
                updates.append("product_name = ?")
                params.append(product_name)
            if selling_price is not None:
                updates.append("selling_price = ?")
                params.append(selling_price)
            if monitored_product_id is not None:
                updates.append("monitored_product_id = ?")
                params.append(monitored_product_id)
            if sourcing_url is not None:
                updates.append("sourcing_url = ?")
                params.append(sourcing_url)
            if sourcing_product_name is not None:
                updates.append("sourcing_product_name = ?")
                params.append(sourcing_product_name)
            if sourcing_price is not None:
                updates.append("sourcing_price = ?")
                params.append(sourcing_price)
            if sourcing_source is not None:
                updates.append("sourcing_source = ?")
                params.append(sourcing_source)
            if detail_page_data is not None:
                updates.append("detail_page_data = ?")
                params.append(detail_page_data)
            if category is not None:
                updates.append("category = ?")
                params.append(category)
            if thumbnail_url is not None:
                updates.append("thumbnail_url = ?")
                params.append(thumbnail_url)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)

            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now())
                params.append(product_id)

                conn.execute(f"""
                    UPDATE my_selling_products
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                conn.commit()

                # 판매가 변경 시 마진 변동 기록
                if selling_price is not None and selling_price != old_product['selling_price']:
                    new_product = self.get_selling_product(product_id)
                    if new_product:
                        self.log_margin_change(
                            selling_product_id=product_id,
                            old_margin=old_product.get('margin', 0),
                            new_margin=new_product.get('margin', 0),
                            old_margin_rate=old_product.get('margin_rate', 0),
                            new_margin_rate=new_product.get('margin_rate', 0),
                            change_reason='selling_price_changed',
                            old_selling_price=old_product['selling_price'],
                            new_selling_price=selling_price,
                            old_sourcing_price=old_product.get('sourcing_price'),
                            new_sourcing_price=new_product.get('sourcing_price')
                        )

    def delete_selling_product(self, product_id: int):
        """판매 상품 삭제"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM my_selling_products WHERE id = ?", (product_id,))
            conn.commit()

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
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO margin_change_logs
                (selling_product_id, old_margin, new_margin, old_margin_rate, new_margin_rate,
                 change_reason, old_selling_price, new_selling_price, old_sourcing_price, new_sourcing_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (selling_product_id, old_margin, new_margin, old_margin_rate, new_margin_rate,
                  change_reason, old_selling_price, new_selling_price, old_sourcing_price, new_sourcing_price))
            conn.commit()
            return cursor.lastrowid

    def get_margin_change_logs(self, selling_product_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """마진 변동 이력 조회"""
        with self.get_connection() as conn:
            if selling_product_id:
                cursor = conn.execute("""
                    SELECT mcl.*, sp.product_name
                    FROM margin_change_logs mcl
                    JOIN my_selling_products sp ON mcl.selling_product_id = sp.id
                    WHERE mcl.selling_product_id = ?
                    ORDER BY mcl.created_at DESC
                    LIMIT ?
                """, (selling_product_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT mcl.*, sp.product_name
                    FROM margin_change_logs mcl
                    JOIN my_selling_products sp ON mcl.selling_product_id = sp.id
                    ORDER BY mcl.created_at DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_margin_notification_status(self, log_id: int, sent: bool = True):
        """마진 변동 알림 발송 상태 업데이트"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE margin_change_logs
                SET notification_sent = ?
                WHERE id = ?
            """, (sent, log_id))
            conn.commit()


# 싱글톤 인스턴스
_db_instance = None


def get_db() -> Database:
    """데이터베이스 인스턴스 가져오기"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
