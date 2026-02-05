"""
마켓 코드 동기화 기능 테스트
"""

import asyncio
from database.db_wrapper import get_db
from playauto.products import PlayautoProductAPI
from playauto.scheduler import sync_marketplace_codes_job


async def test_get_product_detail():
    """상품 상세 조회 테스트"""
    print("=" * 50)
    print("테스트 1: PlayAuto 상품 상세 조회")
    print("=" * 50)

    # 테스트할 ol_shop_no (실제 값으로 변경 필요)
    ol_shop_no = "12345678901234567890"

    api = PlayautoProductAPI()

    try:
        detail = await api.get_product_detail(ol_shop_no)
        print(f"\n[OK] 상품 상세 조회 성공:")
        print(f"  - c_sale_cd: {detail.get('c_sale_cd')}")
        print(f"  - ol_shop_no: {detail.get('ol_shop_no')}")
        print(f"  - shops: {len(detail.get('shops', []))}개")

        for shop in detail.get("shops", []):
            print(f"    * {shop.get('shop_name')} ({shop.get('shop_cd')}): {shop.get('shop_sale_no')}")

    except Exception as e:
        print(f"\n[ERROR] 상품 조회 실패: {e}")


def test_db_marketplace_codes():
    """DB 마켓 코드 관련 메서드 테스트"""
    print("\n" + "=" * 50)
    print("테스트 2: DB 마켓 코드 CRUD")
    print("=" * 50)

    db = get_db()

    # 테스트 데이터 생성
    product_id = 1  # 실제 존재하는 product_id로 변경 필요
    shop_cd = "A001"  # 옥션
    shop_sale_no = "TEST123456789"

    try:
        # 1. 저장
        print(f"\n[1] 마켓 코드 저장 테스트")
        code_id = db.upsert_marketplace_code(
            product_id=product_id,
            shop_cd=shop_cd,
            shop_sale_no=shop_sale_no
        )
        print(f"  -> 저장 성공: ID {code_id}")

        # 2. 조회 (상품별)
        print(f"\n[2] 상품별 마켓 코드 조회")
        codes = db.get_marketplace_codes_by_product(product_id)
        print(f"  -> {len(codes)}개 조회:")
        for code in codes:
            print(f"    * {code['shop_cd']}: {code['shop_sale_no']}")

        # 3. 조회 (마켓 코드로 상품 찾기)
        print(f"\n[3] 마켓 코드로 상품 조회 (주문 매칭)")
        product = db.get_product_by_marketplace_code(shop_cd, shop_sale_no)
        if product:
            print(f"  -> 매칭 성공: {product['product_name']} (ID: {product['id']})")
        else:
            print(f"  -> 매칭 실패: 상품 없음")

        # 4. 동기화 대상 조회
        print(f"\n[4] 동기화 대상 상품 조회")
        products = db.get_products_for_marketplace_sync(hours=24, limit=10)
        print(f"  -> {len(products)}개 상품:")
        for p in products[:5]:  # 최대 5개만 출력
            print(f"    * {p['product_name']} (ol_shop_no: {p.get('ol_shop_no')})")

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_sync_job():
    """마켓 코드 동기화 작업 테스트"""
    print("\n" + "=" * 50)
    print("테스트 3: 마켓 코드 동기화 작업 실행")
    print("=" * 50)

    try:
        await sync_marketplace_codes_job()
        print("\n[OK] 동기화 작업 완료")
    except Exception as e:
        print(f"\n[ERROR] 동기화 작업 실패: {e}")
        import traceback
        traceback.print_exc()


def test_order_matching():
    """주문 매칭 테스트"""
    print("\n" + "=" * 50)
    print("테스트 4: 주문-상품 매칭")
    print("=" * 50)

    db = get_db()

    # 테스트 주문 데이터 (실제 주문 형식)
    test_order = {
        "uniq": "TEST_ORDER_001",
        "shop_cd": "A001",  # 옥션
        "shop_sale_no": "TEST123456789",
        "shop_name": "옥션",
        "shop_ord_no": "ORD-20260205-001",
        "to_name": "홍길동",
        "ord_time": "2026-02-05 10:00:00",
        "pay_amt": 50000
    }

    try:
        # 주문 동기화 (매칭 포함)
        success = db.sync_playauto_order_to_local(test_order)

        if success:
            print(f"\n[OK] 주문 동기화 성공")
            print(f"  -> 자동 매칭 로그 확인")
        else:
            print(f"\n[ERROR] 주문 동기화 실패")

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 70)
    print("    마켓 코드 동기화 시스템 테스트")
    print("=" * 70)

    # 테스트 1: PlayAuto API 상품 상세 조회
    # await test_get_product_detail()

    # 테스트 2: DB 기능 테스트
    test_db_marketplace_codes()

    # 테스트 3: 동기화 작업 실행
    # await test_sync_job()

    # 테스트 4: 주문 매칭 테스트
    test_order_matching()

    print("\n" + "=" * 70)
    print("    테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
