"""
c_sale_cd를 채널별로 분리하는 마이그레이션 (PostgreSQL용)
"""
import os
import sys

# 환경변수 설정
os.environ['USE_POSTGRESQL'] = 'true'
os.environ['DATABASE_URL'] = 'postgresql://postgres:jhs631200!!@db.spkeunlwkrqkdwunkufy.supabase.co:6543/postgres?sslmode=require'

sys.path.insert(0, '.')

from database.database_manager import get_database_manager
from sqlalchemy import text


def migrate_split_c_sale_cd_postgres():
    """PostgreSQL에서 c_sale_cd를 채널별로 분리"""

    print("=== PostgreSQL c_sale_cd 채널별 분리 마이그레이션 ===\n")

    db_manager = get_database_manager()

    print(f"연결 중: {db_manager.database_url[:50]}...")

    # 연결 테스트
    if not db_manager.test_connection():
        print("[ERROR] 데이터베이스 연결 실패")
        return

    try:
        with db_manager.get_session() as session:
            # 1. 새 컬럼 추가
            print("\n1. 새 컬럼 추가 중...")

            try:
                session.execute(text("""
                    ALTER TABLE my_selling_products
                    ADD COLUMN IF NOT EXISTS c_sale_cd_gmk TEXT
                """))
                print("   [OK] c_sale_cd_gmk 컬럼 추가 완료")
            except Exception as e:
                print(f"   [INFO] c_sale_cd_gmk: {e}")

            try:
                session.execute(text("""
                    ALTER TABLE my_selling_products
                    ADD COLUMN IF NOT EXISTS c_sale_cd_smart TEXT
                """))
                print("   [OK] c_sale_cd_smart 컬럼 추가 완료")
            except Exception as e:
                print(f"   [INFO] c_sale_cd_smart: {e}")

            session.commit()

            # 2. 기존 데이터 확인
            print("\n2. 기존 PlayAuto 상품 확인 중...")

            # playauto_product_no 컬럼이 있는지 확인
            result = session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'my_selling_products'
                AND column_name IN ('playauto_product_no', 'ol_shop_no')
            """))
            columns = [row[0] for row in result.fetchall()]

            if 'playauto_product_no' in columns or 'ol_shop_no' in columns:
                result = session.execute(text("""
                    SELECT COUNT(*)
                    FROM my_selling_products
                    WHERE playauto_product_no IS NOT NULL OR ol_shop_no IS NOT NULL
                """))
                count = result.scalar()
                print(f"   [INFO] PlayAuto 등록된 상품: {count}개")
            else:
                print("   [INFO] PlayAuto 관련 컬럼이 없습니다")

            # 3. 테이블 구조 확인
            print("\n3. my_selling_products 테이블 구조 확인...")
            result = session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'my_selling_products'
                AND column_name LIKE '%sale_cd%'
                ORDER BY ordinal_position
            """))

            columns = result.fetchall()
            if columns:
                print("   c_sale_cd 관련 컬럼:")
                for col_name, col_type in columns:
                    print(f"     - {col_name} ({col_type})")

            print("\n[OK] 마이그레이션 완료!")
            print("\n다음 단계:")
            print("1. Railway 서비스 재배포 (환경변수가 반영되도록)")
            print("2. 웹 관리자 페이지에서 각 상품 수정")
            print("3. PlayAuto 연동 정보에서 지마켓/옥션용, 스마트스토어용 코드 각각 입력")

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    migrate_split_c_sale_cd_postgres()
