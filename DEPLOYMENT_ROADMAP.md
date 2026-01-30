# 🚀 온백AI 배포 로드맵

> **목표**: 로컬 SQLite 기반 → 클라우드 프로덕션 환경으로 전환

---

## 📊 현재 상태 분석

### 기술 스택 (AS-IS)
- **Frontend**: Next.js 15 (로컬 개발 서버)
- **Backend**: FastAPI (로컬 Uvicorn)
- **Database**: SQLite (`monitoring.db`)
- **Image Storage**: 로컬 파일 시스템 (`/supabase-images`)
- **Scheduler**: APScheduler (프로세스 내부)
- **API Keys**: `.env.local` (로컬 파일)

### 주요 기능
1. 상품 수집 및 모니터링
2. AI 상세페이지 생성 (OpenAI)
3. 플레이오토 주문 연동
4. 자동 가격 모니터링
5. 송장 업로드 자동화
6. Slack/Discord 알림

### 배포 시 해결 과제
- ❌ SQLite는 다중 접근 제한 (동시성 문제)
- ❌ 로컬 파일 시스템 (이미지 저장)
- ❌ 스케줄러 프로세스 관리
- ❌ 환경 변수 보안
- ❌ 로그 및 모니터링
- ❌ HTTPS/도메인 설정

---

## 🎯 배포 아키텍처 (TO-BE)

### 권장 스택

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    Next.js 15 (Vercel)                       │
│                  https://yourdomain.com                      │
└─────────────────────────────────────────────────────────────┘
                              ↓ API Calls
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│                FastAPI (Railway/Fly.io/GCP)                  │
│              https://api.yourdomain.com                      │
└─────────────────────────────────────────────────────────────┘
                    ↓                    ↓
        ┌───────────────────┐    ┌──────────────────┐
        │   Supabase        │    │  Supabase        │
        │   PostgreSQL      │    │  Storage         │
        │   (Database)      │    │  (Images)        │
        └───────────────────┘    └──────────────────┘
                    ↓
        ┌───────────────────┐
        │  Background Jobs  │
        │  (Railway Cron)   │
        │  or Upstash       │
        └───────────────────┘
```

### 플랫폼 선택

| 구분 | 추천 | 대안 | 비용 (월) |
|-----|-----|-----|----------|
| **Frontend** | Vercel | Netlify, Cloudflare Pages | 무료 ~ $20 |
| **Backend** | Railway | Fly.io, Google Cloud Run | $5 ~ $20 |
| **Database** | Supabase | Railway PostgreSQL, Neon | 무료 ~ $25 |
| **Storage** | Supabase Storage | AWS S3, Cloudflare R2 | 무료 ~ $5 |
| **Scheduler** | Railway Cron | Upstash QStash, AWS Lambda | $5 ~ $10 |
| **Monitoring** | Sentry | LogRocket, Better Stack | 무료 ~ $26 |

**총 예상 비용**: $10~$106/월 (무료 티어 활용 시 $0~$30)

---

## 📅 Phase별 로드맵

---

## 🔷 Phase 1: 기반 준비 (1-2주)

### 1.1 데이터베이스 마이그레이션 준비

**목표**: SQLite → PostgreSQL 스키마 변환

**작업**:
- [ ] Supabase 프로젝트 생성
- [ ] PostgreSQL 스키마 작성 (`schema.sql` 변환)
- [ ] 마이그레이션 스크립트 작성
  ```python
  # backend/migrate_to_postgres.py
  # SQLite → PostgreSQL 데이터 이전
  ```
- [ ] 데이터 타입 변환 처리
  - SQLite `INTEGER` → PostgreSQL `SERIAL`
  - SQLite `DATETIME` → PostgreSQL `TIMESTAMP`
  - SQLite `BOOLEAN` → PostgreSQL `BOOLEAN`
- [ ] 외래키 및 인덱스 재생성

**주의사항**:
- SQLite의 `AUTOINCREMENT`는 PostgreSQL의 `SERIAL` 또는 `IDENTITY`로 변환
- JSON 컬럼은 PostgreSQL `JSONB` 타입 사용 (성능 향상)
- 트랜잭션 처리 로직 확인

**검증**:
```bash
# 로컬에서 PostgreSQL 테스트
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test postgres:15
python migrate_to_postgres.py --test
```

---

### 1.2 Database 레이어 추상화

**목표**: SQLite/PostgreSQL 모두 지원하는 구조

**작업**:
- [ ] `database/db.py` 리팩토링
  ```python
  # 기존: SQLite 직접 사용
  import sqlite3

  # 변경: SQLAlchemy ORM 사용
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  ```
- [ ] SQLAlchemy 모델 정의
  ```python
  # backend/database/models.py
  from sqlalchemy.ext.declarative import declarative_base
  Base = declarative_base()

  class MonitoredProduct(Base):
      __tablename__ = 'monitored_products'
      # ...
  ```
- [ ] Repository 패턴 적용 (이미 일부 구현됨)
  ```python
  # backend/database/repositories/product_repository.py
  ```
- [ ] 환경별 DB URL 설정
  ```python
  # .env.local (로컬)
  DATABASE_URL=sqlite:///./monitoring.db

  # .env.production (배포)
  DATABASE_URL=postgresql://user:pass@host:5432/dbname
  ```

**파일 구조**:
```
backend/database/
├── models.py              # SQLAlchemy 모델
├── connection.py          # DB 연결 관리
├── repositories/          # 데이터 접근 레이어
│   ├── product_repository.py
│   ├── order_repository.py
│   └── ...
└── migrations/            # Alembic 마이그레이션
    └── versions/
