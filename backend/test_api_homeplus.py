"""
홈플러스 API 엔드포인트 테스트
"""
import sys
import io
import requests
import json

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_homeplus_api():
    """홈플러스 URL 정보 추출 API 테스트"""

    url = 'http://localhost:8000/api/monitor/extract-url-info'
    test_url = 'https://mfront.homeplus.co.kr/item?itemNo=10000303142935&storeType=DS&utm_source=danawa&utm_medium=shopping&utm_campaign=shopping_price_item&affiliate=1000016-1771069055765-0'

    print('=' * 80)
    print('홈플러스 URL 정보 추출 API 테스트')
    print('=' * 80)
    print(f'\n테스트 URL: {test_url[:70]}...\n')

    data = {'product_url': test_url}

    try:
        response = requests.post(url, json=data, timeout=30)
        print(f'HTTP Status: {response.status_code}\n')

        result = response.json()

        print('=' * 80)
        print('API 응답 결과')
        print('=' * 80)

        if result.get('success'):
            print(f"\n✅ 성공: {result.get('success')}")
            print(f"📦 상품명: {result.get('product_name')}")
            print(f"💰 가격: {result.get('price')}원")
            print(f"💵 정가: {result.get('original_price')}원" if result.get('original_price') else "💵 정가: 없음")
            print(f"📊 재고 상태: {result.get('status')}")
            print(f"🏷️ 소스: {result.get('source')}")
            print(f"🖼️ 썸네일: {result.get('thumbnail')}")
            print(f"💬 메시지: {result.get('message')}")

            # 재고 상태 한글 변환
            status_kr = {
                'available': '✅ 구매 가능',
                'out_of_stock': '❌ 품절',
                'discontinued': '🚫 단종'
            }.get(result.get('status'), '❓ 알 수 없음')
            print(f"\n📌 상태 (한글): {status_kr}")

        else:
            print(f"\n❌ 실패")
            print(f"오류: {result.get('error')}")
            print(f"메시지: {result.get('message')}")

        print('\n' + '=' * 80)
        print('원본 JSON 응답')
        print('=' * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print('=' * 80)

        return result

    except requests.exceptions.ConnectionError:
        print('❌ 서버가 실행되지 않았습니다.')
        print('다음 명령으로 서버를 시작하세요: cd backend && python main.py')
        return None

    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_homeplus_api()
    sys.exit(0 if result and result.get('success') else 1)
