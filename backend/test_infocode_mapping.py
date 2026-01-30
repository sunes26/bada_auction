"""
카테고리별 infoCode 매핑 테스트
"""
import sqlite3
import sys
sys.path.append('.')

from playauto.product_registration import get_infocode_for_category, build_product_data_from_db


def test_infocode_mapping():
    """infoCode 조회 테스트"""
    print("=" * 60)
    print("infoCode 매핑 테스트")
    print("=" * 60)

    # 테스트 케이스
    test_categories = [
        "간편식 > 밥류 > 즉석밥 > 흰밥",
        "음료 > 전통음료 > 식혜 > 식혜",
        "뷰티 > 스킨케어 > 로션 > 로션",
        "건강기능식품 > 비타민 > 멀티비타민 > 멀티비타민",
        "화장품,생활용품 > 화장품 > 립스틱 > 립스틱",
        "우유/두유 > 우유 > 흰우유 > 흰우유",
        "알 수 없는 카테고리",
        None,
        ""
    ]

    for category in test_categories:
        info_code = get_infocode_for_category(category)
        print(f"카테고리: {category}")
        print(f"  → infoCode: {info_code}")
        print()


def test_build_product_data():
    """build_product_data_from_db 함수 테스트"""
    print("=" * 60)
    print("build_product_data_from_db 함수 테스트")
    print("=" * 60)

    # DB에서 실제 상품 데이터 가져오기
    conn = sqlite3.connect('monitoring.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM my_selling_products LIMIT 1')
    product_row = cursor.fetchone()

    if not product_row:
        print("테스트할 상품 데이터가 없습니다.")
        conn.close()
        return

    product = dict(product_row)
    conn.close()

    print(f"상품명: {product.get('product_name')}")
    print(f"카테고리: {product.get('category')}")
    print()

    # site_list 예시
    site_list = [
        {
            "shop_cd": "10",  # 스마트스토어
            "shop_id": "test_shop",
            "template_no": 1
        }
    ]

    # 변환
    playauto_data = build_product_data_from_db(product, site_list)

    print("변환된 플레이오토 데이터:")
    print(f"  상품명: {playauto_data.get('shop_sale_name')}")
    print(f"  판매가: {playauto_data.get('sale_price')}")
    print(f"  prod_info:")
    for prod_info in playauto_data.get('prod_info', []):
        print(f"    - infoCode: {prod_info.get('infoCode')}")
        print(f"    - is_desc_referred: {prod_info.get('is_desc_referred')}")
        print(f"    - infoDetail: {prod_info.get('infoDetail')}")


if __name__ == "__main__":
    test_infocode_mapping()
    print()
    test_build_product_data()
