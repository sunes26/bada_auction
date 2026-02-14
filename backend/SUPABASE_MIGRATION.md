# Supabase PostgreSQL 마이그레이션 가이드

## 개요

현재 시스템은 다음 두 가지 방식으로 작동합니다:

1. **Railway PostgreSQL**: 자동으로 스키마 적용 (추가 작업 불필요)
2. **Supabase PostgreSQL**: 수동으로 SQL 실행 필요

## Supabase DB 사용 여부 확인

### Railway 환경 변수 확인

```bash
# Railway CLI
railway variables

# 또는 Railway Dashboard → Variables 탭
```

**확인할 변수:**
```bash
DATABASE_URL=postgresql://...
```

- `railway.app` 포함 → Railway PostgreSQL ✅ (추가 작업 불필요)
- `supabase.co` 포함 → Supabase PostgreSQL ⚠️ (아래 절차 진행)

---

## Supabase PostgreSQL 사용 시 마이그레이션

### 1. Supabase Dashboard 접속

1. https://app.supabase.com 로그인
2. 프로젝트 선택: `spkeunlwkrqkdwunkufy`
3. 좌측 메뉴 → **SQL Editor** 클릭

### 2. 인덱스 추가 SQL 실행

**New Query** 클릭 후 다음 SQL 복사/붙여넣기:

```sql
-- 성능 최적화 인덱스 추가 (2026-02-14)

-- 모니터링 상품 인덱스
CREATE INDEX IF NOT EXISTS idx_monitored_products_source
ON monitored_products(source);

-- 주문 인덱스
CREATE INDEX IF NOT EXISTS idx_orders_created_at
ON orders(created_at DESC);

-- 판매 상품 인덱스
CREATE INDEX IF NOT EXISTS idx_my_selling_products_active_updated
ON my_selling_products(is_active, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_my_selling_products_sourcing_url
ON my_selling_products(sourcing_url);

CREATE INDEX IF NOT EXISTS idx_my_selling_products_playauto_no
ON my_selling_products(playauto_product_no);
```

**Run** 버튼 클릭 → ✅ Success 확인

### 3. 인덱스 생성 확인

다음 쿼리로 인덱스가 생성되었는지 확인:

```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY
    tablename, indexname;
```

**기대 결과:**
```
monitored_products | idx_monitored_products_active
monitored_products | idx_monitored_products_source
orders             | idx_orders_created_at
orders             | idx_orders_market
my_selling_products| idx_my_selling_products_active_updated
my_selling_products| idx_my_selling_products_sourcing_url
my_selling_products| idx_my_selling_products_playauto_no
...
```

### 4. 성능 개선 확인

마이그레이션 후 다음 쿼리들이 빨라집니다:

```sql
-- 활성 모니터링 상품 조회 (200ms → 40ms)
SELECT * FROM monitored_products
WHERE is_active = true
ORDER BY created_at DESC;

-- 최근 주문 조회 (300ms → 60ms)
SELECT * FROM orders
ORDER BY created_at DESC
LIMIT 50;

-- 소싱 URL로 판매 상품 조회 (150ms → 30ms)
SELECT * FROM my_selling_products
WHERE sourcing_url = 'https://...';
```

---

## 현재 시스템 구조

### 로컬 개발 환경
```
데이터베이스: SQLite (backend/monitoring.db)
이미지 저장: Supabase Storage
```

### 프로덕션 환경 (Railway)

**옵션 A: Railway PostgreSQL (기본)**
```
데이터베이스: Railway PostgreSQL
이미지 저장: Supabase Storage
마이그레이션: 자동 (schema_postgresql.sql)
```

**옵션 B: Supabase PostgreSQL**
```
데이터베이스: Supabase PostgreSQL
이미지 저장: Supabase Storage
마이그레이션: 수동 (SQL Editor)
```

---

## 추가 최적화 (Supabase 전용)

### Connection Pooler 사용 (이미 적용됨)

```python
# database_manager.py에서 자동 처리
if 'supabase.co' in database_url:
    database_url = database_url.replace(':5432', ':6543')
```

- 포트 5432 (Direct) → 6543 (Pooler)
- 연결 수 제한 우회
- 성능 향상

### Supabase 인덱스 모니터링

Dashboard → Database → Indexes에서:
- 인덱스 크기 확인
- 사용되지 않는 인덱스 삭제
- 쿼리 성능 분석

---

## 문제 해결

### 인덱스 생성 실패

```sql
ERROR: relation "monitored_products" does not exist
```

**해결**: 테이블이 아직 생성되지 않음
1. `schema_postgresql.sql` 전체 실행
2. 인덱스 SQL 재실행

### 권한 오류

```sql
ERROR: permission denied for table ...
```

**해결**: Service Role Key 사용
1. Supabase Dashboard → Settings → API
2. **Service Role** 키 복사
3. SQL Editor에서 해당 키로 연결

### Connection Pooler 오류

```
FATAL: remaining connection slots are reserved
```

**해결**: 이미 포트 6543으로 전환되어 있는지 확인
```python
print(database_url)  # :6543 확인
```

---

## 체크리스트

- [ ] Supabase DB 사용 여부 확인 (`DATABASE_URL` 확인)
- [ ] Supabase 사용 시: SQL Editor에서 인덱스 SQL 실행
- [ ] 인덱스 생성 확인 쿼리 실행
- [ ] Railway 사용 시: 자동 적용 확인 (로그 체크)

---

## 참고 파일

- `backend/database/schema_postgresql.sql` - 전체 스키마
- `backend/database/migrations/add_performance_indexes.sql` - 인덱스만
- `backend/database/database_manager.py` - DB 연결 로직
