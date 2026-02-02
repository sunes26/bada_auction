# 카테고리 매핑 시스템 설정 완료

## 개요
PlayAuto API 상품 등록에 필요한 `sol_cate_no` (카테고리 코드) 자동 매핑 시스템이 구축되었습니다.

## 완료된 작업

### 1. 자동 매칭 스크립트 생성
- **파일**: `backend/scripts/auto_match_categories.py`
- **기능**:
  - 우리 시스템의 81개 카테고리를 PlayAuto 표준 카테고리와 자동 매칭
  - 문자열 유사도 알고리즘 사용 (마지막 키워드에 70% 가중치)
  - CSV 파일로 결과 출력하여 수동 검토 가능
- **결과**: `backend/category_mapping_result.csv`

### 2. 데이터베이스 임포트 스크립트
- **파일**: `backend/scripts/import_category_mapping.py`
- **기능**:
  - CSV 파일의 매핑 데이터를 데이터베이스에 입력
  - SQLite/PostgreSQL 자동 감지 및 호환
  - 81개 카테고리 매핑 성공적으로 저장
- **테이블**: `category_playauto_mapping`

### 3. 카테고리 매핑 유틸리티
- **파일**: `backend/utils/category_mapper.py`
- **주요 함수**:
  ```python
  # 카테고리 코드 조회
  code = get_playauto_category_code("간편식 > 면 > 라면 > 라면")
  # 결과: 36060400

  # 상세 정보 조회
  info = get_category_mapping_info("간편식 > 면 > 라면 > 라면")
  # 결과: {
  #   'sol_cate_no': 36060400,
  #   'playauto_category': '음료/과자/가공식품 > 라면/면류 > 컵라면',
  #   'similarity': '72.10%'
  # }

  # 전체 매핑 조회
  all_mappings = get_all_category_mappings()
  ```

## 데이터베이스 스키마

```sql
CREATE TABLE category_playauto_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    our_category TEXT NOT NULL UNIQUE,          -- 우리 시스템 카테고리
    sol_cate_no INTEGER NOT NULL,               -- PlayAuto 카테고리 코드
    playauto_category TEXT,                     -- PlayAuto 카테고리명
    similarity TEXT,                            -- 유사도 (매칭 품질)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 사용 방법

### 상품 등록 시 카테고리 코드 자동 조회

```python
from utils.category_mapper import get_playauto_category_code

# 상품 카테고리에서 PlayAuto 코드 가져오기
product_category = "간편식 > 면 > 라면 > 라면"
sol_cate_no = get_playauto_category_code(product_category)

# PlayAuto API 호출 시 사용
product_data = {
    "goods_name": "신라면",
    "sol_cate_no": sol_cate_no,  # 36060400
    # ... 기타 필드
}
```

## 통계

- **전체 카테고리**: 81개
- **자동 매칭 성공** (70% 이상 유사도): 20개
- **확인 필요** (50-70% 유사도): 20개
- **수동 매핑** (50% 미만): 41개
- **데이터베이스 저장**: 81/81 성공

## 매핑 예시

| 우리 카테고리 | sol_cate_no | PlayAuto 카테고리 | 유사도 |
|--------------|-------------|------------------|--------|
| 간편식 > 면 > 라면 > 라면 | 36060400 | 음료/과자/가공식품 > 라면/면류 > 컵라면 | 72.10% |
| 냉동식 > 피자 > 피자 > 피자 | 36071201 | 음료/과자/가공식품 > 만두/탕/간편조리식 > 피자 > 피자 | 82.90% |
| 생활용품 > 세제 > 세탁세제 > 세탁세제 | 33020302 | 세제/제지/일용잡화 > 세탁세제 > 세탁세제 기타 | 70.10% |

## 다음 단계

### 1. 상품 등록 API 통합
- `backend/api/admin.py`의 상품 등록 엔드포인트에서 `category_mapper` 사용
- 카테고리 필드에서 자동으로 `sol_cate_no` 조회

### 2. 관리자 페이지 기능 추가 (선택)
- 카테고리 매핑 관리 UI
- 매핑 수정/추가 기능
- 유사도 낮은 매핑 재검토

### 3. PlayAuto API 연동
- 상품 등록 시 자동으로 매핑된 `sol_cate_no` 사용
- API 응답 로깅 및 오류 처리

## 파일 구조

```
backend/
├── scripts/
│   ├── auto_match_categories.py      # 카테고리 자동 매칭
│   └── import_category_mapping.py    # DB 임포트
├── utils/
│   └── category_mapper.py            # 매핑 조회 유틸리티
├── database/
│   └── (category_playauto_mapping 테이블)
├── category_mapping_result.csv       # 매핑 결과 (수동 편집 완료)
└── CATEGORY_MAPPING_SETUP.md         # 이 문서
```

## 문제 해결

### 매핑이 없는 경우
```python
code = get_playauto_category_code("존재하지 않는 카테고리")
# 결과: None

# 기본값 사용
sol_cate_no = code if code else 38  # 38 = 기타 재화
```

### 새 카테고리 추가
1. `category_mapping_result.csv` 파일 편집
2. 새 행 추가: `"새 카테고리",카테고리코드,"PlayAuto 카테고리","유사도","상태"`
3. 임포트 스크립트 재실행: `python backend/scripts/import_category_mapping.py`

## 참고 자료

- `Standard_category_list.xlsx`: PlayAuto 표준 카테고리 목록 (13,366개)
- `PLAYAUTO_API_DOCUMENTATION.md`: PlayAuto API 명세
- `PLAYAUTO_PRODUCT_REGISTRATION_ANALYSIS.md`: 상품 등록 요구사항 분석
