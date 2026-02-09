# 🔑 플레이오토 API 설정 가이드

**작성일**: 2026-01-27
**API 키**: `UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj`
**API 문서**: https://developers.playauto.io/doc/

---

## 📋 현재 구현 분석

### 1. 인증 방식 (`backend/playauto/auth.py`)

코드에서 **2가지 인증 방식**을 지원합니다:

#### Option 1: Bearer 토큰 방식 (기본)
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
```

#### Option 2: HMAC 서명 방식 (api_secret이 있을 때)
```python
headers = {
    "X-API-Key": api_key,
    "X-Signature": signature,  # HMAC-SHA256 서명
    "X-Timestamp": timestamp,
    "Content-Type": "application/json",
    "Accept": "application/json"
}
```

### 2. API Base URL
- **기본값**: `https://api.playauto.co.kr/v2`
- **환경변수**: `PLAYAUTO_API_URL`

### 3. 구현된 엔드포인트

#### 주문 수집 (`backend/playauto/orders.py`)
```
GET /orders
```
**파라미터**:
- `start_date`: YYYY-MM-DD (기본: 7일 전)
- `end_date`: YYYY-MM-DD (기본: 오늘)
- `page`: 페이지 번호
- `limit`: 페이지당 항목 수 (기본: 100)
- `order_status`: 주문 상태 필터 (선택)
- `market`: 마켓 필터 (선택)

**응답 예상 구조**:
```json
{
  "data": {
    "orders": [
      {
        "playauto_order_id": "...",
        "market": "coupang",
        "order_number": "...",
        "customer_name": "...",
        "customer_phone": "...",
        "customer_address": "...",
        "customer_zipcode": "...",
        "total_amount": 15900,
        "order_date": "2026-01-27T12:00:00",
        "order_status": "pending",
        "items": [...]
      }
    ],
    "total": 100,
    "page": 1
  }
}
```

#### 주문 상세 조회
```
GET /orders/{playauto_order_id}
```

#### 송장 업로드 (`backend/playauto/tracking.py`)
```
POST /tracking/upload
```
**요청 바디**:
```json
{
  "tracking_list": [
    {
      "playauto_order_id": "...",
      "tracking_number": "1234567890",
      "courier_code": "cj",
      "tracking_url": "https://..."
    }
  ]
}
```

---

## ⚠️ API 문서 확인 필요 사항

