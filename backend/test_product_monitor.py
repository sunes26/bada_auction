"""
ProductMonitor 홈플러스/G마켓 통합 테스트
"""
import sys
import io

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from monitor.product_monitor import ProductMonitor


def test_homeplus_monitor():
    """홈플러스 일반몰 모니터링 테스트"""
    print('=' * 80)
    print('홈플러스 일반몰 ProductMonitor 테스트')
    print('=' * 80)

    monitor = ProductMonitor()
    test_url = "https://mfront.homeplus.co.kr/item?itemNo=10000303142935&storeType=DS"

    print(f'\n테스트 URL: {test_url}\n')

    result = monitor.check_product_status(test_url, source='homeplus')

    print('\n📊 모니터링 결과:')
    print('-' * 80)
    print(f"상태: {result.get('status')}")
    print(f"가격: {result.get('price')}원" if result.get('price') else "가격: 없음")
    print(f"정가: {result.get('original_price')}원" if result.get('original_price') else "정가: 없음")
    print(f"상세: {result.get('details')}")
    print('-' * 80)

    # 상태 확인
    status_emoji = {
        'available': '✅',
        'out_of_stock': '❌',
        'discontinued': '🚫',
        'error': '⚠️'
    }.get(result.get('status'), '❓')

    print(f"\n{status_emoji} 최종 상태: {result.get('status')}")
    print('=' * 80)

    return result


def test_gmarket_monitor():
    """G마켓 모니터링 테스트"""
    print('\n' * 2)
    print('=' * 80)
    print('G마켓 ProductMonitor 테스트')
    print('=' * 80)

    monitor = ProductMonitor()
    # 실제 G마켓 상품 URL (예시)
    test_url = "http://item.gmarket.co.kr/Item?goodscode=3273726852"

    print(f'\n테스트 URL: {test_url}\n')

    result = monitor.check_product_status(test_url, source='gmarket')

    print('\n📊 모니터링 결과:')
    print('-' * 80)
    print(f"상태: {result.get('status')}")
    print(f"가격: {result.get('price')}원" if result.get('price') else "가격: 없음")
    print(f"정가: {result.get('original_price')}원" if result.get('original_price') else "정가: 없음")
    print(f"상세: {result.get('details')}")
    print('-' * 80)

    # 상태 확인
    status_emoji = {
        'available': '✅',
        'out_of_stock': '❌',
        'discontinued': '🚫',
        'error': '⚠️'
    }.get(result.get('status'), '❓')

    print(f"\n{status_emoji} 최종 상태: {result.get('status')}")
    print('=' * 80)

    return result


if __name__ == "__main__":
    print('\n🧪 ProductMonitor 통합 테스트 시작\n')

    # 홈플러스 테스트
    homeplus_result = test_homeplus_monitor()

    # G마켓 테스트
    gmarket_result = test_gmarket_monitor()

    print('\n' * 2)
    print('=' * 80)
    print('테스트 요약')
    print('=' * 80)
    print(f"홈플러스: {homeplus_result.get('status')} - {homeplus_result.get('details')}")
    print(f"G마켓: {gmarket_result.get('status')} - {gmarket_result.get('details')}")
    print('=' * 80)

    # 성공 여부
    success = (
        homeplus_result.get('status') != 'error' and
        gmarket_result.get('status') != 'error'
    )

    sys.exit(0 if success else 1)
