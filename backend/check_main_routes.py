"""
main.py의 실제 라우트 확인
"""
import sys
from pathlib import Path

# main.py를 import
sys.path.insert(0, str(Path(__file__).parent))

# main.py의 app import
from main import app

print("All registered routes in main.py:")
admin_count = 0
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', set())
        if '/admin' in route.path:
            print(f"  [OK] {route.path} - {methods}")
            admin_count += 1

print(f"\nTotal admin routes: {admin_count}")

if admin_count == 0:
    print("\n[ERROR] No admin routes found!")
    print("\nAll routes:")
    for route in app.routes:
        if hasattr(route, 'path') and '/api/' in route.path:
            methods = getattr(route, 'methods', set())
            print(f"  {route.path} - {methods}")
else:
    print("\n[SUCCESS] Admin routes are registered!")
