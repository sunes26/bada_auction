# 물바다AI - 통합 상품 관리 시스템

AI 기술로 상품 썸네일과 상세페이지를 전문가 수준으로 제작하고, 판매 상품을 체계적으로 관리하는 Next.js 애플리케이션입니다.

## 🎉 배포 완료! (2026-01-30)

**물바다AI가 성공적으로 클라우드에 배포되었습니다!**

### 🌐 배포된 서비스

| 서비스 | URL | 비용 |
|--------|-----|------|
| 🎨 **프론트엔드** | `https://[your-app].vercel.app` | 무료 |
| 🔧 **백엔드 API** | `https://badaauction-production.up.railway.app` | $5/월 |
| 💾 **데이터베이스** | Supabase PostgreSQL | 무료 |

**총 운영 비용**: **$5/월**

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
- **다채널 상품 수집**: 11번가, 홈플러스, SSG, G마켓, 스마트스토어
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
- **Playauto 자동 동기화**: 주문 자동 수집 및 동기화
- **발주 대기 목록**: 자동 발주 관리
- **송장 업로드 스케줄러**: 송장 번호 일괄 업로드

### 🎨 상세페이지 제작
- **Figma 스타일 에디터**: 드래그 앤 드롭 편집
- **9개 템플릿**: Daily, Food, Fresh, Simple 등
- **실시간 미리보기**: 즉시 확인 가능
- **이미지 편집**: 크기, 위치, 스타일 조정

### 🤖 자동화
- **재고 자동 관리**: 품절 시 자동 비활성화
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

### Database
- **Production**: PostgreSQL 15 (Supabase)
- **Development**: SQLite
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
└────────────┬─────────────────────────────┘
             │ PostgreSQL
             │ DATABASE_URL
             ▼
┌──────────────────────────────────────────┐
│    Supabase (데이터베이스)                │
│    ✅ PostgreSQL 15                      │
│    ✅ 24 tables, 170 rows                │
│    ✅ Connection pooling (port 6543)     │
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

```env
# Supabase (선택사항)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API Base URL (필수)
NEXT_PUBLIC_API_BASE_URL=https://badaauction-production.up.railway.app

# Admin Password (필수)
NEXT_PUBLIC_ADMIN_PASSWORD=8888

# OpenAI (선택사항)
OPENAI_API_KEY=sk-proj-...
```

### 백엔드 (Railway)

```env
# Database (필수)
USE_POSTGRESQL=true
DATABASE_URL=postgresql://postgres:***@db.spkeunlwkrqkdwunkufy.supabase.co:6543/postgres?sslmode=require

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

# Environment (필수)
ENVIRONMENT=production
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
GET /api/dashboard/stats  # 대시보드 통계
```

자세한 API 문서는 `/docs` 엔드포인트를 참고하세요.

---

## 🐛 트러블슈팅

### 배포 관련 문제

#### Vercel 빌드 실패
1. `lib/` 디렉토리가 누락되었는지 확인
2. TypeScript 에러 확인 (`npm run build`)
3. 환경 변수가 설정되었는지 확인

#### Railway 연결 실패
1. Health check 확인: `curl https://badaauction-production.up.railway.app/health`
2. Railway 로그 확인
3. 환경 변수 `USE_POSTGRESQL=true` 확인

#### API 연결 실패 (localhost 에러)
이미 수정 완료! 모든 파일이 `API_BASE_URL`을 사용합니다.

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

### 2026-01-30: 클라우드 배포 완료 🎉
- ✅ Phase 1-4 배포 완료
- ✅ Vercel + Railway + Supabase 인프라 구축
- ✅ localhost 하드코딩 문제 수정 (16개 파일)
- ✅ 총 비용: $5/월

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

### 선택사항

1. **이미지 마이그레이션** (Phase 5)
   - 로컬 이미지 → Supabase Storage
   - CDN 가속 활용
   - Railway 디스크 절약

2. **Custom Domain 설정**
   - Vercel에서 본인 도메인 연결
   - 예: `badaauction.com`

3. **성능 최적화**
   - 이미지 최적화 (Next.js Image)
   - API 캐싱 강화
   - Database 인덱스 최적화

4. **추가 기능**
   - 사용자 인증 시스템
   - 이메일 알림
   - 모바일 앱 (React Native)

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
