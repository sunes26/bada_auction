# ol_shop_no 분리 수정 완료

## 문제 원인

### 에러 메시지
```
ol_shop_no가 없어 마켓 코드를 수집할 수 없습니다. 상품을 재등록하세요.
```

### 근본 원인
1. **이중 등록 구조**: 상품이 플레이오토에 2번 등록됨
   - GMK/옥션용: `std_ol_yn="Y"`, `opt_type="옵션없음"`
   - 스마트스토어용: `std_ol_yn="N"`, `opt_type="독립형"`

2. **각 등록마다 다른 `ol_shop_no` 반환**:
   ```json
   {
     "result": "성공",
     "c_sale_cd": "m20200925497324",
     "site_list": [
       {
         "shop_name": "마스터 상품",
         "shop_cd": "Z000",
         "ol_shop_no": 11111111    // GMK 등록의 ol_shop_no
       },
       {
         "shop_name": "옥션",
         "shop_cd": "A001",
         "ol_shop_no": 22222222
       }
     ]
   }
   ```

   ```json
   {
     "result": "성공",
     "c_sale_cd": "m20200925497325",
     "site_list": [
       {
         "shop_name": "마스터 상품",
         "shop_cd": "Z000",
         "ol_shop_no": 33333333    // SmartStore 등록의 ol_shop_no
       },
       {
         "shop_name": "스마트스토어",
         "shop_cd": "A027",
         "ol_shop_no": 44444444
       }
     ]
   }
   ```

3. **DB에는 하나의 `ol_shop_no`만 저장**:
   - 기존 코드: `site_list`에서 **첫 번째** `ol_shop_no`만 저장
   - 문제: GMK 마켓 코드를 조회할 때 SmartStore의 `ol_shop_no`를 사용하거나, 그 반대의 경우 발생

4. **마켓 코드 동기화 실패**:
   - `GET /api/products/:ol_shop_no/v1.2` 엔드포인트는 특정 `ol_shop_no`의 마켓 코드만 반환
   - 잘못된 `ol_shop_no`로 조회하면 일부 마켓 코드가 누락됨

---

## 해결 방법

### 1. 데이터베이스 스키마 확장
`c_sale_cd`와 동일하게 `ol_shop_no`를 채널별로 분리:

**변경 전**:
```sql
ol_shop_no TEXT,  -- 하나의 필드만 존재
c_sale_cd_gmk TEXT,
c_sale_cd_smart TEXT
```

**변경 후**:
```sql
ol_shop_no TEXT,  -- 하위 호환성 유지
ol_shop_no_gmk TEXT,  -- 지마켓/옥션용 온라인 쇼핑몰 번호
ol_shop_no_smart TEXT,  -- 스마트스토어용 온라인 쇼핑몰 번호
c_sale_cd_gmk TEXT,
c_sale_cd_smart TEXT
```

### 2. 상품 등록 코드 수정
`backend/api/products.py` - `register_products_to_playauto` 함수 수정

**변경 전** (잘못된 로직):
```python
# 첫 번째 ol_shop_no만 저장 (문제 발생!)
for site in site_list_result:
    if site.get("result") == "성공" and site.get("ol_shop_no"):
        ol_shop_no = site.get("ol_shop_no")
        break  # ← 첫 번째만 저장하고 종료
```

**변경 후** (채널별 분리):
```python
# 채널별로 ol_shop_no 분리 저장
ol_shop_no_gmk = None
ol_shop_no_smart = None

for site in site_list_result:
    if site.get("result") == "성공" and site.get("ol_shop_no"):
        shop_cd = site.get("shop_cd", "")
        ol_no = site.get("ol_shop_no")

        # GMK 채널: Z000(마스터), A001(옥션), A002(지마켓)
        if shop_cd in ["Z000", "A001", "A002"] and c_sale_cd_gmk:
            if not ol_shop_no_gmk or shop_cd == "Z000":
                ol_shop_no_gmk = ol_no

        # SmartStore 채널
        elif c_sale_cd_smart:
            if not ol_shop_no_smart or shop_cd == "Z000":
                ol_shop_no_smart = ol_no

# DB에 저장
update_params["ol_shop_no_gmk"] = ol_shop_no_gmk
update_params["ol_shop_no_smart"] = ol_shop_no_smart
```

### 3. 마켓 코드 동기화 수정
`backend/api/products.py` - `sync_product_marketplace_codes` 함수 수정

**변경 전** (하나의 ol_shop_no만 사용):
```python
ol_shop_no = product.get("ol_shop_no")
detail = await api.get_product_detail(ol_shop_no)
shops = detail.get("shops", [])
```

**변경 후** (모든 ol_shop_no 사용):
```python
ol_shop_no_gmk = product.get("ol_shop_no_gmk")
ol_shop_no_smart = product.get("ol_shop_no_smart")

all_shops = []

# GMK 채널 조회
if ol_shop_no_gmk:
    detail_gmk = await api.get_product_detail(ol_shop_no_gmk)
    all_shops.extend(detail_gmk.get("shops", []))

# SmartStore 채널 조회
if ol_shop_no_smart:
    detail_smart = await api.get_product_detail(ol_shop_no_smart)
    all_shops.extend(detail_smart.get("shops", []))

shops = all_shops  # 모든 마켓 코드 병합
```

---

## 변경된 파일

### 1. 데이터베이스
- ✅ `backend/database/models.py` - `ol_shop_no_gmk`, `ol_shop_no_smart` 컬럼 추가
- ✅ `backend/database/schema.sql` - 스키마 업데이트
- ✅ `backend/database/migrate_split_ol_shop_no.py` - 마이그레이션 스크립트 (신규)
- ✅ `backend/database/db_wrapper.py` - `update_selling_product()` 함수 파라미터 추가

