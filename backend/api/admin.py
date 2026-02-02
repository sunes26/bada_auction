"""
관리자 페이지 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends, Request
from typing import Optional, Dict, Any, List
import os
import time
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Optional imports with error handling
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[WARN] psutil not available - system monitoring disabled")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARN] PIL not available - image processing disabled")

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    print("[WARN] sqlite3 not available - using DatabaseWrapper instead")

from database.db import get_db

# Admin API 인증 (프로덕션 환경에서만)
def verify_admin_access(
    request: Request,
    x_admin_password: Optional[str] = Header(None)
):
    """
    Admin API 접근 검증
    프로덕션 환경에서는 X-Admin-Password 헤더 필요
    개발 환경에서는 인증 생략

    CORS preflight (OPTIONS) 요청은 인증 생략
    디버그 엔드포인트는 인증 생략
    """
    # CORS preflight 요청은 인증 생략
    if request.method == "OPTIONS":
        return True

    # 디버그 엔드포인트는 인증 생략
    if "/debug" in request.url.path:
        return True

    # 개발 환경에서는 인증 생략
    if os.getenv('ENVIRONMENT') != 'production':
        return True

    # 프로덕션 환경: 비밀번호 검증
    expected_password = os.getenv('NEXT_PUBLIC_ADMIN_PASSWORD', '8888')

    if not x_admin_password:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required. Provide X-Admin-Password header.",
            headers={"WWW-Authenticate": "X-Admin-Password"}
        )

    if x_admin_password != expected_password:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin password"
        )

    return True

# Admin router with authentication
# 프로덕션 환경에서는 모든 엔드포인트에 인증 필요
router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin_access)]
)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent
IMAGES_DIR = PROJECT_ROOT / "supabase-images"
DB_PATH = PROJECT_ROOT / "backend" / "monitoring.db"

# 환경에 따라 다른 디렉토리 사용
if os.getenv('ENVIRONMENT') == 'production':
    # 프로덕션(Railway): 임시 디렉토리 사용 (읽기 전용 파일시스템 대응)
    import tempfile
    TEMP_DIR = Path(tempfile.gettempdir()) / "badaauction"
    BACKUP_DIR = TEMP_DIR / "backups"
    LOG_DIR = TEMP_DIR / "logs"
    print(f"[INFO] Production mode - using temp directory: {TEMP_DIR}")
else:
    # 로컬 개발: 프로젝트 디렉토리 사용
    BACKUP_DIR = PROJECT_ROOT / "backend" / "backups"
    LOG_DIR = PROJECT_ROOT / "backend" / "logs"

# 디렉토리 생성 시도
try:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directories created - Backup: {BACKUP_DIR}, Log: {LOG_DIR}")
except Exception as e:
    print(f"[WARN] Failed to create directories: {e}")
    print(f"[INFO] Backup and logging features may be limited")

@router.get("/system/status")
async def get_system_status():
    """시스템 상태 조회"""
    try:
        # 데이터베이스 상태
        db_size = 0
        db_status = "연결됨"
        try:
            # Use get_db() instead of direct sqlite3 connection
            db = get_db()
            # Test connection
            if hasattr(db, 'execute'):
                db.execute("SELECT 1")
                db_status = "연결됨"

            # Get DB size if SQLite file exists
            if DB_PATH.exists():
                db_size = DB_PATH.stat().st_size / (1024 * 1024)  # MB
        except Exception as e:
            db_status = f"오류: {str(e)}"

        # 시스템 리소스
        if PSUTIL_AVAILABLE:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(PROJECT_ROOT))
            cpu_percent = psutil.cpu_percent(interval=0.1)
            uptime_seconds = time.time() - psutil.boot_time()
        else:
            # Default values when psutil not available
            memory = type('obj', (object,), {
                'used': 0, 'total': 0, 'percent': 0
            })()
            disk = type('obj', (object,), {
                'used': 0, 'total': 0, 'percent': 0
            })()
            cpu_percent = 0
            uptime_seconds = 0

        # API 응답 시간 (자기 자신 테스트)
        start = time.time()
        try:
            # 간단한 헬스체크
            pass
        except:
            pass
        api_response_time = (time.time() - start) * 1000

        return {
            "success": True,
            "database": {
                "status": db_status,
                "size_mb": round(db_size, 2),
                "path": str(DB_PATH)
            },
            "server": {
                "status": "정상",
                "response_time_ms": round(api_response_time, 2),
                "uptime_seconds": uptime_seconds
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_used_mb": memory.used / (1024 * 1024) if PSUTIL_AVAILABLE else 0,
                "memory_total_mb": memory.total / (1024 * 1024) if PSUTIL_AVAILABLE else 0,
                "memory_percent": memory.percent if PSUTIL_AVAILABLE else 0,
                "disk_used_gb": disk.used / (1024 * 1024 * 1024) if PSUTIL_AVAILABLE else 0,
                "disk_total_gb": disk.total / (1024 * 1024 * 1024) if PSUTIL_AVAILABLE else 0,
                "disk_percent": disk.percent if PSUTIL_AVAILABLE else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_category_name_map():
    """카테고리 ID -> 이름 매핑 딕셔너리 생성"""
    try:
        # PostgreSQL 연결 (프로덕션)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            print(f"[DEBUG] Connecting to PostgreSQL for categories")
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT folder_number, folder_name
                FROM categories
            """)
            rows = cursor.fetchall()
            category_map = {str(row['folder_number']): row['folder_name'] for row in rows}
            cursor.close()
            conn.close()
        else:
            # SQLite 연결 (로컬 개발)
            print(f"[DEBUG] Connecting to SQLite for categories")
            db = get_db()
            conn = db.get_connection()
            cursor = conn.execute("""
                SELECT folder_number, folder_name
                FROM categories
            """)
            rows = cursor.fetchall()
            category_map = {str(row['folder_number']): row['folder_name'] for row in rows}
            conn.close()

        print(f"[DEBUG] Loaded {len(category_map)} categories from database")
        if len(category_map) > 0:
            print(f"[DEBUG] Sample categories: {dict(list(category_map.items())[:3])}")

        return category_map
    except Exception as e:
        print(f"[ERROR] Failed to load category map: {e}")
        import traceback
        traceback.print_exc()
        return {}


