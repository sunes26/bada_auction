-- 상품 모니터링 시스템 DB 스키마

-- ==========================================
-- 모니터링 대상 상품
-- ==========================================
-- 소싱처(구매처)의 상품을 모니터링하는 테이블
-- source 필드: 소싱처 마켓 이름 ('traders', 'ssg', '11st', 'gmarket' 등)
CREATE TABLE IF NOT EXISTS monitored_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_url TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    source TEXT NOT NULL,  -- 소싱처(구매처) 마켓: 'traders', 'ssg', '11st', 'gmarket' 등
    current_price REAL,
    original_price REAL,
    current_status TEXT DEFAULT 'available',  -- 'available', 'out_of_stock', 'discontinued', 'unavailable'
    last_checked_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    check_interval INTEGER DEFAULT 15,  -- 체크 주기 (분)
    is_active BOOLEAN DEFAULT TRUE,  -- 모니터링 활성화 여부
    notes TEXT  -- 사용자 메모
);

-- 가격 변동 이력
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    price REAL NOT NULL,
    original_price REAL,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 상태 변경 이력
CREATE TABLE IF NOT EXISTS status_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,  -- 추가 상세 정보 (JSON)
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 알림 로그
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,  -- 'price_change', 'status_change', 'error'
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_monitored_products_active ON monitored_products(is_active, last_checked_at);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_status_changes_product ON status_changes(product_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(is_read, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_product_type ON notifications(product_id, notification_type, created_at DESC);  -- 복합 조회 최적화

-- ========================================
-- RPA 자동 발주 시스템
-- ========================================

-- ==========================================
-- 주문 정보 (마켓에서 수신한 주문)
-- ==========================================
-- 판매 마켓에서 들어온 주문을 관리하는 테이블
-- market 필드: 판매처 마켓 이름 ('coupang', 'naver', '11st', 'gmarket' 등)
--
-- ⚠️ 필드명 차이 주의:
-- - monitored_products.source: 소싱처(구매처) 마켓
-- - orders.market: 판매처 마켓
-- 이 두 필드는 의미가 다릅니다. source는 우리가 상품을 구매하는 곳,
-- market은 고객이 우리 상품을 구매하는 곳입니다.
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,  -- 마켓 주문번호
    market TEXT NOT NULL,  -- 판매처(판매 마켓): 'coupang', 'naver', '11st', 'gmarket' 등
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_address TEXT NOT NULL,
    customer_zipcode TEXT,
    order_status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed', 'cancelled'
    total_amount REAL NOT NULL,
    total_profit REAL,  -- 예상 순이익
    payment_method TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,  -- RPA 완료 시각
    notes TEXT
);

-- ==========================================
-- 주문 상품 목록
-- ==========================================
-- 각 주문에 포함된 상품 정보
-- source 필드: 소싱처(구매처) 마켓 - monitored_products.source와 동일한 의미
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    monitored_product_id INTEGER,  -- 모니터링 상품 ID (있는 경우)
    product_name TEXT NOT NULL,
    product_url TEXT NOT NULL,  -- 소싱처 URL
    source TEXT NOT NULL,  -- 소싱처(구매처) 마켓: 'ssg', 'traders', '11st', 'gmarket' 등
    quantity INTEGER NOT NULL DEFAULT 1,
    sourcing_price REAL NOT NULL,  -- 소싱가(구매가)
    selling_price REAL NOT NULL,  -- 판매가
    profit REAL,  -- 예상 이익 (selling_price - sourcing_price) * quantity
    rpa_status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    tracking_number TEXT,  -- 송장번호
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (monitored_product_id) REFERENCES monitored_products (id) ON DELETE SET NULL
);

-- RPA 자동 발주 실행 로그
CREATE TABLE IF NOT EXISTS auto_order_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id INTEGER NOT NULL,
    source TEXT NOT NULL,  -- 소싱처
    action TEXT NOT NULL,  -- 'login', 'add_to_cart', 'checkout', 'payment', 'extract_tracking' 등
    status TEXT NOT NULL,  -- 'success', 'failed'
    message TEXT,
    error_details TEXT,  -- 에러 상세 정보 (JSON)
    screenshot_path TEXT,  -- 스크린샷 경로 (디버깅용)
    execution_time REAL,  -- 실행 시간 (초)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_item_id) REFERENCES order_items (id) ON DELETE CASCADE
);

