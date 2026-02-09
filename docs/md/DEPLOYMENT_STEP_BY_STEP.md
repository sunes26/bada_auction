# 🚀 배포 실행 가이드 - 단계별 순서

> **지금 당장 무엇부터 해야 하는지** 명확한 순서를 제시합니다.

---

## 📋 시작하기 전 체크리스트

배포를 시작하기 전에 현재 시스템이 정상 작동하는지 확인하세요.

```bash
# 1. Backend 서버 실행 확인
cd backend
python main.py

# 2. Frontend 서버 실행 확인
npm run dev

# 3. 주요 기능 테스트
- [ ] 상품 모니터링 동작
- [ ] AI 상세페이지 생성
- [ ] 플레이오토 주문 동기화
- [ ] 데이터베이스 정상 작동
```

**모든 기능이 정상이면 다음 단계로 진행하세요.**

---

## 🎯 전체 타임라인 (5-7주)

```
Week 1-2: Phase 1 - 데이터베이스 마이그레이션
Week 3-4: Phase 2 - 백엔드 배포
Week 5: Phase 3 - 프론트엔드 배포
Week 6: Phase 4 - 통합 테스트
Week 7+: Phase 5 - 최적화 (지속)
```

---

## 📅 Week 0: 사전 준비 (1-2일)

### Step 0.1: 필수 계정 생성

다음 서비스에 가입하세요 (모두 무료 티어 가능):

#### 1. Supabase (데이터베이스 & 스토리지)
- 🔗 https://supabase.com/
- [ ] 계정 생성 (GitHub 로그인 추천)
- [ ] 이메일 인증
- [ ] 프로젝트 생성: "onbaek-ai-production"
- [ ] 데이터베이스 비밀번호 설정 (안전한 곳에 저장!)

**받아야 할 정보**:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

#### 2. Railway (백엔드 호스팅)
- 🔗 https://railway.app/
- [ ] 계정 생성 (GitHub 로그인 추천)
- [ ] GitHub 저장소 연동 권한 부여
- [ ] $5 무료 크레딧 확인

#### 3. Vercel (프론트엔드 호스팅)
- 🔗 https://vercel.com/
- [ ] 계정 생성 (GitHub 로그인 추천)
- [ ] GitHub 저장소 연동 권한 부여

#### 4. Sentry (에러 모니터링) - 선택
- 🔗 https://sentry.io/
- [ ] 계정 생성
- [ ] 프로젝트 생성: "onbaek-ai-backend"

#### 5. GitHub 저장소 확인
- [ ] 현재 프로젝트가 GitHub에 푸시되어 있는지 확인
- [ ] Private 저장소 권장 (환경 변수 보안)

---

### Step 0.2: 로컬 백업

**중요**: 배포 전 현재 데이터를 백업하세요!

```bash
# 1. 데이터베이스 백업
cd backend
cp monitoring.db monitoring.db.backup.$(date +%Y%m%d)

# 2. 이미지 폴더 백업
cd ..
zip -r supabase-images-backup-$(date +%Y%m%d).zip supabase-images/

# 3. .env.local 백업 (안전한 곳에 보관)
cp .env.local .env.local.backup
```

**백업 파일 위치 확인**:
```
backend/monitoring.db.backup.20260130
supabase-images-backup-20260130.zip
.env.local.backup
```

---

### Step 0.3: Git 브랜치 생성

배포 작업을 별도 브랜치에서 진행하세요:

```bash
# 현재 main 브랜치에서 작업 중이라고 가정
git checkout -b deployment-preparation

# 변경사항 커밋
git add .
git commit -m "Prepare for cloud deployment"
git push -u origin deployment-preparation
```

---

## 📅 Week 1-2: Phase 1 - 데이터베이스 마이그레이션

### Day 1-2: Supabase 설정

#### Step 1.1: Supabase Storage 버킷 생성

1. Supabase 대시보드 → Storage 메뉴
2. 새 버킷 생성:

```
버킷 이름: product-images
Public: ✅ (체크)
File size limit: 50MB
Allowed MIME types: image/*
```

3. 두 번째 버킷 생성:

```
버킷 이름: detail-pages
Public: ✅ (체크)
```

**확인**: Storage → product-images, detail-pages 버킷 생성됨

---

#### Step 1.2: PostgreSQL 스키마 생성

1. Supabase 대시보드 → SQL Editor
2. 새 쿼리 생성
3. 다음 스크립트 실행:

