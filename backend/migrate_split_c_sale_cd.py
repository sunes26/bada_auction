"""
c_sale_cd를 채널별로 분리하는 마이그레이션

기존:
- c_sale_cd (단일 필드)

변경 후:
- c_sale_cd_gmk (지마켓/옥션용)
- c_sale_cd_smart (스마트스토어 등용)
"""
import sys
sys.path.insert(0, '.')

from database.db import Database


def migrate_split_c_sale_cd():
    """c_sale_cd를 채널별로 분리"""
    db = Database()
    conn = db.get_connection()

    try:
        # 1. 새 컬럼 추가
        print("1. 새 컬럼 추가 중...")

        try:
            conn.execute("ALTER TABLE selling_products ADD COLUMN c_sale_cd_gmk TEXT")
            print("   ✅ c_sale_cd_gmk 컬럼 추가 완료")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("   ℹ️  c_sale_cd_gmk 컬럼이 이미 존재합니다")
            else:
                raise

        try:
            conn.execute("ALTER TABLE selling_products ADD COLUMN c_sale_cd_smart TEXT")
            print("   ✅ c_sale_cd_smart 컬럼 추가 완료")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("   ℹ️  c_sale_cd_smart 컬럼이 이미 존재합니다")
            else:
                raise

        conn.commit()

        # 2. 기존 c_sale_cd 데이터 확인
        print("\n2. 기존 c_sale_cd 데이터 확인 중...")
        cursor = conn.execute("""
            SELECT id, product_name, c_sale_cd, playauto_product_no
            FROM selling_products
            WHERE c_sale_cd IS NOT NULL OR playauto_product_no IS NOT NULL
        """)

        products = cursor.fetchall()
        print(f"   📊 PlayAuto 등록된 상품: {len(products)}개")

        if products:
            print("\n3. 데이터 안내:")
            print("   ⚠️  기존 c_sale_cd는 수동으로 확인하여 분리해야 합니다.")
            print("   - PlayAuto 관리자 페이지에서 각 상품의 채널별 c_sale_cd 확인")
            print("   - 웹 관리자 페이지에서 상품 수정 → 각각 입력")
            print()

            for product in products[:5]:  # 처음 5개만 표시
                print(f"   상품 ID {product[0]}: {product[1]}")
                print(f"      현재 c_sale_cd: {product[2] or product[3]}")
                print()

        print("\n✅ 마이그레이션 완료!")
        print()
        print("다음 단계:")
        print("1. 서버 재시작")
        print("2. 웹 관리자 페이지에서 각 상품의 '수정' 버튼 클릭")
        print("3. PlayAuto 연동 정보에서 지마켓/옥션용, 스마트스토어용 코드 각각 입력")

    except Exception as e:
        conn.rollback()
        print(f"❌ 오류 발생: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== c_sale_cd 채널별 분리 마이그레이션 ===\n")

    confirm = input("마이그레이션을 시작하시겠습니까? (y/n): ")
    if confirm.lower() == 'y':
        migrate_split_c_sale_cd()
    else:
        print("취소되었습니다.")
