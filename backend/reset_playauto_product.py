"""
특정 상품의 PlayAuto 등록 정보를 초기화하는 스크립트
PlayAuto에 존재하지 않는 상품의 정보를 DB에서 제거
"""
import sys
sys.path.insert(0, '.')

from database.db import Database

def reset_playauto_info(product_id: int):
    """상품의 PlayAuto 정보 초기화"""
    db = Database()
    conn = db.get_connection()

    try:
        # 현재 정보 조회
        cursor = conn.execute(
            "SELECT id, product_name, playauto_product_no, c_sale_cd FROM selling_products WHERE id = ?",
            (product_id,)
        )
        product = cursor.fetchone()

        if not product:
            print(f"❌ 상품 ID {product_id}를 찾을 수 없습니다.")
            return

        print(f"=== 상품 {product_id}번 현재 정보 ===")
        print(f"상품명: {product[1]}")
        print(f"playauto_product_no: {product[2]}")
        print(f"c_sale_cd: {product[3]}")
        print()

        # PlayAuto 정보 초기화
        conn.execute("""
            UPDATE selling_products
            SET playauto_product_no = NULL,
                c_sale_cd = NULL,
                ol_shop_no = NULL
            WHERE id = ?
        """, (product_id,))

        conn.commit()
        print(f"✅ 상품 {product_id}번의 PlayAuto 정보가 초기화되었습니다.")
        print("이제 관리자 페이지에서 '상품등록' 버튼을 눌러 PlayAuto에 다시 등록하세요.")

    except Exception as e:
        conn.rollback()
        print(f"❌ 오류 발생: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    # 상품 ID 13번 초기화
    product_id = int(input("초기화할 상품 ID를 입력하세요 (예: 13): "))

    confirm = input(f"상품 {product_id}번의 PlayAuto 등록 정보를 초기화하시겠습니까? (y/n): ")

    if confirm.lower() == 'y':
        reset_playauto_info(product_id)
    else:
        print("취소되었습니다.")
