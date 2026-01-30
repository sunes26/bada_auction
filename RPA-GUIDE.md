# RPA 자동 발주 모듈 사용 가이드

물바다AI RPA(Robotic Process Automation) 자동 발주 시스템은 고객 주문이 발생하면 자동으로 소싱처에 주문하는 무인 발주 시스템입니다.

---

## 🎯 개요

### RPA 자동 발주란?

고객이 마켓(쿠팡, 네이버 등)에서 상품을 주문하면, **로봇이 자동으로** 소싱처(SSG, 홈플러스 등)에 접속하여 주문, 결제, 송장번호 추출까지 완료하는 시스템입니다.

### 워크플로우

```
[고객 주문] → [RPA 자동 실행] → [소싱처 로그인] → [장바구니 담기]
→ [배송지 입력] → [결제] → [송장번호 추출] → [완료!]
```

### 지원 소싱처

- ✅ **SSG.COM** - 완전 지원 (2Captcha API 통합, 쿠키 로그인)
- ✅ **홈플러스/Traders** - 완전 지원
- ✅ **11번가** - 완전 지원 (2Captcha API 통합, 쿠키 로그인)
- ⏳ G마켓, 스마트스토어 (추후 지원 예정)

---

## 📦 설치 및 설정

### 1. Playwright 설치

RPA는 Playwright를 사용하므로 브라우저 드라이버를 설치해야 합니다.

```bash
cd backend
pip install playwright
playwright install chromium
```

### 2. requirements.txt 설치

```bash
pip install -r requirements.txt
```

**requirements.txt에 포함된 패키지:**
- `fastapi`
- `uvicorn`
- `playwright>=1.49.0`
- `selenium>=4.27.0`
- `webdriver-manager>=4.0.2`
- 기타...

### 3. 데이터베이스 초기화

백엔드 서버를 실행하면 자동으로 DB가 초기화됩니다.

```bash
cd backend
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔧 소싱처 계정 등록

RPA가 자동 발주를 하려면 먼저 **소싱처 계정 정보**를 등록해야 합니다.

### API 사용 (권장)

**POST** `/api/orders/sourcing-account`

```json
{
  "source": "ssg",
  "account_id": "your_ssg_id",
  "account_password": "your_ssg_password",
  "payment_method": "card",
  "notes": "메인 계정"
}
```

**curl 예시:**

```bash
curl -X POST http://localhost:8000/api/orders/sourcing-account \
  -H "Content-Type: application/json" \
  -d '{
    "source": "ssg",
    "account_id": "your_id",
    "account_password": "your_password"
  }'