```sql
-- 기존 schema.sql의 PostgreSQL 버전
-- SQLite 전용 문법을 PostgreSQL로 변환 필요

-- 예시: monitored_products 테이블
CREATE TABLE IF NOT EXISTS monitored_products (
    id SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_url TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    current_price REAL,
    original_price REAL,
    current_status TEXT DEFAULT 'available',
    check_interval INTEGER DEFAULT 900,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    thumbnail_url TEXT
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_monitored_products_source ON monitored_products(source);
CREATE INDEX IF NOT EXISTS idx_monitored_products_status ON monitored_products(current_status);
CREATE INDEX IF NOT EXISTS idx_monitored_products_active ON monitored_products(is_active);

-- ... (나머지 테이블도 동일하게 변환)
```

**작업 필요**:
```bash
# PostgreSQL 스키마 변환 스크립트 생성
cd backend
python create_postgres_schema.py
```

**이 스크립트를 만들어야 합니다** (다음 단계에서 생성)

---

#### Step 1.3: SQLite → PostgreSQL 변환 스크립트 작성

**파일 생성**: `backend/create_postgres_schema.py`

```python
"""
SQLite schema.sql을 PostgreSQL로 변환
"""

def convert_sqlite_to_postgres():
    """SQLite DDL을 PostgreSQL DDL로 변환"""

    replacements = [
        # INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
        ('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY'),

        # DATETIME → TIMESTAMP
        ('DATETIME DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('DATETIME', 'TIMESTAMP'),

        # BOOLEAN 처리 (SQLite는 INTEGER로 저장)
        ('BOOLEAN DEFAULT 1', 'BOOLEAN DEFAULT TRUE'),
        ('BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),

        # REAL → DECIMAL 또는 NUMERIC (더 정확한 소수점)
        ('REAL', 'NUMERIC(10,2)'),
    ]

    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        sqlite_sql = f.read()

    postgres_sql = sqlite_sql
    for old, new in replacements:
        postgres_sql = postgres_sql.replace(old, new)

    # PostgreSQL 전용 문법 추가
    postgres_sql = postgres_sql.replace(
        'CREATE TABLE IF NOT EXISTS',
        'CREATE TABLE IF NOT EXISTS'
    )

    # 저장
    with open('database/schema_postgres.sql', 'w', encoding='utf-8') as f:
        f.write(postgres_sql)

    print("✅ PostgreSQL 스키마 생성 완료: database/schema_postgres.sql")
    print("👉 이 파일을 Supabase SQL Editor에서 실행하세요")

if __name__ == "__main__":
    convert_sqlite_to_postgres()
```

**실행**:
```bash
cd backend
python create_postgres_schema.py
```

**결과**:
- `backend/database/schema_postgres.sql` 파일 생성됨
- 이 파일을 복사하여 Supabase SQL Editor에 붙여넣고 실행

---

### Day 3-4: SQLAlchemy ORM 전환

#### Step 1.4: 필요한 패키지 설치

```bash
cd backend
pip install sqlalchemy psycopg2-binary alembic python-dotenv
pip freeze > requirements.txt
```

**requirements.txt에 추가되어야 할 항목**:
```
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.1
```

---

#### Step 1.5: SQLAlchemy 모델 생성

**파일 생성**: `backend/database/models.py`

```python
"""
SQLAlchemy ORM 모델 정의
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class MonitoredProduct(Base):
    """모니터링 상품"""
    __tablename__ = 'monitored_products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    product_url = Column(String, nullable=False, unique=True)
    source = Column(String, nullable=False)
    current_price = Column(Float)
    original_price = Column(Float)
    current_status = Column(String, default='available')
    check_interval = Column(Integer, default=900)
    last_checked = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    thumbnail_url = Column(String)

    # 관계
    price_history = relationship("PriceHistory", back_populates="product")


class PriceHistory(Base):
    """가격 변동 이력"""
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('monitored_products.id'), nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow)
    price_change = Column(Float)

    # 관계
    product = relationship("MonitoredProduct", back_populates="price_history")


class MySellingProduct(Base):
    """내 판매 상품"""
    __tablename__ = 'my_selling_products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    selling_price = Column(Float, nullable=False)
    monitored_product_id = Column(Integer, ForeignKey('monitored_products.id'))
    sourcing_url = Column(String)
    sourcing_product_name = Column(String)
    sourcing_price = Column(Float)
    sourcing_source = Column(String)
    detail_page_data = Column(Text)  # JSON
    category = Column(String)
    thumbnail_url = Column(String)
    original_thumbnail_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)

    # 관계
    monitored_product = relationship("MonitoredProduct")


# ... (나머지 테이블도 동일하게 작성)
```

