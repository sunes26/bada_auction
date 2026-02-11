"""
CJ더마켓 상품 상태 감지 테스트
"""
import sys
sys.path.insert(0, '.')

from monitor.product_monitor import ProductMonitor
from utils.flaresolverr import solve_cloudflare
from bs4 import BeautifulSoup

def test_cjthemarket_status(url: str):
    """CJ더마켓 URL의 상품 상태를 테스트"""
    print(f"\n{'='*60}")
    print(f"테스트 URL: {url}")
    print('='*60)

    # 1. FlareSolverr로 HTML 가져오기
    print("\n[1] FlareSolverr로 페이지 가져오는 중...")
    result = solve_cloudflare(url, max_timeout=60000)

    if not result or not result.get('html'):
        print("[ERROR] HTML을 가져올 수 없습니다.")
        return

    html = result.get('html', '')
    print(f"[OK] HTML 수신 완료 (길이: {len(html)})")

    # 2. BeautifulSoup으로 파싱
    soup = BeautifulSoup(html, 'html.parser')

    # 3. 페이지 텍스트에서 주요 키워드 확인
    page_text = soup.get_text()
    print("\n[2] 페이지 텍스트에서 키워드 검색...")

    keywords_to_check = [
        '구매할 수 있는 상품이 존재하지 않아요',
        '재입고 알림',
        '품절',
        '판매종료',
        '판매중지',
        '장바구니',
        '바로구매'
    ]

    for keyword in keywords_to_check:
        if keyword in page_text:
            print(f"  [FOUND] '{keyword}'")
        else:
            print(f"  [NOT FOUND] '{keyword}'")

    # 4. 버튼 요소 확인
    print("\n[3] 버튼 요소 확인...")

    restock_btn = soup.select_one('.btn__restock')
    if restock_btn:
        print(f"  [FOUND] .btn__restock: '{restock_btn.get_text(strip=True)}'")
    else:
        print("  [NOT FOUND] .btn__restock")

    default_btn = soup.select_one('.btn__default')
    if default_btn:
        print(f"  [FOUND] .btn__default: '{default_btn.get_text(strip=True)}'")
    else:
        print("  [NOT FOUND] .btn__default")

    btn_wrap = soup.select_one('.btn--wrap')
    if btn_wrap:
        print(f"  [FOUND] .btn--wrap 내용: '{btn_wrap.get_text(strip=True)[:100]}'")

    # 5. ProductMonitor로 상태 체크
    print("\n[4] ProductMonitor._check_cjthemarket_status() 호출...")
    monitor = ProductMonitor()
    status_result = monitor._check_cjthemarket_status(soup)

    print(f"\n{'='*60}")
    print("최종 결과:")
    print(f"  상태: {status_result.get('status')}")
    print(f"  가격: {status_result.get('price')}")
    print(f"  상세: {status_result.get('details')}")
    print('='*60)

    return status_result


if __name__ == "__main__":
    # 테스트할 URL들
    test_urls = [
        # 판매종료 상품 (사용자 제공)
        "https://www.cjthemarket.com/the/product/product-main?prdCd=40221140",
        # 이전에 테스트한 품절 상품
        "https://www.cjthemarket.com/the/product/product-main?prdCd=40221192",
    ]

    for url in test_urls:
        try:
            test_cjthemarket_status(url)
        except Exception as e:
            print(f"[ERROR] 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
