# 마켓별 상품번호 자동 동기화 시스템

## 개요

상품을 PlayAuto에 등록하고 각 마켓(옥션, 쿠팡, 스마트스토어 등)에 전송하면, 마켓별로 다른 `shop_sale_no`가 부여됩니다. 이 시스템은 자동으로 이 정보를 수집하고 저장하여 주문이 들어왔을 때 자동으로 상품을 매칭합니다.

## 구조

### 1. 데이터베이스 스키마

**product_marketplace_codes 테이블**
```sql
CREATE TABLE product_marketplace_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,        -- my_selling_products.id
    shop_cd TEXT NOT NULL,              -- 마켓 코드 (A001=옥션, A006=쿠팡 등)
    shop_sale_no TEXT,                  -- 마켓별 상품번호
    transmitted_at DATETIME,            -- 전송 일시
    last_checked_at DATETIME,           -- 마지막 확인 일시
    UNIQUE(product_id, shop_cd)         -- 상품+마켓 조합 중복 방지
);
```

### 2. 저장 예시

**상품 정보**
```
상품 ID: 100
상품명: "무선 블루투스 이어폰"
ol_shop_no: "12345678901234567890"  (PlayAuto 내부 ID)
```

**마켓별 코드**
```
product_id=100, shop_cd="A001", shop_sale_no="B123456789"      (옥션)
product_id=100, shop_cd="A006", shop_sale_no="7891234567"      (쿠팡)
product_id=100, shop_cd="A112", shop_sale_no="2024567890"      (스마트스토어)
```

### 3. 주문 매칭

주문 데이터:
```json
{
  "shop_cd": "A006",           // 쿠팡
  "shop_sale_no": "7891234567",
  "shop_ord_no": "ORDER-001",
  "to_name": "홍길동"
}
```

매칭 로직:
```sql
SELECT p.*
FROM my_selling_products p
JOIN product_marketplace_codes pmc ON p.id = pmc.product_id
WHERE pmc.shop_cd = 'A006'
  AND pmc.shop_sale_no = '7891234567'
```

→ 자동으로 상품 ID 100 ("무선 블루투스 이어폰")과 매칭!

---

## 자동 동기화

### 스케줄러

**1시간마다 자동 실행**
```python
# backend/playauto/scheduler.py
scheduler.add_job(
    sync_marketplace_codes_job,
    trigger=IntervalTrigger(hours=1),
    name="플레이오토 마켓 코드 동기화"
)
```

**동작 방식**
1. PlayAuto에 등록된 모든 활성 상품 조회
2. 각 상품의 `ol_shop_no`로 상세 정보 API 호출
3. 응답에서 `shops` 배열 추출
4. 각 마켓별 `shop_cd` + `shop_sale_no` 저장

### 수동 동기화

**특정 상품 강제 동기화**
```bash
POST /api/products/{product_id}/sync-marketplace-codes
```

예시:
```bash
curl -X POST http://localhost:8000/api/products/100/sync-marketplace-codes
```

응답:
```json
{
  "success": true,
  "message": "3개 마켓 코드 동기화 완료",
  "synced_count": 3,
  "marketplace_codes": [
    {
      "shop_cd": "A001",
      "shop_sale_no": "B123456789",
      "transmitted_at": "2026-02-05 15:30:00"
    },
    {
      "shop_cd": "A006",
      "shop_sale_no": "7891234567",
      "transmitted_at": "2026-02-05 15:30:00"
    }
  ]
}
```

---

## API 엔드포인트

### 1. 마켓 코드 조회

**GET /api/products/{product_id}/marketplace-codes**

상품의 모든 마켓 코드 조회

응답:
```json
{
  "success": true,
  "product_id": 100,
  "product_name": "무선 블루투스 이어폰",
  "ol_shop_no": "12345678901234567890",
  "marketplace_codes": [
    {
      "id": 1,
      "shop_cd": "A001",
      "shop_sale_no": "B123456789",
      "transmitted_at": "2026-02-05 10:00:00",
      "last_checked_at": "2026-02-05 15:00:00"
    }
  ]
}
```

### 2. 마켓 코드 동기화

**POST /api/products/{product_id}/sync-marketplace-codes**

특정 상품의 마켓 코드 강제 동기화

---

## DB 메서드