-- 소싱처 계정 정보 (암호화 저장 권장)
CREATE TABLE IF NOT EXISTS sourcing_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL UNIQUE,  -- 'ssg', 'traders', '11st', 'gmarket', 'smartstore'
    account_id TEXT NOT NULL,  -- 로그인 ID
    account_password TEXT NOT NULL,  -- 로그인 비밀번호 (암호화 필요!)
    payment_method TEXT,  -- 'card', 'account' 등
    payment_info TEXT,  -- 결제 정보 (암호화 필요!)
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 인덱스 생성 (RPA 시스템)
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_market ON orders(market, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);  -- 주문번호 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_rpa_status ON order_items(rpa_status);
CREATE INDEX IF NOT EXISTS idx_order_items_tracking ON order_items(tracking_number);  -- 송장번호 조회 최적화
CREATE INDEX IF NOT EXISTS idx_auto_order_logs_item ON auto_order_logs(order_item_id, created_at DESC);

-- ========================================
-- 플레이오토 API 통합 시스템
-- ========================================

-- 플레이오토 설정 관리
CREATE TABLE IF NOT EXISTS playauto_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 플레이오토 동기화 로그
CREATE TABLE IF NOT EXISTS playauto_sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,  -- 'order_fetch', 'tracking_upload', 'product_sync'
    status TEXT NOT NULL,  -- 'success', 'failed', 'partial'
    request_data TEXT,
    response_data TEXT,
    items_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    error_message TEXT,
    execution_time REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 마켓 주문 원본 데이터
CREATE TABLE IF NOT EXISTS market_orders_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playauto_order_id TEXT NOT NULL UNIQUE,
    market TEXT NOT NULL,
    order_number TEXT NOT NULL,
    raw_data TEXT NOT NULL,  -- JSON
    order_date DATETIME,
    synced_to_local BOOLEAN DEFAULT FALSE,
    local_order_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (local_order_id) REFERENCES orders (id) ON DELETE SET NULL
);

-- 인덱스 생성 (플레이오토 시스템)
CREATE INDEX IF NOT EXISTS idx_playauto_settings_key ON playauto_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_playauto_sync_logs_type ON playauto_sync_logs(sync_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_orders_raw_playauto_id ON market_orders_raw(playauto_order_id);
CREATE INDEX IF NOT EXISTS idx_market_orders_raw_synced ON market_orders_raw(synced_to_local, created_at DESC);

-- ========================================
-- Slack/Discord 알림 시스템
-- ========================================

-- Webhook 설정
CREATE TABLE IF NOT EXISTS webhook_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webhook_type TEXT NOT NULL UNIQUE,  -- 'slack' or 'discord'
    webhook_url TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    notification_types TEXT DEFAULT 'all',  -- JSON array: ['margin_alert', 'rpa', 'order_sync', 'inventory']
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Webhook 실행 로그
CREATE TABLE IF NOT EXISTS webhook_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webhook_id INTEGER,
    notification_type TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'success', 'failed'
    message TEXT,
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (webhook_id) REFERENCES webhook_settings (id) ON DELETE SET NULL
);

-- ========================================
-- 내 판매 상품 관리 시스템
-- ========================================

