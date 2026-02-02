"""
Migration script to add PlayAuto fields to my_selling_products table.

This script adds:
- sol_cate_no: INTEGER - PlayAuto category code
- playauto_product_no: TEXT - PlayAuto's c_sale_cd
- ol_shop_no: TEXT - Online shop number from registration

Supports both SQLite and PostgreSQL with idempotent operations.
"""

import sqlite3
import os
import sys
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


def column_exists(cursor, table_name: str, column_name: str, db_type: str = 'sqlite') -> bool:
    """Check if a column exists in a table."""
    if db_type == 'sqlite':
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    elif db_type == 'postgresql':
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        return cursor.fetchone() is not None
    return False


def get_columns_to_add(cursor, table_name: str, db_type: str) -> List[Tuple[str, str]]:
    """Get list of columns that need to be added."""
    columns = [
        ('sol_cate_no', 'INTEGER'),
        ('playauto_product_no', 'TEXT'),
        ('ol_shop_no', 'TEXT')
    ]

    columns_to_add = []
    for col_name, col_type in columns:
        if not column_exists(cursor, table_name, col_name, db_type):
            columns_to_add.append((col_name, col_type))

    return columns_to_add


def migrate_sqlite(db_path: str = None) -> bool:
    """Run migration on SQLite database."""
    if db_path is None:
        # Default SQLite path - monitoring.db in backend directory
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'monitoring.db')

    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        return False

    print(f"[INFO] Checking SQLite database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check which columns need to be added
        columns_to_add = get_columns_to_add(cursor, 'my_selling_products', 'sqlite')

        if not columns_to_add:
            print("[OK] All PlayAuto columns already exist in SQLite database")
            conn.close()
            return True

        print(f"[MIGRATION] Adding {len(columns_to_add)} column(s) to my_selling_products table...")

        # Add missing columns
        for col_name, col_type in columns_to_add:
            print(f"   Adding {col_name} ({col_type})...")
            cursor.execute(f"ALTER TABLE my_selling_products ADD COLUMN {col_name} {col_type}")

        conn.commit()
        print("[OK] SQLite migration completed successfully")

        # Verify columns were added
        columns_after = get_columns_to_add(cursor, 'my_selling_products', 'sqlite')
        if columns_after:
            print(f"[WARNING]  Warning: Some columns may not have been added: {columns_after}")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"[ERROR] SQLite migration error: {e}")
        return False


def migrate_postgresql(connection_string: str) -> bool:
    """Run migration on PostgreSQL database."""
    if not POSTGRES_AVAILABLE:
        print("[ERROR] psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False

    print(f"[INFO] Checking PostgreSQL database...")

    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        # Check which columns need to be added
        columns_to_add = get_columns_to_add(cursor, 'my_selling_products', 'postgresql')

        if not columns_to_add:
            print("[OK] All PlayAuto columns already exist in PostgreSQL database")
            conn.close()
            return True

        print(f"[MIGRATION] Adding {len(columns_to_add)} column(s) to my_selling_products table...")

        # Add missing columns
        for col_name, col_type in columns_to_add:
            print(f"   Adding {col_name} ({col_type})...")
            cursor.execute(f"ALTER TABLE my_selling_products ADD COLUMN {col_name} {col_type}")

        conn.commit()
        print("[OK] PostgreSQL migration completed successfully")

        # Verify columns were added
        columns_after = get_columns_to_add(cursor, 'my_selling_products', 'postgresql')
        if columns_after:
            print(f"[WARNING]  Warning: Some columns may not have been added: {columns_after}")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] PostgreSQL migration error: {e}")
        return False


def rollback_sqlite(db_path: str = None) -> bool:
    """Rollback SQLite migration by removing the columns."""
    print("[WARNING]  SQLite does not support DROP COLUMN in older versions.")
    print("    To rollback, you would need to:")
    print("    1. Create a new table without the columns")
    print("    2. Copy data from old table")
    print("    3. Drop old table and rename new table")
    print("    This is not implemented for safety. Please restore from backup if needed.")
    return False


def rollback_postgresql(connection_string: str) -> bool:
    """Rollback PostgreSQL migration by removing the columns."""
    if not POSTGRES_AVAILABLE:
        print("[ERROR] psycopg2 not installed")
        return False

    print("[WARNING]  Rolling back PostgreSQL migration...")

    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        columns = ['sol_cate_no', 'playauto_product_no', 'ol_shop_no']

        for col_name in columns:
            if column_exists(cursor, 'my_selling_products', col_name, 'postgresql'):
                print(f"   Removing {col_name}...")
                cursor.execute(f"ALTER TABLE my_selling_products DROP COLUMN {col_name}")

        conn.commit()
        print("[OK] PostgreSQL rollback completed successfully")
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] PostgreSQL rollback error: {e}")
        return False


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate PlayAuto fields to my_selling_products table')
    parser.add_argument('--db-type', choices=['sqlite', 'postgresql', 'both'], default='sqlite',
                      help='Database type to migrate (default: sqlite)')
    parser.add_argument('--sqlite-path', help='Path to SQLite database file')
    parser.add_argument('--pg-connection', help='PostgreSQL connection string')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')

    args = parser.parse_args()

    print("=" * 60)
    print("PlayAuto Fields Migration Script")
    print("=" * 60)

    if args.rollback:
        print("[WARNING]  ROLLBACK MODE - This will remove the PlayAuto columns!")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Rollback cancelled.")
            return

        if args.db_type in ['sqlite', 'both']:
            rollback_sqlite(args.sqlite_path)

        if args.db_type in ['postgresql', 'both'] and args.pg_connection:
            rollback_postgresql(args.pg_connection)

        return

    # Normal migration
    print("\nThis will add the following columns to my_selling_products:")
    print("   - sol_cate_no (INTEGER) - PlayAuto category code")
    print("   - playauto_product_no (TEXT) - PlayAuto's c_sale_cd")
    print("   - ol_shop_no (TEXT) - Online shop number\n")

    success = True

    if args.db_type in ['sqlite', 'both']:
        print("\n" + "=" * 60)
        if not migrate_sqlite(args.sqlite_path):
            success = False

    if args.db_type in ['postgresql', 'both']:
        if not args.pg_connection:
            print("\n[WARNING]  PostgreSQL migration skipped - no connection string provided")
            print("   Use --pg-connection flag to specify connection string")
        else:
            print("\n" + "=" * 60)
            if not migrate_postgresql(args.pg_connection):
                success = False

    print("\n" + "=" * 60)
    if success:
        print("[OK] Migration completed successfully!")
    else:
        print("[ERROR] Migration completed with errors - please check the output above")
    print("=" * 60)


if __name__ == "__main__":
    main()
