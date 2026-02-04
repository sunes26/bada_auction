"""
모든 판매 상품 삭제 스크립트
"""
import sys
sys.path.insert(0, '.')

from database.db import Database


def delete_all_products():
    """모든 판매 상품 삭제"""
    db = Database()
    conn = db.get_connection()

    try:
        # 현재 상품 개수 확인
        cursor = conn.execute("SELECT COUNT(*) FROM my_selling_products")
        count = cursor.fetchone()[0]

        print(f"현재 판매 상품: {count}개")

        if count == 0:
            print("삭제할 상품이 없습니다.")
            return

        # 상품 목록 표시
        print("\n삭제될 상품 목록:")
        cursor = conn.execute("SELECT id, product_name, selling_price FROM my_selling_products")
        products = cursor.fetchall()
        for product in products:
            print(f"  ID {product[0]}: {product[1]} - {product[2]:,}원")

        print(f"\n총 {count}개의 상품을 삭제합니다.")
        confirm = input("정말 삭제하시겠습니까? (yes 입력): ")

        if confirm.lower() != 'yes':
            print("취소되었습니다.")
            return

        # 모든 상품 삭제
        conn.execute("DELETE FROM my_selling_products")
        conn.commit()

        print(f"\n[OK] {count}개의 상품이 삭제되었습니다!")

        # 확인
        cursor = conn.execute("SELECT COUNT(*) FROM my_selling_products")
        remaining = cursor.fetchone()[0]
        print(f"남은 상품: {remaining}개")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] 오류 발생: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== 모든 판매 상품 삭제 ===\n")
    delete_all_products()
