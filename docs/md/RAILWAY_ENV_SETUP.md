# Railway 환경 변수 설정 가이드

## 🎯 목적
Railway에서 PlayAuto 자동 동기화가 작동하도록 환경 변수를 설정합니다.

## ⚠️ 현재 문제

코드 확인 결과, `start_scheduler()` 함수가 DB에서 `enabled` 설정을 체크합니다:

```python
def start_scheduler():
    db = get_db()
    enabled = db.get_playauto_setting("enabled") == "true"

    if not enabled:
        print("[PLAYAUTO] 플레이오토가 비활성화되어 있어 스케줄러를 시작하지 않습니다")
        return  # ← 여기서 중단!
```

**문제**: DB 설정이 `enabled=false`이면 스케줄러가 시작되지 않습니다.

## 🔧 해결 방법

### 방법 1: Railway 환경 변수 설정 (권장)

Railway 대시보드에서 환경 변수를 추가하면, DB 설정보다 우선됩니다.

#### 1단계: Railway 대시보드 접속
```
https://railway.app/project/[your-project-id]/service/[your-service-id]/variables
```

#### 2단계: 환경 변수 추가

**Settings → Variables → New Variable** 클릭 후 다음 추가:

```env
# PlayAuto 자동 동기화 활성화 (중요!)
PLAYAUTO_AUTO_SYNC_ENABLED=true
PLAYAUTO_ENABLED=true

# 기존 변수가 없다면 추가
PLAYAUTO_API_KEY=UMEl86zDkRawuO6vJmR3RXTkOROWltT3YqxlJ5nj
PLAYAUTO_SOLUTION_KEY=d4bd64ca14e4bb3727e3730f3607a7af7d78f7e9e08dcb3494cf8cd4
PLAYAUTO_EMAIL=haeseong050321@gmail.com
PLAYAUTO_PASSWORD=jhs6312**
PLAYAUTO_API_URL=https://openapi.playauto.io/api
```

#### 3단계: 저장 및 재배포
- 변수 추가 후 자동으로 재배포됨
- 또는 수동으로 "Redeploy" 클릭

---

### 방법 2: 코드 수정 (임시)

`backend/playauto/scheduler.py` 파일을 수정하여 강제로 활성화:

```python
def start_scheduler():
    try:
        # 설정 확인
        db = get_db()

        # ===== 여기를 수정 =====
        # enabled = db.get_playauto_setting("enabled") == "true"
        enabled = True  # 강제 활성화
        # =======================

        auto_sync_enabled = db.get_playauto_setting("auto_sync_enabled") == "true"
        auto_sync_interval = int(db.get_playauto_setting("auto_sync_interval") or "30")
```

단점: 코드를 직접 수정해야 하므로 유지보수가 어려움

---

### 방법 3: DB 설정을 직접 수정하는 스크립트 실행

Railway에 SSH로 접속하거나, API를 통해 DB 설정을 변경:

```python
# update_db_settings.py
from database.db_wrapper import get_db

db = get_db()
db.save_playauto_setting('enabled', 'true', notes='PlayAuto 활성화')
db.save_playauto_setting('auto_sync_enabled', 'true', notes='자동 동기화 활성화')
print("설정 완료!")
```

이 스크립트를 Railway에서 실행:
```bash
railway run python update_db_settings.py
```

---

## ✅ 추천 순서

1. **방법 1** (환경 변수) - 가장 깨끗하고 유지보수 용이
2. **방법 3** (DB 스크립트) - 환경 변수 설정이 어려운 경우
3. **방법 2** (코드 수정) - 마지막 수단

---

## 📊 설정 후 확인

### 1. Railway 로그 확인
```
[PLAYAUTO] 스케줄러 시작 완료
[PLAYAUTO] 주문 자동 수집 작업 등록 (30분마다)
```

### 2. API 확인
```bash
curl https://badaauction-production.up.railway.app/api/scheduler/status
```

예상 결과:
```json
{
  "playauto": {
    "running": true,  // ✅
    "jobs": [...]
  }
}
```

### 3. 수동 테스트
```bash
curl "https://badaauction-production.up.railway.app/api/playauto/orders?auto_sync=true"
```

---

## 🎉 성공!

모든 것이 정상이면:
- ✅ Railway 로그에 "PlayAuto 스케줄러 시작" 표시
- ✅ `playauto.running: true`
- ✅ 30분마다 자동 주문 수집
- ✅ 실시간 알림 작동
