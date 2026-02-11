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
            js_required_sites = ['ssg.com', '11st.co.kr', 'lotteon.com', 'gsshop.com', 'cjthemarket.com', 'otokimall.com', 'dongwonmall.com']
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
            elif 'dongwonmall.com' in url:
                selectors = ['h1', 'input[name="product_nm"]', '.product-name', '.prd-name']

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

        elif 'dongwonmall.com' in url:
            # 동원몰: userPrice input 또는 .userPriceText
            price_input = soup.find('input', id='userPrice')
            if price_input and price_input.get('value'):
                try:
                    price = float(price_input['value'].replace(',', ''))
                    if price > 100:
                        return price
                except:
                    pass
            selectors = ['.userPriceText', '.sale-price', '.price']
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

        # 0. 사이트별 특수 선택자 (og:image가 로고인 경우 대비)
        site_specific_selectors = {
            'dongwonmall.com': ['#mainImg img', '.product_image img', '.photo img'],
            'otokimall.com': ['#prdImage img', '.product-image img', '.prd-img img'],
        }

        for site, selectors in site_specific_selectors.items():
            if site in url:
                for selector in selectors:
                    img = soup.select_one(selector)
                    if img:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif not src.startswith('http'):
                                src = urljoin(url, src)
                            return src

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
            elif 'dongwonmall.com' in product_url:
                result = self._check_dongwonmall_status(soup)
            else:
                # 알 수 없는 소싱처: 범용 추출 사용
                result = self._check_generic_status(soup, product_url)

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
        """CJ제일제당 더마켓 상품 상태 체크"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'cjthemarket.com')
            details = '정상'

            # 1. 삭제된 상품 확인 (alert 메시지)
            page_text = soup.get_text()
            if '구매할 수 있는 상품이 존재하지 않아요' in page_text:
                print(f"[CJTHEMARKET] 상품 삭제됨 감지")
                return {
                    'status': 'discontinued',
                    'price': None,
                    'original_price': None,
                    'details': '상품이 삭제됨'
                }

            # 2. 재입고 알림 버튼 확인 → 일시품절
            restock_btn = soup.select_one('.btn__restock')
            if restock_btn:
                print(f"[CJTHEMARKET] 재입고 알림 버튼 감지 → 일시품절")
                return {
                    'status': 'out_of_stock',
                    'price': price,
                    'original_price': None,
                    'details': '일시품절 (재입고 알림)'
                }

            # 3. 구매 버튼 영역에서 상태 확인
            buy_button_selectors = [
                '.btn__default',      # CJ더마켓 기본 버튼
                '.btn--wrap button',  # 버튼 래퍼 내 버튼
                '[class*="soldout"]', # 품절 클래스
            ]

            for selector in buy_button_selectors:
                elem = soup.select_one(selector)
                if elem:
                    elem_text = elem.get_text().lower()
                    if '품절' in elem_text or '일시품절' in elem_text or 'sold out' in elem_text:
                        status = 'out_of_stock'
                        details = '일시품절'
                        break
                    if '판매종료' in elem_text or '판매중지' in elem_text:
                        status = 'discontinued'
                        details = '판매종료'
                        break
                    if '구매' in elem_text or '장바구니' in elem_text:
                        status = 'available'
                        details = '정상'
                        break

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': details
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

    def _check_dongwonmall_status(self, soup: BeautifulSoup) -> Dict:
        """동원몰 상품 상태 체크"""
        try:
            status = 'available'
            price = self._extract_price(soup, 'dongwonmall.com')

            # 정가 추출
            original_price = None
            original_elem = soup.select_one('.origin-price')
            if original_elem:
                original_price = self._parse_price(original_elem.get_text())

            # 1. 판매상태 코드 확인 (PB_COM_CD: 01=판매중)
            status_input = soup.find('input', id='PB_COM_CD')
            if status_input:
                status_code = status_input.get('value', '01')
                if status_code != '01':
                    status = 'out_of_stock'

            # 2. soldout 클래스 확인
            soldout_elem = soup.select_one('.soldout')
            if soldout_elem:
                status = 'out_of_stock'

            # 3. 구매 버튼 텍스트 확인
            buy_buttons = soup.select('.btn-buy, .btn_buy, .cart-btn')
            for btn in buy_buttons:
                btn_text = btn.get_text().lower()
                if '품절' in btn_text or 'sold out' in btn_text:
                    status = 'out_of_stock'
                    break

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
                'details': f"동원몰 체크 오류: {str(e)}"
            }

    def _check_generic_status(self, soup: BeautifulSoup, url: str = '') -> Dict:
        """범용 상품 상태 체크 - 새로운 범용 추출 기능 사용"""
        try:
            # 범용 추출 기능 사용 (JSON-LD → 메타태그 → Microdata → CSS패턴)
            generic_result = self.extract_generic_product_info(soup, url)

            if generic_result:
                price = generic_result.get('price')
                status = generic_result.get('status', 'available')
                method = generic_result.get('extraction_method', 'unknown')

                return {
                    'status': status,
                    'price': price,
                    'original_price': None,
                    'details': f'범용 추출 ({method})'
                }

            # 범용 추출 실패 시 기본 상태 체크
            status = self._check_status_common(soup)

            return {
                'status': status,
                'price': None,
                'original_price': None,
                'details': '범용 추출 실패 - 가격 확인 필요'
            }
        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"체크 오류: {str(e)}"
            }

    # ========== 범용 추출 메서드 (알 수 없는 쇼핑몰용) ==========

    def extract_generic_product_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        범용 상품 정보 추출 - 우선순위에 따라 여러 방법 시도
        1. JSON-LD 구조화 데이터
        2. 표준 메타 태그 (og:, product:)
        3. Microdata (Schema.org)
        4. 공통 CSS 패턴
        """
        result = {
            'product_name': None,
            'price': None,
            'thumbnail': None,
            'status': 'available',
            'extraction_method': None
        }

        # 1단계: JSON-LD 구조화 데이터 시도
        json_ld_result = self._extract_from_json_ld(soup)
        if json_ld_result.get('product_name') and json_ld_result.get('price'):
            result.update(json_ld_result)
            result['extraction_method'] = 'json-ld'
            print(f"[GENERIC] JSON-LD 추출 성공: {result['product_name']}, {result['price']}원")
            return result

        # 2단계: 표준 메타 태그 시도
        meta_result = self._extract_from_meta_tags(soup)
        if meta_result.get('product_name') and meta_result.get('price'):
            result.update(meta_result)
            result['extraction_method'] = 'meta-tags'
            print(f"[GENERIC] 메타 태그 추출 성공: {result['product_name']}, {result['price']}원")
            return result

        # 3단계: Microdata 시도
        microdata_result = self._extract_from_microdata(soup)
        if microdata_result.get('product_name') and microdata_result.get('price'):
            result.update(microdata_result)
            result['extraction_method'] = 'microdata'
            print(f"[GENERIC] Microdata 추출 성공: {result['product_name']}, {result['price']}원")
            return result

        # 4단계: 공통 CSS 패턴 시도
        css_result = self._extract_from_css_patterns(soup, url)
        if css_result.get('product_name') and css_result.get('price'):
            result.update(css_result)
            result['extraction_method'] = 'css-patterns'
            print(f"[GENERIC] CSS 패턴 추출 성공: {result['product_name']}, {result['price']}원")
            return result

        # 부분적 결과라도 병합 (이름만 있거나 가격만 있는 경우)
        for partial in [json_ld_result, meta_result, microdata_result, css_result]:
            if not result['product_name'] and partial.get('product_name'):
                result['product_name'] = partial['product_name']
            if not result['price'] and partial.get('price'):
                result['price'] = partial['price']
            if not result['thumbnail'] and partial.get('thumbnail'):
                result['thumbnail'] = partial['thumbnail']

        if result['product_name'] or result['price']:
            result['extraction_method'] = 'partial'
            print(f"[GENERIC] 부분 추출: 이름={result['product_name']}, 가격={result['price']}")
            return result

        print("[GENERIC] 모든 추출 방법 실패")
        return None

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Dict:
        """JSON-LD 구조화 데이터에서 상품 정보 추출"""
        result = {'product_name': None, 'price': None, 'thumbnail': None, 'status': 'available'}

        try:
            import json
            scripts = soup.find_all('script', type='application/ld+json')

            for script in scripts:
                try:
                    data = json.loads(script.string)

                    # @graph 배열 처리
                    if isinstance(data, dict) and '@graph' in data:
                        data = data['@graph']

                    # 배열인 경우 Product 타입 찾기
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') in ['Product', 'IndividualProduct']:
                                data = item
                                break
                        else:
                            continue

                    # Product 타입 확인
                    if isinstance(data, dict) and data.get('@type') in ['Product', 'IndividualProduct']:
                        # 상품명
                        result['product_name'] = data.get('name')

                        # 이미지
                        image = data.get('image')
                        if isinstance(image, list) and image:
                            result['thumbnail'] = image[0] if isinstance(image[0], str) else image[0].get('url')
                        elif isinstance(image, str):
                            result['thumbnail'] = image
                        elif isinstance(image, dict):
                            result['thumbnail'] = image.get('url')

                        # 가격 (offers에서)
                        offers = data.get('offers')
                        if offers:
                            if isinstance(offers, list):
                                offers = offers[0]
                            if isinstance(offers, dict):
                                price = offers.get('price') or offers.get('lowPrice')
                                if price:
                                    try:
                                        result['price'] = float(str(price).replace(',', ''))
                                    except:
                                        pass

                                # 재고 상태
                                availability = offers.get('availability', '')
                                if 'OutOfStock' in str(availability):
                                    result['status'] = 'out_of_stock'

                        if result['product_name']:
                            return result

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"[JSON-LD] 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"[JSON-LD] 전체 오류: {e}")

        return result

    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """표준 메타 태그에서 상품 정보 추출"""
        result = {'product_name': None, 'price': None, 'thumbnail': None, 'status': 'available'}

        try:
            # 상품명: og:title, twitter:title
            for prop in ['og:title', 'twitter:title']:
                meta = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
                if meta and meta.get('content'):
                    name = meta['content'].strip()
                    # 사이트명 제거
                    for sep in [' - ', ' | ', ' :: ', ' – ']:
                        if sep in name:
                            name = name.split(sep)[0].strip()
                    if len(name) > 3:
                        result['product_name'] = name
                        break

            # 가격: og:price:amount, product:price:amount
            for prop in ['og:price:amount', 'product:price:amount', 'product:sale_price:amount']:
                meta = soup.find('meta', property=prop)
                if meta and meta.get('content'):
                    try:
                        result['price'] = float(meta['content'].replace(',', ''))
                        break
                    except:
                        pass

            # 이미지: og:image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                result['thumbnail'] = og_image['content']
                if result['thumbnail'].startswith('//'):
                    result['thumbnail'] = 'https:' + result['thumbnail']

            # 재고 상태: product:availability
            availability = soup.find('meta', property='product:availability')
            if availability and availability.get('content'):
                if 'out' in availability['content'].lower():
                    result['status'] = 'out_of_stock'

        except Exception as e:
            print(f"[META] 오류: {e}")

        return result

    def _extract_from_microdata(self, soup: BeautifulSoup) -> Dict:
        """Microdata (Schema.org)에서 상품 정보 추출"""
        result = {'product_name': None, 'price': None, 'thumbnail': None, 'status': 'available'}

        try:
            # Product itemtype 찾기
            product_elem = soup.find(itemtype=re.compile(r'schema\.org.*Product', re.I))
            if not product_elem:
                product_elem = soup.find(itemscope=True)

            if product_elem:
                # 상품명
                name_elem = product_elem.find(itemprop='name')
                if name_elem:
                    result['product_name'] = name_elem.get_text(strip=True) or name_elem.get('content')

                # 가격
                price_elem = product_elem.find(itemprop='price')
                if price_elem:
                    price_text = price_elem.get('content') or price_elem.get_text(strip=True)
                    if price_text:
                        price = self._parse_price(price_text)
                        if price:
                            result['price'] = price

                # 이미지
                image_elem = product_elem.find(itemprop='image')
                if image_elem:
                    result['thumbnail'] = image_elem.get('src') or image_elem.get('content') or image_elem.get('href')

                # 재고
                availability_elem = product_elem.find(itemprop='availability')
                if availability_elem:
                    avail_text = availability_elem.get('content', '') or availability_elem.get('href', '')
                    if 'OutOfStock' in avail_text:
                        result['status'] = 'out_of_stock'

        except Exception as e:
            print(f"[MICRODATA] 오류: {e}")

        return result

    def _extract_from_css_patterns(self, soup: BeautifulSoup, url: str) -> Dict:
        """공통 CSS 패턴에서 상품 정보 추출"""
        result = {'product_name': None, 'price': None, 'thumbnail': None, 'status': 'available'}

        try:
            # 상품명 CSS 선택자 (우선순위 순)
            name_selectors = [
                'h1.product-name', 'h1.product-title', 'h1.prd-name', 'h1.goods-name',
                '.product-name h1', '.product-title h1', '.prd-name', '.goods-name',
                '.product_name', '.productName', '.item-name', '.item_name',
                'h1[class*="product"]', 'h1[class*="title"]', 'h1[class*="name"]',
                '.detail-title', '.product-detail-title', '.prd_name',
                'h1', 'h2.product-name', 'h2.prd-name'
            ]

            for selector in name_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        name = elem.get_text(strip=True)
                        if name and len(name) > 3 and len(name) < 200:
                            result['product_name'] = name
                            break
                except:
                    continue

            # 가격 CSS 선택자 (우선순위 순)
            price_selectors = [
                '.sale-price', '.sale_price', '.salePrice', '.selling-price',
                '.final-price', '.final_price', '.finalPrice',
                '.price-value', '.price_value', '.priceValue',
                '.product-price', '.product_price', '.productPrice',
                '.prd-price', '.prd_price', '.item-price', '.item_price',
                '.current-price', '.now-price', '.discount-price',
                '[class*="sale"][class*="price"]', '[class*="final"][class*="price"]',
                '.price strong', '.price em', '.price span',
                '.price', '#price'
            ]

            for selector in price_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        price = self._parse_price(text)
                        if price and price > 100:
                            result['price'] = price
                            break
                except:
                    continue

            # 가격을 못 찾으면 휴리스틱으로 시도
            if not result['price']:
                page_text = soup.get_text()
                # 한국 원화 가격 패턴
                price_patterns = [
                    r'(\d{1,3}(?:,\d{3})+)\s*원',  # 1,000원 ~ 999,999,999원
                    r'₩\s*(\d{1,3}(?:,\d{3})+)',   # ₩1,000
                    r'KRW\s*(\d{1,3}(?:,\d{3})+)', # KRW 1,000
                ]
                for pattern in price_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        for match in matches[:10]:  # 처음 10개만 확인
                            try:
                                p = int(match.replace(',', ''))
                                if 100 < p < 100000000:  # 100원 ~ 1억
                                    result['price'] = p
                                    break
                            except:
                                pass
                        if result['price']:
                            break

            # 이미지 CSS 선택자
            image_selectors = [
                '.product-image img', '.product_image img', '.prd-image img',
                '.main-image img', '.main_image img', '.mainImage img',
                '.thumb img', '.thumbnail img', '.product-photo img',
                '#product-image', '#productImage', '#main-image',
                '.swiper-slide img', '.slick-slide img', '.carousel img',
                '[class*="product"][class*="image"] img',
                '[class*="main"][class*="image"] img',
                'img[class*="product"]', 'img[class*="main"]',
            ]

            for selector in image_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        src = elem.get('src') or elem.get('data-src') or elem.get('data-lazy')
                        if src and not any(skip in src.lower() for skip in ['icon', 'logo', 'banner', 'btn', 'sprite', '1x1']):
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif not src.startswith('http'):
                                src = urljoin(url, src)
                            result['thumbnail'] = src
                            break
                except:
                    continue

            # 품절 상태 확인
            page_text_lower = soup.get_text().lower()
            soldout_keywords = ['품절', '일시품절', 'sold out', 'out of stock', '재고없음', '재고 없음']
            for keyword in soldout_keywords:
                if keyword in page_text_lower:
                    result['status'] = 'out_of_stock'
                    break

        except Exception as e:
            print(f"[CSS] 오류: {e}")

        return result
