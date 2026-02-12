-- 마이그레이션: my_selling_products에 ship_price_type, ship_price 컬럼 추가
-- 상품별 배송비 설정 (선결제/무료)
-- 실행 방법: Supabase SQL Editor에서 실행

-- 1. ship_price_type 컬럼 추가 (기본값: 선결제)
ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS ship_price_type TEXT DEFAULT '선결제';

-- 2. ship_price 컬럼 추가 (기본값: 3000)
ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS ship_price INTEGER DEFAULT 3000;

-- 3. 확인 쿼리
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'my_selling_products' AND column_name IN ('ship_price_type', 'ship_price');

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: ship_price_type, ship_price columns added to my_selling_products table';
END $$;
