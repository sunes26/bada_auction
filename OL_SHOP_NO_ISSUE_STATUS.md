# ol_shop_no 마켓 코드 동기화 이슈 - 현재 상태

## 📋 문제 요약

**에러 메시지**:
```
❌ ol_shop_no가 없어 마켓 코드를 수집할 수 없습니다. 상품을 재등록하세요.
```

**근본 원인**:
- 상품을 PlayAuto에 2번 등록 (GMK/옥션용, 스마트스토어용)
- 각 등록마다 다른 `ol_shop_no`를 반환
- 기존 DB는 하나의 `ol_shop_no`만 저장 → 일부 마켓 코드 누락

---

## ✅ 완료된 작업 (2026-02-05)

### 1. 데이터베이스 스키마 확장
**파일**: `backend/database/models.py`, `backend/database/schema.sql`

**변경 내용**:
```python
# 기존 (문제)
ol_shop_no = Column(Text)  # 하나만 저장

# 변경 후 (해결)
ol_shop_no = Column(Text)  # 하위 호환성
ol_shop_no_gmk = Column(Text)  # 지마켓/옥션용
ol_shop_no_smart = Column(Text)  # 스마트스토어용
```

**커밋**: `3058b41`

---

### 2. 마이그레이션 실행
**파일**: `backend/database/migrate_split_ol_shop_no.py`

**실행 결과**:
```bash
# 로컬에서 실행
✅ python backend/database/migrate_split_ol_shop_no.py
✅ 새 컬럼 추가 완료 (ol_shop_no_gmk, ol_shop_no_smart)

# Railway에서 실행
✅ railway run python backend/database/migrate_split_ol_shop_no.py
✅ PostgreSQL 데이터베이스에 컬럼 추가 완료
```

**확인 방법**:
```sql
-- PostgreSQL에서 확인
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'my_selling_products'
  AND column_name LIKE 'ol_shop_no%';

-- 결과:
-- ol_shop_no       | text
-- ol_shop_no_gmk   | text
-- ol_shop_no_smart | text
```

---

### 3. 상품 등록 로직 수정
**파일**: `backend/api/products.py` (라인 868-941)

**변경 내용**:
```python
# 기존 (문제 있음)
for site in site_list_result:
    if site.get("result") == "성공" and site.get("ol_shop_no"):
        ol_shop_no = site.get("ol_shop_no")
        break  # ❌ 첫 번째만 저장하고 종료

# 변경 후 (해결)
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

**커밋**: `3058b41`

---

### 4. 마켓 코드 동기화 로직 수정
**파일**: `backend/api/products.py` (라인 1232-1292)

**변경 내용**:
```python
# 기존 (문제 있음)
ol_shop_no = product.get("ol_shop_no")
detail = await api.get_product_detail(ol_shop_no)
shops = detail.get("shops", [])

# 변경 후 (해결)
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

**커밋**: `3058b41`

---

### 5. DB Wrapper 함수 업데이트
**파일**: `backend/database/db_wrapper.py` (라인 414-478)

**변경 내용**:
```python
def update_selling_product(
    self,
    product_id: int,
    # ... 기존 파라미터 ...
    ol_shop_no: Optional[str] = None,
    ol_shop_no_gmk: Optional[str] = None,  # ✅ 추가
    ol_shop_no_smart: Optional[str] = None,  # ✅ 추가
    # ... 나머지 파라미터 ...
):
```

**커밋**: `3058b41`

---

### 6. Railway 배포 완료
**상태**: ✅ 정상 작동 중

**확인 결과**:
```
[2026-02-05 13:05:59 +0000] [2] [INFO] Starting gunicorn 23.0.0
[2026-02-05 13:05:59 +0000] [2] [INFO] Listening at: http://0.0.0.0:8080 (2)
[2026-02-05 13:06:06 +0000] [3] [INFO] Application startup complete.
[BACKUP] 백업 스케줄러 시작 완료 (매일 새벽 2시)
[INFO] 데이터베이스 백업 스케줄러 시작 완료
[PLAYAUTO] 스케줄러 시작 완료
[INFO] 플레이오토 스케줄러 시작 완료
```