```

**검증**:
- 로컬에서 SQLite로 정상 동작
- Docker PostgreSQL로 정상 동작
- 모든 API 엔드포인트 테스트 통과

---

### 1.3 이미지 저장소 전환

**목표**: 로컬 파일 시스템 → Supabase Storage

**작업**:
- [ ] Supabase Storage 버킷 생성
  ```javascript
  // Supabase Dashboard
  Create bucket: 'product-images' (public)
  Create bucket: 'detail-pages' (public)
  ```
- [ ] 이미지 업로드 헬퍼 함수
  ```python
  # backend/utils/storage.py
  from supabase import create_client

  def upload_image(file_path: str, bucket: str):
      supabase = create_client(url, key)
      with open(file_path, 'rb') as f:
          res = supabase.storage.from_(bucket).upload(
              file=f,
              path=file_path,
              file_options={"content-type": "image/jpeg"}
          )
      return res.get('publicUrl')
  ```
- [ ] 기존 이미지 마이그레이션 스크립트
  ```python
  # backend/migrate_images_to_supabase.py
  # /supabase-images/* → Supabase Storage
  ```
- [ ] URL 패턴 변경
  ```python
  # Before: http://localhost:8000/supabase-images/1_흰밥/image.jpg
  # After:  https://xxx.supabase.co/storage/v1/object/public/product-images/1_흰밥/image.jpg
  ```
- [ ] 썸네일 다운로드 로직 수정
  ```python
  # backend/api/monitoring.py - save_thumbnail
  # 로컬 저장 → Supabase Storage 업로드
  ```

**주의사항**:
- Supabase Storage 무료 티어: 1GB
- 이미지 최적화 필요 (리사이징, WebP 변환)
- CDN 캐싱 설정

---

### 1.4 환경 변수 관리

**작업**:
- [ ] 환경별 설정 파일 분리
  ```
  .env.local          # 로컬 개발
  .env.development    # 개발 서버
  .env.production     # 프로덕션
  ```
- [ ] Pydantic Settings 사용
  ```python
  # backend/config.py
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      database_url: str
      openai_api_key: str
      playauto_email: str
      playauto_password: str
      supabase_url: str
      supabase_key: str

      class Config:
          env_file = ".env"

  settings = Settings()
  ```
- [ ] 민감 정보 암호화
  ```python
  # 플레이오토 비밀번호 등은 KMS/Vault 사용 권장
  ```

---

## 🔷 Phase 2: 백엔드 배포 (1-2주)

### 2.1 FastAPI 프로덕션 준비

**작업**:
- [ ] Gunicorn + Uvicorn workers 설정
  ```python
  # backend/gunicorn_conf.py
  workers = 4
  worker_class = "uvicorn.workers.UvicornWorker"
  bind = "0.0.0.0:8000"
  ```
- [ ] CORS 설정 업데이트
  ```python
  # backend/main.py
  origins = [
      "https://yourdomain.com",
      "https://*.vercel.app",
  ]
  app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
  ```
- [ ] Health check 엔드포인트 강화
  ```python
  @app.get("/health")
  async def health():
      # DB 연결 확인
      # 외부 API 연결 확인 (Playauto, OpenAI)
      return {"status": "healthy", "database": "ok", "apis": "ok"}
  ```
- [ ] 로깅 설정
  ```python
  # backend/logger.py
  import logging
  from logging.handlers import RotatingFileHandler

  # JSON 로그 포맷 (Sentry 연동)
  ```
- [ ] 에러 핸들링 미들웨어
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      # Sentry 전송
      # 사용자 친화적 에러 메시지 반환
  ```

