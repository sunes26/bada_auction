"""
G마켓 상품 정보 추출 스크래퍼

G마켓 상품 페이지에서 상품명, 가격, 재고 상태, 썸네일 자동 추출
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
from logger import get_logger

logger = get_logger(__name__)


class GmarketScraper:
    """G마켓 상품 정보 추출"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def extract_product_info(self, product_url: str) -> Dict:
        """
        G마켓 상품 정보 추출

        Args:
            product_url: G마켓 상품 URL
                        예: http://item.gmarket.co.kr/Item?goodscode=1234567890

        Returns:
            {
                "success": bool,
                "product_name": str,
                "price": float,
                "original_price": float,  # 할인 전 가격
                "status": str,  # available, out_of_stock
                "thumbnail": str,
                "source": "gmarket",
                "error": str  # 실패 시
            }
        """
        try:
            logger.info(f"G마켓 상품 정보 추출 시작: {product_url}")

            # 페이지 가져오기
            response = requests.get(product_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. 상품명 추출
            product_name = self._extract_product_name(soup)

            # 2. 가격 추출
            price_info = self._extract_price(soup)

            # 3. 재고 상태 체크
            status = self._check_stock_status(soup)

            # 4. 썸네일 추출
            thumbnail_url = self._extract_thumbnail(soup)

            logger.info(f"G마켓 추출 성공: {product_name}, 가격: {price_info.get('price')}")

            return {
                "success": True,
                "product_name": product_name,
                "price": price_info.get('price'),
                "original_price": price_info.get('original_price'),
                "status": status,
                "thumbnail": thumbnail_url,
                "source": "gmarket"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"G마켓 페이지 요청 실패: {e}")
            return {
                "success": False,
                "error": f"페이지 요청 실패: {str(e)}",
                "source": "gmarket"
            }

        except Exception as e:
            logger.error(f"G마켓 상품 정보 추출 실패: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": "gmarket"
            }

    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """상품명 추출"""
        # G마켓 상품명 선택자 (여러 패턴 시도)
        selectors = [
            'div.itemtit',
            'h1.itemtit',
            '.box__item-title',
            'meta[property="og:title"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text(strip=True)

        logger.warning("G마켓 상품명을 찾을 수 없습니다")
        return None

    def _extract_price(self, soup: BeautifulSoup) -> Dict:
        """
        가격 추출 (판매가, 정가)

        Returns:
            {
                "price": float,  # 실제 판매가
                "original_price": float  # 할인 전 정가
            }
        """
        price = None
        original_price = None

        # 1. 판매가 추출
        price_selectors = [
            '.price_innerwrap .price',
            '.price_real',
            '.price strong',
            'span.price_real'
        ]

        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                price_text = re.sub(r'[^\d]', '', price_text)  # 숫자만 추출
                if price_text:
                    try:
                        price = int(price_text)
                        break
                    except ValueError:
                        continue

        # 2. 정가 추출 (할인 전 가격)
        original_selectors = [
            '.price_origin',
            '.price_real_org',
            'del.price'
        ]

        for selector in original_selectors:
            element = soup.select_one(selector)
            if element:
                original_text = element.get_text(strip=True)
                original_text = re.sub(r'[^\d]', '', original_text)
                if original_text:
                    try:
                        original_price = int(original_text)
                        break
                    except ValueError:
                        continue

        return {
            "price": price,
            "original_price": original_price
        }

    def _check_stock_status(self, soup: BeautifulSoup) -> str:
        """
        재고 상태 체크

        Returns:
            "available" | "out_of_stock"
        """
        # 품절 키워드 체크
        out_of_stock_indicators = [
            '품절',
            '일시품절',
            '재고없음',
            '판매종료',
            'sold out'
        ]

        page_text = soup.get_text().lower()

        for indicator in out_of_stock_indicators:
            if indicator in page_text:
                logger.info(f"G마켓 품절 감지: {indicator}")
                return "out_of_stock"

        # 품절 CSS 클래스 체크
        sold_out_elements = soup.select('.soldout, .out_of_stock, [class*="sold"]')
        if sold_out_elements:
            logger.info("G마켓 품절 클래스 감지")
            return "out_of_stock"

        return "available"

    def _extract_thumbnail(self, soup: BeautifulSoup) -> Optional[str]:
        """썸네일 이미지 URL 추출"""
        # 썸네일 선택자 (우선순위대로)
        selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            '.thumb_image img',
            '.item_photo_view img',
            '#objImgW img'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    url = element.get('content', '')
                else:
                    url = element.get('src', '') or element.get('data-src', '')

                if url:
                    # 상대 경로를 절대 경로로 변환
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif url.startswith('/'):
                        url = 'https://gdimg.gmarket.co.kr' + url

                    logger.debug(f"G마켓 썸네일 추출: {url}")
                    return url

        logger.warning("G마켓 썸네일을 찾을 수 없습니다")
        return None


if __name__ == "__main__":
    # 테스트용
    scraper = GmarketScraper()

    # 테스트 URL (실제 G마켓 상품 URL로 교체)
    test_url = "http://item.gmarket.co.kr/Item?goodscode=2583445095"

    print("G마켓 스크래퍼 테스트")
    print("=" * 50)

    result = scraper.extract_product_info(test_url)

    print(f"\n결과: {result['success']}")
    if result['success']:
        print(f"상품명: {result.get('product_name')}")
        print(f"가격: {result.get('price'):,}원")
        print(f"정가: {result.get('original_price'):,}원" if result.get('original_price') else "정가: 없음")
        print(f"상태: {result.get('status')}")
        print(f"썸네일: {result.get('thumbnail')}")
    else:
        print(f"오류: {result.get('error')}")