---

#### Step 1.6: Database 연결 레이어 생성

**파일 생성**: `backend/database/connection.py`

```python
"""
데이터베이스 연결 관리
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

# 환경 변수에서 DATABASE_URL 가져오기
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./monitoring.db')

# PostgreSQL URL 수정 (Supabase는 postgresql:// 사용)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 확인
    pool_size=10,
    max_overflow=20,
    echo=False  # SQL 로그 (디버깅 시 True)
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """데이터베이스 세션 제공"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Session:
    """FastAPI dependency로 사용"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

#### Step 1.7: 기존 Database 클래스 마이그레이션

**파일 수정**: `backend/database/db.py`

기존 SQLite 코드를 유지하면서 SQLAlchemy로 전환:

```python
"""
데이터베이스 레이어 - SQLAlchemy 버전
"""
import os
from typing import List, Dict, Optional
from .connection import get_db_session
from .models import MonitoredProduct, PriceHistory, MySellingProduct
from sqlalchemy import func

class Database:
    """데이터베이스 접근 클래스"""

    def __init__(self):
        # SQLite 모드 또는 PostgreSQL 모드 자동 선택
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./monitoring.db')
        self.use_orm = not self.database_url.startswith('sqlite://')

    # 모니터링 상품 관련
    def add_monitored_product(self, product_name: str, product_url: str, source: str, **kwargs) -> int:
        """모니터링 상품 추가"""
        if self.use_orm:
            with get_db_session() as session:
                product = MonitoredProduct(
                    product_name=product_name,
                    product_url=product_url,
                    source=source,
                    **kwargs
                )
                session.add(product)
                session.flush()
                return product.id
        else:
            # 기존 SQLite 코드 유지
            pass

    def get_monitored_products(self, is_active: Optional[bool] = None) -> List[Dict]:
        """모니터링 상품 목록 조회"""
        if self.use_orm:
            with get_db_session() as session:
                query = session.query(MonitoredProduct)
                if is_active is not None:
                    query = query.filter(MonitoredProduct.is_active == is_active)
                products = query.all()
                return [self._model_to_dict(p) for p in products]
        else:
            # 기존 SQLite 코드 유지
            pass

    def _model_to_dict(self, model) -> Dict:
        """SQLAlchemy 모델을 딕셔너리로 변환"""
        return {c.name: getattr(model, c.name) for c in model.__table__.columns}

    # ... (나머지 메서드도 동일하게 작성)
```

**전략**:
- 로컬에서는 SQLite 사용 (`DATABASE_URL` 없음)
- 배포 환경에서는 PostgreSQL 사용 (`DATABASE_URL` 있음)

---

### Day 5-7: 이미지 마이그레이션

#### Step 1.8: Supabase Storage 업로드 스크립트

**파일 생성**: `backend/migrate_images_to_supabase.py`

```python
"""
로컬 이미지를 Supabase Storage로 마이그레이션
"""
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv('.env.local')

# Supabase 클라이언트 초기화
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Service Role Key 사용 (권한 필요)
)

def upload_directory(local_dir: Path, bucket_name: str = 'product-images'):
    """디렉토리의 모든 이미지를 업로드"""

    if not local_dir.exists():
        print(f"❌ 디렉토리를 찾을 수 없습니다: {local_dir}")
        return

    # 모든 이미지 파일 찾기
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(local_dir.rglob(f'*{ext}'))

    print(f"📂 총 {len(image_files)}개 이미지 발견")

    uploaded = 0
    failed = 0

    for image_path in tqdm(image_files, desc="업로드 중"):
        try:
            # 상대 경로 계산 (버킷 내 경로)
            relative_path = str(image_path.relative_to(local_dir))

            # 파일 읽기
            with open(image_path, 'rb') as f:
                file_data = f.read()

            # Supabase Storage에 업로드
            result = supabase.storage.from_(bucket_name).upload(
                path=relative_path,
                file=file_data,
                file_options={
                    "content-type": f"image/{image_path.suffix[1:]}",
                    "upsert": "true"  # 이미 있으면 덮어쓰기
                }
            )

            uploaded += 1

        except Exception as e:
            print(f"❌ 실패: {image_path.name} - {e}")
            failed += 1

    print(f"\n✅ 업로드 완료: {uploaded}개")
    print(f"❌ 실패: {failed}개")

    # 업로드된 URL 예시 출력
    if uploaded > 0:
        example_url = supabase.storage.from_(bucket_name).get_public_url(relative_path)
        print(f"\n📝 이미지 URL 형식: {example_url}")


