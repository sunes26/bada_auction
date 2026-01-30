# 플레이오토 상품 등록 API 구현 분석 보고서

**작성일**: 2026-01-30
**분석 대상**: Playauto Product Registration API v1.2
**구현 파일**:
- `backend/playauto/product_registration.py` (build_product_data_from_db)
- `backend/api/products.py` (register_products_to_playauto)

---

## 목차
1. [개요](#개요)
2. [필수 필드 분석](#필수-필드-분석)
3. [선택 필드 분석](#선택-필드-분석)
4. [옵션 구조 분석](#옵션-구조-분석)
5. [이미지 처리 분석](#이미지-처리-분석)
6. [상품정보제공고시 분석](#상품정보제공고시-분석)
7. [종합 평가](#종합-평가)
8. [개선 제안사항](#개선-제안사항)

---

## 개요

플레이오토 상품 등록 API (v1.2)는 여러 쇼핑몰에 상품을 자동 등록하는 기능을 제공합니다.
현재 구현은 `build_product_data_from_db()` 함수에서 DB 상품 정보를 플레이오토 API 형식으로 변환합니다.

**API 엔드포인트**: `POST https://openapi.playauto.io/api/products/add/v1.2`

---

## 필수 필드 분석

### ✅ 정상 구현된 필수 필드

| 필드명 | API 요구사항 | 현재 구현 | 상태 |
|--------|-------------|----------|------|
| `c_sale_cd` | String (필수) | `"__AUTO__"` (자동생성) | ✅ 정상 |
| `sol_cate_no` | Number (필수) | `1` (기본값) | ⚠️ 하드코딩 |
| `shop_sale_name` | String (필수, 최대 100Byte) | `product_name` | ✅ 정상 |
| `sale_price` | Number (필수, 10원 단위) | `selling_price` (int 변환) | ✅ 정상 |
| `sale_cnt_limit` | Number (필수) | `999` (고정값) | ⚠️ 하드코딩 |
| `site_list` | Object[] (필수) | 파라미터로 전달받음 | ✅ 정상 |
| `opt_type` | String (필수) | `"옵션없음"` | ⚠️ 고정값 |
| `tax_type` | String (필수) | `"과세"` | ⚠️ 고정값 |
| `ship_price_type` | String (필수) | `"무료"` | ⚠️ 고정값 |
| `detail_desc` | String (필수) | `detail_page_data` 또는 기본 HTML | ✅ 정상 |
| `madein` | Object (필수) | `{"madein_no": 1, "multi_yn": false}` | ⚠️ 고정값 |
| `prod_info` | Object[] (필수) | infoCode "38" (기타 재화) | ⚠️ 범용 코드 |

### ⚠️ 개선이 필요한 필수 필드

#### 1. `sol_cate_no` (카테고리 코드)
```python
# 현재: 하드코딩
"sol_cate_no": product.get("sol_cate_no") or 1

# 문제점:
# - 기본값 1은 임의의 값
# - 카테고리 매핑 로직 부재
# - 상품별 적절한 카테고리 미지정
```

**개선 방안**:
- DB에 `sol_cate_no` 필드 추가
- 카테고리 매핑 테이블 구축
- 플레이오토 카테고리 조회 API 활용

#### 2. `sale_cnt_limit` (판매수량)
```python
# 현재: 고정값
"sale_cnt_limit": 999

# 문제점:
# - 모든 상품이 999개로 고정
# - 실제 재고 수량과 무관
```

**개선 방안**:
- DB에 재고 필드 추가 (`stock_count`)
- 실시간 재고 연동 기능 구현

#### 3. `opt_type` (옵션 구분)
```python
# 현재: 고정값
"opt_type": "옵션없음"
"opts": []

# 문제점:
# - 옵션 있는 상품 등록 불가
# - "조합형", "독립형" 옵션 미지원
```

**개선 방안**:
- 옵션 데이터 모델 설계 (DB 스키마)
- 옵션 타입별 변환 로직 구현
- 옵션 UI 개발 (프론트엔드)

#### 4. `tax_type` (과세여부)
```python
# 현재: 고정값
"tax_type": "과세"

# 문제점:
# - 면세 상품 처리 불가
# - 영세, 비과세 상품 처리 불가
```

**개선 방안**:
- DB에 `tax_type` 필드 추가
- 상품 등록 시 과세 유형 선택 기능

#### 5. `ship_price_type` (배송방법)
```python
# 현재: 고정값
"ship_price_type": "무료"
"ship_price": 0

# 문제점:
# - 유료 배송 상품 처리 불가
# - 착불 배송 처리 불가
```

**개선 방안**:
- DB에 배송 정보 필드 추가
- 템플릿별 기본 배송 설정 기능

#### 6. `madein` (원산지)
```python
# 현재: 고정값
"madein": {
    "madein_no": 1,  # 국내 (고정)
    "multi_yn": False
}

# 문제점:
# - 모든 상품이 국내산으로 고정
# - 수입 상품 처리 불가
```

**개선 방안**:
- DB에 원산지 정보 필드 추가
- 플레이오토 원산지 조회 API 활용
- 복수 원산지 지원

---

## 선택 필드 분석

### ✅ 정상 구현된 선택 필드

| 필드명 | 현재 구현 | 상태 |
|--------|----------|------|
| `supply_price` | `sourcing_price` | ✅ 정상 |
| `cost_price` | `sourcing_price` | ✅ 정상 |
| `street_price` | `selling_price` | ✅ 정상 |

### ❌ 누락된 선택 필드

| 필드명 | API 설명 | 누락 영향도 | 우선순위 |
|--------|---------|-----------|---------|
| `adult_yn` | 미성년자 구매여부 | 중 | 중 |
| `brand` | 브랜드 | 낮음 | 낮음 |
| `model` | 모델명 | 낮음 | 낮음 |
| `maker` | 제조사 | 낮음 | 낮음 |
| `keywords` | 키워드 (최대 40개) | 중 | 중 |
| `ship_price` | 배송비 | 높음 | 높음 |
| `sale_img2~11` | 추가 이미지 (10개) | 높음 | 높음 |
| `made_date` | 제조일자 | 낮음 | 낮음 |
| `expire_date` | 유효일자 | 중 | 중 |
| `gift_name` | 사은품 | 낮음 | 낮음 |
| `global_barcode` | UPC/EAN 코드 | 낮음 | 낮음 |
| `barcode` | 바코드 | 낮음 | 낮음 |
| `hscd` | HS코드 | 낮음 | 낮음 |
| `prod_weight` | 상품 무게 | 중 | 중 |
| `certs` | 인증 정보 | 높음 | 높음 |
| `add_desc_info` | 29CM 전용 상세설명 이미지 | 낮음 | 낮음 |

### 🔧 개선이 필요한 필드 상세

#### 1. `adult_yn` (성인용 상품 여부)
```python
# 현재 구현
"adult_yn": False  # 하드코딩

# 개선 방안
# - DB에 adult_yn 필드 추가
# - 상품 등록 시 체크박스로 선택
```

#### 2. `keywords` (검색 키워드)
```python
# 현재 구현
"keywords": []  # 빈 배열

# 개선 방안
# - DB에 keywords JSON 필드 추가
# - AI 기반 자동 키워드 생성
# - 수동 키워드 입력 UI
```

**중요도**: 검색 노출에 영향을 미치므로 중요

#### 3. `sale_img2~11` (추가 이미지)
```python
# 현재 구현
"sale_img1": thumbnail_url  # 대표 이미지만

# 누락된 필드
# sale_img2, sale_img3, ..., sale_img11 (총 10개)

# 개선 방안
# - DB에 이미지 테이블 생성 (1:N 관계)
# - 이미지 다중 업로드 기능
# - 이미지 순서 관리
```

**중요도**: 상품 상세 정보 제공에 매우 중요

#### 4. `certs` (인증 정보)
```python
# 현재: 누락

# 필요한 인증 유형 (예시)
# - KC 인증 (생활용품, 전기용품, 어린이제품)
# - 방송통신기자재 인증
# - HACCP, GAP (식품)
# - 건강기능식품 광고사전심의
```

**중요도**: 특정 카테고리 상품은 필수 (법적 요구사항)

---

## 옵션 구조 분석

### 📋 API 요구사항

플레이오토는 3가지 옵션 타입을 지원합니다:

1. **옵션없음**: 단일 상품
2. **조합형**: 색상 × 사이즈 등 조합 (예: 빨강-L, 빨강-S, 파랑-L, 파랑-S)
3. **독립형**: 옵션명과 옵션값이 독립적 (예: 색상-빨강, 색상-파랑, 사이즈-L, 사이즈-S)

### ❌ 현재 구현 상태

```python
# 옵션 없음으로 고정
"opt_type": "옵션없음"
"opts": []
```

**문제점**:
- 옵션이 있는 상품 등록 불가
- 의류, 신발, 전자제품 등 대부분의 상품은 옵션 필요

### 🔧 옵션 구현 로드맵

#### Phase 1: 데이터베이스 설계
```sql
-- 옵션 테이블
CREATE TABLE product_options (
    id INTEGER PRIMARY KEY,
    selling_product_id INTEGER,
    opt_type TEXT,  -- '옵션없음', '조합형', '독립형'
    FOREIGN KEY (selling_product_id) REFERENCES my_selling_products(id)
);

-- 옵션 상세 테이블
CREATE TABLE product_option_items (
    id INTEGER PRIMARY KEY,
    option_id INTEGER,
    opt_sort1 TEXT,       -- 옵션명1 (예: 색상)
    opt_sort2 TEXT,       -- 옵션명2 (예: 사이즈)
    opt_sort3 TEXT,       -- 옵션명3
    opt_sort1_desc TEXT,  -- 옵션값1 (예: 빨강)
    opt_sort2_desc TEXT,  -- 옵션값2 (예: Large)
    opt_sort3_desc TEXT,  -- 옵션값3
    sku_cd TEXT,          -- SKU 코드
    pack_unit INTEGER,    -- 출고 수량
    add_price INTEGER,    -- 추가 금액
    stock_cnt INTEGER,    -- 재고 수량
    weight REAL,          -- 무게
    status TEXT,          -- '정상', '품절'
    FOREIGN KEY (option_id) REFERENCES product_options(id)
);

-- 추가구매 옵션 테이블
CREATE TABLE product_add_options (
    id INTEGER PRIMARY KEY,
    selling_product_id INTEGER,
    opt_sort TEXT,        -- 추가 항목명
    opt_sort_desc TEXT,   -- 추가 옵션명
    price INTEGER,        -- 추가 금액
    stock_cnt INTEGER,    -- 재고
    sku_cd TEXT,
    pack_unit INTEGER,
    weight REAL,
    status TEXT,
    FOREIGN KEY (selling_product_id) REFERENCES my_selling_products(id)
);
```

#### Phase 2: 백엔드 로직 구현
```python
def build_product_options(product_id: int) -> Dict:
    """옵션 정보 조회 및 변환"""
    db = get_db()

    # 옵션 타입 조회
    option = db.get_product_option(product_id)

    if not option or option['opt_type'] == '옵션없음':
        return {
            "opt_type": "옵션없음",
            "opts": []
        }

    # 옵션 아이템 조회
    option_items = db.get_product_option_items(option['id'])

    # 플레이오토 형식으로 변환
    opts = []
    for item in option_items:
        opts.append({
            "opt_sort1": item['opt_sort1'],
            "opt_sort2": item.get('opt_sort2', ''),
            "opt_sort3": item.get('opt_sort3', ''),
            "opt_sort1_desc": item['opt_sort1_desc'],
            "opt_sort2_desc": item.get('opt_sort2_desc', ''),
            "opt_sort3_desc": item.get('opt_sort3_desc', ''),
            "sku_cd": item.get('sku_cd', ''),
            "pack_unit": item.get('pack_unit', 1),
            "add_price": item.get('add_price', 0),
            "stock_cnt": item['stock_cnt'],
            "weight": item.get('weight', 0),
            "status": item.get('status', '정상')
        })

    return {
        "opt_type": option['opt_type'],
        "opts": opts
    }
```

#### Phase 3: 프론트엔드 UI
- 옵션 타입 선택 (라디오 버튼)
- 조합형 옵션 입력 (동적 폼)
- 독립형 옵션 입력 (테이블)
- 재고/가격 일괄 설정 기능
- 옵션 프리뷰 기능

---

## 이미지 처리 분석

### ✅ 현재 구현

```python
# 대표 이미지 (sale_img1)
thumbnail_url = product.get("original_thumbnail_url") or product.get("thumbnail_url") or ""

# // 로 시작하는 URL은 https: 추가
if thumbnail_url.startswith("//"):
    thumbnail_url = f"https:{thumbnail_url}"

# 로컬 경로 처리
if thumbnail_url and thumbnail_url.startswith("/static"):
    logger.warning(f"[플레이오토] 썸네일이 로컬 경로입니다. 플레이오토가 접근할 수 없습니다: {thumbnail_url}")
    server_url = os.getenv("SERVER_URL", "http://localhost:8000")
    thumbnail_url = f"{server_url}{thumbnail_url}"
```

**장점**:
- 외부 URL 우선 사용 (original_thumbnail_url)
- URL 프로토콜 자동 보정
- 로컬 경로 감지 및 경고

**문제점**:
- localhost URL은 플레이오토에서 접근 불가
- 추가 이미지 (sale_img2~11) 미지원

### 🔧 개선 방안

#### 1. 이미지 호스팅 전략
```python
# 옵션 1: CDN 업로드
# - AWS S3, Cloudflare R2 등에 이미지 업로드
# - 공개 URL 생성

# 옵션 2: 임시 공개 URL
# - ngrok, Cloudflare Tunnel 등 활용
# - 개발/테스트용

# 옵션 3: 외부 이미지 재사용
# - 소싱처 원본 이미지 URL 직접 사용
# - 저작권 주의
```

#### 2. 다중 이미지 지원
```python
def build_product_images(product: Dict) -> Dict:
    """상품 이미지 목록 생성"""
    images = {}

    # 대표 이미지
    images['sale_img1'] = get_public_url(product.get('thumbnail_url'))

    # 추가 이미지 (DB에서 조회)
    additional_images = db.get_product_images(product['id'])
    for i, img in enumerate(additional_images[:10], start=2):
        images[f'sale_img{i}'] = get_public_url(img['url'])

    return images

def get_public_url(local_path: str) -> str:
    """로컬 경로를 공개 URL로 변환"""
    if not local_path:
        return ""

    # 이미 외부 URL이면 그대로 반환
    if local_path.startswith('http'):
        return local_path

    # S3 업로드 및 URL 반환
    s3_url = upload_to_s3(local_path)
    return s3_url
```

---

## 상품정보제공고시 분석

### 📋 API 요구사항

```python
"prod_info": [
    {
        "infoCode": "38",  # 상품 분류 코드
        "infoDetail": {    # Key-Value 형식
            "제품명": "...",
            "제조자/수입자": "...",
            "원산지": "...",
            "제조일자": "...",
            "품질보증기준": "...",
            "A/S책임자와 전화번호": "..."
        },
        "is_desc_referred": False  # 일괄 [상세설명참조] 적용 여부
    }
]
```

### ✅ 현재 구현

```python
"prod_info": [
    {
        "infoCode": "38",  # 기타 재화 (범용)
        "infoDetail": {
            "제품명": product.get("product_name", ""),
            "제조자/수입자": "상세페이지 참조",
            "원산지": "상세페이지 참조",
            "제조일자": "상세페이지 참조",
            "품질보증기준": "상세페이지 참조",
            "A/S책임자와 전화번호": "상세페이지 참조"
        }
    }
]
```

**장점**:
- 기본 구조 정상 구현
- "상세페이지 참조"로 최소 요구사항 충족

**문제점**:
- infoCode "38" (기타 재화)로 고정
- 카테고리별 적절한 infoCode 미사용
- 실제 정보 입력 불가

### 🔧 infoCode 매핑 테이블

| infoCode | 카테고리 | 필수 정보 항목 |
|----------|---------|---------------|
| 01 | 식품 | 제품명, 내용량, 제조일자, 유통기한, 원재료, 영양성분, 알레르기 유발물질 |
| 22 | 가공식품 | 제품명, 내용량, 제조일자, 유통기한, 원재료, 영양성분 |
| 19 | 화장품 | 용량, 제품 주요 사양, 사용기한, 사용방법, 화장품제조업자 |
| Wear2023 | 의류/패션잡화 | 소재, 색상, 치수, 제조자, 제조국, 취급시 주의사항 |
| Shoes2023 | 신발 | 소재, 색상, 치수, 제조자, 제조국, 품질보증기준 |
| 38 | 기타 재화 | 제품명, 제조자/수입자, 원산지, 제조일자, 품질보증기준, A/S |

### 🔧 개선 방안

#### 1. 카테고리별 infoCode 매핑
```python
INFO_CODE_MAPPING = {
    "식품": "01",
    "가공식품": "22",
    "화장품": "19",
    "의류": "Wear2023",
    "신발": "Shoes2023",
    "가전제품": "16",
    # ... 더 많은 매핑
}

def get_info_code(category: str) -> str:
    """카테고리에 맞는 infoCode 반환"""
    return INFO_CODE_MAPPING.get(category, "38")
```

#### 2. infoDetail 자동 생성
```python
def build_prod_info(product: Dict) -> List[Dict]:
    """상품정보제공고시 생성"""
    category = product.get('category', '')
    info_code = get_info_code(category)

    # 카테고리별 템플릿
    if info_code == "Wear2023":
        return [{
            "infoCode": "Wear2023",
            "infoDetail": {
                "material": product.get('material', '상세페이지 참조'),
                "color": product.get('color', '상세페이지 참조'),
                "size": product.get('size', '상세페이지 참조'),
                "manufacturer": product.get('manufacturer', '상세페이지 참조'),
                "made_in": product.get('made_in', '상세페이지 참조'),
                "caution": "상세페이지 참조",
                "release": product.get('release_date', '상세페이지 참조'),
                "warranty": "상세페이지 참조",
                "customer_service": "상세페이지 참조"
            }
        }]

    # 기타 재화 (기본)
    return [{
        "infoCode": "38",
        "infoDetail": {
            "제품명": product.get('product_name', ''),
            "제조자/수입자": "상세페이지 참조",
            "원산지": "상세페이지 참조",
            "제조일자": "상세페이지 참조",
            "품질보증기준": "상세페이지 참조",
            "A/S책임자와 전화번호": "상세페이지 참조"
        }
    }]
```

#### 3. 일괄 처리 옵션 활용
```python
"prod_info": [
    {
        "infoCode": "38",
        "infoDetail": {},
        "is_desc_referred": True  # 모든 항목을 [상세설명참조]로 처리
    }
]
```

---

## 종합 평가

### 📊 구현 완성도

| 구분 | 구현률 | 평가 |
|------|--------|------|
| 필수 필드 | 85% | ⚠️ 대부분 구현되었으나 하드코딩 많음 |
| 선택 필드 | 20% | ❌ 대부분 누락 |
| 옵션 구조 | 0% | ❌ 미구현 (옵션없음만 지원) |
| 이미지 처리 | 40% | ⚠️ 대표 이미지만 지원 |
| 상품정보고시 | 60% | ⚠️ 최소 요구사항만 충족 |
| **전체** | **45%** | ⚠️ 기본 등록은 가능하나 고급 기능 부족 |

### ✅ 잘 구현된 부분

1. **기본 상품 등록 플로우**
   - API 호출 구조 정상
   - 에러 처리 적절
   - 로깅 충분

2. **이미지 URL 처리**
   - 외부 URL 우선 사용
   - 프로토콜 자동 보정
   - 로컬 경로 감지

3. **가격 정보**
   - 판매가, 공급가, 원가 모두 전송
   - int 변환 처리

4. **상품정보제공고시**
   - 기본 구조 정상
   - 최소 요구사항 충족

### ❌ 개선이 필요한 부분

1. **하드코딩된 값들**
   - 카테고리 번호: 1 (고정)
   - 판매수량: 999 (고정)
   - 옵션 타입: 옵션없음 (고정)
   - 과세 유형: 과세 (고정)
   - 배송 방법: 무료 (고정)
   - 원산지: 국내 (고정)

2. **미구현 기능**
   - 옵션 있는 상품 등록
   - 추가 이미지 등록
   - 인증 정보 등록
   - 키워드 설정

3. **데이터베이스 스키마**
   - 옵션 테이블 부재
   - 이미지 테이블 부재
   - 인증 정보 테이블 부재

---

## 개선 제안사항

### 🎯 우선순위 1 (긴급 - 1주일 내)

#### 1. 카테고리 매핑 시스템 구축
```python
# DB 테이블
CREATE TABLE playauto_category_mapping (
    id INTEGER PRIMARY KEY,
    our_category TEXT,      -- 우리 카테고리
    sol_cate_no INTEGER,    -- 플레이오토 카테고리 번호
    info_code TEXT          -- 상품정보고시 코드
);

# 사용 예시
category_map = db.get_category_mapping(product['category'])
sol_cate_no = category_map['sol_cate_no']
```

**효과**: 적절한 카테고리로 상품 등록, 검색 노출 개선

#### 2. 이미지 호스팅 설정
```python
# AWS S3 또는 Cloudflare R2 설정
# 환경변수 추가
AWS_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# 이미지 업로드 함수
def upload_to_s3(local_path: str) -> str:
    """이미지를 S3에 업로드하고 공개 URL 반환"""
    pass
```

**효과**: 플레이오토가 이미지 접근 가능, 상품 등록 성공률 향상

#### 3. 동적 필드 설정
```python
# DB 스키마 확장
ALTER TABLE my_selling_products ADD COLUMN tax_type TEXT DEFAULT '과세';
ALTER TABLE my_selling_products ADD COLUMN ship_price_type TEXT DEFAULT '무료';
ALTER TABLE my_selling_products ADD COLUMN ship_price INTEGER DEFAULT 0;
ALTER TABLE my_selling_products ADD COLUMN sale_cnt_limit INTEGER DEFAULT 999;
ALTER TABLE my_selling_products ADD COLUMN madein_no INTEGER DEFAULT 1;
```

**효과**: 하드코딩 제거, 상품별 유연한 설정

### 🎯 우선순위 2 (중요 - 1개월 내)

#### 4. 옵션 시스템 구현
- 데이터베이스 스키마 설계
- 옵션 입력 UI 개발
- 옵션 데이터 변환 로직

**효과**: 의류, 신발 등 옵션 있는 상품 등록 가능

#### 5. 다중 이미지 지원
- 이미지 테이블 생성
- 이미지 업로드 UI (최대 11개)
- sale_img1~11 자동 생성

**효과**: 상품 정보 풍부화, 구매 전환율 향상

#### 6. 상품정보제공고시 개선
- 카테고리별 infoCode 자동 매핑
- infoDetail 입력 폼 제공
- 템플릿 저장 기능

**효과**: 법적 요구사항 완벽 충족, 상품 등록 승인률 향상

### 🎯 우선순위 3 (보조 - 2개월 내)

#### 7. 인증 정보 시스템
```sql
CREATE TABLE product_certifications (
    id INTEGER PRIMARY KEY,
    selling_product_id INTEGER,
    cert_cd TEXT,           -- cert_01 ~ cert_46
    cert_exc_type TEXT,     -- kc_01, kc_02, kc_03
    cert_ministry TEXT,     -- 인증 기관
    cert_no TEXT,           -- 인증 번호
    cert_model TEXT,        -- 인증 모델
    cert_cname TEXT,        -- 인증 상호
    cert_date DATE,         -- 인증일
    cert_expire_date DATE,  -- 인증 만료일
    FOREIGN KEY (selling_product_id) REFERENCES my_selling_products(id)
);
```

**효과**: KC 인증 등 필수 인증 상품 등록 가능

#### 8. 키워드 자동 생성
```python
async def generate_keywords(product: Dict) -> List[str]:
    """AI 기반 키워드 자동 생성"""
    prompt = f"""
    상품명: {product['product_name']}
    카테고리: {product['category']}

    이 상품에 적합한 검색 키워드 20개를 생성해주세요.
    """

    # OpenAI API 호출
    keywords = await call_openai(prompt)
    return keywords[:40]  # 최대 40개
```

**효과**: SEO 최적화, 검색 노출 증가

#### 9. 배송 템플릿 시스템
- 배송 템플릿 CRUD
- 템플릿별 기본 배송비 설정
- 지역별 차등 배송비 (미래 기능)

**효과**: 배송 정보 관리 효율화

### 🎯 우선순위 4 (선택 - 3개월 이후)

#### 10. 고급 필드 지원
- 바코드/UPC/EAN
- HS코드
- 제조일자/유효일자
- 사은품
- 29CM 전용 이미지

**효과**: 특수 요구사항 대응

---

## 코드 개선 예시

### Before (현재 코드)
```python
def build_product_data_from_db(product: Dict, site_list: List[Dict]) -> Dict:
    return {
        "c_sale_cd": product.get("c_sale_cd") or "__AUTO__",
        "sol_cate_no": product.get("sol_cate_no") or 1,  # 하드코딩
        "shop_sale_name": product.get("product_name"),
        "adult_yn": False,  # 하드코딩
        "sale_price": int(product.get("selling_price", 0)),
        "sale_cnt_limit": 999,  # 하드코딩
        "opt_type": "옵션없음",  # 하드코딩
        "tax_type": "과세",  # 하드코딩
        "ship_price_type": "무료",  # 하드코딩
        "madein": {
            "madein_no": 1,  # 하드코딩
            "multi_yn": False
        },
        # ...
    }
```

### After (개선 코드)
```python
def build_product_data_from_db(product: Dict, site_list: List[Dict]) -> Dict:
    """
    DB 상품 정보를 플레이오토 API 형식으로 변환

    개선사항:
    - 하드코딩 제거
    - 카테고리 자동 매핑
    - 옵션 지원
    - 다중 이미지 지원
    - 동적 상품정보고시
    """
    db = get_db()

    # 카테고리 매핑
    category_map = db.get_category_mapping(product.get('category'))
    sol_cate_no = category_map['sol_cate_no'] if category_map else 1

    # 옵션 정보
    options = build_product_options(product['id'])

    # 이미지 정보
    images = build_product_images(product)

    # 상품정보제공고시
    prod_info = build_prod_info(product)

    return {
        # 기본 정보
        "c_sale_cd": product.get("c_sale_cd") or "__AUTO__",
        "sol_cate_no": sol_cate_no,
        "shop_sale_name": product.get("product_name"),
        "adult_yn": product.get("adult_yn", False),
        "sale_price": int(product.get("selling_price", 0)),
        "sale_cnt_limit": product.get("sale_cnt_limit", 999),
        "site_list": site_list,

        # 옵션 정보 (동적)
        "opt_type": options['opt_type'],
        "opts": options['opts'],

        # 상세 정보
        "tax_type": product.get("tax_type", "과세"),
        "ship_price_type": product.get("ship_price_type", "무료"),
        "ship_price": product.get("ship_price", 0),

        # 원산지 정보 (동적)
        "madein": {
            "madein_no": product.get("madein_no", 1),
            "multi_yn": product.get("madein_multi_yn", False),
            "madein_etc": product.get("madein_etc", "")
        },

        # 이미지 정보 (다중)
        **images,

        # 상품정보제공고시 (동적)
        "prod_info": prod_info,

        # 키워드 (있으면)
        "keywords": product.get("keywords", []),

        # 인증 정보 (있으면)
        "certs": build_certifications(product['id']),

        # 기타
        "detail_desc": product.get("detail_page_data") or f"<p>{product.get('product_name')}</p>",
        "brand": product.get("brand", ""),
        "model": product.get("model", ""),
        "maker": product.get("maker", ""),
        "supply_price": int(product.get("sourcing_price", 0)),
        "cost_price": int(product.get("sourcing_price", 0)),
        "street_price": int(product.get("selling_price", 0)),
    }
```

---

## 결론

### 📝 요약

현재 플레이오토 상품 등록 구현은 **기본적인 상품 등록은 가능**하지만, 다음과 같은 한계가 있습니다:

1. **옵션 없는 상품만** 등록 가능 (의류, 신발 등 제한)
2. **하드코딩된 값**이 많아 유연성 부족
3. **이미지 1개만** 등록 가능 (추가 이미지 미지원)
4. **범용 상품정보고시**만 사용 (카테고리별 최적화 부족)

### 🎯 핵심 개선 과제

#### 즉시 개선 (1주일)
1. ✅ 카테고리 매핑 시스템
2. ✅ 이미지 호스팅 설정
3. ✅ 동적 필드 설정 (DB 스키마 확장)

#### 단기 개선 (1개월)
4. ✅ 옵션 시스템 구현
5. ✅ 다중 이미지 지원
6. ✅ 상품정보제공고시 개선

#### 중장기 개선 (2~3개월)
7. 인증 정보 시스템
8. AI 키워드 자동 생성
9. 배송 템플릿 시스템

### 💡 최종 권장사항

**Phase 1 완성** 후 실제 상품 등록 테스트를 진행하고, 플레이오토 API 응답을 기반으로 추가 개선사항을 도출하는 것을 권장합니다.

특히 **옵션 시스템**은 대부분의 상품에 필수이므로, 우선순위를 높여 진행하는 것이 좋습니다.

---

**보고서 작성**: Claude Code
**작성일**: 2026-01-30
**문서 버전**: 1.0
