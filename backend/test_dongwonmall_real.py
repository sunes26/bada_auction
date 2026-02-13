"""
실제 동원몰 품절 상품 URL로 테스트
"""
import sys
sys.path.insert(0, '.')

from monitor.product_monitor import ProductMonitor
from bs4 import BeautifulSoup
import requests


def test_real_dongwonmall_product():
    """실제 동원몰 품절 상품 테스트"""
    url = "https://www.dongwonmall.com/product/detail.do?productId=003870958&cate_id="

    print("\n" + "="*60)
    print(f"실제 동원몰 상품 테스트")
    print(f"URL: {url}")
    print("="*60)

    # ProductMonitor 인스턴스 생성
    monitor = ProductMonitor()

    print("\n[1] 상품 상태 체크 시작...")

    # check_product_status 메서드 호출 (전체 플로우)
    result = monitor.check_product_status(
        product_url=url,
        source='dongwonmall'
    )

    print("\n" + "="*60)
    print("최종 결과:")
    print(f"  상태 (status): {result.get('status')}")
    print(f"  가격 (price): {result.get('price')}")
    print(f"  정가 (original_price): {result.get('original_price')}")
    print(f"  상세 (details): {result.get('details')}")
    print("="*60)

    # 검증
    if result.get('status') == 'out_of_stock':
        print("\n[OK] 품절 상품 정상 감지!")
        print(f"     상세: {result.get('details')}")

        # 재고 0으로 감지되었는지 확인
        if '재고 0' in result.get('details', ''):
            print("\n[OK] leftCnt 재고 체크가 정상 작동했습니다!")
            return True
        else:
            print("\n[INFO] 다른 방법으로 품절 감지됨")
            return True

    elif result.get('status') == 'available':
        print("\n[WARN] 판매중으로 감지됨 - 상품이 재입고되었을 수 있습니다")
        return False

    elif result.get('status') == 'error':
        print(f"\n[ERROR] 오류 발생: {result.get('details')}")
        return False

    else:
        print(f"\n[UNKNOWN] 알 수 없는 상태: {result.get('status')}")
        return False


if __name__ == "__main__":
    try:
        success = test_real_dongwonmall_product()

        if success:
            print("\n" + "="*60)
            print("[SUCCESS] 실제 동원몰 품절 상품 테스트 성공!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("[FAIL] 테스트 실패 또는 상품 상태 변경")
            print("="*60)
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