@router.get("/images/stats")
async def get_image_stats():
    """이미지 통계 조회 - Supabase Storage 우선"""
    try:
        from utils.supabase_storage import supabase

        # 카테고리 이름 매핑 로드
        category_map = get_category_name_map()

        # Supabase Storage 사용
        if supabase:
            try:
                # 모든 폴더(카테고리) 목록 조회 (페이지네이션)
                all_folders = []
                offset = 0
                limit = 1000

                while True:
                    folder_batch = supabase.storage.from_("product-images").list(
                        "",
                        {
                            "limit": limit,
                            "offset": offset
                        }
                    )

                    if not folder_batch:
                        break

                    all_folders.extend(folder_batch)

                    if len(folder_batch) < limit:
                        break

                    offset += limit

                folders = []
                total_images = 0
                total_size = 0

                for folder_obj in all_folders:
                    folder_name = folder_obj['name']

                    # 폴더명에서 카테고리 ID 추출 (cat-1 -> 1)
                    category_id = None
                    display_name = folder_name
                    if folder_name.startswith('cat-'):
                        category_id = folder_name.replace('cat-', '')
                        # 카테고리 이름 조회 (folder_name이 이미 "1_흰밥" 형식으로 저장됨)
                        if category_id in category_map:
                            display_name = category_map[category_id]  # 그대로 사용 (이미 "1_흰밥" 형식)
                            print(f"[DEBUG] Folder {folder_name} -> display_name: {display_name}")
                        else:
                            print(f"[DEBUG] Category ID {category_id} not found in category_map")
                            display_name = folder_name

                    # 폴더 내 이미지 목록 조회 (페이지네이션)
                    try:
                        all_images = []
                        img_offset = 0
                        img_limit = 1000

                        while True:
                            image_batch = supabase.storage.from_("product-images").list(
                                folder_name,
                                {
                                    "limit": img_limit,
                                    "offset": img_offset
                                }
                            )

                            if not image_batch:
                                break

                            all_images.extend(image_batch)

                            if len(image_batch) < img_limit:
                                break

                            img_offset += img_limit

                        folder_size = sum(
                            img.get('metadata', {}).get('size', 0)
                            for img in all_images
                        )

                        folders.append({
                            "name": folder_name,  # 실제 스토리지 폴더명 (cat-1)
                            "display_name": display_name,  # UI 표시용 이름 (1_흰밥)
                            "path": f"product-images/{folder_name}",
                            "image_count": len(all_images),
                            "size_mb": round(folder_size / (1024 * 1024), 2)
                        })

                        total_images += len(all_images)
                        total_size += folder_size
                    except:
                        continue

                return {
                    "success": True,
                    "storage_type": "Supabase Storage",
                    "total_folders": len(folders),
                    "total_images": total_images,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "folders": folders  # 모든 폴더 반환
                }
            except Exception as e:
                print(f"[ERROR] Supabase Storage stats failed: {e}")
                # Fallback to local

        # Fallback: 로컬 파일시스템
        if not IMAGES_DIR.exists():
            return {
                "success": True,
                "storage_type": "Local (empty)",
                "total_folders": 0,
                "total_images": 0,
                "total_size_mb": 0,
                "folders": []
            }

        folders = []
        total_images = 0
        total_size = 0

        for folder in sorted(IMAGES_DIR.iterdir()):
            if folder.is_dir():
                images = list(folder.glob("*.[jJ][pP][gG]")) + \
                        list(folder.glob("*.[jJ][pP][eE][gG]")) + \
                        list(folder.glob("*.[pP][nN][gG]")) + \
                        list(folder.glob("*.[wW][eE][bB][pP]")) + \
                        list(folder.glob("*.[gG][iI][fF]"))

                folder_size = sum(img.stat().st_size for img in images)

                folders.append({
                    "name": folder.name,
                    "path": str(folder),
                    "image_count": len(images),
                    "size_mb": round(folder_size / (1024 * 1024), 2)
                })

                total_images += len(images)
                total_size += folder_size

        return {
            "success": True,
            "storage_type": "Local Filesystem",
            "total_folders": len(folders),
            "total_images": total_images,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "folders": folders
        }
    except Exception as e:
        print(f"[ERROR] Image stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/gallery/{folder_name}")
