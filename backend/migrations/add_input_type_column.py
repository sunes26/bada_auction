"""
마이그레이션: my_selling_products 테이블에 input_type 컬럼 추가
날짜: 2026-02-12
설명: 자동추출/수동입력 구분을 위한 input_type 컬럼 추가
"""

from database.database_manager import get_database_manager

def migrate():
    """마이그레이션 실행"""
    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    print("마이그레이션 시작: input_type 컬럼 추가")

    try:
        # 1. 컬럼 존재 여부 확인
        if db_manager.is_sqlite:
            cursor.execute("PRAGMA table_info(my_selling_products)")
            columns = [row[1] for row in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'my_selling_products'
            """)
            columns = [row[0] for row in cursor.fetchall()]

        if 'input_type' in columns:
            print("[OK] input_type column already exists. Skipping.")
            conn.close()
            return

        # 2. 컬럼 추가
        if db_manager.is_sqlite:
            cursor.execute("""
                ALTER TABLE my_selling_products
                ADD COLUMN input_type TEXT DEFAULT 'auto' NOT NULL
            """)
        else:
            cursor.execute("""
                ALTER TABLE my_selling_products
                ADD COLUMN input_type TEXT DEFAULT 'auto' NOT NULL
            """)

        conn.commit()
        print("[OK] input_type column added successfully")

        # 3. 기존 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM my_selling_products")
        count = cursor.fetchone()[0]
        print(f"[OK] {count} existing products set to 'auto'")

        conn.close()
        print("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"[ERROR] Migration failed: {e}")
        raise

def rollback():
    """마이그레이션 롤백"""
    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    print("롤백 시작: input_type 컬럼 제거")

    try:
        if db_manager.is_sqlite:
            print("[WARN] SQLite does not support dropping columns.")
            print("       You need to recreate the table manually.")
        else:
            cursor.execute("""
                ALTER TABLE my_selling_products
                DROP COLUMN IF EXISTS input_type
            """)
            conn.commit()
            print("[OK] input_type column removed successfully")

        conn.close()

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"[ERROR] Rollback failed: {e}")
        raise

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
