# API 문서

## Production API
- **Base URL**: `https://badaauction-production.up.railway.app`
- **Swagger UI**: `https://badaauction-production.up.railway.app/docs`
- **ReDoc**: `https://badaauction-production.up.railway.app/redoc`

## Local API
- **Base URL**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`

---

## 주요 엔드포인트

### Health Check
```bash
GET /health
```

### 상품 관리
```bash
GET    /api/products          # 판매 상품 목록
POST   /api/products/create   # 상품 등록
PUT    /api/products/{id}     # 상품 수정
DELETE /api/products/{id}     # 상품 삭제
```

### 모니터링
```bash
GET    /api/monitoring/products  # 모니터링 상품 목록
POST   /api/monitoring/products  # 모니터링 추가
DELETE /api/monitoring/products/{id}  # 모니터링 삭제
```

### 주문 관리
```bash
GET  /api/orders              # 주문 목록
GET  /api/orders/unified      # 통합 주문 관리
POST /api/orders/create       # 주문 생성
```

### Playauto
```bash
GET  /api/playauto/settings          # 설정 조회
POST /api/playauto/products/register # 상품 등록
GET  /api/playauto/orders/sync       # 주문 동기화
```

### 대시보드
```bash
GET /api/dashboard/all    # 통합 대시보드 (5개 API 통합)
GET /api/dashboard/stats  # 대시보드 통계
```

### 자동 가격 조정
```bash
GET  /api/auto-pricing/settings          # 설정 조회
POST /api/auto-pricing/settings          # 설정 저장
POST /api/auto-pricing/adjust-product/{id}  # 개별 상품 가격 조정
POST /api/auto-pricing/adjust-all        # 모든 상품 일괄 조정
```

### WebSocket
```bash
WS /ws/notifications  # 실시간 알림 (주문, 가격, 송장 등)
```

---

자세한 API 문서는 `/docs` 엔드포인트를 참고하세요.
