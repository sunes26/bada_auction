from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from api.sourcing import router as sourcing_router
from api.monitoring import router as monitoring_router
from api.orders import router as orders_router
from api.playauto import router as playauto_router
from api.playauto_categories import router as playauto_categories_router
from api.tracking_scheduler import router as tracking_scheduler_router
from api.notifications import router as notifications_router
from api.scheduler import router as scheduler_router
from api.products import router as products_router
from api.categories import router as categories_router
from api.accounting import router as accounting_router
from api.category_mappings import router as category_mappings_router
from api.category_playauto_mappings import router as category_playauto_mappings_router
from api.dashboard import router as dashboard_router
from api.websocket import router as websocket_router
from api.auto_pricing import router as auto_pricing_router

# Admin router import with error handling
try:
    from api.admin import router as admin_router
    print(f"[OK] Admin router imported: {len(admin_router.routes)} routes")
except Exception as e:
    print(f"[ERROR] Failed to import admin router: {e}")
    import traceback
    traceback.print_exc()
    admin_router = None
from database.db_wrapper import get_db
from playauto.scheduler import start_scheduler as start_playauto_scheduler, stop_scheduler as stop_playauto_scheduler
from monitor.scheduler import start_scheduler as start_monitor_scheduler, stop_scheduler as stop_monitor_scheduler
from backup.scheduler import start_scheduler as start_backup_scheduler, stop_scheduler as stop_backup_scheduler
from services.tracking_scheduler import start_tracking_scheduler, stop_tracking_scheduler
import sys
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from logger import get_logger

# 로거 초기화
logger = get_logger(__name__)

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    import codecs
    try:
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, TypeError):
        # 이미 wrapping되었거나 encoding 속성이 없는 경우 무시
        pass

# .env.local 파일 로드 (프로젝트 루트에서)
env_path = Path(__file__).parent.parent / '.env.local'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"환경 변수 로드 완료: {env_path}")
else:
    logger.warning(f".env.local 파일을 찾을 수 없습니다: {env_path}")

# 필수 환경 변수 검증
# 프로덕션과 개발 환경에서 필요한 변수 구분
REQUIRED_ENV_VARS_DEV = []  # 개발 환경 필수 변수 (선택적)
REQUIRED_ENV_VARS_PROD = [
    'DATABASE_URL',  # PostgreSQL 연결 (프로덕션 필수)
    'SUPABASE_URL',  # Supabase Storage (이미지 저장)
    'SUPABASE_SERVICE_ROLE_KEY',  # Supabase 인증
]

# OPENAI_API_KEY는 AI 기능 사용시에만 필요 (경고만)
OPTIONAL_ENV_VARS = ['OPENAI_API_KEY', 'PLAYAUTO_API_KEY', 'PLAYAUTO_SOLUTION_KEY']

# 환경에 따라 검증
is_production = os.getenv('ENVIRONMENT') == 'production'
required_vars = REQUIRED_ENV_VARS_PROD if is_production else REQUIRED_ENV_VARS_DEV

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"필수 환경 변수 누락: {', '.join(missing_vars)}")
    if is_production:
        logger.error("프로덕션 환경에서 필수 변수 누락으로 시작 불가")
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
    else:
        logger.warning("개발 환경에서 일부 변수 누락 (계속 진행)")

# 선택적 변수 경고
missing_optional = [var for var in OPTIONAL_ENV_VARS if not os.getenv(var)]
if missing_optional:
    logger.warning(f"선택적 환경 변수 누락 (일부 기능 제한): {', '.join(missing_optional)}")

if not missing_vars:
    logger.info(f"환경 변수 검증 완료 ({'production' if is_production else 'development'} 모드)")

# Windows 환경에서 Playwright 실행을 위한 설정
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 데이터베이스 초기화
get_db()

