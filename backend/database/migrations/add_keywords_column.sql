-- 검색 키워드 컬럼 추가 마이그레이션
-- PlayAuto API의 keywords 필드와 연동하여 오픈마켓 검색에 사용되는 키워드 저장
-- keywords 필드는 JSON 배열 형태의 문자열로 저장됨 (최대 40개)

-- SQLite 버전
-- ALTER TABLE my_selling_products ADD COLUMN keywords TEXT;

-- PostgreSQL 버전
ALTER TABLE my_selling_products ADD COLUMN IF NOT EXISTS keywords TEXT;

-- 마이그레이션 확인
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'my_selling_products' AND column_name = 'keywords';
