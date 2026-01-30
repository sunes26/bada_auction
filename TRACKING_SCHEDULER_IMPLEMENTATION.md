# 송장 자동 업로드 스케줄러 구현 완료

## 📋 개요

플레이오토로 송장 정보를 자동으로 업로드하는 스케줄러 시스템이 완성되었습니다.

### 주요 기능
- ⏰ **자동 스케줄 실행**: 매일 지정한 시간에 자동으로 송장 업로드
- 🔄 **재시도 로직**: 실패 시 자동 재시도 (지수 백오프)
- 📊 **진행률 추적**: 실시간 업로드 진행 상황 모니터링
- 🔔 **알림 시스템**: Discord/Slack 웹훅을 통한 완료 알림
- 📝 **상세 로그**: 각 주문별 업로드 성공/실패 내역 기록

## 🏗️ 구현 상세

### 1. 데이터베이스 스키마 (`backend/database/schema.sql`)

#### 스케줄러 설정 테이블
```sql
CREATE TABLE IF NOT EXISTS tracking_upload_scheduler (
    id INTEGER PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT 0,
    schedule_time TEXT NOT NULL DEFAULT '17:00',
    retry_count INTEGER NOT NULL DEFAULT 3,
    notify_discord BOOLEAN DEFAULT 0,
    notify_slack BOOLEAN DEFAULT 0,
    discord_webhook TEXT,
    slack_webhook TEXT,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 작업 추적 테이블
```sql
CREATE TABLE IF NOT EXISTS tracking_upload_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,  -- 'scheduled' or 'manual'
    status TEXT NOT NULL,     -- 'pending', 'running', 'completed', 'failed'
    total_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    progress_percent REAL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 상세 로그 테이블
```sql
CREATE TABLE IF NOT EXISTS tracking_upload_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    order_id INTEGER,
    order_no TEXT,
    carrier_code TEXT,
    tracking_number TEXT,
    status TEXT,              -- 'success' or 'failed'
    retry_attempt INTEGER DEFAULT 0,
    error_message TEXT,
    uploaded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES tracking_upload_jobs(id)
);
```

### 2. 백엔드 서비스

#### TrackingUploadService (`backend/services/tracking_upload_service.py`)

**주요 메서드:**
- `execute_upload()`: 송장 업로드 작업 실행
- `_upload_single_tracking()`: 개별 송장 업로드 (재시도 포함)
- `_get_pending_orders()`: 업로드 대기 중인 주문 조회
- `_send_notifications()`: Discord/Slack 알림 발송

**특징:**
- ✅ 지수 백오프 재시도 (2^attempt 초)
- ✅ 진행률 실시간 업데이트
- ✅ 상세 로그 기록
- ✅ 성공 시 로컬 DB에 업로드 완료 표시

#### TrackingScheduler (`backend/services/tracking_scheduler.py`)

**주요 메서드:**
- `start()`: 스케줄러 시작
- `stop()`: 스케줄러 중지
- `update_schedule()`: 스케줄 업데이트
- `_scheduled_upload()`: 예약된 시간에 업로드 실행

**특징:**
- ✅ APScheduler 사용 (AsyncIOScheduler)
- ✅ Cron 트리거 (매일 지정 시간 실행)
- ✅ 자동 다음 실행 시각 계산

### 3. API 엔드포인트 (`backend/api/tracking_scheduler.py`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/tracking-scheduler/config` | 스케줄러 설정 조회 |
| POST | `/api/tracking-scheduler/config` | 스케줄러 설정 업데이트 |
| POST | `/api/tracking-scheduler/execute` | 수동 송장 업로드 실행 |
| GET | `/api/tracking-scheduler/jobs/recent` | 최근 작업 목록 조회 |
| GET | `/api/tracking-scheduler/jobs/{job_id}` | 작업 상태 조회 |
| GET | `/api/tracking-scheduler/jobs/{job_id}/details` | 작업 상세 내역 조회 |
| GET | `/api/tracking-scheduler/pending-count` | 업로드 대기 주문 수 조회 |

### 4. 프론트엔드 UI (`components/pages/TrackingSchedulerPage.tsx`)

#### 주요 섹션:
1. **현황 카드**
   - 업로드 대기 중인 주문 수
   - 마지막 실행 시각
   - 다음 실행 예정 시각

2. **스케줄러 설정**
   - 활성화/비활성화 토글
   - 실행 시간 설정 (HH:MM)
   - 재시도 횟수 설정 (0-10)
   - Discord/Slack 알림 설정

3. **실행 기록**
   - 최근 10개 작업 내역
   - 작업별 성공/실패 건수
   - 진행률 표시
   - 실시간 새로고침

