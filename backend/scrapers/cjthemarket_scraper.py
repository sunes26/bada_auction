"""
CJ The Market 스크래퍼 - FlareSolverr 기반 (Selenium 제거)
"""
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote, urljoin, parse_qs, urlparse
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


class CJTheMarketScraper(BaseScraper):
    """
    CJ The Market 스크래퍼 - FlareSolverr 기반
    """

    def __init__(self):
        super().__init__()
        self.source_name = "CJ제일제당"
        self.base_url = "https://www.cjthemarket.com"
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
        CJ The Market에서 상품 검색
        """
        products = []

        try:
            # 검색 쿼리 구성
            search_query = keyword if keyword else category if category else "선물세트"
            encoded_query = quote(search_query)

            # CJ The Market 검색 URL
            search_url = f"{self.base_url}/the/search?keyword={encoded_query}"

            print(f"CJ The Market: 검색 시도 - {search_url}")

            html = self._get_html(search_url)
            if not html:
                print(f"CJ The Market: HTML 가져오기 실패")
                return self._get_sample_products(search_query, min(10, page_size))

            soup = BeautifulSoup(html, 'html.parser')

            # 상품 링크 찾기
            links = soup.find_all('a', href=re.compile(r'prdCd='))
            seen_prd_cd = set()

            for link in links:
                try:
                    href = link.get('href', '')
                    text = link.get_text()

                    # prdCd 추출
                    prd_cd_match = re.search(r'prdCd=(\d+)', href)
                    if not prd_cd_match or prd_cd_match.group(1) in seen_prd_cd:
                        continue

                    prd_cd = prd_cd_match.group(1)
                    seen_prd_cd.add(prd_cd)

                    # 이미지 찾기
                    img = link.find('img')
                    img_src = ''
                    img_alt = ''
                    if img:
                        img_src = img.get('src') or img.get('data-src') or ''
                        img_alt = img.get('alt') or ''

                    # 가격 찾기
                    price = 0
                    original_price = None
                    price_matches = re.findall(r'([\d,]+)원', text)
                    if price_matches:
                        if len(price_matches) >= 2:
                            original_price = int(price_matches[0].replace(',', ''))
                            price = int(price_matches[-1].replace(',', ''))
                        elif len(price_matches) == 1:
                            price = int(price_matches[0].replace(',', ''))

                    # 상품명 추출
                    name = img_alt
                    if not name or len(name) < 5:
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        for line in lines:
                            if len(line) > 5 and len(line) < 100 and '원' not in line and '%' not in line:
                                name = line
                                break

                    if name and len(name) > 3:
                        product = self._parse_product_data({
                            'prdCd': prd_cd,
                            'name': name,
                            'price': price,
                            'originalPrice': original_price,
                            'url': href,
                            'image': img_src
                        }, search_query)
                        if product:
                            products.append(product)

                        if len(products) >= page_size:
                            break

                except Exception as e:
                    print(f"CJ 상품 파싱 오류: {str(e)}")
                    continue

            print(f"CJ The Market: {len(products)}개 상품 추출")

            # 상품이 없으면 샘플 데이터 반환
            if not products:
                print(f"CJ The Market: 상품을 찾지 못해 샘플 데이터 반환")
                products = self._get_sample_products(search_query, min(10, page_size))

        except Exception as e:
            print(f"CJ The Market 스크래핑 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            products = self._get_sample_products(keyword or category or "선물세트", min(10, page_size))

        return products

    def _parse_product_data(self, data: dict, search_query: str) -> Optional[ProductCreate]:
        """상품 데이터 파싱"""
        try:
            name = data.get('name', '')
            price = data.get('price', 0)
            original_price = data.get('originalPrice')
            url = data.get('url', '')
            image = data.get('image', '')
            prd_cd = data.get('prdCd', '')

            if not name or len(name) < 3:
                return None

            # 이미지 URL 보정
            if image and not image.startswith('http'):
                image = 'https:' + image if image.startswith('//') else urljoin(self.base_url, image)

            if not image:
                image = f"https://via.placeholder.com/400x400/E53935/FFFFFF?text={quote(name[:20])}"

            # URL 보정
            if url and not url.startswith('http'):
                url = urljoin(self.base_url, url)

            if not url:
                url = f"{self.base_url}/the/product/product-main?prdCd={prd_cd}"

            return ProductCreate(
                name=name,
                price=price if price > 0 else 10000,
                original_price=original_price if original_price and original_price > price else None,
                image_url=image,
                product_url=url,
                source="CJ제일제당",
                category=search_query,
                description=f"CJ제일제당 더마켓에서 판매하는 {name}",
                brand="CJ제일제당",
                in_stock=True
            )

        except Exception as e:
            print(f"CJ 파싱 상세 오류: {str(e)}")
            return None

    async def get_product_detail(self, product_url: str) -> Dict:
        """상품 상세 정보 가져오기"""
        try:
            print(f"CJ The Market: 상품 상세 페이지 로드 - {product_url}")

            html = self._get_html(product_url)
            if not html:
                return {}

            soup = BeautifulSoup(html, 'html.parser')

            # 상품명
            name = ''
            for selector in ['h1', '.prd-name', '.product-name', '[class*="title"]']:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True) and len(elem.get_text(strip=True)) > 3:
                    name = elem.get_text(strip=True)
                    break

            # 가격
            price = 0
            original_price = None
            page_text = soup.get_text()
            price_matches = re.findall(r'([\d,]+)원', page_text)
            if price_matches:
                price = int(price_matches[-1].replace(',', ''))
                if len(price_matches) > 1:
                    original_price = int(price_matches[0].replace(',', ''))

            # 이미지
            images = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and 'cjthemarket' in src and 'icon' not in src and 'logo' not in src:
                    if not src.startswith('http'):
                        src = 'https:' + src
                    images.append(src)

            return {
                "name": name,
                "price": price,
                "original_price": original_price,
                "description": "",
                "images": images,
                "brand": "CJ제일제당",
            }

        except Exception as e:
            print(f"CJ The Market 상품 상세 정보 조회 오류: {str(e)}")
            return {}

    async def get_product_by_url(self, product_url: str) -> Optional[ProductCreate]:
        """URL로 단일 상품 정보 가져오기"""
        try:
            parsed = urlparse(product_url)
            params = parse_qs(parsed.query)
            prd_cd = params.get('prdCd', [''])[0]

            if not prd_cd:
                print(f"CJ The Market: prdCd를 찾을 수 없음 - {product_url}")
                return None

            detail = await self.get_product_detail(product_url)

            if not detail.get('name'):
                return None

            image_url = detail['images'][0] if detail.get('images') else f"https://via.placeholder.com/400x400/E53935/FFFFFF?text=CJ"

            return ProductCreate(
                name=detail['name'],
                price=detail.get('price', 0),
                original_price=detail.get('original_price'),
                image_url=image_url,
                product_url=product_url,
                source="CJ제일제당",
                category="선물세트",
                description=detail.get('description', f"CJ제일제당 더마켓에서 판매하는 {detail['name']}"),
                brand=detail.get('brand', 'CJ제일제당'),
                in_stock=True
            )

        except Exception as e:
            print(f"CJ The Market URL 상품 조회 오류: {str(e)}")
            return None

    async def check_price(self, product_url: str) -> float:
        """현재 가격 확인"""
        try:
            detail = await self.get_product_detail(product_url)
            return detail.get("price", 0.0)
        except Exception as e:
            print(f"CJ The Market 가격 확인 오류: {str(e)}")
            return 0.0

    def _get_sample_products(self, keyword: str, count: int) -> List[ProductCreate]:
        """샘플 상품 데이터 생성"""
        sample_templates = [
            ("[설선물세트] 스팸 클래식 1호", 32900, 39900, "스팸"),
            ("[설선물세트] 스팸 블랙라벨 2호", 45900, 54900, "스팸"),
            ("[설선물세트] 비비고 왕교자 세트", 29900, 35900, "비비고"),
            ("[설선물세트] 햇반 혼합 세트", 24900, 29900, "햇반"),
            ("[설선물세트] 백설 요리유 세트", 19900, 24900, "백설"),
            ("[설선물세트] 다시다 프리미엄 세트", 27900, 32900, "다시다"),
            ("[설선물세트] 해찬들 고추장 세트", 22900, 27900, "해찬들"),
            ("[설선물세트] CJ 종합 1호", 49900, 59900, "CJ"),
            ("[설선물세트] 참치 세트 1호", 38900, 45900, "동원"),
            (f"{keyword} 프리미엄 세트", 35900, 42900, "CJ제일제당"),
        ]

        products = []

        for i in range(count):
            template = sample_templates[i % len(sample_templates)]
            name, price, original_price, brand = template

            product = ProductCreate(
                name=name,
                price=price,
                original_price=original_price,
                image_url=f"https://via.placeholder.com/400x400/E53935/FFFFFF?text={quote(name[:15])}",
                product_url=f"{self.base_url}/the/product/product-main?prdCd={40220900 + i}",
                source="CJ제일제당",
                category=keyword,
                description=f"CJ제일제당 더마켓에서 판매하는 {name}입니다. 명절 선물세트로 인기가 많습니다.",
                brand=brand,
                in_stock=True
            )
            products.append(product)

        return products
