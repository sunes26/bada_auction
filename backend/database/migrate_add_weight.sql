-- ==========================================
-- 마이그레이션: my_selling_products에 weight, c_sale_cd_coupang 컬럼 추가
-- 쿠팡 전송 시 "개당 중량" 옵션값 및 판매자 관리코드로 사용
-- ==========================================

-- 1. weight 컬럼 추가 (TEXT 타입, 예: "500g", "1kg")
ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS weight TEXT;

-- 2. c_sale_cd_coupang 컬럼 추가 (쿠팡용 판매자 관리코드)
ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS c_sale_cd_coupang TEXT;

-- 3. 확인 쿼리
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'my_selling_products' AND column_name IN ('weight', 'c_sale_cd_coupang');

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: weight, c_sale_cd_coupang columns added to my_selling_products table';
END $$;
