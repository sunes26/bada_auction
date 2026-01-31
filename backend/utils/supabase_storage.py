"""
Supabase Storage 유틸리티
이미지 업로드 및 URL 생성을 위한 헬퍼 함수
"""
import os
from pathlib import Path
from typing import Optional, List
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 초기화
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# 버킷 이름
BUCKET_NAME = "product-images"

# 클라이언트 생성
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print(f"[OK] Supabase Storage client initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client: {e}")
else:
    print("[WARN] Supabase credentials not found - Storage features disabled")


def ensure_bucket_exists():
    """버킷이 존재하는지 확인하고 없으면 생성"""
    if not supabase:
        return False

    try:
        # 버킷 목록 조회
        buckets = supabase.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]

        if BUCKET_NAME not in bucket_names:
            # 버킷 생성 (public: True - 공개 접근 허용)
            supabase.storage.create_bucket(BUCKET_NAME, options={"public": True})
            print(f"[OK] Bucket '{BUCKET_NAME}' created")
        else:
            print(f"[OK] Bucket '{BUCKET_NAME}' already exists")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to ensure bucket exists: {e}")
        return False


def upload_image(file_path: Path, storage_path: str) -> Optional[str]:
    """
    이미지를 Supabase Storage에 업로드

    Args:
        file_path: 로컬 파일 경로
        storage_path: Storage 내 저장 경로 (예: "1_흰밥/image.jpg")

    Returns:
        업로드된 이미지의 공개 URL 또는 None
    """
    if not supabase:
        print("[ERROR] Supabase client not initialized")
        return None

    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return None

    try:
        # 파일 읽기
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # 업로드 (upsert: 덮어쓰기 허용)
        result = supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            file_data,
            file_options={"content-type": f"image/{file_path.suffix[1:]}", "upsert": "true"}
        )

        # 공개 URL 생성
        public_url = get_public_url(storage_path)

        return public_url
    except Exception as e:
        print(f"[ERROR] Failed to upload {storage_path}: {e}")
        return None


def upload_image_from_bytes(file_data: bytes, storage_path: str, content_type: str = "image/jpeg") -> Optional[str]:
    """
    바이트 데이터를 Supabase Storage에 업로드

    Args:
        file_data: 이미지 바이트 데이터
        storage_path: Storage 내 저장 경로
        content_type: MIME 타입

    Returns:
        업로드된 이미지의 공개 URL 또는 None
    """
    if not supabase:
        print("[ERROR] Supabase client not initialized")
        return None

    try:
        # 업로드
        result = supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            file_data,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        # 공개 URL 생성
        public_url = get_public_url(storage_path)

        return public_url
    except Exception as e:
        print(f"[ERROR] Failed to upload {storage_path}: {e}")
        return None


def get_public_url(storage_path: str) -> str:
    """
    Storage 경로에 대한 공개 URL 생성

    Args:
        storage_path: Storage 내 경로 (예: "1_흰밥/image.jpg")

    Returns:
        공개 URL
    """
    if not supabase or not SUPABASE_URL:
        return f"/supabase-images/{storage_path}"  # 로컬 fallback

    # Supabase Storage 공개 URL 형식
    # https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"


def list_images(folder: str = "") -> List[str]:
    """
    폴더의 이미지 목록 조회

    Args:
        folder: 폴더 경로 (예: "1_흰밥")

    Returns:
        이미지 파일 경로 목록
    """
    if not supabase:
        return []

    try:
        files = supabase.storage.from_(BUCKET_NAME).list(folder)
        return [f"{folder}/{file['name']}" if folder else file['name'] for file in files]
    except Exception as e:
        print(f"[ERROR] Failed to list images in {folder}: {e}")
        return []


def delete_image(storage_path: str) -> bool:
    """
    이미지 삭제

    Args:
        storage_path: Storage 내 경로

    Returns:
        삭제 성공 여부
    """
    if not supabase:
        return False

    try:
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        print(f"[OK] Deleted: {storage_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete {storage_path}: {e}")
        return False


# 버킷 자동 생성
if supabase:
    ensure_bucket_exists()
