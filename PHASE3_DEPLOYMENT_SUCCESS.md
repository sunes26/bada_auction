# Phase 3: Railway 배포 완료 ✅

## 날짜
2026-01-30

## 목표
FastAPI 백엔드를 Railway에 성공적으로 배포 완료

---

## 배포 과정

### 문제 해결 과정

#### 문제 1: Root Directory 인식 실패
**증상**: Railway가 Next.js 프론트엔드를 빌드하려고 시도
```
npm run build
Build error occurred
```

**해결**: 프로젝트 루트에 `railway.json` 및 `nixpacks.toml` 추가

#### 문제 2: `cd` 명령어 실패
**증상**:
```
The executable `cd` could not be found.
```

**원인**: Nixpacks 빌더에서 `cd backend &&` 명령어 실행 실패

**최종 해결**: Dockerfile 사용으로 전환
- `railway.json` 및 `nixpacks.toml` 제거
- Dockerfile만 유지하여 명확한 빌드 프로세스 정의

---

## 배포 구성

### 사용된 파일

1. **`Dockerfile`** (프로젝트 루트)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/ /app/
RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD gunicorn main:app --config gunicorn_conf.py --bind 0.0.0.0:$PORT
```

2. **`.dockerignore`** (프로젝트 루트)
- Frontend 파일 제외 (node_modules, .next, package.json 등)
- Backend 내 불필요한 파일 제외 (test_*.py, RPA, CSV 등)

3. **`backend/gunicorn_conf.py`**
- Worker 수: CPU * 2 + 1 (자동 계산)
- Worker class: uvicorn.workers.UvicornWorker
- Timeout: 120초
- Preload app: True (성능 최적화)

4. **`backend/.railwayignore`**
- 로컬 파일 배포 제외 설정

---

## 환경 변수 설정

Railway Variables에 설정된 환경 변수:

```env
USE_POSTGRESQL=true
DATABASE_URL=postgresql://postgres:***@db.spkeunlwkrqkdwunkufy.supabase.co:6543/postgres?sslmode=require
PLAYAUTO_SOLUTION_KEY=***
PLAYAUTO_API_KEY=***
PLAYAUTO_EMAIL=***
PLAYAUTO_PASSWORD=***
PLAYAUTO_API_URL=https://openapi.playauto.io/api
ENCRYPTION_KEY=***
OPENAI_API_KEY=***
CAPTCHA_API_KEY=***
ENVIRONMENT=production
```

---

## 배포 결과

### 빌드 정보
- **빌드 방식**: Docker
- **베이스 이미지**: python:3.9-slim
- **빌드 시간**: 약 2-3분
- **패키지 설치**: 17개 Python 패키지

### 실행 정보
- **서버**: Gunicorn + Uvicorn
- **Workers**: 자동 계산 (CPU * 2 + 1)
- **포트**: Railway 자동 할당 ($PORT)
- **Health Check**: /health 엔드포인트

### 데이터베이스
- **타입**: PostgreSQL (Supabase)
- **연결**: Connection pooler (포트 6543)
- **상태**: ✅ 연결 성공

---

## API 엔드포인트

### Railway 배포 URL
```
https://[your-app-name].up.railway.app
```

### 주요 엔드포인트

1. **Health Check**
   ```
   GET /health
   ```
   응답:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "environment": "true",
     "timestamp": "2026-01-30T..."
   }
   ```

2. **API Root**
   ```
   GET /
   ```

3. **상품 수집**
   ```
   POST /api/sourcing/search
   GET /api/sourcing/accounts
   ```

4. **모니터링**
   ```
   GET /api/monitoring/products
   POST /api/monitoring/products
   ```

5. **주문 관리**
   ```
   GET /api/orders
   GET /api/orders/unified
   ```

6. **Playauto 연동**
   ```
   GET /api/playauto/settings
   POST /api/playauto/products/register
   GET /api/playauto/orders/sync
   ```

7. **카테고리**
   ```
   GET /api/categories
   GET /api/playauto/categories
   ```

8. **대시보드**
   ```
   GET /api/dashboard/stats
   ```

---

## Git 커밋 히스토리

### Phase 3 관련 커밋

1. **Commit `84d79b7`**: Railway 배포 설정 추가
   - railway.json, gunicorn_conf.py, .railwayignore
   - Health check 엔드포인트 강화
   - CORS 설정 업데이트

2. **Commit `dbfa884`**: Root level Railway 설정
   - 프로젝트 루트에 railway.json 추가
   - nixpacks.toml 추가

3. **Commit `0cb84cc`**: Dockerfile 추가
   - Docker 기반 배포로 전환
   - .dockerignore 추가

4. **Commit `e37eee3`**: 충돌 설정 제거
   - railway.json 및 nixpacks.toml 제거
   - Dockerfile만 사용

---

## 배포 검증 체크리스트

- [x] Railway 프로젝트 생성
- [x] GitHub 저장소 연결
- [x] 환경 변수 11개 설정
- [x] Dockerfile 기반 빌드 성공
- [x] 컨테이너 시작 성공
- [x] Health check 응답 확인
- [x] PostgreSQL 연결 확인
- [ ] API 엔드포인트 전체 테스트
- [ ] Playauto API 연동 테스트
- [ ] 스케줄러 동작 확인

---

## 비용

- **Railway Hobby Plan**: $5/월
- **Supabase Free Plan**: $0/월
- **총 비용**: $5/월

---

## 다음 단계: Phase 4 - Vercel 프론트엔드 배포

### 준비 사항

1. **Railway URL 확인**
   - Settings → Networking → Domain

2. **프론트엔드 환경 변수 업데이트**
   ```env
   NEXT_PUBLIC_API_BASE_URL=https://[railway-url].railway.app
   ```

3. **Vercel 배포**
   - GitHub 연동
   - 환경 변수 설정
   - 자동 배포

---

## 트러블슈팅 가이드

### 문제: Health check 실패
**확인 사항**:
1. Railway Logs에서 에러 확인
2. DATABASE_URL 환경 변수 확인
3. USE_POSTGRESQL=true 설정 확인

### 문제: 502 Bad Gateway
**확인 사항**:
1. Gunicorn이 올바른 포트 사용 ($PORT)
2. 컨테이너가 정상 시작되었는지 확인
3. Railway Logs 확인

### 문제: Database connection failed
**확인 사항**:
1. Supabase PostgreSQL 상태 확인
2. 네트워크 연결 확인 (Railway → Supabase)
3. DATABASE_URL 정확성 확인

---

## 성과

### 성공적으로 완료한 항목

✅ SQLite → PostgreSQL 마이그레이션 (170 rows)
✅ SQLAlchemy ORM 기반 코드 구현 (40+ 메서드)
✅ Hybrid database selection (환경 변수 기반)
✅ Docker 기반 배포 설정
✅ Railway 프로덕션 배포 완료
✅ PostgreSQL 연결 검증
✅ Health check 엔드포인트 동작

### 기술 스택

**Backend**:
- FastAPI 0.115.0
- Gunicorn 21.2.0
- Uvicorn (workers)
- SQLAlchemy 2.0.36
- psycopg2-binary 2.9.9

**Infrastructure**:
- Railway (Hosting)
- Supabase (PostgreSQL)
- Docker (Containerization)

**Deployment**:
- GitHub (Source control)
- Docker (Build)
- Gunicorn + Uvicorn (Production server)

---

**작성자**: Claude Sonnet 4.5
**날짜**: 2026-01-30
**상태**: ✅ Railway 배포 완료
**다음**: Phase 4 - Vercel 프론트엔드 배포