**최신 커밋**: `2aa4aa0`

---

## ❌ 남아있는 문제

### 문제 1: 기존 상품의 ol_shop_no 데이터 부족

**현재 상황**:
- ✅ 새 코드 배포 완료
- ✅ DB 스키마 확장 완료 (`ol_shop_no_gmk`, `ol_shop_no_smart` 컬럼 존재)
- ❌ **기존 상품들은 여전히 `ol_shop_no_gmk`, `ol_shop_no_smart`가 NULL**

**이유**:
- 마이그레이션 스크립트는 컬럼만 추가함
- 기존 데이터 이동 시도했으나 `c_sale_cd`와 `ol_shop_no`의 매핑 정확도 낮음
- 실제로 기존 상품들은 `ol_shop_no` 자체가 없거나 잘못된 값 저장됨

**증상**:
```
# 마켓 코드 동기화 시도
❌ ol_shop_no가 없어 마켓 코드를 수집할 수 없습니다. 상품을 재등록하세요.
```

**왜 여전히 에러가 나는가?**:
```python
# backend/api/products.py:1232-1240
ol_shop_no_gmk = product.get("ol_shop_no_gmk")  # → None
ol_shop_no_smart = product.get("ol_shop_no_smart")  # → None
ol_shop_no_legacy = product.get("ol_shop_no")  # → None 또는 잘못된 값

# 모두 None이면 에러 발생
if not ol_shop_no_gmk and not ol_shop_no_smart and not ol_shop_no_legacy:
    raise HTTPException(
        status_code=400,
        detail="ol_shop_no가 없어 마켓 코드를 수집할 수 없습니다. 상품을 재등록하세요."
    )
```

---

### 문제 2: 재등록이 필요한 상품 식별 어려움

**현재 상황**:
- 어떤 상품이 재등록이 필요한지 사용자가 알 수 없음
- 모든 상품을 일일이 클릭해서 마켓 코드 동기화를 시도해야 함

**필요한 기능**:
1. 대시보드에서 `ol_shop_no` 상태 표시
2. 일괄 재등록 기능
3. 또는 자동 복구 스크립트

---

## 🔧 해결 방법 (우선순위 순)

### 방법 1: 상품 수동 재등록 (현재 유일한 방법)

**절차**:
1. Railway 프로덕션 사이트 접속
2. "판매 상품" 페이지 이동
3. 문제 있는 상품 선택
4. "PlayAuto 등록" 버튼 클릭
5. 등록 완료 후 로그 확인:
   ```
   [상품등록] GMK ol_shop_no 발견: 12345678 (shop_cd: Z000)
   [상품등록] SmartStore ol_shop_no 발견: 87654321 (shop_cd: Z000)
   [상품등록] GMK 온라인 쇼핑몰 번호 저장: 12345678
   [상품등록] SmartStore 온라인 쇼핑몰 번호 저장: 87654321
   ```
6. "마켓 코드 동기화" 버튼 클릭
7. ✅ 모든 마켓 코드 수집 성공

**단점**:
- 상품이 많으면 시간 소요
- 수동 작업 필요

**장점**:
- 확실한 해결
- 추가 코드 불필요

---

### 방법 2: 자동 복구 스크립트 작성 (추천, 다음 세션에서 구현)

**목표**:
PlayAuto API를 통해 기존 상품의 `ol_shop_no`를 자동으로 채우는 스크립트