---

### 2.2 Railway 배포

**Railway 선택 이유**:
- ✅ 간단한 배포 (GitHub 연동)
- ✅ PostgreSQL 기본 제공
- ✅ Cron Jobs 지원
- ✅ 무료 티어 ($5 크레딧/월)

**작업**:
- [ ] `railway.json` 설정
  ```json
  {
    "$schema": "https://railway.app/railway.schema.json",
    "build": {
      "builder": "NIXPACKS",
      "buildCommand": "pip install -r requirements.txt"
    },
    "deploy": {
      "startCommand": "gunicorn -c gunicorn_conf.py main:app",
      "restartPolicyType": "ON_FAILURE",
      "healthcheckPath": "/health"
    }
  }
  ```
- [ ] `Procfile` (또는 `nixpacks.toml`)
  ```
  web: gunicorn -c gunicorn_conf.py main:app
  ```
- [ ] 환경 변수 설정 (Railway Dashboard)
  ```
  DATABASE_URL=postgresql://...
  OPENAI_API_KEY=sk-...
  PLAYAUTO_EMAIL=...
  PLAYAUTO_PASSWORD=...
  SUPABASE_URL=https://...
  SUPABASE_KEY=...
  ENVIRONMENT=production
  ```
- [ ] GitHub 연동 및 자동 배포
- [ ] 커스텀 도메인 설정 (선택)
  ```
  api.yourdomain.com → Railway 앱
  ```

**대안 (Fly.io)**:
```toml
# fly.toml
app = "onbaek-ai-backend"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8000"

[[services]]
  http_checks = []
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
```

---

### 2.3 스케줄러 분리

**문제점**: APScheduler는 단일 프로세스에서만 동작

**해결 방법 1: Railway Cron Jobs**
```json
// railway.json
{
  "deploy": {
    "cron": [
      {
        "schedule": "*/10 * * * *",  // 10분마다
        "command": "python -m monitor.product_monitor"
      },
      {
        "schedule": "0 */6 * * *",   // 6시간마다
        "command": "python -m playauto.scheduler"
      },
      {
        "schedule": "0 2 * * *",     // 매일 새벽 2시
        "command": "python -m backup.scheduler"
      }
    ]
  }
}
```

**해결 방법 2: Upstash QStash (권장)**
```python
# backend/scheduler/qstash_tasks.py
from upstash_qstash import QStash

client = QStash(os.getenv("QSTASH_TOKEN"))

# 10분마다 실행
client.publish_json(
    url="https://api.yourdomain.com/cron/monitor-products",
    body={},
    schedule="*/10 * * * *"
)
```

**작업**:
- [ ] 스케줄러 작업을 독립 엔드포인트로 분리
  ```python
  # backend/api/cron.py
  from fastapi import APIRouter, Header, HTTPException

  router = APIRouter(prefix="/cron", tags=["Cron"])

  @router.post("/monitor-products")
  async def monitor_products(authorization: str = Header(None)):
      # Cron 시크릿 검증
      if authorization != f"Bearer {os.getenv('CRON_SECRET')}":
          raise HTTPException(401)

      # 상품 모니터링 실행
      from monitor.product_monitor import check_all_products
      await check_all_products()
      return {"status": "ok"}
  ```
- [ ] Railway Cron 또는 Upstash 설정
- [ ] 실행 로그 DB 저장
- [ ] 실패 시 알림 (Slack/Discord)

---

## 🔷 Phase 3: 프론트엔드 배포 (1주)

### 3.1 Next.js 프로덕션 빌드

**작업**:
- [ ] API URL 환경 변수 설정
  ```env
  # .env.production
  NEXT_PUBLIC_API_URL=https://api.yourdomain.com
  ```
- [ ] 프론트엔드 코드 수정
  ```typescript
  // 기존
  const API_BASE_URL = 'http://localhost:8000';

  // 변경
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  ```
- [ ] 이미지 최적화 설정
  ```javascript
  // next.config.js
  module.exports = {
    images: {
      domains: ['xxx.supabase.co'],  // Supabase Storage
      formats: ['image/avif', 'image/webp'],
    },
  }
  ```
- [ ] Static export 여부 결정
  ```javascript
  // Static export (GitHub Pages 가능)
  output: 'export'

  // SSR (Vercel/Netlify 권장)
  // output 설정 없음
  ```

---

### 3.2 Vercel 배포

