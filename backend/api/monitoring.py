"""
상품 모니터링 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database.db import get_db
from monitor.product_monitor import ProductMonitor
from utils.cache import async_cached
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
        elif 'smartstore.naver.com' in product_url:
            source = 'smartstore'
        elif 'gmarket.co.kr' in product_url:
            source = 'gmarket'
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 URL입니다. SSG, 홈플러스/Traders, 11번가, 스마트스토어, G마켓 URL을 입력해주세요.")

        # 모니터로 상품 정보 추출
        monitor = ProductMonitor()

        # 모든 마켓에서 Selenium 사용 (정확도 우선)
        print(f"[SELENIUM] 정확한 추출을 위해 Selenium 사용")
        monitor._init_driver()

        try:
            monitor.driver.get(product_url)
            import time
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import UnexpectedAlertPresentException

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

            # 사이트별 대기 시간 조정 (최적화됨)
            if 'smartstore.naver.com' in product_url:
                time.sleep(3)  # 스마트스토어 (7초 → 3초)
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

            # 상품명 추출 (페이지가 로드된 상태에서)
            try:
                product_name = monitor.extract_product_name(product_url, source)
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
            elif 'smartstore.naver.com' in product_url:
                result = monitor._check_smartstore_status()
            elif 'gmarket.co.kr' in product_url:
                result = monitor._check_gmarket_status()
            else:
                result = monitor._check_generic_status()

            # 썸네일 추출 및 다운로드 (이미 로드된 페이지에서)
            logger.debug("썸네일 추출 중...")
            thumbnail_url = None
            thumbnail_path = None
            try:
                # 썸네일 URL 추출
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
                logger.debug(f"썸네일 URL: {thumbnail_url}")

                # 썸네일 다운로드
                if thumbnail_url:
                    from utils.image_downloader import download_thumbnail
                    thumbnail_path = download_thumbnail(thumbnail_url)
                    logger.info(f"썸네일 저장 완료: {thumbnail_path}")

            except Exception as e:
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
    """
    try:
        import requests
        import hashlib
        from datetime import datetime
        from utils.supabase_storage import upload_image_from_bytes, supabase

        # 이미지 다운로드
        response = requests.get(request.image_url, timeout=10)
        if not response.ok:
            raise HTTPException(status_code=400, detail="이미지 다운로드 실패")

        # 파일명 생성 (상품명 해시 + 타임스탬프)
        name_hash = hashlib.md5(request.product_name.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = ".jpg"  # 기본값

        # Content-Type에서 확장자 추출
        content_type = response.headers.get('content-type', '')
        if 'png' in content_type:
            extension = '.png'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            extension = '.jpg'

        filename = f"{name_hash}_{timestamp}{extension}"

        # Supabase 클라이언트 확인
        if not supabase:
            # Fallback: 로컬 파일시스템 사용
            from pathlib import Path
            static_dir = Path(__file__).parent.parent / "static" / "thumbnails"
            static_dir.mkdir(parents=True, exist_ok=True)

            file_path = static_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)

            thumbnail_path = f"/static/thumbnails/{filename}"

            return {
                "success": True,
                "thumbnail_path": thumbnail_path,
                "message": "썸네일이 로컬에 저장되었습니다."
            }

        # Supabase Storage에 업로드
        storage_path = f"thumbnails/{filename}"
        public_url = upload_image_from_bytes(
            response.content,
            storage_path,
            content_type=content_type or "image/jpeg"
        )

        if not public_url:
            raise HTTPException(status_code=500, detail="Supabase Storage 업로드 실패")

        return {
            "success": True,
            "thumbnail_path": public_url,
            "message": "썸네일이 Supabase Storage에 저장되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"썸네일 저장 실패: {str(e)}")

