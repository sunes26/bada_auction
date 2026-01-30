-- ==========================================
-- 온백AI 상품 모니터링 시스템
-- PostgreSQL Migration Schema
-- ==========================================

-- ==========================================
-- 모니터링 대상 상품
-- ==========================================
CREATE TABLE IF NOT EXISTS monitored_products (
    id BIGSERIAL PRIMARY KEY,
    product_url TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    source TEXT NOT NULL,  -- 소싱처(구매처) 마켓
    current_price NUMERIC(10,2),
    original_price NUMERIC(10,2),
    current_status TEXT DEFAULT 'available',
    last_checked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_interval INTEGER DEFAULT 15,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- 가격 변동 이력
CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    original_price NUMERIC(10,2),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 상태 변경 이력
CREATE TABLE IF NOT EXISTS status_changes (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 알림 로그
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    notification_type TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_monitored_products_active ON monitored_products(is_active, last_checked_at);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_status_changes_product ON status_changes(product_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(is_read, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_product_type ON notifications(product_id, notification_type, created_at DESC);

-- ==========================================
-- 주문 정보 (마켓에서 수신한 주문)
-- ==========================================
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    order_number TEXT NOT NULL UNIQUE,
    market TEXT NOT NULL,  -- 판매처 마켓
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_address TEXT NOT NULL,
    customer_zipcode TEXT,
    order_status TEXT DEFAULT 'pending',
    total_amount NUMERIC(10,2) NOT NULL,
    total_profit NUMERIC(10,2),
    payment_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);

-- ==========================================
-- 주문 상품 목록
-- ==========================================
CREATE TABLE IF NOT EXISTS order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    monitored_product_id BIGINT,
    product_name TEXT NOT NULL,
    product_url TEXT NOT NULL,
    source TEXT NOT NULL,  -- 소싱처(구매처) 마켓
    quantity INTEGER NOT NULL DEFAULT 1,
    sourcing_price NUMERIC(10,2) NOT NULL,
    selling_price NUMERIC(10,2) NOT NULL,
    profit NUMERIC(10,2),
    rpa_status TEXT DEFAULT 'pending',
    tracking_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (monitored_product_id) REFERENCES monitored_products (id) ON DELETE SET NULL
);

-- RPA 자동 발주 실행 로그
CREATE TABLE IF NOT EXISTS auto_order_logs (
    id BIGSERIAL PRIMARY KEY,
    order_item_id BIGINT NOT NULL,
    source TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    error_details TEXT,
    screenshot_path TEXT,
    execution_time NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_item_id) REFERENCES order_items (id) ON DELETE CASCADE
);

-- 소싱처 계정 정보
CREATE TABLE IF NOT EXISTS sourcing_accounts (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL UNIQUE,
    account_id TEXT NOT NULL,
    account_password TEXT NOT NULL,
    payment_method TEXT,
    payment_info TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 인덱스 생성 (RPA 시스템)
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_market ON orders(market, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_rpa_status ON order_items(rpa_status);
CREATE INDEX IF NOT EXISTS idx_order_items_tracking ON order_items(tracking_number);
CREATE INDEX IF NOT EXISTS idx_auto_order_logs_item ON auto_order_logs(order_item_id, created_at DESC);

-- ==========================================
-- 플레이오토 API 통합 시스템
-- ==========================================

-- 플레이오토 설정 관리
CREATE TABLE IF NOT EXISTS playauto_settings (
    id BIGSERIAL PRIMARY KEY,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 플레이오토 동기화 로그
CREATE TABLE IF NOT EXISTS playauto_sync_logs (
    id BIGSERIAL PRIMARY KEY,
    sync_type TEXT NOT NULL,
    status TEXT NOT NULL,
    request_data TEXT,
    response_data TEXT,
    items_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    error_message TEXT,
    execution_time NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 마켓 주문 원본 데이터
CREATE TABLE IF NOT EXISTS market_orders_raw (
    id BIGSERIAL PRIMARY KEY,
    playauto_order_id TEXT NOT NULL UNIQUE,
    market TEXT NOT NULL,
    order_number TEXT NOT NULL,
    raw_data TEXT NOT NULL,
    order_date TIMESTAMP,
    synced_to_local BOOLEAN DEFAULT FALSE,
    local_order_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (local_order_id) REFERENCES orders (id) ON DELETE SET NULL
);

-- 인덱스 생성 (플레이오토 시스템)
CREATE INDEX IF NOT EXISTS idx_playauto_settings_key ON playauto_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_playauto_sync_logs_type ON playauto_sync_logs(sync_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_orders_raw_playauto_id ON market_orders_raw(playauto_order_id);
CREATE INDEX IF NOT EXISTS idx_market_orders_raw_synced ON market_orders_raw(synced_to_local, created_at DESC);

-- ==========================================
-- Slack/Discord 알림 시스템
-- ==========================================

-- Webhook 설정
CREATE TABLE IF NOT EXISTS webhook_settings (
    id BIGSERIAL PRIMARY KEY,
    webhook_type TEXT NOT NULL UNIQUE,
    webhook_url TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    notification_types TEXT DEFAULT 'all',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook 실행 로그
CREATE TABLE IF NOT EXISTS webhook_logs (
    id BIGSERIAL PRIMARY KEY,
    webhook_id BIGINT,
    notification_type TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    error_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (webhook_id) REFERENCES webhook_settings (id) ON DELETE SET NULL
);

-- ==========================================
-- 내 판매 상품 관리 시스템
-- ==========================================

-- 내가 판매하는 상품 목록
CREATE TABLE IF NOT EXISTS my_selling_products (
    id BIGSERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    selling_price NUMERIC(10,2) NOT NULL,
    monitored_product_id BIGINT,
    sourcing_url TEXT,
    sourcing_product_name TEXT,
    sourcing_price NUMERIC(10,2),
    sourcing_source TEXT,
    detail_page_data TEXT,
    category TEXT,
    thumbnail_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (monitored_product_id) REFERENCES monitored_products (id) ON DELETE SET NULL
);

-- 마진 변동 이력
CREATE TABLE IF NOT EXISTS margin_change_logs (
    id BIGSERIAL PRIMARY KEY,
    selling_product_id BIGINT NOT NULL,
    old_margin NUMERIC(10,2),
    new_margin NUMERIC(10,2) NOT NULL,
    old_margin_rate NUMERIC(5,2),
    new_margin_rate NUMERIC(5,2) NOT NULL,
    change_reason TEXT NOT NULL,
    old_selling_price NUMERIC(10,2),
    new_selling_price NUMERIC(10,2),
    old_sourcing_price NUMERIC(10,2),
    new_sourcing_price NUMERIC(10,2),
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (selling_product_id) REFERENCES my_selling_products (id) ON DELETE CASCADE
);

-- 인덱스 생성 (판매 상품 관리)
CREATE INDEX IF NOT EXISTS idx_my_selling_products_active ON my_selling_products(is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_my_selling_products_monitored ON my_selling_products(monitored_product_id);
CREATE INDEX IF NOT EXISTS idx_margin_change_logs_product ON margin_change_logs(selling_product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_margin_change_logs_notification ON margin_change_logs(notification_sent, created_at DESC);

-- ==========================================
-- 자동 재고 관리 시스템
-- ==========================================

-- 자동 재고 관리 로그
CREATE TABLE IF NOT EXISTS inventory_auto_logs (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    action TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    is_active_before BOOLEAN,
    is_active_after BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 인덱스 생성 (알림 및 재고 시스템)
CREATE INDEX IF NOT EXISTS idx_webhook_settings_type ON webhook_settings(webhook_type);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_webhook ON webhook_logs(webhook_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_type ON webhook_logs(notification_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_auto_logs_product ON inventory_auto_logs(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_auto_logs_action ON inventory_auto_logs(action, created_at DESC);

-- ==========================================
-- 상세페이지 카테고리 관리
-- ==========================================

CREATE TABLE IF NOT EXISTS categories (
    id BIGSERIAL PRIMARY KEY,
    folder_number INTEGER NOT NULL UNIQUE,
    folder_name TEXT NOT NULL,
    level1 TEXT NOT NULL,
    level2 TEXT NOT NULL,
    level3 TEXT NOT NULL,
    level4 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 카테고리 인덱스
CREATE INDEX IF NOT EXISTS idx_categories_folder_number ON categories(folder_number);
CREATE INDEX IF NOT EXISTS idx_categories_levels ON categories(level1, level2, level3, level4);

-- ==========================================
-- 회계 시스템 (Accounting System)
-- ==========================================

-- 지출 관리
CREATE TABLE IF NOT EXISTS expenses (
    id BIGSERIAL PRIMARY KEY,
    expense_date DATE NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    amount NUMERIC(10,2) NOT NULL,
    description TEXT,
    payment_method TEXT,
    receipt_url TEXT,
    is_vat_deductible BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 마켓별 정산 관리
CREATE TABLE IF NOT EXISTS settlements (
    id BIGSERIAL PRIMARY KEY,
    market TEXT NOT NULL,
    settlement_date DATE NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_sales NUMERIC(10,2),
    commission NUMERIC(10,2),
    shipping_fee NUMERIC(10,2),
    promotion_cost NUMERIC(10,2),
    net_amount NUMERIC(10,2),
    settlement_status TEXT DEFAULT 'pending',
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 세금 정보
CREATE TABLE IF NOT EXISTS tax_info (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER,
    total_sales NUMERIC(10,2),
    total_purchases NUMERIC(10,2),
    vat_payable NUMERIC(10,2),
    income_tax_estimate NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 회계 인덱스
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_settlements_market ON settlements(market);
CREATE INDEX IF NOT EXISTS idx_settlements_date ON settlements(settlement_date);
CREATE INDEX IF NOT EXISTS idx_tax_year_quarter ON tax_info(year, quarter);

-- ==========================================
-- 자동 송장 업로드 스케줄러
-- ==========================================

-- 스케줄러 설정
CREATE TABLE IF NOT EXISTS tracking_upload_scheduler (
    id BIGSERIAL PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    schedule_time TEXT DEFAULT '17:00',
    retry_count INTEGER DEFAULT 3,
    notify_discord BOOLEAN DEFAULT FALSE,
    notify_slack BOOLEAN DEFAULT FALSE,
    discord_webhook TEXT,
    slack_webhook TEXT,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기본 설정 삽입
INSERT INTO tracking_upload_scheduler (id, enabled, schedule_time, retry_count)
VALUES (1, FALSE, '17:00', 3)
ON CONFLICT (id) DO NOTHING;

-- 송장 업로드 작업 로그
CREATE TABLE IF NOT EXISTS tracking_upload_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    total_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    progress_percent NUMERIC(5,2) DEFAULT 0,
    error_message TEXT,
    details TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 송장 업로드 상세 로그
CREATE TABLE IF NOT EXISTS tracking_upload_details (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL,
    order_id BIGINT,
    order_no TEXT,
    carrier_code TEXT,
    tracking_number TEXT,
    status TEXT NOT NULL,
    retry_attempt INTEGER DEFAULT 0,
    error_message TEXT,
    uploaded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES tracking_upload_jobs (id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_tracking_upload_jobs_status ON tracking_upload_jobs(status);
CREATE INDEX IF NOT EXISTS idx_tracking_upload_jobs_created_at ON tracking_upload_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tracking_upload_details_job_id ON tracking_upload_details(job_id);
CREATE INDEX IF NOT EXISTS idx_tracking_upload_details_status ON tracking_upload_details(status);

-- ==========================================
-- updated_at 자동 업데이트 트리거 (PostgreSQL)
-- ==========================================

-- 트리거 함수 생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 각 테이블에 트리거 적용
CREATE TRIGGER update_monitored_products_timestamp
    BEFORE UPDATE ON monitored_products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_timestamp
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_order_items_timestamp
    BEFORE UPDATE ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sourcing_accounts_timestamp
    BEFORE UPDATE ON sourcing_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_playauto_settings_timestamp
    BEFORE UPDATE ON playauto_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_orders_raw_timestamp
    BEFORE UPDATE ON market_orders_raw
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhook_settings_timestamp
    BEFORE UPDATE ON webhook_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_my_selling_products_timestamp
    BEFORE UPDATE ON my_selling_products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_timestamp
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_expenses_timestamp
    BEFORE UPDATE ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settlements_timestamp
    BEFORE UPDATE ON settlements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tax_info_timestamp
    BEFORE UPDATE ON tax_info
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tracking_upload_scheduler_timestamp
    BEFORE UPDATE ON tracking_upload_scheduler
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