# Lifespan 이벤트 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 및 종료 시 실행되는 이벤트 핸들러"""
    # Startup
    print("[INFO] 서버 시작 중...")

    # 데이터베이스 자동 마이그레이션 (프로덕션 환경)
    try:
        from database.database_manager import get_database_manager
        db_manager = get_database_manager()

        # PostgreSQL인 경우에만 마이그레이션 실행
        if db_manager.is_postgresql:
            print("[INFO] PostgreSQL 데이터베이스 마이그레이션 확인 중...")
            from database.migrate_playauto_fields import get_columns_to_add

            conn = db_manager.engine.raw_connection()
            cursor = conn.cursor()

            # 1. category_playauto_mapping 테이블 생성
            try:
                cursor.execute("""
                    SELECT to_regclass('public.category_playauto_mapping')
                """)
                table_exists = cursor.fetchone()[0] is not None

                if not table_exists:
                    print("[MIGRATION] category_playauto_mapping 테이블 생성 중...")
                    cursor.execute("""
                        CREATE TABLE category_playauto_mapping (
                            id SERIAL PRIMARY KEY,
                            our_category TEXT NOT NULL UNIQUE,
                            sol_cate_no INTEGER NOT NULL,
                            playauto_category TEXT,
                            similarity TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute("""
                        CREATE INDEX idx_category_playauto_mapping_our_category
                        ON category_playauto_mapping(our_category)
                    """)
                    conn.commit()
                    print("[OK] category_playauto_mapping 테이블 생성 완료")
            except Exception as e:
                print(f"[WARN] category_playauto_mapping 테이블 생성 중 오류: {e}")
                conn.rollback()

            # 2. my_selling_products 컬럼 추가
            columns_to_add = get_columns_to_add(cursor, 'my_selling_products', 'postgresql')

            if columns_to_add:
                print(f"[MIGRATION] {len(columns_to_add)}개 컬럼 추가 중...")
                for col_name, col_type in columns_to_add:
                    print(f"   추가: {col_name} ({col_type})")
                    cursor.execute(f"ALTER TABLE my_selling_products ADD COLUMN {col_name} {col_type}")

                conn.commit()
                print("[OK] 데이터베이스 마이그레이션 완료")
            else:
                print("[OK] 데이터베이스가 최신 상태입니다")

            # 3. categories 테이블에 sol_cate_no 컬럼 추가
            try:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'categories' AND column_name = 'sol_cate_no'
                """)
                column_exists = cursor.fetchone() is not None

                if not column_exists:
                    print("[MIGRATION] categories 테이블에 sol_cate_no 컬럼 추가 중...")
                    cursor.execute("ALTER TABLE categories ADD COLUMN sol_cate_no INTEGER")
                    conn.commit()
                    print("[OK] sol_cate_no 컬럼 추가 완료")
            except Exception as e:
                print(f"[WARN] sol_cate_no 컬럼 추가 중 오류: {e}")
                conn.rollback()

            # 4. category_infocode_mapping 테이블 생성
            try:
                cursor.execute("""
                    SELECT to_regclass('public.category_infocode_mapping')
                """)
                table_exists = cursor.fetchone()[0] is not None

                if not table_exists:
                    print("[MIGRATION] category_infocode_mapping 테이블 생성 중...")
                    cursor.execute("""
                        CREATE TABLE category_infocode_mapping (
                            id SERIAL PRIMARY KEY,
                            level1 TEXT NOT NULL UNIQUE,
                            info_code TEXT NOT NULL,
                            info_code_name TEXT,
                            notes TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute("""
                        CREATE INDEX idx_category_infocode_level1
                        ON category_infocode_mapping(level1)
                    """)
                    cursor.execute("""
                        CREATE INDEX idx_category_infocode_info_code
                        ON category_infocode_mapping(info_code)
                    """)

                    # 기본 데이터 삽입
                    cursor.execute("""
                        INSERT INTO category_infocode_mapping (level1, info_code, info_code_name, notes)
                        VALUES
                            ('간편식', 'ProcessedFood2023', '가공식품', '즉석밥, 죽, 국/탕/찌개 등'),
                            ('음료', 'ProcessedFood2023', '가공식품', '주스, 탄산음료, 식혜 등'),
                            ('우유/두유', 'ProcessedFood2023', '가공식품', '우유, 두유, 요구르트 등'),
                            ('스낵류', 'ProcessedFood2023', '가공식품', '과자, 초콜릿, 사탕 등'),
                            ('신선/냉장품', 'ProcessedFood2023', '가공식품', '냉장/냉동 가공식품'),
                            ('쿠킹소스/장류', 'ProcessedFood2023', '가공식품', '소스, 장류, 양념 등'),
                            ('커피/차류', 'ProcessedFood2023', '가공식품', '커피, 차, 분말음료 등'),
                            ('과일류', 'ProcessedFood2023', '가공식품', '과일 가공품'),
                            ('통조림/캔류', 'ProcessedFood2023', '가공식품', '통조림, 캔 식품'),
                            ('건강기능식품', 'HealthFunctionalFood2023', '건강기능식품', '영양제, 보충제 등'),
                            ('뷰티', 'Cosmetic2023', '화장품', '스킨케어, 메이크업 등'),
                            ('화장품,생활용품', 'Cosmetic2023', '화장품', '화장품 및 일부 생활용품'),
                            ('생활용품', 'HouseHoldChemical2023', '생활화학제품', '세제, 방향제 등')
                    """)

                    conn.commit()
                    print("[OK] category_infocode_mapping 테이블 생성 및 데이터 삽입 완료")
            except Exception as e:
                print(f"[WARN] category_infocode_mapping 테이블 생성 중 오류: {e}")
                conn.rollback()

            cursor.close()
            conn.close()
    except Exception as e:
        print(f"[WARN] 데이터베이스 마이그레이션 실패 (계속 진행): {e}")

    # 플레이오토 스케줄러 시작
    try:
        start_playauto_scheduler()
        print("[INFO] 플레이오토 스케줄러 시작 완료")
    except Exception as e:
        print(f"[WARN] 플레이오토 스케줄러 시작 실패: {e}")
        import traceback
        traceback.print_exc()

    # 상품 모니터링 스케줄러 시작
    try:
        start_monitor_scheduler()
        print("[INFO] 상품 모니터링 스케줄러 시작 완료")
    except Exception as e:
        print(f"[WARN] 상품 모니터링 스케줄러 시작 실패: {e}")

    # 데이터베이스 백업 스케줄러 시작
    try:
        start_backup_scheduler()
        print("[INFO] 데이터베이스 백업 스케줄러 시작 완료")
    except Exception as e:
        print(f"[WARN] 데이터베이스 백업 스케줄러 시작 실패: {e}")

    # 송장 업로드 스케줄러 시작
    try:
        start_tracking_scheduler()
        print("[INFO] 송장 업로드 스케줄러 시작 완료")
    except Exception as e:
        print(f"[WARN] 송장 업로드 스케줄러 시작 실패: {e}")

    yield

    # Shutdown
    print("[INFO] 서버 종료 중...")

    # 플레이오토 스케줄러 중지
    try:
        stop_playauto_scheduler()
        print("[INFO] 플레이오토 스케줄러 중지 완료")
    except Exception as e:
        print(f"[WARN] 플레이오토 스케줄러 중지 실패: {e}")

    # 상품 모니터링 스케줄러 중지
    try:
        stop_monitor_scheduler()
        print("[INFO] 상품 모니터링 스케줄러 중지 완료")
    except Exception as e:
        print(f"[WARN] 상품 모니터링 스케줄러 중지 실패: {e}")

    # 데이터베이스 백업 스케줄러 중지
    try:
        stop_backup_scheduler()
        print("[INFO] 데이터베이스 백업 스케줄러 중지 완료")
    except Exception as e:
        print(f"[WARN] 데이터베이스 백업 스케줄러 중지 실패: {e}")

    # 송장 업로드 스케줄러 중지
    try:
        stop_tracking_scheduler()
        print("[INFO] 송장 업로드 스케줄러 중지 완료")
    except Exception as e:
        print(f"[WARN] 송장 업로드 스케줄러 중지 실패: {e}")

# FastAPI 앱 생성
app = FastAPI(
    title="물바다AI 통합 자동화 API",
    description="상품 수집, 모니터링, RPA 자동 발주를 제공하는 통합 API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정 (Next.js 프론트엔드와 통신 허용)
allowed_origins = []

# 개발 환경
if os.getenv('ENVIRONMENT') != 'production':
    allowed_origins.extend([
        "http://localhost:3000",  # Next.js 개발 서버
        "http://localhost:3001",  # 대체 포트
    ])

# 프로덕션 환경 - 환경 변수로 정확한 URL 지정
if os.getenv('ENVIRONMENT') == 'production':
    frontend_url = os.getenv('FRONTEND_URL')
    if frontend_url:
        # 명시적으로 지정된 프론트엔드 URL만 허용
        allowed_origins.append(frontend_url)
        print(f"[OK] CORS allowed origin: {frontend_url}")
    else:
        # FRONTEND_URL이 설정되지 않은 경우 Vercel 도메인 허용
        print("[WARN] FRONTEND_URL not set - allowing Vercel domains")
        allowed_origins.append("https://bada-auction.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Requested-With",
        "X-Admin-Password",  # Admin API 인증 헤더
    ],
    # Vercel preview 도메인을 위한 정규식 패턴
    allow_origin_regex=r"https://.*\.vercel\.app",
)

# Static 파일 서빙 설정 (개발 환경에서만 필요)
import os
from pathlib import Path

# Static 디렉토리 마운트 (읽기 전용 환경 고려)
static_dir = Path(__file__).parent / "static"
try:
    # 디렉토리가 없으면 생성 시도 (개발 환경)
    if not static_dir.exists() and os.getenv('ENVIRONMENT') != 'production':
        static_dir.mkdir(parents=True, exist_ok=True)

    # 디렉토리가 존재하면 마운트
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static 파일 서빙 활성화: {static_dir}")
    else:
        logger.warning("Static 디렉토리 없음 (프로덕션에서는 Supabase Storage 사용)")
except Exception as e:
    logger.warning(f"Static 파일 마운트 실패 (무시): {e}")

# 이미지 파일 서빙 설정 (개발 환경에서만)
# 프로덕션에서는 Supabase Storage 직접 사용
if os.getenv('ENVIRONMENT') != 'production':
    images_dir = Path(__file__).parent.parent / "supabase-images"
    if images_dir.exists():
        try:
            app.mount("/supabase-images", StaticFiles(directory=str(images_dir)), name="supabase-images")
            logger.info(f"이미지 디렉토리 마운트: {images_dir}")
        except Exception as e:
            logger.warning(f"이미지 디렉토리 마운트 실패: {e}")
    else:
        logger.info("로컬 이미지 디렉토리 없음 (Supabase Storage 사용)")
else:
    logger.info("프로덕션 환경: Supabase Storage 사용 (로컬 이미지 마운트 비활성화)")

# 라우터 등록
app.include_router(dashboard_router)
app.include_router(sourcing_router)
app.include_router(monitoring_router)
app.include_router(orders_router)

# Playauto router with debug
import sys
sys.stderr.write(f"\n[MAIN] About to register playauto_router with {len(playauto_router.routes)} routes\n")
for r in playauto_router.routes:
    sys.stderr.write(f"[MAIN]   - {r.path} ({r.methods})\n")
sys.stderr.flush()

app.include_router(playauto_router)

sys.stderr.write(f"\n[MAIN] About to register playauto_categories_router with {len(playauto_categories_router.routes)} routes\n")
for r in playauto_categories_router.routes:
    sys.stderr.write(f"[MAIN]   - {r.path} ({r.methods})\n")
sys.stderr.flush()

try:
    app.include_router(playauto_categories_router)
    sys.stderr.write(f"[MAIN] Successfully included playauto_categories_router\n")
    sys.stderr.flush()
except Exception as e:
    sys.stderr.write(f"[MAIN ERROR] Failed to include playauto_categories_router: {e}\n")
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()

sys.stderr.write(f"[MAIN] Playauto routers registered. Total app routes: {len(app.routes)}\n")
sys.stderr.flush()

app.include_router(tracking_scheduler_router)
app.include_router(notifications_router)
app.include_router(scheduler_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(accounting_router)

# Category mappings router
print(f"[DEBUG] About to register category_mappings_router with {len(category_mappings_router.routes)} routes")
for r in category_mappings_router.routes:
    print(f"[DEBUG]   - {r.path} ({r.methods})")
app.include_router(category_mappings_router)
print(f"[DEBUG] Category mappings router registered. Total app routes: {len(app.routes)}")

# PlayAuto category mappings router
print(f"[DEBUG] About to register category_playauto_mappings_router with {len(category_playauto_mappings_router.routes)} routes")
app.include_router(category_playauto_mappings_router)
print(f"[DEBUG] PlayAuto category mappings router registered. Total app routes: {len(app.routes)}")

# WebSocket router
app.include_router(websocket_router)
print(f"[OK] WebSocket router registered")

# Auto Pricing router
app.include_router(auto_pricing_router)
print(f"[OK] Auto Pricing router registered")

# Admin router (with error handling)
if admin_router is not None:
    app.include_router(admin_router)
    print(f"[OK] Admin router registered")
else:
    print(f"[ERROR] Admin router not registered")

# 등록된 라우트 출력 (디버깅용)
logger.debug("\n등록된 라우트:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        if 'products' in route.path or 'admin' in route.path:
            logger.debug(f"  {route.path} {route.methods}")

# 디버그: 전체 라우트 확인 (개발 환경에서만)
@app.get("/debug/routes")
async def debug_routes():
    # 프로덕션 환경에서는 비활성화
    if os.getenv('ENVIRONMENT') == 'production':
        raise HTTPException(
            status_code=404,
            detail="Debug endpoints are disabled in production"
        )

    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(getattr(route, 'methods', []))
            })
    return {"total_routes": len(routes), "routes": routes}


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "물바다AI 상품 수집 API",
        "version": "1.0.0",
        "endpoints": {
            "sourcing": "/api/sourcing",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment"""
    from datetime import datetime
    from fastapi.responses import JSONResponse

    try:
        # Test database connection
        db = get_db()
        db.get_dashboard_stats()  # Simple query to verify DB connection

        return {
            "status": "healthy",
            "database": "connected",
            "environment": os.getenv("USE_POSTGRESQL", "false"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
