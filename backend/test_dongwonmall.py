"""
동원몰 상품 상태 감지 테스트
"""
import sys
sys.path.insert(0, '.')

from monitor.product_monitor import ProductMonitor
from utils.flaresolverr import solve_cloudflare
from bs4 import BeautifulSoup


def test_dongwonmall_status(url: str):
    """동원몰 URL의 상품 상태를 테스트"""
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

    # 3. 주요 요소 확인
    print("\n[2] 주요 요소 확인...")

    # leftCnt 확인
    stock_input = soup.find('input', id='leftCnt')
    if stock_input:
        print(f"  [FOUND] leftCnt: value='{stock_input.get('value')}'")
    else:
        print("  [NOT FOUND] leftCnt")

    # PB_COM_CD 확인
    status_input = soup.find('input', id='PB_COM_CD')
    if status_input:
        print(f"  [FOUND] PB_COM_CD: value='{status_input.get('value')}'")
    else:
        print("  [NOT FOUND] PB_COM_CD")

    # 구매 버튼 확인
    buy_buttons = soup.select('.btn-buy, .btn_buy, .cart-btn, button')
    print(f"  [INFO] 총 {len(buy_buttons)}개의 버튼 발견")
    for i, btn in enumerate(buy_buttons[:5]):  # 상위 5개만 출력
        btn_text = btn.get_text(strip=True)
        if btn_text:
            print(f"    버튼 {i+1}: '{btn_text[:50]}'")

    # JavaScript sold_out 변수 확인
    scripts = soup.find_all('script', string=lambda t: t and 'sold_out' in t)
    if scripts:
        print(f"  [FOUND] sold_out 변수가 있는 script 태그 {len(scripts)}개")
        for script in scripts:
            if "sold_out = 'out of stock'" in (script.string or ''):
                print("    → sold_out = 'out of stock' 발견")
    else:
        print("  [NOT FOUND] sold_out 변수")

    # 4. ProductMonitor로 상태 체크
    print("\n[3] ProductMonitor._check_dongwonmall_status() 호출...")
    monitor = ProductMonitor()
    status_result = monitor._check_dongwonmall_status(soup)

    print(f"\n{'='*60}")
    print("최종 결과:")
    print(f"  상태: {status_result.get('status')}")
    print(f"  가격: {status_result.get('price')}")
    print(f"  정가: {status_result.get('original_price')}")
    print(f"  상세: {status_result.get('details')}")
    print('='*60)

    return status_result


if __name__ == "__main__":
    # 테스트할 URL
    test_urls = [
        # 품절 상품 (사용자 제공)
        "https://www.dongwonmall.com/product/detail.do?productId=003870958&cate_id=",
    ]

    for url in test_urls:
        try:
            result = test_dongwonmall_status(url)

            # 예상 결과 검증
            if '003870958' in url:
                # 품절 상품이어야 함
                assert result.get('status') == 'out_of_stock', \
                    f"품절 상품이 {result.get('status')}로 감지됨"
                print("\n✅ 테스트 통과: 품절 상품 정상 감지")

        except AssertionError as e:
            print(f"\n❌ 테스트 실패: {e}")
        except Exception as e:
            print(f"\n❌ 테스트 오류: {e}")
            import traceback
            traceback.print_exc()
