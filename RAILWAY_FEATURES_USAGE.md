# Railway에서 사용하는 기능 정리

> **우리 프로젝트가 Railway에서 실제로 사용할 기능들**

---

## 📊 현재 백엔드가 하는 일

```python
# backend/main.py
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI()

# 1. 웹 서버 실행
uvicorn.run("main:app", host="0.0.0.0", port=8000)

# 2. 스케줄러 (백그라운드 작업)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 플레이오토 스케줄러 시작
    start_playauto_scheduler()

    # 상품 모니터링 스케줄러 시작
    start_monitor_scheduler()

    # 백업 스케줄러 시작
    start_backup_scheduler()

    # 송장 업로드 스케줄러 시작
    start_tracking_scheduler()

    yield

    # 종료 시 정리
    stop_all_schedulers()
```

**현재 로컬에서 실행 중인 작업들**:
1. ✅ FastAPI 웹 서버
2. ✅ 10분마다 가격 모니터링
3. ✅ 1시간마다 플레이오토 주문 동기화
4. ✅ 6시간마다 송장 업로드
5. ✅ 매일 새벽 2시 백업
6. ✅ API 요청 처리 (AI 생성, 상품 관리 등)

---

## 🚂 Railway에서 사용할 기능

### 1. **컨테이너 실행 (Web Service)**

**우리가 필요한 것**:
```
FastAPI 서버를 24/7 실행
```

**Railway 기능**:
```yaml
# railway.json
{
  "deploy": {
    "startCommand": "gunicorn -c gunicorn_conf.py main:app",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**제공되는 것**:
- ✅ 컨테이너 자동 실행
- ✅ 크래시 시 자동 재시작
- ✅ 무제한 실행 시간
- ✅ 공개 URL: `https://your-app.railway.app`
- ✅ HTTPS 자동 설정

**비용**: $5/월 (512MB RAM, 1 vCPU)

---

### 2. **Cron Jobs (스케줄 작업)**

**우리가 필요한 것**:
```
현재 APScheduler로 실행 중인 백그라운드 작업들:
- 10분마다: 상품 가격 모니터링
- 1시간마다: 플레이오토 주문 동기화
- 6시간마다: 송장 업로드 체크
- 매일 새벽 2시: 데이터베이스 백업
```

**Railway 기능**:
```json
// railway.json
{
  "deploy": {
    "cron": [
      {
        "schedule": "*/10 * * * *",  // 10분마다
        "command": "curl -X POST https://your-app.railway.app/cron/monitor-products -H 'Authorization: Bearer SECRET'"
      },
      {
        "schedule": "0 * * * *",     // 매시간
        "command": "curl -X POST https://your-app.railway.app/cron/sync-playauto"
      },
      {
        "schedule": "0 */6 * * *",   // 6시간마다
        "command": "curl -X POST https://your-app.railway.app/cron/tracking-upload"
      },
      {
        "schedule": "0 2 * * *",     // 매일 새벽 2시
        "command": "curl -X POST https://your-app.railway.app/cron/backup"
      }
    ]
  }
}
```

**제공되는 것**:
- ✅ Cron 스케줄 자동 실행
- ✅ APScheduler 불필요 (제거 가능)
- ✅ 실행 로그 확인 가능
- ✅ 실패 시 재시도

**비용**: 무료 (Web Service에 포함)

---

### 3. **환경 변수 관리**

**우리가 필요한 것**:
```
현재 .env.local에 있는 민감 정보들:
- DATABASE_URL
- OPENAI_API_KEY
- PLAYAUTO_EMAIL
- PLAYAUTO_PASSWORD
- SLACK_WEBHOOK_URL
- DISCORD_WEBHOOK_URL
- SUPABASE_URL
- SUPABASE_KEY
```

**Railway 기능**:
```
Railway Dashboard → Variables 탭

DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
PLAYAUTO_EMAIL=your@email.com
PLAYAUTO_PASSWORD=***
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ENVIRONMENT=production
PORT=8000
```

**제공되는 것**:
- ✅ 암호화 저장
- ✅ 웹에서 관리 (파일 불필요)
- ✅ 자동으로 앱에 주입
- ✅ 히스토리 관리
- ✅ 팀원과 공유 가능

**비용**: 무료

---

### 4. **PostgreSQL 데이터베이스 (선택)**

**우리가 필요한 것**:
```
현재: SQLite (monitoring.db)
배포 후: PostgreSQL
```

**Railway 기능**:
```
Railway 내장 PostgreSQL 또는 Supabase 연결

옵션 1: Railway PostgreSQL
- New → Database → Add PostgreSQL
- 자동으로 DATABASE_URL 생성

옵션 2: Supabase (추천)
- 무료 500MB
- 별도 환경 변수로 연결
```

