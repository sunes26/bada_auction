"""
이미지 다운로드 유틸리티
Supabase Storage를 사용하여 이미지 저장 (프로덕션 환경 호환)
"""
import os
import hashlib
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime

# Supabase Storage import
try:
    from utils.supabase_storage import upload_image_from_bytes, delete_image, get_public_url, supabase
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("[WARN] Supabase Storage 모듈을 찾을 수 없습니다. 로컬 저장소 사용")


def download_thumbnail(image_url: str, product_id: Optional[int] = None) -> Optional[str]:
    """
    썸네일 이미지를 다운로드하여 Supabase Storage에 저장 (프로덕션)
    또는 로컬 파일시스템에 저장 (개발 환경)

    Args:
        image_url: 다운로드할 이미지 URL
        product_id: 상품 ID (파일명에 사용)

    Returns:
        저장된 이미지의 URL (Supabase 공개 URL 또는 로컬 경로)
        실패 시 None
    """
    try:
        if not image_url:
            return None

        # 프로토콜이 없는 URL 처리 (// 로 시작하는 경우)
        if image_url.startswith('//'):
            image_url = 'https:' + image_url

        # URL 해시로 고유한 파일명 생성
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]

        # 확장자 추출 (기본값: jpg)
        ext = 'jpg'
        if '.' in image_url.split('?')[0]:
            ext = image_url.split('?')[0].split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                ext = 'jpg'

        # 파일명 생성
        if product_id:
            filename = f"product_{product_id}_{url_hash}.{ext}"
        else:
            filename = f"{url_hash}.{ext}"

        # Content-Type 매핑
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(ext, 'image/jpeg')

        # 이미지 다운로드
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': image_url.split('/')[0] + '//' + image_url.split('/')[2] if len(image_url.split('/')) > 2 else image_url
        }

        response = requests.get(image_url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()

        # 이미지 데이터를 메모리에 로드
        image_data = b''
        max_size = 10 * 1024 * 1024  # 최대 10MB
        current_size = 0

        for chunk in response.iter_content(chunk_size=8192):
            current_size += len(chunk)
            if current_size > max_size:
                print(f"[IMAGE ERROR] 이미지 크기가 너무 큽니다 (> 10MB): {image_url}")
                return None
            image_data += chunk

        # Supabase Storage에 업로드 (프로덕션 환경)
        if SUPABASE_AVAILABLE and supabase and os.getenv('ENVIRONMENT') == 'production':
            storage_path = f"thumbnails/{filename}"
            public_url = upload_image_from_bytes(image_data, storage_path, content_type)

            if public_url:
                print(f"[IMAGE] 썸네일 Supabase Storage 업로드 완료: {filename}")
                return public_url
            else:
                print(f"[IMAGE ERROR] Supabase Storage 업로드 실패, 로컬 저장소로 fallback")

        # 로컬 파일시스템에 저장 (개발 환경 또는 fallback)
        thumbnails_dir = Path(__file__).parent.parent / "static" / "thumbnails"

        try:
            thumbnails_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[IMAGE ERROR] 디렉토리 생성 실패: {e}")
            # 컨테이너 읽기 전용 환경에서는 실패
            # 이 경우 원본 URL 반환
            return image_url

        file_path = thumbnails_dir / filename

        # 이미 파일이 존재하면 기존 경로 반환
        if file_path.exists():
            return f"/static/thumbnails/{filename}"

        # 파일로 저장
        try:
            with open(file_path, 'wb') as f:
                f.write(image_data)

            print(f"[IMAGE] 썸네일 로컬 저장 완료: {filename}")
            return f"/static/thumbnails/{filename}"
        except Exception as e:
            print(f"[IMAGE ERROR] 로컬 파일 저장 실패: {e}")
            # 저장 실패시 원본 URL 반환
            return image_url

    except requests.exceptions.Timeout:
        print(f"[IMAGE ERROR] 썸네일 다운로드 타임아웃: {image_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[IMAGE ERROR] 썸네일 다운로드 실패: {str(e)}")
        return None
    except Exception as e:
        print(f"[IMAGE ERROR] 예상치 못한 오류: {str(e)}")
        return None


def delete_thumbnail(thumbnail_path: str) -> bool:
    """
    썸네일 이미지 파일 삭제 (Supabase Storage 또는 로컬)

    Args:
        thumbnail_path: 삭제할 이미지 경로
                       - Supabase URL: https://...supabase.co/storage/v1/object/public/...
                       - 로컬 경로: /static/thumbnails/abc123.jpg

    Returns:
        삭제 성공 여부
    """
    try:
        if not thumbnail_path:
            return False

        # Supabase Storage URL인 경우
        if SUPABASE_AVAILABLE and supabase and 'supabase.co' in thumbnail_path:
            # URL에서 storage path 추출
            # https://{project}.supabase.co/storage/v1/object/public/product-images/thumbnails/abc.jpg
            # -> thumbnails/abc.jpg
            if '/public/product-images/' in thumbnail_path:
                storage_path = thumbnail_path.split('/public/product-images/')[-1]
                return delete_image(storage_path)

        # 로컬 파일 경로인 경우
        if thumbnail_path.startswith('/static/thumbnails/'):
            filename = thumbnail_path.split('/')[-1]
            file_path = Path(__file__).parent.parent / "static" / "thumbnails" / filename

            if file_path.exists():
                file_path.unlink()
                print(f"[IMAGE] 썸네일 삭제 완료: {filename}")
                return True

        return False

    except Exception as e:
        print(f"[IMAGE ERROR] 썸네일 삭제 실패: {str(e)}")
        return False
