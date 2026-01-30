"""
네이버 스마트스토어 상품 정보 추출 스크래퍼

네이버 스마트스토어 상품 페이지에서 상품명, 가격, 재고 상태, 썸네일 자동 추출
⚠️  주의: 스마트스토어는 JavaScript 동적 로딩이 많아 Selenium 사용 권장
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import json
from logger import get_logger

logger = get_logger(__name__)


class SmartstoreScraper:
    """네이버 스마트스토어 상품 정보 추출"""

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
            use_selenium: Selenium 사용 여부 (동적 로딩 대응)

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
        if use_selenium:
            return self._extract_with_selenium(product_url)
        else:
            return self._extract_with_requests(product_url)

    def _extract_with_requests(self, product_url: str) -> Dict:
        """
        requests로 기본 정보 추출 (제한적)

        스마트스토어는 JavaScript 렌더링이 많아 완전한 정보 추출 불가능
        """
        try:
            logger.info(f"스마트스토어 상품 정보 추출 시작 (requests): {product_url}")

            response = requests.get(product_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. 메타 태그에서 기본 정보 추출 (og 태그)
            product_name = self._extract_from_meta(soup, 'og:title')
            thumbnail = self._extract_from_meta(soup, 'og:image')
            description = self._extract_from_meta(soup, 'og:description')

            # 2. JSON-LD 스키마에서 가격 추출 시도
            price_info = self._extract_from_json_ld(soup)

            # 3. 재고 상태는 동적 로딩으로 추출 어려움
            status = "unknown"  # Selenium 필요

            logger.info(f"스마트스토어 기본 정보 추출: {product_name}")

            return {
                "success": True,
                "product_name": product_name,
                "price": price_info.get('price'),
                "original_price": price_info.get('original_price'),
                "status": status,
                "thumbnail": thumbnail,
                "source": "smartstore",
                "note": "동적 로딩으로 일부 정보만 추출 가능. Selenium 사용 권장."
            }

        except Exception as e:
            logger.error(f"스마트스토어 상품 정보 추출 실패 (requests): {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": "smartstore",
                "note": "Selenium으로 재시도 권장"
            }

    def _extract_with_selenium(self, product_url: str) -> Dict:
        """
        Selenium으로 완전한 정보 추출

        JavaScript 렌더링 대응
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time

            logger.info(f"스마트스토어 상품 정보 추출 시작 (Selenium): {product_url}")

            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')

            driver = webdriver.Chrome(options=chrome_options)

            try:
                driver.get(product_url)

                # JavaScript 렌더링 대기 (최대 10초)
                time.sleep(3)

                # 상품명 추출
                product_name = self._selenium_extract_product_name(driver)

                # 가격 추출
                price_info = self._selenium_extract_price(driver)

                # 재고 상태 체크
                status = self._selenium_check_stock(driver)

                # 썸네일 추출
                thumbnail = self._selenium_extract_thumbnail(driver)

                logger.info(f"스마트스토어 Selenium 추출 성공: {product_name}, 가격: {price_info.get('price')}")

                return {
                    "success": True,
                    "product_name": product_name,
                    "price": price_info.get('price'),
                    "original_price": price_info.get('original_price'),
                    "status": status,
                    "thumbnail": thumbnail,
                    "source": "smartstore"
                }

            finally:
                driver.quit()

        except ImportError:
            logger.error("Selenium이 설치되지 않았습니다")
            return {
                "success": False,
                "error": "Selenium이 설치되지 않았습니다. pip install selenium 필요",
                "source": "smartstore"
            }

        except Exception as e:
            logger.error(f"스마트스토어 Selenium 추출 실패: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": "smartstore"
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

    def _selenium_extract_product_name(self, driver) -> Optional[str]:
        """Selenium으로 상품명 추출"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # 상품명 요소 대기 및 추출
            name_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h3.bd_tit, .product_title, h1._2-I30XS1lA'))
            )
            return name_element.text.strip()

        except Exception as e:
            logger.warning(f"스마트스토어 상품명 추출 실패: {e}")
            return None

    def _selenium_extract_price(self, driver) -> Dict:
        """Selenium으로 가격 추출"""
        try:
            from selenium.webdriver.common.by import By

            price = None
            original_price = None

            # 판매가 추출
            price_elements = driver.find_elements(By.CSS_SELECTOR, '.price_num, .product_price, ._1LY7DqCnwR')
            if price_elements:
                price_text = price_elements[0].text.strip()
                price_text = re.sub(r'[^\d]', '', price_text)
                if price_text:
                    price = int(price_text)

            # 정가 추출
            original_elements = driver.find_elements(By.CSS_SELECTOR, '.origin_price, .product_origin_price, del.price')
            if original_elements:
                original_text = original_elements[0].text.strip()
                original_text = re.sub(r'[^\d]', '', original_text)
                if original_text:
                    original_price = int(original_text)

            return {"price": price, "original_price": original_price}

        except Exception as e:
            logger.warning(f"스마트스토어 가격 추출 실패: {e}")
            return {"price": None, "original_price": None}

    def _selenium_check_stock(self, driver) -> str:
        """Selenium으로 재고 상태 체크"""
        try:
            from selenium.webdriver.common.by import By

            # 품절 키워드 체크
            page_source = driver.page_source.lower()
            out_of_stock_keywords = ['품절', '일시품절', '재고없음', '판매종료']

            for keyword in out_of_stock_keywords:
                if keyword in page_source:
                    return "out_of_stock"

            # 품절 버튼 체크
            sold_out_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '품절')]")
            if sold_out_buttons:
                return "out_of_stock"

            return "available"

        except Exception as e:
            logger.warning(f"스마트스토어 재고 상태 체크 실패: {e}")
            return "unknown"

    def _selenium_extract_thumbnail(self, driver) -> Optional[str]:
        """Selenium으로 썸네일 추출"""
        try:
            from selenium.webdriver.common.by import By

            # 썸네일 이미지 요소
            img_elements = driver.find_elements(By.CSS_SELECTOR, '.product_img img, .image_thumb img, ._25CKxIKjAk img')
            if img_elements:
                thumbnail_url = img_elements[0].get_attribute('src')
                if thumbnail_url:
                    return thumbnail_url

            return None

        except Exception as e:
            logger.warning(f"스마트스토어 썸네일 추출 실패: {e}")
            return None


if __name__ == "__main__":
    # 테스트용
    scraper = SmartstoreScraper()

    # 테스트 URL (실제 스마트스토어 상품 URL로 교체)
    test_url = "https://smartstore.naver.com/your-store/products/1234567890"

    print("스마트스토어 스크래퍼 테스트")
    print("=" * 50)

    # 1. requests 테스트
    print("\n[1] requests 방식 (기본 정보만):")
    result1 = scraper.extract_product_info(test_url, use_selenium=False)
    print(f"결과: {result1}")

    # 2. Selenium 테스트
    print("\n[2] Selenium 방식 (완전한 정보):")
    result2 = scraper.extract_product_info(test_url, use_selenium=True)
    print(f"결과: {result2}")
