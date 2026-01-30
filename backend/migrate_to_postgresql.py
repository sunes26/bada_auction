"""
SQLite to PostgreSQL Migration Script
Migrates all data from local SQLite to Supabase PostgreSQL
"""

import os
import sys
import sqlite3
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database_manager import DatabaseManager
from database.models import (
    MonitoredProduct, PriceHistory, StatusChange, Notification,
    Order, OrderItem, AutoOrderLog, SourcingAccount,
    PlayautoSetting, PlayautoSyncLog, MarketOrderRaw,
    WebhookSetting, WebhookLog, MySellingProduct, MarginChangeLog,
    InventoryAutoLog, Category, Expense, Settlement, TaxInfo,
    TrackingUploadScheduler, TrackingUploadJob, TrackingUploadDetail
)

# Load environment variables
load_dotenv()


class SQLiteToPostgreSQLMigrator:
    """Migrates data from SQLite to PostgreSQL"""

    def __init__(self, sqlite_path: str = "monitoring.db", postgres_url: str = None):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url or os.getenv('DATABASE_URL')

        if not self.postgres_url:
            raise ValueError("PostgreSQL URL not provided. Set DATABASE_URL environment variable.")

        # Connect to SQLite
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row

        # Connect to PostgreSQL
        self.pg_manager = DatabaseManager(self.postgres_url)
        self.pg_manager.create_all_tables()

        print(f"[OK] Connected to SQLite: {sqlite_path}")
        print(f"[OK] Connected to PostgreSQL: {postgres_url[:50]}...")

    def migrate_all(self):
        """Migrate all tables"""
        print("\n" + "="*60)
        print("Starting Full Migration: SQLite → PostgreSQL")
        print("="*60 + "\n")

        start_time = datetime.now()

        # Migration order (respects foreign key constraints)
        migration_steps = [
            ("monitored_products", self.migrate_monitored_products),
            ("price_history", self.migrate_price_history),
            ("status_changes", self.migrate_status_changes),
            ("notifications", self.migrate_notifications),
            ("orders", self.migrate_orders),
            ("order_items", self.migrate_order_items),
            ("auto_order_logs", self.migrate_auto_order_logs),
            ("sourcing_accounts", self.migrate_sourcing_accounts),
            ("playauto_settings", self.migrate_playauto_settings),
            ("playauto_sync_logs", self.migrate_playauto_sync_logs),
            ("market_orders_raw", self.migrate_market_orders_raw),
            ("webhook_settings", self.migrate_webhook_settings),
            ("webhook_logs", self.migrate_webhook_logs),
            ("my_selling_products", self.migrate_my_selling_products),
            ("margin_change_logs", self.migrate_margin_change_logs),
            ("inventory_auto_logs", self.migrate_inventory_auto_logs),
            ("categories", self.migrate_categories),
            ("expenses", self.migrate_expenses),
            ("settlements", self.migrate_settlements),
            ("tax_info", self.migrate_tax_info),
            ("tracking_upload_scheduler", self.migrate_tracking_upload_scheduler),
            ("tracking_upload_jobs", self.migrate_tracking_upload_jobs),
            ("tracking_upload_details", self.migrate_tracking_upload_details),
        ]

        total_records = 0
        for table_name, migrate_func in migration_steps:
            try:
                count = migrate_func()
                total_records += count
                print(f"✓ {table_name}: {count} records migrated")
            except Exception as e:
                print(f"✗ {table_name}: Migration failed - {e}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "="*60)
        print(f"Migration completed in {duration:.2f} seconds")
        print(f"Total records migrated: {total_records}")
        print("="*60 + "\n")

    def migrate_monitored_products(self) -> int:
        """Migrate monitored_products table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM monitored_products")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                product = MonitoredProduct(
                    id=row['id'],
                    product_url=row['product_url'],
                    product_name=row['product_name'],
                    source=row['source'],
                    current_price=row['current_price'],
                    original_price=row['original_price'],
                    current_status=row['current_status'],
                    last_checked_at=self._parse_datetime(row['last_checked_at']),
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at']),
                    check_interval=row['check_interval'],
                    is_active=bool(row['is_active']),
                    notes=row['notes']
                )
                session.add(product)

        return len(rows)

    def migrate_price_history(self) -> int:
        """Migrate price_history table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM price_history")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                history = PriceHistory(
                    id=row['id'],
                    product_id=row['product_id'],
                    price=row['price'],
                    original_price=row['original_price'],
                    checked_at=self._parse_datetime(row['checked_at'])
                )
                session.add(history)

        return len(rows)

    def migrate_status_changes(self) -> int:
        """Migrate status_changes table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM status_changes")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                change = StatusChange(
                    id=row['id'],
                    product_id=row['product_id'],
                    old_status=row['old_status'],
                    new_status=row['new_status'],
                    changed_at=self._parse_datetime(row['changed_at']),
                    details=row['details']
                )
                session.add(change)

        return len(rows)

    def migrate_notifications(self) -> int:
        """Migrate notifications table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM notifications")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                notification = Notification(
                    id=row['id'],
                    product_id=row['product_id'],
                    notification_type=row['notification_type'],
                    message=row['message'],
                    is_read=bool(row['is_read']),
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(notification)

        return len(rows)

    def migrate_orders(self) -> int:
        """Migrate orders table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM orders")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                order = Order(
                    id=row['id'],
                    order_number=row['order_number'],
                    market=row['market'],
                    customer_name=row['customer_name'],
                    customer_phone=row['customer_phone'],
                    customer_address=row['customer_address'],
                    customer_zipcode=row['customer_zipcode'],
                    order_status=row['order_status'],
                    total_amount=row['total_amount'],
                    total_profit=row['total_profit'],
                    payment_method=row['payment_method'],
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at']),
                    completed_at=self._parse_datetime(row['completed_at']),
                    notes=row['notes']
                )
                session.add(order)

        return len(rows)

    def migrate_order_items(self) -> int:
        """Migrate order_items table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM order_items")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                item = OrderItem(
                    id=row['id'],
                    order_id=row['order_id'],
                    monitored_product_id=row['monitored_product_id'],
                    product_name=row['product_name'],
                    product_url=row['product_url'],
                    source=row['source'],
                    quantity=row['quantity'],
                    sourcing_price=row['sourcing_price'],
                    selling_price=row['selling_price'],
                    profit=row['profit'],
                    rpa_status=row['rpa_status'],
                    tracking_number=row['tracking_number'],
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(item)

        return len(rows)

    def migrate_auto_order_logs(self) -> int:
        """Migrate auto_order_logs table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM auto_order_logs")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                log = AutoOrderLog(
                    id=row['id'],
                    order_item_id=row['order_item_id'],
                    source=row['source'],
                    action=row['action'],
                    status=row['status'],
                    message=row['message'],
                    error_details=row['error_details'],
                    screenshot_path=row['screenshot_path'],
                    execution_time=row['execution_time'],
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(log)

        return len(rows)

    def migrate_sourcing_accounts(self) -> int:
        """Migrate sourcing_accounts table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM sourcing_accounts")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                account = SourcingAccount(
                    id=row['id'],
                    source=row['source'],
                    account_id=row['account_id'],
                    account_password=row['account_password'],
                    payment_method=row['payment_method'],
                    payment_info=row['payment_info'],
                    is_active=bool(row['is_active']),
                    last_login_at=self._parse_datetime(row['last_login_at']),
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at']),
                    notes=row['notes']
                )
                session.add(account)

        return len(rows)

    def migrate_playauto_settings(self) -> int:
        """Migrate playauto_settings table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM playauto_settings")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                setting = PlayautoSetting(
                    id=row['id'],
                    setting_key=row['setting_key'],
                    setting_value=row['setting_value'],
                    encrypted=bool(row['encrypted']),
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at']),
                    notes=row['notes']
                )
                session.add(setting)

        return len(rows)

    def migrate_playauto_sync_logs(self) -> int:
        """Migrate playauto_sync_logs table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM playauto_sync_logs")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                log = PlayautoSyncLog(
                    id=row['id'],
                    sync_type=row['sync_type'],
                    status=row['status'],
                    request_data=row['request_data'],
                    response_data=row['response_data'],
                    items_count=row['items_count'],
                    success_count=row['success_count'],
                    fail_count=row['fail_count'],
                    error_message=row['error_message'],
                    execution_time=row['execution_time'],
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(log)

        return len(rows)

    def migrate_market_orders_raw(self) -> int:
        """Migrate market_orders_raw table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM market_orders_raw")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                raw_order = MarketOrderRaw(
                    id=row['id'],
                    playauto_order_id=row['playauto_order_id'],
                    market=row['market'],
                    order_number=row['order_number'],
                    raw_data=row['raw_data'],
                    order_date=self._parse_datetime(row['order_date']),
                    synced_to_local=bool(row['synced_to_local']),
                    local_order_id=row['local_order_id'],
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(raw_order)

        return len(rows)

    def migrate_webhook_settings(self) -> int:
        """Migrate webhook_settings table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM webhook_settings")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                webhook = WebhookSetting(
                    id=row['id'],
                    webhook_type=row['webhook_type'],
                    webhook_url=row['webhook_url'],
                    enabled=bool(row['enabled']),
                    notification_types=row['notification_types'],
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(webhook)

        return len(rows)

    def migrate_webhook_logs(self) -> int:
        """Migrate webhook_logs table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM webhook_logs")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                log = WebhookLog(
                    id=row['id'],
                    webhook_id=row['webhook_id'],
                    notification_type=row['notification_type'],
                    status=row['status'],
                    message=row['message'],
                    error_details=row['error_details'],
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(log)

        return len(rows)

    def migrate_my_selling_products(self) -> int:
        """Migrate my_selling_products table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM my_selling_products")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                product = MySellingProduct(
                    id=row['id'],
                    product_name=row['product_name'],
                    selling_price=row['selling_price'],
                    monitored_product_id=row['monitored_product_id'],
                    sourcing_url=row['sourcing_url'],
                    sourcing_product_name=row['sourcing_product_name'],
                    sourcing_price=row['sourcing_price'],
                    sourcing_source=row['sourcing_source'],
                    detail_page_data=row['detail_page_data'],
                    category=row['category'],
                    thumbnail_url=row['thumbnail_url'],
                    is_active=bool(row['is_active']),
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at']),
                    notes=row['notes']
                )
                session.add(product)

        return len(rows)

    def migrate_margin_change_logs(self) -> int:
        """Migrate margin_change_logs table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM margin_change_logs")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                log = MarginChangeLog(
                    id=row['id'],
                    selling_product_id=row['selling_product_id'],
                    old_margin=row['old_margin'],
                    new_margin=row['new_margin'],
                    old_margin_rate=row['old_margin_rate'],
                    new_margin_rate=row['new_margin_rate'],
                    change_reason=row['change_reason'],
                    old_selling_price=row['old_selling_price'],
                    new_selling_price=row['new_selling_price'],
                    old_sourcing_price=row['old_sourcing_price'],
                    new_sourcing_price=row['new_sourcing_price'],
                    notification_sent=bool(row['notification_sent']),
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(log)

        return len(rows)

    def migrate_inventory_auto_logs(self) -> int:
        """Migrate inventory_auto_logs table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM inventory_auto_logs")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                log = InventoryAutoLog(
                    id=row['id'],
                    product_id=row['product_id'],
                    action=row['action'],
                    old_status=row['old_status'],
                    new_status=row['new_status'],
                    is_active_before=bool(row['is_active_before']) if row['is_active_before'] is not None else None,
                    is_active_after=bool(row['is_active_after']) if row['is_active_after'] is not None else None,
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(log)

        return len(rows)

    def migrate_categories(self) -> int:
        """Migrate categories table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM categories")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                category = Category(
                    id=row['id'],
                    folder_number=row['folder_number'],
                    folder_name=row['folder_name'],
                    level1=row['level1'],
                    level2=row['level2'],
                    level3=row['level3'],
                    level4=row['level4'],
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(category)

        return len(rows)

    def migrate_expenses(self) -> int:
        """Migrate expenses table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM expenses")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                expense = Expense(
                    id=row['id'],
                    expense_date=self._parse_date(row['expense_date']),
                    category=row['category'],
                    subcategory=row['subcategory'],
                    amount=row['amount'],
                    description=row['description'],
                    payment_method=row['payment_method'],
                    receipt_url=row['receipt_url'],
                    is_vat_deductible=bool(row['is_vat_deductible']),
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(expense)

        return len(rows)

    def migrate_settlements(self) -> int:
        """Migrate settlements table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM settlements")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                settlement = Settlement(
                    id=row['id'],
                    market=row['market'],
                    settlement_date=self._parse_date(row['settlement_date']),
                    period_start=self._parse_date(row['period_start']),
                    period_end=self._parse_date(row['period_end']),
                    total_sales=row['total_sales'],
                    commission=row['commission'],
                    shipping_fee=row['shipping_fee'],
                    promotion_cost=row['promotion_cost'],
                    net_amount=row['net_amount'],
                    settlement_status=row['settlement_status'],
                    memo=row['memo'],
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(settlement)

        return len(rows)

    def migrate_tax_info(self) -> int:
        """Migrate tax_info table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM tax_info")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                tax = TaxInfo(
                    id=row['id'],
                    year=row['year'],
                    quarter=row['quarter'],
                    total_sales=row['total_sales'],
                    total_purchases=row['total_purchases'],
                    vat_payable=row['vat_payable'],
                    income_tax_estimate=row['income_tax_estimate'],
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(tax)

        return len(rows)

    def migrate_tracking_upload_scheduler(self) -> int:
        """Migrate tracking_upload_scheduler table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM tracking_upload_scheduler")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                scheduler = TrackingUploadScheduler(
                    id=row['id'],
                    enabled=bool(row['enabled']),
                    schedule_time=row['schedule_time'],
                    retry_count=row['retry_count'],
                    notify_discord=bool(row['notify_discord']),
                    notify_slack=bool(row['notify_slack']),
                    discord_webhook=row['discord_webhook'],
                    slack_webhook=row['slack_webhook'],
                    last_run_at=self._parse_datetime(row['last_run_at']),
                    next_run_at=self._parse_datetime(row['next_run_at']),
                    created_at=self._parse_datetime(row['created_at']),
                    updated_at=self._parse_datetime(row['updated_at'])
                )
                session.add(scheduler)

        return len(rows)

    def migrate_tracking_upload_jobs(self) -> int:
        """Migrate tracking_upload_jobs table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM tracking_upload_jobs")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                job = TrackingUploadJob(
                    id=row['id'],
                    job_type=row['job_type'],
                    status=row['status'],
                    total_count=row['total_count'],
                    success_count=row['success_count'],
                    failed_count=row['failed_count'],
                    retry_count=row['retry_count'],
                    progress_percent=row['progress_percent'],
                    error_message=row['error_message'],
                    details=row['details'],
                    started_at=self._parse_datetime(row['started_at']),
                    completed_at=self._parse_datetime(row['completed_at']),
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(job)

        return len(rows)

    def migrate_tracking_upload_details(self) -> int:
        """Migrate tracking_upload_details table"""
        cursor = self.sqlite_conn.execute("SELECT * FROM tracking_upload_details")
        rows = cursor.fetchall()

        with self.pg_manager.get_session() as session:
            for row in rows:
                detail = TrackingUploadDetail(
                    id=row['id'],
                    job_id=row['job_id'],
                    order_id=row['order_id'],
                    order_no=row['order_no'],
                    carrier_code=row['carrier_code'],
                    tracking_number=row['tracking_number'],
                    status=row['status'],
                    retry_attempt=row['retry_attempt'],
                    error_message=row['error_message'],
                    uploaded_at=self._parse_datetime(row['uploaded_at']),
                    created_at=self._parse_datetime(row['created_at'])
                )
                session.add(detail)

        return len(rows)

    def _parse_datetime(self, value):
        """Parse datetime from SQLite"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return None

    def _parse_date(self, value):
        """Parse date from SQLite"""
        if value is None:
            return None
        try:
            return datetime.fromisoformat(str(value)).date()
        except:
            return None

    def close(self):
        """Close connections"""
        self.sqlite_conn.close()


def main():
    """Run migration"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate SQLite to PostgreSQL')
    parser.add_argument('--sqlite', default='monitoring.db', help='Path to SQLite database')
    parser.add_argument('--postgres', help='PostgreSQL connection URL (or use DATABASE_URL env var)')
    parser.add_argument('--dry-run', action='store_true', help='Test connection without migrating')

    args = parser.parse_args()

    try:
        migrator = SQLiteToPostgreSQLMigrator(args.sqlite, args.postgres)

        if args.dry_run:
            print("[DRY RUN] Testing connections...")
            print(f"✓ SQLite connection OK")
            print(f"✓ PostgreSQL connection OK")
            print(f"✓ Tables created/verified")
            print("\nRun without --dry-run to migrate data")
        else:
            migrator.migrate_all()

        migrator.close()

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
