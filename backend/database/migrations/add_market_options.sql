-- 마켓별 옵션 컬럼 추가
-- 지마켓/옥션, 쿠팡, 스마트스토어 옵션을 JSON으로 저장

ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS gmk_opts TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS coupang_opts TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS smart_opts TEXT DEFAULT NULL;

COMMENT ON COLUMN my_selling_products.gmk_opts IS '지마켓/옥션 옵션 (JSON 배열, 최대 3개)';
COMMENT ON COLUMN my_selling_products.coupang_opts IS '쿠팡 옵션 (JSON 배열, 최대 3개)';
COMMENT ON COLUMN my_selling_products.smart_opts IS '스마트스토어 옵션 (JSON 배열, 최대 3개)';
