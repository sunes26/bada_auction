# 카테고리 코드 수동 매핑 가이드

## 📋 개요

PlayAuto 카테고리 코드를 구 시스템(Standard_category_list.xlsx)에서 신 시스템(category.xlsx)으로 변경하기 위한 가이드입니다.

## 🔄 매핑 프로세스

### 1단계: 매핑 파일 열기

```bash
backend\category_code_mapping.csv
```

Excel에서 열면 다음 컬럼들을 볼 수 있습니다:

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `old_code` | 구 시스템 코드 | 10010100 |
| `old_category_path` | 구 카테고리 경로 | 여성의류 > 가디건 > 라운드/U넥가디건 |
| `new_code` | 신 시스템 코드 (수정 필요) | 6220807 |
| `new_category_path` | 신 카테고리 경로 | 여성의류 > 가디건 > 라운드/U넥가디건 |
| `similarity_score` | 자동 매칭 유사도 | 75.50% |
| `match_status` | 매칭 상태 | high_confidence / medium_confidence / low_confidence / unmapped |

### 2단계: 우선순위 매핑

**우선순위 1: 현재 사용 중인 카테고리**
- 먼저 실제 데이터베이스에서 사용 중인 sol_cate_no부터 매핑
- `python backend/check_current_categories.py` 실행하면 현재 사용 중인 코드 확인 가능

**우선순위 2: 높은 유사도부터**
- `similarity_score`가 높은 것부터 검토
- 70% 이상: 대부분 정확하므로 간단히 확인만
- 50-70%: 꼼꼼히 확인 필요
- 50% 미만: 수동으로 찾아야 함

### 3단계: 매핑 방법

#### 방법 A: Excel에서 직접 찾기

1. `category.xlsx` 파일을 Excel로 열기
2. `old_category_path`와 비슷한 카테고리를 `카테고리명` 컬럼에서 찾기
3. Ctrl+F로 검색하면 빠름
4. 해당 카테고리의 `카테고리코드`를 복사
5. `category_code_mapping.csv`의 `new_code` 컬럼에 붙여넣기

#### 방법 B: 자동 매칭 검증

- `similarity_score`가 높은 것은 이미 자동으로 매칭됨
- `new_category_path` 컬럼을 보고 올바른지만 확인
- 틀렸다면 올바른 코드로 수정

#### 방법 C: 매핑 불가능한 경우

- 신 시스템에 해당 카테고리가 없다면:
  - 가장 비슷한 상위 카테고리로 매핑
  - 또는 "기타" 카테고리로 매핑
  - `new_code` 컬럼을 비워두면 업데이트 시 건너뜀

### 4단계: 매핑 검증

매핑을 완료했다면 검증:

```bash
# Dry run - 실제 업데이트 없이 확인만
python backend/apply_category_mapping.py

# 결과 확인:
# - 매핑 가능한 개수
# - 매핑 불가능한 개수
# - 업데이트 예정 목록
```

### 5단계: 데이터베이스 적용

검증이 완료되면 실제 업데이트:

```bash
# 실제 데이터베이스 업데이트
python backend/apply_category_mapping.py --apply
```

**⚠️ 주의사항:**
- 반드시 dry run으로 먼저 확인
- 데이터베이스 백업 권장
- PostgreSQL 프로덕션에서는 신중히 진행

## 📊 매핑 팁

### 카테고리 경로 이해하기

**구 시스템 특징:**
- 매우 상세한 4단계 계층
- 예: `여성의류 > 가디건 > 라운드/U넥가디건`

**신 시스템 특징:**
- 더 간결한 계층 구조
- 예: `여성의류 > 가디건 > 라운드/U넥가디건`

### 빠른 검색 방법

Excel에서 Ctrl+F를 사용하여:
1. 마지막 단계 카테고리명으로 검색 (가장 구체적)
2. 없으면 상위 카테고리로 검색
3. 여러 개 나오면 전체 경로를 비교

### 일반적인 매핑 규칙

| 구 시스템 | 신 시스템 |
|----------|----------|
| 세부 카테고리 | 상위 카테고리로 통합된 경우가 많음 |
| "기타" 카테고리 | 신 시스템에서는 없는 경우가 많음 |
| "리퍼/반품/전시" | 상위 카테고리로 매핑 |

