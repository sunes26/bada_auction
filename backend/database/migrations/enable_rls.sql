-- ==========================================
-- Supabase RLS 활성화 마이그레이션
-- ==========================================
-- 이 스크립트를 Supabase SQL Editor에서 실행하세요.
--
-- 이 시스템은 백엔드 API(service_role)를 통해서만 DB에 접근하므로,
-- RLS를 활성화하고 service_role에게 모든 권한을 부여합니다.
-- ==========================================

-- 1. 모든 테이블에 RLS 활성화
ALTER TABLE IF EXISTS public.monitored_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.status_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.auto_order_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.playauto_sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.market_orders_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.margin_change_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.webhook_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.webhook_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.my_selling_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.inventory_auto_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tracking_upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tracking_upload_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sourcing_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.playauto_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tax_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tracking_upload_scheduler ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.category_infocode_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.category_playauto_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.product_marketplace_codes ENABLE ROW LEVEL SECURITY;

-- 2. service_role에게 모든 권한 부여 (백엔드 API용)
-- service_role은 RLS를 우회하므로 정책이 필요 없지만, 명시적으로 설정

-- monitored_products
DROP POLICY IF EXISTS "service_role_all_monitored_products" ON public.monitored_products;
CREATE POLICY "service_role_all_monitored_products" ON public.monitored_products
    FOR ALL USING (auth.role() = 'service_role');

-- price_history
DROP POLICY IF EXISTS "service_role_all_price_history" ON public.price_history;
CREATE POLICY "service_role_all_price_history" ON public.price_history
    FOR ALL USING (auth.role() = 'service_role');

-- status_changes
DROP POLICY IF EXISTS "service_role_all_status_changes" ON public.status_changes;
CREATE POLICY "service_role_all_status_changes" ON public.status_changes
    FOR ALL USING (auth.role() = 'service_role');

-- notifications
DROP POLICY IF EXISTS "service_role_all_notifications" ON public.notifications;
CREATE POLICY "service_role_all_notifications" ON public.notifications
    FOR ALL USING (auth.role() = 'service_role');

-- orders
DROP POLICY IF EXISTS "service_role_all_orders" ON public.orders;
CREATE POLICY "service_role_all_orders" ON public.orders
    FOR ALL USING (auth.role() = 'service_role');

-- order_items
DROP POLICY IF EXISTS "service_role_all_order_items" ON public.order_items;
CREATE POLICY "service_role_all_order_items" ON public.order_items
    FOR ALL USING (auth.role() = 'service_role');

-- auto_order_logs
DROP POLICY IF EXISTS "service_role_all_auto_order_logs" ON public.auto_order_logs;
CREATE POLICY "service_role_all_auto_order_logs" ON public.auto_order_logs
    FOR ALL USING (auth.role() = 'service_role');

-- playauto_sync_logs
DROP POLICY IF EXISTS "service_role_all_playauto_sync_logs" ON public.playauto_sync_logs;
CREATE POLICY "service_role_all_playauto_sync_logs" ON public.playauto_sync_logs
    FOR ALL USING (auth.role() = 'service_role');

-- market_orders_raw
DROP POLICY IF EXISTS "service_role_all_market_orders_raw" ON public.market_orders_raw;
CREATE POLICY "service_role_all_market_orders_raw" ON public.market_orders_raw
    FOR ALL USING (auth.role() = 'service_role');

-- margin_change_logs
DROP POLICY IF EXISTS "service_role_all_margin_change_logs" ON public.margin_change_logs;
CREATE POLICY "service_role_all_margin_change_logs" ON public.margin_change_logs
    FOR ALL USING (auth.role() = 'service_role');

-- webhook_settings
DROP POLICY IF EXISTS "service_role_all_webhook_settings" ON public.webhook_settings;
CREATE POLICY "service_role_all_webhook_settings" ON public.webhook_settings
    FOR ALL USING (auth.role() = 'service_role');

-- webhook_logs
DROP POLICY IF EXISTS "service_role_all_webhook_logs" ON public.webhook_logs;
CREATE POLICY "service_role_all_webhook_logs" ON public.webhook_logs
    FOR ALL USING (auth.role() = 'service_role');

