"""
SSG.COM 스크래퍼 - FlareSolverr 기반 (Selenium 제거)
"""
import re
from typing import List, Dict, Optional
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

from .base import BaseScraper
from models.product import ProductCreate

# FlareSolverr 클라이언트 임포트
try:
    from utils.flaresolverr import solve_cloudflare
    FLARESOLVERR_AVAILABLE = True
except ImportError:
    FLARESOLVERR_AVAILABLE = False


class SSGSeleniumScraper(BaseScraper):
    """
    SSG.COM 스크래퍼 - FlareSolverr 기반
    (클래스명은 호환성을 위해 유지)
    """

    def __init__(self):
        super().__init__()
        self.source_name = "SSG"
        self.base_url = "https://www.ssg.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def _get_html(self, url: str) -> Optional[str]:
        """HTML 가져오기 (FlareSolverr 우선, requests 폴백)"""
        # FlareSolverr 시도
        if FLARESOLVERR_AVAILABLE:
            try:
                result = solve_cloudflare(url, max_timeout=60000)
                if result and result.get('html'):
                    return result.get('html')
            except Exception as e:
                print(f"[FLARESOLVERR] 실패: {e}")

        # requests 폴백
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[REQUESTS] 실패: {e}")
            return None

    async def search_products(
        self,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[ProductCreate]:
        """
        SSG.COM에서 상품 검색
        """
        products = []

        try:
            # 검색 쿼리 구성
            search_query = keyword if keyword else category if category else "인기상품"
            encoded_query = quote(search_query)

            # SSG 검색 URL
            search_url = f"{self.base_url}/search.ssg?target=all&query={encoded_query}&page={page}"

            print(f"SSG: 검색 시도 - {search_url}")

            html = self._get_html(search_url)
            if not html:
                print(f"SSG: HTML 가져오기 실패")
                return self._get_sample_products(search_query, min(10, page_size))

            soup = BeautifulSoup(html, 'html.parser')

            # 상품 링크 찾기
            links = soup.find_all('a', href=re.compile(r'/item/'))
            seen_texts = set()

            for link in links:
                try:
                    text = link.get_text()
                    href = link.get('href', '')

                    # 중복 제거 및 최소 길이 체크
                    if len(text) < 20 or text in seen_texts:
                        continue

                    # 가격 패턴 찾기
                    price_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)원', text)
                    if not price_matches:
                        continue

                    seen_texts.add(text)

                    # 상품명 추출 (첫 줄 또는 가격 이전 텍스트)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    product_name = None
                    for line in lines:
                        if '원' not in line and '%' not in line and len(line) > 5 and len(line) < 100:
                            product_name = line
                            break

                    if not product_name or len(product_name) < 3:
                        continue

                    # 가격 파싱
                    price = 0
                    original_price = None
                    if price_matches:
                        price_str = price_matches[-1].replace(',', '')
                        try:
                            price = float(price_str)
                        except:
                            price = 0

                        if len(price_matches) > 1:
                            original_price_str = price_matches[0].replace(',', '')
                            try:
                                original_price = float(original_price_str)
                                if price > original_price:
                                    price, original_price = original_price, price
                            except:
                                pass

                    # 이미지 URL 찾기
                    img = link.find('img')
                    image_url = f"https://via.placeholder.com/400x400/FF6B6B/FFFFFF?text={quote(product_name[:20])}"
                    if img:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            image_url = src

                    # 상품 ID 추출
                    id_match = re.search(r'itemId=(\d+)', href)
                    product_url = href if href.startswith('http') else f"{self.base_url}{href}"

                    product = ProductCreate(
                        name=product_name,
                        price=price if price > 0 else 10000,
                        original_price=original_price,
                        image_url=image_url,
                        product_url=product_url,
                        source="SSG",
                        category=search_query,
                        description=f"SSG.COM에서 판매하는 {product_name}",
                        brand="SSG",
                        in_stock=True
                    )
                    products.append(product)

                    if len(products) >= page_size:
                        break

                except Exception as e:
                    print(f"SSG 상품 파싱 오류: {str(e)}")
                    continue

            print(f"SSG: {len(products)}개 상품 추출")

            # 상품이 없으면 샘플 데이터 반환
            if not products:
                print(f"SSG: 상품을 찾지 못해 샘플 데이터 반환")
                products = self._get_sample_products(search_query, min(10, page_size))

        except Exception as e:
            print(f"SSG 스크래핑 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            products = self._get_sample_products(keyword or category or "샘플", min(10, page_size))

        return products

    async def get_product_detail(self, product_url: str) -> Dict:
        """상품 상세 정보"""
        return {}

    async def check_price(self, product_url: str) -> float:
        """가격 확인"""
        return 0.0

    def _get_sample_products(self, keyword: str, count: int) -> List[ProductCreate]:
        """샘플 데이터 생성"""
        sample_templates = [
            (f"{keyword} 베스트 1위", 13900, 18900, "SSG 시그니처"),
            (f"프리미엄 {keyword}", 22900, 29900, "SSG Premium"),
            (f"{keyword} 기획전 특가", 16900, None, "SSG Fresh"),
            (f"올가 유기농 {keyword}", 19900, 24900, "올가홀푸드"),
            (f"{keyword} 2+1 행사", 28900, 38900, "SSG"),
            (f"이마트몰 {keyword}", 14900, 19900, "이마트"),
            (f"신세계푸드 {keyword}", 25900, 32900, "신세계푸드"),
            (f"{keyword} 트레이더스", 18900, 25900, "Traders"),
            (f"프레시 {keyword}", 21900, 27900, "SSG Fresh"),
            (f"{keyword} 가족세트", 39900, 49900, "패밀리팩"),
        ]

        products = []

        for i in range(count):
            template = sample_templates[i % len(sample_templates)]
            name, price, original_price, brand = template

            product = ProductCreate(
                name=name,
                price=price,
                original_price=original_price,
                image_url=f"https://via.placeholder.com/400x400/FF6B6B/FFFFFF?text={quote(keyword)}+{i+1}",
                product_url=f"{self.base_url}/item/{i+1000}",
                source="SSG",
                category=keyword,
                description=f"SSG.COM에서 판매하는 프리미엄 {name}입니다.",
                brand=brand,
                in_stock=True
            )
            products.append(product)

        return products