**제공되는 것** (Railway PostgreSQL 사용 시):
- ✅ PostgreSQL 15
- ✅ 자동 백업 (매일)
- ✅ 1GB 스토리지
- ✅ 동일 네트워크 (빠른 연결)

**비용**:
- Railway PostgreSQL: $5/월
- Supabase: $0 (무료)

**추천**: Supabase 사용 (무료 + 백업 기능 더 좋음)

---

### 5. **로그 관리**

**우리가 필요한 것**:
```python
# 현재 로컬 콘솔 출력
print("[INFO] 서버 시작...")
logger.info("상품 모니터링 완료")
```

**Railway 기능**:
```
Railway Dashboard → Logs 탭

실시간 로그 스트리밍:
[2026-01-30 16:00:00] INFO: 서버 시작 중...
[2026-01-30 16:00:10] INFO: 상품 모니터링 시작
[2026-01-30 16:00:45] INFO: 100개 상품 체크 완료
[2026-01-30 16:00:46] ERROR: OpenAI API 오류 발생
```

**제공되는 것**:
- ✅ 실시간 로그 확인
- ✅ 최근 7일 보관
- ✅ 검색 및 필터링
- ✅ 다운로드 가능
- ✅ Webhook으로 외부 전송 가능

**비용**: 무료

---

### 6. **자동 배포 (GitHub 연동)**

**우리가 필요한 것**:
```
코드 수정 → 배포
```

**Railway 기능**:
```
GitHub 저장소 연동

1. Railway와 GitHub 연결
2. 저장소 선택: your-username/onbaek-ai
3. 브랜치 선택: main

이후:
git push origin main
→ Railway가 자동 감지
→ 자동 빌드
→ 자동 배포 (무중단)
→ Health check 통과 확인
```

**제공되는 것**:
- ✅ Git push만 하면 자동 배포
- ✅ 빌드 로그 실시간 확인
- ✅ 배포 실패 시 롤백
- ✅ PR 미리보기 (Preview Deploy)

**비용**: 무료

---

### 7. **Health Check**

**우리가 필요한 것**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Railway 기능**:
```json
// railway.json
{
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

**제공되는 것**:
- ✅ 배포 후 Health check 자동 실행
- ✅ 실패 시 자동 롤백
- ✅ 주기적 Health check
- ✅ 다운 시 자동 재시작

**비용**: 무료

---

### 8. **도메인 연결 (선택)**

**우리가 필요한 것**:
```
현재: https://xxxx.railway.app
원하는: https://api.yourdomain.com
```

**Railway 기능**:
```
Railway Dashboard → Settings → Domains

1. Custom Domain 추가
2. DNS 레코드 설정:
   CNAME api yourdomain.com

