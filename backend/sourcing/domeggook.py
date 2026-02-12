"""
도매꾹 상품 정보 추출 스크래퍼

도매꾹 상품 페이지에서 상품명, 가격, 재고 상태, 썸네일 자동 추출
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import json
from logger import get_logger

logger = get_logger(__name__)


class DomeggookScraper:
    """도매꾹 상품 정보 추출 - requests 기반"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://domeggook.com',
        }

    def extract_product_info(self, product_url: str, use_selenium: bool = False) -> Dict:
        """
        도매꾹 상품 정보 추출

        Args:
            product_url: 도매꾹 상품 URL
                        예: https://domeggook.com/63109713
            use_selenium: 무시됨 (requests만 사용)

        Returns:
            {
                "success": bool,
                "product_name": str,
                "price": float,
                "original_price": float,
                "status": str,  # available, out_of_stock
                "thumbnail": str,
                "source": "domeggook",
                "error": str,
                "note": str  # 추가 정보
            }
        """
        return self._extract_with_requests(product_url)

    def _extract_with_requests(self, product_url: str) -> Dict:
        """
        requests로 상품 정보 추출
        """
        try:
            logger.info(f"도매꾹 상품 정보 추출 시작: {product_url}")

            response = requests.get(product_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.content, 'html.parser')

            # 1. 메타 태그에서 기본 정보 추출
            product_name = self._extract_from_meta(soup, 'og:title')
            thumbnail = self._extract_from_meta(soup, 'og:image')

            # [도매꾹] 접두사 제거
            if product_name and product_name.startswith('[도매꾹]'):
                product_name = product_name.replace('[도매꾹]', '').strip()

            # 2. 가격 추출
            price_info = self._extract_price(soup)

            # 3. 재고 상태 확인
            status = self._check_stock_status(soup)

            logger.info(f"도매꾹 상품 정보 추출 완료: {product_name}, 가격: {price_info.get('price')}")

            return {
                "success": True,
                "product_name": product_name,
                "price": price_info.get('price'),
                "original_price": price_info.get('original_price'),
                "status": status,
                "thumbnail": thumbnail,
                "source": "domeggook",
                "note": None
            }

        except Exception as e:
            logger.error(f"도매꾹 상품 정보 추출 실패: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": "domeggook",
                "note": "상품 정보를 수동으로 입력해주세요."
            }

    def _extract_from_meta(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """메타 태그에서 정보 추출"""
        meta = soup.find('meta', property=property_name)
        if meta:
            return meta.get('content', '').strip()
        return None

    def _extract_price(self, soup: BeautifulSoup) -> Dict:
        """
        가격 추출
        도매꾹은 'lDomeggookMainTopCateBnrPrice' 클래스를 사용
        여러 가격이 나올 수 있으므로 첫 번째 것을 메인 가격으로 사용
        """
        try:
            # lDomeggookMainTopCateBnrPrice 클래스 찾기
            price_elements = soup.find_all(class_='lDomeggookMainTopCateBnrPrice')

            if not price_elements:
                # 일반적인 price 클래스로 fallback
                price_elements = soup.find_all(class_=re.compile('price', re.I))

            prices = []
            for elem in price_elements:
                text = elem.get_text(strip=True)
                # 숫자 추출 (콤마 제거)
                numbers = re.findall(r'([\d,]+)', text)
                for num_str in numbers:
                    try:
                        price = int(num_str.replace(',', ''))
                        if price > 100:  # 100원 이상만 유효한 가격으로 간주
                            prices.append(price)
                    except ValueError:
                        continue

            if prices:
                # 첫 번째 가격을 메인 가격으로 사용
                main_price = prices[0]
                original_price = prices[1] if len(prices) > 1 else None

                return {
                    "price": float(main_price),
                    "original_price": float(original_price) if original_price else None
                }

            # JSON-LD에서 추출 시도
            return self._extract_from_json_ld(soup)

        except Exception as e:
            logger.warning(f"가격 추출 실패: {e}")
            return {"price": None, "original_price": None}

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Dict:
        """JSON-LD 스키마에서 가격 추출"""
        scripts = soup.find_all('script', type='application/ld+json')

        for script in scripts:
            try:
                data = json.loads(script.string)

                # Product 스키마 찾기
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    offers = data.get('offers', {})

                    price_text = offers.get('price')
                    if price_text:
                        try:
                            price = float(price_text)
                            return {"price": price, "original_price": None}
                        except ValueError:
                            pass

            except (json.JSONDecodeError, AttributeError):
                continue

        return {"price": None, "original_price": None}

    def _check_stock_status(self, soup: BeautifulSoup) -> str:
        """
        재고 상태 확인
        품절/일시품절 텍스트를 찾거나, 구매 버튼 상태 확인
        """
        text_lower = soup.get_text().lower()

        # 품절 키워드 확인
        if any(keyword in text_lower for keyword in ['품절', '일시품절', 'sold out', 'out of stock']):
            return "out_of_stock"

        # 기본값: 판매 가능
        return "available"


if __name__ == "__main__":
    import json as json_module

    # 테스트용
    scraper = DomeggookScraper()

    # 테스트 URL
    test_url = "https://domeggook.com/63109713?from=lstBiz"

    print("=== Domeggook Scraper Test ===")

    result = scraper.extract_product_info(test_url)

    # JSON으로 출력 (인코딩 문제 회피)
    print(json_module.dumps(result, ensure_ascii=False, indent=2))

    if result['success']:
        print(f"\nSuccess! Price: {result['price']} KRW")
        print(f"Status: {result['status']}")
