"""
상품 모니터링 로직
"""
import re
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from logger import get_logger

logger = get_logger(__name__)

# undetected-chromedriver (봇 감지 우회)
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False
    logger.warning("undetected-chromedriver 미설치 - 일반 selenium 사용")


class ProductMonitor:
    """상품 상태 모니터링"""

    def __init__(self):
        self.driver = None

    def _init_driver(self, use_undetected: bool = True):
        """Selenium 드라이버 초기화

        Args:
            use_undetected: 봇 감지 우회 모드 사용 여부
        """
        if self.driver is None:
            import os
            import shutil

            # undetected-chromedriver 사용 (봇 감지 우회)
            if use_undetected and UC_AVAILABLE:
                logger.info("undetected-chromedriver 사용 (봇 감지 우회)")

                options = uc.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')

                # 속도 향상 옵션
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-plugins')

                # Cloudflare 우회를 위한 추가 옵션
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-infobars')
                options.add_argument('--lang=ko-KR')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

                # headless 모드 (undetected-chromedriver v3.5+)
                options.add_argument('--headless=new')

                # ChromeDriver 경로 설정
                chromedriver_path = '/usr/local/bin/chromedriver'
                driver_executable_path = None

                if os.path.exists(chromedriver_path):
                    driver_executable_path = chromedriver_path
                    logger.info("프로덕션 ChromeDriver 사용")
                elif shutil.which('chromedriver'):
                    driver_executable_path = shutil.which('chromedriver')
                    logger.info(f"시스템 ChromeDriver 사용: {driver_executable_path}")

                # Chrome 버전 자동 감지
                try:
                    import subprocess
                    if os.name == 'nt':  # Windows
                        result = subprocess.run(
                            ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                            capture_output=True, text=True
                        )
                        if result.returncode == 0:
                            version_match = re.search(r'(\d+)\.', result.stdout)
                            chrome_version = int(version_match.group(1)) if version_match else None
                        else:
                            chrome_version = None
                    else:  # Linux/Docker
                        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
                        version_match = re.search(r'(\d+)\.', result.stdout)
                        chrome_version = int(version_match.group(1)) if version_match else None

                    logger.info(f"감지된 Chrome 버전: {chrome_version}")
                except Exception as e:
                    logger.warning(f"Chrome 버전 감지 실패: {e}")
                    chrome_version = None

                # undetected-chromedriver 초기화
                self.driver = uc.Chrome(
                    options=options,
                    driver_executable_path=driver_executable_path,
                    use_subprocess=True,
                    version_main=chrome_version,
                )

                # 타임아웃 설정
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(5)

                logger.info("undetected-chromedriver 초기화 완료")
                return

            # 일반 selenium 사용 (fallback)
            logger.info("일반 selenium 사용")

            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            # 속도 향상 옵션
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.page_load_strategy = 'eager'

            # User Agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # 자동화 감지 방지
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')

            # ChromeDriver 경로 설정
            chromedriver_path = '/usr/local/bin/chromedriver'
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                logger.info("프로덕션 ChromeDriver 사용: /usr/local/bin/chromedriver")
            elif shutil.which('chromedriver'):
                service = Service(shutil.which('chromedriver'))
                logger.info(f"시스템 ChromeDriver 사용: {shutil.which('chromedriver')}")
            else:
                service = Service(ChromeDriverManager().install())
                logger.info("ChromeDriverManager로 자동 다운로드")

            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # 타임아웃 설정
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)

            # navigator.webdriver 속성 제거
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

    def _close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def extract_info_fast(self, product_url: str) -> Dict[str, Optional[str]]:
        """
        requests + BeautifulSoup으로 빠르게 상품 정보 추출
        성공하면 상품명, 가격, 썸네일 반환
        실패하면 None 반환하여 Selenium 폴백
        """
        try:
            print(f"[FAST] 빠른 추출 시도: {product_url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            }

            # 빠른 HTTP 요청 (Railway 환경 고려)
            response = requests.get(product_url, headers=headers, timeout=15)  # 5초 → 15초
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 상품명 추출
            product_name = None

            # 1. og:title 메타 태그 (가장 신뢰성 높음)
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                product_name = og_title['content'].strip()

            # 2. title 태그
            if not product_name:
                title_tag = soup.find('title')
                if title_tag and title_tag.string:
                    product_name = title_tag.string.strip()
                    # 사이트명 제거
                    if '|' in product_name:
                        product_name = product_name.split('|')[0].strip()
                    elif '-' in product_name:
                        product_name = product_name.split('-')[0].strip()

            # 3. 상품명 일반 선택자
            if not product_name:
                selectors = [
                    '.prod-buy-header__title',  # SSG
                    '.itemtit',  # G마켓
                    'h1[class*="prod"]',
                    'h1[class*="product"]',
                    '.product-name',
                    '.product-title',
                ]
                for selector in selectors:
                    elem = soup.select_one(selector)
                    if elem and elem.get_text(strip=True):
                        product_name = elem.get_text(strip=True)
                        break

            # 가격 추출
            price = None

            # 1. og:price 메타 태그
            og_price = soup.find('meta', property='og:price:amount')
            if og_price and og_price.get('content'):
                try:
                    price = float(og_price['content'])
                except:
                    pass

            # 2. 사이트별 가격 선택자
            if not price:
                # SSG와 11번가는 JavaScript로 렌더링되므로 Selenium 필수
                if 'ssg.com' in product_url or '11st.co.kr' in product_url:
                    # Selenium 폴백 사용 (가격 추출 skip)
                    print(f"[FAST] SKIP: SSG/11st requires Selenium for price")
                    pass
                else:
                    # 일반 선택자
                    price_selectors = [
                        '.price',
                        '[class*="price"]',
                        '.prod-price',
                        '.sale-price',
                    ]
                    for selector in price_selectors:
                        elem = soup.select_one(selector)
                        if elem:
                            price_text = elem.get_text(strip=True)
                            # 연속된 숫자만 추출 (콤마 포함, 최소 3자리 이상)
                            price_match = re.search(r'[\d,]{3,}', price_text)
                            if price_match:
                                try:
                                    price = float(price_match.group(0).replace(',', ''))
                                    if price > 100:  # 100원 이상만 유효
                                        break
                                    else:
                                        price = None
                                except:
                                    pass

            # 썸네일 추출
            thumbnail = None

            # 1. og:image 메타 태그
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                thumbnail = og_image['content']
                # 상대 URL을 절대 URL로 변환
                thumbnail = urljoin(product_url, thumbnail)

            # 2. 이미지 선택자
            if not thumbnail:
                img_selectors = [
                    '.product-image img',
                    '.prod-image img',
                    '[class*="product"][class*="img"] img',
                ]
                for selector in img_selectors:
                    elem = soup.select_one(selector)
                    if elem and elem.get('src'):
                        thumbnail = urljoin(product_url, elem['src'])
                        break

            # 상품명과 가격이 모두 추출되어야 성공
            if product_name and len(product_name) > 3:
                # SSG와 11번가는 가격이 없어도 Selenium 폴백 필요
                if 'ssg.com' in product_url or '11st.co.kr' in product_url:
                    print(f"[FAST] FALLBACK: {product_name} (SSG/11st needs Selenium for price)")
                    return None

                if price and price > 0:
                    print(f"[FAST] SUCCESS: {product_name}, Price: {price}")
                    result = {
                        'product_name': product_name,
                        'price': price,
                        'thumbnail': thumbnail,
                    }
                    return result
                else:
                    # 가격이 없으면 Selenium 폴백
                    print(f"[FAST] FALLBACK: Price not found")
                    return None
            else:
                print(f"[FAST] FAIL: No product name")
                return None

        except requests.Timeout:
            print(f"[FAST] FAIL: Timeout")
            return None
        except Exception as e:
            print(f"[FAST] FAIL: {str(e)}")
            return None

    def extract_product_name(self, product_url: str, source: str) -> Optional[str]:
        """
        URL에서 상품명 추출
        """
        try:
            if not self.driver:
                self._init_driver()

            # 이미 페이지가 로드되어 있으므로 추가 로드 불필요
            # self.driver.get(product_url)
            # time.sleep는 이미 API에서 했으므로 불필요

            # JavaScript로 상품명 추출
            product_name = self.driver.execute_script("""
                // SSG 전용 선택자
                if (window.location.hostname.includes('ssg.com')) {
                    const el = document.querySelector('.cdtl_info_tit');
                    if (el) {
                        // 텍스트 정제: 여러 줄과 공백 제거
                        const lines = el.textContent.split('\\n').map(l => l.trim()).filter(l => l.length > 5 && l.length < 200);
                        // 가장 긴 줄이 상품명일 가능성
                        if (lines.length > 0) {
                            const longest = lines.reduce((a, b) => a.length > b.length ? a : b, '');
                            if (longest && longest.length > 5) {
                                return longest;
                            }
                        }
                    }
                }

                // 11번가 선택자
                if (window.location.hostname.includes('11st.co.kr')) {
                    // 페이지 타이틀에서 추출 (가장 정확)
                    const title = document.title;
                    if (title && title.length > 5) {
                        // "상품명 - 11번가" 형태에서 상품명만 추출
                        return title.split(' - ')[0].trim();
                    }
                }

                // 스마트스토어 선택자 (클래스명이 동적 생성되므로 다양한 패턴 시도)
                if (window.location.hostname.includes('smartstore.naver.com')) {
                    // 1. _copyable 클래스가 있는 h3 (가장 안정적)
                    const copyable = document.querySelector('h3._copyable');
                    if (copyable) return copyable.textContent.trim();

                    // 2. 기존 선택자
                    const el = document.querySelector('._22kNQuEXmb h3') || document.querySelector('.bd_tit');
                    if (el) return el.textContent.trim();

                    // 3. og:title 메타 태그
                    const ogTitle = document.querySelector('meta[property="og:title"]');
                    if (ogTitle && ogTitle.content) return ogTitle.content.trim();

                    // 4. 페이지 타이틀에서 추출
                    const title = document.title;
                    if (title && title.length > 5) {
                        // "상품명 : 스토어명" 형태에서 상품명만 추출
                        return title.split(' : ')[0].split(' - ')[0].trim();
                    }
                }

                // G마켓 선택자
                if (window.location.hostname.includes('gmarket.co.kr')) {
                    const el = document.querySelector('.itemtit') || document.querySelector('h1');
                    if (el) return el.textContent.trim();
                }

                // 옥션 선택자 (G마켓과 유사한 구조)
                if (window.location.hostname.includes('auction.co.kr')) {
                    const el = document.querySelector('.itemtit') ||
                              document.querySelector('.product-name') ||
                              document.querySelector('h1');
                    if (el) return el.textContent.trim();

                    // og:title 메타 태그
                    const ogTitle = document.querySelector('meta[property="og:title"]');
                    if (ogTitle && ogTitle.content) return ogTitle.content.trim();
                }

                // 홈플러스/Traders 선택자
                if (window.location.hostname.includes('homeplus.co.kr')) {
                    // 1. 페이지 타이틀에서 추출 (가장 안정적)
                    const title = document.title;
                    if (title && title.includes('|')) {
                        const productName = title.split('|')[0].trim();
                        if (productName && productName.length > 5) {
                            return productName;
                        }
                    }

                    // 2. prodNameBox 클래스의 h1 요소
                    const prodNameBox = document.querySelector('.prodNameBox');
                    if (prodNameBox) {
                        const text = prodNameBox.textContent.trim();
                        if (text && text.length > 5) {
                            return text;
                        }
                    }

                    // 3. 모든 h1 요소 확인
                    const h1Elements = document.querySelectorAll('h1');
                    for (let h1 of h1Elements) {
                        const text = h1.textContent.trim();
                        if (text.length > 10 && text.length < 200 && text !== '상품상세') {
                            return text;
                        }
                    }
                }

                // 일반적인 상품명 선택자들
                const selectors = [
                    'h1',
                    'h2',
                    '[class*="product"][class*="name"]',
                    '[class*="product"][class*="title"]',
                    '[class*="item"][class*="name"]',
                    '.product-title',
                    '.item-title'
                ];

                for (let selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    for (let el of elements) {
                        const text = el.textContent.trim();
                        // 상품명으로 추정되는 텍스트 (10자 이상, 500자 이하)
                        if (text.length > 10 && text.length < 500 && !text.includes('\\n\\n')) {
                            return text;
                        }
                    }
                }

                // title 태그에서 추출 (최후의 수단)
                const title = document.title;
                if (title && title.length > 5) {
                    // 일반적인 사이트명 제거
                    return title.split('|')[0].split('-')[0].split(':')[0].trim();
                }

                return null;
            """)

            print(f"[DEBUG] 상품명 추출 결과: {product_name}")
            logger.debug(f"추출된 상품명: {product_name}")

            # 빈 문자열이면 None 반환
            if not product_name or not product_name.strip():
                return None

            return product_name

        except Exception as e:
            print(f"[DEBUG] 상품명 추출 오류: {str(e)}")
            return None

    def check_product_status(self, product_url: str, source: str) -> Dict:
        """
        상품 페이지를 체크하여 상태 및 가격 정보 반환

        Returns:
            {
                'status': 'available' | 'out_of_stock' | 'discontinued' | 'unavailable' | 'error',
                'price': float or None,
                'original_price': float or None,
                'details': str  # 추가 정보
            }
        """
        try:
            self._init_driver()

            print(f"모니터링: {product_url}")

            # 페이지 로드
            self.driver.get(product_url)

            # 사이트별 대기 시간 조정 (최적화됨)
            if 'smartstore.naver.com' in product_url:
                time.sleep(3)  # 스마트스토어 (7초 → 3초)
            elif 'homeplus.co.kr' in product_url:
                # 홈플러스: title이 로드될 때까지 대기 (최적화)
                time.sleep(1)
                for i in range(8):  # 15회 → 8회
                    title = self.driver.title
                    if title and '|' in title and len(title) > 10:
                        break
                    time.sleep(0.5)  # 1초 → 0.5초
                time.sleep(1)  # 추가 안정화 (2초 → 1초)
            else:
                time.sleep(2)  # React 렌더링 대기 (5초 → 2초)

            # 소스별 상태 체크
            if 'ssg.com' in product_url:
                result = self._check_ssg_status()
            elif 'homeplus.co.kr' in product_url or 'traders' in product_url:
                result = self._check_homeplus_status()
            elif '11st.co.kr' in product_url:
                result = self._check_11st_status()
            elif 'lotteon.com' in product_url:
                result = self._check_lotteon_status()
            elif 'gmarket.co.kr' in product_url:
                result = self._check_gmarket_status()
            elif 'auction.co.kr' in product_url:
                result = self._check_auction_status()
            else:
                result = self._check_generic_status()

            return result

        except Exception as e:
            print(f"모니터링 오류: {str(e)}")
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"체크 실패: {str(e)}"
            }

        finally:
            self._close_driver()

    def _check_ssg_status(self) -> Dict:
        """SSG 상품 상태 체크"""
        try:
            # JavaScript로 더 정확한 상태 체크
            status_info = self.driver.execute_script("""
                // 구매 버튼 영역에서만 품절 확인
                const buyBtn = document.querySelector('.cdtl_btn_cart') ||
                              document.querySelector('.btn_cart') ||
                              document.querySelector('[class*="btn_cart"]');

                if (buyBtn) {
                    const text = buyBtn.textContent;
                    if (text.includes('품절') || text.includes('일시품절') || text.includes('SOLD OUT')) {
                        return { status: 'out_of_stock', details: '품절' };
                    }
                    if (text.includes('판매종료') || text.includes('판매중지')) {
                        return { status: 'discontinued', details: '판매종료' };
                    }
                }

                // 품절 배지 확인
                const soldoutBadge = document.querySelector('.cdtl_badge_soldout') ||
                                    document.querySelector('.soldout') ||
                                    document.querySelector('[class*="soldout"]');

                if (soldoutBadge && soldoutBadge.offsetParent !== null) {
                    return { status: 'out_of_stock', details: '품절' };
                }

                // 404 페이지 확인
                if (document.title.includes('404') || document.body.textContent.includes('페이지를 찾을 수 없습니다')) {
                    return { status: 'unavailable', details: '페이지 없음' };
                }

                return { status: 'available', details: '정상' };
            """)

            status = status_info.get('status', 'available')
            details = [status_info.get('details', '')]

            # JavaScript로 가격 추출 (SSG 전용)
            # 먼저 페이지에 어떤 가격 관련 요소들이 있는지 확인
            debug_info = self.driver.execute_script("""
                const info = {
                    selectors_found: {},
                    all_prices_text: []
                };

                // 각 셀렉터별로 찾은 요소 개수 기록
                const testSelectors = [
                    '.cdtl_price .ssg_price',
                    '.cdtl_old_price .ssg_price',
                    '.cdtl_price',
                    '.ssg_price',
                    '.ssg_price em',
                    '[class*="price"]',
                    '[class*="Price"]'
                ];

                testSelectors.forEach(sel => {
                    const els = document.querySelectorAll(sel);
                    info.selectors_found[sel] = els.length;
                    if (els.length > 0 && els.length < 10) {
                        els.forEach(el => {
                            info.all_prices_text.push(sel + ': ' + el.textContent.trim().substring(0, 50));
                        });
                    }
                });

                return info;
            """)
            logger.debug(f"SSG 페이지 구조: {debug_info}")

            # 실제 가격 추출 (SSG 판매가 vs 정가 구분)
            price_data = self.driver.execute_script("""
                const result = {
                    sale_price: null,  // 실제 판매가
                    original_price: null,  // 정가 (할인 전)
                    all_prices: []
                };

                // 1단계: 정가(할인 전) 추출
                const oldPriceEl = document.querySelector('.cdtl_old_price .ssg_price');
                if (oldPriceEl) {
                    const num = parseInt(oldPriceEl.textContent.trim().replace(/[^0-9]/g, ''));
                    if (num >= 1000 && num < 10000000) {
                        result.original_price = num;
                    }
                }

                // 2단계: 모든 가격 수집 (정가 제외)
                const priceElements = document.querySelectorAll('.cdtl_price .ssg_price, .ssg_price');
                priceElements.forEach(el => {
                    // 정가 영역 제외
                    if (el.closest('.cdtl_old_price')) return;
                    // 쿠폰 영역 제외
                    if (el.closest('[class*="coupon"]')) return;

                    const text = el.textContent.trim();
                    const num = parseInt(text.replace(/[^0-9]/g, ''));
                    if (num >= 1000 && num < 10000000) {
                        result.all_prices.push(num);
                    }
                });

                // 중복 제거 및 정렬
                result.all_prices = [...new Set(result.all_prices)].sort((a, b) => a - b);

                // 3단계: 판매가 선택 (정가 제외, 쿠폰가 제외)
                if (result.all_prices.length > 0) {
                    // 정가가 있으면 정가보다 낮은 가격 중 가장 큰 값 (할인가)
                    if (result.original_price) {
                        const validPrices = result.all_prices.filter(p => p < result.original_price);
                        if (validPrices.length > 0) {
                            result.sale_price = validPrices[validPrices.length - 1];  // 가장 큰 할인가
                        } else {
                            result.sale_price = result.all_prices[0];
                        }
                    } else {
                        // 정가가 없으면 중간값 선택
                        if (result.all_prices.length >= 3) {
                            result.sale_price = result.all_prices[1];  // 중간값
                        } else {
                            result.sale_price = result.all_prices[0];
                        }
                    }
                }

                return result;
            """)

            price = None
            original_price = None

            logger.debug(f"SSG 가격 데이터: {price_data}")

            if price_data:
                sale_price = price_data.get('sale_price')
                original = price_data.get('original_price')
                all_prices = price_data.get('all_prices', [])

                price = sale_price
                original_price = original

                logger.debug(f"SSG 전체 가격 목록: {all_prices}")
                logger.debug(f"SSG 원가: {original}, 판매가: {sale_price}")
                logger.debug(f"SSG 최종 결과: price={price}, original_price={original_price}")
            else:
                logger.warning("SSG 가격 정보를 찾을 수 없습니다")

            return {
                'status': status,
                'price': price,
                'original_price': original_price,
                'details': ', '.join(details) if details else '정상'
            }

        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"SSG 체크 오류: {str(e)}"
            }

    def _check_homeplus_status(self) -> Dict:
        """홈플러스/Traders 상품 상태 체크"""
        try:
            # JavaScript로 더 정확한 상태 체크
            status_info = self.driver.execute_script("""
                // 구매 버튼 영역에서만 품절 확인
                const buyBtn = document.querySelector('.btn-buy') ||
                              document.querySelector('[class*="buy"]') ||
                              document.querySelector('button[type="button"]');

                if (buyBtn) {
                    const text = buyBtn.textContent;
                    if (text.includes('품절') || text.includes('재고없음') || text.includes('일시품절')) {
                        return { status: 'out_of_stock', details: '품절' };
                    }
                }

                // 품절 표시 확인
                const soldoutEl = document.querySelector('.soldout') ||
                                 document.querySelector('[class*="soldout"]');

                if (soldoutEl && soldoutEl.offsetParent !== null) {
                    return { status: 'out_of_stock', details: '품절' };
                }

                return { status: 'available', details: '정상' };
            """)

            status = status_info.get('status', 'available')
            details = [status_info.get('details', '')]

            # 가격 추출 시도
            price_data = self.driver.execute_script("""
                const text = document.body.textContent;
                const matches = text.match(/(\\d{1,3}(,\\d{3})*)원/g);
                if (matches) {
                    return matches.map(m => parseInt(m.replace(/,|원/g, '')))
                        .filter(n => n > 100 && n < 10000000);
                }
                return null;
            """)

            price = price_data[0] if price_data and len(price_data) > 0 else None

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': ', '.join(details) if details else '정상'
            }

        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"홈플러스 체크 오류: {str(e)}"
            }

    def _check_generic_status(self) -> Dict:
        """범용 상품 상태 체크"""
        try:
            page_source = self.driver.page_source.lower()

            status = 'available'

            # 일반적인 품절 키워드
            out_of_stock_keywords = [
                '품절', '재고없음', 'sold out', 'out of stock',
                '일시품절', '재고부족', 'temporarily out of stock'
            ]

            discontinued_keywords = [
                '판매종료', '판매중지', 'discontinued', '단종',
                '판매중단', 'no longer available'
            ]

            if any(keyword in page_source for keyword in out_of_stock_keywords):
                status = 'out_of_stock'
            elif any(keyword in page_source for keyword in discontinued_keywords):
                status = 'discontinued'

            # 간단한 가격 추출
            price_matches = re.findall(r'(\d{1,3}(,\d{3})*)원', self.driver.page_source)
            prices = [int(p[0].replace(',', '')) for p in price_matches if p]
            prices = [p for p in prices if 100 < p < 10000000]

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

    def _check_11st_status(self) -> Dict:
        """11번가 상품 상태 체크"""
        try:
            # JavaScript로 더 정확한 상태 체크
            status_info = self.driver.execute_script("""
                // 1. 구매 버튼 자체를 확인 (가장 정확)
                const buyBtn = document.querySelector('.btn_buying') ||
                              document.querySelector('[class*="btn_buy"]');

                const cartBtn = document.querySelector('.btn_cart') ||
                               document.querySelector('[class*="btn_cart"]');

                // 버튼이 있고 활성화되어 있으면 구매 가능
                if ((buyBtn && !buyBtn.disabled) || (cartBtn && !cartBtn.disabled)) {
                    // 버튼 텍스트에서 품절 확인
                    const btnText = (buyBtn?.textContent || '') + (cartBtn?.textContent || '');
                    if (btnText.includes('품절') || btnText.includes('SOLD OUT')) {
                        return { status: 'out_of_stock', details: '품절' };
                    }
                    return { status: 'available', details: '정상' };
                }

                // 2. 품절 표시 요소 확인 (보이는 것만)
                const soldoutElements = document.querySelectorAll('[class*="soldout"], .out_of_stock');
                for (let el of soldoutElements) {
                    // 실제로 화면에 표시되는 요소만 확인
                    if (el.offsetParent !== null) {
                        return { status: 'out_of_stock', details: '품절' };
                    }
                }

                // 3. 버튼이 비활성화되어 있으면 품절 가능성
                if (buyBtn?.disabled || cartBtn?.disabled) {
                    return { status: 'out_of_stock', details: '품절' };
                }

                // 기본적으로 구매 가능
                return { status: 'available', details: '정상' };
            """)

            status = status_info.get('status', 'available') if status_info else 'available'
            details = [status_info.get('details', '정상')] if status_info else ['정상']

            # 가격 추출 (11번가 전용)
            price = self.driver.execute_script("""
                // 11번가 첫 번째 .price 요소가 주요 가격
                const priceElement = document.querySelector('.price');

                if (priceElement) {
                    const text = priceElement.textContent.trim();
                    // "23,900원" 형태의 숫자 추출
                    const num = parseInt(text.replace(/[^0-9]/g, ''));
                    // 100원 이상의 합리적인 가격
                    if (num >= 100 && num < 10000000) {
                        return num;
                    }
                }

                return null;
            """)

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': ', '.join(details) if details else '정상'
            }

        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"11번가 체크 오류: {str(e)}"
            }

    def _check_lotteon_status(self) -> Dict:
        """롯데ON 상품 상태 체크"""
        try:
            # JavaScript로 상태 및 가격 추출
            result = self.driver.execute_script(r"""
                const result = { status: 'available', price: null, originalPrice: null, details: '정상', debug: [] };

                // 1. 품절 상태 확인
                const pageText = document.body.innerText || '';
                if (pageText.includes('품절') || pageText.includes('SOLD OUT')) {
                    result.status = 'out_of_stock';
                    result.details = '품절';
                }

                // 2. 페이지 전체에서 가격 패턴 찾기 (가장 확실한 방법)
                const priceMatches = pageText.match(/(\d{1,3}(?:,\d{3})+)\s*원/g);
                result.debug.push(`Found price patterns: ${priceMatches ? priceMatches.length : 0}`);

                if (priceMatches) {
                    // 모든 가격 추출
                    const allPrices = priceMatches.map(p => {
                        const num = parseInt(p.replace(/[^0-9]/g, ''));
                        return num;
                    }).filter(n => n >= 10000 && n < 10000000);  // 1만원 이상 ~ 1000만원 미만

                    result.debug.push(`Filtered prices: ${allPrices.join(', ')}`);

                    if (allPrices.length > 0) {
                        // 중복 제거
                        const uniquePrices = [...new Set(allPrices)].sort((a, b) => b - a);
                        result.debug.push(`Unique prices (desc): ${uniquePrices.join(', ')}`);

                        if (uniquePrices.length >= 2) {
                            // 가장 큰 값이 원가
                            result.originalPrice = uniquePrices[0];
                            // 두 번째로 큰 값이 판매가 (할인가)
                            result.price = uniquePrices[0];  // 원가 반환
                        } else {
                            result.price = uniquePrices[0];
                            result.originalPrice = uniquePrices[0];
                        }
                    }
                }

                // 3. og:price 메타 태그 폴백
                if (!result.price) {
                    const ogPrice = document.querySelector('meta[property="product:price:amount"]');
                    if (ogPrice && ogPrice.content) {
                        const num = parseInt(ogPrice.content);
                        result.debug.push(`og:price: ${num}`);
                        if (num >= 10000 && num < 10000000) {
                            result.price = num;
                            result.originalPrice = num;
                        }
                    }
                }

                return result;
            """)

            print(f"[LOTTEON DEBUG] 가격 추출 결과: {result}")

            return {
                'status': result.get('status', 'available') if result else 'available',
                'price': result.get('price') if result else None,
                'original_price': result.get('originalPrice') if result else None,
                'details': result.get('details', '정상') if result else '정상'
            }

        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"롯데ON 체크 오류: {str(e)}"
            }

    def _check_smartstore_status(self) -> Dict:
        """네이버 스마트스토어 상품 상태 체크"""
        try:
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title

            status = 'available'
            details = []

            # 봇 감지 에러 페이지 확인
            if '[에러]' in page_title or '에러페이지' in page_title:
                return {
                    'status': 'error',
                    'price': None,
                    'original_price': None,
                    'details': '스마트스토어 접근 차단됨 (봇 감지). 잠시 후 다시 시도하거나 수동으로 확인해주세요.'
                }

            # 서비스 접속 불가 메시지 확인
            if '현재 서비스 접속이 불가' in page_source or '접속이 불가합니다' in page_source:
                return {
                    'status': 'error',
                    'price': None,
                    'original_price': None,
                    'details': '스마트스토어 일시적 접근 제한. 잠시 후 다시 시도해주세요.'
                }

            # 품절/판매중지 키워드
            if any(keyword in page_source for keyword in ['품절', '일시품절', '재고없음']):
                status = 'out_of_stock'
                details.append("품절")
            elif any(keyword in page_source for keyword in ['판매종료', '판매중지']):
                status = 'discontinued'
                details.append("판매종료")

            # 가격 추출 (개선된 로직 - 동적 클래스명 대응)
            price_data = self.driver.execute_script(r"""
                const prices = [];
                const debugInfo = [];

                // 방법 1: "원" 텍스트를 포함한 span의 이전 형제 요소에서 숫자 추출
                document.querySelectorAll('span').forEach(span => {
                    if (span.textContent.trim() === '원' || span.classList.contains('won')) {
                        const parent = span.parentElement;
                        if (parent) {
                            // 부모 요소의 모든 span에서 숫자 찾기
                            parent.querySelectorAll('span').forEach(s => {
                                const text = s.textContent.trim();
                                // 숫자와 콤마만 있는 텍스트
                                if (/^[\d,]+$/.test(text) && text.length >= 3) {
                                    const num = parseInt(text.replace(/,/g, ''));
                                    if (num > 100 && num < 10000000) {
                                        prices.push(num);
                                        debugInfo.push('won형제: ' + num);
                                    }
                                }
                            });
                        }
                    }
                });

                // 방법 2: strong 태그 내의 가격 패턴
                document.querySelectorAll('strong').forEach(strong => {
                    const text = strong.textContent.trim();
                    // "29,200원" 또는 "29,200" 패턴
                    const match = text.match(/([\d,]+)\s*원/);
                    if (match) {
                        const num = parseInt(match[1].replace(/,/g, ''));
                        if (num > 100 && num < 10000000 && !prices.includes(num)) {
                            prices.push(num);
                            debugInfo.push('strong: ' + num);
                        }
                    }
                });

                // 방법 3: 페이지 전체에서 가격 패턴 찾기 (XX,XXX원 형태)
                const bodyText = document.body.innerText;
                const priceMatches = bodyText.match(/(\d{1,3}(,\d{3})+)\s*원/g);
                if (priceMatches) {
                    priceMatches.forEach(match => {
                        const num = parseInt(match.replace(/[^0-9]/g, ''));
                        if (num > 1000 && num < 10000000 && !prices.includes(num)) {
                            prices.push(num);
                            debugInfo.push('body: ' + num);
                        }
                    });
                }

                // 방법 4: og:price 메타 태그
                const ogPrice = document.querySelector('meta[property="product:price:amount"]');
                if (ogPrice && ogPrice.content) {
                    const num = parseInt(ogPrice.content);
                    if (num > 100 && num < 10000000 && !prices.includes(num)) {
                        prices.push(num);
                        debugInfo.push('og:price: ' + num);
                    }
                }

                // 방법 5: 기존 선택자
                const selectors = [
                    '.price_num strong',
                    '.lowestPrice strong',
                    '[class*="price"] strong',
                    '[class*="Price"] strong'
                ];

                for (let selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const text = el.textContent || '';
                        const num = parseInt(text.replace(/[^0-9]/g, ''));
                        if (num > 100 && num < 10000000 && !prices.includes(num)) {
                            prices.push(num);
                            debugInfo.push(selector + ': ' + num);
                        }
                    });
                }

                console.log('스마트스토어 가격 디버그:', debugInfo);
                return { prices: prices, debug: debugInfo };
            """)

            print(f"[DEBUG] 스마트스토어 가격 추출 결과: {price_data}")

            # 결과에서 가격 추출
            if price_data and isinstance(price_data, dict):
                prices = price_data.get('prices', [])
                price = min(prices) if prices else None
            elif price_data and isinstance(price_data, list):
                price = min(price_data) if price_data else None
            else:
                price = None

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': ', '.join(details) if details else '정상'
            }

        except Exception as e:
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"스마트스토어 체크 오류: {str(e)}"
            }

    def _check_gmarket_status(self) -> Dict:
        """G마켓 상품 상태 체크"""
        try:
            # JavaScript로 더 정확한 상태 체크
            status_info = self.driver.execute_script("""
                // 구매 버튼 영역에서만 품절 확인
                const buyBtn = document.querySelector('.btn-buy') ||
                              document.querySelector('.button-buy') ||
                              document.querySelector('[class*="btn"][class*="buy"]');

                if (buyBtn) {
                    const text = buyBtn.textContent;
                    if (text.includes('품절') || text.includes('SOLD OUT') || text.includes('일시품절')) {
                        return { status: 'out_of_stock', details: '품절' };
                    }
                    if (text.includes('판매종료') || text.includes('판매중지')) {
                        return { status: 'discontinued', details: '판매종료' };
                    }
                }

                // 품절 표시 확인
                const soldoutEl = document.querySelector('.soldout') ||
                                 document.querySelector('[class*="soldout"]');

                if (soldoutEl && soldoutEl.offsetParent !== null) {
                    return { status: 'out_of_stock', details: '품절' };
                }

                return { status: 'available', details: '정상' };
            """)

            status = status_info.get('status', 'available')
            details = [status_info.get('details', '')]

            # 가격 추출 (개선된 로직)
            price_data = self.driver.execute_script(r"""
                const result = {
                    prices: [],
                    debug_info: []
                };

                // G마켓 주요 가격 선택자 (우선순위 순)
                const mainSelectors = [
                    // 1. 주요 판매가 영역
                    '.price_sect .price strong',
                    '.item_price .price strong',
                    '.box__item-price .price strong',
                    // 2. 일반 가격 영역
                    '.price_innerwrap strong',
                    '.item_price strong',
                    // 3. 폴백
                    '.price strong'
                ];

                // 우선순위대로 시도
                for (let selector of mainSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        elements.forEach(el => {
                            // 부모가 배송비, 포인트, 쿠폰 영역이 아닌지 확인
                            const parentText = el.closest('.price_sect, .item_price, .box__item-price')?.textContent || '';
                            const isDelivery = parentText.includes('배송비') || parentText.includes('무료배송');
                            const isPoint = parentText.includes('포인트') || parentText.includes('적립');
                            const isCoupon = el.closest('[class*="coupon"]') !== null;

                            if (!isDelivery && !isPoint && !isCoupon) {
                                const text = el.textContent.trim();
                                const num = parseInt(text.replace(/[^0-9]/g, ''));
                                if (num > 1000 && num < 10000000) {
                                    result.prices.push(num);
                                    result.debug_info.push(`${selector}: ${num}원`);
                                }
                            }
                        });

                        // 첫 번째 우선순위 선택자에서 가격을 찾았으면 중단
                        if (result.prices.length > 0) {
                            break;
                        }
                    }
                }

                // 가격을 못 찾은 경우, 페이지의 모든 텍스트에서 "원" 패턴 찾기
                if (result.prices.length === 0) {
                    const priceSection = document.querySelector('.item_price, .price_sect, .box__item-price');
                    if (priceSection) {
                        const text = priceSection.textContent;
                        const matches = text.match(/(\d{1,3}(,\d{3})*)\s*원/g);
                        if (matches) {
                            matches.forEach(match => {
                                const num = parseInt(match.replace(/[^0-9]/g, ''));
                                if (num > 1000 && num < 10000000) {
                                    result.prices.push(num);
                                    result.debug_info.push(`텍스트 추출: ${num}원`);
                                }
                            });
                        }
                    }
                }

                // og:price 메타 태그 확인
                if (result.prices.length === 0) {
                    const ogPrice = document.querySelector('meta[property="product:price:amount"]');
                    if (ogPrice && ogPrice.content) {
                        const num = parseInt(ogPrice.content);
                        if (num > 100 && num < 10000000) {
                            result.prices.push(num);
                            result.debug_info.push(`og:price: ${num}원`);
                        }
                    }
                }

                // body 텍스트에서 가격 패턴 찾기
                if (result.prices.length === 0) {
                    const bodyText = document.body.innerText;
                    const priceMatches = bodyText.match(/(\d{1,3}(,\d{3})+)\s*원/g);
                    if (priceMatches) {
                        priceMatches.slice(0, 10).forEach(match => {
                            const num = parseInt(match.replace(/[^0-9]/g, ''));
                            if (num > 1000 && num < 10000000) {
                                result.prices.push(num);
                                result.debug_info.push(`body: ${num}원`);
                            }
                        });
                    }
                }

                return result;
            """)

            print(f"[DEBUG] G마켓 가격 추출 정보: {price_data}")
            logger.debug(f"G마켓 가격 추출 정보: {price_data}")

            prices = price_data.get('prices', []) if price_data else []
            debug_info = price_data.get('debug_info', []) if price_data else []

            # 가격이 여러 개면 중간값 선택 (최소값은 배송비일 수 있음)
            if len(prices) > 0:
                prices_sorted = sorted(prices)
                if len(prices) == 1:
                    price = prices_sorted[0]
                elif len(prices) >= 3:
                    # 3개 이상이면 중간값 선택 (최소값과 최대값 제외)
                    price = prices_sorted[len(prices) // 2]
                else:
                    # 2개면 더 큰 값 선택 (할인가 vs 정가)
                    price = prices_sorted[-1]

                logger.info(f"G마켓 추출된 모든 가격: {prices_sorted}")
                logger.info(f"G마켓 선택된 가격: {price}원")
                logger.info(f"G마켓 디버그 정보: {debug_info}")
            else:
                price = None
                logger.warning("G마켓 가격 추출 실패")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': ', '.join(details) if details else '정상'
            }

        except Exception as e:
            logger.error(f"G마켓 체크 오류: {str(e)}")
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"G마켓 체크 오류: {str(e)}"
            }

    def _check_auction_status(self) -> Dict:
        """옥션 상품 상태 체크 (G마켓과 유사한 구조)"""
        try:
            # JavaScript로 상태 체크
            status_info = self.driver.execute_script("""
                // 구매 버튼 영역에서 품절 확인
                const buyBtn = document.querySelector('.btn-buy') ||
                              document.querySelector('.button-buy') ||
                              document.querySelector('[class*="btn"][class*="buy"]');

                if (buyBtn) {
                    const text = buyBtn.textContent;
                    if (text.includes('품절') || text.includes('SOLD OUT') || text.includes('일시품절')) {
                        return { status: 'out_of_stock', details: '품절' };
                    }
                    if (text.includes('판매종료') || text.includes('판매중지')) {
                        return { status: 'discontinued', details: '판매종료' };
                    }
                }

                // 품절 표시 확인
                const soldoutEl = document.querySelector('.soldout') ||
                                 document.querySelector('[class*="soldout"]');

                if (soldoutEl && soldoutEl.offsetParent !== null) {
                    return { status: 'out_of_stock', details: '품절' };
                }

                return { status: 'available', details: '정상' };
            """)

            status = status_info.get('status', 'available')
            details = [status_info.get('details', '')]

            # 가격 추출 (옥션 - G마켓과 유사)
            price_data = self.driver.execute_script(r"""
                const result = {
                    prices: [],
                    debug_info: []
                };

                // 옥션 주요 가격 선택자
                const mainSelectors = [
                    '.price_sect .price strong',
                    '.item_price .price strong',
                    '.box__item-price .price strong',
                    '.price_innerwrap strong',
                    '.item_price strong',
                    '.price strong'
                ];

                for (let selector of mainSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        elements.forEach(el => {
                            const parentText = el.closest('.price_sect, .item_price, .box__item-price')?.textContent || '';
                            const isDelivery = parentText.includes('배송비') || parentText.includes('무료배송');
                            const isPoint = parentText.includes('포인트') || parentText.includes('적립');
                            const isCoupon = el.closest('[class*="coupon"]') !== null;

                            if (!isDelivery && !isPoint && !isCoupon) {
                                const text = el.textContent.trim();
                                const num = parseInt(text.replace(/[^0-9]/g, ''));
                                if (num > 1000 && num < 10000000) {
                                    result.prices.push(num);
                                    result.debug_info.push(`${selector}: ${num}원`);
                                }
                            }
                        });

                        if (result.prices.length > 0) {
                            break;
                        }
                    }
                }

                // 가격을 못 찾은 경우, 텍스트에서 "원" 패턴 찾기
                if (result.prices.length === 0) {
                    const priceSection = document.querySelector('.item_price, .price_sect, .box__item-price');
                    if (priceSection) {
                        const text = priceSection.textContent;
                        const matches = text.match(/(\\d{1,3}(,\\d{3})*)\\s*원/g);
                        if (matches) {
                            matches.forEach(match => {
                                const num = parseInt(match.replace(/[^0-9]/g, ''));
                                if (num > 1000 && num < 10000000) {
                                    result.prices.push(num);
                                    result.debug_info.push(`텍스트 추출: ${num}원`);
                                }
                            });
                        }
                    }
                }

                // og:price 메타 태그 확인
                if (result.prices.length === 0) {
                    const ogPrice = document.querySelector('meta[property="product:price:amount"]');
                    if (ogPrice && ogPrice.content) {
                        const num = parseInt(ogPrice.content);
                        if (num > 100 && num < 10000000) {
                            result.prices.push(num);
                            result.debug_info.push(`og:price: ${num}원`);
                        }
                    }
                }

                // body 텍스트에서 가격 패턴 찾기
                if (result.prices.length === 0) {
                    const bodyText = document.body.innerText;
                    const priceMatches = bodyText.match(/(\\d{1,3}(,\\d{3})+)\\s*원/g);
                    if (priceMatches) {
                        priceMatches.slice(0, 10).forEach(match => {
                            const num = parseInt(match.replace(/[^0-9]/g, ''));
                            if (num > 1000 && num < 10000000) {
                                result.prices.push(num);
                                result.debug_info.push(`body: ${num}원`);
                            }
                        });
                    }
                }

                return result;
            """)

            print(f"[DEBUG] 옥션 가격 추출 정보: {price_data}")
            logger.debug(f"옥션 가격 추출 정보: {price_data}")

            prices = price_data.get('prices', []) if price_data else []

            if len(prices) > 0:
                prices_sorted = sorted(prices)
                if len(prices) == 1:
                    price = prices_sorted[0]
                elif len(prices) >= 3:
                    price = prices_sorted[len(prices) // 2]
                else:
                    price = prices_sorted[-1]

                logger.info(f"옥션 추출된 모든 가격: {prices_sorted}")
                logger.info(f"옥션 선택된 가격: {price}원")
            else:
                price = None
                logger.warning("옥션 가격 추출 실패")

            return {
                'status': status,
                'price': price,
                'original_price': None,
                'details': ', '.join(details) if details else '정상'
            }

        except Exception as e:
            logger.error(f"옥션 체크 오류: {str(e)}")
            return {
                'status': 'error',
                'price': None,
                'original_price': None,
                'details': f"옥션 체크 오류: {str(e)}"
            }