if __name__ == "__main__":
    print("🚀 Supabase Storage 이미지 마이그레이션 시작\n")

    # supabase-images 폴더 업로드
    images_dir = Path(__file__).parent.parent / 'supabase-images'
    upload_directory(images_dir, 'product-images')

    print("\n✅ 마이그레이션 완료!")
    print("👉 이제 로컬 이미지 URL을 Supabase URL로 변경하세요")
```

**실행**:
```bash
cd backend

# 필요한 패키지 설치
pip install supabase tqdm

# 마이그레이션 실행
python migrate_images_to_supabase.py
```

**예상 시간**: 이미지 개수에 따라 5-30분

---

#### Step 1.9: 이미지 URL 업데이트

이미지가 업로드되면 DB의 URL을 Supabase URL로 변경해야 합니다.

**파일 생성**: `backend/update_image_urls.py`

```python
"""
DB의 로컬 이미지 URL을 Supabase URL로 변경
"""
import os
from database.db import get_db
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('SUPABASE_URL')
BUCKET_NAME = 'product-images'

def update_urls():
    """모든 이미지 URL 업데이트"""
    db = get_db()

    # 1. monitored_products의 thumbnail_url 업데이트
    products = db.get_monitored_products()
    updated_count = 0

    for product in products:
        old_url = product.get('thumbnail_url')
        if old_url and old_url.startswith('/supabase-images/'):
            # /supabase-images/1_흰밥/image.jpg → 1_흰밥/image.jpg
            relative_path = old_url.replace('/supabase-images/', '')

            # Supabase URL로 변경
            new_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{relative_path}"

            db.update_monitored_product(
                product_id=product['id'],
                thumbnail_url=new_url
            )
            updated_count += 1
            print(f"✅ Updated: {product['product_name']}")

    print(f"\n✅ 총 {updated_count}개 URL 업데이트 완료")

if __name__ == "__main__":
    update_urls()
```

---

### Day 8-10: 로컬 테스트

#### Step 1.10: 로컬에서 PostgreSQL 테스트

로컬에서 Docker로 PostgreSQL을 실행하여 테스트:

```bash
# Docker PostgreSQL 실행
docker run -d \
  --name postgres-test \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=onbaek_test \
  -p 5432:5432 \
  postgres:15

# .env.local에 테스트 DATABASE_URL 추가
echo "DATABASE_URL=postgresql://postgres:testpass@localhost:5432/onbaek_test" >> .env.local

# 서버 실행
cd backend
python main.py
```

**테스트 항목**:
- [ ] 서버가 정상 실행되는가?
- [ ] API 엔드포인트가 정상 작동하는가?
- [ ] 데이터 CRUD가 정상 작동하는가?
- [ ] 이미지가 Supabase에서 로딩되는가?

**문제 발생 시**:
- 로그 확인
- SQLAlchemy echo=True로 SQL 쿼리 확인
- 스키마 비교 (SQLite vs PostgreSQL)

---

### ✅ Phase 1 완료 체크리스트

다음 항목이 모두 체크되면 Phase 2로 진행:

- [ ] Supabase 프로젝트 생성 완료
- [ ] PostgreSQL 스키마 생성 완료
- [ ] SQLAlchemy 모델 작성 완료
- [ ] Database 클래스 마이그레이션 완료
- [ ] 이미지 Supabase Storage 업로드 완료
- [ ] 이미지 URL 업데이트 완료
- [ ] 로컬에서 PostgreSQL 테스트 성공
- [ ] 모든 API 엔드포인트 정상 작동
- [ ] Git 커밋 및 푸시 완료

```bash
git add .
git commit -m "Phase 1 complete: Database migration to PostgreSQL"
git push
```

---

## 📅 Week 3-4: Phase 2 - 백엔드 배포

### Day 11-12: Railway 설정

#### Step 2.1: Railway 프로젝트 생성

1. Railway 대시보드 접속: https://railway.app/dashboard
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. 저장소 선택: `your-username/onbaek-ai`
5. 프로젝트 이름: "onbaek-ai-backend"

---

#### Step 2.2: 환경 변수 설정

Railway Dashboard → Variables 탭:

```env
# Database
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Railway PostgreSQL 또는 Supabase

