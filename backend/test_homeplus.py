"""
홈플러스 스크래퍼 테스트

사용자가 제공한 홈플러스 상품 URL에서 정보를 추출하여 확인
"""
import sys
import os
import io

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# backend 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sourcing.homeplus import HomeplusScraper


def test_homeplus_scraper():
    """홈플러스 스크래퍼 테스트"""

    # 사용자가 제공한 URL
    test_url = "https://mfront.homeplus.co.kr/item?itemNo=10000303142935&storeType=DS&utm_source=danawa&utm_medium=shopping&utm_campaign=shopping_price_item&affiliate=1000016-1771069055765-0"

    print("=" * 80)
    print("홈플러스 스크래퍼 테스트")
    print("=" * 80)
    print(f"\n테스트 URL: {test_url}\n")

    # 스크래퍼 인스턴스 생성
    scraper = HomeplusScraper()

    # 상품 정보 추출
    result = scraper.extract_product_info(test_url)

    # 결과 출력
    print("추출 결과:")
    print("-" * 80)

    if result.get('success'):
        print(f"✅ 성공: {result.get('success')}")
        print(f"📦 상품명: {result.get('product_name')}")
        print(f"💰 가격: {result.get('price')}원")
        print(f"💵 정가: {result.get('original_price')}원" if result.get('original_price') else "💵 정가: 없음")
        print(f"📊 재고 상태: {result.get('status')}")
        print(f"🏷️ 소스: {result.get('source')}")
        print(f"🖼️ 썸네일: {result.get('thumbnail')}")

        # 재고 상태 한글 변환
        status_kr = {
            'available': '구매 가능',
            'out_of_stock': '품절',
            'discontinued': '단종'
        }.get(result.get('status'), '알 수 없음')
        print(f"\n상태 (한글): {status_kr}")

    else:
        print(f"❌ 실패")
        print(f"오류: {result.get('error')}")

    print("=" * 80)

    return result


if __name__ == "__main__":
    result = test_homeplus_scraper()

    # 종료 코드 반환
    sys.exit(0 if result.get('success') else 1)