-- 내가 판매하는 상품 목록
CREATE TABLE IF NOT EXISTS my_selling_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    selling_price REAL NOT NULL,  -- 내 판매가
    monitored_product_id INTEGER,  -- 연결된 모니터링 상품 (소싱처)
    sourcing_url TEXT,  -- 소싱처 URL
    sourcing_product_name TEXT,  -- 소싱처 상품명
    sourcing_price REAL,  -- 소싱가
    sourcing_source TEXT,  -- 소싱처 마켓 (11ST, GMARKET 등)
    detail_page_data TEXT,  -- 상세페이지 JSON 데이터
    category TEXT,
    thumbnail_url TEXT,
    original_thumbnail_url TEXT,  -- 원본 썸네일 URL (리사이즈 전)
    sol_cate_no INTEGER,  -- PlayAuto 카테고리 코드
    playauto_product_no TEXT,  -- PlayAuto 상품 등록 번호 (c_sale_cd)
    ol_shop_no TEXT,  -- 온라인 쇼핑몰 번호 (PlayAuto 등록 시)
    is_active BOOLEAN DEFAULT TRUE,  -- 판매 중 여부
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (monitored_product_id) REFERENCES monitored_products (id) ON DELETE SET NULL
);

-- 마진 변동 이력
CREATE TABLE IF NOT EXISTS margin_change_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    selling_product_id INTEGER NOT NULL,
    old_margin REAL,  -- 이전 마진 (금액)
    new_margin REAL NOT NULL,  -- 새 마진 (금액)
    old_margin_rate REAL,  -- 이전 마진율 (%)
    new_margin_rate REAL NOT NULL,  -- 새 마진율 (%)
    change_reason TEXT NOT NULL,  -- 'selling_price_changed', 'sourcing_price_changed'
    old_selling_price REAL,
    new_selling_price REAL,
    old_sourcing_price REAL,
    new_sourcing_price REAL,
    notification_sent BOOLEAN DEFAULT FALSE,  -- 알림 발송 여부
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (selling_product_id) REFERENCES my_selling_products (id) ON DELETE CASCADE
);