# Supabase (Supabase 사용 시)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI
OPENAI_API_KEY=sk-...

# Playauto
PLAYAUTO_EMAIL=your@email.com
PLAYAUTO_PASSWORD=your_password

# Slack (선택)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Discord (선택)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Environment
ENVIRONMENT=production
PORT=8000

# Sentry (선택)
SENTRY_DSN=https://...@sentry.io/...
```

---

#### Step 2.3: 프로덕션 설정 파일 생성

**파일 생성**: `backend/gunicorn_conf.py`

```python
"""
Gunicorn 프로덕션 설정
"""
import os
import multiprocessing

# 서버 소켓
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Worker 프로세스
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# 타임아웃
timeout = 120
graceful_timeout = 30
keepalive = 5

# 로깅
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 프로세스 이름
proc_name = "onbaek-ai-backend"

# 재시작 정책
preload_app = True
reload = False
```

---

**파일 생성**: `backend/Procfile` (Railway용)

```
web: gunicorn -c gunicorn_conf.py main:app
```

---

**파일 생성**: `railway.json`

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
    "healthcheckTimeout": 100
  }
}
```

---

#### Step 2.4: Requirements 업데이트

```bash
cd backend

# Gunicorn 추가
pip install gunicorn

# 전체 패키지 목록 갱신
pip freeze > requirements.txt
```

**requirements.txt 확인**:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
gunicorn>=21.2.0
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
supabase>=2.0.0
```

---

#### Step 2.5: Health Check 강화

**파일 수정**: `backend/main.py`

```python
@app.get("/health")
async def health_check():
    """프로덕션용 헬스 체크"""
    health_status = {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

    # DB 연결 확인
    try:
        db = get_db()
        # 간단한 쿼리 실행
        products = db.get_monitored_products(limit=1)
        health_status["database"] = "ok"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Supabase Storage 확인 (선택)
    try:
        if os.getenv('SUPABASE_URL'):
            from supabase import create_client
            supabase = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_ANON_KEY')
            )
            # 버킷 존재 확인
            buckets = supabase.storage.list_buckets()
            health_status["storage"] = "ok"
    except Exception as e:
        health_status["storage"] = f"error: {str(e)}"

    return health_status
```

---

#### Step 2.6: Git 푸시 및 자동 배포

```bash
git add .
git commit -m "Add Railway production configuration"
git push
```

Railway가 자동으로 감지하고 배포 시작.

**Railway 대시보드에서 확인**:
- Build Logs 확인
- Deploy Logs 확인
- 배포 완료 후 URL 확인: `https://your-app.railway.app`

**테스트**:
```bash
# Health check
curl https://your-app.railway.app/health

# API 테스트
curl https://your-app.railway.app/api/products
```

---

### Day 13-14: 스케줄러 분리

#### Step 2.7: Cron 엔드포인트 생성

**파일 생성**: `backend/api/cron.py`

