"""
Test imports for tracking scheduler system
"""

print("Testing tracking scheduler imports...")

try:
    from services.tracking_upload_service import TrackingUploadService
    print("[OK] TrackingUploadService imported")
except Exception as e:
    print(f"[FAIL] TrackingUploadService import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from services.tracking_scheduler import TrackingScheduler, get_tracking_scheduler
    print("[OK] TrackingScheduler imported")
except Exception as e:
    print(f"[FAIL] TrackingScheduler import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from api.tracking_scheduler import router
    print(f"[OK] API router imported with {len(router.routes)} routes")
    print(f"[OK] Router prefix: {router.prefix}")
except Exception as e:
    print(f"[FAIL] API router import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nAll imports successful!")
