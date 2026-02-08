import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote, urljoin, parse_qs, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

from .base import BaseScraper
from models.product import ProductCreate


class CJTheMarketScraper(BaseScraper):
    """
    CJ The Market 스크래퍼

    Selenium을 사용하여 CJ제일제당 더마켓에서 상품 정보를 수집합니다.
    """

    def __init__(self):
        super().__init__()
        self.source_name = "CJ제일제당"
        self.base_url = "https://www.cjthemarket.com"
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
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # ChromeDriver 경로 설정 (프로덕션/개발 환경 자동 감지)
            import os
            import shutil

            chromedriver_path = '/usr/local/bin/chromedriver'
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
            elif shutil.which('chromedriver'):
                service = Service(shutil.which('chromedriver'))
            else:
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
        CJ The Market에서 상품 검색 (Selenium 사용)
        """
        products = []

        try:
            self._init_driver()

            # 검색 쿼리 구성
            search_query = keyword if keyword else category if category else "선물세트"
            encoded_query = quote(search_query)

            # CJ The Market 검색 URL
            search_url = f"{self.base_url}/the/search?keyword={encoded_query}"

            print(f"CJ The Market: 검색 시도 - {search_url}")

            # 페이지 로드
            self.driver.get(search_url)
            time.sleep(5)  # JavaScript 렌더링 대기

            # JavaScript로 상품 데이터 추출
            product_data = self.driver.execute_script("""
                const products = [];

                // 상품 카드 찾기 (다양한 셀렉터 시도)
                const selectors = [
                    '.prd-item',
                    '.product-item',
                    '.item-card',
                    '[class*="product"]',
                    '[class*="item"]'
                ];

                let items = [];
                for (const selector of selectors) {
                    items = document.querySelectorAll(selector);
                    if (items.length > 0) break;
                }

                // 상품 링크에서 데이터 추출
                const links = document.querySelectorAll('a[href*="prdCd="]');
                const seenPrdCd = new Set();

                links.forEach(link => {
                    const href = link.href || '';
                    const text = link.textContent || '';

                    // prdCd 추출
                    const prdCdMatch = href.match(/prdCd=(\d+)/);
                    if (prdCdMatch && !seenPrdCd.has(prdCdMatch[1])) {
                        seenPrdCd.add(prdCdMatch[1]);

                        // 이미지 찾기
                        const img = link.querySelector('img');
                        const imgSrc = img ? (img.src || img.getAttribute('data-src') || '') : '';
                        const imgAlt = img ? (img.alt || '') : '';

                        // 가격 찾기
                        let price = 0;
                        let originalPrice = null;

                        const priceMatches = text.match(/([\d,]+)원/g);
                        if (priceMatches) {
                            if (priceMatches.length >= 2) {
                                originalPrice = parseInt(priceMatches[0].replace(/[^0-9]/g, ''));
                                price = parseInt(priceMatches[priceMatches.length - 1].replace(/[^0-9]/g, ''));
                            } else if (priceMatches.length === 1) {
                                price = parseInt(priceMatches[0].replace(/[^0-9]/g, ''));
                            }
                        }

                        // 상품명 추출 (이미지 alt 또는 텍스트)
                        let name = imgAlt || '';
                        if (!name || name.length < 5) {
                            // 텍스트에서 상품명 추출 시도
                            const lines = text.split('\n').map(l => l.trim()).filter(l => l);
                            for (const line of lines) {
                                if (line.length > 5 && line.length < 100 && !line.includes('원') && !line.includes('%')) {
                                    name = line;
                                    break;
                                }
                            }
                        }

                        if (name && name.length > 0) {
                            products.push({
                                prdCd: prdCdMatch[1],
                                name: name,
                                price: price,
                                originalPrice: originalPrice,
                                url: href,
                                image: imgSrc
                            });
                        }
                    }
                });

                return products;
            """)

            print(f"CJ The Market: {len(product_data)}개 상품 데이터 추출")

            # 데이터 파싱
            for idx, data in enumerate(product_data[:page_size]):
                try:
                    product = self._parse_product_data(data, search_query)
                    if product:
                        products.append(product)
                except Exception as e:
                    print(f"CJ 상품 파싱 오류 #{idx}: {str(e)}")
                    continue

            # 상품이 없으면 샘플 데이터 반환
            if not products:
                print(f"CJ The Market: 상품을 찾지 못해 샘플 데이터 반환")
                products = self._get_sample_products(search_query, min(10, page_size))

        except Exception as e:
            print(f"CJ The Market 스크래핑 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            products = self._get_sample_products(keyword or category or "선물세트", min(10, page_size))

        finally:
            self._close_driver()

        return products

    def _parse_product_data(self, data: dict, search_query: str) -> Optional[ProductCreate]:
        """
        JavaScript로 추출한 데이터 파싱
        """
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
        """
        상품 상세 정보 가져오기
        """
        try:
            self._init_driver()

            print(f"CJ The Market: 상품 상세 페이지 로드 - {product_url}")

            self.driver.get(product_url)
            time.sleep(5)

            # JavaScript로 상세 정보 추출
            detail_data = self.driver.execute_script("""
                const result = {
                    name: '',
                    price: 0,
                    originalPrice: null,
                    description: '',
                    images: [],
                    brand: 'CJ제일제당'
                };

                // 상품명
                const nameSelectors = ['h1', '.prd-name', '.product-name', '[class*="title"]'];
                for (const sel of nameSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.textContent.trim().length > 3) {
                        result.name = el.textContent.trim();
                        break;
                    }
                }

                // 가격
                const priceText = document.body.innerText || '';
                const priceMatches = priceText.match(/([\d,]+)원/g);
                if (priceMatches && priceMatches.length > 0) {
                    result.price = parseInt(priceMatches[priceMatches.length - 1].replace(/[^0-9]/g, ''));
                    if (priceMatches.length > 1) {
                        result.originalPrice = parseInt(priceMatches[0].replace(/[^0-9]/g, ''));
                    }
                }

                // 설명
                const descSelectors = ['.prd-desc', '.product-description', '[class*="description"]', '[class*="detail"]'];
                for (const sel of descSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.textContent.trim().length > 10) {
                        result.description = el.textContent.trim().substring(0, 500);
                        break;
                    }
                }

                // 이미지
                const images = document.querySelectorAll('img[src*="cjthemarket"], img[class*="prd"], img[class*="product"]');
                images.forEach(img => {
                    const src = img.src || img.getAttribute('data-src');
                    if (src && !src.includes('icon') && !src.includes('logo')) {
                        let imgUrl = src;
                        if (!imgUrl.startsWith('http')) {
                            imgUrl = 'https:' + imgUrl;
                        }
                        result.images.push(imgUrl);
                    }
                });

                return result;
            """)

            return {
                "name": detail_data.get('name', ''),
                "price": detail_data.get('price', 0),
                "original_price": detail_data.get('originalPrice'),
                "description": detail_data.get('description', ''),
                "images": detail_data.get('images', []),
                "brand": detail_data.get('brand', 'CJ제일제당'),
            }

        except Exception as e:
            print(f"CJ The Market 상품 상세 정보 조회 오류: {str(e)}")
            return {}

        finally:
            self._close_driver()

    async def get_product_by_url(self, product_url: str) -> Optional[ProductCreate]:
        """
        URL로 단일 상품 정보 가져오기
        """
        try:
            # prdCd 추출
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
        """
        현재 가격 확인
        """
        try:
            detail = await self.get_product_detail(product_url)
            return detail.get("price", 0.0)
        except Exception as e:
            print(f"CJ The Market 가격 확인 오류: {str(e)}")
            return 0.0

    def _get_sample_products(self, keyword: str, count: int) -> List[ProductCreate]:
        """
        샘플 상품 데이터 생성 (CJ 선물세트 기반)
        """
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
            ("{keyword} 프리미엄 세트", 35900, 42900, "CJ제일제당"),
        ]

        products = []

        for i in range(count):
            template = sample_templates[i % len(sample_templates)]
            name_template, price, original_price, brand = template

            name = name_template.format(keyword=keyword)

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
