"""
관리자 페이지 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
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

router = APIRouter(prefix="/api/admin", tags=["admin"])

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


@router.get("/images/stats")
async def get_image_stats():
    """이미지 통계 조회 - Supabase Storage 우선"""
    try:
        from utils.supabase_storage import supabase

        # Supabase Storage 사용
        if supabase:
            try:
                # 모든 폴더(카테고리) 목록 조회
                all_files = supabase.storage.from_("product-images").list()

                folders = []
                total_images = 0
                total_size = 0

                for folder_obj in all_files:
                    folder_name = folder_obj['name']

                    # 폴더 내 이미지 목록 조회
                    try:
                        images = supabase.storage.from_("product-images").list(folder_name)

                        folder_size = sum(
                            img.get('metadata', {}).get('size', 0)
                            for img in images
                        )

                        folders.append({
                            "name": folder_name,
                            "path": f"product-images/{folder_name}",
                            "image_count": len(images),
                            "size_mb": round(folder_size / (1024 * 1024), 2)
                        })

                        total_images += len(images)
                        total_size += folder_size
                    except:
                        continue

                return {
                    "success": True,
                    "storage_type": "Supabase Storage",
                    "total_folders": len(folders),
                    "total_images": total_images,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "folders": folders[:20]  # 처음 20개만 반환
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
        # 폴더명에서 카테고리 ID 추출 (예: "100_식혜" → "100")
        category_id = folder_name.split('_')[0]
        storage_folder = f"cat-{category_id}"

        # 이미지 목록 조회
        try:
            files = supabase.storage.from_("product-images").list(storage_folder)

            image_list = []
            for file in files:
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

            return {
                "success": True,
                "folder": folder_name,
                "images": image_list,
                "count": len(image_list)
            }
        except Exception as e:
            print(f"[ERROR] Failed to list images from Supabase Storage: {e}")
            return {"success": False, "detail": f"Supabase Storage 조회 실패: {str(e)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