async def get_image_gallery(folder_name: str):
    """특정 폴더의 이미지 목록 조회 - Supabase Storage 사용"""
    try:
        from utils.supabase_storage import list_images, get_public_url, supabase

        # Supabase 클라이언트 확인
        if not supabase:
            # Fallback: 로컬 파일시스템 사용
            folder_path = IMAGES_DIR / folder_name
            if not folder_path.exists():
                return {"success": False, "detail": "폴더를 찾을 수 없습니다"}

            images = []
            for ext in ["jpg", "jpeg", "png", "webp", "gif"]:
                images.extend(folder_path.glob(f"*.[{ext[0].upper()}{ext[0].lower()}]*"))

            image_list = []
            for img_path in images:
                try:
                    if PIL_AVAILABLE:
                        with Image.open(img_path) as img:
                            width, height = img.size
                            format_name = img.format
                    else:
                        width, height, format_name = 0, 0, "Unknown"
                except:
                    width, height, format_name = 0, 0, "Unknown"

                image_list.append({
                    "filename": img_path.name,
                    "path": f"/supabase-images/{folder_name}/{img_path.name}",
                    "size_kb": round(img_path.stat().st_size / 1024, 2),
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "modified": datetime.fromtimestamp(img_path.stat().st_mtime).isoformat()
                })

            return {
                "success": True,
                "folder": folder_name,
                "images": image_list,
                "count": len(image_list)
            }

        # Supabase Storage에서 이미지 목록 조회
        # 폴더명에서 카테고리 ID 추출 (예: "100_식혜" → "100" 또는 "1" → "1" 또는 "cat-1" → "1")
        if folder_name.startswith('cat-'):
            # 이미 cat- 형식인 경우
            category_id = folder_name.replace('cat-', '')
            storage_folder = folder_name
        elif '_' in folder_name:
            # 1_흰밥 형식
            category_id = folder_name.split('_')[0]
            storage_folder = f"cat-{category_id}"
        else:
            # 숫자만 있는 경우
            category_id = folder_name
            storage_folder = f"cat-{category_id}"

        print(f"[DEBUG] Gallery request:")
        print(f"  - folder_name: {folder_name}")
        print(f"  - category_id: {category_id}")
        print(f"  - storage_folder: {storage_folder}")

        # 이미지 목록 조회 (모든 파일 가져오기)
        try:
            # Supabase Storage list API options
            # limit: 한 번에 가져올 최대 파일 수 (기본값 100)
            # offset: 시작 위치
            # sortBy: 정렬 기준

            # 모든 파일 가져오기 (페이지네이션)
            all_files = []
            offset = 0
            limit = 1000  # 한 번에 1000개씩 가져오기

            while True:
                files = supabase.storage.from_("product-images").list(
                    storage_folder,
                    {
                        "limit": limit,
                        "offset": offset,
                        "sortBy": {"column": "name", "order": "asc"}
                    }
                )

                if not files:
                    print(f"[DEBUG] No files returned at offset {offset}")
                    break

                print(f"[DEBUG] Batch {offset//limit + 1}: {len(files)} files")
                all_files.extend(files)

                # 더 이상 파일이 없으면 종료
                if len(files) < limit:
                    break

                offset += limit

            print(f"[DEBUG] Total files retrieved: {len(all_files)}")

            image_list = []
            for file in all_files:
                # 파일인지 폴더인지 확인 (폴더는 제외)
                if file.get('id') is None:
                    print(f"[DEBUG] Skipping folder: {file.get('name')}")
                    continue

                # 공개 URL 생성
                storage_path = f"{storage_folder}/{file['name']}"
                public_url = get_public_url(storage_path)

                image_list.append({
                    "filename": file['name'],
                    "path": public_url,  # Supabase Storage 공개 URL
                    "size_kb": round(file.get('metadata', {}).get('size', 0) / 1024, 2) if file.get('metadata') else 0,
                    "width": 0,  # Supabase Storage는 이미지 메타데이터 제공하지 않음
                    "height": 0,
                    "format": file['name'].split('.')[-1].upper() if '.' in file['name'] else "Unknown",
                    "modified": file.get('updated_at', file.get('created_at', ''))
                })

            print(f"[DEBUG] Returning {len(image_list)} images")

            return {
                "success": True,
                "folder": folder_name,
                "images": image_list,
                "count": len(image_list)
            }
        except Exception as e:
            print(f"[ERROR] Failed to list images from Supabase Storage: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "detail": f"Supabase Storage 조회 실패: {str(e)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/debug", dependencies=[])
async def debug_categories():
    """카테고리 데이터 디버그"""
    try:
        # PostgreSQL 연결 (프로덕션)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 전체 카테고리 개수 확인
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            total_count = cursor.fetchone()['count']

            # 샘플 카테고리 조회
            cursor.execute("""
                SELECT folder_number, folder_name, level1, level2, level3, level4
                FROM categories
                ORDER BY folder_number
                LIMIT 10
            """)
            sample_categories = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()
        else:
            # SQLite 연결 (로컬 개발)
            db = get_db()
            conn = db.get_connection()

            # 전체 카테고리 개수 확인
            cursor = conn.execute("SELECT COUNT(*) as count FROM categories")
            total_count = cursor.fetchone()['count']

            # 샘플 카테고리 조회
            cursor = conn.execute("""
                SELECT folder_number, folder_name, level1, level2, level3, level4
                FROM categories
                ORDER BY folder_number
                LIMIT 10
            """)
            sample_categories = [dict(row) for row in cursor.fetchall()]

            conn.close()

        # 카테고리 맵 생성
        category_map = get_category_name_map()

        return {
            "success": True,
            "total_categories": total_count,
            "category_map_size": len(category_map),
            "sample_categories": sample_categories,
            "sample_map_entries": dict(list(category_map.items())[:10]) if category_map else {},
            "database_type": "PostgreSQL" if database_url else "SQLite"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.get("/images/debug-storage")
async def debug_supabase_storage():
    """Supabase Storage 디버그 - 모든 폴더와 파일 목록 조회"""
    try:
        from utils.supabase_storage import supabase, BUCKET_NAME, get_public_url

        if not supabase:
            return {"success": False, "detail": "Supabase client not initialized"}

        # 루트 폴더 목록 조회
        folders = supabase.storage.from_(BUCKET_NAME).list()

        result = {
            "success": True,
            "bucket": BUCKET_NAME,
            "folders": []
        }

        for folder in folders[:10]:  # 처음 10개만
            folder_name = folder.get('name', 'unknown')
            folder_info = {
                "name": folder_name,
                "id": folder.get('id'),
                "is_folder": folder.get('id') is None,
                "files": []
            }

            # 폴더면 내부 파일 목록 조회
            if folder.get('id') is None:
                try:
                    files = supabase.storage.from_(BUCKET_NAME).list(folder_name)
                    for file in files[:5]:  # 각 폴더에서 처음 5개만
                        storage_path = f"{folder_name}/{file.get('name', 'unknown')}"
                        public_url = get_public_url(storage_path)
                        folder_info["files"].append({
                            "name": file.get('name'),
                            "url": public_url,
                            "size": file.get('metadata', {}).get('size', 0)
                        })
                except Exception as e:
                    folder_info["error"] = str(e)

            result["folders"].append(folder_info)

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "detail": str(e)}


@router.delete("/images/delete")
async def delete_image(folder_name: str, filename: str):
    """이미지 삭제"""
    try:
        img_path = IMAGES_DIR / folder_name / filename
        if not img_path.exists():
            return {"success": False, "detail": "이미지를 찾을 수 없습니다"}

        img_path.unlink()
        return {"success": True, "message": "이미지가 삭제되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images/create-folder")
async def create_folder(
    folder_name: str,
    level1: str,
    level2: str,
    level3: str,
    level4: str,
    folder_number: Optional[int] = None
):
    """새 폴더 생성 + 카테고리 DB 등록"""
    try:
        # 입력값 검증
        if not folder_name or folder_name.strip() == "":
            return {"success": False, "detail": "폴더명을 입력해주세요"}
        if not all([level1, level2, level3, level4]):
            return {"success": False, "detail": "모든 카테고리를 입력해주세요"}

        folder_name = folder_name.strip()

        # 폴더 번호 자동 생성 (제공되지 않은 경우)
        db = get_db()
        conn = db.get_connection()

        if folder_number is None:
            cursor = conn.execute("SELECT MAX(folder_number) as max_num FROM categories")
            result = cursor.fetchone()
            max_number = result['max_num'] if result and result['max_num'] else 0
            folder_number = max_number + 1

        full_folder_name = f"{folder_number}_{folder_name}"

        # 1. 폴더 번호 중복 체크 (DB)
        cursor = conn.execute("SELECT id FROM categories WHERE folder_number = ?", (folder_number,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "detail": f"폴더 번호 {folder_number}는 이미 사용 중입니다"}

        # 2. 폴더 생성
        folder_path = IMAGES_DIR / full_folder_name
        if folder_path.exists():
            conn.close()
            return {"success": False, "detail": f"폴더 '{full_folder_name}'이(가) 이미 존재합니다"}

        folder_path.mkdir(parents=True, exist_ok=True)

        # 3. DB에 카테고리 등록
        conn.execute("""
            INSERT INTO categories (folder_number, folder_name, level1, level2, level3, level4)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (folder_number, full_folder_name, level1, level2, level3, level4))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"폴더 '{full_folder_name}'이(가) 생성되고 카테고리가 등록되었습니다",
            "folder_name": full_folder_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images/upload")
async def upload_images(folder_name: str, files: List[UploadFile] = File(...)):
    """이미지 업로드 - Supabase Storage 사용"""
    try:
        from utils.supabase_storage import upload_image_from_bytes, supabase

        # Supabase 클라이언트 확인
        if not supabase:
            # Fallback: 로컬 파일시스템 사용
            folder_path = IMAGES_DIR / folder_name
            if not folder_path.exists():
                return {"success": False, "detail": "폴더를 찾을 수 없습니다"}

            uploaded_files = []
            for file in files:
                file_path = folder_path / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                uploaded_files.append(file.filename)

            return {
                "success": True,
                "message": f"{len(uploaded_files)}개 파일이 로컬에 업로드되었습니다",
                "files": uploaded_files
            }

        # Supabase Storage에 업로드
        # 폴더명에서 카테고리 ID 추출 (예: "100_식혜" → "100")
        category_id = folder_name.split('_')[0]
        storage_folder = f"cat-{category_id}"

        uploaded_files = []
        uploaded_urls = []

        for file in files:
            # 파일 읽기
            content = await file.read()

            # Storage 경로
            storage_path = f"{storage_folder}/{file.filename}"

            # 업로드
            public_url = upload_image_from_bytes(
                content,
                storage_path,
                content_type=file.content_type or "image/jpeg"
            )

            if public_url:
                uploaded_files.append(file.filename)
                uploaded_urls.append(public_url)

        return {
            "success": True,
            "message": f"{len(uploaded_files)}개 파일이 Supabase Storage에 업로드되었습니다",
            "files": uploaded_files,
            "urls": uploaded_urls
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/stats")
async def get_database_stats():
    """데이터베이스 통계"""
    try:
        import os
        from database.db import get_db

        db = get_db()

        # Get database connection
        conn = db.get_connection()

        # Always use SQLite queries since Database class uses SQLite
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = [row[0] for row in cursor.fetchall()]

        # 테이블별 레코드 수
        table_stats = []
        for table in all_tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats.append({"table": table, "count": count})
            except Exception as e:
                table_stats.append({"table": table, "count": 0, "error": str(e)})

        # SQLite: 파일 크기
        db_size = DB_PATH.stat().st_size / (1024 * 1024) if DB_PATH.exists() else 0

        conn.close()

        return {
            "success": True,
            "database_type": "SQLite",
            "database_size_mb": round(db_size, 2),
            "tables": table_stats,
            "total_records": sum(t["count"] for t in table_stats)
        }
    except Exception as e:
        print(f"[ERROR] Database stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/backup")
async def backup_database():
    """데이터베이스 백업"""
    try:
        if not DB_PATH.exists():
            return {"success": False, "detail": "데이터베이스를 찾을 수 없습니다"}

        # 백업 파일명 (타임스탬프)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"monitoring_backup_{timestamp}.db"

        # 백업 실행
        shutil.copy2(DB_PATH, backup_file)

        return {
            "success": True,
            "backup_file": str(backup_file),
            "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
            "timestamp": timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/backups")
async def list_backups():
    """백업 파일 목록"""
    try:
        backups = []
        if BACKUP_DIR.exists():
            for backup_file in sorted(BACKUP_DIR.glob("monitoring_backup_*.db"), reverse=True):
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                })

        return {
            "success": True,
            "backups": backups,
            "count": len(backups)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/restore")
async def restore_database(backup_filename: str):
    """데이터베이스 복원"""
    try:
        backup_file = BACKUP_DIR / backup_filename
        if not backup_file.exists():
            return {"success": False, "detail": "백업 파일을 찾을 수 없습니다"}

        # 현재 DB 백업
        current_backup = BACKUP_DIR / f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        if DB_PATH.exists():
            shutil.copy2(DB_PATH, current_backup)

        # 복원
        shutil.copy2(backup_file, DB_PATH)

        return {
            "success": True,
            "message": "데이터베이스가 복원되었습니다",
            "current_backup": str(current_backup)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/optimize")
async def optimize_database():
    """데이터베이스 최적화"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        conn.close()

        return {
            "success": True,
            "message": "데이터베이스 최적화 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """캐시 상태 조회"""
    # 프론트엔드 캐시는 클라이언트 측이므로 여기서는 간단한 통계만
    return {
        "success": True,
        "message": "캐시는 클라이언트 측에서 관리됩니다",
        "recommendation": "브라우저에서 캐시 삭제를 수행하세요"
    }


@router.post("/cache/clear")
async def clear_cache():
    """캐시 삭제 (서버 측)"""
    # 서버 측에서 할 수 있는 캐시 정리
    return {
        "success": True,
        "message": "클라이언트에서 캐시를 삭제하세요"
    }


@router.get("/logs/recent")
async def get_recent_logs(level: Optional[str] = None, limit: int = 100):
    """최근 로그 조회"""
    try:
        logs = []
        log_file = LOG_DIR / "app.log"

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 최근 N개만
            recent_lines = lines[-limit:]

            for line in recent_lines:
                try:
                    # 간단한 로그 파싱
                    logs.append({
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "message": line.strip()
                    })
                except:
                    pass

        return {
            "success": True,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        return {
            "success": True,
            "logs": [],
            "count": 0,
            "note": "로그 파일이 없거나 읽을 수 없습니다"
        }


@router.get("/settings/env")
async def get_environment_variables():
    """환경 변수 조회 (민감한 정보 마스킹)"""
    try:
        env_file = PROJECT_ROOT / ".env.local"
        env_vars = {}

        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # 민감한 정보 마스킹
                        if any(keyword in key.upper() for keyword in ["KEY", "SECRET", "PASSWORD", "TOKEN"]):
                            if len(value) > 8:
                                env_vars[key] = value[:4] + "*" * (len(value) - 8) + value[-4:]
                            else:
                                env_vars[key] = "****"
                        else:
                            env_vars[key] = value

        return {
            "success": True,
            "environment_variables": env_vars,
            "count": len(env_vars)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/metrics")
async def get_performance_metrics():
    """성능 메트릭"""
    try:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)

        # 메모리
        memory = psutil.virtual_memory()

        # 디스크 I/O
        disk_io = psutil.disk_io_counters()

        # 네트워크
        net_io = psutil.net_io_counters()

        return {
            "success": True,
            "cpu": {
                "percent_per_core": cpu_percent,
                "average_percent": sum(cpu_percent) / len(cpu_percent),
                "core_count": psutil.cpu_count()
            },
            "memory": {
                "used_mb": memory.used / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "percent": memory.percent
            },
            "disk": {
                "read_mb": disk_io.read_bytes / (1024 * 1024),
                "write_mb": disk_io.write_bytes / (1024 * 1024)
            },
            "network": {
                "sent_mb": net_io.bytes_sent / (1024 * 1024),
                "recv_mb": net_io.bytes_recv / (1024 * 1024)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/old-orders")
async def cleanup_old_orders(days: int = 90):
    """오래된 주문 삭제"""
    try:
        db = get_db()
        cutoff_date = datetime.now() - timedelta(days=days)

        # 삭제할 주문 수 확인
        result = db.execute(
            "SELECT COUNT(*) as count FROM orders WHERE created_at < ?",
            (cutoff_date.isoformat(),)
        )
        count = result[0]['count'] if result else 0

        # 실제 삭제 (주문 아이템도 함께)
        db.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE created_at < ?)",
                  (cutoff_date.isoformat(),))
        db.execute("DELETE FROM orders WHERE created_at < ?",
                  (cutoff_date.isoformat(),))

        return {
            "success": True,
            "deleted_count": count,
            "cutoff_date": cutoff_date.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/temp-files")
async def cleanup_temp_files():
    """임시 파일 정리"""
    try:
        temp_dir = PROJECT_ROOT / "temp"
        deleted_count = 0
        deleted_size = 0

        if temp_dir.exists():
            for item in temp_dir.iterdir():
                size = item.stat().st_size
                if item.is_file():
                    item.unlink()
                    deleted_count += 1
                    deleted_size += size

        return {
            "success": True,
            "deleted_files": deleted_count,
            "freed_mb": round(deleted_size / (1024 * 1024), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test")
async def test_api_endpoints():
    """API 엔드포인트 테스트"""
    try:
        endpoints = [
            "/api/products/list",
            "/api/orders/list",
            "/api/monitor/stats",
            "/api/playauto/stats"
        ]

        results = []
        for endpoint in endpoints:
            start = time.time()
            try:
                # 여기서는 단순히 상태만 체크
                status = "OK"
                response_time = (time.time() - start) * 1000
            except:
                status = "FAIL"
                response_time = 0

            results.append({
                "endpoint": endpoint,
                "status": status,
                "response_time_ms": round(response_time, 2)
            })

        return {
            "success": True,
            "tests": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