## 🔍 현재 사용 중인 카테고리 확인

실제로 데이터베이스에 있는 상품들이 사용하는 카테고리를 먼저 매핑하는 것이 효율적입니다.

```bash
# 현재 사용 중인 카테고리 확인
python backend/check_current_categories.py
```

이 스크립트는:
- `selling_products` 테이블의 sol_cate_no
- `category_playauto_mapping` 테이블의 sol_cate_no
- 사용 빈도가 높은 순으로 정렬
- 우선 매핑이 필요한 카테고리 리스트 출력

## 📁 파일 구조

```
backend/
├── category_code_mapping.csv        # 여기를 수정하세요!
├── category_code_mapping.json       # JSON 버전 (자동 생성)
├── apply_category_mapping.py        # 데이터베이스 적용 스크립트
├── check_current_categories.py      # 현재 사용 중인 카테고리 확인
└── CATEGORY_MAPPING_GUIDE.md        # 이 문서

프로젝트 루트/
├── Standard_category_list.xlsx      # 구 시스템 (참고용)
└── category.xlsx                    # 신 시스템 (참고용)
```

## ✅ 체크리스트

매핑 작업을 시작하기 전:

- [ ] `category.xlsx` 파일 확인
- [ ] `Standard_category_list.xlsx` 파일 확인
- [ ] `category_code_mapping.csv` 백업 생성
- [ ] Excel 또는 스프레드시트 프로그램 준비

매핑 작업 중:

- [ ] 현재 사용 중인 카테고리부터 매핑
- [ ] 높은 유사도(70%+) 항목 검증
- [ ] 중간 유사도(50-70%) 항목 수정
- [ ] 낮은 유사도(<50%) 항목 수동 매핑

매핑 완료 후:

- [ ] Dry run으로 검증
- [ ] 매핑 불가능한 항목 처리 방법 결정
- [ ] 데이터베이스 백업
- [ ] 실제 업데이트 적용
- [ ] 업데이트 결과 확인

## 🆘 문제 해결

### Q: 신 시스템에 없는 카테고리는?
A: 가장 비슷한 상위 카테고리로 매핑하거나, new_code를 비워두세요.

### Q: 여러 개의 구 카테고리가 하나의 신 카테고리로?
A: 괜찮습니다. 여러 old_code가 같은 new_code를 가질 수 있습니다.

### Q: 잘못 매핑했다면?
A: CSV 파일을 다시 수정하고 `--apply`를 다시 실행하면 덮어씁니다.

### Q: 일부만 먼저 매핑하고 싶다면?
A: 매핑한 것만 new_code를 채우고, 나머지는 비워두세요. 나중에 추가로 매핑 가능합니다.

## 💡 예시

### 예시 1: 높은 유사도 (검증만 필요)

```csv
old_code,old_category_path,new_code,new_category_path,similarity_score,match_status
10010100,여성의류 > 가디건 > 라운드/U넥가디건,6220807,여성의류 > 가디건 > 라운드/U넥가디건,85.50%,high_confidence
```

→ 경로가 동일하므로 그대로 사용 ✅

### 예시 2: 중간 유사도 (수정 필요)

```csv
old_code,old_category_path,new_code,new_category_path,similarity_score,match_status
23110300,TV/냉장고/세탁기 > 리퍼/반품/전시 > 냉장고/세탁기,6223583,TV/냉장고/세탁기,65.50%,medium_confidence
```

→ "리퍼/반품/전시"는 신 시스템에 없으므로 상위 카테고리로 매핑됨 ✅

### 예시 3: 낮은 유사도 (수동 매핑)

```csv
old_code,old_category_path,new_code,new_category_path,similarity_score,match_status
36190600,음료/과자/가공식품 > 즉석/카레/덮밥 > 즉석밥/레토르트,,UNMAPPED,25.00%,unmapped
```

→ category.xlsx에서 "즉석밥"으로 검색하여 올바른 코드 찾기 🔍
→ 찾은 코드를 new_code에 입력 ✏️

## 📞 추가 지원

질문이나 문제가 있으면:
1. README.md의 트러블슈팅 섹션 확인
2. GitHub Issues 생성
3. 매핑 작업 로그 저장 (향후 참고용)

---

**작업 시작하세요!** 🚀

우선순위 카테고리부터 천천히 매핑하면 됩니다.