```

### 지원 소싱처 코드

- `ssg` - SSG.COM
- `traders` - 홈플러스/Traders
- `homeplus` - 홈플러스 (traders와 동일)
- `11st` - 11번가

**⚠️ 보안 주의:**
- 비밀번호는 DB에 **평문**으로 저장됩니다.
- 실제 운영 환경에서는 **암호화** 필수!
- 서버 접근 권한 제한 필수!

---

## 🚀 주문 생성 및 자동 발주

### 1단계: 주문 생성

고객이 마켓에서 주문하면, 물바다AI에 주문 정보를 등록합니다.

**POST** `/api/orders/create`

```json
{
  "order_number": "COUPANG-20260109-001",
  "market": "coupang",
  "customer_name": "홍길동",
  "customer_phone": "010-1234-5678",
  "customer_address": "서울시 강남구 테헤란로 123, 101동 101호",
  "customer_zipcode": "06000",
  "total_amount": 15900,
  "payment_method": "card",
  "notes": "빠른 배송 요청"
}
```

**응답:**

```json
{
  "success": true,
  "order_id": 1,
  "message": "주문이 생성되었습니다."
}
```

### 2단계: 주문 상품 추가

주문에 상품을 추가합니다.

**POST** `/api/orders/order/1/add-item`

```json
{
  "product_name": "[온백] 햇반 흰밥 210g x 10개",
  "product_url": "https://emart.ssg.com/item/itemView.ssg?itemId=1000012345678",
  "source": "ssg",
  "quantity": 1,
  "sourcing_price": 10900,
  "selling_price": 15900,
  "monitored_product_id": 5
}
```

**11번가 상품 추가 예시:**

```json
{
  "product_name": "[즉할10%+5%+사은품] 네슬레 킷캣 청키 오리지널",
  "product_url": "https://www.11st.co.kr/products/1595504325",
  "source": "11st",
  "quantity": 1,
  "sourcing_price": 11000,
  "selling_price": 15900,
  "monitored_product_id": 10
}
```

**응답:**

```json
{
  "success": true,
  "order_item_id": 1,
  "message": "주문 상품이 추가되었습니다."
}
```

### 3단계: 자동 발주 실행

**POST** `/api/orders/auto-order`

```json
{
  "order_item_id": 1,
  "headless": true
}
```

**파라미터:**
- `order_item_id`: 주문 상품 ID
- `headless`: 브라우저 헤드리스 모드 (true = 백그라운드 실행, false = 브라우저 화면 보기)

**응답:**

```json
{
  "success": true,
  "message": "자동 발주가 시작되었습니다. 백그라운드에서 실행됩니다.",
  "order_item_id": 1
}
```

**실행 프로세스:**
1. 소싱처 접속 (SSG, 홈플러스, 11번가 등)
2. 로그인 (등록된 계정 정보 사용)
   - 쿠키 우선 사용 (빠른 로그인) - **SSG, 11번가 지원**
   - CAPTCHA 자동 해결 지원 (2Captcha API) - **SSG, 11번가 지원**
3. 상품 페이지 이동
4. 옵션 선택 및 장바구니 담기
5. 주문서 작성 (고객 배송지 입력)
6. 결제
7. 송장번호 추출
8. DB 업데이트 (상태: `completed`, 송장번호 저장)

**소싱처별 특이사항:**

**SSG.COM:**
- 쿠키 로그인: 저장된 쿠키로 빠른 로그인 지원
- CAPTCHA: 2Captcha API로 자동 해결 (API 키 필요)
- 천천히 타이핑: 봇 감지 우회 (100ms 딜레이)

**11번가:**
- **2개 UI 패턴 자동 감지**
  - 패턴 1: 드롭다운 → Accordion → 옵션 선택 (복잡한 옵션)
  - 패턴 2: "선택한 옵션 추가하기" 버튼 즉시 클릭 (간단한 옵션)
- 표준상품: 여러 상품 중 선택 가능 (자동으로 첫 번째 상품 선택)
- CAPTCHA: 2Captcha API로 자동 해결 (API 키 필요)
- 쿠키 로그인: 저장된 쿠키로 빠른 로그인 지원
- 직접 구매: 장바구니를 건너뛰고 직접 구매하기 버튼 클릭
- 수량 조절: + 버튼 자동 클릭 (1-99개)
- 배송지 자동 입력: readonly 필드 강제 입력 (3초 이내)

---

## 📊 주문 관리

### 주문 목록 조회

**GET** `/api/orders/list?status=pending&limit=50`

**응답:**

```json
{
  "success": true,
  "orders": [
    {
      "id": 1,
      "order_number": "COUPANG-20260109-001",
      "market": "coupang",
      "customer_name": "홍길동",
      "order_status": "pending",
      "total_amount": 15900,
      "created_at": "2026-01-09 12:00:00"
    }
  ],
  "total": 1
}
```

### 자동 발주 대기 목록 조회

**GET** `/api/orders/pending-items`

```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "product_name": "[온백] 햇반 흰밥 210g x 10개",
      "product_url": "https://emart.ssg.com/item/itemView.ssg?itemId=1000012345678",
      "source": "ssg",
      "rpa_status": "pending",
      "customer_name": "홍길동",
      "customer_address": "서울시 강남구..."
    }
  ],
  "total": 1
}
```

### RPA 실행 로그 조회

**GET** `/api/orders/item/1/logs`

```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "order_item_id": 1,
      "source": "ssg",
      "action": "login",
      "status": "success",
      "message": "로그인 완료",
      "execution_time": 3.2,
      "created_at": "2026-01-09 12:01:00"
    },
    {
      "id": 2,
      "action": "add_to_cart",
      "status": "success",
      "message": "장바구니 추가 완료",
      "execution_time": 2.5
    },
    {
      "id": 3,
      "action": "auto_order",
      "status": "success",
      "message": "자동 발주 완료",
      "execution_time": 45.8
    }
  ],
  "total": 3
}
```

---

## 🔍 RPA 상태 코드

### 주문 상태 (order_status)

- `pending` - 대기 중
- `processing` - 처리 중
- `completed` - 완료
- `failed` - 실패
- `cancelled` - 취소

### RPA 상태 (rpa_status)

- `pending` - 자동 발주 대기
- `in_progress` - 실행 중
- `completed` - 완료
- `failed` - 실패

---

## 🛠 디버깅 및 문제 해결

### headless=false로 브라우저 확인

RPA가 실패하면 브라우저를 직접 보면서 디버깅할 수 있습니다.

```json
{
  "order_item_id": 1,
  "headless": false
}
```

### 스크린샷 확인

RPA 실행 중 각 단계마다 스크린샷이 저장됩니다.

**위치:** `backend/screenshots/`

- `login_success_20260109_120100.png`
- `cart_success_20260109_120105.png`
- `checkout_success_20260109_120110.png`
- `payment_success_20260109_120120.png`
- `error_20260109_120125.png` (에러 발생 시)

### 로그 확인

터미널에서 실시간 로그를 확인할 수 있습니다.

```
[2026-01-09 12:01:00] [SUCCESS] login - 로그인 완료
[2026-01-09 12:01:05] [SUCCESS] add_to_cart - 버튼 클릭: button:has-text("장바구니")
[2026-01-09 12:01:10] [SUCCESS] checkout - 배송지 입력 완료
[2026-01-09 12:01:20] [SUCCESS] payment - 결제 완료 확인
[2026-01-09 12:01:25] [INFO] extract_tracking - 주문번호 추출: 1234567890
```

---

## ⚠️ 주의사항

### 1. 법적 리스크
- 소싱처의 이용약관을 확인하세요.
- 자동화 프로그램 사용이 금지된 사이트도 있습니다.
- **본인 책임 하에 사용**하세요.

### 2. 봇 감지
- 소싱처에서 봇으로 감지하여 계정이 차단될 수 있습니다.
- 너무 빠른 속도로 주문하지 마세요.
- 여러 계정을 번갈아 사용하는 것을 권장합니다.

### 3. 보안
- **비밀번호는 암호화하여 저장**하세요 (현재는 평문 저장).
- 서버 접근 권한을 제한하세요.
- API에 인증을 추가하세요.

### 4. 결제 정보
- 현재 RPA는 **이미 등록된 결제 수단**을 사용합니다.
- 카드 정보를 입력하는 기능은 포함되지 않았습니다.
- 소싱처 계정에 결제 수단이 미리 등록되어 있어야 합니다.

---

## 📈 다음 단계

### 구현 예정 기능

1. **G마켓, 스마트스토어 RPA** 추가
2. **송장번호 자동 등록** (마켓 API 연동)
3. **플레이오토 2.0 API 통합** (다채널 주문 수집)
4. **비밀번호 암호화** (AES-256)
5. **실패 시 자동 재시도** (최대 3회)
6. **Slack/Discord 알림** (발주 완료/실패 시)
7. **일일 발주 통계 대시보드**

---

## 🆘 트러블슈팅

### Q: RPA가 로그인에 실패합니다.

**A:**
- 소싱처 계정 정보가 올바른지 확인하세요.
- `headless=false`로 브라우저를 열어서 확인하세요.
- 소싱처에서 보안 인증(OTP, 캡차 등)이 필요한지 확인하세요.
- **SSG / 11번가 CAPTCHA 발생 시:**
  - 2Captcha API 키를 `.env.local` 파일에 `CAPTCHA_API_KEY`로 설정
  - API 키가 없으면 headless=false로 수동 해결 필요
  - 쿠키가 저장되면 다음부터는 CAPTCHA 없이 로그인 가능

### Q: 결제가 안 됩니다.

**A:**
- 소싱처 계정에 결제 수단이 등록되어 있는지 확인하세요.
- 카드 한도나 잔액이 충분한지 확인하세요.
- 스크린샷을 확인하여 어느 단계에서 멈췄는지 파악하세요.

### Q: 송장번호를 추출하지 못했습니다.

**A:**
- SSG와 홈플러스는 주문 완료 즉시 송장번호가 발급되지 않을 수 있습니다.
- 나중에 마이페이지 > 주문내역에서 수동으로 확인하세요.
- `order_number`(주문번호)는 추출되므로, 이를 기반으로 나중에 조회 가능합니다.

### Q: Playwright가 설치되지 않습니다.

**A:**
```bash
pip uninstall playwright
pip install playwright
playwright install chromium
```

---

## 📞 문의 및 지원

RPA 자동 발주 시스템에 대한 문의는 프로젝트 이슈 트래커를 이용해주세요.

**프로젝트:** 물바다AI (Onbaek AI)
**버전:** 2.0.0 (RPA Auto-Order)
**업데이트:** 2026-01-09
