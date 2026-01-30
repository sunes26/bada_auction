# Supabase 데이터베이스 설정 가이드

## 1단계: PostgreSQL 스키마 적용

### 방법 1: Supabase Dashboard (권장)

1. **Supabase 대시보드 접속**
   ```
   https://app.supabase.com/project/spkeunlwkrqkdwunkufy
   ```

2. **SQL Editor 열기**
   - 왼쪽 메뉴에서 "SQL Editor" 클릭

3. **스키마 파일 복사 & 실행**
   - `backend/database/schema_postgresql.sql` 파일 전체 내용 복사
   - SQL Editor에 붙여넣기
   - **RUN** 버튼 클릭

4. **결과 확인**
   - 성공 메시지 확인: "Success. No rows returned"
   - Table Editor에서 테이블 생성 확인

### 방법 2: 로컬에서 psql 사용

```bash
# PostgreSQL 클라이언트 설치 (Windows)
# https://www.postgresql.org/download/windows/

# 스키마 적용
psql "postgresql://postgres:[YOUR-PASSWORD]@db.spkeunlwkrqkdwunkufy.supabase.co:5432/postgres" -f backend/database/schema_postgresql.sql
```

---

## 2단계: Python 패키지 설치

```bash
cd backend
pip install psycopg2-binary sqlalchemy python-dotenv
```

또는 `requirements.txt`에 추가:

```txt
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
python-dotenv==1.0.0
```

---

## 3단계: 환경 변수 설정

`.env.local` 파일이 이미 설정되어 있는지 확인:

```env
# Supabase PostgreSQL Connection
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.spkeunlwkrqkdwunkufy.supabase.co:5432/postgres

# Supabase API Keys
SUPABASE_URL=https://spkeunlwkrqkdwunkufy.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**주의**: `[YOUR-PASSWORD]`를 실제 Supabase 데이터베이스 비밀번호로 변경하세요.
- Supabase Dashboard → Settings → Database → Connection string에서 확인 가능

---

## 4단계: 데이터 마이그레이션 (SQLite → PostgreSQL)

### 사전 준비

1. **현재 SQLite 데이터 백업**
   ```bash
   cp monitoring.db monitoring.db.backup
   ```

2. **환경 변수 확인**
   ```bash
   echo $DATABASE_URL  # PostgreSQL URL이 설정되어 있는지 확인
   ```

### 마이그레이션 실행

```bash
cd backend

# 1. Dry run (연결 테스트만)
python migrate_to_postgresql.py --dry-run

# 2. 실제 마이그레이션 실행
python migrate_to_postgresql.py --sqlite monitoring.db
```

### 마이그레이션 로그 예시

```
============================================================
Starting Full Migration: SQLite → PostgreSQL
============================================================

✓ monitored_products: 15 records migrated
✓ price_history: 342 records migrated
✓ status_changes: 28 records migrated
✓ notifications: 67 records migrated
✓ orders: 23 records migrated
✓ order_items: 45 records migrated
...

============================================================
Migration completed in 12.34 seconds
Total records migrated: 620
============================================================
```

---

## 5단계: 데이터 확인

### Supabase Dashboard에서 확인

1. **Table Editor** 열기
2. 각 테이블 선택하여 데이터 확인:
   - `monitored_products`
   - `orders`
   - `my_selling_products`
   - 등등...

### Python 스크립트로 확인

```python
# backend/test_postgresql.py
from database.database_manager import get_database_manager
from database.models import MonitoredProduct

db_manager = get_database_manager()

# 연결 테스트
if db_manager.test_connection():
    print("✓ PostgreSQL 연결 성공!")

# 데이터 조회 테스트
with db_manager.get_session() as session:
    products = session.query(MonitoredProduct).limit(5).all()
    print(f"상품 {len(products)}개 조회됨")
    for p in products:
        print(f"  - {p.product_name} ({p.source})")
```

실행:
```bash
python test_postgresql.py
```

---

## 6단계: 백엔드 코드 업데이트

### 기존 코드 (SQLite)

```python
from database.db import get_db

db = get_db()
products = db.get_all_monitored_products()
```

### 새 코드 (PostgreSQL with SQLAlchemy)

```python
from database.database_manager import get_database_manager
from database.models import MonitoredProduct

db_manager = get_database_manager()

with db_manager.get_session() as session:
    products = session.query(MonitoredProduct).filter_by(is_active=True).all()
```

### FastAPI 엔드포인트 예시

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from database.database_manager import get_db
from database.models import MonitoredProduct

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(MonitoredProduct).filter_by(is_active=True).all()
    return products
```

---

## 트러블슈팅

### 1. `psycopg2` 설치 실패

**에러**: `pg_config executable not found`

**해결**:
```bash
# Windows
pip install psycopg2-binary  # binary 버전 사용

# Linux/Mac
sudo apt-get install libpq-dev  # Ubuntu/Debian
brew install postgresql  # Mac
```

### 2. 연결 타임아웃

**에러**: `Connection timed out`

**해결**:
- Supabase 대시보드에서 Database Pause 상태 확인
- 방화벽 설정 확인
- Connection pooler 사용 (`:6543` 포트)

```python
# Pooler 사용 (권장)
DATABASE_URL=postgresql://postgres:password@db.spkeunlwkrqkdwunkufy.supabase.co:6543/postgres
```

### 3. SSL 에러

**에러**: `SSL connection has been closed unexpectedly`

**해결**:
```python
# URL에 SSL 파라미터 추가
DATABASE_URL=postgresql://...?sslmode=require
```

### 4. 마이그레이션 중 외래키 에러

**에러**: `violates foreign key constraint`

**해결**:
- 마이그레이션 스크립트는 올바른 순서로 실행됨
- 만약 에러 발생 시, 테이블 삭제 후 재실행:

```python
# backend/reset_database.py
from database.database_manager import get_database_manager

db_manager = get_database_manager()
db_manager.drop_all_tables()  # 주의: 모든 데이터 삭제!
db_manager.create_all_tables()
```

---

## 성공 체크리스트

- [ ] Supabase 스키마 적용 완료 (23개 테이블 생성)
- [ ] `psycopg2-binary`, `sqlalchemy` 설치 완료
- [ ] `.env.local`에 `DATABASE_URL` 설정 완료
- [ ] 마이그레이션 스크립트 dry-run 성공
- [ ] 데이터 마이그레이션 완료
- [ ] Supabase Dashboard에서 데이터 확인 완료
- [ ] Python으로 PostgreSQL 연결 테스트 성공

---

## 다음 단계

마이그레이션이 완료되면:

1. **이미지 마이그레이션** (로컬 → Supabase Storage)
   - `DEPLOYMENT_STEP_BY_STEP.md` Week 1 참고

2. **백엔드 코드 업데이트**
   - SQLite 전용 코드 → SQLAlchemy ORM으로 변경

3. **Railway 배포 준비**
   - `railway.json` 설정
   - 환경 변수 설정

4. **프론트엔드 API URL 업데이트**
   - localhost:8000 → Railway URL

---

## 참고 자료

- [Supabase Database 문서](https://supabase.com/docs/guides/database)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [PostgreSQL vs SQLite 차이점](https://www.sqlite.org/whentouse.html)
