-- 성능 최적화 인덱스 추가 마이그레이션
-- 실행 일시: 2026-02-14
-- 작성자: Claude Sonnet 4.5

-- 모니터링 상품 인덱스
CREATE INDEX IF NOT EXISTS idx_monitored_products_source ON monitored_products(source);

-- 주문 인덱스
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- 판매 상품 인덱스
CREATE INDEX IF NOT EXISTS idx_my_selling_products_active_updated ON my_selling_products(is_active, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_my_selling_products_sourcing_url ON my_selling_products(sourcing_url);
CREATE INDEX IF NOT EXISTS idx_my_selling_products_playauto_no ON my_selling_products(playauto_product_no);

-- 인덱스 생성 확인
SELECT
    tablename,
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY
    tablename, indexname;
