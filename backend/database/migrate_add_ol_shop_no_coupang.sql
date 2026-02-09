-- 마이그레이션: my_selling_products에 ol_shop_no_coupang 컬럼 추가
-- 실행 방법: Railway SQL Editor에서 실행

-- ol_shop_no_coupang 컬럼 추가 (쿠팡용 온라인 쇼핑몰 번호)
ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS ol_shop_no_coupang TEXT;

-- 확인
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'my_selling_products' AND column_name = 'ol_shop_no_coupang';

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: ol_shop_no_coupang column added to my_selling_products table';
END $$;
