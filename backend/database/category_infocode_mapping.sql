-- ==========================================
-- 카테고리별 상품정보제공고시 코드 매핑
-- ==========================================

-- 매핑 테이블 생성
CREATE TABLE IF NOT EXISTS category_infocode_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level1 TEXT NOT NULL,  -- 대분류 (간편식, 음료 등)
    info_code TEXT NOT NULL,  -- Playauto infoCode (ProcessedFood2023, Cosmetic2023 등)
    info_code_name TEXT,  -- infoCode 설명 (가공식품, 화장품 등)
    notes TEXT,  -- 추가 설명
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(level1)  -- level1당 하나의 infoCode만
);

-- 매핑 데이터 삽입
-- 식품류 (가공식품)
INSERT OR REPLACE INTO category_infocode_mapping (level1, info_code, info_code_name, notes)
VALUES
    ('간편식', 'ProcessedFood2023', '가공식품', '즉석밥, 죽, 국/탕/찌개 등'),
    ('음료', 'ProcessedFood2023', '가공식품', '주스, 탄산음료, 식혜 등'),
    ('우유/두유', 'ProcessedFood2023', '가공식품', '우유, 두유, 요구르트 등'),
    ('스낵류', 'ProcessedFood2023', '가공식품', '과자, 초콜릿, 사탕 등'),
    ('신선/냉장품', 'ProcessedFood2023', '가공식품', '냉장/냉동 가공식품'),
    ('쿠킹소스/장류', 'ProcessedFood2023', '가공식품', '소스, 장류, 양념 등'),
    ('커피/차류', 'ProcessedFood2023', '가공식품', '커피, 차, 분말음료 등'),
    ('과일류', 'ProcessedFood2023', '가공식품', '과일 가공품'),
    ('통조림/캔류', 'ProcessedFood2023', '가공식품', '통조림, 캔 식품');

-- 건강기능식품
INSERT OR REPLACE INTO category_infocode_mapping (level1, info_code, info_code_name, notes)
VALUES ('건강기능식품', 'HealthFunctionalFood2023', '건강기능식품', '영양제, 보충제 등');

-- 화장품/생활용품
INSERT OR REPLACE INTO category_infocode_mapping (level1, info_code, info_code_name, notes)
VALUES
    ('뷰티', 'Cosmetic2023', '화장품', '스킨케어, 메이크업 등'),
    ('화장품,생활용품', 'Cosmetic2023', '화장품', '화장품 및 일부 생활용품');

-- 트리거 생성
CREATE TRIGGER IF NOT EXISTS update_category_infocode_mapping_timestamp
AFTER UPDATE ON category_infocode_mapping
FOR EACH ROW
BEGIN
    UPDATE category_infocode_mapping SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_category_infocode_level1 ON category_infocode_mapping(level1);
CREATE INDEX IF NOT EXISTS idx_category_infocode_info_code ON category_infocode_mapping(info_code);