#### 통합:
- UnifiedOrderManagementPage에 새 탭으로 추가
- 탭 이름: "송장 스케줄러"
- 아이콘: Clock

## 🚀 사용 방법

### 1. 스케줄러 설정

1. 주문 관리 페이지 > "송장 스케줄러" 탭 이동
2. "자동 업로드 활성화" 토글 ON
3. 원하는 실행 시간 설정 (예: 17:00)
4. 재시도 횟수 설정 (기본: 3회)
5. (선택) Discord/Slack 웹훅 URL 입력
6. "설정 저장" 버튼 클릭

### 2. 수동 실행

- "수동 실행" 버튼 클릭
- 업로드 대기 중인 주문이 없으면 버튼 비활성화

### 3. 작업 모니터링

- 실행 기록에서 각 작업의 상태 확인
- 성공/실패 건수 및 진행률 확인
- 30초마다 자동 새로고침

## 📊 동작 흐로우

```
1. 스케줄 시간 도래 또는 수동 실행
   ↓
2. DB에서 업로드 대기 중인 주문 조회
   (tracking_number가 있지만 playauto_uploaded = 0)
   ↓
3. 각 주문별로 순차 업로드
   ├─ 성공 → DB에 업로드 완료 표시
   ├─ 실패 → 재시도 (최대 3회)
   └─ 최종 실패 → 에러 로그 기록
   ↓
4. 전체 작업 완료
   ↓
5. (선택) Discord/Slack 알림 발송
```

## 🔧 설정 옵션

### 스케줄러 설정
- `enabled`: 자동 실행 활성화 여부
- `schedule_time`: 실행 시간 (HH:MM 형식)
- `retry_count`: 재시도 횟수 (0-10)

### 알림 설정
- `notify_discord`: Discord 알림 활성화
- `notify_slack`: Slack 알림 활성화
- `discord_webhook`: Discord 웹훅 URL
- `slack_webhook`: Slack 웹훅 URL

## 📝 업로드 대상 주문

다음 조건을 모두 만족하는 주문만 업로드:
- ✅ `tracking_number`가 입력됨
- ✅ `carrier_code`가 입력됨
- ✅ `playauto_uploaded = 0` (아직 업로드 안됨)
- ✅ `order_status`가 '취소', '반품', '교환'이 아님

## 🎯 주요 이점

1. **자동화**: 수동 작업 불필요, 매일 정해진 시간에 자동 실행
2. **안정성**: 재시도 로직으로 일시적 오류 대응
3. **추적성**: 모든 업로드 내역 상세 기록
4. **가시성**: 실시간 진행 상황 및 통계 확인
5. **알림**: 작업 완료 시 즉시 알림

## 🐛 트러블슈팅

### 스케줄러가 실행되지 않을 때
1. 스케줄러 활성화 여부 확인
2. 다음 실행 예정 시각 확인
3. 백엔드 서버 로그 확인

### 업로드 실패가 반복될 때
1. 플레이오토 API 설정 확인
2. 송장번호/택배사 코드 형식 확인
3. 에러 메시지 확인 (작업 상세 내역)

### 알림이 오지 않을 때
1. 웹훅 URL 정확성 확인
2. Discord/Slack 서버 상태 확인
3. 알림 활성화 여부 확인

## 📦 파일 목록

### 백엔드
- `backend/database/schema.sql` - DB 스키마 정의
- `backend/services/tracking_upload_service.py` - 업로드 서비스
- `backend/services/tracking_scheduler.py` - 스케줄러 서비스
- `backend/api/tracking_scheduler.py` - API 라우터
- `backend/main.py` - 스케줄러 시작/종료 통합

### 프론트엔드
- `components/pages/TrackingSchedulerPage.tsx` - UI 컴포넌트
- `components/pages/UnifiedOrderManagementPage.tsx` - 탭 통합

## ✅ 구현 완료 사항

- [x] 데이터베이스 스키마 설계
- [x] 백엔드 업로드 서비스 구현
- [x] 백엔드 스케줄러 서비스 구현
- [x] API 엔드포인트 구현
- [x] 프론트엔드 UI 구현
- [x] main.py에 스케줄러 통합
- [x] 재시도 로직 구현
- [x] 진행률 추적 구현
- [x] Discord/Slack 알림 구현
- [x] 상세 로그 기록 구현

## 🎉 결론

송장 자동 업로드 스케줄러가 완전히 구현되었습니다. 이제 매일 정해진 시간에 자동으로 송장 정보가 플레이오토로 업로드되며, 모든 과정이 상세하게 기록되고 모니터링됩니다.

사용자는 대시보드에서 간편하게 설정을 변경하고, 작업 내역을 확인하며, 필요시 수동으로도 실행할 수 있습니다.
