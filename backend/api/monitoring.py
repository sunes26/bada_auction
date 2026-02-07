"""
상품 모니터링 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database.db_wrapper import get_db
from monitor.product_monitor import ProductMonitor
from utils.cache import async_cached
from utils.flaresolverr import solve_cloudflare, get_flaresolverr_client
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/monitor", tags=["monitoring"])


# Request 모델
class AddMonitoringRequest(BaseModel):
    product_url: str
    product_name: str
    source: str  # 'traders', 'ssg', 등
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    check_interval: int = 15  # 분
    notes: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    is_active: bool


# API 엔드포인트

@router.post("/add")
async def add_monitoring_product(request: AddMonitoringRequest, background_tasks: BackgroundTasks):
    """
    모니터링 상품 추가
    """
    try:
        db = get_db()

        # DB에 추가
        product_id = db.add_monitored_product(
            product_url=request.product_url,
            product_name=request.product_name,
            source=request.source,
            current_price=request.current_price,
            original_price=request.original_price,
            check_interval=request.check_interval,
            notes=request.notes
        )

        # 즉시 첫 체크 수행 (백그라운드)
        background_tasks.add_task(perform_check, product_id)

        return {
            "success": True,
            "product_id": product_id,
            "message": "모니터링 상품이 추가되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 추가 실패: {str(e)}")


@router.get("/products")
@async_cached(ttl=30)  # 30초 캐싱
async def get_monitored_products(active_only: bool = True):
    """
    모니터링 중인 상품 목록 조회
    """
    try:
        db = get_db()
        products = db.get_all_monitored_products(active_only=active_only)

        return {
            "success": True,
            "products": products,
            "total": len(products)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"목록 조회 실패: {str(e)}")


@router.get("/product/{product_id}")
async def get_product_status(product_id: int):
    """
    특정 상품의 상세 정보 및 이력 조회
    """
    try:
        db = get_db()

        product = db.get_monitored_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        status_history = db.get_status_history(product_id, limit=20)
        price_history = db.get_price_history(product_id, limit=50)

        return {
            "success": True,
            "product": product,
            "status_history": status_history,
            "price_history": price_history
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.post("/check/{product_id}")
async def check_product_now(product_id: int, background_tasks: BackgroundTasks):
    """
    특정 상품을 즉시 체크
    """
    try:
        db = get_db()

        product = db.get_monitored_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # 백그라운드 태스크로 체크 수행
        background_tasks.add_task(perform_check, product_id)

        return {
            "success": True,
            "message": "상품 체크가 시작되었습니다.",
            "product_id": product_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"체크 실패: {str(e)}")


@router.put("/product/{product_id}/status")
async def update_monitoring_status(product_id: int, request: UpdateStatusRequest):
    """
    모니터링 활성화/비활성화
    """
    try:
        db = get_db()

        product = db.get_monitored_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        db.toggle_monitoring(product_id, request.is_active)

        return {
            "success": True,
            "message": f"모니터링이 {'활성화' if request.is_active else '비활성화'}되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업데이트 실패: {str(e)}")


@router.delete("/product/{product_id}")
async def delete_monitoring_product(product_id: int):
    """
    모니터링 상품 삭제
    """
    try:
        db = get_db()

        product = db.get_monitored_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        db.delete_monitored_product(product_id)

        return {
            "success": True,
            "message": "모니터링 상품이 삭제되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")


@router.get("/notifications")
@async_cached(ttl=10)  # 10초 캐싱 (알림은 자주 업데이트되므로 짧게)
async def get_notifications(limit: int = 50):
    """
    알림 목록 조회
    """
    try:
        db = get_db()
        notifications = db.get_unread_notifications(limit=limit)

        return {
            "success": True,
            "notifications": notifications,
            "total": len(notifications)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {str(e)}")


@router.put("/notification/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """
    알림을 읽음으로 표시
    """
    try:
        db = get_db()
        db.mark_notification_as_read(notification_id)

        return {
            "success": True,
            "message": "알림이 읽음으로 표시되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업데이트 실패: {str(e)}")


@router.get("/dashboard/stats")
@async_cached(ttl=60)  # 1분 캐싱
async def get_dashboard_stats():
    """
    대시보드 통계 조회
    - 총 상품 수
    - 활성/비활성 상품 수
    - 알림 통계
    - 최근 가격 변동
    """
    try:
        db = get_db()
        stats = db.get_dashboard_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/dashboard/margin-alerts")
async def get_margin_alert_products():
    """
    역마진 발생 상품 목록 조회
    """
    try:
        db = get_db()
        products = db.get_margin_alert_products()

        return {
            "success": True,
            "products": products,
            "total": len(products)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/product/{product_id}/price-history")
async def get_product_price_history(product_id: int, limit: int = 30):
    """
    특정 상품의 가격 변동 이력 조회 (차트용)
    """
    try:
        db = get_db()
        history = db.get_price_history(product_id, limit=limit)

        # 차트용 데이터 포맷 (시간순 정렬)
        chart_data = {
            "labels": [item["checked_at"] for item in reversed(history)],
            "prices": [item["price"] for item in reversed(history)]
        }

        return {
            "success": True,
            "history": history,
            "chart_data": chart_data,
            "total": len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가격 이력 조회 실패: {str(e)}")


@router.post("/extract-url-info")
async def extract_url_info(request: dict):
    """
    URL에서 상품 정보 자동 추출
    """
    try:
        product_url = request.get('product_url')
        if not product_url:
            raise HTTPException(status_code=400, detail="URL이 필요합니다.")

        # URL에서 소스 감지
        source = 'other'
        if 'ssg.com' in product_url:
            source = 'ssg'
        elif 'homeplus.co.kr' in product_url or 'traders' in product_url:
            source = 'traders'
        elif '11st.co.kr' in product_url:
            source = '11st'
        elif 'lotteon.com' in product_url:
            source = 'lotteon'
        elif 'gmarket.co.kr' in product_url:
            source = 'gmarket'
        elif 'auction.co.kr' in product_url:
            source = 'auction'
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 URL입니다. SSG, 홈플러스/Traders, 11번가, 롯데ON, G마켓, 옥션 URL을 입력해주세요.")

        # 봇 감지 보호 사이트 (FlareSolverr 사용)
        bot_protected_sites = ['gmarket.co.kr', 'auction.co.kr']
        is_bot_protected = any(site in product_url for site in bot_protected_sites)

        clean_url = product_url

        # FlareSolverr로 먼저 시도 (봇 감지 우회)
        flaresolverr_result = None

        if is_bot_protected:
            print(f"[FLARESOLVERR] 봇 보호 사이트 감지, FlareSolverr 시도...")
            # 스마트스토어는 React SPA라 더 긴 대기 시간 필요
            timeout = 90000 if 'smartstore.naver.com' in product_url else 60000
            flaresolverr_result = solve_cloudflare(clean_url, max_timeout=timeout)

            if flaresolverr_result and flaresolverr_result.get('html'):
                html_content = flaresolverr_result.get('html', '')
                print(f"[FLARESOLVERR] 성공! HTML 길이: {len(html_content)}")

                # HTML 직접 파싱으로 데이터 추출 (Selenium 사용 안 함)
                from bs4 import BeautifulSoup
                import re

                soup = BeautifulSoup(html_content, 'html.parser')

                # 페이지 타이틀 확인 (에러 페이지 감지)
                page_title = soup.title.string if soup.title else ""
                print(f"[FLARESOLVERR] 페이지 타이틀: {page_title}")

                # CAPTCHA/에러 페이지 감지
                is_captcha = 'captcha' in html_content.lower() or 'ncpt.naver.com' in html_content
                is_error_page = '에러' in str(page_title) or 'error' in str(page_title).lower()
                is_blocked = len(html_content) < 50000 and ('smartstore.naver.com' in product_url)

                if is_captcha:
                    print(f"[FLARESOLVERR] CAPTCHA 페이지 감지 - 네이버 봇 차단")
                    # 스마트스토어는 CAPTCHA로 차단됨 - 에러 반환
                    if 'smartstore.naver.com' in product_url:
                        return {
                            "success": False,
                            "error": "smartstore_captcha",
                            "message": "네이버 스마트스토어가 CAPTCHA로 자동 접근을 차단했습니다. 상품 정보를 수동으로 입력해주세요."
                        }
                    flaresolverr_result = None  # 다른 사이트는 Selenium 폴백
                elif is_error_page or is_blocked:
                    print(f"[FLARESOLVERR] 에러/차단 페이지 감지, Selenium으로 폴백")
                    flaresolverr_result = None  # Selenium 폴백 트리거
                else:
                    # 상품명 추출
                    product_name = None
                    if 'gmarket.co.kr' in product_url or 'auction.co.kr' in product_url:
                        # G마켓/옥션
                        title_el = soup.select_one('.itemtit') or soup.select_one('h1')
                        if title_el:
                            product_name = title_el.get_text(strip=True)
                    elif 'smartstore.naver.com' in product_url:
                        # 스마트스토어 - 다양한 선택자 시도
                        selectors = [
                            'h3._copyable',
                            'meta[property="og:title"]',
                            'title',
                            '.bd_tit',
                            'h1'
                        ]
                        for selector in selectors:
                            title_el = soup.select_one(selector)
                            if title_el:
                                if title_el.name == 'meta':
                                    product_name = title_el.get('content', '')
                                elif title_el.name == 'title':
                                    # "상품명 : 스토어명" 형태에서 상품명 추출
                                    full_title = title_el.get_text(strip=True)
                                    if ' : ' in full_title:
                                        product_name = full_title.split(' : ')[0]
                                    elif ' - ' in full_title:
                                        product_name = full_title.split(' - ')[0]
                                    else:
                                        product_name = full_title
                                else:
                                    product_name = title_el.get_text(strip=True)
                                if product_name and len(product_name) > 3:
                                    break
                        print(f"[FLARESOLVERR] 스마트스토어 HTML 미리보기: {html_content[:500]}")

                    # og:title 폴백
                    if not product_name:
                        og_title = soup.select_one('meta[property="og:title"]')
                        if og_title:
                            product_name = og_title.get('content', '')

                print(f"[FLARESOLVERR] 추출된 상품명: {product_name}")

                # 가격 추출
                current_price = None
                # og:price 먼저 시도
                og_price = soup.select_one('meta[property="product:price:amount"]')
                if og_price and og_price.get('content'):
                    try:
                        current_price = int(og_price.get('content'))
                        print(f"[FLARESOLVERR] og:price에서 가격 추출: {current_price}")
                    except:
                        pass

                # HTML에서 가격 패턴 찾기
                if not current_price:
                    price_patterns = [
                        r'(\d{1,3}(?:,\d{3})+)\s*원',  # XX,XXX원
                        r'"price":\s*"?(\d+)"?',  # JSON price
                    ]
                    for pattern in price_patterns:
                        matches = re.findall(pattern, html_content)
                        if matches:
                            for match in matches:
                                try:
                                    price = int(match.replace(',', ''))
                                    if 1000 < price < 10000000:
                                        current_price = price
                                        print(f"[FLARESOLVERR] 패턴에서 가격 추출: {current_price}")
                                        break
                                except:
                                    pass
                            if current_price:
                                break

                    # 썸네일 추출
                    thumbnail_url = None

                    # 1. og:image 메타 태그
                    og_image = soup.select_one('meta[property="og:image"]')
                    if og_image and og_image.get('content'):
                        thumbnail_url = og_image.get('content')
                        # 프로토콜 상대 URL 처리
                        if thumbnail_url.startswith('//'):
                            thumbnail_url = 'https:' + thumbnail_url
                        print(f"[FLARESOLVERR] og:image에서 썸네일 추출: {thumbnail_url}")

                    # 2. G마켓/옥션 전용: CDN 도메인에서 이미지 찾기
                    if not thumbnail_url and ('gmarket.co.kr' in product_url or 'auction.co.kr' in product_url):
                        # G마켓/옥션 이미지 CDN 도메인
                        cdn_domains = ['gstatic.gmarket.co.kr', 'gimage.gmarket.co.kr', 'image.auction.co.kr', 'g-static.auction.co.kr']

                        # 모든 이미지에서 CDN 도메인 찾기
                        for img in soup.find_all('img'):
                            src = img.get('src') or img.get('data-src') or img.get('data-original')
                            if src:
                                for cdn in cdn_domains:
                                    if cdn in src:
                                        thumbnail_url = src
                                        if thumbnail_url.startswith('//'):
                                            thumbnail_url = 'https:' + thumbnail_url
                                        print(f"[FLARESOLVERR] CDN 이미지 발견: {thumbnail_url}")
                                        break
                            if thumbnail_url:
                                break

                        # HTML에서 이미지 URL 패턴 직접 찾기 (정규식)
                        if not thumbnail_url:
                            import re
                            img_patterns = [
                                r'(https?://gstatic\.gmarket\.co\.kr[^\s"\'<>]+\.(?:jpg|jpeg|png|gif))',
                                r'(https?://gimage\.gmarket\.co\.kr[^\s"\'<>]+\.(?:jpg|jpeg|png|gif))',
                                r'(https?://image\.auction\.co\.kr[^\s"\'<>]+\.(?:jpg|jpeg|png|gif))',
                                r'(//gstatic\.gmarket\.co\.kr[^\s"\'<>]+\.(?:jpg|jpeg|png|gif))',
                            ]
                            for pattern in img_patterns:
                                matches = re.findall(pattern, html_content, re.IGNORECASE)
                                if matches:
                                    thumbnail_url = matches[0]
                                    if thumbnail_url.startswith('//'):
                                        thumbnail_url = 'https:' + thumbnail_url
                                    print(f"[FLARESOLVERR] 정규식으로 이미지 발견: {thumbnail_url}")
                                    break

                    # 3. 첫 번째 큰 이미지 찾기 (폴백)
                    if not thumbnail_url:
                        for img in soup.find_all('img'):
                            src = img.get('src') or img.get('data-src')
                            if src and ('http' in src or src.startswith('//')):
                                # 작은 아이콘, 로고, 배너 제외
                                skip_keywords = ['icon', 'logo', 'banner', 'btn', 'button', 'sprite', 'blank', '1x1']
                                if not any(kw in src.lower() for kw in skip_keywords):
                                    thumbnail_url = src
                                    if thumbnail_url.startswith('//'):
                                        thumbnail_url = 'https:' + thumbnail_url
                                    print(f"[FLARESOLVERR] 이미지 태그에서 썸네일 추출: {thumbnail_url}")
                                    break

                    # FlareSolverr로 성공적으로 데이터 추출 완료
                    if product_name or current_price:
                        print(f"[FLARESOLVERR] 데이터 추출 완료 - 상품명: {product_name}, 가격: {current_price}, 썸네일: {thumbnail_url}")
                        return {
                            "success": True,
                            "data": {
                                "source": source,
                                "product_name": product_name or "자동 감지 실패",
                                "current_price": current_price,
                                "status": "available",
                                "details": "FlareSolverr로 추출",
                                "thumbnail_url": thumbnail_url
                            }
                        }
                    else:
                        print(f"[FLARESOLVERR] HTML에서 데이터 추출 실패, Selenium으로 폴백")
            else:
                print(f"[FLARESOLVERR] 실패 또는 사용 불가, Selenium으로 폴백")

        # 모니터로 상품 정보 추출 (FlareSolverr 실패 시 또는 비-Cloudflare 사이트)
        monitor = ProductMonitor()

        # Selenium 사용
        print(f"[SELENIUM] Selenium으로 추출 시도")
        monitor._init_driver()

        try:
            import time
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import UnexpectedAlertPresentException

            monitor.driver.get(product_url)

            # Alert 처리
            try:
                time.sleep(1)
                alert = monitor.driver.switch_to.alert
                print(f"[ALERT] Alert 감지: {alert.text}")
                alert.dismiss()
                print(f"[ALERT] Alert 닫음")
            except:
                pass  # Alert 없으면 무시

            # 실제 도착한 URL 확인
            actual_url = monitor.driver.current_url
            print(f"[URL DEBUG] 요청 URL: {product_url}")
            print(f"[URL DEBUG] 실제 URL: {actual_url}")

            # Cloudflare 챌린지 대기 (G마켓, 옥션 등에서 사용)
            def wait_for_cloudflare():
                """Cloudflare 챌린지가 완료될 때까지 대기"""
                cloudflare_indicators = ['just a moment', 'checking your browser', '사용자 활동 검토']
                max_wait = 20  # 최대 20초 대기
                for i in range(max_wait):
                    title = monitor.driver.title.lower()
                    is_cloudflare = any(indicator in title for indicator in cloudflare_indicators)
                    if not is_cloudflare:
                        print(f"[CLOUDFLARE] 챌린지 통과 완료 ({i}초 후)")
                        return True
                    print(f"[CLOUDFLARE] 챌린지 대기 중... ({i+1}/{max_wait}초)")
                    time.sleep(1)
                print(f"[CLOUDFLARE] 챌린지 통과 실패 (타임아웃)")
                return False

            # 사이트별 대기 시간 조정 (최적화됨)
            if 'smartstore.naver.com' in product_url:
                # 스마트스토어: React SPA - 가격 요소가 로드될 때까지 대기
                print(f"[SMARTSTORE] React 콘텐츠 로딩 대기 중...")
                for i in range(10):  # 최대 10초 대기
                    try:
                        # 가격 요소 또는 상품명 요소 확인
                        has_content = monitor.driver.execute_script("""
                            // 가격 요소 확인
                            const priceEl = document.querySelector('meta[property="product:price:amount"]');
                            if (priceEl && priceEl.content) return true;

                            // 상품명 확인 (og:title)
                            const titleEl = document.querySelector('meta[property="og:title"]');
                            if (titleEl && titleEl.content && titleEl.content.length > 5) return true;

                            // "원" 텍스트가 있는 가격 표시 확인
                            const bodyText = document.body.innerText;
                            if (bodyText && /\d{1,3}(,\d{3})+\s*원/.test(bodyText)) return true;

                            return false;
                        """)
                        if has_content:
                            print(f"[SMARTSTORE] 콘텐츠 로드 완료 ({i+1}초)")
                            break
                    except:
                        pass
                    print(f"[SMARTSTORE] 대기 중... ({i+1}/10초)")
                    time.sleep(1)
                time.sleep(1)  # 추가 안정화
            elif 'lotteon.com' in product_url:
                # 롯데ON: React SPA - 가격 요소 로드 대기
                print(f"[LOTTEON] React 콘텐츠 로딩 대기 중...")
                for i in range(10):  # 최대 10초 대기
                    try:
                        has_price = monitor.driver.execute_script("""
                            // 가격 텍스트가 있는지 확인
                            const bodyText = document.body.innerText || '';
                            // XX,XXX원 패턴 찾기
                            if (/\\d{1,3}(,\\d{3})+\\s*원/.test(bodyText)) return true;
                            return false;
                        """)
                        if has_price:
                            print(f"[LOTTEON] 가격 콘텐츠 로드 완료 ({i+1}초)")
                            break
                    except:
                        pass
                    print(f"[LOTTEON] 대기 중... ({i+1}/10초)")
                    time.sleep(1)
                time.sleep(2)  # 추가 안정화
            elif 'gmarket.co.kr' in product_url or 'auction.co.kr' in product_url:
                # G마켓/옥션: Cloudflare 보호 사용
                time.sleep(2)
                wait_for_cloudflare()
                time.sleep(1)  # 추가 안정화
            elif 'homeplus.co.kr' in product_url:
                # 홈플러스: DOM 완전히 로드될 때까지 명시적 대기 (최적화)
                time.sleep(1)
                # 페이지 title이 "홈플러스"가 아닌 실제 상품명을 포함할 때까지 대기
                print(f"[HOMEPLUS] 페이지 타이틀 로딩 대기 중...")
                for i in range(8):  # 최대 8초 대기 (15초 → 8초)
                    title = monitor.driver.title
                    print(f"[HOMEPLUS] Wait {i+1}/8: title = '{title}'")
                    if title and '|' in title and len(title) > 10:
                        print(f"[HOMEPLUS] 타이틀 로드 완료!")
                        break
                    time.sleep(0.5)  # 1초 → 0.5초
                time.sleep(1)  # 추가 안정화 시간 (2초 → 1초)
            else:
                time.sleep(2)  # React 렌더링 대기 (5초 → 2초)

            # Alert 재확인 (로딩 후에 나올 수 있음)
            try:
                alert = monitor.driver.switch_to.alert
                print(f"[ALERT] 로딩 후 Alert 감지: {alert.text}")
                alert.dismiss()
                print(f"[ALERT] Alert 닫음")
                time.sleep(1)
            except:
                pass

            # 페이지 로드 확인
            page_title = monitor.driver.title
            print(f"[DEBUG] 페이지 타이틀: {page_title}")
            print(f"[DEBUG] 현재 URL: {monitor.driver.current_url}")

            # Cloudflare/봇 탐지 확인
            cloudflare_indicators = ['just a moment', 'checking your browser', '사용자 활동 검토', '서비스접속불가', '차단', 'blocked']
            is_blocked = any(indicator in page_title.lower() for indicator in cloudflare_indicators)

            if is_blocked:
                print(f"[DEBUG] 봇 탐지/Cloudflare 차단: 페이지 타이틀 = {page_title}")
                # 드라이버 종료
                monitor._close_driver()
                raise HTTPException(
                    status_code=503,
                    detail=f"사이트 보안 시스템(Cloudflare)에 의해 접근이 차단되었습니다. 잠시 후 다시 시도해주세요. (페이지 타이틀: {page_title})"
                )

            # 페이지 소스 일부 확인 (디버깅용)
            try:
                page_source_preview = monitor.driver.page_source[:500]
                print(f"[DEBUG] 페이지 소스 미리보기: {page_source_preview}")
            except Exception as e:
                print(f"[DEBUG] 페이지 소스 가져오기 실패: {e}")

            # 상품명 추출 (페이지가 로드된 상태에서)
            try:
                product_name = monitor.extract_product_name(product_url, source)
                print(f"[DEBUG] 상품명 추출 결과: {product_name}")
                logger.debug(f"상품명 추출: {product_name}")
            except UnexpectedAlertPresentException:
                try:
                    alert = monitor.driver.switch_to.alert
                    alert.dismiss()
                    time.sleep(1)
                    product_name = monitor.extract_product_name(product_url, source)
                    logger.debug(f"Alert 처리 후 상품명 추출: {product_name}")
                except Exception as e:
                    logger.error(f"Alert 처리 후 상품명 추출 실패: {str(e)}", exc_info=True)
                    product_name = None
            except Exception as e:
                logger.error(f"상품명 추출 중 오류: {str(e)}", exc_info=True)
                product_name = None

            # 상태 및 가격 체크 (이미 로드된 페이지 사용)
            logger.debug(f"가격 체크 시작: {product_url}")
            if 'ssg.com' in product_url:
                logger.debug("SSG 체커 사용")
                result = monitor._check_ssg_status()
                logger.debug(f"SSG 결과: {result}")
            elif 'homeplus.co.kr' in product_url or 'traders' in product_url:
                result = monitor._check_homeplus_status()
            elif '11st.co.kr' in product_url:
                result = monitor._check_11st_status()
            elif 'lotteon.com' in product_url:
                result = monitor._check_lotteon_status()
            elif 'gmarket.co.kr' in product_url:
                result = monitor._check_gmarket_status()
            elif 'auction.co.kr' in product_url:
                result = monitor._check_auction_status()
            else:
                result = monitor._check_generic_status()

            print(f"[DEBUG] 가격 추출 결과: {result}")

            # 썸네일 추출 및 다운로드 (이미 로드된 페이지에서)
            logger.debug("썸네일 추출 중...")
            thumbnail_url = None
            thumbnail_path = None
            try:
                # 썸네일 URL 추출 (사이트별 최적화)
                thumbnail_url = monitor.driver.execute_script("""
                    // 1. 스마트스토어 전용 셀렉터
                    if (window.location.hostname.includes('smartstore.naver.com')) {
                        // 대표 이미지 (클래스명이 동적이므로 구조로 찾기)
                        const mainImg = document.querySelector('img[alt="대표이미지"]') ||
                                       document.querySelector('img[class*="TgO1N1wWTm"]') ||
                                       document.querySelector('[class*="mdFeBiFowv"] img');
                        if (mainImg && mainImg.src) return mainImg.src;
                    }

                    // 2. 옥션/G마켓 전용 셀렉터
                    if (window.location.hostname.includes('auction.co.kr') ||
                        window.location.hostname.includes('gmarket.co.kr')) {
                        const mainImg = document.querySelector('.thumb-image img') ||
                                       document.querySelector('.item-topimg img') ||
                                       document.querySelector('#mainImage') ||
                                       document.querySelector('.box-im img');
                        if (mainImg && mainImg.src) return mainImg.src;
                    }

                    // 3. og:image 메타 태그 (가장 신뢰성 높음)
                    const ogImage = document.querySelector('meta[property="og:image"]');
                    if (ogImage && ogImage.content) return ogImage.content;

                    // 4. 일반적인 선택자들
                    const selectors = [
                        'meta[name="twitter:image"]',
                        '.product-image img',
                        '.detail-image img',
                        '[class*="product"][class*="img"] img',
                        '[class*="thumb"] img',
                        'img[alt*="대표"]',
                        'img[alt*="메인"]'
                    ];

                    for (let selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            if (el.tagName === 'META') {
                                return el.content;
                            } else if (el.tagName === 'IMG' && el.src) {
                                return el.src;
                            }
                        }
                    }

                    // 5. 첫 번째 큰 이미지 찾기
                    const images = document.querySelectorAll('img');
                    for (let img of images) {
                        if (img.naturalWidth > 200 && img.naturalHeight > 200 && img.src) {
                            return img.src;
                        }
                    }

                    return null;
                """)
                print(f"[DEBUG] 썸네일 URL 추출 결과: {thumbnail_url}")
                logger.debug(f"썸네일 URL: {thumbnail_url}")

                # 썸네일 다운로드
                if thumbnail_url:
                    from utils.image_downloader import download_thumbnail
                    thumbnail_path = download_thumbnail(thumbnail_url)
                    print(f"[DEBUG] 썸네일 저장 경로: {thumbnail_path}")
                    logger.info(f"썸네일 저장 완료: {thumbnail_path}")

            except Exception as e:
                print(f"[DEBUG] 썸네일 추출 에러: {str(e)}")
                logger.warning(f"썸네일 추출 실패: {str(e)}")
                thumbnail_url = None
                thumbnail_path = None

        finally:
            # 드라이버 종료 (반드시 실행)
            monitor._close_driver()

        return {
            "success": True,
            "data": {
                "source": source,
                "product_name": product_name or "자동 감지 실패",
                "current_price": result.get('price'),
                "status": result.get('status'),
                "details": result.get('details'),
                "thumbnail_url": thumbnail_path or thumbnail_url
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] 정보 추출 실패: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"정보 추출 실패: {str(e)}")


@router.post("/extract-thumbnail")
async def extract_thumbnail(request: dict):
    """
    URL에서 대표 썸네일 이미지 추출
    """
    try:
        product_url = request.get('product_url')
        if not product_url:
            raise HTTPException(status_code=400, detail="URL이 필요합니다.")

        # 모니터로 썸네일 추출
        monitor = ProductMonitor()
        monitor._init_driver()

        try:
            monitor.driver.get(product_url)
            import time
            time.sleep(1)  # 페이지 로딩 대기 (3초 → 1초, eager 로드 전략 활용)

            # 대표 이미지 추출 (사이트별 선택자)
            thumbnail_url = monitor.driver.execute_script("""
                // 대표 이미지 찾기 (일반적인 선택자들)
                const selectors = [
                    'meta[property="og:image"]',
                    'meta[name="twitter:image"]',
                    '.product-image img',
                    '.detail-image img',
                    '[class*="product"][class*="img"] img',
                    '[class*="thumb"] img',
                    'img[alt*="대표"]',
                    'img[alt*="메인"]'
                ];

                for (let selector of selectors) {
                    const el = document.querySelector(selector);
                    if (el) {
                        if (el.tagName === 'META') {
                            return el.content;
                        } else if (el.tagName === 'IMG') {
                            return el.src;
                        }
                    }
                }

                // 첫 번째 큰 이미지 찾기
                const images = document.querySelectorAll('img');
                for (let img of images) {
                    if (img.naturalWidth > 200 && img.naturalHeight > 200) {
                        return img.src;
                    }
                }

                return null;
            """)

            return {
                "success": True,
                "thumbnail_url": thumbnail_url
            }

        finally:
            monitor._close_driver()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"썸네일 추출 실패: {str(e)}")


# 헬퍼 함수

def perform_check(product_id: int):
    """
    실제 상품 체크 수행 (백그라운드 태스크)
    """
    try:
        db = get_db()
        product = db.get_monitored_product(product_id)

        if not product or not product['is_active']:
            return

        # 모니터 인스턴스 생성 및 체크
        monitor = ProductMonitor()
        result = monitor.check_product_status(
            product_url=product['product_url'],
            source=product['source']
        )

        # DB 업데이트
        db.update_product_status(
            product_id=product_id,
            new_status=result['status'],
            new_price=result['price'],
            details=result['details']
        )

        print(f"[OK] 상품 #{product_id} 체크 완료: {result['status']}, {result['price']}원")

    except Exception as e:
        print(f"[ERROR] 상품 #{product_id} 체크 실패: {str(e)}")
        # 오류 알림 생성
        try:
            db = get_db()
            db.update_product_status(
                product_id=product_id,
                new_status='error',
                details=f"체크 실패: {str(e)}"
            )
        except:
            pass


class SaveThumbnailRequest(BaseModel):
    """썸네일 저장 요청"""
    image_url: str
    product_name: str


@router.post("/save-thumbnail")
async def save_thumbnail(request: SaveThumbnailRequest):
    """
    외부 URL의 썸네일 이미지를 다운로드하여 Supabase Storage에 저장
    600x600 미만 이미지는 자동으로 리사이즈
    """
    try:
        import requests
        import hashlib
        from datetime import datetime
        from io import BytesIO
        from PIL import Image
        from utils.supabase_storage import upload_image_from_bytes, supabase

        print(f"[DEBUG] save-thumbnail 요청: URL={request.image_url[:100]}...")
        print(f"[DEBUG] save-thumbnail 요청: product_name={request.product_name}")

        # data: URL 처리 (Cloudflare 페이지에서 추출된 경우)
        if request.image_url.startswith('data:'):
            print(f"[DEBUG] data: URL 감지 - Cloudflare 페이지에서 추출된 이미지일 가능성")
            raise HTTPException(
                status_code=400,
                detail="유효한 이미지 URL이 아닙니다. Cloudflare 보호로 인해 실제 상품 이미지를 가져올 수 없습니다."
            )

        # 이미지 다운로드 (Railway 환경 고려하여 타임아웃 증가)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': 'https://www.gmarket.co.kr/',
        }
        response = requests.get(request.image_url, timeout=20, headers=headers)
        print(f"[DEBUG] 이미지 다운로드 응답: status={response.status_code}, size={len(response.content)}")

        if not response.ok:
            raise HTTPException(status_code=400, detail=f"이미지 다운로드 실패: HTTP {response.status_code}")

        # 이미지 열기 및 리사이즈 (600x600 미만인 경우)
        image_data = response.content
        try:
            img = Image.open(BytesIO(image_data))
            width, height = img.size
            min_size = 600

            print(f"[DEBUG] 원본 이미지 크기: {width}x{height}")

            if width < min_size or height < min_size:
                # 비율 유지하면서 최소 600x600으로 확대
                scale = max(min_size / width, min_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)

                print(f"[DEBUG] 이미지 리사이즈: {width}x{height} → {new_width}x{new_height}")

                # 고품질 리사이즈 (LANCZOS 필터)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # RGB 모드로 변환 (RGBA인 경우 JPEG 저장 불가)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # 리사이즈된 이미지를 바이트로 변환
                output = BytesIO()
                img.save(output, format='JPEG', quality=95)
                image_data = output.getvalue()
                print(f"[DEBUG] 리사이즈된 이미지 크기: {len(image_data)} bytes")
        except Exception as resize_err:
            print(f"[DEBUG] 이미지 리사이즈 실패 (원본 사용): {resize_err}")

        # 파일명 생성 (상품명 해시 + 타임스탬프)
        name_hash = hashlib.md5(request.product_name.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 리사이즈된 경우 항상 JPEG
        extension = ".jpg"
        upload_content_type = "image/jpeg"

        filename = f"{name_hash}_{timestamp}{extension}"

        # Supabase 클라이언트 확인
        if not supabase:
            # Fallback: 로컬 파일시스템 사용
            from pathlib import Path
            static_dir = Path(__file__).parent.parent / "static" / "thumbnails"
            static_dir.mkdir(parents=True, exist_ok=True)

            file_path = static_dir / filename
            with open(file_path, 'wb') as f:
                f.write(image_data)

            thumbnail_path = f"/static/thumbnails/{filename}"

            return {
                "success": True,
                "thumbnail_path": thumbnail_path,
                "message": "썸네일이 로컬에 저장되었습니다."
            }

        # Supabase Storage에 업로드
        storage_path = f"thumbnails/{filename}"
        print(f"[DEBUG] Supabase 업로드 시작: path={storage_path}, content_type={upload_content_type}")

        try:
            public_url = upload_image_from_bytes(
                image_data,
                storage_path,
                content_type=upload_content_type
            )
            print(f"[DEBUG] Supabase 업로드 결과: {public_url}")
        except Exception as upload_err:
            print(f"[DEBUG] Supabase 업로드 에러: {upload_err}")
            raise HTTPException(status_code=500, detail=f"Supabase Storage 업로드 실패: {str(upload_err)}")

        if not public_url:
            raise HTTPException(status_code=500, detail="Supabase Storage 업로드 실패: 빈 URL 반환")

        return {
            "success": True,
            "thumbnail_path": public_url,
            "message": "썸네일이 Supabase Storage에 저장되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[DEBUG] save-thumbnail 예외: {str(e)}")
        print(f"[DEBUG] 스택 트레이스:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"썸네일 저장 실패: {str(e)}")

