"""
홈플러스 상품 정보 추출 스크래퍼

홈플러스 온라인몰(mfront.homeplus.co.kr) 상품 페이지에서
상품명, 가격, 재고 상태, 썸네일 자동 추출
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import json
from logger import get_logger

logger = get_logger(__name__)


class HomeplusScraper:
    """홈플러스 상품 정보 추출"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def extract_product_info(self, product_url: str) -> Dict:
        """
        홈플러스 상품 정보 추출

        Args:
            product_url: 홈플러스 상품 URL
                        예: https://mfront.homeplus.co.kr/item?itemNo=10000303142935

        Returns:
            {
                "success": bool,
                "product_name": str,
                "price": float,
                "original_price": float,  # 할인 전 가격
                "status": str,  # available, out_of_stock
                "thumbnail": str,
                "source": "homeplus",
                "error": str  # 실패 시
            }
        """
        try:
            logger.info(f"홈플러스 상품 정보 추출 시작: {product_url}")

            # 페이지 가져오기
            response = requests.get(product_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # 홈플러스는 React SPA이므로 JSON 데이터를 추출해야 함
            # 1. JSON-LD 스키마에서 추출 시도
            product_data = self._extract_from_json_ld(soup)

            # 2. JSON-LD가 없으면 페이지 내 JSON 데이터에서 추출
            if not product_data:
                product_data = self._extract_from_page_json(soup, response.text)

            if not product_data:
                raise Exception("상품 데이터를 찾을 수 없습니다")

            # 3. 상품명 추출
            product_name = product_data.get('product_name') or self._extract_product_name(soup)

            # 4. 가격 추출
            price = product_data.get('price', 0)
            original_price = product_data.get('original_price')

            # 5. 재고 상태 체크
            status = product_data.get('status', 'available')

            # 6. 썸네일 추출
            thumbnail_url = product_data.get('thumbnail') or self._extract_thumbnail(soup)

            logger.info(f"홈플러스 추출 성공: {product_name}, 가격: {price}, 상태: {status}")

            return {
                "success": True,
                "product_name": product_name,
                "price": price,
                "original_price": original_price,
                "status": status,
                "thumbnail": thumbnail_url,
                "source": "homeplus"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"홈플러스 페이지 요청 실패: {e}")
            return {
                "success": False,
                "error": f"페이지 요청 실패: {str(e)}",
                "source": "homeplus"
            }

        except Exception as e:
            logger.error(f"홈플러스 상품 정보 추출 실패: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": "homeplus"
            }

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """JSON-LD 스키마에서 상품 정보 추출"""
        try:
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        # JSON-LD Product 스키마 발견
                        offers = data.get('offers', {})
                        availability = offers.get('availability', '').lower()

                        status = 'available'
                        if 'outofstock' in availability or 'soldout' in availability:
                            status = 'out_of_stock'

                        return {
                            'product_name': data.get('name'),
                            'price': float(offers.get('price', 0)),
                            'original_price': None,  # JSON-LD에는 할인 전 가격이 없을 수 있음
                            'status': status,
                            'thumbnail': data.get('image')
                        }
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.warning(f"JSON-LD 파싱 실패: {e}")

        return None

    def _extract_from_page_json(self, soup: BeautifulSoup, html_text: str) -> Optional[Dict]:
        """페이지 내 JSON 데이터에서 상품 정보 추출 (React SPA)"""
        try:
            # 방법 1: window.__INITIAL_STATE__ 또는 유사한 전역 변수에서 추출
            script_tags = soup.find_all('script')
            for script in script_tags:
                if not script.string:
                    continue

                script_content = script.string

                # itemNm, salePrice, itemSoldOutYn 패턴 검색
                item_name_match = re.search(r'"itemNm"\s*:\s*"([^"]+)"', script_content)
                sale_price_match = re.search(r'"salePrice"\s*:\s*(\d+)', script_content)
                sold_out_match = re.search(r'"itemSoldOutYn"\s*:\s*"([YN])"', script_content)

                # 이미지 URL 추출 (mainList 배열에서)
                image_match = re.search(r'"mainList"\s*:\s*\[\s*{\s*"url"\s*:\s*"([^"]+)"', script_content)

                # 할인가 추출 (dcPrice)
                dc_price_match = re.search(r'"dcPrice"\s*:\s*(\d+)', script_content)

                if item_name_match and sale_price_match:
                    product_name = item_name_match.group(1)
                    price = float(sale_price_match.group(1))

                    # 재고 상태 확인
                    status = 'available'
                    if sold_out_match and sold_out_match.group(1) == 'Y':
                        status = 'out_of_stock'

                    # 할인가가 있으면 original_price 설정
                    original_price = None
                    if dc_price_match:
                        dc_price = float(dc_price_match.group(1))
                        if dc_price > 0 and dc_price < price:
                            original_price = price
                            price = dc_price

                    # 썸네일
                    thumbnail = None
                    if image_match:
                        thumbnail = image_match.group(1)
                        # 상대 URL이면 절대 URL로 변환
                        if thumbnail and not thumbnail.startswith('http'):
                            if thumbnail.startswith('//'):
                                thumbnail = 'https:' + thumbnail
                            else:
                                thumbnail = 'https://image.homeplus.kr/' + thumbnail.lstrip('/')

                    return {
                        'product_name': product_name,
                        'price': price,
                        'original_price': original_price,
                        'status': status,
                        'thumbnail': thumbnail
                    }

        except Exception as e:
            logger.warning(f"페이지 JSON 파싱 실패: {e}")

        return None

    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """상품명 추출 (fallback)"""
        # 홈플러스 상품명 선택자 (여러 패턴 시도)
        selectors = [
            'h1.product-name',
            'h1.item-name',
            'div.product-title',
            'h1',
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        # meta 태그에서 시도
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content']

        return "상품명 없음"

    def _extract_thumbnail(self, soup: BeautifulSoup) -> Optional[str]:
        """썸네일 이미지 URL 추출 (fallback)"""
        # Open Graph 이미지
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']

        # 첫 번째 상품 이미지
        product_img = soup.select_one('img.product-image, img.item-image, div.product-img img')
        if product_img:
            img_url = product_img.get('src') or product_img.get('data-src')
            if img_url:
                if not img_url.startswith('http'):
                    if img_url.startswith('//'):
                        return 'https:' + img_url
                    else:
                        return 'https://image.homeplus.kr/' + img_url.lstrip('/')
                return img_url

        return None
