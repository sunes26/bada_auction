# 로컬 개발 환경 설정

## 필수 요구사항

- **Node.js**: 18.x 이상
- **Python**: 3.9 이상
- **Git**: 최신 버전

## 1. 저장소 클론

```bash
git clone https://github.com/sunes26/bada_auction.git
cd bada_auction
```

## 2. 환경 변수 설정

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

## 3. 프론트엔드 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 시작
npm run dev
```

프론트엔드가 http://localhost:3000 에서 실행됩니다.

## 4. 백엔드 설치 및 실행

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

## 5. 접속 확인

- **프론트엔드**: http://localhost:3000
- **백엔드 API 문서**: http://localhost:8000/docs
- **관리자 페이지**: http://localhost:3000/admin (비밀번호: 8888)

---

## 환경 변수 상세

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

**⚠️ 주의**: 로컬 개발 시 `.env.local`에는 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`을 사용하세요.

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
