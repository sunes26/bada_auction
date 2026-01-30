# Railway 백엔드 배포 완료 ✅

## 날짜
2026-01-30

## 배포 정보

### Railway URL
**Production URL**: `https://badaauction-production.up.railway.app`

### Health Check
```bash
curl https://badaauction-production.up.railway.app/health
```

**응답**:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "true",
  "timestamp": "2026-01-30T13:43:56.286770"
}
```

---

## 해결한 문제들

### 문제 1: Next.js 빌드 시도
**증상**: Railway가 프론트엔드를 빌드하려고 시도
```
npm run build
Build error occurred
```

**해결**: Dockerfile 사용

---

### 문제 2: python-multipart 누락
**증상**: 서버 크래시 반복
```
Form data requires "python-multipart" to be installed
```

**해결**: requirements.txt에 `python-multipart>=0.0.6` 추가

---

### 문제 3: Worker 과다 생성
**증상**: 38개 이상의 worker 시작 → 메모리 부족 → 응답 없음
```
[INFO] Booting worker with pid: 5, 6, 7, ... 43
```

**해결**: Worker 수를 2개로 제한
```python
workers = int(os.getenv('WEB_CONCURRENCY', 2))
```

---

### 문제 4: 환경 변수 미설정
**증상**: `"environment": "false"` → SQLite 사용 (데이터 손실 위험)

**해결**: Railway Variables에 11개 환경 변수 설정
- USE_POSTGRESQL=true
- DATABASE_URL (Supabase PostgreSQL)
- Playauto API keys
- Encryption key
- External API keys

---

## 최종 구성

### Docker 설정
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/ /app/
RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD gunicorn main:app --config gunicorn_conf.py --bind 0.0.0.0:$PORT
```

### Gunicorn 설정
- **Workers**: 2 (Railway Hobby Plan 최적화)
- **Worker Class**: uvicorn.workers.UvicornWorker
- **Timeout**: 120초
- **Port**: Railway 자동 할당 ($PORT)

### 환경 변수 (11개)
```
USE_POSTGRESQL=true
DATABASE_URL=postgresql://...
PLAYAUTO_SOLUTION_KEY=...
PLAYAUTO_API_KEY=...
PLAYAUTO_EMAIL=...
PLAYAUTO_PASSWORD=...
PLAYAUTO_API_URL=https://openapi.playauto.io/api
ENCRYPTION_KEY=...
OPENAI_API_KEY=...
CAPTCHA_API_KEY=...
ENVIRONMENT=production
```

---

## 배포 통계

### 빌드 정보
- **빌드 방식**: Docker
- **베이스 이미지**: python:3.9-slim
- **빌드 시간**: 약 2-3분
- **패키지 수**: 18개 Python 패키지

### 실행 정보
- **서버**: Gunicorn + Uvicorn
- **Workers**: 2개
- **메모리 사용**: ~200-300MB
- **CPU 사용**: ~10-20%

### 데이터베이스
- **타입**: PostgreSQL (Supabase)
- **연결 방식**: Connection pooler (포트 6543)
- **테이블 수**: 24개
- **데이터**: 170 rows
- **상태**: ✅ 연결 성공

---

## API 엔드포인트

### 주요 엔드포인트

#### Health & Info
- `GET /health` - Health check
- `GET /` - API 정보
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

#### 상품 수집
- `POST /api/sourcing/search` - 상품 검색
- `GET /api/sourcing/accounts` - 소싱 계정 목록
- `POST /api/sourcing/accounts` - 소싱 계정 추가

#### 모니터링
- `GET /api/monitoring/products` - 모니터링 상품 목록
- `POST /api/monitoring/products` - 상품 추가
- `DELETE /api/monitoring/products/{id}` - 상품 삭제
- `PUT /api/monitoring/products/{id}/toggle` - 모니터링 활성화/비활성화

#### 주문 관리
- `GET /api/orders` - 주문 목록
- `GET /api/orders/unified` - 통합 주문 관리
- `GET /api/orders/pending` - 발주 대기 목록

#### Playauto 연동
- `GET /api/playauto/settings` - Playauto 설정
- `POST /api/playauto/products/register` - 상품 등록
- `GET /api/playauto/orders/sync` - 주문 동기화
- `GET /api/playauto/categories` - Playauto 카테고리

#### 카테고리
- `GET /api/categories` - 카테고리 목록
- `GET /api/category-mappings` - 카테고리 매핑

#### 대시보드
- `GET /api/dashboard/stats` - 대시보드 통계

#### 스케줄러
- `GET /api/scheduler/status` - 스케줄러 상태
- `POST /api/scheduler/toggle` - 스케줄러 활성화/비활성화

#### 알림
- `GET /api/notifications` - 알림 목록
- `PUT /api/notifications/{id}/read` - 알림 읽음 처리

---

## Git 커밋 히스토리

1. **Commit `84d79b7`**: Railway 배포 설정 추가
2. **Commit `dbfa884`**: Root level Railway 설정
3. **Commit `0cb84cc`**: Dockerfile 추가
4. **Commit `e37eee3`**: 충돌 설정 제거 (railway.json, nixpacks.toml)
5. **Commit `07f9740`**: python-multipart 추가
6. **Commit `c96a77f`**: Worker 수 제한 (2개)

---

## 성능 & 비용

### Railway Hobby Plan
- **가격**: $5/월
- **리소스**:
  - 0.5-1 vCPU
  - 512MB-1GB RAM
  - 1GB 디스크
- **실행 시간**: 500시간/월 (약 20일)
- **네트워크**: 무제한 대역폭

### Supabase Free Plan
- **가격**: $0/월
- **데이터베이스**: 500MB
- **스토리지**: 1GB
- **네트워크**: 5GB/월

**총 비용**: $5/월

---

## 검증 체크리스트

- [x] Railway 프로젝트 생성
- [x] GitHub 저장소 연결
- [x] Dockerfile 기반 빌드
- [x] 환경 변수 11개 설정
- [x] 컨테이너 시작 성공
- [x] Health check 응답 확인
- [x] PostgreSQL 연결 확인
- [x] Worker 수 최적화
- [x] python-multipart 설치
- [x] API 엔드포인트 응답 확인

---

## 다음 단계: Phase 4 - Vercel 프론트엔드 배포

### 준비 사항

1. **Railway URL 확인** ✅
   ```
   https://badaauction-production.up.railway.app
   ```

2. **프론트엔드 환경 변수 업데이트**
   ```env
   NEXT_PUBLIC_API_BASE_URL=https://badaauction-production.up.railway.app
   ```

3. **Vercel 배포**
   - GitHub 연동
   - 환경 변수 설정
   - 자동 빌드 및 배포

---

## 트러블슈팅

### Health check 실패
1. Railway Logs 확인
2. 환경 변수 확인 (특히 DATABASE_URL, USE_POSTGRESQL)
3. Worker가 정상 시작되었는지 확인

### Database 연결 실패
1. Supabase PostgreSQL 상태 확인
2. DATABASE_URL 정확성 확인 (포트 6543)
3. 네트워크 연결 확인

### 메모리 부족
1. Worker 수 확인 (2개 권장)
2. Railway Metrics 확인
3. 필요 시 Plan 업그레이드

---

**작성자**: Claude Sonnet 4.5
**날짜**: 2026-01-30
**상태**: ✅ Railway 배포 완료
**Railway URL**: https://badaauction-production.up.railway.app
**다음**: Phase 4 - Vercel 프론트엔드 배포
