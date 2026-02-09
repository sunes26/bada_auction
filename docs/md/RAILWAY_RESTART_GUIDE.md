# Railway 서버 재시작 가이드

## 🎯 목적
PlayAuto 자동 동기화 설정을 활성화하기 위해 Railway 서버를 재시작합니다.

## 📋 방법 1: Railway 웹 대시보드 (가장 간단)

### 1단계: Railway 로그인
1. 브라우저에서 https://railway.app 접속
2. GitHub 계정으로 로그인

### 2단계: 프로젝트 선택
1. Dashboard에서 `badaauction-production` 프로젝트 클릭
2. 또는 직접 링크: https://railway.app/project/[your-project-id]

### 3단계: 서버 재시작
1. 백엔드 서비스 클릭 (Python/FastAPI)
2. 오른쪽 상단 "..." 메뉴 클릭
3. **"Redeploy"** 선택
4. 또는 **"Restart"** 선택

### 4단계: 재시작 확인 (2-3분 소요)
```bash
# Health check
curl https://badaauction-production.up.railway.app/health

# PlayAuto 설정 확인 (enabled가 true인지)
curl https://badaauction-production.up.railway.app/api/playauto/settings

# 스케줄러 상태 확인 (playauto.running이 true인지)
curl https://badaauction-production.up.railway.app/api/scheduler/status
```

---

## 📋 방법 2: Git Push (자동 재배포)

### 1단계: 더미 커밋 생성
```bash
cd C:\Users\User\Documents\coding\onbaek-ai

# 빈 커밋 생성
git commit --allow-empty -m "Restart Railway to enable PlayAuto auto-sync"
```

### 2단계: Railway에 푸시
```bash
git push
```

### 3단계: 재배포 대기
- Railway가 자동으로 감지하고 재배포 시작
- 약 2-3분 소요

---

## 📋 방법 3: Railway CLI (고급)

### 설치
```bash
# Windows
npm i -g @railway/cli

# 또는
curl -fsSL https://railway.app/install.sh | sh
```

### 사용
```bash
# 로그인
railway login

# 프로젝트 연결
railway link

# 재시작
railway service restart
```

---

## ✅ 재시작 후 확인 사항

### 1. PlayAuto 설정 확인
```bash
curl https://badaauction-production.up.railway.app/api/playauto/settings
```

**예상 결과**:
```json
{
  "enabled": true,           // ✅ true여야 함!
  "auto_sync_enabled": true, // ✅ true여야 함!
  "auto_sync_interval": 30
}
```

### 2. 스케줄러 상태 확인
```bash
curl https://badaauction-production.up.railway.app/api/scheduler/status
```

**예상 결과**:
```json
{
  "playauto": {
    "running": true,  // ✅ true여야 함!
    "jobs": [
      {
        "id": "playauto_auto_fetch_orders",
        "name": "플레이오토 주문 자동 수집",
        "next_run_time": "2026-02-05 02:15:00..."
      }
    ]
  }
}
```

### 3. Railway 로그 확인
Railway 대시보드 → Deployments → Latest → Logs

찾아야 할 메시지:
```
[PLAYAUTO] 스케줄러 시작 완료
[PLAYAUTO] 주문 자동 수집 작업 등록 (30분마다)
[PLAYAUTO] 송장 자동 업로드 작업 등록 (매일 오전 9시)
```

### 4. 수동 주문 수집 테스트
```bash
curl "https://badaauction-production.up.railway.app/api/playauto/orders?auto_sync=true&start_date=2026-01-29&end_date=2026-02-05&limit=100"
```

---

## 🎉 성공 확인

모든 것이 정상이면:
- ✅ `enabled: true`
- ✅ `auto_sync_enabled: true`
- ✅ `playauto.running: true`
- ✅ 30분마다 자동 주문 수집
- ✅ 새 주문 시 실시간 알림

---

## 🚨 문제 해결

### 여전히 `enabled: false`인 경우

#### 원인: Railway 환경 변수 미설정
Railway 대시보드에서 환경 변수 확인:

**Settings → Variables**

필수 변수:
```env
PLAYAUTO_API_KEY=UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj
PLAYAUTO_SOLUTION_KEY=d4bd64ca14e4bb3727e3730f3607a7af7d78f7e9e08dcb3494cf8cd4
PLAYAUTO_EMAIL=haeseong050321@gmail.com
PLAYAUTO_PASSWORD=jhs6312**
PLAYAUTO_API_URL=https://openapi.playauto.io/api
```

설정 후 다시 재시작!

---

## 📞 추가 도움

문제가 계속되면:
1. Railway 로그 전체 복사
2. API 응답 복사:
   - `/health`
   - `/api/playauto/settings`
   - `/api/scheduler/status`
3. 보고
