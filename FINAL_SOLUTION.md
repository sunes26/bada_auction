# ✅ PlayAuto 자동 동기화 최종 해결 방법

## 📊 현재 상황

### 완료된 작업 ✅
1. ✅ PlayAuto API 연결 테스트 완료 (정상)
2. ✅ DB에 auto_sync 설정 저장 완료
3. ✅ Git 커밋 & 푸시 완료 (2회)
4. ✅ Railway 재배포 진행 중

### 남은 문제 ⚠️
```python
# backend/playauto/scheduler.py (line 91-97)
enabled = db.get_playauto_setting("enabled") == "true"

if not enabled:
    print("[PLAYAUTO] 비활성화되어 있어 스케줄러를 시작하지 않습니다")
    return  # ← DB의 enabled가 false면 여기서 중단!
```

**문제**: DB의 `enabled` 플래그가 `false`이면 스케줄러가 시작되지 않음

---

## 🎯 최종 해결 방법 (선택)

### 방법 1: Railway 환경 변수 추가 ⭐ (가장 확실)

#### 단계:
1. **Railway 대시보드 접속**
   - https://railway.app
   - 로그인 → `badaauction-production` 프로젝트 클릭

2. **환경 변수 추가**
   - **Settings** → **Variables** 탭
   - **New Variable** 클릭
   - 다음 2개 변수 추가:

   ```
   이름: PLAYAUTO_ENABLED
   값: true
   ```

   ```
   이름: PLAYAUTO_AUTO_SYNC_ENABLED
   값: true
   ```

3. **저장 및 재배포**
   - 변수 추가하면 자동으로 재배포됨 (2-3분)

4. **확인**
   ```bash
   curl https://badaauction-production.up.railway.app/api/scheduler/status
   ```

   → `"playauto": { "running": true }` 확인!

#### 장점:
- ✅ 가장 깨끗하고 명확한 해결책
- ✅ 재배포 후 즉시 작동
- ✅ DB 설정과 무관하게 작동

---

### 방법 2: Railway CLI로 스크립트 실행

Railway CLI가 설치되어 있다면:

```bash
# Railway CLI 설치 (없는 경우)
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# DB 설정 업데이트 스크립트 실행
railway run python backend/update_production_db_settings.py

# 서비스 재시작
railway service restart
```

---

### 방법 3: 코드 수정 (임시 해결)

`backend/playauto/scheduler.py` 파일 수정:

```python
def start_scheduler():
    """스케줄러 시작"""
    try:
        # 설정 확인
        db = get_db()

        # ==== 이 부분을 수정 ====
        # enabled = db.get_playauto_setting("enabled") == "true"
        enabled = os.getenv("PLAYAUTO_ENABLED", "true") == "true"  # 환경변수 우선
        # =======================

        auto_sync_enabled = db.get_playauto_setting("auto_sync_enabled") == "true"
        auto_sync_interval = int(db.get_playauto_setting("auto_sync_interval") or "30")
```

수정 후:
```bash
git add backend/playauto/scheduler.py
git commit -m "Use environment variable for PlayAuto enabled flag"
git push
```

---

## 🚀 추천 순서

### 즉시 해결하려면:
**→ 방법 1 (Railway 환경 변수)**
- 5분 이내 해결 가능
- 가장 확실함

### CLI 사용 가능하면:
**→ 방법 2 (Railway CLI)**
- DB를 직접 업데이트
- 환경 변수 없이도 작동

### 코드로 해결하려면:
**→ 방법 3 (코드 수정)**
- 코드를 직접 수정하여 환경 변수 우선 사용

---

## ✅ 성공 확인

모든 방법 실행 후:

### 1. 스케줄러 상태
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
        "next_run_time": "..."
      }
    ]
  }
}
```

### 2. Railway 로그
```
[PLAYAUTO] 스케줄러 시작 완료
[PLAYAUTO] 주문 자동 수집 작업 등록 (30분마다)
[PLAYAUTO] 송장 자동 업로드 작업 등록 (매일 오전 9시)
```

### 3. 수동 테스트
```bash
curl "https://badaauction-production.up.railway.app/api/playauto/orders?auto_sync=true"
```

---

## 🎉 완료 후

- ✅ 30분마다 자동 주문 수집
- ✅ 새 주문 시 실시간 알림
- ✅ 송장 자동 업로드 (매일 오전 9시)
- ✅ 프론트엔드에서 실시간 확인 가능

---

## 📞 지원

**선택 가이드**:
- Railway 대시보드 접근 가능 → **방법 1**
- Railway CLI 사용 경험 있음 → **방법 2**
- 코드 수정 선호 → **방법 3**

**가장 빠르고 확실한 방법**: 방법 1 (Railway 환경 변수)
