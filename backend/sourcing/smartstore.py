"""
네이버 스마트스토어 상품 정보 추출 스크래퍼

네이버 스마트스토어 상품 페이지에서 상품명, 가격, 재고 상태, 썸네일 자동 추출
주의: 스마트스토어는 CAPTCHA로 자동 접근을 차단합니다. requests 기반으로만 동작합니다.
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import json
from logger import get_logger

logger = get_logger(__name__)


class SmartstoreScraper:
    """네이버 스마트스토어 상품 정보 추출 - requests 기반"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://shopping.naver.com',
        }

    def extract_product_info(self, product_url: str, use_selenium: bool = False) -> Dict:
        """
        스마트스토어 상품 정보 추출

        Args:
            product_url: 스마트스토어 상품 URL
                        예: https://smartstore.naver.com/store/products/1234567890
            use_selenium: 무시됨 (Selenium 제거됨)

        Returns:
            {
                "success": bool,
                "product_name": str,
                "price": float,
                "original_price": float,
                "status": str,  # available, out_of_stock
                "thumbnail": str,
                "source": "smartstore",
                "error": str,
                "note": str  # 추가 정보
            }
        """
        return self._extract_with_requests(product_url)

    def _extract_with_requests(self, product_url: str) -> Dict:
        """
        requests로 기본 정보 추출 (제한적)

        스마트스토어는 JavaScript 렌더링이 많아 완전한 정보 추출 불가능
        CAPTCHA로 자동 접근이 차단될 수 있음
        """
        try:
            logger.info(f"스마트스토어 상품 정보 추출 시작 (requests): {product_url}")

            response = requests.get(product_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # CAPTCHA 페이지 확인
            if 'captcha' in response.text.lower() or 'ncpt.naver.com' in response.text:
                logger.warning("스마트스토어 CAPTCHA 감지")
                return {
                    "success": False,
                    "error": "CAPTCHA 감지됨",
                    "source": "smartstore",
                    "note": "네이버가 자동 접근을 차단했습니다. 상품 정보를 수동으로 입력해주세요."
                }

            # 1. 메타 태그에서 기본 정보 추출 (og 태그)
            product_name = self._extract_from_meta(soup, 'og:title')
            thumbnail = self._extract_from_meta(soup, 'og:image')
            description = self._extract_from_meta(soup, 'og:description')

            # 2. JSON-LD 스키마에서 가격 추출 시도
            price_info = self._extract_from_json_ld(soup)

            # 3. 재고 상태는 동적 로딩으로 추출 어려움
            status = "unknown"

            logger.info(f"스마트스토어 기본 정보 추출: {product_name}")

            return {
                "success": True,
                "product_name": product_name,
                "price": price_info.get('price'),
                "original_price": price_info.get('original_price'),
                "status": status,
                "thumbnail": thumbnail,
                "source": "smartstore",
                "note": "동적 로딩으로 일부 정보만 추출 가능. 완전한 정보는 수동 입력 필요."
            }

        except Exception as e:
            logger.error(f"스마트스토어 상품 정보 추출 실패 (requests): {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": "smartstore",
                "note": "상품 정보를 수동으로 입력해주세요."
            }

    def _extract_from_meta(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """메타 태그에서 정보 추출"""
        meta = soup.find('meta', property=property_name)
        if meta:
            return meta.get('content', '').strip()
        return None

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


if __name__ == "__main__":
    # 테스트용
    scraper = SmartstoreScraper()

    # 테스트 URL (실제 스마트스토어 상품 URL로 교체)
    test_url = "https://smartstore.naver.com/your-store/products/1234567890"

    print("스마트스토어 스크래퍼 테스트")
    print("=" * 50)

    result = scraper.extract_product_info(test_url)
    print(f"결과: {result}")
