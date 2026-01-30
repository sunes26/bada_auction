"""
이미지 다운로드 유틸리티
"""
import os
import hashlib
import requests
from pathlib import Path
from typing import Optional


def download_thumbnail(image_url: str, product_id: Optional[int] = None) -> Optional[str]:
    """
    썸네일 이미지를 다운로드하여 저장

    Args:
        image_url: 다운로드할 이미지 URL
        product_id: 상품 ID (파일명에 사용)

    Returns:
        저장된 이미지의 상대 경로 (예: /static/thumbnails/abc123.jpg)
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

        # 저장 경로
        thumbnails_dir = Path(__file__).parent.parent / "static" / "thumbnails"
        thumbnails_dir.mkdir(parents=True, exist_ok=True)

        file_path = thumbnails_dir / filename

        # 이미 파일이 존재하면 기존 경로 반환
        if file_path.exists():
            return f"/static/thumbnails/{filename}"

        # 이미지 다운로드
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': image_url.split('/')[0] + '//' + image_url.split('/')[2]
        }

        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()

        # 파일로 저장
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[IMAGE] 썸네일 다운로드 완료: {filename}")
        return f"/static/thumbnails/{filename}"

    except Exception as e:
        print(f"[IMAGE ERROR] 썸네일 다운로드 실패: {str(e)}")
        return None


def delete_thumbnail(thumbnail_path: str) -> bool:
    """
    썸네일 이미지 파일 삭제

    Args:
        thumbnail_path: 삭제할 이미지 경로 (예: /static/thumbnails/abc123.jpg)

    Returns:
        삭제 성공 여부
    """
    try:
        if not thumbnail_path or not thumbnail_path.startswith('/static/thumbnails/'):
            return False

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