```python
"""
Cron 작업용 엔드포인트
"""
from fastapi import APIRouter, Header, HTTPException
import os

router = APIRouter(prefix="/cron", tags=["Cron"])

# Cron 시크릿 (Railway Variables에 설정)
CRON_SECRET = os.getenv("CRON_SECRET", "change-this-secret")


def verify_cron_secret(authorization: str = Header(None)):
    """Cron 요청 인증"""
    if not authorization or authorization != f"Bearer {CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/monitor-products")
async def cron_monitor_products(auth: None = Depends(verify_cron_secret)):
    """상품 모니터링 실행 (10분마다)"""
    try:
        from monitor.product_monitor import check_all_products
        await check_all_products()
        return {"status": "success", "message": "Monitoring completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync-playauto-orders")
async def cron_sync_orders(auth: None = Depends(verify_cron_secret)):
    """플레이오토 주문 동기화 (1시간마다)"""
    try:
        from playauto.scheduler import sync_orders
        await sync_orders()
        return {"status": "success", "message": "Orders synced"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/backup-database")
async def cron_backup(auth: None = Depends(verify_cron_secret)):
    """데이터베이스 백업 (매일 새벽 2시)"""
    try:
        from backup.scheduler import create_backup
        await create_backup()
        return {"status": "success", "message": "Backup completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

**main.py에 라우터 등록**:
```python
from api.cron import router as cron_router
app.include_router(cron_router)
```

---

#### Step 2.8: Railway Cron 설정

**railway.json에 추가**:
```json
{
  "deploy": {
    "cron": [
      {
        "schedule": "*/10 * * * *",
        "command": "curl -X POST https://your-app.railway.app/cron/monitor-products -H 'Authorization: Bearer ${CRON_SECRET}'"
      },
      {
        "schedule": "0 * * * *",
        "command": "curl -X POST https://your-app.railway.app/cron/sync-playauto-orders -H 'Authorization: Bearer ${CRON_SECRET}'"
      },
      {
        "schedule": "0 2 * * *",
        "command": "curl -X POST https://your-app.railway.app/cron/backup-database -H 'Authorization: Bearer ${CRON_SECRET}'"
      }
    ]
  }
}
```

**환경 변수 추가** (Railway Dashboard):
```
CRON_SECRET=your-random-secret-key-here
```

---

### ✅ Phase 2 완료 체크리스트

- [ ] Railway 프로젝트 생성
- [ ] 환경 변수 설정 완료
- [ ] Gunicorn 설정 완료
- [ ] 자동 배포 성공
- [ ] Health check API 정상
- [ ] 모든 API 엔드포인트 동작
- [ ] Cron 엔드포인트 생성
- [ ] Railway Cron 설정 완료
- [ ] 스케줄러 정상 동작 확인

**백엔드 URL 기록**:
```
https://your-app.railway.app
```

---

## 📅 Week 5: Phase 3 - 프론트엔드 배포

### Day 15-16: Vercel 배포

#### Step 3.1: 환경 변수 설정

**파일 생성**: `.env.production`

```env
NEXT_PUBLIC_API_URL=https://your-app.railway.app
```

---

#### Step 3.2: Next.js 설정 수정

**파일 수정**: `next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: [
      'xxxxx.supabase.co',  // Supabase Storage
      'localhost',
    ],
    formats: ['image/avif', 'image/webp'],
  },
  // 환경 변수 노출
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
}

module.exports = nextConfig
```

---

#### Step 3.3: API URL 수정

프론트엔드 코드에서 API URL을 환경 변수로 변경:

**전역 검색 및 수정**:
```typescript
// 기존
const API_BASE_URL = 'http://localhost:8000';

// 변경
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**파일 수정 필요**:
- `components/pages/ProductSourcingPage.tsx`
- `components/pages/DetailPage.tsx`
- `components/pages/UnifiedOrderManagementPage.tsx`
- 기타 API 호출하는 모든 파일

---

#### Step 3.4: Vercel 프로젝트 생성

1. Vercel 대시보드: https://vercel.com/dashboard
2. "Add New" → "Project"
3. GitHub 저장소 선택: `your-username/onbaek-ai`
4. Framework Preset: **Next.js** (자동 감지)
5. Root Directory: `.` (프로젝트 루트)
6. Build Command: `npm run build`
7. Output Directory: `.next`

---

#### Step 3.5: 환경 변수 설정

Vercel Dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://your-app.railway.app
```

**모든 환경에 적용**: Production, Preview, Development

---

#### Step 3.6: 배포

1. "Deploy" 버튼 클릭
2. 자동 빌드 시작
3. 배포 완료 후 URL 확인: `https://your-domain.vercel.app`

**테스트**:
- 프론트엔드 접속
- 상품 목록 로딩 확인
- API 연결 확인
- 이미지 로딩 확인

---

#### Step 3.7: 커스텀 도메인 (선택)

1. Vercel Dashboard → Settings → Domains
2. 도메인 입력: `yourdomain.com`
3. DNS 레코드 추가 (도메인 제공업체에서):
   ```
   A    @    76.76.21.21
   CNAME www  cname.vercel-dns.com
   ```