-- my_selling_products
DROP POLICY IF EXISTS "service_role_all_my_selling_products" ON public.my_selling_products;
CREATE POLICY "service_role_all_my_selling_products" ON public.my_selling_products
    FOR ALL USING (auth.role() = 'service_role');

-- inventory_auto_logs
DROP POLICY IF EXISTS "service_role_all_inventory_auto_logs" ON public.inventory_auto_logs;
CREATE POLICY "service_role_all_inventory_auto_logs" ON public.inventory_auto_logs
    FOR ALL USING (auth.role() = 'service_role');

-- tracking_upload_jobs
DROP POLICY IF EXISTS "service_role_all_tracking_upload_jobs" ON public.tracking_upload_jobs;
CREATE POLICY "service_role_all_tracking_upload_jobs" ON public.tracking_upload_jobs
    FOR ALL USING (auth.role() = 'service_role');

-- tracking_upload_details
DROP POLICY IF EXISTS "service_role_all_tracking_upload_details" ON public.tracking_upload_details;
CREATE POLICY "service_role_all_tracking_upload_details" ON public.tracking_upload_details
    FOR ALL USING (auth.role() = 'service_role');

-- sourcing_accounts
DROP POLICY IF EXISTS "service_role_all_sourcing_accounts" ON public.sourcing_accounts;
CREATE POLICY "service_role_all_sourcing_accounts" ON public.sourcing_accounts
    FOR ALL USING (auth.role() = 'service_role');

-- playauto_settings
DROP POLICY IF EXISTS "service_role_all_playauto_settings" ON public.playauto_settings;
CREATE POLICY "service_role_all_playauto_settings" ON public.playauto_settings
    FOR ALL USING (auth.role() = 'service_role');

-- expenses
DROP POLICY IF EXISTS "service_role_all_expenses" ON public.expenses;
CREATE POLICY "service_role_all_expenses" ON public.expenses
    FOR ALL USING (auth.role() = 'service_role');

-- settlements
DROP POLICY IF EXISTS "service_role_all_settlements" ON public.settlements;
CREATE POLICY "service_role_all_settlements" ON public.settlements
    FOR ALL USING (auth.role() = 'service_role');

-- tax_info
DROP POLICY IF EXISTS "service_role_all_tax_info" ON public.tax_info;
CREATE POLICY "service_role_all_tax_info" ON public.tax_info
    FOR ALL USING (auth.role() = 'service_role');

-- tracking_upload_scheduler
DROP POLICY IF EXISTS "service_role_all_tracking_upload_scheduler" ON public.tracking_upload_scheduler;
CREATE POLICY "service_role_all_tracking_upload_scheduler" ON public.tracking_upload_scheduler
    FOR ALL USING (auth.role() = 'service_role');

-- category_infocode_mapping
DROP POLICY IF EXISTS "service_role_all_category_infocode_mapping" ON public.category_infocode_mapping;
CREATE POLICY "service_role_all_category_infocode_mapping" ON public.category_infocode_mapping
    FOR ALL USING (auth.role() = 'service_role');

-- categories
DROP POLICY IF EXISTS "service_role_all_categories" ON public.categories;
CREATE POLICY "service_role_all_categories" ON public.categories
    FOR ALL USING (auth.role() = 'service_role');

-- category_playauto_mapping
DROP POLICY IF EXISTS "service_role_all_category_playauto_mapping" ON public.category_playauto_mapping;
CREATE POLICY "service_role_all_category_playauto_mapping" ON public.category_playauto_mapping
    FOR ALL USING (auth.role() = 'service_role');

-- product_marketplace_codes
DROP POLICY IF EXISTS "service_role_all_product_marketplace_codes" ON public.product_marketplace_codes;
CREATE POLICY "service_role_all_product_marketplace_codes" ON public.product_marketplace_codes
    FOR ALL USING (auth.role() = 'service_role');

-- ==========================================
-- 완료 메시지
-- ==========================================
SELECT 'RLS 활성화 및 정책 설정 완료' AS status;