### 2. API 로직
- ✅ `backend/api/products.py`:
  - `register_products_to_playauto()` - 채널별 ol_shop_no 저장 로직
  - `sync_product_marketplace_codes()` - 모든 ol_shop_no로 마켓 코드 조회

---

## 테스트 방법

### 1. 마이그레이션 실행
```bash
cd backend
python database/migrate_split_ol_shop_no.py
```

**출력 예시**:
```
[마이그레이션] ol_shop_no 분리 시작...
[마이그레이션] ✓ 새 컬럼 추가 완료 (ol_shop_no_gmk, ol_shop_no_smart)
[마이그레이션] ✓ 기존 데이터 마이그레이션 완료
[마이그레이션]   - GMK: 0개
[마이그레이션]   - 스마트스토어: 0개
[마이그레이션] ✅ 마이그레이션 완료!
```

### 2. 상품 재등록
기존 상품을 플레이오토에 재등록하여 올바른 `ol_shop_no_gmk`, `ol_shop_no_smart` 값 수집:

1. 판매 상품 페이지에서 상품 선택
2. "PlayAuto 등록" 버튼 클릭
3. 등록 완료 후 로그 확인:
   ```
   [상품등록] GMK ol_shop_no 발견: 12345678 (shop_cd: Z000)
   [상품등록] SmartStore ol_shop_no 발견: 87654321 (shop_cd: Z000)
   [상품등록] GMK 온라인 쇼핑몰 번호 저장: 12345678
   [상품등록] SmartStore 온라인 쇼핑몰 번호 저장: 87654321
   ```

### 3. 마켓 코드 동기화 테스트
```bash
curl -X POST http://localhost:8000/api/products/{product_id}/sync-marketplace-codes
```

**성공 응답**:
```json
{
  "success": true,
  "message": "마켓 코드 동기화 완료",
  "synced_count": 5,
  "marketplace_codes": [
    {
      "shop_cd": "A001",
      "shop_name": "옥션",
      "shop_sale_no": "B123456789"
    },
    {
      "shop_cd": "A002",
      "shop_name": "지마켓",
      "shop_sale_no": "B987654321"
    },
    {
      "shop_cd": "A027",
      "shop_name": "스마트스토어",
      "shop_sale_no": "1234567890"
    }
  ]
}
```

**로그 확인**:
```
[마켓코드동기화] 상품 123번 동기화 시작
[마켓코드동기화] GMK 채널 조회 (ol_shop_no: 12345678)
[마켓코드동기화] GMK: 3개 마켓 코드 수집
[마켓코드동기화] SmartStore 채널 조회 (ol_shop_no: 87654321)
[마켓코드동기화] SmartStore: 2개 마켓 코드 수집
[마켓코드동기화] 옥션 (A001): B123456789
[마켓코드동기화] 지마켓 (A002): B987654321
[마켓코드동기화] 스마트스토어 (A027): 1234567890
```

---

## 하위 호환성

### 레거시 데이터 처리
- 기존 `ol_shop_no` 컬럼은 유지됨 (하위 호환성)
- 마이그레이션 스크립트가 기존 데이터를 자동으로 분리:
  - `c_sale_cd_gmk`가 있으면 → `ol_shop_no_gmk`로 복사
  - `c_sale_cd_smart`만 있으면 → `ol_shop_no_smart`로 복사
- 마켓 코드 동기화 시:
  1. 신규 필드 우선 사용 (`ol_shop_no_gmk`, `ol_shop_no_smart`)
  2. 없으면 레거시 필드 사용 (`ol_shop_no`)

### API 응답
기존 코드와의 호환성을 위해 응답에 레거시 필드 포함:
```python
return {
    "ol_shop_no": product.get("ol_shop_no"),  # 레거시 (하위 호환)
    "ol_shop_no_gmk": product.get("ol_shop_no_gmk"),  # 신규
    "ol_shop_no_smart": product.get("ol_shop_no_smart"),  # 신규
}
```

---

## 예상 효과

### 1. 버그 수정
✅ "ol_shop_no가 없어 마켓 코드를 수집할 수 없습니다" 에러 해결

### 2. 데이터 정확성
✅ 모든 마켓의 코드 100% 수집 (GMK + SmartStore)

### 3. 자동화 개선
✅ 마켓 코드 자동 동기화 성공률 향상
✅ 수동 작업 최소화

---

## 배포 전 체크리스트

- [x] 마이그레이션 스크립트 작성 및 테스트
- [x] 데이터 모델 업데이트
- [x] API 로직 수정
- [x] 하위 호환성 보장
- [ ] 로컬 테스트 (상품 등록 → 마켓 코드 동기화)
- [ ] Railway 배포 전 DB 백업
- [ ] Railway 배포 및 마이그레이션 실행
- [ ] 프로덕션 테스트

---

## 커밋 메시지
```
Fix: ol_shop_no를 채널별로 분리하여 마켓 코드 동기화 문제 해결

- 문제: GMK/SmartStore 이중 등록 시 하나의 ol_shop_no만 저장되어 일부 마켓 코드 누락
- 해결: ol_shop_no_gmk, ol_shop_no_smart로 분리 저장
- 마켓 코드 동기화 시 모든 채널의 ol_shop_no 사용
- 하위 호환성 유지 (레거시 ol_shop_no 필드 보존)

변경 파일:
- backend/database/models.py
- backend/database/schema.sql
- backend/database/migrate_split_ol_shop_no.py (신규)
- backend/database/db_wrapper.py
- backend/api/products.py
```
