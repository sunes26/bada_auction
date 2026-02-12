-- 마이그레이션: my_selling_products에 target_margin_rate 컬럼 추가
-- 상품별 개별 마진율 저장 (수동으로 가격 변경 시 해당 마진율 기억)
-- 실행 방법: Railway SQL Editor에서 실행

-- 1. target_margin_rate 컬럼 추가 (NUMERIC(5,2) 타입, 예: 30.00, 45.50)
-- NULL인 경우 시스템 기본값 30% 적용
ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS target_margin_rate NUMERIC(5, 2);

-- 2. 확인 쿼리
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'my_selling_products' AND column_name = 'target_margin_rate';

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: target_margin_rate column added to my_selling_products table';
END $$;
