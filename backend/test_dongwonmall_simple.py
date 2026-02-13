"""
동원몰 품절 감지 로직 간단 테스트 (FlareSolverr 불필요)
"""
import sys
sys.path.insert(0, '.')

from monitor.product_monitor import ProductMonitor
from bs4 import BeautifulSoup


def test_case_1_out_of_stock():
    """테스트 케이스 1: leftCnt=0 품절 상품"""
    print("\n" + "="*60)
    print("테스트 케이스 1: leftCnt=0 품절 상품")
    print("="*60)

    # 실제 동원몰 품절 상품 HTML 구조 재현
    html = """
    <html>
    <head>
        <title>동원 참치캔</title>
    </head>
    <body>
        <input id="leftCnt" value="0" />
        <input id="PB_COM_CD" value="01" />
        <input id="userPrice" value="19,710" />
        <button class="btn_cart_lg"> 품절</button>
        <script>
            var sold_out = 'out of stock';
        </script>
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'html.parser')
    monitor = ProductMonitor()
    result = monitor._check_dongwonmall_status(soup)

    print(f"결과 상태: {result.get('status')}")
    print(f"결과 가격: {result.get('price')}")
    print(f"결과 상세: {result.get('details')}")

    assert result.get('status') == 'out_of_stock', \
        f"Expected 'out_of_stock', got '{result.get('status')}'"
    assert result.get('details') == '일시품절 (재고 0)', \
        f"Expected '일시품절 (재고 0)', got '{result.get('details')}'"

    print("[OK] 테스트 통과: leftCnt=0 -> 품절 감지")


def test_case_2_in_stock():
    """테스트 케이스 2: leftCnt>0 판매중 상품"""
    print("\n" + "="*60)
    print("테스트 케이스 2: leftCnt>0 판매중 상품")
    print("="*60)

    html = """
    <html>
    <body>
        <input id="leftCnt" value="100" />
        <input id="PB_COM_CD" value="01" />
        <input id="userPrice" value="15,000" />
        <button class="btn_buy">구매하기</button>
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'html.parser')
    monitor = ProductMonitor()
    result = monitor._check_dongwonmall_status(soup)

    print(f"결과 상태: {result.get('status')}")
    print(f"결과 가격: {result.get('price')}")

    assert result.get('status') == 'available', \
        f"Expected 'available', got '{result.get('status')}'"

    print("[OK] 테스트 통과: leftCnt=100 -> 판매중 감지")


def test_case_3_button_text_soldout():
    """테스트 케이스 3: 버튼 텍스트에 '품절' (공백 포함)"""
    print("\n" + "="*60)
    print("테스트 케이스 3: 버튼 텍스트 '품절' (공백 처리)")
    print("="*60)

    html = """
    <html>
    <body>
        <input id="PB_COM_CD" value="01" />
        <input id="userPrice" value="19,710" />
        <button class="btn_cart_lg">  품절  </button>
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'html.parser')
    monitor = ProductMonitor()
    result = monitor._check_dongwonmall_status(soup)

    print(f"결과 상태: {result.get('status')}")

    assert result.get('status') == 'out_of_stock', \
        f"Expected 'out_of_stock', got '{result.get('status')}'"

    print("[OK] 테스트 통과: 버튼 텍스트 공백 처리 정상")


def test_case_4_pb_com_cd():
    """테스트 케이스 4: PB_COM_CD != '01' 품절"""
    print("\n" + "="*60)
    print("테스트 케이스 4: PB_COM_CD != '01'")
    print("="*60)

    html = """
    <html>
    <body>
        <input id="PB_COM_CD" value="03" />
        <input id="userPrice" value="19,710" />
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'html.parser')
    monitor = ProductMonitor()
    result = monitor._check_dongwonmall_status(soup)

    print(f"결과 상태: {result.get('status')}")

    assert result.get('status') == 'out_of_stock', \
        f"Expected 'out_of_stock', got '{result.get('status')}'"

    print("[OK] 테스트 통과: PB_COM_CD != '01' -> 품절 감지")


def test_case_5_javascript_soldout():
    """테스트 케이스 5: JavaScript sold_out 변수"""
    print("\n" + "="*60)
    print("테스트 케이스 5: JavaScript sold_out 변수")
    print("="*60)

    html = """
    <html>
    <body>
        <input id="PB_COM_CD" value="01" />
        <script>
            var sold_out = 'out of stock';
        </script>
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'html.parser')
    monitor = ProductMonitor()
    result = monitor._check_dongwonmall_status(soup)

    print(f"결과 상태: {result.get('status')}")

    assert result.get('status') == 'out_of_stock', \
        f"Expected 'out_of_stock', got '{result.get('status')}'"

    print("[OK] 테스트 통과: JavaScript sold_out 변수 감지")


def test_case_6_priority():
    """테스트 케이스 6: leftCnt가 최우선 (early return 확인)"""
    print("\n" + "="*60)
    print("테스트 케이스 6: leftCnt 우선순위 (재고 0이면 즉시 반환)")
    print("="*60)

    # leftCnt=0이면 PB_COM_CD='01'이어도 품절
    html = """
    <html>
    <body>
        <input id="leftCnt" value="0" />
        <input id="PB_COM_CD" value="01" />
        <input id="userPrice" value="19,710" />
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'html.parser')
    monitor = ProductMonitor()
    result = monitor._check_dongwonmall_status(soup)

    print(f"결과 상태: {result.get('status')}")
    print(f"결과 상세: {result.get('details')}")

    assert result.get('status') == 'out_of_stock', \
        f"Expected 'out_of_stock', got '{result.get('status')}'"
    assert result.get('details') == '일시품절 (재고 0)', \
        f"Expected '일시품절 (재고 0)', got '{result.get('details')}'"

    print("[OK] 테스트 통과: leftCnt 최우선 체크 정상")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("동원몰 품절 감지 로직 유닛 테스트")
    print("="*60)

    test_cases = [
        test_case_1_out_of_stock,
        test_case_2_in_stock,
        test_case_3_button_text_soldout,
        test_case_4_pb_com_cd,
        test_case_5_javascript_soldout,
        test_case_6_priority,
    ]

    passed = 0
    failed = 0

    for test_func in test_cases:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] 테스트 실패: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] 테스트 오류: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"테스트 결과: {passed}개 통과, {failed}개 실패")
    print("="*60)

    if failed == 0:
        print("\n[SUCCESS] 모든 테스트 통과!")
    else:
        print(f"\n[WARN]  {failed}개의 테스트가 실패했습니다.")
        sys.exit(1)