-- 인덱스 생성 (판매 상품 관리)
CREATE INDEX IF NOT EXISTS idx_my_selling_products_active ON my_selling_products(is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_my_selling_products_monitored ON my_selling_products(monitored_product_id);
CREATE INDEX IF NOT EXISTS idx_margin_change_logs_product ON margin_change_logs(selling_product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_margin_change_logs_notification ON margin_change_logs(notification_sent, created_at DESC);

-- ========================================
-- 자동 재고 관리 시스템
-- ========================================

-- 자동 재고 관리 로그
CREATE TABLE IF NOT EXISTS inventory_auto_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- 'auto_disable', 'restock_detected', 'auto_enable'
    old_status TEXT,
    new_status TEXT,
    is_active_before BOOLEAN,
    is_active_after BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES monitored_products (id) ON DELETE CASCADE
);

-- 인덱스 생성 (알림 및 재고 시스템)
CREATE INDEX IF NOT EXISTS idx_webhook_settings_type ON webhook_settings(webhook_type);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_webhook ON webhook_logs(webhook_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_type ON webhook_logs(notification_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_auto_logs_product ON inventory_auto_logs(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_auto_logs_action ON inventory_auto_logs(action, created_at DESC);

-- 상세페이지 카테고리 관리
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_number INTEGER NOT NULL UNIQUE,  -- 폴더 번호 (1~149 등)
    folder_name TEXT NOT NULL,  -- 폴더명 (예: 1_흰밥, 100_식혜)
    level1 TEXT NOT NULL,  -- 대분류 (예: 간편식, 음료, 우유/두유)
    level2 TEXT NOT NULL,  -- 중분류 (예: 밥류, 전통음료, 우유)
    level3 TEXT NOT NULL,  -- 소분류 (예: 즉석밥, 식혜, 딸기)
    level4 TEXT NOT NULL,  -- 제품종류 (예: 흰밥, 식혜, 딸기) - 실제 표시명
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 카테고리 인덱스
CREATE INDEX IF NOT EXISTS idx_categories_folder_number ON categories(folder_number);
CREATE INDEX IF NOT EXISTS idx_categories_levels ON categories(level1, level2, level3, level4);

-- ==========================================
-- 회계 시스템 (Accounting System)
-- ==========================================

-- 지출 관리
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date DATE NOT NULL,              -- 지출일자
    category TEXT NOT NULL,                  -- 카테고리 (광고비, 배송비, 포장재, 기타)
    subcategory TEXT,                        -- 세부분류 (네이버광고, 쿠팡광고 등)
    amount DECIMAL(10,2) NOT NULL,           -- 금액
    description TEXT,                        -- 설명
    payment_method TEXT,                     -- 결제수단 (카드, 현금, 계좌이체)
    receipt_url TEXT,                        -- 영수증 이미지/파일 URL
    is_vat_deductible BOOLEAN DEFAULT 0,     -- 부가세 공제 가능 여부
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 마켓별 정산 관리
CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market TEXT NOT NULL,                    -- 마켓명 (쿠팡, 네이버 등)
    settlement_date DATE NOT NULL,           -- 정산일
    period_start DATE NOT NULL,              -- 정산 기간 시작
    period_end DATE NOT NULL,                -- 정산 기간 종료
    total_sales DECIMAL(10,2),               -- 총 판매액
    commission DECIMAL(10,2),                -- 수수료
    shipping_fee DECIMAL(10,2),              -- 배송비
    promotion_cost DECIMAL(10,2),            -- 프로모션 비용
    net_amount DECIMAL(10,2),                -- 실 정산액
    settlement_status TEXT DEFAULT 'pending', -- 상태 (pending, completed)
    memo TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 세금 정보
CREATE TABLE IF NOT EXISTS tax_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    quarter INTEGER,                         -- 분기 (1~4, 부가세용)
    total_sales DECIMAL(10,2),               -- 총 매출
    total_purchases DECIMAL(10,2),           -- 총 매입
    vat_payable DECIMAL(10,2),               -- 납부할 부가세
    income_tax_estimate DECIMAL(10,2),       -- 예상 소득세
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 회계 인덱스
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_settlements_market ON settlements(market);
CREATE INDEX IF NOT EXISTS idx_settlements_date ON settlements(settlement_date);
CREATE INDEX IF NOT EXISTS idx_tax_year_quarter ON tax_info(year, quarter);

-- ==========================================
-- updated_at 자동 업데이트 트리거
-- ==========================================

-- monitored_products 트리거
CREATE TRIGGER IF NOT EXISTS update_monitored_products_timestamp
AFTER UPDATE ON monitored_products
FOR EACH ROW
BEGIN
    UPDATE monitored_products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- orders 트리거
CREATE TRIGGER IF NOT EXISTS update_orders_timestamp
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    UPDATE orders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- order_items 트리거
CREATE TRIGGER IF NOT EXISTS update_order_items_timestamp
AFTER UPDATE ON order_items
FOR EACH ROW
BEGIN
    UPDATE order_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- sourcing_accounts 트리거
CREATE TRIGGER IF NOT EXISTS update_sourcing_accounts_timestamp
AFTER UPDATE ON sourcing_accounts
FOR EACH ROW
BEGIN
    UPDATE sourcing_accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- playauto_settings 트리거
CREATE TRIGGER IF NOT EXISTS update_playauto_settings_timestamp
AFTER UPDATE ON playauto_settings
FOR EACH ROW
BEGIN
    UPDATE playauto_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- market_orders_raw 트리거
CREATE TRIGGER IF NOT EXISTS update_market_orders_raw_timestamp
AFTER UPDATE ON market_orders_raw
FOR EACH ROW
BEGIN
    UPDATE market_orders_raw SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- webhook_settings 트리거
CREATE TRIGGER IF NOT EXISTS update_webhook_settings_timestamp
AFTER UPDATE ON webhook_settings
FOR EACH ROW
BEGIN
    UPDATE webhook_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- my_selling_products 트리거
CREATE TRIGGER IF NOT EXISTS update_my_selling_products_timestamp
AFTER UPDATE ON my_selling_products
FOR EACH ROW
BEGIN
    UPDATE my_selling_products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- categories 트리거
CREATE TRIGGER IF NOT EXISTS update_categories_timestamp
AFTER UPDATE ON categories
FOR EACH ROW
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- expenses 트리거
CREATE TRIGGER IF NOT EXISTS update_expenses_timestamp
AFTER UPDATE ON expenses
FOR EACH ROW
BEGIN
    UPDATE expenses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- settlements 트리거
CREATE TRIGGER IF NOT EXISTS update_settlements_timestamp
AFTER UPDATE ON settlements
FOR EACH ROW
BEGIN
    UPDATE settlements SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- tax_info 트리거
CREATE TRIGGER IF NOT EXISTS update_tax_info_timestamp
AFTER UPDATE ON tax_info
FOR EACH ROW
BEGIN
    UPDATE tax_info SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ==========================================
-- 자동 송장 업로드 스케줄러
-- ==========================================

-- 스케줄러 설정
CREATE TABLE IF NOT EXISTS tracking_upload_scheduler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enabled BOOLEAN DEFAULT FALSE,  -- 스케줄러 활성화 여부
    schedule_time TEXT DEFAULT '17:00',  -- 실행 시간 (HH:MM)
    retry_count INTEGER DEFAULT 3,  -- 재시도 횟수
    notify_discord BOOLEAN DEFAULT FALSE,  -- Discord 알림
    notify_slack BOOLEAN DEFAULT FALSE,  -- Slack 알림
    discord_webhook TEXT,  -- Discord 웹훅 URL
    slack_webhook TEXT,  -- Slack 웹훅 URL
    last_run_at DATETIME,  -- 마지막 실행 시각
    next_run_at DATETIME,  -- 다음 실행 예정 시각
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 기본 설정 삽입
INSERT OR IGNORE INTO tracking_upload_scheduler (id, enabled, schedule_time, retry_count)
VALUES (1, FALSE, '17:00', 3);

-- 송장 업로드 작업 로그
CREATE TABLE IF NOT EXISTS tracking_upload_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,  -- 'scheduled', 'manual'
    status TEXT NOT NULL,  -- 'running', 'completed', 'failed'
    total_count INTEGER DEFAULT 0,  -- 총 업로드 건수
    success_count INTEGER DEFAULT 0,  -- 성공 건수
    failed_count INTEGER DEFAULT 0,  -- 실패 건수
    retry_count INTEGER DEFAULT 0,  -- 재시도 횟수
    progress_percent REAL DEFAULT 0,  -- 진행률 (0-100)
    error_message TEXT,  -- 에러 메시지
    details TEXT,  -- 상세 정보 (JSON)
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 송장 업로드 상세 로그 (개별 주문별)
CREATE TABLE IF NOT EXISTS tracking_upload_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,  -- tracking_upload_jobs FK
    order_id INTEGER,  -- 로컬 주문 ID
    order_no TEXT,  -- 주문 번호
    carrier_code TEXT,  -- 택배사 코드
    tracking_number TEXT,  -- 송장 번호
    status TEXT NOT NULL,  -- 'pending', 'success', 'failed'
    retry_attempt INTEGER DEFAULT 0,  -- 재시도 횟수
    error_message TEXT,  -- 에러 메시지
    uploaded_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES tracking_upload_jobs (id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_tracking_upload_jobs_status ON tracking_upload_jobs(status);
CREATE INDEX IF NOT EXISTS idx_tracking_upload_jobs_created_at ON tracking_upload_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tracking_upload_details_job_id ON tracking_upload_details(job_id);
CREATE INDEX IF NOT EXISTS idx_tracking_upload_details_status ON tracking_upload_details(status);

-- 트리거
CREATE TRIGGER IF NOT EXISTS update_tracking_upload_scheduler_timestamp
AFTER UPDATE ON tracking_upload_scheduler
FOR EACH ROW
BEGIN
    UPDATE tracking_upload_scheduler SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ==========================================
-- PlayAuto 카테고리 매핑
-- ==========================================
-- 우리 시스템 카테고리를 PlayAuto 카테고리 코드(sol_cate_no)로 매핑
CREATE TABLE IF NOT EXISTS category_playauto_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    our_category TEXT NOT NULL UNIQUE,
    sol_cate_no INTEGER NOT NULL,
    playauto_category TEXT,
    similarity TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_category_playauto_mapping_our_category
ON category_playauto_mapping(our_category);