3. 자동 HTTPS 적용 (Let's Encrypt)
```

**제공되는 것**:
- ✅ 커스텀 도메인 무제한
- ✅ 자동 HTTPS
- ✅ 자동 갱신

**비용**: 무료 (도메인 구매 비용만 연 $10-15)

---

### 9. **모니터링 & 메트릭**

**Railway 기능**:
```
Railway Dashboard → Metrics 탭

실시간 확인:
- CPU 사용량
- 메모리 사용량
- 네트워크 트래픽
- 응답 시간
- 에러율
```

**제공되는 것**:
- ✅ 실시간 메트릭
- ✅ 알림 설정 (CPU 80% 이상 시)
- ✅ 7일 히스토리

**비용**: 무료

---

### 10. **팀 협업 (선택)**

**Railway 기능**:
```
Settings → Team

팀원 초대:
- viewer@company.com → Read Only
- dev@company.com → Full Access
```

**제공되는 것**:
- ✅ 팀원 초대
- ✅ 역할 기반 권한
- ✅ 활동 로그

**비용**: 무료 (5명까지)

---

## 📋 우리 프로젝트 사용 요약

### 필수 기능 (무료/저비용)

| 기능 | 용도 | 비용 |
|-----|-----|-----|
| **Web Service** | FastAPI 서버 실행 | $5/월 |
| **Cron Jobs** | 스케줄러 (모니터링, 동기화) | 무료 |
| **환경 변수** | API 키, DB URL 관리 | 무료 |
| **로그** | 디버깅 및 모니터링 | 무료 |
| **자동 배포** | GitHub 연동 | 무료 |
| **Health Check** | 자동 재시작 | 무료 |
| **메트릭** | CPU, 메모리 모니터링 | 무료 |

**총 비용**: **$5/월**

---

### 선택 기능 (필요 시)

| 기능 | 용도 | 비용 |
|-----|-----|-----|
| **PostgreSQL** | DB (Supabase로 대체 가능) | $5/월 또는 $0 |
| **커스텀 도메인** | api.yourdomain.com | 무료 (도메인비만) |
| **팀 협업** | 직원/개발자 초대 | 무료 |

---

## 🔄 현재 vs 배포 후 비교

### 현재 (로컬)

```
PC 실행 중:
├─ FastAPI 서버 (main.py)
├─ APScheduler
│  ├─ 10분마다 모니터링
│  ├─ 1시간마다 동기화
│  ├─ 6시간마다 송장
│  └─ 매일 백업
├─ SQLite (monitoring.db)
└─ 로그 (콘솔)

문제점:
❌ PC 꺼지면 모든 작업 중단
❌ 외부 접근 불가
❌ 백업 수동
❌ 관리 어려움
```

### 배포 후 (Railway)

```
Railway:
├─ FastAPI 서버 (24/7 실행)
├─ Railway Cron Jobs
│  ├─ 10분마다 /cron/monitor-products
│  ├─ 1시간마다 /cron/sync-playauto
│  ├─ 6시간마다 /cron/tracking
│  └─ 매일 /cron/backup
├─ PostgreSQL (Supabase)
├─ 로그 (대시보드)
├─ 메트릭 (CPU, 메모리)
└─ 자동 배포 (Git push)

장점:
✅ 24/7 자동 실행
✅ 전 세계 어디서든 접근
✅ 자동 백업
✅ 웹 대시보드로 관리
✅ 자동 재시작
✅ 무중단 배포
```

---

## 🎯 실제 설정 예시

### 1. railway.json 파일

```json
{
  "$schema": "https://railway.app/railway.schema.json",

  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },

  "deploy": {
    "startCommand": "cd backend && gunicorn -c gunicorn_conf.py main:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,

    "cron": [
      {
        "schedule": "*/10 * * * *",
        "command": "curl -X POST https://your-app.railway.app/cron/monitor-products -H 'Authorization: Bearer $CRON_SECRET'"
      },
      {
        "schedule": "0 * * * *",
        "command": "curl -X POST https://your-app.railway.app/cron/sync-playauto -H 'Authorization: Bearer $CRON_SECRET'"
      },
      {
        "schedule": "0 2 * * *",
        "command": "curl -X POST https://your-app.railway.app/cron/backup -H 'Authorization: Bearer $CRON_SECRET'"
      }
    ]
  }
}
```

### 2. 환경 변수 (Railway Dashboard)

```env
# Database
DATABASE_URL=postgresql://postgres:***@db.xxxxx.supabase.co:5432/postgres

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...

# OpenAI
OPENAI_API_KEY=sk-...

# Playauto
PLAYAUTO_EMAIL=your@email.com
PLAYAUTO_PASSWORD=***

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# App Config
ENVIRONMENT=production
PORT=8000
CRON_SECRET=your-random-secret
```

### 3. Cron 엔드포인트 (backend/api/cron.py)

```python
from fastapi import APIRouter, Header, HTTPException
import os

router = APIRouter(prefix="/cron", tags=["Cron"])

CRON_SECRET = os.getenv("CRON_SECRET")

def verify_cron(authorization: str = Header(None)):
    if authorization != f"Bearer {CRON_SECRET}":
        raise HTTPException(401, "Unauthorized")

@router.post("/monitor-products")
async def cron_monitor(auth: None = Depends(verify_cron)):
    """10분마다 실행 - 상품 가격 모니터링"""
    from monitor.product_monitor import check_all_products
    await check_all_products()
    return {"status": "success"}

@router.post("/sync-playauto")
async def cron_sync(auth: None = Depends(verify_cron)):
    """1시간마다 실행 - 플레이오토 주문 동기화"""
    from playauto.scheduler import sync_orders
    await sync_orders()
    return {"status": "success"}

@router.post("/backup")
async def cron_backup(auth: None = Depends(verify_cron)):
    """매일 새벽 2시 실행 - 백업"""
    from backup.scheduler import create_backup
    await create_backup()
    return {"status": "success"}
```

---

## 💡 결론

**Railway에서 사용할 핵심 기능**:

1. ✅ **Web Service** - FastAPI 24/7 실행 ($5/월)
2. ✅ **Cron Jobs** - 스케줄러 대체 (무료)
3. ✅ **환경 변수** - API 키 관리 (무료)
4. ✅ **로그** - 디버깅 (무료)
5. ✅ **자동 배포** - Git push (무료)
6. ✅ **Health Check** - 자동 재시작 (무료)

**총 비용**: **$5/월**
**얻는 것**: 24/7 실행, 자동 관리, 전 세계 접근

**대안 비용**:
- PC 24시간 가동: $65/월 (전기세)
- Vercel Pro + Upstash: $30/월

→ Railway가 가장 저렴하고 기능 완벽!
