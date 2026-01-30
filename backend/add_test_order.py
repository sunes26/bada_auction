"""테스트용 주문 데이터 추가"""
import sys
sys.path.insert(0, '.')

from database.db import get_db

def main():
    db = get_db()

    # SSG 테스트 주문 생성
    import time
    timestamp = int(time.time())
    order_id = db.add_order(
        order_number=f"TEST-SSG-{timestamp}",
        market="coupang",
        customer_name="홍길동",
        customer_phone="010-1234-5678",
        customer_address="서울시 강남구 테헤란로 123",
        customer_zipcode="06142",
        total_amount=25000,
        payment_method="card"
    )
    print(f"[OK] 테스트 주문 생성 완료: ID={order_id}")

    # SSG 테스트 상품 추가
    item_id_1 = db.add_order_item(
        order_id=order_id,
        product_name="[SSG 테스트] 샘플 상품",
        product_url="https://www.ssg.com/item/itemView.ssg?itemId=1000000000000",
        source="ssg",
        quantity=1,
        sourcing_price=20000,
        selling_price=25000
    )
    print(f"[OK] SSG 테스트 상품 추가 완료: ID={item_id_1}")

    # 11번가 테스트 주문 생성
    order_id_2 = db.add_order(
        order_number=f"TEST-11ST-{timestamp}",
        market="coupang",
        customer_name="김철수",
        customer_phone="010-9876-5432",
        customer_address="서울시 서초구 서초대로 200",
        customer_zipcode="06590",
        total_amount=18000,
        payment_method="card"
    )
    print(f"[OK] 테스트 주문 생성 완료: ID={order_id_2}")

    # 11번가 테스트 상품 추가
    item_id_2 = db.add_order_item(
        order_id=order_id_2,
        product_name="[11번가 테스트] 샘플 상품",
        product_url="https://www.11st.co.kr/products/1234567890",
        source="11st",
        quantity=1,
        sourcing_price=15000,
        selling_price=18000
    )
    print(f"[OK] 11번가 테스트 상품 추가 완료: ID={item_id_2}")

    print("\n[INFO] 대기 중인 주문 상품:")
    items = db.get_pending_order_items()
    for item in items:
        print(f"  - ID: {item['id']} | {item['source']} | {item['product_name']}")

if __name__ == "__main__":
    main()
