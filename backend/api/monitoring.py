"""
상품 모니터링 API 엔드포인트 - FlareSolverr 기반 (Selenium 제거)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import re

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
    URL에서 상품 정보 자동 추출 - FlareSolverr 기반
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
        elif 'gsshop.com' in product_url:
            source = 'gsshop'
        elif 'cjthemarket.com' in product_url:
            source = 'cjthemarket'
        elif 'otokimall.com' in product_url:
            source = 'otokimall'
        elif 'dongwonmall.com' in product_url:
            source = 'dongwonmall'
        elif 'smartstore.naver.com' in product_url:
            source = 'smartstore'
        elif 'domeggook.com' in product_url:
            source = 'domeggook'
        # else: source는 이미 'other'로 설정되어 있음 - 범용 추출 시도

        # 스마트스토어 경고
        if source == 'smartstore':
            return {
                "success": False,
                "error": "smartstore_captcha",
                "message": "네이버 스마트스토어가 CAPTCHA로 자동 접근을 차단했습니다. 상품 정보를 수동으로 입력해주세요."
            }

        # 도매꾹 수동 입력 안내
        if source == 'domeggook':
            # 도매꾹 스크래퍼로 상품명만 추출 시도
            try:
                from sourcing.domeggook import DomeggookScraper
                scraper = DomeggookScraper()
                result = scraper.extract_product_info(product_url)

                product_name = result.get('product_name', '')
                thumbnail = result.get('thumbnail', '')

                return {
                    "success": True,
                    "manual_input_required": True,
                    "source": "domeggook",
                    "product_name": product_name,
                    "thumbnail": thumbnail,
                    "price": None,
                    "original_price": None,
                    "message": "도매꾹은 사업자 전용 사이트로 로그인이 필요합니다. 가격 정보를 직접 입력해주세요.",
                    "note": "상품명과 썸네일은 자동으로 추출되었습니다. 소싱가와 판매가를 입력해주세요."
                }
            except Exception as e:
                print(f"[DOMEGGOOK] 상품명 추출 실패: {e}")
                return {
                    "success": True,
                    "manual_input_required": True,
                    "source": "domeggook",
                    "product_name": "",
                    "price": None,
                    "original_price": None,
                    "message": "도매꾹은 사업자 전용 사이트로 로그인이 필요합니다. 상품 정보를 직접 입력해주세요."
                }

        print(f"[EXTRACT] URL 정보 추출 시작: {product_url}")
        print(f"[EXTRACT] 감지된 소스: {source}")

        # FlareSolverr로 HTML 가져오기
        html = None
        flaresolverr_result = solve_cloudflare(product_url, max_timeout=60000)

        if flaresolverr_result and flaresolverr_result.get('html'):
            html = flaresolverr_result.get('html', '')
            print(f"[FLARESOLVERR] HTML 수신 완료 (길이: {len(html)})")
        else:
            # FlareSolverr 실패 시 requests로 시도
            import requests as req
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            try:
                response = req.get(product_url, headers=headers, timeout=15)
                response.raise_for_status()
                html = response.text
                print(f"[REQUESTS] HTML 수신 완료 (길이: {len(html)})")
            except Exception as e:
                print(f"[REQUESTS] 실패: {e}")

        if not html:
            raise HTTPException(status_code=503, detail="페이지를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")

        # BeautifulSoup으로 파싱
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # 페이지 차단 확인
        page_title = soup.title.string if soup.title else ""
        cloudflare_indicators = ['just a moment', 'checking your browser', '사용자 활동 검토', '차단', 'blocked']
        if any(indicator in str(page_title).lower() for indicator in cloudflare_indicators):
            raise HTTPException(
                status_code=503,
                detail=f"사이트 보안 시스템에 의해 접근이 차단되었습니다. 잠시 후 다시 시도해주세요."
            )

        # ProductMonitor 사용하여 데이터 추출
        monitor = ProductMonitor()
        extraction_method = None  # 범용 추출 시에만 사용

        # 알려진 소스인 경우: 기존 방식으로 추출
        if source != 'other':
            # 상품명 추출
            product_name = monitor._extract_product_name(soup, product_url)
            print(f"[EXTRACT] 상품명: {product_name}")

            # 가격 추출
            current_price = monitor._extract_price(soup, product_url)
            print(f"[EXTRACT] 가격: {current_price}")

            # 썸네일 추출
            thumbnail_url = monitor._extract_thumbnail(soup, product_url)
            print(f"[EXTRACT] 썸네일: {thumbnail_url}")

            # 상태 체크 - 소스별 전용 함수 사용
            status = 'available'
            status_details = '정상'

            if source == 'cjthemarket':
                status_result = monitor._check_cjthemarket_status(soup)
                status = status_result.get('status', 'available')
                status_details = status_result.get('details', '정상')
                # 판매종료 상품인 경우 가격/상품명 무효화
                if status == 'discontinued':
                    current_price = None
                    product_name = None
                print(f"[EXTRACT] CJ더마켓 상태: {status} ({status_details})")
            elif source == 'otokimall':
                status_result = monitor._check_otokimall_status(soup)
                status = status_result.get('status', 'available')
                status_details = status_result.get('details', '정상')
                print(f"[EXTRACT] 오뚜기몰 상태: {status} ({status_details})")
            elif source == 'dongwonmall':
                status_result = monitor._check_dongwonmall_status(soup)
                status = status_result.get('status', 'available')
                status_details = status_result.get('details', '정상')
                print(f"[EXTRACT] 동원몰 상태: {status} ({status_details})")
            elif source == 'ssg':
                status_result = monitor._check_ssg_status(soup)
                status = status_result.get('status', 'available')
                status_details = status_result.get('details', '정상')
                print(f"[EXTRACT] SSG 상태: {status} ({status_details})")
            elif source == '11st':
                status_result = monitor._check_11st_status(soup)
                status = status_result.get('status', 'available')
                status_details = status_result.get('details', '정상')
                print(f"[EXTRACT] 11번가 상태: {status} ({status_details})")
            elif source == 'gsshop':
                status_result = monitor._check_gsshop_status(soup)
                status = status_result.get('status', 'available')
                status_details = status_result.get('details', '정상')
                print(f"[EXTRACT] GS샵 상태: {status} ({status_details})")
            else:
                # 기본 키워드 체크
                page_text = soup.get_text().lower()
                if '품절' in page_text or 'sold out' in page_text:
                    status = 'out_of_stock'
                elif '판매종료' in page_text or '단종' in page_text:
                    status = 'discontinued'
        else:
            # 알 수 없는 소스: 범용 추출 시도 (JSON-LD → 메타태그 → Microdata → CSS패턴)
            print(f"[EXTRACT] 범용 추출 모드 시작...")
            generic_result = monitor.extract_generic_product_info(soup, product_url)

            if generic_result:
                product_name = generic_result.get('product_name')
                current_price = generic_result.get('price')
                thumbnail_url = generic_result.get('thumbnail')
                status = generic_result.get('status', 'available')
                extraction_method = generic_result.get('extraction_method', 'unknown')
                print(f"[EXTRACT] 범용 추출 성공 (방법: {extraction_method})")
                print(f"[EXTRACT] 상품명: {product_name}")
                print(f"[EXTRACT] 가격: {current_price}")
                print(f"[EXTRACT] 썸네일: {thumbnail_url}")
            else:
                # 범용 추출도 실패
                print(f"[EXTRACT] 범용 추출 실패")
                raise HTTPException(
                    status_code=400,
                    detail="상품 정보 추출 실패: 이 사이트에서 상품 정보를 자동으로 추출할 수 없습니다. 상품명과 가격을 수동으로 입력해주세요."
                )

        # 썸네일 다운로드 및 저장
        if thumbnail_url:
            try:
                from utils.image_downloader import download_thumbnail
                saved_thumbnail = download_thumbnail(thumbnail_url)
                if saved_thumbnail:
                    thumbnail_url = saved_thumbnail
                    print(f"[EXTRACT] 썸네일 저장 완료: {thumbnail_url}")
            except Exception as e:
                print(f"[EXTRACT] 썸네일 저장 실패: {e}")

        # 추출 방법 정보 설정
        if source == 'other':
            details = f"범용 추출 ({extraction_method})"
        else:
            details = "FlareSolverr로 추출"

        return {
            "success": True,
            "data": {
                "source": source,
                "product_name": product_name or "자동 감지 실패",
                "current_price": current_price,
                "status": status,
                "details": details,
                "thumbnail_url": thumbnail_url
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
    URL에서 대표 썸네일 이미지 추출 - FlareSolverr 기반
    """
    try:
        product_url = request.get('product_url')
        if not product_url:
            raise HTTPException(status_code=400, detail="URL이 필요합니다.")

        # FlareSolverr로 HTML 가져오기
        flaresolverr_result = solve_cloudflare(product_url, max_timeout=60000)

        if not flaresolverr_result or not flaresolverr_result.get('html'):
            raise HTTPException(status_code=503, detail="페이지를 가져올 수 없습니다.")

        html = flaresolverr_result.get('html', '')

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # 썸네일 추출
        monitor = ProductMonitor()
        thumbnail_url = monitor._extract_thumbnail(soup, product_url)

        return {
            "success": True,
            "thumbnail_url": thumbnail_url
        }

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

        # 고해상도 이미지 URL 변환 시도
        image_url = request.image_url

        # G마켓/옥션: 이미지 크기 파라미터 확대 (300 → 800)
        if 'gmarket.co.kr' in image_url or 'auction.co.kr' in image_url:
            high_res_url = re.sub(r'/(\d{2,3})([/?]|$)', r'/800\2', image_url)
            if high_res_url != image_url:
                print(f"[DEBUG] 고해상도 URL 시도: {high_res_url[:100]}...")
                image_url = high_res_url

        # SSG/이마트: _300.jpg → _800.jpg
        if 'ssgcdn.com' in image_url or 'ssg.com' in image_url:
            high_res_url = re.sub(r'_(\d{2,3})\.(jpg|jpeg|png|webp)', r'_800.\2', image_url, flags=re.IGNORECASE)
            if high_res_url != image_url:
                print(f"[DEBUG] SSG 고해상도 URL 시도: {high_res_url[:100]}...")
                image_url = high_res_url

        # GS샵: 이미지 크기 파라미터 확대
        if 'gsshop.com' in image_url or 'gstatic.gsshop.com' in image_url:
            high_res_url = re.sub(r'[?&](width|height)=\d+', r'?\1=800', image_url)
            high_res_url = re.sub(r'/(\d{2,3})/', r'/800/', high_res_url)
            if high_res_url != image_url:
                print(f"[DEBUG] GS샵 고해상도 URL 시도: {high_res_url[:100]}...")
                image_url = high_res_url

        # 이미지 다운로드 (Railway 환경 고려하여 타임아웃 증가)
        # URL에 따라 동적으로 Referer 설정 (핫링킹 방지 우회)
        referer = 'https://www.gmarket.co.kr/'  # 기본값
        if 'domeggook.com' in image_url:
            referer = 'https://domeggook.com/'
        elif 'ssgcdn.com' in image_url or 'ssg.com' in image_url:
            referer = 'https://www.ssg.com/'
        elif 'smartstore.naver.com' in image_url or 'shopping.naver.com' in image_url:
            referer = 'https://smartstore.naver.com/'
        elif '11st.co.kr' in image_url:
            referer = 'https://www.11st.co.kr/'
        elif 'auction.co.kr' in image_url:
            referer = 'https://www.auction.co.kr/'
        elif 'coupang.com' in image_url:
            referer = 'https://www.coupang.com/'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': referer,
        }

        # 고해상도 URL 먼저 시도, 실패 시 원본 URL
        response = requests.get(image_url, timeout=20, headers=headers)
        if not response.ok and image_url != request.image_url:
            print(f"[DEBUG] 고해상도 URL 실패, 원본 URL 시도")
            response = requests.get(request.image_url, timeout=20, headers=headers)
        print(f"[DEBUG] 이미지 다운로드 응답: status={response.status_code}, size={len(response.content)}")

        if not response.ok:
            # 403 에러 (핫링킹 방지) 시 원본 URL 그대로 사용
            if response.status_code == 403:
                print(f"[WARN] 이미지 다운로드 차단됨 (403) - 원본 URL 그대로 사용")
                print(f"[WARN] 브라우저에서는 정상적으로 표시될 수 있습니다: {request.image_url}")
                return {
                    "success": True,
                    "thumbnail_path": request.image_url,  # 원본 URL 그대로 반환
                    "message": "이미지가 핫링킹 방지로 차단되어 원본 URL을 사용합니다"
                }
            raise HTTPException(status_code=400, detail=f"이미지 다운로드 실패: HTTP {response.status_code}")

        # 이미지 열기 및 JPEG 변환 (webp 등 다른 포맷도 JPEG로 통일)
        image_data = response.content
        try:
            from PIL import ImageFilter, ImageEnhance

            img = Image.open(BytesIO(image_data))
            width, height = img.size
            min_size = 600

            print(f"[DEBUG] 원본 이미지 크기: {width}x{height}, 포맷: {img.format}")

            # RGB 모드로 먼저 변환 (RGBA, P 모드인 경우)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 리사이즈가 필요한 경우
            if width < min_size or height < min_size:
                # 비율 유지하면서 최소 600x600으로 확대
                scale = max(min_size / width, min_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)

                print(f"[DEBUG] 이미지 리사이즈: {width}x{height} → {new_width}x{new_height} (scale: {scale:.2f}x)")

                # 고품질 리사이즈 (LANCZOS 필터)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # 확대 시 화질 개선: 언샤프 마스크 적용 (선명도 향상)
                img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

                # 대비 약간 증가 (1.05 = 5% 증가)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.05)

                print(f"[DEBUG] 이미지 선명화 및 대비 보정 적용")

            # 항상 JPEG로 변환하여 저장 (webp, png 등 모든 포맷 통일)
            output = BytesIO()
            img.save(output, format='JPEG', quality=98, subsampling=0)
            image_data = output.getvalue()
            print(f"[DEBUG] JPEG 변환 완료: {len(image_data)} bytes")
        except Exception as resize_err:
            print(f"[DEBUG] 이미지 변환 실패 (원본 사용): {resize_err}")

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
