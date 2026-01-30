# Phase 3: Railway 백엔드 배포 가이드

## 날짜
2026-01-30

## 목표
FastAPI 백엔드를 Railway에 배포하여 PostgreSQL 연결 및 API 서비스 제공

---

## 준비 완료된 파일

### 1. Railway 설정 파일 ✅
- **파일**: `backend/railway.json`
- **기능**: Railway 배포 설정 (빌드, 실행, 환경 변수)
- **내용**:
  - Nixpacks 빌더 사용
  - Gunicorn + Uvicorn 워커로 FastAPI 실행
  - Health check 설정 (/health 엔드포인트)
  - 환경 변수 템플릿

### 2. Gunicorn 설정 파일 ✅
- **파일**: `backend/gunicorn_conf.py`
- **기능**: 프로덕션 서버 설정
- **주요 설정**:
  ```python
  workers = CPU 수 * 2 + 1  # 자동 계산
  worker_class = 'uvicorn.workers.UvicornWorker'  # FastAPI 최적화
  timeout = 120  # 요청 타임아웃
  preload_app = True  # 성능 최적화
  ```

### 3. Railway Ignore 파일 ✅
- **파일**: `backend/.railwayignore`
- **기능**: 배포 시 제외할 파일 지정
- **제외 대상**:
  - 로컬 DB (monitoring.db)
  - 테스트 파일 (test_*.py)
  - RPA 관련 파일
  - 환경 변수 파일 (.env.local)
  - 마이그레이션 파일

### 4. Requirements 업데이트 ✅
- **파일**: `backend/requirements.txt`
- **추가**: `gunicorn>=21.2.0`

---

## Railway 배포 단계

### Step 1: Railway 계정 생성 및 프로젝트 생성

1. **Railway 회원가입**
   - https://railway.app 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - `sunes26/bada_auction` 저장소 선택
   - Root directory: `/backend` 설정

3. **서비스 설정**
   - Service name: `onbaek-ai-backend`
   - Branch: `main`

### Step 2: 환경 변수 설정

Railway 대시보드에서 다음 환경 변수를 설정:

#### 필수 환경 변수

```env
# Database (PostgreSQL)
USE_POSTGRESQL=true
DATABASE_URL=<Copy from .env.local>

# Playauto API
PLAYAUTO_SOLUTION_KEY=<Copy from .env.local>
PLAYAUTO_API_KEY=<Copy from .env.local>
PLAYAUTO_EMAIL=<Copy from .env.local>
PLAYAUTO_PASSWORD=<Copy from .env.local>
PLAYAUTO_API_URL=https://openapi.playauto.io/api

# Security
ENCRYPTION_KEY=<Copy from .env.local>

# External APIs
OPENAI_API_KEY=<Copy from .env.local>
CAPTCHA_API_KEY=<Copy from .env.local>

# Railway auto-provides PORT variable (default: 8000)
```

**중요**: 실제 값은 `.env.local` 파일에서 복사하여 Railway 대시보드에 입력하세요.

#### 환경 변수 입력 방법

1. Railway 프로젝트 대시보드에서 `onbaek-ai-backend` 서비스 클릭
2. "Variables" 탭 클릭
3. "New Variable" 클릭하여 위의 각 변수 추가
4. 또는 "Raw Editor" 클릭하여 한 번에 붙여넣기

### Step 3: 배포 트리거

1. **자동 배포**
   - GitHub에 push하면 자동으로 배포됨
   - 배포 로그는 "Deployments" 탭에서 확인

2. **수동 배포**
   - Railway 대시보드에서 "Deploy" 버튼 클릭

### Step 4: Health Check 확인

배포 완료 후:

1. **서비스 URL 확인**
   - Railway 대시보드에서 자동 생성된 URL 확인
   - 예: `https://onbaek-ai-backend-production.up.railway.app`

