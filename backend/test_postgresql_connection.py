"""
PostgreSQL 연결 및 DatabaseWrapper 테스트
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

# Force PostgreSQL usage for this test
os.environ['USE_POSTGRESQL'] = 'true'

from database.db_wrapper import get_db_wrapper
from database.database_manager import get_database_manager


def test_connection():
    """Test PostgreSQL connection"""
    print("="*60)
    print("PostgreSQL Connection Test")
    print("="*60)

    # Test 1: Database Manager Connection
    print("\n[Test 1] Database Manager Connection")
    try:
        db_manager = get_database_manager()
        if db_manager.test_connection():
            print("[OK] Connection successful!")
            print(f"  Database: {'PostgreSQL' if db_manager.is_postgresql else 'SQLite'}")
            print(f"  URL: {db_manager.database_url[:50]}...")
        else:
            print("[X] Connection failed!")
            return False
    except Exception as e:
        print(f"[X] Connection error: {e}")
        return False

    # Test 2: DatabaseWrapper Basic Operations
    print("\n[Test 2] DatabaseWrapper Operations")
    try:
        db = get_db_wrapper()
        print("[OK] DatabaseWrapper initialized")

        # Test 2.1: Get Categories
        print("\n[Test 2.1] Get Categories")
        categories = db.get_all_categories()
        print(f"[OK] Categories: {len(categories)} found")
        if categories:
            print(f"  First category: {categories[0].get('folder_name', 'N/A')}")

        # Test 2.2: Get Monitored Products
        print("\n[Test 2.2] Get Monitored Products")
        products = db.get_all_monitored_products(active_only=False)
        print(f"[OK] Monitored Products: {len(products)} found")
        if products:
            print(f"  First product: {products[0].get('product_name', 'N/A')}")

        # Test 2.3: Get Selling Products
        print("\n[Test 2.3] Get Selling Products")
        selling_products = db.get_selling_products(is_active=None, limit=10)
        print(f"[OK] Selling Products: {len(selling_products)} found")
        if selling_products:
            print(f"  First product: {selling_products[0].get('product_name', 'N/A')}")

        # Test 2.4: Get Playauto Settings
        print("\n[Test 2.4] Get Playauto Settings")
        settings = db.get_all_playauto_settings()
        print(f"[OK] Playauto Settings: {len(settings)} found")
        if settings:
            print(f"  First setting: {settings[0].get('setting_key', 'N/A')}")

        # Test 2.5: Get Dashboard Stats
        print("\n[Test 2.5] Get Dashboard Stats")
        stats = db.get_dashboard_stats()
        print(f"[OK] Dashboard Stats:")
        print(f"  Total Products: {stats.get('total_products', 0)}")
        print(f"  Active Products: {stats.get('active_products', 0)}")
        print(f"  Unread Notifications: {stats.get('unread_notifications', 0)}")

        return True

    except Exception as e:
        print(f"[X] DatabaseWrapper error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_integrity():
    """Test data integrity"""
    print("\n"+"="*60)
    print("Data Integrity Test")
    print("="*60)

    db = get_db_wrapper()

    # Compare counts
    print("\n[Data Counts]")
    categories = db.get_all_categories()
    monitored_products = db.get_all_monitored_products(active_only=False)
    selling_products = db.get_selling_products(is_active=None)
    settings = db.get_all_playauto_settings()

    print(f"  Categories: {len(categories)}")
    print(f"  Monitored Products: {len(monitored_products)}")
    print(f"  Selling Products: {len(selling_products)}")
    print(f"  Playauto Settings: {len(settings)}")

    # Expected counts from migration
    expected = {
        'categories': 138,
        'monitored_products': 4,
        'selling_products': 1,
        'settings': 11
    }

    print("\n[Comparison with Expected]")
    all_match = True
    if len(categories) == expected['categories']:
        print(f"[OK] Categories: {len(categories)} (expected: {expected['categories']})")
    else:
        print(f"[X] Categories: {len(categories)} (expected: {expected['categories']})")
        all_match = False

    if len(monitored_products) == expected['monitored_products']:
        print(f"[OK] Monitored Products: {len(monitored_products)} (expected: {expected['monitored_products']})")
    else:
        print(f"[X] Monitored Products: {len(monitored_products)} (expected: {expected['monitored_products']})")
        all_match = False

    if len(selling_products) == expected['selling_products']:
        print(f"[OK] Selling Products: {len(selling_products)} (expected: {expected['selling_products']})")
    else:
        print(f"[X] Selling Products: {len(selling_products)} (expected: {expected['selling_products']})")
        all_match = False

    if len(settings) == expected['settings']:
        print(f"[OK] Playauto Settings: {len(settings)} (expected: {expected['settings']})")
    else:
        print(f"[X] Playauto Settings: {len(settings)} (expected: {expected['settings']})")
        all_match = False

    return all_match


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PostgreSQL DatabaseWrapper Test Suite")
    print("="*60)

    # Check environment
    print("\n[Environment]")
    print(f"  DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
    print(f"  USE_POSTGRESQL: {os.getenv('USE_POSTGRESQL', 'Not set')}")

    # Run tests
    test1 = test_connection()
    test2 = test_data_integrity() if test1 else False

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"  Connection Test: {'[OK] PASS' if test1 else '[X] FAIL'}")
    print(f"  Data Integrity Test: {'[OK] PASS' if test2 else '[X] FAIL'}")

    if test1 and test2:
        print("\n[OK] All tests passed! PostgreSQL connection is ready.")
        print("\nNext steps:")
        print("  1. Set USE_POSTGRESQL=true in .env.local")
        print("  2. Restart backend server")
        print("  3. Test APIs via frontend or Postman")
    else:
        print("\n[ERROR] Some tests failed. Please check the errors above.")

    return test1 and test2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
