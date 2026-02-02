"""실제 11번가 상품으로 테스트 주문 추가"""
import sys
sys.path.insert(0, '.')

from database.db_wrapper import get_db
import time

def main():
    db = get_db()

    timestamp = int(time.time())

    # 11번가 실제 상품 주문 생성
    order_id = db.add_order(
        order_number=f"TEST-11ST-REAL-{timestamp}",
        market="coupang",
        customer_name="김철수",
        customer_phone="010-9876-5432",
        customer_address="서울시 서초구 서초대로 200",
        customer_zipcode="06590",
        total_amount=18000,
        payment_method="card"
    )
    print(f"[OK] 테스트 주문 생성: ID={order_id}")

    # 11번가 실제 상품 추가 (씨제이 햇반)
    item_id = db.add_order_item(
        order_id=order_id,
        product_name="씨제이 햇반 백미밥 210g X 24개",
        product_url="https://www.11st.co.kr/products/8953443214?service_id=estimatedn&utm_term=&utm_campaign=%B4%D9%B3%AA%BF%CDpc_%B0%A1%B0%DD%BA%F1%B1%B3%B1%E2%BA%BB&utm_source=%B4%D9%B3%AA%BF%CD_PC_PCS&utm_medium=%B0%A1%B0%DD%BA%F1%B1%B3",
        source="11st",
        quantity=1,
        sourcing_price=35000,
        selling_price=45000
    )
    print(f"[OK] 11번가 실제 상품 추가: ID={item_id}")

    print("\n[INFO] 대기 중인 주문 상품:")
    items = db.get_pending_order_items()
    for item in items:
        print(f"  - ID: {item['id']} | {item['source']} | {item['product_name']}")

if __name__ == "__main__":
    main()
