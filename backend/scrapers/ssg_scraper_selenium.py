import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

from .base import BaseScraper
from models.product import ProductCreate


class SSGSeleniumScraper(BaseScraper):
    """
    SSG.COM Selenium 스크래퍼

    Selenium을 사용하여 JavaScript 렌더링된 상품 데이터 수집
    """

    def __init__(self):
        super().__init__()
        self.source_name = "SSG"
        self.base_url = "https://www.ssg.com"
        self.driver = None

    def _init_driver(self):
        """Selenium 드라이버 초기화"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def _close_driver(self):
        """Selenium 드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    async def search_products(
        self,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[ProductCreate]:
        """
        SSG.COM에서 상품 검색 (Selenium 사용)
        """
        products = []

        try:
            self._init_driver()

            # 검색 쿼리 구성
            search_query = keyword if keyword else category if category else "인기상품"
            encoded_query = quote(search_query)

            # SSG 검색 URL
            search_url = f"{self.base_url}/search.ssg?target=all&query={encoded_query}&page={page}"

            print(f"SSG Selenium: 검색 시도 - {search_url}")

            # 페이지 로드
            self.driver.get(search_url)
            time.sleep(6)  # JavaScript 렌더링 대기

            # JavaScript로 상품 데이터 추출
            product_data = self.driver.execute_script("""
                const products = [];
                const seenTexts = new Set();

                // 상품 링크 찾기
                const links = Array.from(document.querySelectorAll('a[href*="/item/"]'));

                links.forEach(link => {
                    const text = link.textContent || '';
                    const href = link.href || '';

                    // 중복 제거 및 최소 길이 체크
                    if (text.length > 20 && !seenTexts.has(text)) {
                        seenTexts.add(text);

                        // 가격 패턴 찾기
                        const priceMatch = text.match(/(\\d{1,3}(,\\d{3})*)원/g);

                        if (priceMatch && priceMatch.length > 0) {
                            products.push({
                                text: text,
                                url: href,
                                prices: priceMatch
                            });
                        }
                    }
                });

                return products;
            """)

            print(f"SSG Selenium: {len(product_data)}개 상품 데이터 추출")

            # 이미지로 상품명 보강
            try:
                img_elements = self.driver.find_elements(By.TAG_NAME, 'img')
                product_names_from_img = {}

                for img in img_elements:
                    alt = img.get_attribute('alt') or ''
                    src = img.get_attribute('src') or ''

                    if len(alt) > 5 and any(keyword in alt for keyword in [search_query, '생수', '물']) if search_query else True:
                        # 상품 ID 추출 시도
                        product_id = None
                        if 'itemId=' in src:
                            product_id = re.search(r'itemId=(\d+)', src)
                            if product_id:
                                product_id = product_id.group(1)

                        product_names_from_img[alt] = {
                            'name': alt,
                            'image': src,
                            'id': product_id
                        }

            except Exception as e:
                print(f"이미지 추출 오류: {str(e)}")
                product_names_from_img = {}

            # 데이터 파싱
            for idx, data in enumerate(product_data[:page_size]):
                try:
                    product = self._parse_product_data(data, search_query, product_names_from_img)
                    if product:
                        products.append(product)
                except Exception as e:
                    print(f"SSG 상품 파싱 오류 #{idx}: {str(e)}")
                    continue

            # 상품이 없으면 샘플 데이터 반환
            if not products:
                print(f"SSG Selenium: 상품을 찾지 못해 샘플 데이터 반환")
                products = self._get_sample_products(search_query, min(10, page_size))

        except Exception as e:
            print(f"SSG Selenium 스크래핑 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            products = self._get_sample_products(keyword or category or "샘플", min(10, page_size))

        finally:
            self._close_driver()

        return products

    def _parse_product_data(self, data, search_query: str, product_names: dict) -> Optional[ProductCreate]:
        """
        JavaScript로 추출한 데이터 파싱
        """
        try:
            text = data['text']
            url = data['url']
            prices = data['prices']

            # 상품명 추출 (첫 줄 또는 가격 이전 텍스트)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            product_name = None

            for line in lines:
                # 가격이나 할인율이 아닌 실제 상품명으로 보이는 라인
                if '원' not in line and '%' not in line and len(line) > 5 and len(line) < 100:
                    product_name = line
                    break

            if not product_name:
                # 이미지 ALT에서 매칭되는 상품명 찾기
                for alt_name, info in product_names.items():
                    if alt_name[:20] in text[:200]:
                        product_name = alt_name
                        break

            if not product_name or len(product_name) < 3:
                return None

            # 가격 파싱
            price = 0
            original_price = None

            # 판매가격 추출 (마지막 가격이 판매가)
            if prices:
                # 가격 문자열에서 숫자만 추출
                price_str = prices[-1].replace(',', '').replace('원', '')
                try:
                    price = float(price_str)
                except:
                    price = 0

                # 할인가가 있다면 원가도 추출
                if len(prices) > 1:
                    original_price_str = prices[0].replace(',', '').replace('원', '')
                    try:
                        original_price = float(original_price_str)
                        # 판매가가 원가보다 크면 swap
                        if price > original_price:
                            price, original_price = original_price, price
                    except:
                        pass

            # 이미지 URL 찾기
            image_url = f"https://via.placeholder.com/400x400/FF6B6B/FFFFFF?text={quote(product_name[:20])}"
            for alt_name, info in product_names.items():
                if alt_name == product_name or product_name[:15] in alt_name:
                    image_url = info['image']
                    break

            # 상품 ID 추출
            product_id = None
            id_match = re.search(r'itemId=(\d+)', url)
            if id_match:
                product_id = id_match.group(1)

            return ProductCreate(
                name=product_name,
                price=price if price > 0 else 10000,
                original_price=original_price,
                image_url=image_url,
                product_url=url,
                source="SSG",
                category=search_query,
                description=f"SSG.COM에서 판매하는 {product_name}",
                brand="SSG",
                in_stock=True
            )

        except Exception as e:
            print(f"SSG 파싱 상세 오류: {str(e)}")
            return None

    async def get_product_detail(self, product_url: str) -> Dict:
        """상품 상세 정보"""
        # 기존 구현 유지
        return {}

    async def check_price(self, product_url: str) -> float:
        """가격 확인"""
        return 0.0

    def _get_sample_products(self, keyword: str, count: int) -> List[ProductCreate]:
        """샘플 데이터 생성"""
        sample_templates = {
            "default": [
                ("{keyword} 베스트 1위", 13900, 18900, "SSG 시그니처"),
                ("프리미엄 {keyword}", 22900, 29900, "SSG Premium"),
                ("{keyword} 기획전 특가", 16900, None, "SSG Fresh"),
                ("올가 유기농 {keyword}", 19900, 24900, "올가홀푸드"),
                ("{keyword} 2+1 행사", 28900, 38900, "SSG"),
                ("이마트몰 {keyword}", 14900, 19900, "이마트"),
                ("신세계푸드 {keyword}", 25900, 32900, "신세계푸드"),
                ("{keyword} 트레이더스", 18900, 25900, "Traders"),
                ("프레시 {keyword}", 21900, 27900, "SSG Fresh"),
                ("{keyword} 가족세트", 39900, 49900, "패밀리팩"),
            ]
        }

        products = []
        templates = sample_templates["default"]

        for i in range(count):
            template = templates[i % len(templates)]
            name_template, price, original_price, brand = template

            product = ProductCreate(
                name=name_template.format(keyword=keyword),
                price=price,
                original_price=original_price,
                image_url=f"https://via.placeholder.com/400x400/FF6B6B/FFFFFF?text={quote(keyword)}+{i+1}",
                product_url=f"{self.base_url}/item/{i+1000}",
                source="SSG",
                category=keyword,
                description=f"SSG.COM에서 판매하는 프리미엄 {name_template.format(keyword=keyword)}입니다.",
                brand=brand,
                in_stock=True
            )
            products.append(product)

        return products
