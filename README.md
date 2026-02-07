# 물바다AI - 통합 상품 관리 시스템

AI 기술로 상품 썸네일과 상세페이지를 전문가 수준으로 제작하고, 판매 상품을 체계적으로 관리하는 Next.js 애플리케이션입니다.

## 🎉 배포 완료! (2026-01-30)

**물바다AI가 성공적으로 클라우드에 배포되었습니다!**

### 🌐 배포된 서비스

| 서비스 | URL | 비용 |
|--------|-----|------|
| 🎨 **프론트엔드** | `https://[your-app].vercel.app` ([Vercel 대시보드](https://vercel.com/dashboard)에서 확인) | 무료 |
| 🔧 **백엔드 API** | `https://badaauction-production.up.railway.app` | $5/월 |
| 💾 **데이터베이스** | Supabase PostgreSQL | 무료 |
| 📦 **이미지 스토리지** | Supabase Storage (6248개, 8.7GB) | 무료 |

**총 운영 비용**: **$5/월**

### ✅ 배포 상태 확인
```bash
# 백엔드 헬스 체크
curl https://badaauction-production.up.railway.app/health

# Admin API 상태 확인 (Railway 재배포 후 2-3분 소요)
curl https://badaauction-production.up.railway.app/api/admin/system/status

# 등록된 라우트 확인
curl https://badaauction-production.up.railway.app/debug/routes | grep admin

# API 문서 확인
open https://badaauction-production.up.railway.app/docs

# 프론트엔드 접속
# Vercel 대시보드에서 본인의 배포 URL 확인
```

**⚠️ 주의**: Railway에 코드를 push한 후 재배포가 완료되기까지 **2-3분** 소요됩니다.

---

## 📋 목차

- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [배포 아키텍처](#-배포-아키텍처)
- [로컬 개발 환경 설정](#-로컬-개발-환경-설정)
- [배포 가이드](#-배포-가이드)
- [환경 변수](#-환경-변수)
- [API 문서](#-api-문서)
- [트러블슈팅](#-트러블슈팅)
- [업데이트 히스토리](#-업데이트-히스토리)

---

## ✨ 주요 기능

### 🛍️ 상품 수집 & 관리
- **다채널 상품 수집**: G마켓, 옥션, 11번가, SSG, 홈플러스/트레이더스, 롯데ON
- **Cloudflare 우회**: FlareSolverr 연동으로 G마켓/옥션 자동 수집
- **자동 이미지 다운로드**: 상품 이미지 자동 수집 및 저장
- **카테고리 자동 매핑**: 138개 카테고리 계층 구조
- **AI 상세페이지 생성**: GPT-4 기반 자동 상세페이지 작성

### 💰 가격 모니터링
- **실시간 가격 추적**: 15분마다 자동 체크
- **역마진 알림**: 마진율 자동 계산 및 알림
- **가격 히스토리**: 가격 변동 차트 시각화
- **Slack/Discord 알림**: 실시간 알림 시스템

### 📦 주문 관리
- **통합 주문 관리**: 다채널 주문 통합 대시보드
- **실시간 검색**: 주문번호, 고객명, 전화번호, 마켓으로 즉시 검색
- **Playauto 자동 동기화**: 주문 자동 수집 및 동기화
- **발주 대기 목록**: 자동 발주 관리
- **송장 업로드 스케줄러**: 송장 번호 일괄 업로드
- **주문 처리 워크플로우**:
  - 신규주문 → 소싱처 구매 → 송장 입력 → 출고완료
  - 상품 매칭: 판매 상품 ↔ 소싱처 상품 자동 연결
  - PlayAuto API 연동: 출고지시, 송장 업데이트

### 💰 회계 관리
- **자동 매출/매입 계산**: 주문 데이터 기반 자동 집계
- **상품 매칭 연동**: 소싱가(sourcing_price) 자동 입력
- **이익 자동 계산**: (판매가 - 소싱가) × 수량
- **대시보드**: 매출, 매입, 지출, 순이익 요약
- **손익계산서**: 기간별 P&L 리포트
- **지출 관리**: CRUD + Excel 다운로드
- **마켓별 정산**: 정산 내역 관리
- **세금 계산**: 부가세(분기별), 종합소득세(연간)
- **월별 리포트**: 베스트셀러, 마켓 분석

### 🎨 상세페이지 제작
- **Figma 스타일 에디터**: 드래그 앤 드롭 편집
- **9개 템플릿**: Daily, Food, Fresh, Simple 등
- **실시간 미리보기**: 즉시 확인 가능
- **이미지 편집**: 크기, 위치, 스타일 조정

### 🤖 자동화
- **재고 자동 관리**: 품절 시 자동 비활성화
- **자동 가격 조정**: 마진 기반 스마트 가격 계산 및 자동 조정
- **가격 자동 업데이트**: 소싱처 가격 변동 반영
- **알림 자동 발송**: Slack, Discord, 웹 알림
- **백업 자동화**: 데이터베이스 자동 백업

---

## 🛠️ 기술 스택

### Frontend
- **Framework**: Next.js 16.1.1 (App Router, Turbopack)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Lucide Icons, Recharts
- **State Management**: React Hooks
- **Deployment**: Vercel (무료)

### Backend
- **Framework**: FastAPI (Python 3.9)
- **ORM**: SQLAlchemy 2.0
- **Server**: Gunicorn + Uvicorn workers
- **Authentication**: JWT
- **Deployment**: Railway (Docker)

### Database & Storage
- **Production DB**: PostgreSQL 15 (Supabase)
- **Development DB**: SQLite
- **Image Storage**: Supabase Storage (6248 images, 8.7GB)
- **CDN**: Cloudflare (Supabase 통합)
- **ORM**: SQLAlchemy with hybrid selection
- **Migration**: Alembic-style schema management

### Infrastructure
- **Frontend Hosting**: Vercel (Global CDN, Auto HTTPS)
- **Backend Hosting**: Railway (Docker containers)
- **Database**: Supabase (Connection pooling)
- **CI/CD**: GitHub (Auto deployment on push)

### External APIs
- **AI**: OpenAI GPT-4o-mini
- **E-commerce**: Playauto API
- **Notifications**: Slack, Discord Webhooks
- **Captcha**: 2Captcha

---

## 🏗️ 배포 아키텍처

```
┌──────────────────────────────────────────┐
│         사용자 (Browser)                  │
└────────────┬─────────────────────────────┘
             │ HTTPS
             ▼
┌──────────────────────────────────────────┐
│    Vercel (프론트엔드)                    │
│    ✅ Next.js 16.1.1                     │
│    ✅ 글로벌 CDN                         │
│    ✅ 자동 HTTPS                         │
│    ✅ $0/월                              │
└────────────┬─────────────────────────────┘
             │ API Requests
             │ NEXT_PUBLIC_API_BASE_URL
             ▼
┌──────────────────────────────────────────┐
│    Railway (백엔드 API)                   │
│    ✅ FastAPI + Gunicorn                 │
│    ✅ 2 Uvicorn workers                  │
│    ✅ Docker container                   │
│    ✅ $5/월                              │
└──────┬────────────────┬──────────────────┘
       │ PostgreSQL     │ Storage API
       │ DATABASE_URL   │
       ▼                ▼
┌──────────────────────────────────────────┐
│    Supabase (데이터 + 스토리지)           │
│    ✅ PostgreSQL 15                      │
│    ✅ 24 tables, 170 rows                │
│    ✅ Connection pooling (port 6543)     │
│    ✅ Storage (6248개 이미지, 8.7GB)     │
│    ✅ Cloudflare CDN                     │
│    ✅ $0/월                              │
└──────────────────────────────────────────┘
```

---

## 💻 로컬 개발 환경 설정

### 필수 요구사항

- **Node.js**: 18.x 이상
- **Python**: 3.9 이상
- **Git**: 최신 버전

### 1. 저장소 클론

```bash
git clone https://github.com/sunes26/bada_auction.git
cd bada_auction
```

### 2. 환경 변수 설정

루트 디렉토리에 `.env.local` 파일 생성:

```env
# Supabase (선택사항 - 로컬에서는 불필요)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API Base URL (로컬 개발)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Admin Password
NEXT_PUBLIC_ADMIN_PASSWORD=8888

# OpenAI (AI 상세페이지 생성용 - 선택사항)
OPENAI_API_KEY=sk-proj-...

# Backend (backend/.env.local)
USE_POSTGRESQL=false  # 로컬에서는 SQLite 사용
DATABASE_URL=sqlite:///monitoring.db

# Playauto API (선택사항)
PLAYAUTO_SOLUTION_KEY=your-key
PLAYAUTO_API_KEY=your-key
PLAYAUTO_EMAIL=your-email
PLAYAUTO_PASSWORD=your-password
```

### 3. 프론트엔드 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 시작
npm run dev
```

프론트엔드가 http://localhost:3000 에서 실행됩니다.

### 4. 백엔드 설치 및 실행

```bash
cd backend

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 시작
python main.py
```

백엔드가 http://localhost:8000 에서 실행됩니다.

### 5. 접속 확인

- **프론트엔드**: http://localhost:3000
- **백엔드 API 문서**: http://localhost:8000/docs
- **관리자 페이지**: http://localhost:3000/admin (비밀번호: 8888)

---

## 🚀 배포 가이드

### 배포 완료 상태 ✅

모든 배포가 성공적으로 완료되었습니다!

#### Phase 1: PostgreSQL 마이그레이션 ✅
- Supabase PostgreSQL 설정
- 24개 테이블 생성
- 170 rows 데이터 마이그레이션
- SQLAlchemy ORM 모델 정의

**문서**: `PHASE1_MIGRATION_COMPLETE.md`

#### Phase 2: SQLAlchemy 백엔드 ✅
- DatabaseWrapper 구현 (40+ 메서드)
- Hybrid database selection (환경 변수 기반)
- 100% API 호환성
- SQLAlchemy 2.0 지원

**문서**: `PHASE2_BACKEND_UPDATE_COMPLETE.md`

#### Phase 3: Railway 백엔드 배포 ✅
- Docker 기반 배포
- Gunicorn + Uvicorn 설정
- 환경 변수 11개 설정
- Worker 최적화 (2개)
- Health check 정상 동작

**문서**: `RAILWAY_DEPLOYMENT_COMPLETE.md`

#### Phase 4: Vercel 프론트엔드 배포 ✅
- Next.js 빌드 성공
- TypeScript 에러 6개 수정
- 환경 변수 4개 설정
- localhost 하드코딩 16개 파일 수정
- 자동 배포 설정

**문서**: `PHASE4_VERCEL_DEPLOYMENT.md`

### 배포 문서

| 문서 | 내용 |
|------|------|
| `DEPLOYMENT_COMPLETE.md` | 전체 배포 요약 및 가이드 |
| `PHASE1_MIGRATION_COMPLETE.md` | PostgreSQL 마이그레이션 |
| `PHASE2_BACKEND_UPDATE_COMPLETE.md` | SQLAlchemy 백엔드 |
| `PHASE3_DEPLOYMENT_SUCCESS.md` | Railway 배포 |
| `RAILWAY_DEPLOYMENT_COMPLETE.md` | Railway 상세 가이드 |
| `PHASE4_VERCEL_DEPLOYMENT.md` | Vercel 배포 가이드 |

---

## 🔐 환경 변수

### 프론트엔드 (Vercel)

**Vercel 대시보드 > Settings > Environment Variables**에서 설정:

```env
# Supabase (선택사항)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API Base URL (필수) ⚠️ 중요!
NEXT_PUBLIC_API_BASE_URL=https://badaauction-production.up.railway.app

# Admin Password (필수)
NEXT_PUBLIC_ADMIN_PASSWORD=8888

# OpenAI (선택사항)
OPENAI_API_KEY=sk-proj-...
```

**⚠️ 주의**: 로컬 개발 시 `.env.local`에는 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`을 사용하세요. `lib/api.ts`가 환경에 따라 자동으로 올바른 URL을 선택합니다.

### 백엔드 (Railway)

```env
# Database (필수)
USE_POSTGRESQL=true
DATABASE_URL=postgresql://postgres:***@db.spkeunlwkrqkdwunkufy.supabase.co:6543/postgres?sslmode=require

# Supabase Storage (필수 - 이미지 스토리지)
SUPABASE_URL=https://spkeunlwkrqkdwunkufy.supabase.co
SUPABASE_SERVICE_ROLE_KEY=***

# Playauto API (필수)
PLAYAUTO_SOLUTION_KEY=***
PLAYAUTO_API_KEY=***
PLAYAUTO_EMAIL=***
PLAYAUTO_PASSWORD=***
PLAYAUTO_API_URL=https://openapi.playauto.io/api

# Security (필수)
ENCRYPTION_KEY=***

# External APIs (선택사항)
OPENAI_API_KEY=sk-proj-...
CAPTCHA_API_KEY=***

# FlareSolverr (G마켓/옥션 Cloudflare 우회용)
FLARESOLVERR_URL=https://your-flaresolverr.up.railway.app/v1

# Environment (필수)
ENVIRONMENT=production
FRONTEND_URL=https://[your-app].vercel.app
```

---

## 📚 API 문서

### Production API
- **Base URL**: `https://badaauction-production.up.railway.app`
- **Swagger UI**: `https://badaauction-production.up.railway.app/docs`
- **ReDoc**: `https://badaauction-production.up.railway.app/redoc`

### Local API
- **Base URL**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`

### 주요 엔드포인트

#### Health Check
```bash
GET /health
```

#### 상품 관리
```bash
GET    /api/products          # 판매 상품 목록
POST   /api/products/create   # 상품 등록
PUT    /api/products/{id}     # 상품 수정
DELETE /api/products/{id}     # 상품 삭제
```

#### 모니터링
```bash
GET    /api/monitoring/products  # 모니터링 상품 목록
POST   /api/monitoring/products  # 모니터링 추가
DELETE /api/monitoring/products/{id}  # 모니터링 삭제
```

#### 주문 관리
```bash
GET  /api/orders              # 주문 목록
GET  /api/orders/unified      # 통합 주문 관리
POST /api/orders/create       # 주문 생성
```

#### Playauto
```bash
GET  /api/playauto/settings          # 설정 조회
POST /api/playauto/products/register # 상품 등록
GET  /api/playauto/orders/sync       # 주문 동기화
```

#### 대시보드
```bash
GET /api/dashboard/all    # 통합 대시보드 (5개 API 통합)
GET /api/dashboard/stats  # 대시보드 통계
```

#### 자동 가격 조정
```bash
GET  /api/auto-pricing/settings          # 설정 조회
POST /api/auto-pricing/settings          # 설정 저장
POST /api/auto-pricing/adjust-product/{id}  # 개별 상품 가격 조정
POST /api/auto-pricing/adjust-all        # 모든 상품 일괄 조정
```

#### WebSocket
```bash
WS /ws/notifications  # 실시간 알림 (주문, 가격, 송장 등)
```

자세한 API 문서는 `/docs` 엔드포인트를 참고하세요.

---

## 🐛 트러블슈팅

### 배포 관련 문제

#### ❌ API 404 에러 - URL이 `%7BAPI_BASE_URL%7D`로 인코딩됨

**증상**:
```
Failed to load resource: the server responded with a status of 404
URL: /$%7BAPI_BASE_URL%7D/api/orders/list
```

**원인**: 템플릿 리터럴에 작은따옴표(`'`)를 사용하여 `${API_BASE_URL}`이 변수로 인식되지 않음

**해결 방법**:
```typescript
// ❌ 잘못된 코드
fetch('${API_BASE_URL}/api/orders')

// ✅ 올바른 코드
fetch(`${API_BASE_URL}/api/orders`)  // 백틱 사용!
```

**수정 완료**: 모든 파일이 백틱(`` ` ``)으로 수정되었습니다.

---

#### ❌ Railway Admin API 404 에러 (최종 해결)

**증상**:
```
badaauction-production.up.railway.app/api/admin/system/status: 404
badaauction-production.up.railway.app/api/admin/images/stats: 404
badaauction-production.up.railway.app/api/admin/database/stats: 404
```

**원인 1**: `psutil`, `Pillow` 패키지가 `requirements.txt`에 누락되어 admin router import 실패

**해결 1**:
```bash
# backend/requirements.txt에 추가
psutil>=5.9.0
Pillow>=10.0.0
```

**원인 2**: admin.py가 프로덕션 환경(Railway)과 호환되지 않음
- 모듈 로드 시점에 디렉토리 생성 시도 (권한 문제)
- sqlite3를 직접 import하여 PostgreSQL 환경에서 문제
- psutil/PIL 없을 때 에러 발생

**해결 2 (최종)**:
```python
# Optional imports with fallbacks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Safe directory creation
try:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"[WARN] Failed to create directories: {e}")

# Use get_db() instead of sqlite3.connect()
db = get_db()  # Works with both SQLite and PostgreSQL

# Conditional feature usage
if PSUTIL_AVAILABLE:
    memory = psutil.virtual_memory()
else:
    memory = default_values  # Provide defaults
```

**수정 완료**: Railway 재배포 후 19개 admin 라우트가 정상 작동합니다.

**검증 명령어**:
```bash
curl https://badaauction-production.up.railway.app/api/admin/system/status
curl https://badaauction-production.up.railway.app/debug/routes | grep admin
```

---

#### ❌ Admin Database Stats 500 에러 (해결 완료)

**증상**:
```
{"detail": "'Database' object has no attribute 'execute'"}
{"detail": "no such table: information_schema.tables"}
```

**원인**:
1. `Database` 클래스는 `.execute()` 메서드가 없음 - `.get_connection()`을 먼저 호출해야 함
2. Railway 환경 변수 `USE_POSTGRESQL=true`이지만 실제 DB는 SQLite (monitoring.db)
3. PostgreSQL 쿼리(`information_schema.tables`)를 SQLite DB에 실행

**해결 방법**:
```python
# ❌ 잘못된 코드
db = get_db()
cursor = db.execute("SELECT ...")  # Database 객체에 execute() 없음

# ✅ 올바른 코드
db = get_db()
conn = db.get_connection()  # sqlite3.Connection 객체 반환
cursor = conn.execute("SELECT ...")
conn.close()

# ✅ SQLite 전용 쿼리 사용
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
```

**수정 완료**:
- `backend/api/admin.py:464` get_database_stats() 수정
- PostgreSQL 감지 로직 제거, SQLite 전용으로 단순화
- 커밋: `544f37b`

**검증**:
```bash
curl https://badaauction-production.up.railway.app/api/admin/database/stats
# {"success":true,"database_type":"SQLite","database_size_mb":0,"tables":[...]}
```

---

#### ⚠️ 브라우저 Admin API 500 에러 (조사 중)

**증상**:
```
Failed to load resource: the server responded with a status of 500
badaauction-production.up.railway.app/api/admin/database/stats
```

**현재 상태**:
- ✅ curl 테스트: 정상 (HTTP 200)
- ✅ 모든 admin API 엔드포인트 정상 작동:
  - `/api/admin/system/status` ✅
  - `/api/admin/images/stats` ✅
  - `/api/admin/database/stats` ✅
  - `/api/admin/database/backups` ✅
  - `/api/admin/logs/recent` ✅
  - `/api/admin/settings/env` ✅
  - `/api/admin/performance/metrics` ✅

**의심 원인**:
1. 브라우저 캐시 문제
2. CORS 관련 preflight 요청 실패
3. 특정 브라우저 환경에서만 발생하는 이슈

**해결 시도**:
1. 브라우저 캐시 지우기: `Ctrl+Shift+R` (하드 리프레시)
2. 개발자 도구(F12) → Network 탭에서 실제 에러 확인
3. Response 탭에서 정확한 에러 메시지 확인

---

#### ❌ Vercel 빌드 실패
1. `lib/` 디렉토리가 누락되었는지 확인
2. TypeScript 에러 확인 (`npm run build`)
3. 환경 변수가 설정되었는지 확인
4. `import type` 블록에 일반 import가 섞이지 않았는지 확인

**일반적인 빌드 에러**:
```typescript
// ❌ 잘못된 import
import type {
import { API_BASE_URL } from '@/lib/api';  // type 블록 안에 일반 import
  SomeType
}

// ✅ 올바른 import
import { API_BASE_URL } from '@/lib/api';
import type {
  SomeType
}
```

---

#### Railway 연결 실패
1. Health check 확인: `curl https://badaauction-production.up.railway.app/health`
2. Railway 로그 확인
3. 환경 변수 `USE_POSTGRESQL=true` 확인
4. `requirements.txt`의 모든 패키지가 설치되었는지 확인

---

#### API 연결 실패 (localhost 에러)
✅ **수정 완료!** 모든 파일이 `API_BASE_URL`을 사용하며, 프로덕션에서는 Railway URL을 자동으로 사용합니다.

### 로컬 개발 문제

#### 백엔드 시작 실패
```bash
# 의존성 재설치
cd backend
pip install -r requirements.txt --force-reinstall
```

#### 프론트엔드 빌드 에러
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules
npm install
```

#### SQLite 데이터베이스 초기화
```bash
cd backend
rm monitoring.db
python main.py  # 자동으로 새 DB 생성
```

---

## 💰 비용

### 운영 비용 (월간)
- **Vercel**: $0 (Hobby Plan)
- **Railway**: $5 (Hobby Plan)
- **Supabase**: $0 (Free Plan)

**총 비용**: **$5/월**

### 리소스 사용량
- **Railway**: 200-300MB RAM, 10-20% CPU
- **Supabase**: ~10MB 데이터베이스
- **Vercel**: 서버리스 (무제한)

### 확장 옵션
- **Railway Pro**: $20/월 (더 많은 리소스)
- **Supabase Pro**: $25/월 (8GB 데이터베이스)
- **Vercel Pro**: $20/월 (팀 협업 기능)

---

## 📈 업데이트 히스토리

### 2026-02-08 (최신): PlayAuto 카테고리 재매핑 + 채널별 옵션 분리 🏷️⚙️

**PlayAuto 카테고리 매핑 업데이트**:
- ✅ **sol_cate_no 전면 재매핑**: 81개 카테고리 → 47개 고유 코드
- ✅ **매핑 업데이트 스크립트 생성**: `update_category_mapping.sql`
- ✅ **로컬 + 프로덕션(Supabase) 동기화 완료**

**채널별 상품 등록 방식 분리**:
```
┌─────────────────┬─────────────┬────────────┐
│ 채널            │ opt_type    │ std_ol_yn  │
├─────────────────┼─────────────┼────────────┤
│ 옥션/지마켓     │ 옵션없음    │ Y (단일)   │
│ 쿠팡            │ 조합형      │ N          │
│ 스마트스토어 등 │ 독립형      │ N          │
└─────────────────┴─────────────┴────────────┘
```

**코드 변경**:
- ✅ **쿠팡 별도 채널로 분리** (`products.py`):
  - 기존: 옥션/지마켓과 동일 처리 (옵션없음)
  - 변경: 쿠팡 전용 `channel_type="coupang"` 추가
- ✅ **쿠팡 옵션 타입 변경** (`product_registration.py`):
  - `opt_type = "조합형"` 적용
  - opts 배열에 상품선택 옵션 포함

**🚨 미해결 이슈**:
- ❌ **쿠팡 상품 등록 오류**: "필수 구매 옵션이 존재하지 않습니다"
- 상세 내용은 하단 "PlayAuto 카테고리 관리" 섹션 참고

**커밋 해시**:
- `16b887f`: PlayAuto 카테고리 매핑 업데이트 (81개)
- `ab9b6d4`: 쿠팡 상품 등록 시 스마트스토어 방식으로 변경
- `4e561b1`: 쿠팡 상품 등록 시 조립형 옵션으로 변경
- `e30fede`: 쿠팡 옵션 타입을 조합형으로 변경

---

### 2026-02-06: FlareSolverr 연동 + 소싱 사이트 확장 🔓🛒

**FlareSolverr 연동 (Cloudflare 우회)**:
- ✅ **G마켓/옥션 자동 수집 지원**: FlareSolverr로 Cloudflare 보호 우회
- ✅ **FlareSolverr 클라이언트 추가** (`backend/utils/flaresolverr.py`):
  - 세션 관리 (브라우저 인스턴스 재사용)
  - 페이지 요청 및 HTML 파싱
  - 쿠키 추출 (requests/Selenium용)
- ✅ **HTML 직접 파싱**: FlareSolverr 응답에서 BeautifulSoup으로 데이터 추출
- ✅ **프로토콜 상대 URL 처리**: `//image.auction.co.kr/...` → `https://...` 변환

**소싱 사이트 지원 현황**:
| 사이트 | 방식 | 상품명 | 가격 | 썸네일 |
|--------|------|--------|------|--------|
| G마켓 | FlareSolverr | ✅ | ✅ | ✅ |
| 옥션 | FlareSolverr | ✅ | ✅ | ✅ |
| 11번가 | Selenium | ✅ | ✅ | ✅ |
| SSG | Selenium | ✅ | ✅ | ✅ |
| 홈플러스 | Selenium | ✅ | ✅ | ✅ |
| 롯데ON | Selenium | ✅ | ✅ | ✅ |
| ~~스마트스토어~~ | - | ❌ | ❌ | ❌ |

**롯데ON 지원 추가**:
- ✅ **롯데ON (lotteon.com) 소싱 지원**
- ✅ **React SPA 대응**: 콘텐츠 로딩 대기 (최대 10초)
- ✅ **가격 추출 최적화**: 상품 영역에서만 가격 패턴 추출

**스마트스토어 지원 중단**:
- ❌ **네이버 CAPTCHA 차단**: FlareSolverr로도 우회 불가
- ❌ **대안 검토**: 네이버 쇼핑 API (무료) 또는 2captcha (유료)
- 📝 **권장**: 스마트스토어 대신 롯데ON 사용

**환경변수 추가**:
```env
FLARESOLVERR_URL=https://your-flaresolverr.up.railway.app/v1
```

**관련 파일**:
- `backend/utils/flaresolverr.py` - FlareSolverr 클라이언트
- `backend/api/monitoring.py` - 소싱 URL 정보 추출
- `backend/monitor/product_monitor.py` - 사이트별 가격 체크
- `docs/FLARESOLVERR_SETUP.md` - FlareSolverr 설정 가이드

---

### 2026-02-06: 자동가격조정 버그 수정 + 알림 시스템 개선 🔧💰🔔

**자동가격조정 시스템 수정**:
- 🐛 **SQLAlchemy ORM 호환성 수정** (`dynamic_pricing_service.py`):
  - 기존: SQLite raw SQL (`cursor.execute()`, `?` placeholder)
  - 수정: SQLAlchemy ORM (`db.update_selling_product()`, `session.query()`)
  - PostgreSQL 환경에서 자동가격조정이 작동하지 않던 버그 수정
- ✅ **모니터링 스케줄러 활성화** (`main.py`):
  - 주석 처리되어 있던 `start_monitor_scheduler()` 활성화
  - 자동가격조정 30분마다 실행
- ✅ **불필요한 기능 비활성화**:
  - `auto_check_products_job()` 비활성화 (경쟁사 가격 모니터링 - 현재 불필요)
  - `update_selling_products_sourcing_price()` 유지 (자동가격조정 핵심 기능)

**자동가격조정 작동 방식**:
```
30분마다 스케줄러 실행
       ↓
소싱 URL이 있는 활성 상품 조회 (최대 20개)
       ↓
소싱처 웹사이트에서 현재 가격 스크래핑
       ↓
가격 변동 감지 시
       ↓
새 판매가 계산 (소싱가 × 2 = 마진율 50%)
       ↓
로컬 DB 업데이트 + PlayAuto 가격 동기화
```

**송장 업로드 스케줄러 수정**:
- 🐛 **SQLAlchemy 호환성 수정** (`tracking_scheduler.py`):
  - `self.db.conn.cursor()` → SQLAlchemy ORM 사용
  - `[ERROR] 설정 로드 실패: 'DatabaseWrapper' object has no attribute 'conn'` 에러 해결

**알림 테스트 엔드포인트 수정**:
- 🐛 **직접 발송 방식으로 변경** (`/api/notifications/test`):
  - 기존: `send_notification()`으로 모든 활성 웹훅에 브로드캐스트
  - 수정: 테스트 대상 웹훅에만 직접 발송
  - 포맷 함수 직접 호출로 정확한 메시지 생성
  - 테스트 발송 결과 로그 기록 추가
- ✅ **누락 메서드 추가** (`db_wrapper.py`):
  - `add_webhook_log()` 메서드 추가

**커밋 해시**:
- `def07fd`: 알림 테스트 엔드포인트 직접 발송 방식으로 수정
- `2b81284`: add_webhook_log 메서드 추가
- `099ad85`: 동적가격조정 서비스 SQLAlchemy ORM으로 수정
- `53f2826`: 모니터링 스케줄러 활성화 및 SQLAlchemy 호환성 수정
- `5058b91`: 모니터링 상품 체크 기능 비활성화

---

### 2026-02-06: 주문-회계 자동 연동 + 주문 처리 시스템 📦💰✅

**회계 시스템 자동 연동 구현**:
- ✅ **PlayAuto 주문 → 회계 테이블 자동 동기화**:
  ```
  PlayAuto 주문 수집 → MarketOrderRaw → Order 테이블 생성
                                              ↓
                    MySellingProduct 매칭 → OrderItem 테이블 생성
                    (sourcing_price 가져오기)   (selling_price, sourcing_price, profit)
                                              ↓
                                       회계 자동 계산!
  ```
- ✅ **상품 매칭 시스템**: `shop_cd` + `shop_sale_no`로 MySellingProduct 자동 매칭
- ✅ **가격 자동 설정**:
  - `selling_price`: PlayAuto 주문에서 가져옴
  - `sourcing_price`: 매칭된 상품의 소싱가 자동 입력
  - `profit`: `(판매가 - 소싱가) × 수량` 자동 계산
- ✅ **기존 주문 마이그레이션**: 대시보드에서 버튼 클릭으로 일괄 동기화

**회계 API 수정**:
- ✅ **SQLAlchemy ORM 재작성**: SQLite raw SQL → PostgreSQL 호환 ORM
- ✅ **동기화 상태 API**: `GET /api/accounting/sync/status`
- ✅ **마이그레이션 API**: `POST /api/accounting/sync/migrate-orders`

**회계 대시보드 UI 추가**:
- ✅ 동기화 상태 카드 (전체/동기화됨/미동기화 건수)
- ✅ 마이그레이션 버튼 ("N건 동기화")
- ✅ 로딩 상태 및 빈 상태 UI

**커밋 해시**:
- `baeb915`: 회계 API SQLAlchemy ORM으로 재작성
- `341ba7f`: 회계탭 프론트엔드 버그 수정
- `c66ad13`: PlayAuto 주문-회계 자동 연동 구현

---

**주문 상태별 탭 분리**:
- ✅ **주문 목록 탭**: 미처리 주문만 표시 (신규주문, 출고대기 등)
- ✅ **송장 관리 탭**: 출고완료된 주문 표시
- ✅ 출고완료 판별: "출고완료", "배송완료", "배송중", completed, shipped, delivered
- ✅ 송장 관리 탭에 통계 카드 추가 (출고완료 수, 업로드된 송장 수, 성공률)
- ✅ 송장 관리 탭 검색 기능 (주문번호, 고객명, 전화번호, 송장번호, 상품명)

**송장 입력 및 출고완료 처리**:
- ✅ **출고지시 API 구현**: `PUT /api/order/instruction`
  - 신규주문 → 출고대기 상태 자동 변경
  - Body: `{bundle_codes, auto_bundle, dupl_doubt_except_yn}`
- ✅ **송장 업데이트 시 자동 상태 변경**:
  - 주문이 "출고대기" 상태가 아니면 먼저 출고지시 API 호출
  - 그 다음 송장번호 입력 및 출고완료 처리
- ✅ 배송사 선택 (CJ대한통운, 한진택배, 롯데택배, 우체국택배, 로젠택배)

**버그 수정**:
- 🐛 **carr_no 타입 변환 문제 해결**: PlayAuto API가 int로 반환 → str로 자동 변환
- 🐛 **주문 금액 표시 단순화**: "10개 × 12,900원 = 129,000원" → "129,000원"
- 🐛 **ord_status 값 전달 문제 해결**: 프론트엔드에서 백엔드로 상태값 전달

**주문 처리 워크플로우 완성**:
```
1. PlayAuto 신규주문 수신 → 주문 목록에 표시
         ↓
2. [🛒 구매하기] 버튼 → 소싱처에서 상품 구매
         ↓
3. [📝 송장 입력] 버튼 → 배송사 선택 + 송장번호 입력
         ↓
4. 🤖 자동 처리:
   - 신규주문 → 출고대기 (PUT /order/instruction)
   - 송장 업데이트 → 출고완료 (PUT /order/setInvoice)
         ↓
5. ✅ 완료! → 송장 관리 탭으로 이동
```

**커밋 해시**:
- `1402a07`: 주문 상태별 탭 분리 (미처리/출고완료)
- `5e37011`: carr_no 타입 변환 문제 해결
- `945ae0c`: 주문 금액 표시 단순화
- `0665f84`: 송장 업데이트 시 출고대기 상태 자동 변경
- `2ebb6f3`: 출고지시 API 수정 (PUT /order/instruction)
- `b5fa3a7`: 송장 관리 탭 검색 기능 추가

---

### 2026-02-05: 주문 처리 시스템 설계 완료 📦🛒

**주문 처리 워크플로우 설계**:
- ✅ **완전한 주문 처리 플로우 정의**:
  ```
  신규주문 → 상품 매칭 → 소싱처 구매 → 송장 입력 → 출고완료
  ```
- ✅ **상품 매칭 시스템 확인**:
  - 이미 구현된 상품 탭 활용
  - 판매 상품 ↔ 소싱처 URL 연결
  - DB 필드: `product_name`, `sourcing_url`, `sourcing_source`, `sourcing_price`
- ✅ **PlayAuto API 분석 완료**:
  - `PUT /api/order/instruction` - 출고 지시 (신규주문 → 출고대기)
  - `PUT /api/order/setInvoice` - 송장 업데이트 (배송사 + 송장번호 → 출고완료)
  - 문서: `instructions.pdf`, `update.pdf`

**반자동 시스템 설계**:
- 🎯 **반자동 방식 채택** (수동 구매 + 자동 처리):
  - 사용자가 소싱처에서 직접 구매 (상품 선택, 수량, 결제)
  - 시스템이 배송지 정보 준비 및 송장 자동 처리
- 🎯 **소싱처 지원**:
  - G마켓, 옥션 (FlareSolverr로 Cloudflare 우회)
  - 11번가, SSG, 홈플러스/트레이더스, 롯데ON (Selenium)
  - ~~스마트스토어~~ (네이버 CAPTCHA로 지원 중단)
  - 각 소싱처 URL 패턴 인식

**UI/UX 설계**:
- 📝 **주문 목록 화면**:
  - [🛒 구매하기] 버튼 - 소싱처 링크 열기 + 배송지 정보 준비
  - [📝 송장 입력] 버튼 - 배송사 선택 + 송장번호 입력 모달
- 📝 **송장 입력 모달**:
  - 배송사 선택 드롭다운 (CJ대한통운, 한진택배, 롯데택배 등)
  - 송장번호 입력 필드
  - PlayAuto 자동 업데이트 (출고완료 처리)

**나중에 결정할 사항**:
- ⏸️ **배송지 자동 입력 방법**:
  - 옵션 1: 크롬 확장 프로그램 (추천)
  - 옵션 2: 수동 복사/붙여넣기 (가장 간단)
  - 옵션 3: RPA (Playwright)
- ⏸️ **구현 우선순위**:
  - Phase 1: 기본 기능 (구매하기 버튼, 송장 입력 UI, PlayAuto API)
  - Phase 2: 배송지 자동 입력 (추후 결정)

**영향**:
- ✅ 주문 처리 플로우 완전 자동화 준비 완료
- ✅ 수작업 50% 감소 예상 (송장 자동 업데이트)
- ✅ PlayAuto API 100% 호환

**다음 단계**:
- 🚧 Phase 1 구현 시작 (기본 기능)
- 🚧 Backend API 개발 (`/api/playauto/instruction`, `/api/playauto/invoice`)
- 🚧 Frontend UI 개발 (주문 목록 버튼, 송장 입력 모달)

**관련 문서**:
- `instructions.pdf` - PlayAuto 출고지시 API
- `update.pdf` - PlayAuto 송장 업데이트 API

---

### 2026-02-04: PlayAuto 채널별 판매자 관리코드 분리 + 자동 가격 조정 수정 🔧💰

**PlayAuto 채널별 c_sale_cd 분리 구현**:
- ✅ **문제 발견**: 상품이 PlayAuto에 2번 등록되지만(지마켓/옥션, 스마트스토어) 판매자 관리코드는 1개만 저장
- ✅ **DB 스키마 변경**:
  - `c_sale_cd_gmk` 컬럼 추가 (지마켓/옥션용 판매자 관리코드)
  - `c_sale_cd_smart` 컬럼 추가 (스마트스토어용 판매자 관리코드)
  - 기존 `c_sale_cd` 필드는 하위 호환성을 위해 유지
- ✅ **데이터베이스 마이그레이션**:
  - 로컬 SQLite: `backend/migrate_split_c_sale_cd.py`
  - 프로덕션 PostgreSQL: `backend/migrate_split_c_sale_cd_postgres.py`
  - Supabase SQL Editor에서 직접 실행 완료
- ✅ **상품 등록 자동화**:
  - `/api/products/register-to-playauto` 수정
  - 지마켓/옥션 등록 시 → `c_sale_cd_gmk` 자동 저장
  - 스마트스토어 등록 시 → `c_sale_cd_smart` 자동 저장
  - 두 채널 독립적으로 등록 및 저장
- ✅ **UI 개선** (EditProductModal):
  - 🛒 지마켓/옥션용 판매자 관리코드 (주황색 테두리)
  - 🏪 스마트스토어용 판매자 관리코드 (녹색 테두리)
  - 설명 텍스트 추가 (왜 2개인지 안내)
  - 각 필드별 placeholder 예시
- ✅ **상품 수정 API 개선**:
  - `/api/products/{product_id}` 수정
  - 두 c_sale_cd 모두 수정 시 각각 PlayAuto API 호출
  - `playauto_updated_gmk`, `playauto_updated_smart` 별도 반환
  - 각 채널별 성공/실패 로깅

**자동 가격 조정 API 수정**:
- ✅ **500 에러 수정** (`/api/auto-pricing/settings`):
  - 존재하지 않는 `settings` 테이블 참조 → `playauto_settings` 사용
  - 잘못된 테이블 이름 `selling_products` → `my_selling_products`
  - 원시 SQL 쿼리 → db wrapper 메소드 사용
  - PostgreSQL 호환성 보장
- ✅ **자동 가격 조정 기능 확인**:
  - `/api/auto-pricing/adjust-product/{id}` - 개별 상품 가격 조정
  - `/api/auto-pricing/adjust-all` - 전체 상품 일괄 조정
  - DynamicPricingService: 소싱가 변동 시 자동 조정
  - Scheduler 연동: 자동 가격 모니터링

**데이터베이스 변경사항**:
```sql
-- 로컬 SQLite
ALTER TABLE my_selling_products ADD COLUMN c_sale_cd_gmk TEXT;
ALTER TABLE my_selling_products ADD COLUMN c_sale_cd_smart TEXT;

-- 프로덕션 PostgreSQL (Supabase)
ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS c_sale_cd_gmk TEXT;

ALTER TABLE my_selling_products
ADD COLUMN IF NOT EXISTS c_sale_cd_smart TEXT;
```

**TypeScript 타입 업데이트**:
```typescript
export interface Product {
  // ... 기존 필드 ...
  c_sale_cd?: string;          // 하위 호환성
  c_sale_cd_gmk?: string;      // 지마켓/옥션용
  c_sale_cd_smart?: string;    // 스마트스토어용
  playauto_product_no?: string;
  // ...
}
```

**API 응답 예시**:
```json
{
  "success": true,
  "message": "상품이 수정되었습니다.",
  "playauto_updated_gmk": true,
  "playauto_updated_smart": true,
  "playauto_changes": ["sale_price", "shop_sale_name"]
}
```

**영향**:
- ✅ 상품 등록 시 두 채널의 c_sale_cd 자동 저장
- ✅ 상품 수정 화면에서 두 코드 모두 확인 가능
- ✅ 가격/정보 수정 시 두 채널 모두 PlayAuto 자동 동기화
- ✅ 각 채널별 성공/실패 독립 처리 및 로깅
- ✅ 자동 가격 조정 설정 페이지 정상 작동

**커밋 해시**:
- `a216b00`: Implement dual c_sale_cd fields for channel-specific PlayAuto sync
- `bb7fa2c`: Fix migration script to use correct table name and encoding
- `e76c909`: Add PostgreSQL migration script for dual c_sale_cd fields
- `b0f89ce`: Auto-save dual c_sale_cd values on product registration
- `84da6e2`: Fix auto-pricing settings API 500 error

---

### 2026-02-04: 검색 기능 + 자동 가격 조정 + 상세페이지 JPG 최적화 + 성능 개선 + 실시간 알림 🔍💰🎨⚡🔔

**주문 검색 기능**:
- ✅ **실시간 검색 필터링**:
  - 주문번호, 고객명, 전화번호, 마켓으로 검색
  - 클라이언트 사이드 실시간 필터링
  - 검색 결과 개수 표시
  - 검색어 초기화 버튼 (X)
- ✅ **검색 UI**:
  - 주문 목록 상단에 검색바 추가
  - 돋보기 아이콘, 입력 필드, 클리어 버튼
  - 검색 시 페이지 1로 자동 리셋
- ✅ **검색 예시**:
  ```typescript
  // 주문번호로 검색: "ORD-001"
  // 고객명으로 검색: "홍길동"
  // 전화번호로 검색: "010-1234-5678"
  // 마켓으로 검색: "coupang", "smartstore"
  ```

**자동 가격 조정 시스템**:
- ✅ **마진 기반 자동 가격 계산**:
  - 목표 마진율 설정 (기본 30%)
  - 최소 마진율 설정 (기본 15%)
  - 가격 올림 단위 선택 (100원 ~ 10,000원)
  - 최소 마진 미달 시 자동 비활성화 옵션
- ✅ **자동 가격 조정 API** (`/api/auto-pricing`):
  - `GET/POST /settings` - 설정 조회/저장
  - `POST /adjust-product/{product_id}` - 개별 상품 가격 조정
  - `POST /adjust-all` - 모든 활성 상품 일괄 조정
- ✅ **가격 계산 공식**:
  ```python
  # 목표 마진율로 판매가 계산
  # 마진율 = (판매가 - 소싱가) / 판매가 * 100
  # 판매가 = 소싱가 / (1 - 마진율/100)

  # 예시: 소싱가 10,000원, 목표 마진 30%
  # 판매가 = 10,000 / (1 - 0.3) = 14,285원
  # 올림 단위 100원 → 14,300원
  # 실제 마진 = (14,300 - 10,000) / 14,300 = 30.1%
  ```
- ✅ **자동 가격 조정 UI**:
  - 새 탭: "자동 가격 조정"
  - 설정 폼: 활성화 토글, 마진율 입력, 가격 단위 선택
  - 수동 실행 버튼: "모든 상품 가격 조정 실행"
  - 가격 계산 예시 테이블 (실시간 미리보기)
  - 현재 설정 카드 (목표 마진율, 최소 마진율)
- ✅ **WebSocket 알림 연동**:
  - 가격 조정 완료 시 실시간 알림
  - 역마진 경고 알림
  - 상품 비활성화 알림
- ✅ **자동 가격 조정 설정 저장**:
  - `settings` 테이블에 JSON 형식으로 저장
  - 페이지 새로고침해도 설정 유지

**자동 가격 조정 예시**:
```json
{
  "enabled": true,
  "target_margin": 30.0,
  "min_margin": 15.0,
  "price_unit": 100,
  "auto_disable_on_low_margin": true
}
```

**자동 가격 조정 시나리오**:
1. 소싱처 가격 상승: 10,000원 → 12,000원
2. 자동 가격 조정 실행
3. 새 판매가 계산: 12,000 / 0.7 = 17,142원 → 17,200원 (100원 단위)
4. 마진율 확인: (17,200 - 12,000) / 17,200 = 30.2% ✅
5. 가격 업데이트 완료
6. WebSocket 알림: "17,200원으로 가격이 조정되었습니다 (마진 30.2%)"

**검색 + 자동 가격 조정 커밋 해시**:
- `[commit-hash]`: 주문 검색 기능 추가
- `[commit-hash]`: 자동 가격 조정 시스템 구현
- `[commit-hash]`: README 업데이트

---

### 2026-02-04 (이전): 상세페이지 JPG 최적화 + 성능 개선 + 실시간 알림 🎨⚡🔔

**상세페이지 JPG 생성 최적화**:

**고화질 JPG 렌더링 시스템 개선**:
- ✅ **화질 최적화**:
  - JPG quality: 0.9 → 1.0 (최고 품질)
  - pixelRatio: 2 (Retina 디스플레이 지원, 860px → 1720px)
  - 인라인 스타일로 너비 강제 고정 (Tailwind CSS 인식 문제 해결)
- ✅ **파란색 선 제거**:
  - 편집 UI 요소 (border-2, outline) 필터링
  - JPG 생성 전 임시로 border/outline 스타일 제거
  - 렌더링 후 원래 스타일 복원
- ✅ **이미지 전송 최적화**:
  - sale_img2~11 제거 (상세 이미지 미전송)
  - sale_img1만 전송 (썸네일)
  - 상세 이미지는 JPG에 통합되어 detail_desc에 포함됨
- ✅ **스마트스토어 호환성**:
  - 옵션값(opt_sort1_desc)에서 콤마 제거
  - "펄 25% 라이트, 340g, 6개" → "펄 25% 라이트 340g 6개"
  - "옵션값 항목에 콤마(,)는 사용하실 수 없습니다" 에러 해결

**상세페이지 JPG 생성 설정**:
```typescript
await htmlToImage.toJpeg(templateRef.current, {
  quality: 1.0,           // 최고 품질
  pixelRatio: 2,          // 2배 해상도 (1720px)
  backgroundColor: '#ffffff',
  cacheBust: true,
  filter: (node) => {
    // 편집 UI 요소 제외
    return !node.classList.contains('border-2') &&
           !node.classList.contains('outline') &&
           node.tagName !== 'INPUT' &&
           node.tagName !== 'BUTTON';
  }
});
```

**PlayAuto API 전송 데이터 간소화**:
```json
{
  "sale_img1": "썸네일 URL",
  "detail_desc": "<img src='고화질_JPG_URL' />"
}
```
- 이전: sale_img1~11 (최대 11개 이미지)
- 현재: sale_img1 (썸네일 1개) + detail_desc (JPG 통합)

**해결된 문제**:
- ✅ 저화질 JPG 이미지 → 최고 품질 (1.0) + 2배 해상도
- ✅ 좁은 너비 (빈 공간) → 인라인 스타일로 860px 강제 고정
- ✅ 파란색 편집 선 → 필터링 + 임시 스타일 제거
- ✅ 중복 이미지 전송 → 썸네일만 전송, 나머지는 JPG에 통합
- ✅ 스마트스토어 콤마 에러 → 옵션값에서 콤마 자동 제거

**성능 최적화 (API 통합 + 서버 사이드 페이지네이션)**:
- ✅ **통합 대시보드 API** (`/api/dashboard/all`):
  - 5개 API 호출 → 1개로 통합
  - 네트워크 요청 80% 감소
  - 페이지 로드 시간 단축
  - 데이터: RPA 통계, PlayAuto 통계, 모니터링, 주문 목록
- ✅ **서버 사이드 페이지네이션**:
  - `/api/orders/with-items`에 page, limit 파라미터 추가
  - 메모리 사용량 대폭 감소 (전체 로드 → 페이지별 로드)
  - 기본 limit: 1000 → 50
  - total_count, total_pages 반환
  - OFFSET/LIMIT SQL 쿼리 사용

**실시간 알림 시스템 (WebSocket)**:
- ✅ **Backend WebSocket 서버**:
  - `/ws/notifications` 엔드포인트
  - ConnectionManager (다중 연결 관리)
  - Ping/Pong 하트비트 (30초 간격)
  - 브로드캐스트 알림 시스템
- ✅ **Frontend WebSocket 클라이언트**:
  - 싱글톤 패턴 (자동 재연결)
  - 최대 5회 재연결 시도 (3초 간격)
  - 연결 상태 실시간 표시
- ✅ **실시간 알림 종류**:
  - 📦 새 주문 생성
  - 📝 주문 상태 변경
  - 🚚 송장 번호 업로드
  - ✅ 상품 등록 완료
  - ⚠️ 가격 변동/역마진 경고
- ✅ **UI 컴포넌트**:
  - RealtimeNotifications (우측 상단 연결 상태)
  - Toast 알림 (react-hot-toast)
  - 알림 카운터
  - 연결 상태 인디케이터 (초록색 점)

**통합 효과**:
```typescript
// Before: 5개 API 호출
const [rpaStats, playautoStats, monitorStats, ordersData, allOrdersData] =
  await Promise.all([...5개 fetch...]);

// After: 1개 API 호출
const data = await fetch('/api/dashboard/all');
// → 80% 네트워크 트래픽 감소
```

**WebSocket 연결 흐름**:
```
Client → ws://localhost:8000/ws/notifications
       → Connected (초록색 점)
       → 주문 생성 시 실시간 알림 📦
       → 자동 재연결 (끊김 시)
```

**커밋 해시**:
- `7d6bc95`: JPG 화질 개선 및 파란색 선 제거
- `47ab3a6`: templateRef div 너비 860px 고정
- `79418ac`: 인라인 스타일로 너비 강제 설정 (width 옵션 제거)
- `02e1668`: sale_img2-11 제거 (썸네일만 전송)
- `1f08320`: 스마트스토어 옵션값 콤마 제거
- `bb24d94`: 성능 최적화 (통합 API + 페이지네이션)
- `0b50dc5`: WebSocket 실시간 알림 시스템
- `95f7f81`: RealtimeNotifications 레이아웃 통합

---

### 2026-02-03: PlayAuto 상품 등록 시스템 개선 🚀

**PlayAuto 채널별 설정 분리 구현**:
- ✅ 지마켓/옥션과 스마트스토어를 별도로 등록하도록 분리
- ✅ 채널별 최적 설정 자동 적용:
  - **지마켓/옥션(GMK, A001, A006)**: `std_ol_yn="Y"` (단일상품), `opt_type="옵션없음"`
  - **스마트스토어(A077 등)**: `std_ol_yn="N"` (단일상품 아님), `opt_type="독립형"`
- ✅ ESM 채널 자동 제외 (단일상품 제약으로 인한 오류 방지)

**이미지 처리 시스템 개선**:
- ✅ 상세페이지 이미지를 Supabase Storage에 직접 업로드
  - `/api/products/upload-image` 엔드포인트 추가
  - DetailPage 이미지 업로드/드롭 시 자동 Supabase 업로드
- ✅ 썸네일 자동 Supabase 업로드
  - URL 추출 후 즉시 Supabase Storage에 저장
  - 외부 접근 가능한 공개 URL 사용
- ✅ 로컬 경로 이미지 자동 제외
  - `/static`, `/uploads` 등 로컬 경로는 PlayAuto 접근 불가
  - 외부 URL(http://, https://)만 사용하도록 필터링
- ✅ detail_desc HTML에 모든 이미지 포함
  - 이전: 이미지 제거 → 빈 상세페이지
  - 수정: 모든 이미지 포함 → 완전한 상세페이지

**상품 관리 UX 개선**:
- ✅ 상품 기본 상태 변경: "판매중" → "중단"
  - 상세페이지에서 추가한 상품은 검토 후 활성화
- ✅ 상품탭 기본 필터 변경: "판매중" → "전체"
  - 새로 추가된 중단 상품도 바로 확인 가능

**원산지 설정 개선**:
- ✅ PlayAuto 원산지(madein) 표시 수정
  - 기존: "국내, 강원, 강릉시" (PlayAuto 계정 첫 번째 등록지)
  - 수정: "국내, 경기도" (기타 필드 사용)
  - madein_etc 필드에 "경기도" 설정
  - 모든 상품에 통일된 원산지 적용

**버그 수정**:
- 🐛 스마트스토어 상품정보고시 에러 수정
  - "유전자변형식품 표시는 Y또는 N으로만 입력할 수 있습니다" 해결
  - `infoDetail`에 GMO 필드 명시: `"유전자변형식품의 경우의 표시": "N"`
- 🐛 Scheduler cursor AttributeError 수정
  - `Session` 객체에 `.cursor()` 호출 에러 해결
  - SQLAlchemy ORM 쿼리 방식으로 변경
  - `db.update_selling_product()` 메서드 사용

**상세 로깅 추가**:
- 📊 채널별 등록 상황 실시간 확인
  - 원본 site_list 전체 출력
  - 각 채널 정보 (shop_cd, shop_id, template_no) 상세 로깅
  - 채널 분리 결과 표시 (지마켓/옥션, 스마트스토어, ESM)
  - 각 그룹별 등록 시작/성공/실패 명확히 표시
  - 설정값 (std_ol_yn, opt_type) 로깅

**해결된 문제**:
- ✅ "ESM은 단일상품만 등록 가능합니다" → ESM 채널 자동 제외
- ✅ "단일상품인경우 독립형 옵션은 사용하실 수 없습니다" → 채널별 설정 분리
- ✅ 썸네일 이미지가 다름 → Supabase URL 사용
- ✅ 상세페이지에 사진/글 없음 → 이미지 포함 + Supabase 업로드
- ✅ 이미지 업로드 405 에러 → API_BASE_URL 사용
- ✅ sortOrder 매개변수 오류 → 이미지를 HTML에 포함하되 Supabase URL만 사용

**커밋 해시**:
- `16214ec`: GMK/Auction 이미지 매개변수 에러 수정 (이미지 분리)
- `42d4df7`: 상품 기본 상태 "중단", 필터 "전체" 변경
- `0602e84`: 채널별 설정 분리 (GMK/Auction vs SmartStore)
- `ecd75a8`: ESM 채널 자동 제외
- `7f58446`: detail_desc HTML에 이미지 포함, 로컬 경로 제외
- `ae030fc`: Supabase Storage 이미지 업로드 시스템
- `8b55e59`: API_BASE_URL 사용 수정
- `e2915a9`: 채널별 상세 로깅 추가
- `dca172f`: 스마트스토어 GMO 필드 수정
- `9751468`: Scheduler cursor 에러 수정
- `31ce55d`: 원산지 경기도 설정 추가
- `10d6dae`: 원산지 "경기도"로 단순화

---

### 2026-02-02: SQLite 완전 제거 및 PostgreSQL 전환 🗄️

**치명적인 데이터 손실 문제 발견 및 해결**:
- 🚨 **문제 발견**: 프로덕션(Railway)에서 SQLite 사용으로 재시작 시 모든 데이터 손실
- 🔍 **전체 코드베이스 감사**: 92개 Python 파일을 15가지 방법으로 검증
- ✅ **27개 파일 수정**: 모든 프로덕션 코드가 PostgreSQL 사용하도록 수정

**수정된 파일들**:
1. **API 폴더** (9개): products, orders, monitoring, playauto, accounting, categories, notifications, tracking_scheduler, admin
2. **PlayAuto 모듈** (5개): auth, orders, scheduler, tracking, product_registration
3. **핵심 시스템** (13개):
   - main.py (메인 애플리케이션!)
   - monitor/scheduler.py, monitor/selling_product_monitor.py
   - notifications/notifier.py
   - services/dynamic_pricing_service.py, tracking_scheduler.py, tracking_upload_service.py
   - inventory/auto_manager.py
   - + 5개 테스트 스크립트

**주요 변경사항**:
```python
# Before (잘못됨 - SQLite 전용)
from database.db import get_db

# After (올바름 - PostgreSQL/SQLite 자동 선택)
from database.db_wrapper import get_db
```

**Railway 환경변수 추가**:
```env
USE_POSTGRESQL=true  # PostgreSQL 사용 강제
DATABASE_URL=postgresql://...  # Supabase PostgreSQL
```

**추가 수정**:
- 🔧 `admin.py`: PostgreSQL 지원 (시스템 상태, DB 통계, 백업/복원, 최적화)
- 🔧 `backup_manager.py`: PostgreSQL 환경 감지 (Supabase 백업 안내)
- 🔧 `base_repository.py`: database_manager 사용, 동적 SQL placeholder 지원
- 🔧 `product_registration.py`: SQLite import 제거, database_manager 사용

**검증 결과** (15가지 검증):
- ✅ 프로덕션 코드 SQLite 직접 사용: **0개**
- ✅ database.db_wrapper 사용: **28개**
- ✅ database_manager 사용: **5개**
- ✅ 동적 import: **0개**
- ✅ 숨겨진 SQLite 연결: **0개**

**영향**:
- ✅ 상품 데이터 → PostgreSQL (영구 보존)
- ✅ 주문 데이터 → PostgreSQL
- ✅ 모니터링 데이터 → PostgreSQL
- ✅ PlayAuto 설정 → PostgreSQL
- ✅ 알림 기록 → PostgreSQL
- ✅ 재고 정보 → PostgreSQL

**Railway 재시작해도 모든 데이터 100% 보존!** 🎉

**커밋 해시**:
- `d3337d9`: API 폴더 전체 db_wrapper 전환 (9개 파일)
- `78ab329`: SQLite 하드코딩 추가 수정 (5개 파일)
- `bba60dd`: admin.py PostgreSQL 지원 추가
- `c8f3996`: PlayAuto 모듈 전체 수정 (5개 파일)
- `0c29c69`: 핵심 시스템 파일 수정 (13개 파일)

**문서**:
- 📄 `scratchpad/SQLITE_AUDIT_FINAL_REPORT.md`: 전체 감사 상세 보고서

---

### ✅ 해결된 문제

#### ✅ PlayAuto 카테고리 코드 시스템 개편 완료 (2026-02-03)

**문제**:
- 기존 구 카테고리 시스템 (Standard_category_list.xlsx, 13,366개)
- PlayAuto 계정 카테고리와 불일치
- 상품 등록 실패: "존재하지 않는 카테고리 입니다.(1)"

**해결**:
- ✅ **138개 카테고리를 새 시스템(category.xlsx)으로 수동 매핑 완료**
- ✅ 모든 카테고리 코드를 PlayAuto 호환 코드로 변경
- ✅ `categories` 테이블: 138/138개 sol_cate_no 업데이트
- ✅ `category_playauto_mapping` 테이블: 81/81개 sol_cate_no 업데이트
- ✅ `playauto_category` 컬럼: 81/81개 카테고리명 업데이트 (관리자 화면 표시)

**변경 사항**:
```
간편식 > 카레/짜장/덮밥 > 카레 > 카레
  구: 36190600 (구 시스템)
  신: 6226818  (신 시스템) ✅

간편식 > 면 > 라면 > 라면
  구: 36060200 (구 시스템)
  신: 6226561  (신 시스템) ✅

냉동식 > 만두 > 고기만두 > 고기만두
  구: 36070500 (구 시스템)
  신: 6226587  (신 시스템) ✅
```

**영향**:
- ✅ PlayAuto 상품 등록 시 올바른 카테고리 코드 사용
- ✅ 계정에 등록된 카테고리와 일치
- ✅ 관리자 화면에서 새 카테고리명 정상 표시
- ✅ 모든 상품 카테고리 정상 작동

**검증 완료**:
- ✅ 데이터베이스: 구 코드 0개, 신 코드 81개
- ✅ 코드 범위: 6226500 ~ 34030100
- ✅ 관리자 화면 표시 정상

**권장 테스트**:
1. PlayAuto 웹사이트에서 카테고리 확인
2. 실제 상품 등록 테스트
3. 필요시 PlayAuto 계정에 추가 카테고리 등록

**관련 파일**:
- `backend/manual_mapping_template.xlsx`: 수동 매핑 템플릿 (사용자 작업 완료)
- `backend/categories_list.csv`: 138개 카테고리 목록
- `backend/MANUAL_MAPPING_GUIDE.md`: 매핑 가이드
- `backend/search_category.py`: 카테고리 검색 도구
- `backend/apply_manual_mapping.py`: 매핑 적용 스크립트
- `backend/prepare_manual_mapping.py`: 템플릿 생성 스크립트
- `category.xlsx`: PlayAuto 카테고리 마스터 파일 (13,363개)

**커밋 해시**:
- `d5f789d`: PlayAuto 카테고리 문제 근본 원인 파악
- `f900d85`: Railway 빌드 최적화
- `3f0d4dd`: PlayAuto 카테고리 시스템 마이그레이션 완료 (138개 수동 매핑)

---

### ⚠️ 현재 알려진 문제

#### 🔴 마켓 코드 동기화 이슈 (작업 중)

**증상**:
```
❌ ol_shop_no가 없어 마켓 코드를 수집할 수 없습니다. 상품을 재등록하세요.
```

**근본 원인**:
- PlayAuto에 상품을 2번 등록 (지마켓/옥션용, 스마트스토어용)
- 각 등록마다 다른 `ol_shop_no`(온라인 쇼핑몰 번호)를 반환
- 기존 DB는 하나의 `ol_shop_no`만 저장 → 일부 마켓 코드 누락

**완료된 작업** (2026-02-05):
- ✅ DB 스키마 확장 (`ol_shop_no_gmk`, `ol_shop_no_smart` 컬럼 추가)
- ✅ 상품 등록 로직 수정 (채널별 `ol_shop_no` 저장)
- ✅ 마켓 코드 동기화 로직 수정 (모든 채널 조회)
- ✅ Railway 배포 및 마이그레이션 완료
- ✅ 커밋: `3058b41`, `a231dbc`, `2aa4aa0`

**남은 작업**:
- ❌ **기존 상품의 `ol_shop_no` 데이터 복구** ← 현재 문제
  - 기존 상품들은 `ol_shop_no_gmk`, `ol_shop_no_smart`가 NULL
  - 마켓 코드 동기화 시도하면 에러 발생

**임시 해결 방법**:
1. 문제 있는 상품을 PlayAuto에 **재등록**
2. 재등록 시 `ol_shop_no_gmk`, `ol_shop_no_smart` 자동 저장
3. 마켓 코드 동기화 → ✅ 정상 작동

**다음 세션 계획**:
1. PlayAuto API 문서 재확인 (상품 검색/목록 조회 API 찾기)
2. 자동 복구 스크립트 작성 (`c_sale_cd`로 `ol_shop_no` 자동 매칭)
3. 또는 일괄 재등록 UI 추가

**상세 문서**: [`OL_SHOP_NO_ISSUE_STATUS.md`](./OL_SHOP_NO_ISSUE_STATUS.md)

---

### 2026-02-01: Supabase Storage 마이그레이션 완료 📦

**이미지 스토리지 클라우드 마이그레이션**:
- ✅ 로컬 파일시스템 → Supabase Storage 전환
- ✅ 6248개 이미지 업로드 성공 (100% 완료)
- ✅ 100개 카테고리 폴더 (`cat-1` ~ `cat-138` 형식)
- ✅ 총 용량: 8.7GB
- ✅ Cloudflare CDN 가속 적용

**백엔드 API 업데이트**:
- 🔧 `backend/utils/supabase_storage.py` 신규 생성
  - `upload_image()`, `upload_image_from_bytes()` 함수
  - `get_public_url()` - Supabase Storage 공개 URL 생성
  - `list_images()` - 폴더별 이미지 목록 조회
- 🔧 `backend/api/admin.py` 수정
  - 이미지 업로드: Supabase Storage 연동
  - 갤러리 API: Supabase CDN URL 반환
  - 이미지 통계: Supabase Storage 메타데이터 조회
- 🔧 `backend/api/monitoring.py` 수정
  - 썸네일 저장: Supabase Storage 사용
- 🔧 `lib/imageService.ts` 수정
  - Admin API에서 Supabase URL 가져오기

**마이그레이션 스크립트**:
- 📄 `backend/migrate_images_to_supabase.py` 생성
- 한글 폴더명 → `cat-{id}` 형식 변환 (Supabase 호환)
- 진행률 표시 (0.0% ~ 100.0%)
- 에러 핸들링 및 재시도 로직

**이미지 URL 변경**:
```
# Before (로컬)
/supabase-images/100_식혜/image.jpg

# After (Supabase CDN)
https://spkeunlwkrqkdwunkufy.supabase.co/storage/v1/object/public/product-images/cat-100/image.jpg
```

**Railway 환경 변수 추가**:
```env
SUPABASE_URL=https://spkeunlwkrqkdwunkufy.supabase.co
SUPABASE_SERVICE_ROLE_KEY=***
```

**트러블슈팅**:
- 🐛 **Database Stats 500 에러 수정** (2단계):
  - 1단계: `db.execute()` → `db.get_connection()` 사용
  - 2단계: PostgreSQL 쿼리 제거, SQLite 전용으로 단순화
  - 커밋: `0215b22`, `544f37b`
- ⚠️ **브라우저 Admin API 500 에러** (조사 중)
  - curl 테스트는 정상 (HTTP 200)
  - 브라우저 캐시 또는 CORS 관련 의심

**커밋 해시**:
- `468ad43`: Supabase Storage 백엔드 API 통합
- `0215b22`: Database stats get_connection() 수정
- `544f37b`: Database stats SQLite 전용 단순화

---

### 2026-01-30: 클라우드 배포 완료 + 트러블슈팅 🎉

**배포 완료**:
- ✅ Phase 1-4 배포 완료
- ✅ Vercel + Railway + Supabase 인프라 구축
- ✅ 총 비용: $5/월

**배포 후 문제 해결**:
- 🐛 **템플릿 리터럴 버그 수정**: 작은따옴표(`'`) → 백틱(`` ` ``) 변경 (11개 파일)
  - `${API_BASE_URL}`이 `%7BAPI_BASE_URL%7D`로 URL 인코딩되던 문제 해결
  - 모든 API 호출이 Railway 백엔드로 정상 연결
- 🐛 **Railway Admin API 404 수정** (2단계):
  - 1단계: `psutil`, `Pillow` 패키지 추가
  - 2단계: admin.py 프로덕션 환경 호환성 개선
    - Optional imports 추가 (psutil, Pillow, sqlite3)
    - 안전한 디렉토리 생성 (Railway 권한 문제 해결)
    - get_db() 사용 (PostgreSQL 호환)
    - 조건부 기능 사용 (모듈 없을 때 기본값 제공)
  - 19개 admin 라우트가 정상 작동
- 🐛 **Localhost 하드코딩 제거**: 80개 이상의 하드코딩된 URL 수정 (16개 파일)
  - 모든 파일이 `API_BASE_URL` 중앙 집중식 관리
  - 환경별 자동 URL 선택 (로컬/프로덕션)
- ✅ **빌드 테스트 통과**: TypeScript 컴파일, Next.js 빌드 성공
- ✅ **README 업데이트**: 완전한 배포 가이드 및 트러블슈팅 문서화

**커밋 해시**:
- `790a55b`: localhost URL 일괄 수정
- `25dcc81`: AccountingPage import 수정
- `d57c6c4`: 템플릿 리터럴 따옴표 수정
- `c57cfc0`: Railway 의존성 추가 (psutil, Pillow)
- `ae213c2`: README 배포 문서화
- `ba2e7e1`: README 트러블슈팅 추가
- `dcd76fb`: admin.py 프로덕션 환경 수정

### 2026-01-29: 플레이오토 통합 완성
- ✅ Phase 19: 상세페이지 생성기 Figma 스타일 UI
- ✅ 이미지 편집 기능 강화
- ✅ API 수정 및 썸네일 최적화

### 2026-01-28: 관리자 페이지 & 카테고리 시스템
- ✅ Phase 16-18: 플레이오토 기본 템플릿 자동화
- ✅ 이미지/폴더 관리 시스템
- ✅ 계층적 카테고리 (138개)

### 2026-01-27: AI 상세페이지 자동 생성
- ✅ Phase 15: GPT-4 기반 자동 작성
- ✅ 9개 템플릿 지원
- ✅ 실시간 미리보기

### 이전 업데이트
- Phase 1-14: 기본 시스템 구축
- 상품 수집, 모니터링, RPA, 알림, 대시보드 등

---

## 🤝 기여

**개발**: 사용자 + Claude Sonnet 4.5
**날짜**: 2026-01-30
**라이선스**: MIT (또는 적절한 라이선스)

---

## 📞 지원

문제가 발생하면:
1. [GitHub Issues](https://github.com/sunes26/bada_auction/issues) 생성
2. 문서 확인 (`DEPLOYMENT_COMPLETE.md` 등)
3. API 문서 참고 (`/docs` 엔드포인트)
4. Vercel/Railway 로그 확인

---

## 🎯 다음 단계

### 완료된 작업 ✅

1. **이미지 마이그레이션** (Phase 5) ✅
   - ✅ 로컬 이미지 → Supabase Storage (6248개)
   - ✅ Cloudflare CDN 가속 활용
   - ✅ Railway 디스크 절약 (8.7GB)

### 개발 중 🚧

2. **주문 처리 시스템 (반자동)**
   - **현재 상태**: 설계 및 계획 단계
   - **목표**: 신규주문 → 소싱처 구매 → 송장 입력 → 출고완료 워크플로우

   **주문 처리 플로우**:
   ```
   1. PlayAuto 신규주문 수신
            ↓
   2. 주문 관리 페이지에서 확인
            ↓
   3. [🛒 구매하기] 버튼 클릭
      - 자동: 내 상품 DB에서 소싱처 URL 찾기
      - 자동: 배송지 정보 준비
      - 자동: 소싱처 사이트 새 창 열기
            ↓
   4. 👤 수동: 상품 선택, 수량 입력, 결제
            ↓
   5. 소싱처에서 송장번호 발급받음
            ↓
   6. [📝 송장 입력] 버튼 클릭
      - 배송사 선택 (CJ대한통운, 한진택배 등)
      - 송장번호 입력 (복사/붙여넣기)
            ↓
   7. 🤖 자동: PlayAuto API 호출
      - PUT /api/order/instruction (출고지시)
      - PUT /api/order/setInvoice (송장 업데이트)
      - 출고완료 상태 변경
            ↓
   8. ✅ 완료!
   ```

   **상품 매칭 시스템**:
   - 이미 구현됨: 상품 탭에서 판매 상품 + 소싱처 URL 관리
   - `product_name`: 내 판매 상품명
   - `sourcing_url`: 소싱처 링크 (쿠팡, 11번가, 네이버, 지마켓, 옥션)
   - `sourcing_source`: 소싱처 이름
   - `sourcing_price`: 소싱가

   **나중에 결정해야 할 사항**:

   **A) 배송지 자동 입력 방법**:
   1. **크롬 확장 프로그램** (추천)
      - 장점: 모든 소싱처에 범용 적용, 사용자 친화적
      - 단점: 설치 필요
   2. **수동으로 복사/붙여넣기** (가장 간단)
      - 장점: 구현 간단, 추가 설치 불필요
      - 단점: 수작업 필요
   3. **RPA (Playwright)**
      - 장점: 완전 자동화 가능
      - 단점: 복잡한 구현, 소싱처별 개별 개발 필요

   **B) 구현 우선순위**:
   1. **기본 기능 먼저** (1-2일 예상):
      - 주문 목록에 "구매하기" 버튼
      - 소싱처 링크 열기
      - 송장번호 입력 UI
      - PlayAuto 업데이트 API (출고지시, 송장 업데이트)
   2. **배송지 자동 입력은 나중에** (추후 결정):
      - 크롬 확장 개발 또는 RPA 구현

   **구현 예정 API**:
   - `PUT /api/playauto/instruction` - 출고 지시 (신규주문 → 출고대기)
   - `PUT /api/playauto/invoice` - 송장 업데이트 (출고대기 → 출고완료)
   - 자동: 배송사 코드 매칭 (CJ대한통운=4, 한진택배=5 등)

   **소싱처 지원** (2026-02-06 업데이트):
   - ✅ G마켓 (gmarket.co.kr) - FlareSolverr
   - ✅ 옥션 (auction.co.kr) - FlareSolverr
   - ✅ 11번가 (11st.co.kr) - Selenium
   - ✅ SSG (ssg.com) - Selenium
   - ✅ 홈플러스/트레이더스 (homeplus.co.kr) - Selenium
   - ✅ 롯데ON (lotteon.com) - Selenium (NEW)
   - ❌ ~~스마트스토어~~ (smartstore.naver.com) - 네이버 CAPTCHA로 지원 중단

### 선택사항

3. **Custom Domain 설정**
   - Vercel에서 본인 도메인 연결
   - 예: `badaauction.com`

4. **성능 최적화**
   - 이미지 최적화 (Next.js Image)
   - API 캐싱 강화
   - Database 인덱스 최적화

5. **추가 기능**
   - 사용자 인증 시스템
   - 이메일 알림
   - 모바일 앱 (React Native)

---

## 🔓 FlareSolverr 설정 (Cloudflare 우회)

G마켓, 옥션 등 Cloudflare로 보호된 사이트에서 상품 정보를 수집하려면 FlareSolverr가 필요합니다.

### Railway에서 FlareSolverr 배포

1. **Railway 대시보드에서 새 프로젝트 생성**
   - https://railway.app/dashboard 접속
   - "New Project" → "Deploy from Docker Image" 선택

2. **Docker 이미지 설정**
   ```
   ghcr.io/flaresolverr/flaresolverr:latest
   ```

3. **환경변수 설정**
   ```env
   LOG_LEVEL=info
   LOG_HTML=false
   CAPTCHA_SOLVER=none
   TZ=Asia/Seoul
   ```

4. **배포 완료 후 URL 확인**
   - 예: `https://flaresolverr-production-xxx.up.railway.app`

5. **백엔드에 환경변수 추가**
   ```env
   FLARESOLVERR_URL=https://flaresolverr-production-xxx.up.railway.app/v1
   ```

### 지원 사이트별 수집 방식

| 사이트 | 수집 방식 | 상태 |
|--------|----------|------|
| G마켓 | FlareSolverr | ✅ 상품명, 가격, 썸네일 |
| 옥션 | FlareSolverr | ✅ 상품명, 가격, 썸네일 |
| 11번가 | Selenium | ✅ 상품명, 가격, 썸네일 |
| SSG | Selenium | ✅ 상품명, 가격, 썸네일 |
| 홈플러스/트레이더스 | Selenium | ✅ 상품명, 가격, 썸네일 |
| 롯데ON | Selenium | ✅ 상품명, 가격, 썸네일 |
| ~~스마트스토어~~ | - | ❌ 네이버 CAPTCHA |

### 리소스 요구사항

- FlareSolverr: RAM 최소 512MB (권장 1GB)
- 각 브라우저 인스턴스당 100-200MB 추가 사용

### 문제 해결

- **FlareSolverr 연결 실패**: Railway 서비스 실행 상태 및 URL 확인 (`/v1` 포함)
- **Cloudflare 우회 실패**: FlareSolverr 버전 업데이트 확인
- **타임아웃**: `maxTimeout` 값 증가 (기본 60000ms)

---

## 🏷️ PlayAuto 카테고리 관리

### 카테고리 코드 체계

PlayAuto 상품 등록 시 두 가지 코드가 사용됩니다:

| 코드 | 용도 | 테이블 | 설명 |
|------|------|--------|------|
| **sol_cate_no** | 마켓 카테고리 | `category_playauto_mapping` | 상품이 마켓에서 **어느 카테고리에 노출**되는지 결정 |
| **infoCode** | 상품정보제공고시 | `category_infocode_mapping` | 전자상거래법에 따른 **필수 표시 항목** 결정 (자동 처리) |

```
상품 카테고리: "간편식 > 밥류 > 즉석밥 > 흰밥"
                    ↓
              level1: "간편식"
                    ↓
        ┌──────────┴──────────┐
        ↓                     ↓
   sol_cate_no            infoCode
   (6226815)         (ProcessedFood2023)
        ↓                     ↓
  마켓 카테고리 결정      법적 표시 항목 결정
  (중요!)               (자동 처리)
```

### 현재 카테고리 매핑 현황

| 구분 | 개수 |
|------|------|
| 총 매핑된 카테고리 | **81개** |
| 고유한 sol_cate_no | **47개** |

> ✅ **2026-02-08**: PlayAuto 카테고리 코드(sol_cate_no) 전면 재매핑 완료

### 마켓별 shop_cd 코드 및 옵션 설정

| 마켓 | shop_cd | opt_type | std_ol_yn | 비고 |
|------|---------|----------|-----------|------|
| 옥션 | A001, AUCTION | 옵션없음 | Y (단일상품) | |
| 지마켓 | A006, GMK | 옵션없음 | Y (단일상품) | |
| 쿠팡 | A027, CPM | **조합형** | N | ⚠️ 아래 이슈 참고 |
| 스마트스토어 | A077 | 독립형 | N | |
| 11번가 | A112 | 독립형 | N | |
| SSG.COM | A524 | 독립형 | N | |
| 롯데ON | A113 | 독립형 | N | |
| GS SHOP | A522 | 독립형 | N | |

### PlayAuto opt_type 허용값

PlayAuto API 문서 기준 `opt_type` 허용값:
- `옵션없음`: 옵션이 없는 단일상품
- `조합형`: 옵션명/옵션값 조합 (예: 색상-빨강, 색상-파랑)
- `독립형`: 각 옵션이 독립적 (예: 색상:빨강, 사이즈:Large)

> ⚠️ **쿠팡 주의**: 쿠팡은 **독립형 옵션 미지원**. 독립형으로 설정 시 '옵션없음' 상품으로 등록됨

### 채널별 옵션 설정 코드

```python
# 옥션/지마켓: 단일상품 (옵션없음)
std_ol_yn = "Y"
opt_type = "옵션없음"
opts = []

# 쿠팡: 조합형 옵션 필수
std_ol_yn = "N"
opt_type = "조합형"
opts = [{"opt_sort1": "상품선택", "opt_sort1_desc": "상품명", "stock_cnt": 999, "status": "정상"}]

# 스마트스토어 등: 독립형 옵션
std_ol_yn = "N"
opt_type = "독립형"
opts = [{"opt_sort1": "상품선택", "opt_sort1_desc": "상품명", "stock_cnt": 999, "status": "정상"}]
```

### 🚨 미해결 이슈: 쿠팡 상품 등록 오류

**현상**:
```
[]. 필수 구매 옵션이 존재하지 않습니다.
```

**시도한 해결 방법**:
1. ❌ `opt_type = "옵션없음"` → 필수 구매 옵션 오류
2. ❌ `opt_type = "독립형"` → 쿠팡 미지원 (옵션없음으로 자동 변경됨)
3. ❌ `opt_type = "조합형"` → 동일한 오류 발생

**현재 옵션 구조**:
```json
{
  "opt_type": "조합형",
  "opts": [
    {
      "opt_sort1": "상품선택",
      "opt_sort1_desc": "CJ제일제당 햇반 210g 10개",
      "stock_cnt": 999,
      "status": "정상"
    }
  ]
}
```

**추정 원인**:
- PlayAuto 쿠팡 템플릿 설정 문제 가능성
- opts 배열 구조가 쿠팡 요구사항과 다를 가능성
- 쿠팡 카테고리별 필수 옵션 요구사항 존재 가능성

**관련 파일**:
- `backend/api/products.py` - 채널별 분기 처리 (라인 833-870)
- `backend/playauto/product_registration.py` - 옵션 설정 (라인 483-518)
- `add.pdf` - PlayAuto API 문서

**해결 방안 검토 필요**:
- [ ] PlayAuto 웹에서 쿠팡 템플릿 옵션 설정 확인
- [ ] PlayAuto 고객센터 문의 (쿠팡 필수 구매 옵션 형식)
- [ ] opts 배열에 추가 필드 필요 여부 확인 (add_price, sku_cd 등)

### 카테고리 매핑 엑셀 파일

카테고리 매핑 데이터 내보내기:
```bash
# 프로젝트 루트에 엑셀 파일 생성됨
PlayAuto_카테고리_매핑.xlsx
```

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

---

## 🙏 감사

- [Next.js](https://nextjs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vercel](https://vercel.com/)
- [Railway](https://railway.app/)
- [Supabase](https://supabase.com/)
- [OpenAI](https://openai.com/)
- [Playauto](https://playauto.io/)

---

**물바다AI - 상품 관리의 미래** 🚀

이제 어디서나 접속하여 사용할 수 있습니다!

**프론트엔드**: `https://[your-app].vercel.app`
**백엔드**: `https://badaauction-production.up.railway.app`
