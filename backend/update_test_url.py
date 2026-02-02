"""테스트 상품 URL 업데이트 및 정리"""
import sys
sys.path.insert(0, '.')

from database.db_wrapper import get_db

def main():
    db = get_db()

    # ID 19의 URL을 실제 상품 URL로 업데이트
    with db.get_connection() as conn:
        conn.execute("""
            UPDATE order_items
            SET product_name = '씨제이 햇반 백미밥 210g X 24개',
                product_url = 'https://www.11st.co.kr/products/8953443214?service_id=estimatedn&utm_term=&utm_campaign=%B4%D9%B3%AA%BF%CDpc_%B0%A1%B0%DD%BA%F1%B1%B3%B1%E2%BA%BB&utm_source=%B4%D9%B3%AA%BF%CD_PC_PCS&utm_medium=%B0%A1%B0%DD%BA%F1%B1%B3'
            WHERE id = 19
        """)
        conn.commit()
    print("[OK] ID 19 상품 URL 업데이트 완료")

    # 대기 중인 상품 확인
    print("\n[INFO] 대기 중인 주문 상품:")
    items = db.get_pending_order_items()
    for item in items:
        print(f"  - ID: {item['id']} | {item['source']} | {item['product_name']}")
        print(f"    URL: {item['product_url'][:80]}...")

if __name__ == "__main__":
    main()