API 문서 (https://developers.playauto.io/doc/)에서 다음 사항을 확인해주세요:

### 1. 인증 방식 확인
- [ ] Bearer 토큰 방식을 사용하는가?
- [ ] HMAC 서명 방식이 필요한가? (api_secret 필요)
- [ ] 헤더 이름이 맞는가? (`Authorization: Bearer {key}` 또는 `X-API-Key: {key}`)

### 2. Base URL 확인
- [ ] API Base URL이 `https://api.playauto.co.kr/v2`가 맞는가?
- [ ] 다른 URL을 사용하는가? (예: `https://api.playauto.io/v1`)

### 3. 엔드포인트 확인
- [ ] 주문 조회: `GET /orders`가 맞는가?
- [ ] 주문 상세: `GET /orders/{order_id}`가 맞는가?
- [ ] 송장 업로드: `POST /tracking/upload`가 맞는가?

### 4. 응답 구조 확인
- [ ] 응답이 `{ "data": { "orders": [...] } }` 구조인가?
- [ ] 다른 구조인가? (예: `{ "success": true, "orders": [...] }`)

### 5. 필수 파라미터 확인
- [ ] 날짜 형식이 `YYYY-MM-DD`가 맞는가?
- [ ] 필수 쿼리 파라미터가 있는가?

---

## 🚀 설정 방법

### Step 1: 암호화 키 생성

```bash
cd backend
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**출력 예시**:
```
xJ8_your_generated_encryption_key_here_abc123==
```

### Step 2: `.env.local` 파일 수정

**현재 상태**:
```env
PLAYAUTO_API_KEY=your_playauto_api_key_here
PLAYAUTO_API_SECRET=your_playauto_api_secret_here
PLAYAUTO_API_URL=https://api.playauto.co.kr/v2
ENCRYPTION_KEY=your_fernet_encryption_key_here
```

**수정 후** (실제 값으로 변경):
```env
# 플레이오토 API 키
PLAYAUTO_API_KEY=UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj

# API Secret (HMAC 서명 방식 사용 시 필요, 없으면 비워두기)
PLAYAUTO_API_SECRET=

# API Base URL (문서에서 확인한 실제 URL로 변경)
PLAYAUTO_API_URL=https://api.playauto.co.kr/v2

# 암호화 키 (Step 1에서 생성한 키)
ENCRYPTION_KEY=xJ8_your_generated_encryption_key_here_abc123==
```

### Step 3: Backend 서버 재시작

```bash
cd backend
python main.py
```

### Step 4: API 연결 테스트

#### 방법 1: Swagger UI (추천)
1. 브라우저에서 http://localhost:8000/docs 접속
2. `POST /api/playauto/settings` 엔드포인트 실행
   ```json
   {
     "api_key": "UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj",
     "api_secret": "",
     "api_base_url": "https://api.playauto.co.kr/v2",
     "enabled": true,
     "auto_sync_enabled": false,
     "auto_sync_interval": 30,
     "encrypt_credentials": true
   }
   ```
3. `POST /api/playauto/test-connection` 실행
4. 결과 확인

#### 방법 2: cURL
```bash
# 1. API 설정 저장
curl -X POST http://localhost:8000/api/playauto/settings \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj",
    "api_secret": "",
    "api_base_url": "https://api.playauto.co.kr/v2",
    "enabled": true,
    "auto_sync_enabled": false,
    "auto_sync_interval": 30,
    "encrypt_credentials": true
  }'

# 2. 연결 테스트
curl -X POST http://localhost:8000/api/playauto/test-connection
```

#### 방법 3: Python 스크립트
```bash
cd backend
python test_playauto_api.py
```

---

## 🔍 API 문서 확인 후 수정이 필요한 경우

### Base URL이 다른 경우

**예시**: API 문서에서 `https://api.playauto.io/v1`을 사용한다면

`.env.local` 수정:
```env
PLAYAUTO_API_URL=https://api.playauto.io/v1
```

### 인증 방식이 다른 경우

#### Case 1: API Secret이 필요한 경우
`.env.local`에 `PLAYAUTO_API_SECRET` 추가

#### Case 2: 다른 헤더 이름을 사용하는 경우
`backend/playauto/auth.py`의 `generate_auth_headers()` 함수 수정 필요

**예시**: `X-API-Token` 헤더를 사용하는 경우
```python
def generate_auth_headers(api_key: str, api_secret: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "X-API-Token": api_key,  # 변경
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    return headers
```

### 엔드포인트가 다른 경우

#### Case 1: 주문 조회 엔드포인트
**예시**: `/api/orders` 대신 `/v1/orders`를 사용하는 경우

`backend/playauto/orders.py` 수정:
```python
# Line 70, 72
response = await client.get("/v1/orders", params=params)  # 변경
```

#### Case 2: 송장 업로드 엔드포인트
**예시**: `/tracking/upload` 대신 `/v1/shipments`를 사용하는 경우

`backend/playauto/tracking.py` 수정 필요

### 응답 구조가 다른 경우

**예시**: 응답이 `{ "success": true, "orders": [...] }` 구조인 경우

`backend/playauto/orders.py`의 `_parse_orders_response()` 수정:
```python
def _parse_orders_response(self, response: Dict) -> Dict:
    try:
        # 응답 구조에 맞게 파싱
        orders_data = response.get("orders", [])  # 변경
        total = response.get("total", 0)
        # ...
```

---

## 🧪 테스트 시나리오

### 1. 연결 테스트
```bash
curl -X POST http://localhost:8000/api/playauto/test-connection
```

**예상 결과 (성공)**:
```json
{
  "success": true,
  "message": "플레이오토 API 연결 성공"
}
```