**알고리즘**:
```python
# backend/scripts/fix_missing_ol_shop_no.py (신규 파일)

"""
PlayAuto에서 상품 목록을 조회하여 ol_shop_no를 자동으로 채우는 스크립트
"""

async def fix_missing_ol_shop_no():
    # 1. DB에서 ol_shop_no가 없는 상품 조회
    products = db.query(MySellingProduct).filter(
        or_(
            MySellingProduct.ol_shop_no_gmk.is_(None),
            MySellingProduct.ol_shop_no_smart.is_(None)
        ),
        or_(
            MySellingProduct.c_sale_cd_gmk.isnot(None),
            MySellingProduct.c_sale_cd_smart.isnot(None)
        )
    ).all()

    # 2. 각 상품에 대해 PlayAuto API로 검색
    for product in products:
        # 2-1. GMK 상품 검색
        if product.c_sale_cd_gmk and not product.ol_shop_no_gmk:
            # GET /products?search=c_sale_cd&keyword={c_sale_cd_gmk}
            # 또는 GET /products/list API로 전체 조회 후 필터링
            result = await search_playauto_product(product.c_sale_cd_gmk)
            if result:
                product.ol_shop_no_gmk = result['ol_shop_no']
                print(f"✅ {product.product_name} GMK ol_shop_no 복구: {result['ol_shop_no']}")

        # 2-2. SmartStore 상품 검색
        if product.c_sale_cd_smart and not product.ol_shop_no_smart:
            result = await search_playauto_product(product.c_sale_cd_smart)
            if result:
                product.ol_shop_no_smart = result['ol_shop_no']
                print(f"✅ {product.product_name} SmartStore ol_shop_no 복구: {result['ol_shop_no']}")

        db.session.commit()
```

**문제점**:
- ⚠️ PlayAuto API에 `c_sale_cd`로 검색하는 엔드포인트가 있는지 확인 필요
- `product.pdf`, `product_detail.pdf`를 확인했으나 검색 API 문서 없음
- 대안: 전체 상품 목록 조회 후 `c_sale_cd`로 매칭

**API 확인 필요**:
```
GET /products/list?... → 전체 상품 목록 조회 가능한지?
GET /products/search?c_sale_cd={...} → 검색 가능한지?
```

**구현 우선순위**: ⭐⭐⭐ 높음

---

### 방법 3: 일괄 재등록 기능 추가 (다음 세션에서 구현)

**목표**:
UI에서 여러 상품을 선택하여 한 번에 재등록

**구현 파일**:
- `backend/api/products.py` - 일괄 재등록 엔드포인트 추가
- `components/modals/BulkReregisterModal.tsx` - UI 컴포넌트 (신규)

**API 엔드포인트**:
```python
@router.post("/bulk-reregister-to-playauto")
async def bulk_reregister_products(request: dict):
    """
    여러 상품을 한 번에 재등록

    Args:
        request: {
            "product_ids": [1, 2, 3, 4, 5],
            "overwrite": true  # 기존 등록 덮어쓰기
        }
    """
    product_ids = request.get("product_ids", [])
    results = []

    for product_id in product_ids:
        try:
            # 기존 등록 로직 재사용
            result = await register_products_to_playauto({
                "product_ids": [product_id],
                "site_list": [...]  # 설정된 마켓 목록
            })
            results.append({
                "product_id": product_id,
                "success": result.get("success"),
                "ol_shop_no_gmk": result.get("ol_shop_no_gmk"),
                "ol_shop_no_smart": result.get("ol_shop_no_smart")
            })
        except Exception as e:
            results.append({
                "product_id": product_id,
                "success": False,
                "error": str(e)
            })

    return {
        "success": True,
        "results": results,
        "total": len(product_ids),
        "success_count": sum(1 for r in results if r.get("success"))
    }
```

**UI 플로우**:
1. 판매 상품 페이지에서 체크박스로 여러 상품 선택
2. "일괄 재등록" 버튼 클릭
3. 모달 열림 → 진행 상황 표시
4. 완료 후 결과 요약 표시

**구현 우선순위**: ⭐⭐ 중간

---

### 방법 4: 상품 상태 대시보드 추가 (선택 사항)

**목표**:
어떤 상품이 문제인지 한눈에 파악

**UI 변경**:
```tsx
// 판매 상품 테이블에 상태 컬럼 추가
<td>
  {product.ol_shop_no_gmk && product.ol_shop_no_smart ? (
    <Badge color="green">✅ 정상</Badge>
  ) : product.ol_shop_no_gmk || product.ol_shop_no_smart ? (
    <Badge color="yellow">⚠️ 일부 누락</Badge>
  ) : (
    <Badge color="red">❌ 재등록 필요</Badge>
  )}
</td>
```

