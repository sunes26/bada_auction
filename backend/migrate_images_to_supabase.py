"""
로컬 이미지를 Supabase Storage로 마이그레이션하는 스크립트

사용법:
    python backend/migrate_images_to_supabase.py

설명:
    - supabase-images/ 디렉토리의 모든 이미지를 Supabase Storage로 업로드
    - 진행 상황 표시
    - 업로드 실패 시 에러 로그 저장
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple
import time
from urllib.parse import quote

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from dotenv import load_dotenv

# 환경 변수 로드 - 프로젝트 루트의 .env.local 파일 우선
env_local = project_root / ".env.local"
env_backend = project_root / "backend" / ".env"

if env_local.exists():
    load_dotenv(env_local)
    print(f"[OK] Loaded environment from: {env_local}")
elif env_backend.exists():
    load_dotenv(env_backend)
    print(f"[OK] Loaded environment from: {env_backend}")
else:
    print("[WARN] No .env file found")

# Supabase Storage import (환경 변수 로드 후)
from utils.supabase_storage import upload_image, ensure_bucket_exists, supabase

# 이미지 디렉토리
IMAGES_DIR = project_root / "supabase-images"
ERROR_LOG = project_root / "backend" / "migration_errors.log"


def get_all_images() -> List[Tuple[Path, str]]:
    """
    모든 이미지 파일 경로와 Storage 경로 반환

    Returns:
        [(로컬 파일 경로, Storage 저장 경로), ...]
    """
    if not IMAGES_DIR.exists():
        print(f"[ERROR] Images directory not found: {IMAGES_DIR}")
        return []

    images = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    # 모든 폴더 순회
    for folder in IMAGES_DIR.iterdir():
        if not folder.is_dir():
            continue

        folder_name = folder.name  # 예: "1_흰밥"

        # 폴더 내 모든 이미지 파일
        for image_file in folder.iterdir():
            if image_file.suffix.lower() in image_extensions:
                # Storage 경로: 한글 제거, 카테고리 ID만 사용
                # "100_식혜" → "cat-100"
                # 폴더명에서 숫자(카테고리 ID) 추출
                category_id = folder_name.split('_')[0]  # "100_식혜" → "100"
                storage_folder = f"cat-{category_id}"

                # 파일명도 한글이 있을 수 있으므로 그대로 사용 (보통 영문/숫자)
                storage_path = f"{storage_folder}/{image_file.name}"
                images.append((image_file, storage_path))

    return images


def migrate_images():
    """이미지 마이그레이션 실행"""
    print("=" * 60)
    print("Supabase Storage 이미지 마이그레이션")
    print("=" * 60)

    # Supabase 클라이언트 확인
    if not supabase:
        print("[ERROR] Supabase client not initialized")
        print("환경 변수를 확인하세요:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_ROLE_KEY")
        return

    # 버킷 확인/생성
    print("\n[1/3] Supabase Storage 버킷 확인 중...")
    if not ensure_bucket_exists():
        print("[ERROR] Failed to ensure bucket exists")
        return

    # 이미지 목록 수집
    print("\n[2/3] 이미지 파일 스캔 중...")
    images = get_all_images()

    if not images:
        print("[WARN] No images found to migrate")
        return

    print(f"[OK] 총 {len(images)}개 이미지 발견")

    # 업로드 시작
    print("\n[3/3] 이미지 업로드 중...")
    print("-" * 60)

    success_count = 0
    fail_count = 0
    errors = []

    start_time = time.time()

    for idx, (file_path, storage_path) in enumerate(images, 1):
        # 진행 상황 표시
        percent = (idx / len(images)) * 100
        print(f"[{idx}/{len(images)}] ({percent:.1f}%) {storage_path}...", end=" ")

        # 업로드
        try:
            public_url = upload_image(file_path, storage_path)

            if public_url:
                print("OK")
                success_count += 1
            else:
                print("FAIL")
                fail_count += 1
                errors.append(f"{storage_path}: Upload failed")

        except Exception as e:
            print(f"FAIL - {e}")
            fail_count += 1
            errors.append(f"{storage_path}: {e}")

        # 진행 상황 요약 (매 50개마다)
        if idx % 50 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            remaining = (len(images) - idx) * avg_time
            print(f"    → 성공: {success_count}, 실패: {fail_count}, "
                  f"예상 남은 시간: {remaining:.0f}초")

    # 최종 결과
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("마이그레이션 완료")
    print("=" * 60)
    print(f"총 이미지: {len(images)}개")
    print(f"성공: {success_count}개 (✓)")
    print(f"실패: {fail_count}개 (✗)")
    print(f"소요 시간: {elapsed_time:.1f}초")
    print(f"평균 속도: {len(images) / elapsed_time:.1f}개/초")

    # 에러 로그 저장
    if errors:
        print(f"\n[WARN] {len(errors)}개 에러 발생 - 로그 저장 중...")
        with open(ERROR_LOG, 'w', encoding='utf-8') as f:
            f.write("이미지 마이그레이션 에러 로그\n")
            f.write("=" * 60 + "\n\n")
            for error in errors:
                f.write(f"{error}\n")
        print(f"[OK] 에러 로그 저장: {ERROR_LOG}")

    print("\n" + "=" * 60)

    # 다음 단계 안내
    if success_count > 0:
        print("\n다음 단계:")
        print("1. 프론트엔드 이미지 URL을 Supabase Storage URL로 변경")
        print("2. 백엔드 이미지 업로드 로직을 Supabase Storage 사용하도록 수정")
        print("3. 테스트 후 로컬 이미지 디렉토리 정리")


if __name__ == "__main__":
    try:
        migrate_images()
    except KeyboardInterrupt:
        print("\n\n[WARN] 마이그레이션 중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