**예상 결과 (실패)**:
```json
{
  "success": false,
  "message": "API 연결 실패: [에러 메시지]"
}
```

### 2. 주문 조회 테스트
```bash
curl http://localhost:8000/api/playauto/orders?limit=10
```

**예상 결과 (성공)**:
```json
{
  "success": true,
  "data": [
    {
      "playauto_order_id": "...",
      "order_number": "...",
      "market": "coupang",
      ...
    }
  ]
}
```

### 3. 주문 동기화 테스트
```bash
curl -X POST http://localhost:8000/api/playauto/orders/sync
```

**예상 결과**:
```json
{
  "success": true,
  "message": "5개 주문 동기화 완료",
  "total_orders": 10,
  "synced_count": 5
}
```

---

## 🐛 트러블슈팅

### 문제 1: 401 Unauthorized
**원인**: API 키가 잘못되었거나 인증 방식이 다름
**해결**:
1. API 키 확인: `UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj`
2. API 문서에서 인증 방식 확인
3. 헤더 형식 확인

### 문제 2: 404 Not Found
**원인**: 엔드포인트 경로가 잘못됨
**해결**:
1. API 문서에서 실제 엔드포인트 확인
2. Base URL 확인
3. 코드 수정 (위의 "엔드포인트가 다른 경우" 참조)

### 문제 3: 응답 파싱 에러
**원인**: 응답 JSON 구조가 예상과 다름
**해결**:
1. API 문서에서 응답 구조 확인
2. 코드 수정 (위의 "응답 구조가 다른 경우" 참조)

### 문제 4: Rate Limiting
**원인**: API 호출 제한 초과
**해결**:
1. API 문서에서 Rate Limit 확인
2. 자동 동기화 간격 조정 (기본: 30분)
3. 재시도 로직 이미 구현되어 있음 (최대 3회, 지수 백오프)

---

## 📝 다음 단계

### 1. API 문서 확인 (우선순위: 높음)
- [ ] https://developers.playauto.io/doc/ 로그인 및 문서 확인
- [ ] 위의 "API 문서 확인 필요 사항" 체크리스트 완료
- [ ] 필요 시 코드 수정

### 2. API 키 설정 (우선순위: 높음)
- [ ] 암호화 키 생성
- [ ] `.env.local` 파일 수정
- [ ] Backend 서버 재시작

### 3. 연결 테스트 (우선순위: 높음)
- [ ] Swagger UI에서 연결 테스트
- [ ] 주문 조회 테스트
- [ ] 에러 발생 시 트러블슈팅

### 4. 자동 동기화 활성화 (우선순위: 중간)
- [ ] 통합 주문 관리 페이지에서 자동 동기화 설정
- [ ] 30분마다 주문 자동 수집 확인
- [ ] Slack/Discord 알림 설정

### 5. 실전 테스트 (우선순위: 중간)
- [ ] 실제 주문 데이터로 동기화 테스트
- [ ] 송장 업로드 테스트
- [ ] 통합 관리 UI에서 주문 확인

---

## 💡 참고 정보

### 현재 구현된 기능
- ✅ API 클라이언트 (httpx 기반, 비동기)
- ✅ 재시도 로직 (최대 3회, 지수 백오프)
- ✅ 타임아웃 관리 (기본 30초)
- ✅ 에러 처리 (PlayautoAPIError, PlayautoNetworkError 등)
- ✅ 암호화 (Fernet 대칭키)
- ✅ 주문 수집 API
- ✅ 송장 업로드 API
- ✅ 자동 동기화 스케줄러
- ✅ 통합 관리 UI

### 대기 중인 기능 (API 키 설정 후 활성화)
- 🔄 다채널 주문 자동 수집 (30분마다)
- 🔄 송장 일괄 업로드 (매일 오전 9시)
- 🔄 주문 동기화 알림 (Slack/Discord)
- 🔄 통합 대시보드 통계

---

**작성자**: Claude Sonnet 4.5
**프로젝트**: 물바다AI 통합 자동화 시스템