**필터 기능**:
- "재등록 필요한 상품만 보기" 버튼
- 상태별 카운트 표시 (정상: 50개, 일부 누락: 10개, 재등록 필요: 5개)

**구현 우선순위**: ⭐ 낮음 (nice to have)

---

## 📝 다음 세션 시작 시 해야 할 일

### Step 1: 현재 상태 확인 (5분)
```bash
# 1. Railway 로그 확인
railway logs --tail 50

# 2. DB 스키마 확인 (Railway shell)
railway run psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'my_selling_products' AND column_name LIKE 'ol_shop_no%';"

# 3. 샘플 상품 데이터 확인
railway run psql $DATABASE_URL -c "SELECT id, product_name, ol_shop_no, ol_shop_no_gmk, ol_shop_no_smart FROM my_selling_products LIMIT 5;"
```

**예상 결과**:
```
 id | product_name | ol_shop_no | ol_shop_no_gmk | ol_shop_no_smart
----+--------------+------------+----------------+------------------
  1 | 흰밥         | NULL       | NULL           | NULL
  2 | 현미밥       | NULL       | NULL           | NULL
```

---

### Step 2: PlayAuto API 문서 재확인 (10분)

**확인할 문서**:
- `product.pdf` - 상품 등록 API
- `product_detail.pdf` - 상품 상세 조회 API
- `orders.pdf` - 주문 API (참고용)

**찾아야 할 내용**:
1. 상품 목록 조회 API (`GET /products/list` 또는 유사)
2. 상품 검색 API (`GET /products/search?keyword=...`)
3. 응답에 `c_sale_cd`와 `ol_shop_no` 모두 포함되는지 확인

**발견 시 기록**:
```markdown
# PlayAuto 상품 조회 API

## 엔드포인트
GET /api/products/list/v1.2

## 파라미터
- page: 페이지 번호
- limit: 페이지당 개수
- search_keyword: 검색어 (c_sale_cd 포함 가능한지?)

## 응답
{
  "products": [
    {
      "c_sale_cd": "m20200925497324",
      "ol_shop_no": 12345678,
      "shop_sale_name": "상품명"
    }
  ]
}
```

---

### Step 3-A: API 검색 지원 시 → 자동 복구 스크립트 구현 (1시간)

**파일**: `backend/scripts/fix_missing_ol_shop_no.py` (신규)

**구현 내용**:
1. DB에서 `ol_shop_no_gmk`, `ol_shop_no_smart`가 NULL인 상품 조회
2. `c_sale_cd_gmk`, `c_sale_cd_smart`로 PlayAuto API 검색
3. 검색 결과에서 `ol_shop_no` 추출하여 DB 업데이트
4. 진행 상황 로그 출력

**실행**:
```bash
# 로컬 테스트
cd backend
python scripts/fix_missing_ol_shop_no.py

# Railway 실행
railway run python backend/scripts/fix_missing_ol_shop_no.py
```

---

### Step 3-B: API 검색 미지원 시 → 수동 재등록 안내 (30분)

**문서 작성**: `HOW_TO_REREGISTER_PRODUCTS.md` (신규)

**내용**:
1. 재등록이 필요한 이유 설명
2. 스크린샷 포함한 단계별 가이드
3. 재등록 전 체크리스트 (백업, PlayAuto 설정 확인 등)
4. 문제 발생 시 대응 방법

**UI 개선**:
- 에러 메시지를 더 친절하게 변경
- "재등록 방법 보기" 버튼 추가 (모달 또는 링크)

---

### Step 4: 테스트 및 검증 (30분)

**테스트 시나리오**:
1. ✅ 새 상품 등록 → `ol_shop_no_gmk`, `ol_shop_no_smart` 정상 저장 확인
2. ✅ 재등록한 기존 상품 → 마켓 코드 동기화 성공 확인
3. ✅ Railway 로그에서 "GMK ol_shop_no 발견", "SmartStore ol_shop_no 발견" 메시지 확인

