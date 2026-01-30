"""
SQLAlchemy ORM Models for 온백AI
Database-agnostic models (works with both SQLite and PostgreSQL)
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Numeric, Boolean,
    DateTime, Date, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ==========================================
# Monitoring System
# ==========================================

class MonitoredProduct(Base):
    __tablename__ = 'monitored_products'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_url = Column(Text, nullable=False, unique=True)
    product_name = Column(Text, nullable=False)
    source = Column(Text, nullable=False)  # 소싱처 마켓
    current_price = Column(Numeric(10, 2))
    original_price = Column(Numeric(10, 2))
    current_status = Column(Text, default='available')
    last_checked_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    check_interval = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    status_changes = relationship("StatusChange", back_populates="product", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="monitored_product")
    selling_products = relationship("MySellingProduct", back_populates="monitored_product")
    inventory_logs = relationship("InventoryAutoLog", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_monitored_products_active', 'is_active', 'last_checked_at'),
    )


class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('monitored_products.id', ondelete='CASCADE'), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2))
    checked_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    product = relationship("MonitoredProduct", back_populates="price_history")

    __table_args__ = (
        Index('idx_price_history_product', 'product_id', 'checked_at'),
    )


class StatusChange(Base):
    __tablename__ = 'status_changes'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('monitored_products.id', ondelete='CASCADE'), nullable=False)
    old_status = Column(Text)
    new_status = Column(Text, nullable=False)
    changed_at = Column(DateTime, default=func.current_timestamp())
    details = Column(Text)

    # Relationships
    product = relationship("MonitoredProduct", back_populates="status_changes")

    __table_args__ = (
        Index('idx_status_changes_product', 'product_id', 'changed_at'),
    )


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('monitored_products.id', ondelete='CASCADE'), nullable=False)
    notification_type = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    product = relationship("MonitoredProduct", back_populates="notifications")

    __table_args__ = (
        Index('idx_notifications_unread', 'is_read', 'created_at'),
        Index('idx_notifications_product_type', 'product_id', 'notification_type', 'created_at'),
    )


# ==========================================
# Order Management System
# ==========================================

class Order(Base):
    __tablename__ = 'orders'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_number = Column(Text, nullable=False, unique=True)
    market = Column(Text, nullable=False)  # 판매처 마켓
    customer_name = Column(Text, nullable=False)
    customer_phone = Column(Text)
    customer_address = Column(Text, nullable=False)
    customer_zipcode = Column(Text)
    order_status = Column(Text, default='pending')
    total_amount = Column(Numeric(10, 2), nullable=False)
    total_profit = Column(Numeric(10, 2))
    payment_method = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    completed_at = Column(DateTime)
    notes = Column(Text)

    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    market_order_raw = relationship("MarketOrderRaw", back_populates="local_order")

    __table_args__ = (
        Index('idx_orders_status', 'order_status', 'created_at'),
        Index('idx_orders_market', 'market', 'created_at'),
        Index('idx_orders_order_number', 'order_number'),
    )


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    monitored_product_id = Column(BigInteger, ForeignKey('monitored_products.id', ondelete='SET NULL'))
    product_name = Column(Text, nullable=False)
    product_url = Column(Text, nullable=False)
    source = Column(Text, nullable=False)  # 소싱처 마켓
    quantity = Column(Integer, nullable=False, default=1)
    sourcing_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    profit = Column(Numeric(10, 2))
    rpa_status = Column(Text, default='pending')
    tracking_number = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    order = relationship("Order", back_populates="order_items")
    monitored_product = relationship("MonitoredProduct", back_populates="order_items")
    auto_order_logs = relationship("AutoOrderLog", back_populates="order_item", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_order_items_order', 'order_id'),
        Index('idx_order_items_rpa_status', 'rpa_status'),
        Index('idx_order_items_tracking', 'tracking_number'),
    )


class AutoOrderLog(Base):
    __tablename__ = 'auto_order_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_item_id = Column(BigInteger, ForeignKey('order_items.id', ondelete='CASCADE'), nullable=False)
    source = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    message = Column(Text)
    error_details = Column(Text)
    screenshot_path = Column(Text)
    execution_time = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    order_item = relationship("OrderItem", back_populates="auto_order_logs")

    __table_args__ = (
        Index('idx_auto_order_logs_item', 'order_item_id', 'created_at'),
    )


class SourcingAccount(Base):
    __tablename__ = 'sourcing_accounts'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(Text, nullable=False, unique=True)
    account_id = Column(Text, nullable=False)
    account_password = Column(Text, nullable=False)
    payment_method = Column(Text)
    payment_info = Column(Text)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    notes = Column(Text)


# ==========================================
# Playauto Integration
# ==========================================

class PlayautoSetting(Base):
    __tablename__ = 'playauto_settings'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    setting_key = Column(Text, nullable=False, unique=True)
    setting_value = Column(Text, nullable=False)
    encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    notes = Column(Text)

    __table_args__ = (
        Index('idx_playauto_settings_key', 'setting_key'),
    )


class PlayautoSyncLog(Base):
    __tablename__ = 'playauto_sync_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sync_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    request_data = Column(Text)
    response_data = Column(Text)
    items_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    error_message = Column(Text)
    execution_time = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=func.current_timestamp())

    __table_args__ = (
        Index('idx_playauto_sync_logs_type', 'sync_type', 'created_at'),
    )


class MarketOrderRaw(Base):
    __tablename__ = 'market_orders_raw'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    playauto_order_id = Column(Text, nullable=False, unique=True)
    market = Column(Text, nullable=False)
    order_number = Column(Text, nullable=False)
    raw_data = Column(Text, nullable=False)
    order_date = Column(DateTime)
    synced_to_local = Column(Boolean, default=False)
    local_order_id = Column(BigInteger, ForeignKey('orders.id', ondelete='SET NULL'))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    local_order = relationship("Order", back_populates="market_order_raw")

    __table_args__ = (
        Index('idx_market_orders_raw_playauto_id', 'playauto_order_id'),
        Index('idx_market_orders_raw_synced', 'synced_to_local', 'created_at'),
    )


# ==========================================
# Notification System
# ==========================================

class WebhookSetting(Base):
    __tablename__ = 'webhook_settings'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    webhook_type = Column(Text, nullable=False, unique=True)
    webhook_url = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    notification_types = Column(Text, default='all')
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    webhook_logs = relationship("WebhookLog", back_populates="webhook_setting")

    __table_args__ = (
        Index('idx_webhook_settings_type', 'webhook_type'),
    )


class WebhookLog(Base):
    __tablename__ = 'webhook_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    webhook_id = Column(BigInteger, ForeignKey('webhook_settings.id', ondelete='SET NULL'))
    notification_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    message = Column(Text)
    error_details = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    webhook_setting = relationship("WebhookSetting", back_populates="webhook_logs")

    __table_args__ = (
        Index('idx_webhook_logs_webhook', 'webhook_id', 'created_at'),
        Index('idx_webhook_logs_type', 'notification_type', 'created_at'),
    )


# ==========================================
# Selling Product Management
# ==========================================

class MySellingProduct(Base):
    __tablename__ = 'my_selling_products'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_name = Column(Text, nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    monitored_product_id = Column(BigInteger, ForeignKey('monitored_products.id', ondelete='SET NULL'))
    sourcing_url = Column(Text)
    sourcing_product_name = Column(Text)
    sourcing_price = Column(Numeric(10, 2))
    sourcing_source = Column(Text)
    detail_page_data = Column(Text)
    category = Column(Text)
    thumbnail_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    notes = Column(Text)

    # Relationships
    monitored_product = relationship("MonitoredProduct", back_populates="selling_products")
    margin_change_logs = relationship("MarginChangeLog", back_populates="selling_product", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_my_selling_products_active', 'is_active', 'created_at'),
        Index('idx_my_selling_products_monitored', 'monitored_product_id'),
    )


class MarginChangeLog(Base):
    __tablename__ = 'margin_change_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    selling_product_id = Column(BigInteger, ForeignKey('my_selling_products.id', ondelete='CASCADE'), nullable=False)
    old_margin = Column(Numeric(10, 2))
    new_margin = Column(Numeric(10, 2), nullable=False)
    old_margin_rate = Column(Numeric(5, 2))
    new_margin_rate = Column(Numeric(5, 2), nullable=False)
    change_reason = Column(Text, nullable=False)
    old_selling_price = Column(Numeric(10, 2))
    new_selling_price = Column(Numeric(10, 2))
    old_sourcing_price = Column(Numeric(10, 2))
    new_sourcing_price = Column(Numeric(10, 2))
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    selling_product = relationship("MySellingProduct", back_populates="margin_change_logs")

    __table_args__ = (
        Index('idx_margin_change_logs_product', 'selling_product_id', 'created_at'),
        Index('idx_margin_change_logs_notification', 'notification_sent', 'created_at'),
    )


# ==========================================
# Inventory Management
# ==========================================

class InventoryAutoLog(Base):
    __tablename__ = 'inventory_auto_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('monitored_products.id', ondelete='CASCADE'), nullable=False)
    action = Column(Text, nullable=False)
    old_status = Column(Text)
    new_status = Column(Text)
    is_active_before = Column(Boolean)
    is_active_after = Column(Boolean)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    product = relationship("MonitoredProduct", back_populates="inventory_logs")

    __table_args__ = (
        Index('idx_inventory_auto_logs_product', 'product_id', 'created_at'),
        Index('idx_inventory_auto_logs_action', 'action', 'created_at'),
    )


# ==========================================
# Category Management
# ==========================================

class Category(Base):
    __tablename__ = 'categories'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    folder_number = Column(Integer, nullable=False, unique=True)
    folder_name = Column(Text, nullable=False)
    level1 = Column(Text, nullable=False)
    level2 = Column(Text, nullable=False)
    level3 = Column(Text, nullable=False)
    level4 = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index('idx_categories_folder_number', 'folder_number'),
        Index('idx_categories_levels', 'level1', 'level2', 'level3', 'level4'),
    )


# ==========================================
# Accounting System
# ==========================================

class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    expense_date = Column(Date, nullable=False)
    category = Column(Text, nullable=False)
    subcategory = Column(Text)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    payment_method = Column(Text)
    receipt_url = Column(Text)
    is_vat_deductible = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index('idx_expenses_date', 'expense_date'),
        Index('idx_expenses_category', 'category'),
    )


class Settlement(Base):
    __tablename__ = 'settlements'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    market = Column(Text, nullable=False)
    settlement_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_sales = Column(Numeric(10, 2))
    commission = Column(Numeric(10, 2))
    shipping_fee = Column(Numeric(10, 2))
    promotion_cost = Column(Numeric(10, 2))
    net_amount = Column(Numeric(10, 2))
    settlement_status = Column(Text, default='pending')
    memo = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index('idx_settlements_market', 'market'),
        Index('idx_settlements_date', 'settlement_date'),
    )


class TaxInfo(Base):
    __tablename__ = 'tax_info'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer)
    total_sales = Column(Numeric(10, 2))
    total_purchases = Column(Numeric(10, 2))
    vat_payable = Column(Numeric(10, 2))
    income_tax_estimate = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index('idx_tax_year_quarter', 'year', 'quarter'),
    )


# ==========================================
# Tracking Upload Scheduler
# ==========================================

class TrackingUploadScheduler(Base):
    __tablename__ = 'tracking_upload_scheduler'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False)
    schedule_time = Column(Text, default='17:00')
    retry_count = Column(Integer, default=3)
    notify_discord = Column(Boolean, default=False)
    notify_slack = Column(Boolean, default=False)
    discord_webhook = Column(Text)
    slack_webhook = Column(Text)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class TrackingUploadJob(Base):
    __tablename__ = 'tracking_upload_jobs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    progress_percent = Column(Numeric(5, 2), default=0)
    error_message = Column(Text)
    details = Column(Text)
    started_at = Column(DateTime, default=func.current_timestamp())
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    upload_details = relationship("TrackingUploadDetail", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_tracking_upload_jobs_status', 'status'),
        Index('idx_tracking_upload_jobs_created_at', 'created_at'),
    )


class TrackingUploadDetail(Base):
    __tablename__ = 'tracking_upload_details'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey('tracking_upload_jobs.id', ondelete='CASCADE'), nullable=False)
    order_id = Column(BigInteger)
    order_no = Column(Text)
    carrier_code = Column(Text)
    tracking_number = Column(Text)
    status = Column(Text, nullable=False)
    retry_attempt = Column(Integer, default=0)
    error_message = Column(Text)
    uploaded_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    job = relationship("TrackingUploadJob", back_populates="upload_details")

    __table_args__ = (
        Index('idx_tracking_upload_details_job_id', 'job_id'),
        Index('idx_tracking_upload_details_status', 'status'),
    )