2. **Health Check 테스트**
   ```bash
   curl https://your-railway-url.railway.app/health
   ```

   **기대 응답**:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "timestamp": "2026-01-30T12:00:00Z"
   }
   ```

3. **API 테스트**
   ```bash
   # Categories 조회
   curl https://your-railway-url.railway.app/api/categories

   # Monitored Products 조회
   curl https://your-railway-url.railway.app/api/monitoring/products

   # Dashboard Stats 조회
   curl https://your-railway-url.railway.app/api/dashboard/stats
   ```

---

## Health Check 엔드포인트 추가

Railway health check를 위해 `backend/main.py`에 엔드포인트 추가 필요:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        db = get_db()
        db.get_dashboard_stats()  # Simple query to verify DB connection

        return {
            "status": "healthy",
            "database": "connected",
            "environment": os.getenv("USE_POSTGRESQL", "false"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
```

---

## 배포 후 검증 체크리스트

- [ ] Railway 빌드 성공
- [ ] 서비스 시작 성공 (Gunicorn 로그 확인)
- [ ] Health check 응답 확인
- [ ] PostgreSQL 연결 확인
- [ ] Categories API 테스트
- [ ] Monitored Products API 테스트
- [ ] Dashboard Stats API 테스트
- [ ] Playauto API 통합 테스트

---

## 예상 비용

### Railway Pricing
- **Hobby Plan**: $5/월
  - 500 실행 시간/월
  - 8GB RAM
  - 8GB 디스크
  - 무제한 대역폭

### Supabase
- **Free Plan**: $0/월 (현재 사용 중)
  - 500MB 데이터베이스
  - 1GB 파일 스토리지
  - 5GB 대역폭

**총 예상 비용**: $5/월

---

## 트러블슈팅

### 문제 1: 빌드 실패
**증상**: `pip install` 실패
**해결**:
1. `requirements.txt` 확인
2. Python 버전 호환성 확인
3. Railway 로그에서 에러 메시지 확인

### 문제 2: Database 연결 실패
**증상**: Health check에서 503 에러
**해결**:
1. `DATABASE_URL` 환경 변수 확인
2. `USE_POSTGRESQL=true` 설정 확인
3. Supabase 연결 문자열 정확성 확인
4. Railway → Supabase 네트워크 연결 확인

### 문제 3: 타임아웃 에러
**증상**: 요청이 120초 후 타임아웃
**해결**:
1. `gunicorn_conf.py`에서 `timeout` 값 증가
2. API 로직 최적화 (느린 쿼리 개선)

### 문제 4: 메모리 부족
**증상**: Worker가 재시작됨
**해결**:
1. Worker 수 감소 (`gunicorn_conf.py`)
2. Railway Plan 업그레이드 고려

---

## 다음 단계

### Immediate
1. ✅ Railway 설정 파일 생성
2. ⏳ `backend/main.py`에 health check 엔드포인트 추가
3. ⏳ Railway 프로젝트 생성
4. ⏳ 환경 변수 설정
5. ⏳ 배포 및 테스트

### Phase 4: Vercel 프론트엔드 배포
1. 프론트엔드 API URL 업데이트 (`NEXT_PUBLIC_API_BASE_URL`)
2. Vercel 프로젝트 생성
3. 환경 변수 설정
4. 배포 및 테스트

### Phase 5: 이미지 마이그레이션 (선택사항)
1. 로컬 이미지 → Supabase Storage
2. 데이터베이스 이미지 URL 업데이트

---

## 파일 변경 사항

### 새 파일
```
backend/railway.json                  - Railway 배포 설정
backend/gunicorn_conf.py              - Gunicorn 서버 설정
backend/.railwayignore                - 배포 제외 파일
PHASE3_RAILWAY_DEPLOYMENT.md          - 이 문서
```

### 수정된 파일
```
backend/requirements.txt              - gunicorn 추가
backend/main.py                       - health check 엔드포인트 추가 (다음 단계)
```

---

## 참고 자료

- Railway 공식 문서: https://docs.railway.app
- Gunicorn 설정: https://docs.gunicorn.org/en/stable/settings.html
- FastAPI 배포: https://fastapi.tiangolo.com/deployment/
- Supabase 연결: https://supabase.com/docs/guides/database

---

**작성자**: Claude Sonnet 4.5
**날짜**: 2026-01-30
**상태**: ⏳ Railway 설정 파일 준비 완료 (배포 대기)
**다음**: Health check 엔드포인트 추가 → Railway 배포