**성공 기준**:
```
# 마켓 코드 동기화 API 호출
POST /api/products/{product_id}/sync-marketplace-codes

# 응답
{
  "success": true,
  "synced_count": 5,
  "marketplace_codes": [
    {"shop_cd": "A001", "shop_sale_no": "B123456789"},  // 옥션
    {"shop_cd": "A002", "shop_sale_no": "B987654321"},  // 지마켓
    {"shop_cd": "A027", "shop_sale_no": "1234567890"}   // 스마트스토어
  ]
}
```

---

## 🔍 디버깅 가이드

### 증상: "ol_shop_no가 없어 마켓 코드를 수집할 수 없습니다"

**확인 순서**:

1. **Railway 배포 확인**
   ```bash
   railway logs --tail 20 | grep -E "(Starting|Application startup)"
   ```
   - ✅ "Application startup complete" 보이면 정상

2. **DB 스키마 확인**
   ```bash
   railway run psql $DATABASE_URL -c "\d my_selling_products" | grep ol_shop_no
   ```
   - ✅ `ol_shop_no`, `ol_shop_no_gmk`, `ol_shop_no_smart` 3개 모두 보여야 함

3. **특정 상품 데이터 확인**
   ```bash
   railway run psql $DATABASE_URL -c "SELECT id, product_name, c_sale_cd_gmk, c_sale_cd_smart, ol_shop_no, ol_shop_no_gmk, ol_shop_no_smart FROM my_selling_products WHERE id = {product_id};"
   ```
   - `ol_shop_no_gmk`와 `ol_shop_no_smart`가 NULL이면 재등록 필요

4. **최신 코드 반영 확인**
   ```bash
   git log --oneline -5
   ```
   - `2aa4aa0` 커밋이 보여야 함

5. **Railway 최신 배포 확인**
   ```bash
   git rev-parse HEAD
   railway status
   ```
   - Railway의 배포 커밋과 로컬 최신 커밋이 일치해야 함

---

## 📚 참고 문서

### 관련 파일
- `OL_SHOP_NO_FIX.md` - 수정 내역 상세 문서
- `ORDER_SYSTEM_VERIFICATION.md` - 주문 시스템 검증 문서 (참고)
- `ORDER_SYSTEM_FIX_PLAN.md` - 주문 시스템 수정 계획 (참고)

### API 문서
- `order.pdf` - 주문 조회 API
- `orders.pdf` - 주문 수집 API
- `product.pdf` - 상품 등록 API
- `product_detail.pdf` - 상품 상세 조회 API
- `playauto_api_upload_document.pdf` - 상품 등록 API (전체)

### 코드 위치
- **상품 등록**: `backend/api/products.py:692-941`
- **마켓 코드 동기화**: `backend/api/products.py:1213-1310`
- **DB 모델**: `backend/database/models.py:332-336`
- **마이그레이션**: `backend/database/migrate_split_ol_shop_no.py`

---

## 💡 핵심 요약

### 현재 상태
- ✅ 코드 수정 완료 및 배포
- ✅ DB 스키마 확장 완료
- ❌ **기존 상품 데이터 미해결** ← 여기가 문제!

### 왜 아직 에러가 나는가?
**기존 상품들의 `ol_shop_no_gmk`, `ol_shop_no_smart`가 NULL이기 때문**

### 해결 방법
1. 상품 재등록 (수동) ← 현재 유일한 방법
2. 자동 복구 스크립트 (구현 필요) ← 다음 세션에서 우선 작업
3. 일괄 재등록 UI (선택 사항)

### 다음 세션 시작
1. PlayAuto API 문서에서 상품 검색/목록 조회 API 찾기
2. 찾으면 → 자동 복구 스크립트 작성
3. 못 찾으면 → 수동 재등록 가이드 + UI 개선

---

**작성일**: 2026-02-05
**최종 커밋**: `2aa4aa0` (backup scheduler indentation fix)
**Railway 배포 상태**: ✅ 정상 작동 중
**남은 작업**: 기존 상품의 `ol_shop_no` 데이터 복구
