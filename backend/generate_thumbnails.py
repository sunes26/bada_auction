#!/usr/bin/env python3
"""
기존 이미지에 대한 썸네일 일괄 생성 스크립트

Supabase Storage의 모든 이미지에 대해 썸네일을 생성합니다.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
env_path = Path(__file__).parent.parent / '.env.local'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded environment from {env_path}")
else:
    print(f"[WARN] .env.local not found")

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from utils.supabase_storage import supabase, BUCKET_NAME, create_thumbnail, upload_image_from_bytes, get_public_url

def generate_all_thumbnails():
    """모든 이미지에 대해 썸네일 생성"""
    if not supabase:
        print("[ERROR] Supabase client not initialized")
        print("Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")
        return

    print(f"[INFO] Starting thumbnail generation for bucket: {BUCKET_NAME}")
    print()

    # 모든 폴더 조회
    try:
        folders = supabase.storage.from_(BUCKET_NAME).list()
        print(f"[INFO] Found {len(folders)} folders")
    except Exception as e:
        print(f"[ERROR] Failed to list folders: {e}")
        return

    total_processed = 0
    total_created = 0
    total_skipped = 0
    total_failed = 0

    for folder_obj in folders:
        folder_name = folder_obj.get('name')

        # 폴더만 처리
        if folder_obj.get('id') is not None:
            continue

        # thumbs 폴더는 건너뛰기
        if folder_name == 'thumbs' or folder_name.startswith('.'):
            continue

        print(f"\n[INFO] Processing folder: {folder_name}")

        # thumbs 폴더 존재 여부 확인
        thumbs_folder = f"{folder_name}/thumbs"

        # 폴더 내 모든 이미지 조회
        try:
            files = supabase.storage.from_(BUCKET_NAME).list(folder_name)
            image_files = [f for f in files if f.get('id') is not None and not f.get('name', '').startswith('thumbs')]

            print(f"  Found {len(image_files)} images")

            for file_obj in image_files:
                filename = file_obj.get('name')
                total_processed += 1

                # 원본 이미지 경로
                original_path = f"{folder_name}/{filename}"
                thumb_path = f"{folder_name}/thumbs/{filename}"

                # 썸네일이 이미 존재하는지 확인
                try:
                    existing_thumbs = supabase.storage.from_(BUCKET_NAME).list(f"{folder_name}/thumbs")
                    if any(t.get('name') == filename for t in existing_thumbs):
                        print(f"  ⏭️  Skipping {filename} (thumbnail exists)")
                        total_skipped += 1
                        continue
                except:
                    pass  # thumbs 폴더가 없을 수 있음

                # 원본 이미지 다운로드
                try:
                    response = supabase.storage.from_(BUCKET_NAME).download(original_path)
                    if not response:
                        print(f"  ❌ Failed to download {filename}")
                        total_failed += 1
                        continue

                    # 썸네일 생성
                    thumb_data = create_thumbnail(response)
                    if not thumb_data:
                        print(f"  ❌ Failed to create thumbnail for {filename}")
                        total_failed += 1
                        continue

                    # 썸네일 업로드
                    thumb_url = upload_image_from_bytes(thumb_data, thumb_path, "image/jpeg")
                    if thumb_url:
                        print(f"  ✅ Created thumbnail: {filename}")
                        total_created += 1
                    else:
                        print(f"  ❌ Failed to upload thumbnail for {filename}")
                        total_failed += 1

                except Exception as e:
                    print(f"  ❌ Error processing {filename}: {e}")
                    total_failed += 1

        except Exception as e:
            print(f"  [ERROR] Failed to process folder {folder_name}: {e}")

    # 최종 통계
    print("\n" + "="*60)
    print("THUMBNAIL GENERATION SUMMARY")
    print("="*60)
    print(f"Total images processed: {total_processed}")
    print(f"Thumbnails created:     {total_created}")
    print(f"Thumbnails skipped:     {total_skipped} (already exist)")
    print(f"Failed:                 {total_failed}")
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("BATCH THUMBNAIL GENERATOR")
    print("="*60)
    print()

    confirmation = input("This will generate thumbnails for ALL images in Supabase Storage.\nContinue? (yes/no): ")

    if confirmation.lower() in ['yes', 'y']:
        generate_all_thumbnails()
        print("\n[DONE] Thumbnail generation completed!")
    else:
        print("[CANCELLED] Operation cancelled by user")
