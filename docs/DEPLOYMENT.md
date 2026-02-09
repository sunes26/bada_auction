# 배포 가이드

## 배포 상태

모든 배포가 성공적으로 완료되었습니다!

| 서비스 | URL | 비용 |
|--------|-----|------|
| 🎨 **프론트엔드** | Vercel ([대시보드](https://vercel.com/dashboard)) | 무료 |
| 🔧 **백엔드 API** | `https://badaauction-production.up.railway.app` | $5/월 |
| 💾 **데이터베이스** | Supabase PostgreSQL | 무료 |
| 📦 **이미지 스토리지** | Supabase Storage | 무료 |

**총 운영 비용**: **$5/월**

---

## 아키텍처

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
│    ✅ Connection pooling (port 6543)     │
│    ✅ Storage (이미지)                   │
│    ✅ Cloudflare CDN                     │
│    ✅ $0/월                              │
└──────────────────────────────────────────┘
```

---

## 배포 단계

### Phase 1: PostgreSQL 마이그레이션 ✅
- Supabase PostgreSQL 설정
- 24개 테이블 생성
- SQLAlchemy ORM 모델 정의

**문서**: [PHASE1_MIGRATION_COMPLETE.md](./md/PHASE1_MIGRATION_COMPLETE.md)

### Phase 2: SQLAlchemy 백엔드 ✅
- DatabaseWrapper 구현 (40+ 메서드)
- Hybrid database selection (환경 변수 기반)
- 100% API 호환성

**문서**: [PHASE2_BACKEND_UPDATE_COMPLETE.md](./md/PHASE2_BACKEND_UPDATE_COMPLETE.md)

### Phase 3: Railway 백엔드 배포 ✅
- Docker 기반 배포
- Gunicorn + Uvicorn 설정
- 환경 변수 11개 설정

**문서**: [RAILWAY_DEPLOYMENT_COMPLETE.md](./md/RAILWAY_DEPLOYMENT_COMPLETE.md)

### Phase 4: Vercel 프론트엔드 배포 ✅
- Next.js 빌드 성공
- 환경 변수 4개 설정
- 자동 배포 설정

**문서**: [PHASE4_VERCEL_DEPLOYMENT.md](./md/PHASE4_VERCEL_DEPLOYMENT.md)

---

## 상태 확인

```bash
# 백엔드 헬스 체크
curl https://badaauction-production.up.railway.app/health

# Admin API 상태 확인 (Railway 재배포 후 2-3분 소요)
curl https://badaauction-production.up.railway.app/api/admin/system/status

# 등록된 라우트 확인
curl https://badaauction-production.up.railway.app/debug/routes | grep admin

# API 문서 확인
open https://badaauction-production.up.railway.app/docs
```

**⚠️ 주의**: Railway에 코드를 push한 후 재배포가 완료되기까지 **2-3분** 소요됩니다.

---

## 비용

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
