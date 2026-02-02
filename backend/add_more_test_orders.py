"""추가 테스트 주문 생성"""
import sys
sys.path.insert(0, '.')

from database.db_wrapper import get_db
import time

def main():
    db = get_db()
    timestamp = int(time.time())

    # SSG 테스트 주문 생성
    print("[INFO] SSG 테스트 주문 생성 중...")
    order_id_ssg = db.add_order(
        order_number=f"TEST-SSG-{timestamp}",
        market="coupang",
        customer_name="이영희",
        customer_phone="010-1111-2222",
        customer_address="서울시 강남구 역삼동 123-45",
        customer_zipcode="06234",
        total_amount=35000,
        payment_method="card"
    )
    print(f"[OK] SSG 테스트 주문 생성: ID={order_id_ssg}")

    # SSG 실제 상품 추가 (예시: 햇반)
    item_id_ssg = db.add_order_item(
        order_id=order_id_ssg,
        product_name="[SSG] CJ 햇반 백미밥 210g 24개",
        product_url="https://www.ssg.com/item/itemView.ssg?itemId=1000045619264",
        source="ssg",
        quantity=1,
        sourcing_price=28000,
        selling_price=35000
    )
    print(f"[OK] SSG 상품 추가: ID={item_id_ssg}")

    # 11번가 테스트 주문 생성 (추가)
    print("\n[INFO] 11번가 테스트 주문 생성 중...")
    order_id_11st_2 = db.add_order(
        order_number=f"TEST-11ST-{timestamp+1}",
        market="naver",
        customer_name="박민수",
        customer_phone="010-3333-4444",
        customer_address="경기도 성남시 분당구 정자동 100",
        customer_zipcode="13561",
        total_amount=45000,
        payment_method="card"
    )
    print(f"[OK] 11번가 테스트 주문 생성: ID={order_id_11st_2}")

    # 11번가 실제 상품 추가 (동일한 햇반)
    item_id_11st_2 = db.add_order_item(
        order_id=order_id_11st_2,
        product_name="씨제이 햇반 백미밥 210g X 24개",
        product_url="https://www.11st.co.kr/products/8953443214?service_id=estimatedn&utm_term=&utm_campaign=%B4%D9%B3%AA%BF%CDpc_%B0%A1%B0%DD%BA%F1%B1%B3%B1%E2%BA%BB&utm_source=%B4%D9%B3%AA%BF%CD_PC_PCS&utm_medium=%B0%A1%B0%DD%BA%F1%B1%B3",
        source="11st",
        quantity=1,
        sourcing_price=35000,
        selling_price=45000
    )
    print(f"[OK] 11번가 상품 추가: ID={item_id_11st_2}")

    print("\n[INFO] 대기 중인 주문 상품 (최신 3개):")
    items = db.get_pending_order_items()
    for item in items[-3:]:  # 마지막 3개만
        print(f"  - ID: {item['id']} | {item['source'].upper()} | {item['product_name']}")

if __name__ == "__main__":
    main()
