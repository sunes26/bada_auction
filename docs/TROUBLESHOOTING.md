# 트러블슈팅

## 배포 관련 문제

### API 404 에러 - URL이 `%7BAPI_BASE_URL%7D`로 인코딩됨

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

---

### Railway Admin API 404 에러

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

**해결 2**: admin.py 지연 로딩 및 에러 핸들링 추가

---

### Railway에서 빌드 실패

**증상**: Docker 빌드 중 에러

**해결 방법**:
1. `requirements.txt` 의존성 버전 확인
2. Dockerfile의 Python 버전 확인 (3.9 권장)
3. Railway 환경 변수 설정 확인

---

### Vercel 빌드 에러

**증상**: TypeScript 에러로 빌드 실패

**해결 방법**:
1. `npm run build`로 로컬에서 먼저 테스트
2. TypeScript 에러 수정
3. 환경 변수 설정 확인 (NEXT_PUBLIC_API_BASE_URL)

---

## FlareSolverr 관련

### Cloudflare 우회 실패

**증상**: G마켓/옥션 상품 정보 수집 실패

**해결 방법**:
1. FlareSolverr 서버 상태 확인
2. `FLARESOLVERR_URL` 환경 변수 확인
3. 세션 만료 시 재생성

**참고**: [FlareSolverr 설정 가이드](./md/FLARESOLVERR_SETUP.md)

---

## 데이터베이스 관련

### PostgreSQL 연결 실패

**증상**: `psycopg2.OperationalError: connection refused`

**해결 방법**:
1. `DATABASE_URL` 형식 확인: `postgresql://user:pass@host:port/db?sslmode=require`
2. Supabase 포트: Connection Pooling 사용 시 `6543`
3. `sslmode=require` 필수

### SQLite에서 PostgreSQL 마이그레이션

**참고**: [마이그레이션 가이드](./md/PHASE1_MIGRATION_COMPLETE.md)

---

## PlayAuto API 관련

### 쿠팡 상품 등록 오류

**증상**: "필수 구매 옵션이 존재하지 않습니다"

**현재 상태**: PlayAuto 고객센터 문의 중 (2026-02-08)

**참고**: [PlayAuto 카테고리 이슈](./md/PLAYAUTO_CATEGORY_ISSUE.md)

---

## 일반적인 문제

### 로컬에서 API 호출 안됨

**확인 사항**:
1. 백엔드 서버가 실행 중인지 확인 (http://localhost:8000/health)
2. `.env.local`에 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` 설정
3. CORS 설정 확인

### 이미지 업로드 실패

**확인 사항**:
1. Supabase Storage 설정 확인
2. `SUPABASE_SERVICE_ROLE_KEY` 환경 변수 확인
3. 버킷 정책 확인 (public 또는 authenticated)