### 저장/업데이트
```python
from database.db_wrapper import get_db

db = get_db()

# 마켓 코드 저장
db.upsert_marketplace_code(
    product_id=100,
    shop_cd="A001",
    shop_sale_no="B123456789"
)
```

### 조회 (상품별)
```python
# 상품의 모든 마켓 코드 조회
codes = db.get_marketplace_codes_by_product(product_id=100)
# [
#   {"shop_cd": "A001", "shop_sale_no": "B123456789"},
#   {"shop_cd": "A006", "shop_sale_no": "7891234567"}
# ]
```

### 조회 (주문 매칭용)
```python
# 마켓 코드로 상품 찾기
product = db.get_product_by_marketplace_code(
    shop_cd="A006",
    shop_sale_no="7891234567"
)
# {"id": 100, "product_name": "무선 블루투스 이어폰", ...}
```

### 동기화 대상 조회
```python
# 최근 24시간 동안 확인 안 된 상품
products = db.get_products_for_marketplace_sync(hours=24, limit=100)
```

---

## 테스트

### 테스트 실행
```bash
cd backend
python test_marketplace_sync.py
```

### 테스트 항목
1. PlayAuto API 상품 상세 조회
2. DB CRUD 기능
3. 스케줄러 작업 실행
4. 주문 매칭

---

## 주문 자동 매칭

주문이 동기화될 때 자동으로 상품 매칭 시도:

```python
# backend/database/db_wrapper.py
def sync_playauto_order_to_local(self, order_data: Dict):
    # 주문 저장
    # ...

    # 자동 매칭
    shop_cd = order_data.get("shop_cd")
    shop_sale_no = order_data.get("shop_sale_no")

    product = self.get_product_by_marketplace_code(shop_cd, shop_sale_no)

    if product:
        print(f"✅ 주문 매칭 성공: {product['product_name']}")
    else:
        print(f"⚠️ 매칭 실패: shop_cd={shop_cd}, shop_sale_no={shop_sale_no}")
```

---

## 프론트엔드 연동

### 상품 상세 페이지에서 마켓 코드 표시

```typescript
// 마켓 코드 조회
const response = await fetch(`/api/products/${productId}/marketplace-codes`);
const data = await response.json();

// 표시
data.marketplace_codes.forEach(code => {
  console.log(`${code.shop_cd}: ${code.shop_sale_no}`);
});
```

### 수동 동기화 버튼

```typescript
// 동기화 실행
const syncMarketplaceCodes = async (productId: number) => {
  const response = await fetch(
    `/api/products/${productId}/sync-marketplace-codes`,
    { method: 'POST' }
  );

  const result = await response.json();
  alert(`${result.synced_count}개 마켓 코드 동기화 완료`);
};
```

---

## 마켓 코드 (shop_cd)

| 코드 | 마켓명 |
|------|--------|
| A001 | 옥션 |
| A006 | 쿠팡 |
| A112 | 네이버 스마트스토어 |
| A027 | 11번가 |
| A077 | 지마켓 |
| ... | ... |

---

## 트러블슈팅

### 1. 마켓 코드가 저장 안 됨

**원인**: 상품이 아직 마켓에 전송되지 않음

**해결**: PlayAuto에서 수동으로 마켓 전송 후 동기화 실행

### 2. 주문 매칭 실패

**원인**: 마켓 코드가 DB에 없음

**해결**:
```bash
POST /api/products/{product_id}/sync-marketplace-codes
```

### 3. 스케줄러가 작동 안 함

**확인**:
```bash
GET /api/scheduler/status
```

**로그 확인**:
```bash
railway logs
```

---

## 장점

1. ✅ **완전 자동화**: 수동 입력 불필요
2. ✅ **실시간 동기화**: 1시간마다 자동 업데이트
3. ✅ **정확한 매칭**: shop_cd + shop_sale_no 조합으로 100% 정확
4. ✅ **다중 마켓 지원**: 무제한 마켓 추가 가능
5. ✅ **스키마 확장 불필요**: 새 마켓 추가 시 코드 변경 없음

---

## 다음 단계

1. 프론트엔드 UI 추가 (상품 상세 페이지에 마켓 코드 표시)
2. 주문-상품 연결 테이블 생성 (심화)
3. 재고 동기화 (마켓별 재고 관리)
4. 알림 추가 (매칭 실패 시 알림)
