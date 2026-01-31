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

# Admin router import with error handling
try:
    from api.admin import router as admin_router
    print(f"[OK] Admin router imported: {len(admin_router.routes)} routes")
except Exception as e:
    print(f"[ERROR] Failed to import admin router: {e}")
    import traceback
    traceback.print_exc()
    admin_router = None
from database.db import get_db
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
REQUIRED_ENV_VARS = ['OPENAI_API_KEY']  # 필수 환경 변수 목록
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    logger.error(f"필수 환경 변수 누락: {', '.join(missing_vars)}")
    logger.error("애플리케이션을 시작할 수 없습니다. .env.local 파일을 확인하세요.")
    # 개발 환경에서는 경고만 표시, 프로덕션에서는 종료
    if os.getenv('ENVIRONMENT') == 'production':
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
else:
    logger.info("모든 필수 환경 변수 확인 완료")

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

    # 플레이오토 스케줄러 시작
    try:
        db = get_db()
        enabled = db.get_playauto_setting("enabled") == "true"
        if enabled:
            start_playauto_scheduler()
            print("[INFO] 플레이오토 스케줄러 시작 완료")
    except Exception as e:
        print(f"[WARN] 플레이오토 스케줄러 시작 실패: {e}")

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
        # FRONTEND_URL이 설정되지 않은 경우 경고
        print("[WARN] FRONTEND_URL not set in production - CORS may fail")
        # 임시로 모든 origin 허용 (보안 위험 - FRONTEND_URL 설정 권장)
        allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if allowed_origins != ["*"] else False,  # 와일드카드 사용 시 credentials 비활성화
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Requested-With",
    ],
)

# Static 파일 서빙 설정
import os
from pathlib import Path
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 이미지 파일 서빙 설정
images_dir = Path(__file__).parent.parent / "supabase-images"
if images_dir.exists():
    app.mount("/supabase-images", StaticFiles(directory=str(images_dir)), name="supabase-images")
    print(f"[OK] 이미지 디렉토리 마운트: {images_dir}")
else:
    print(f"[WARN] 이미지 디렉토리를 찾을 수 없습니다: {images_dir}")

# 라우터 등록
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

# 디버그: 전체 라우트 확인
@app.get("/debug/routes")
async def debug_routes():
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