**Vercel 선택 이유**:
- ✅ Next.js 최적화
- ✅ 자동 HTTPS/CDN
- ✅ GitHub 연동
- ✅ 무료 티어 (Hobby)

**작업**:
- [ ] Vercel 프로젝트 생성
- [ ] GitHub 레포지토리 연동
- [ ] 환경 변수 설정
  ```
  NEXT_PUBLIC_API_URL=https://api.yourdomain.com
  ```
- [ ] 빌드 설정
  ```json
  // vercel.json
  {
    "buildCommand": "npm run build",
    "outputDirectory": ".next",
    "framework": "nextjs"
  }
  ```
- [ ] 커스텀 도메인 연결
  ```
  yourdomain.com → Vercel 프로젝트
  ```
- [ ] Git push 시 자동 배포 확인

---

## 🔷 Phase 4: 통합 및 테스트 (1주)

### 4.1 End-to-End 테스트

**작업**:
- [ ] 프론트엔드 → 백엔드 연결 확인
- [ ] 모든 주요 기능 테스트
  - [ ] 상품 수집
  - [ ] 모니터링
  - [ ] AI 상세페이지 생성
  - [ ] 플레이오토 주문 동기화
  - [ ] 송장 업로드
  - [ ] 알림 전송
- [ ] 성능 테스트
  ```bash
  # Apache Bench
  ab -n 1000 -c 10 https://api.yourdomain.com/api/products
  ```
- [ ] 부하 테스트
  ```bash
  # k6
  k6 run load-test.js
  ```

---

### 4.2 모니터링 및 로깅

**작업**:
- [ ] Sentry 설정 (에러 추적)
  ```python
  # backend/main.py
  import sentry_sdk
  sentry_sdk.init(
      dsn=os.getenv("SENTRY_DSN"),
      traces_sample_rate=0.1,
  )
  ```
- [ ] Uptime 모니터링 (UptimeRobot, Better Uptime)
  - 1분마다 `/health` 체크
  - 다운 시 이메일/Slack 알림
- [ ] 로그 수집 (Better Stack, Datadog)
  ```python
  # JSON 로그 포맷으로 전환
  import json
  import logging

  class JsonFormatter(logging.Formatter):
      def format(self, record):
          return json.dumps({
              "time": self.formatTime(record),
              "level": record.levelname,
              "message": record.getMessage(),
              "module": record.module,
          })
  ```

---

### 4.3 보안 강화

**작업**:
- [ ] API Rate Limiting
  ```python
  from slowapi import Limiter, _rate_limit_exceeded_handler
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter

  @router.post("/generate-content")
  @limiter.limit("10/minute")  # 1분에 10회
  async def generate_content(request: Request):
      ...
  ```
- [ ] HTTPS 강제
  ```python
  from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
  app.add_middleware(HTTPSRedirectMiddleware)
  ```
- [ ] SQL Injection 방지 (SQLAlchemy ORM 사용으로 기본 방지)
- [ ] XSS 방지 (프론트엔드에서 `dangerouslySetInnerHTML` 최소화)
- [ ] CSRF 토큰 (필요 시)
- [ ] API 키 로테이션 전략

---

## 🔷 Phase 5: 최적화 및 운영 (지속)

### 5.1 성능 최적화

**백엔드**:
- [ ] DB 쿼리 최적화
  - N+1 문제 해결 (Eager Loading)
  - 인덱스 추가
  - 쿼리 캐싱
- [ ] Redis 캐싱
  ```python
  # 상품 목록, 통계 등 자주 조회되는 데이터 캐싱
  import redis
  cache = redis.Redis(host='...', port=6379, decode_responses=True)

  @router.get("/products")
  async def get_products():
      cached = cache.get("products:list")
      if cached:
          return json.loads(cached)

      products = db.get_selling_products()
      cache.setex("products:list", 300, json.dumps(products))  # 5분 캐싱
      return products
  ```
- [ ] 비동기 처리 강화
  ```python
  # 느린 작업은 백그라운드로
  from fastapi import BackgroundTasks

  @router.post("/generate-detail-page")
  async def generate(product_id: int, background_tasks: BackgroundTasks):
      background_tasks.add_task(generate_with_ai, product_id)
      return {"status": "processing"}
  ```

**프론트엔드**:
- [ ] 이미지 Lazy Loading
- [ ] Code Splitting
  ```typescript
  const DetailPage = dynamic(() => import('@/components/pages/DetailPage'), {
    loading: () => <LoadingSpinner />
  });
  ```
