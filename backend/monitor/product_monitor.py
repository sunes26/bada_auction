"""
상품 모니터링 로직 - FlareSolverr 기반 (Selenium 제거)
"""
import re
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from logger import get_logger

# FlareSolverr 클라이언트 임포트
try:
    from utils.flaresolverr import solve_cloudflare
    FLARESOLVERR_AVAILABLE = True
except ImportError:
    FLARESOLVERR_AVAILABLE = False

logger = get_logger(__name__)


class ProductMonitor:
    """상품 상태 모니터링 - FlareSolverr 기반"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def _get_html_with_flaresolverr(self, url: str) -> Optional[str]:
        """FlareSolverr로 HTML 가져오기"""
        if not FLARESOLVERR_AVAILABLE:
            logger.warning("FlareSolverr 사용 불가")
            return None

        try:
            logger.info(f"[FLARESOLVERR] 페이지 요청: {url}")
            result = solve_cloudflare(url, max_timeout=60000)

            if result and result.get('html'):
                html = result.get('html', '')
                logger.info(f"[FLARESOLVERR] HTML 수신 완료 (길이: {len(html)})")
                return html
            else:
                logger.warning("[FLARESOLVERR] 실패 또는 빈 응답")
                return None
        except Exception as e:
            logger.error(f"[FLARESOLVERR] 오류: {e}")
            return None

    def _get_html_with_requests(self, url: str) -> Optional[str]:
        """requests로 HTML 가져오기 (빠른 추출용)"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"[REQUESTS] 실패: {e}")
            return None

    def extract_info_fast(self, product_url: str) -> Dict[str, Optional[str]]:
        """
        requests + BeautifulSoup으로 빠르게 상품 정보 추출
        JavaScript 렌더링이 필요한 사이트는 FlareSolverr 사용
        """
        try:
            print(f"[FAST] 빠른 추출 시도: {product_url}")

            # JavaScript 렌더링이 필요한 사이트 목록
            js_required_sites = ['ssg.com', '11st.co.kr', 'lotteon.com', 'gsshop.com', 'cjthemarket.com', 'otokimall.com']
            needs_js = any(site in product_url for site in js_required_sites)

            if needs_js:
                # FlareSolverr 사용
                html = self._get_html_with_flaresolverr(product_url)
                if not html:
                    print(f"[FAST] FlareSolverr 실패")
                    return None
            else:
                # requests 사용 (빠름)
                html = self._get_html_with_requests(product_url)
                if not html:
                    # requests 실패 시 FlareSolverr 폴백
                    html = self._get_html_with_flaresolverr(product_url)
                    if not html:
                        print(f"[FAST] 모든 방법 실패")
                        return None

            soup = BeautifulSoup(html, 'html.parser')

            # 상품명 추출
            product_name = self._extract_product_name(soup, product_url)

            # 가격 추출
            price = self._extract_price(soup, product_url)

            # 썸네일 추출
            thumbnail = self._extract_thumbnail(soup, product_url)

            if product_name and len(product_name) > 3:
                if price and price > 0:
                    print(f"[FAST] SUCCESS: {product_name}, Price: {price}")
                    return {
                        'product_name': product_name,
                        'price': price,
                        'thumbnail': thumbnail,
                    }
                else:
                    print(f"[FAST] 상품명은 있지만 가격 없음: {product_name}")
                    return {
                        'product_name': product_name,
                        'price': None,
                        'thumbnail': thumbnail,
                    }
            else:
                print(f"[FAST] FAIL: 상품명 없음")
                return None

        except Exception as e:
            print(f"[FAST] FAIL: {str(e)}")
            return None

    def _extract_product_name(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """HTML에서 상품명 추출"""
        product_name = None

        # 1. og:title 메타 태그 (가장 신뢰성 높음)
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            product_name = og_title['content'].strip()
            # 사이트명 제거
            if ' - 11번가' in product_name:
                product_name = product_name.split(' - 11번가')[0].strip()
            elif ' | ' in product_name:
                product_name = product_name.split(' | ')[0].strip()
            elif ' - ' in product_name and len(product_name.split(' - ')) == 2:
                product_name = product_name.split(' - ')[0].strip()

        # 2. title 태그
        if not product_name:
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                product_name = title_tag.string.strip()
                # 사이트명 제거
                for separator in [' - 11번가', ' | ', ' - SSG', ' - GS SHOP']:
                    if separator in product_name:
                        product_name = product_name.split(separator)[0].strip()
                        break

        # 3. 사이트별 선택자
        if not product_name or len(product_name) < 5:
            selectors = []
            if '11st.co.kr' in url:
                selectors = ['.c_product_info_title h1', '.l_product_title h1', 'h1.title']
            elif 'ssg.com' in url:
                selectors = ['.cdtl_info_tit', '.product_title']
            elif 'gmarket.co.kr' in url or 'auction.co.kr' in url:
                selectors = ['.itemtit', 'h1']
            elif 'gsshop.com' in url:
                selectors = ['.prd-btns h2', '.goods-header h2', 'h1']
            elif 'cjthemarket.com' in url:
                selectors = ['.prd-name', '.product-name', 'h1']
            elif 'homeplus.co.kr' in url:
                selectors = ['.prodNameBox', 'h1']
            elif 'lotteon.com' in url:
                selectors = ['h1', '.product-name']
            elif 'otokimall.com' in url:
                selectors = ['.prd_name', '.product-name', 'h1', 'h2']

            for selector in selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    product_name = elem.get_text(strip=True)
                    if len(product_name) > 5:
                        break

        return product_name

    def _extract_price(self, soup: BeautifulSoup, url: str) -> Optional[float]:
        """HTML에서 가격 추출"""
        price = None

        # 1. og:price 메타 태그
        og_price = soup.find('meta', property='og:price:amount')
        if not og_price:
            og_price = soup.find('meta', property='product:price:amount')
        if og_price and og_price.get('content'):
            try:
                price = float(og_price['content'])
                if price > 100:
                    return price
            except:
                pass

        # 2. 사이트별 가격 선택자
        if '11st.co.kr' in url:
            # 11번가: .price 클래스 또는 가격 패턴
            selectors = ['.price', '.c_product_price .price strong', '.l_product_price strong']
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price:
                        return price

        elif 'ssg.com' in url:
            # SSG
            selectors = ['.cdtl_price .ssg_price', '.ssg_price']
            for selector in selectors:
                elems = soup.select(selector)
                for elem in elems:
                    # 정가 영역 제외
                    if elem.find_parent(class_='cdtl_old_price'):
                        continue
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price and price > 1000:
                        return price

        elif 'gmarket.co.kr' in url or 'auction.co.kr' in url:
            selectors = ['.price_sect .price strong', '.item_price strong', '.price strong']
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price and price > 1000:
                        return price

        elif 'gsshop.com' in url:
            selectors = ['.price-definition__amount', '.price-amount', '.price strong']
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price:
                        return price

        elif 'cjthemarket.com' in url:
            selectors = ['.prd-price strong', '.price-area .sale-price', '.final-price']
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price:
                        return price

        elif 'homeplus.co.kr' in url:
            selectors = ['.price', '.sale-price']
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price:
                        return price

        elif 'lotteon.com' in url:
            selectors = ['.price', '[class*="price"]']
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price and price > 1000:
                        return price

        elif 'otokimall.com' in url:
            # 오뚜기몰: hidden input의 data-finalprice 또는 .price 영역
            price_input = soup.find('input', id='pdPrice')
            if price_input and price_input.get('data-finalprice'):
                try:
                    price = float(price_input['data-finalprice'])
                    if price > 100:
                        return price
                except:
                    pass
            selectors = ['.price', '.sale_price', '.prd_price']
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    price = self._parse_price(text)
                    if price and price > 100:
                        return price

        # 3. 페이지에서 가격 패턴 찾기 (폴백)
        if not price:
            page_text = soup.get_text()
            matches = re.findall(r'(\d{1,3}(?:,\d{3})+)\s*원', page_text)
            if matches:
                # 첫 번째 가격 사용 (상품 가격일 가능성 높음)
                for match in matches[:5]:
                    try:
                        p = int(match.replace(',', ''))
                        if 1000 < p < 10000000:
                            price = p
                            break
                    except:
                        pass

        return price

    def _parse_price(self, text: str) -> Optional[float]:
        """가격 텍스트를 숫자로 변환"""
        if not text:
            return None
        # 숫자와 콤마만 추출
        num_str = re.sub(r'[^\d]', '', text)
        if num_str:
            try:
                price = float(num_str)
                if 100 < price < 100000000:
                    return price
            except:
                pass
        return None

    def _extract_thumbnail(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """HTML에서 썸네일 추출"""
        thumbnail = None

        # 1. og:image 메타 태그
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            thumbnail = og_image['content']
            if thumbnail.startswith('//'):
                thumbnail = 'https:' + thumbnail
            return thumbnail

        # 2. 첫 번째 큰 이미지 찾기
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                # 작은 아이콘, 로고 제외
                skip_keywords = ['icon', 'logo', 'banner', 'btn', 'button', 'sprite', 'blank', '1x1']
                if not any(kw in src.lower() for kw in skip_keywords):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif not src.startswith('http'):
                        src = urljoin(url, src)
                    return src

        return thumbnail

    def extract_product_name(self, product_url: str, source: str) -> Optional[str]:
        """URL에서 상품명 추출"""
        try:
            html = self._get_html_with_flaresolverr(product_url)
            if not html:
                html = self._get_html_with_requests(product_url)

            if html:
                soup = BeautifulSoup(html, 'html.parser')
                return self._extract_product_name(soup, product_url)
            return None
        except Exception as e:
            print(f"[DEBUG] 상품명 추출 오류: {str(e)}")
            return None

    def check_product_status(self, product_url: str, source: str) -> Dict:
        """
        상품 페이지를 체크하여 상태 및 가격 정보 반환
        """
        try:
            print(f"모니터링: {product_url}")

            # FlareSolverr로 HTML 가져오기
            html = self._get_html_with_flaresolverr(product_url)

            if not html:
                # FlareSolverr 실패 시 requests 시도
                html = self._get_html_with_requests(product_url)

            if not html:
                return {
                    'status': 'error',
                    'price': None,
                    'original_price': None,
                    'details': 'HTML 가져오기 실패'
                }

            soup = BeautifulSoup(html, 'html.parser')

            # 사이트별 상태 체크
            if 'ssg.com' in product_url:
                result = self._check_ssg_status(soup)
            elif 'homeplus.co.kr' in product_url or 'traders' in product_url:
                result = self._check_homeplus_status(soup)
            elif '11st.co.kr' in product_url:
                result = self._check_11st_status(soup)
            elif 'lotteon.com' in product_url:
                result = self._check_lotteon_status(soup)
            elif 'gmarket.co.kr' in product_url:
                result = self._check_gmarket_status(soup, product_url)
            elif 'auction.co.kr' in product_url:
                result = self._check_auction_status(soup, product_url)
            elif 'gsshop.com' in product_url:
                result = self._check_gsshop_status(soup)
            elif 'cjthemarket.com' in product_url:
                result = self._check_cjthemarket_status(soup)
            elif 'otokimall.com' in product_url:
                result = self._check_otokimall_status(soup)
            else:
                result = self._check_generic_status(soup)

            return result

        except Exception as e:
            print(f"모니터링 오류: {str(e)}")
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"체크 실패: {str(e)}"
            }

    def _check_status_common(self, soup: BeautifulSoup) -> str:
        """공통 품절/판매종료 상태 체크"""
        page_text = soup.get_text().lower()

        out_of_stock_keywords = ['품절', '일시품절', 'sold out', 'out of stock', '재고없음']
        discontinued_keywords = ['판매종료', '판매중지', 'discontinued', '단종', '판매중단']

        for keyword in out_of_stock_keywords:
            if keyword in page_text:
                return 'out_of_stock'

        for keyword in discontinued_keywords:
            if keyword in page_text:
                return 'discontinued'

        return 'available'

    def _check_ssg_status(self, soup: BeautifulSoup) -> Dict:
        """SSG 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'ssg.com')

            # 정가 추출
            original_price = None
            old_price_elem = soup.select_one('.cdtl_old_price .ssg_price')
            if old_price_elem:
                original_price = self._parse_price(old_price_elem.get_text())

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.cdtl_btn_wrap',     # 버튼 영역
                '.btn_buy',           # 구매 버튼
                '.btn_cart',          # 장바구니 버튼
                '[class*="soldout"]', # 품절 클래스
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'soldout' in elem.get('class', []):
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 가격이 정상 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                buy_btn = soup.select_one('.btn_buy, .cdtl_btn_buy')
                if buy_btn and '품절' not in buy_btn.get_text().lower():
                    status = 'available'
                    print(f"[SSG] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': original_price,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"SSG 체크 오류: {str(e)}"
            }

    def _check_homeplus_status(self, soup: BeautifulSoup) -> Dict:
        """홈플러스/Traders 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'homeplus.co.kr')

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn-buy',           # 구매 버튼
                '.btn-cart',          # 장바구니 버튼
                '.product-button',    # 상품 버튼 영역
                '[class*="soldout"]', # 품절 클래스
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 가격이 정상 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                buy_btn = soup.select_one('.btn-buy, [class*="btn-buy"]')
                if buy_btn and '품절' not in buy_btn.get_text().lower():
                    status = 'available'
                    print(f"[HOMEPLUS] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"홈플러스 체크 오류: {str(e)}"
            }

    def _check_11st_status(self, soup: BeautifulSoup) -> Dict:
        """11번가 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, '11st.co.kr')

            # 1. 구매 버튼 영역에서 품절 확인 (가장 정확)
            buy_button_selectors = [
                '.c_product_button',  # 상품 버튼 영역
                '.l_product_side',    # 사이드 영역
                '.btn_buy',           # 구매 버튼
                '.btn_cart',          # 장바구니 버튼
                '[class*="buy"]',     # buy 포함 클래스
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    # 구매 버튼 영역에 품절 키워드가 있으면 품절
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    # 구매하기/장바구니 버튼이 있으면 판매 중
                    if '구매' in elem_text or '장바구니' in elem_text or '카트' in elem_text:
                        status = 'available'
                        break

            # 2. 상품 정보 영역에서만 품절 확인 (페이지 전체 아님)
            if status == 'available':
                product_info_selectors = [
                    '.c_product_info',    # 상품 정보 영역
                    '.l_product_summary', # 상품 요약
                    '.product_info',      # 상품 정보
                ]
                for selector in product_info_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        elem_text = elem.get_text().lower()
                        if '품절' in elem_text or '판매종료' in elem_text:
                            status = 'out_of_stock'
                            break

            # 3. 가격이 정상적으로 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                # 가격이 있는데 품절로 감지된 경우, 페이지 다른 곳의 "품절" 일 수 있음
                # 구매 버튼이 있는지 한번 더 확인
                buy_btn = soup.select_one('.btn_buy, [class*="btn_buy"], button[class*="buy"]')
                if buy_btn:
                    btn_text = buy_btn.get_text().lower()
                    if '품절' not in btn_text and '일시품절' not in btn_text:
                        status = 'available'
                        print(f"[11ST] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"11번가 체크 오류: {str(e)}"
            }

    def _check_lotteon_status(self, soup: BeautifulSoup) -> Dict:
        """롯데ON 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'lotteon.com')

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn_buy',           # 구매 버튼
                '.btn_cart',          # 장바구니 버튼
                '[class*="buy"]',     # buy 포함 클래스
                '[class*="soldout"]', # 품절 클래스
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 가격이 정상 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                buy_btn = soup.select_one('[class*="btn_buy"], [class*="buy"]')
                if buy_btn and '품절' not in buy_btn.get_text().lower():
                    status = 'available'
                    print(f"[LOTTEON] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"롯데ON 체크 오류: {str(e)}"
            }

    def _check_gmarket_status(self, soup: BeautifulSoup, url: str) -> Dict:
        """G마켓 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, url)

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn_buy',           # 구매 버튼
                '.btn_cart',          # 장바구니 버튼
                '.box_buy',           # 구매 박스
                '[class*="soldout"]', # 품절 클래스
                '.item_buy',          # 구매 영역
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 가격이 정상 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                buy_btn = soup.select_one('.btn_buy, [class*="btn_buy"]')
                if buy_btn and '품절' not in buy_btn.get_text().lower():
                    status = 'available'
                    print(f"[GMARKET] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"G마켓 체크 오류: {str(e)}"
            }

    def _check_auction_status(self, soup: BeautifulSoup, url: str) -> Dict:
        """옥션 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, url)

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn_buy',           # 구매 버튼
                '.btn_cart',          # 장바구니 버튼
                '.box_buy',           # 구매 박스
                '[class*="soldout"]', # 품절 클래스
                '.item_buy',          # 구매 영역
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 가격이 정상 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                buy_btn = soup.select_one('.btn_buy, [class*="btn_buy"]')
                if buy_btn and '품절' not in buy_btn.get_text().lower():
                    status = 'available'
                    print(f"[AUCTION] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"옥션 체크 오류: {str(e)}"
            }

    def _check_gsshop_status(self, soup: BeautifulSoup) -> Dict:
        """GS샵 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'gsshop.com')

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn-buy',           # 구매 버튼
                '.btn-cart',          # 장바구니 버튼
                '.prd-btns',          # 상품 버튼 영역
                '[class*="soldout"]', # 품절 클래스
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '방송종료' in elem_text:
                        status = 'discontinued'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 상품 정보 영역에서 방송종료 확인
            product_info = soup.select_one('.prd-info, .goods-header')
            if product_info and '방송종료' in product_info.get_text():
                status = 'discontinued'

            # 3. 가격이 정상 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                buy_btn = soup.select_one('.btn-buy, [class*="btn-buy"]')
                if buy_btn and '품절' not in buy_btn.get_text().lower():
                    status = 'available'
                    print(f"[GSSHOP] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"GS샵 체크 오류: {str(e)}"
            }

    def _check_cjthemarket_status(self, soup: BeautifulSoup) -> Dict:
        """CJ제일제당 더마켓 상품 상태 체크 - 구매 버튼 영역만 확인"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'cjthemarket.com')

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn-buy',           # 구매 버튼
                '.btn-cart',          # 장바구니 버튼
                '.prd-btn',           # 상품 버튼
                '[class*="soldout"]', # 품절 클래스
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 가격이 정상 추출되면 판매 중일 가능성 높음
            if status == 'out_of_stock' and price and price > 1000:
                buy_btn = soup.select_one('.btn-buy, [class*="btn-buy"]')
                if buy_btn and '품절' not in buy_btn.get_text().lower():
                    status = 'available'
                    print(f"[CJTHEMARKET] 가격 있고 구매버튼 정상 → 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"CJ더마켓 체크 오류: {str(e)}"
            }

    def _check_otokimall_status(self, soup: BeautifulSoup) -> Dict:
        """오뚜기몰 상품 상태 체크"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'otokimall.com')

            # 정가 추출 (할인 전 가격)
            original_price = None

            # 1. stock 속성으로 재고 확인
            qty_input = soup.find('input', class_='item_qty_count')
            if qty_input:
                stock = qty_input.get('stock', '0')
                max_qty = qty_input.get('max', '0')
                try:
                    if int(stock) <= 0 or int(max_qty) <= 0:
                        status = 'out_of_stock'
                except:
                    pass

            # 2. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn_buy', '.btn_cart',
                '.buy_btn', '.cart_btn',
                '[class*="soldout"]',
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        if status != 'out_of_stock':  # 재고 체크에서 품절이 아닌 경우에만
                            status = 'available'
                        break

            # 3. 가격이 정상 추출되고 품절 표시가 없으면 판매 중
            if price and price > 100 and status == 'available':
                print(f"[OTOKIMALL] 가격 {price}원, 판매중으로 판정")

            return {
                'status': status,
                'price': price,
                'original_price': original_price,
                'details': '정상' if status == 'available' else status
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"오뚜기몰 체크 오류: {str(e)}"
            }

    def _check_generic_status(self, soup: BeautifulSoup) -> Dict:
        """범용 상품 상태 체크 - 구매 버튼 영역 우선 확인"""
        try:
            status = 'available'

            # 1. 구매 버튼 영역에서 품절 확인
            buy_button_selectors = [
                '.btn-buy', '.btn_buy',
                '.btn-cart', '.btn_cart',
                '[class*="buy"]',
                '[class*="cart"]',
                '[class*="soldout"]',
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        break

            # 2. 가격 추출 (패턴 매칭)
            page_text = soup.get_text()
            price_matches = re.findall(r'(\d{1,3}(?:,\d{3})+)\s*원', page_text)
            prices = []
            for match in price_matches:
                try:
                    p = int(match.replace(',', ''))
                    if 100 < p < 10000000:
                        prices.append(p)
                except:
                    pass

            price = min(prices) if prices else None

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': '범용 체크'
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"체크 오류: {str(e)}"
            }