4. 자동 HTTPS 설정 (Let's Encrypt)

---

### Day 17: CORS 업데이트

#### Step 3.8: 백엔드 CORS 설정

**파일 수정**: `backend/main.py`

```python
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 로컬 개발
        "https://your-domain.vercel.app",  # Vercel 배포
        "https://yourdomain.com",  # 커스텀 도메인 (있는 경우)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
```

**Git 푸시**:
```bash
git add .
git commit -m "Update CORS for production"
git push
```

Railway가 자동으로 재배포.

---

### ✅ Phase 3 완료 체크리스트

- [ ] Next.js 환경 변수 설정
- [ ] API URL 모두 수정
- [ ] Vercel 프로젝트 생성
- [ ] 자동 배포 성공
- [ ] 프론트엔드 정상 접속
- [ ] API 연결 확인
- [ ] 이미지 로딩 확인
- [ ] CORS 설정 완료
- [ ] (선택) 커스텀 도메인 연결

**프론트엔드 URL 기록**:
```
https://your-domain.vercel.app
```

---

## 📅 Week 6: Phase 4 - 통합 테스트 & 보안

### Day 18-19: E2E 테스트

#### Step 4.1: 전체 기능 테스트

다음 기능들을 실제로 테스트:

**체크리스트**:
- [ ] 상품 모니터링 등록
- [ ] 가격 변동 확인
- [ ] AI 상세페이지 생성
- [ ] 플레이오토 주문 동기화
- [ ] 송장 업로드
- [ ] Slack/Discord 알림
- [ ] Excel 내보내기
- [ ] 모든 페이지 접근

**버그 발견 시**:
- 로그 확인 (Railway Dashboard → Logs)
- Sentry에서 에러 확인
- 수정 후 재배포

---

### Day 20-21: 모니터링 설정

#### Step 4.2: Sentry 설정

**백엔드 Sentry**:

```bash
cd backend
pip install sentry-sdk
```

**main.py에 추가**:
```python
import sentry_sdk

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "production"),
    )
```

**프론트엔드 Sentry**:

```bash
npm install @sentry/nextjs
npx @sentry/wizard -i nextjs
```

---

#### Step 4.3: Uptime 모니터링

1. UptimeRobot 가입: https://uptimerobot.com/
2. 새 모니터 생성:
   - Monitor Type: HTTP(s)
   - URL: `https://your-app.railway.app/health`
   - Monitoring Interval: 5 minutes
3. Alert Contacts 설정 (이메일, Slack)

---

### Day 22: 보안 강화

#### Step 4.4: Rate Limiting

```bash
cd backend
pip install slowapi
```

**main.py에 추가**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# API에 적용
@router.post("/generate-content")
@limiter.limit("10/minute")  # 1분에 10회만
async def generate_content(request: Request):
    ...
```

---

### ✅ Phase 4 완료 체크리스트

- [ ] 전체 기능 E2E 테스트 완료
- [ ] Sentry 설정 완료
- [ ] Uptime 모니터링 설정
- [ ] Rate Limiting 적용
- [ ] 보안 취약점 확인
- [ ] 성능 테스트 완료

---

## 📅 Week 7+: Phase 5 - 최적화 (지속)

### 지속적 개선 작업

#### Step 5.1: Redis 캐싱 (선택)

트래픽이 증가하면 Redis 캐싱 추가:

1. Railway에서 Redis 추가
2. 캐싱 레이어 구현
3. 자주 조회되는 데이터 캐싱

---

#### Step 5.2: CI/CD 파이프라인

**파일 생성**: `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        run: echo "Railway auto-deploys on push"
      - name: Deploy to Vercel
        run: echo "Vercel auto-deploys on push"
```

---

### ✅ Phase 5 완료

Phase 5는 지속적인 개선이므로, 다음 항목들을 점진적으로 진행:

- [ ] Redis 캐싱 구현
- [ ] DB 쿼리 최적화
- [ ] 프론트엔드 코드 스플리팅
- [ ] 이미지 최적화 (WebP)
- [ ] CI/CD 파이프라인 구축
- [ ] 백업 자동화
- [ ] 로그 분석

---

## 🎉 배포 완료!

모든 Phase가 완료되면:

✅ 24/7 접근 가능
✅ 자동 백업 & 복구
✅ 99.9% 가동률
✅ 팀 협업 가능
✅ 비즈니스 확장 준비 완료

**다음 단계**:
1. 실제 사용자 피드백 수집
2. 성능 모니터링
3. 기능 개선
4. 비즈니스 성장

---

## 📞 도움이 필요하면

- DEPLOYMENT_ROADMAP.md - 상세 기술 문서
- DEPLOYMENT_BENEFITS.md - 배포 이점
- 각 Phase별로 문제 발생 시 질문하세요!