- [ ] React Query로 API 캐싱
  ```typescript
  import { useQuery } from '@tanstack/react-query';

  const { data, isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
    staleTime: 5 * 60 * 1000,  // 5분
  });
  ```

---

### 5.2 CI/CD 파이프라인

**작업**:
- [ ] GitHub Actions 설정
  ```yaml
  # .github/workflows/deploy.yml
  name: Deploy

  on:
    push:
      branches: [main]

  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Run tests
          run: |
            cd backend
            pip install -r requirements.txt
            pytest

    deploy-backend:
      needs: test
      runs-on: ubuntu-latest
      steps:
        - name: Deploy to Railway
          run: railway up

    deploy-frontend:
      needs: test
      runs-on: ubuntu-latest
      steps:
        - name: Deploy to Vercel
          run: vercel --prod
  ```
- [ ] 자동 테스트 실행
- [ ] 배포 전 승인 프로세스 (선택)
- [ ] Rollback 전략

---

### 5.3 백업 및 복구

**작업**:
- [ ] Supabase 자동 백업 활성화
- [ ] 수동 백업 스크립트
  ```bash
  # backup.sh
  pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql
  # S3 업로드
  aws s3 cp backup-*.sql s3://backups/
  ```
- [ ] 복구 테스트
- [ ] 재해 복구 계획 (Disaster Recovery Plan)

---

## 📋 체크리스트 요약

### Phase 1: 기반 준비
- [ ] Supabase 프로젝트 생성
- [ ] PostgreSQL 스키마 마이그레이션
- [ ] SQLAlchemy ORM 전환
- [ ] Supabase Storage 설정
- [ ] 이미지 마이그레이션
- [ ] 환경 변수 설정

### Phase 2: 백엔드 배포
- [ ] FastAPI 프로덕션 설정
- [ ] Railway/Fly.io 배포
- [ ] 스케줄러 분리 (Cron/QStash)
- [ ] Health check 구현
- [ ] 로깅 설정

### Phase 3: 프론트엔드 배포
- [ ] Next.js 빌드 설정
- [ ] Vercel 배포
- [ ] API URL 환경 변수
- [ ] 커스텀 도메인

### Phase 4: 통합 테스트
- [ ] E2E 테스트
- [ ] 성능 테스트
- [ ] Sentry 설정
- [ ] Uptime 모니터링
- [ ] 보안 강화

### Phase 5: 최적화
- [ ] DB 쿼리 최적화
- [ ] Redis 캐싱
- [ ] 프론트엔드 최적화
- [ ] CI/CD 파이프라인
- [ ] 백업 전략

---

## 💰 예상 비용 (월간)

| 서비스 | 티어 | 비용 | 비고 |
|--------|------|------|------|
| **Vercel** | Hobby | $0 | 100GB 대역폭 |
| **Railway** | Developer | $5 | 백엔드 + Cron |
| **Supabase** | Free | $0 | 500MB DB, 1GB Storage |
| **Upstash Redis** | Free | $0 | 10,000 커맨드/일 |
| **Sentry** | Developer | $0 | 5,000 에러/월 |
| **Better Uptime** | Free | $0 | 1 모니터 |
| **총계** | - | **$5/월** | - |

**스케일업 시 (월 10만 방문자 기준)**:
- Vercel Pro: $20
- Railway: $20 (더 많은 리소스)
- Supabase Pro: $25
- **총계: $65/월**

---

## 🎓 학습 리소스

### 필수 문서
- [Supabase Docs](https://supabase.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Vercel Docs](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

### 참고 프로젝트
- [FastAPI + PostgreSQL Template](https://github.com/tiangolo/full-stack-fastapi-postgresql)
- [Next.js + Supabase Starter](https://github.com/vercel/next.js/tree/canary/examples/with-supabase)

---

## 🚨 주의사항

1. **데이터 마이그레이션**: 반드시 백업 후 진행
2. **환경 변수**: 프로덕션 키는 별도 관리
3. **API 키 비용**: OpenAI, Playauto 사용량 모니터링
4. **스케줄러**: 중복 실행 방지 (분산 락 사용)
5. **로그 크기**: 로그 로테이션 설정 필수
6. **Supabase 무료 티어**: 500MB 제한 (모니터링 필요)

---

## 📞 다음 단계

이 로드맵을 기반으로:

1. **Phase 1부터 순차 진행**
2. **단계별 테스트 철저히**
3. **문제 발생 시 롤백 준비**
4. **배포 후 모니터링 지속**

질문이나 지원이 필요하면 언제든 요청하세요!
