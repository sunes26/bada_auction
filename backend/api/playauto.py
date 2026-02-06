"""
플레이오토 API 통합 FastAPI 엔드포인트

주문 수집, 송장 업로드, 설정 관리 등의 API 제공
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from utils.cache import async_cached

from playauto.models import (
    PlayautoSettingsRequest,
    PlayautoSettingsResponse,
    OrdersFetchRequest,
    OrdersFetchResponse,
    UploadTrackingRequest,
    UploadTrackingResponse,
    ConnectionTestResponse,
    SyncLog,
    PlayautoStats
)
from playauto.auth import (
    save_api_credentials_to_db,
    mask_api_key,
    load_api_credentials,
    validate_api_key
)
from playauto.client import PlayautoClient
from playauto.orders import PlayautoOrdersAPI, fetch_and_sync_orders
from playauto.tracking import PlayautoTrackingAPI, auto_upload_tracking_from_local
from playauto.carriers import PlayautoCarriersAPI, get_cached_carriers
from playauto.exceptions import PlayautoAPIError
from database.db_wrapper import get_db

router = APIRouter(prefix="/api/playauto", tags=["Playauto"])


# ========================================
# Request Models
# ========================================

class InvoiceOrderItem(BaseModel):
    """송장 업데이트 주문 항목"""
    bundle_no: str
    carr_no: str
    invoice_no: str


class InvoiceUpdateRequest(BaseModel):
    """송장 업데이트 요청"""
    orders: List[InvoiceOrderItem]
    overwrite: bool = False
    change_complete: bool = True
    dupl_doubt_except_yn: str = "N"


# Debug: Print when module is loaded
import sys
sys.stderr.write(f"\n[PLAYAUTO MODULE LOADED] Total routes defined: {len(router.routes) if hasattr(router, 'routes') else 0}\n")
sys.stderr.flush()


@router.get("/test-new-route-12345")
async def test_new_route():
    """테스트 라우트 - 파일이 로드되는지 확인"""
    return {"message": "New route works!", "success": True}

# After test route
sys.stderr.write(f"[PLAYAUTO] Added test-new-route-12345\n")
sys.stderr.flush()


# ========================================
# 설정 관리 엔드포인트
# ========================================

@router.post("/settings", response_model=dict)
async def save_playauto_settings(request: PlayautoSettingsRequest):
    """플레이오토 API 설정 저장"""
    try:
        # API 키 검증
        if not validate_api_key(request.api_key):
            raise HTTPException(status_code=400, detail="유효하지 않은 API 키 형식입니다")

        # DB에 저장
        success = save_api_credentials_to_db(
            api_key=request.api_key,
            email=request.email,
            password=request.password,
            encrypt=request.encrypt_credentials
        )

        if not success:
            raise HTTPException(status_code=500, detail="설정 저장 실패")

        # 추가 설정 저장
        db = get_db()
        db.save_playauto_setting("api_base_url", request.api_base_url)
        db.save_playauto_setting("enabled", str(request.enabled))
        db.save_playauto_setting("auto_sync_enabled", str(request.auto_sync_enabled))
        db.save_playauto_setting("auto_sync_interval", str(request.auto_sync_interval))

        return {
            "success": True,
            "message": "플레이오토 설정이 저장되었습니다",
            "api_key_masked": mask_api_key(request.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 저장 중 오류: {str(e)}")


@router.get("/settings", response_model=PlayautoSettingsResponse)
async def get_playauto_settings():
    """플레이오토 설정 조회 (API 키 마스킹)"""
    try:
        db = get_db()

        # 설정 로드
        try:
            api_key, email, password = load_api_credentials()
            api_key_masked = mask_api_key(api_key)
        except Exception:
            api_key_masked = "설정되지 않음"

        api_base_url = db.get_playauto_setting("api_base_url") or "https://openapi.playauto.io/api"
        enabled = db.get_playauto_setting("enabled") == "true"
        auto_sync_enabled = db.get_playauto_setting("auto_sync_enabled") == "true"
        auto_sync_interval = int(db.get_playauto_setting("auto_sync_interval") or "30")

        # 마지막 동기화 시각
        logs = db.get_playauto_sync_logs(sync_type="order_fetch", limit=1)
        last_sync_at = None
        if logs:
            last_sync_at = logs[0].get("created_at")

        return PlayautoSettingsResponse(
            api_key_masked=api_key_masked,
            api_base_url=api_base_url,
            enabled=enabled,
            auto_sync_enabled=auto_sync_enabled,
            auto_sync_interval=auto_sync_interval,
            last_sync_at=last_sync_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 조회 중 오류: {str(e)}")


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_playauto_connection():
    """플레이오토 API 연결 테스트"""
    try:
        # API 자격 증명 로드
        api_key, email, password = load_api_credentials()

        # 연결 테스트 (PlayautoClient는 자동으로 자격 증명을 로드함)
        client = PlayautoClient()
        success = client.test_connection()

        if success:
            return ConnectionTestResponse(
                success=True,
                message="플레이오토 API 연결 성공",
                api_key_masked=mask_api_key(api_key),
                base_url=client.base_url
            )
        else:
            return ConnectionTestResponse(
                success=False,
                message="플레이오토 API 연결 실패",
                api_key_masked=mask_api_key(api_key),
                base_url=client.base_url
            )

    except PlayautoAPIError as e:
        return ConnectionTestResponse(
            success=False,
            message=f"API 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연결 테스트 중 오류: {str(e)}")


# ========================================
# 주문 수집 엔드포인트
# ========================================

@router.get("/orders", response_model=OrdersFetchResponse)
async def fetch_playauto_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market: Optional[str] = None,
    order_status: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
    auto_sync: bool = False,
    # 신규 파라미터 (고급 필터링)
    bundle_yn: bool = False,
    search_key: Optional[str] = None,
    search_word: Optional[str] = None,
    status: Optional[str] = None,  # 쉼표 구분 ("신규주문,출고대기")
    background_tasks: BackgroundTasks = None
):
    """
    플레이오토에서 주문 수집 (고급 필터링 지원)

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        market: 마켓 필터 (쇼핑몰 코드)
        order_status: 단일 주문 상태 필터 (레거시)
        page: 페이지 번호
        limit: 페이지당 항목 수
        auto_sync: 자동 동기화 여부
        bundle_yn: 묶음 주문 그룹화
        search_key: 검색 필드 (order_name, shop_ord_no 등)
        search_word: 검색어
        status: 다중 주문 상태 필터 (쉼표 구분)
        background_tasks: 백그라운드 작업
    """
    try:
        import time
        start_time = time.time()

        # 상태 필터 파싱 (다중 상태 지원)
        status_list = None
        if status:
            # 쉼표로 구분된 다중 상태
            status_list = [s.strip() for s in status.split(",")]
        elif order_status:
            # 레거시 단일 상태
            status_list = [order_status]

        # 페이지네이션 계산 (start/length 방식)
        start = (page - 1) * limit

        # 주문 수집
        if auto_sync:
            # 자동 동기화 모드
            result = await fetch_and_sync_orders(
                start_date=start_date,
                end_date=end_date,
                market=market
            )
            synced_count = result.get("synced_count", 0)
            orders = []
            total = result.get("total_orders", 0)
        else:
            # 조회만 (새로운 파라미터 전달)
            orders_api = PlayautoOrdersAPI()
            result = await orders_api.fetch_orders(
                start_date=start_date,
                end_date=end_date,
                order_status=status_list,
                market=market,
                start=start,
                length=limit,
                bundle_yn=bundle_yn,
                search_key=search_key,
                search_word=search_word,
                page=page,
                limit=limit
            )
            orders = result.get("orders", [])
            total = result.get("total", 0)
            synced_count = 0

        # 실행 시간
        execution_time = time.time() - start_time

        # 로그 기록
        db = get_db()
        db.add_playauto_sync_log(
            sync_type="order_fetch",
            status="success" if result.get("success") else "failed",
            items_count=total,
            success_count=synced_count,
            execution_time=execution_time
        )

        return OrdersFetchResponse(
            success=True,
            total=total,
            page=page,
            orders=orders,
            synced_count=synced_count
        )

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"주문 수집 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 수집 중 오류: {str(e)}")


@router.post("/orders/sync")
async def sync_playauto_orders_to_local(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market: Optional[str] = None
):
    """플레이오토 주문을 로컬 DB에 동기화"""
    try:
        result = await fetch_and_sync_orders(
            start_date=start_date,
            end_date=end_date,
            market=market
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 동기화 중 오류: {str(e)}")


@router.get("/orders/status")
async def get_order_sync_status():
    """주문 동기화 상태 확인"""
    try:
        db = get_db()

        # 미동기화 주문 수
        unsynced_orders = db.get_unsynced_market_orders(limit=1000)
        unsynced_count = len(unsynced_orders)

        # 최근 동기화 로그
        recent_logs = db.get_playauto_sync_logs(sync_type="order_fetch", limit=5)

        return {
            "unsynced_count": unsynced_count,
            "recent_logs": recent_logs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 중 오류: {str(e)}")


# ========================================
# 송장 업로드 엔드포인트
# ========================================

@router.post("/upload-tracking", response_model=UploadTrackingResponse)
async def upload_tracking_numbers(request: UploadTrackingRequest):
    """송장번호 일괄 업로드"""
    try:
        import time
        start_time = time.time()

        # 송장 데이터 변환
        tracking_data = [item.dict() for item in request.tracking_data]

        # 업로드
        tracking_api = PlayautoTrackingAPI()
        result = await tracking_api.upload_tracking(tracking_data)

        # 실행 시간
        execution_time = time.time() - start_time

        # 로그 기록
        db = get_db()
        db.add_playauto_sync_log(
            sync_type="tracking_upload",
            status="success" if result.get("success") else "failed",
            items_count=result.get("total_count", 0),
            success_count=result.get("success_count", 0),
            fail_count=result.get("fail_count", 0),
            execution_time=execution_time
        )

        return UploadTrackingResponse(**result)

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"송장 업로드 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"송장 업로드 중 오류: {str(e)}")


@router.post("/upload-tracking/auto")
async def auto_upload_tracking(days: int = 7):
    """완료된 주문 송장 자동 업로드 (최근 N일)"""
    try:
        result = await auto_upload_tracking_from_local(days=days)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자동 송장 업로드 중 오류: {str(e)}")


@router.get("/tracking-upload-history")
async def get_tracking_upload_history(limit: int = 50):
    """송장 업로드 이력 조회"""
    try:
        db = get_db()
        logs = db.get_playauto_sync_logs(sync_type="tracking_upload", limit=limit)

        return {
            "success": True,
            "logs": logs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이력 조회 중 오류: {str(e)}")


# ========================================
# 로그 및 통계 엔드포인트
# ========================================

@router.get("/sync-logs")
async def get_playauto_sync_logs(
    sync_type: Optional[str] = None,
    limit: int = 100
):
    """플레이오토 동기화 로그 조회"""
    try:
        db = get_db()
        logs = db.get_playauto_sync_logs(sync_type=sync_type, limit=limit)

        return {
            "success": True,
            "logs": logs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 조회 중 오류: {str(e)}")


# ========================================
# 실시간 모니터링 엔드포인트
# ========================================

@router.get("/stats/by-market")
async def get_market_stats(days: int = 7):
    """마켓별 통계 조회"""
    try:
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        orders_api = PlayautoOrdersAPI()
        result = await orders_api.fetch_orders(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        orders = result.get('orders', [])

        # 마켓별 집계
        market_stats = {}
        for order in orders:
            market = order.get('shop_name', '기타')
            if market not in market_stats:
                market_stats[market] = {
                    'market': market,
                    'order_count': 0,
                    'total_amount': 0,
                }

            market_stats[market]['order_count'] += 1
            market_stats[market]['total_amount'] += order.get('total_amount', 0)

        # 전일 대비 증감률 계산
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=days)

        prev_result = await orders_api.fetch_orders(
            start_date=prev_start_date.strftime('%Y-%m-%d'),
            end_date=prev_end_date.strftime('%Y-%m-%d')
        )

        prev_orders = prev_result.get('orders', [])
        prev_market_counts = {}
        for order in prev_orders:
            market = order.get('shop_name', '기타')
            prev_market_counts[market] = prev_market_counts.get(market, 0) + 1

        # 증감률 계산
        for market, stats in market_stats.items():
            prev_count = prev_market_counts.get(market, 0)
            curr_count = stats['order_count']

            if prev_count == 0:
                change_percent = 100 if curr_count > 0 else 0
            else:
                change_percent = ((curr_count - prev_count) / prev_count) * 100

            stats['change_percent'] = round(change_percent, 1)
            stats['prev_count'] = prev_count

        # 리스트로 변환 (주문 수 기준 정렬)
        market_list = sorted(market_stats.values(), key=lambda x: x['order_count'], reverse=True)

        return {
            "success": True,
            "markets": market_list,
            "total_orders": len(orders),
            "period_days": days
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"마켓별 통계 조회 중 오류: {str(e)}")


@router.get("/stats/by-status")
async def get_status_stats():
    """주문 상태별 카운트 조회"""
    try:
        from datetime import datetime, timedelta

        orders_api = PlayautoOrdersAPI()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        result = await orders_api.fetch_orders(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        orders = result.get('orders', [])

        # 상태별 집계
        status_counts = {}
        for order in orders:
            status = order.get('order_status', '기타')
            status_counts[status] = status_counts.get(status, 0) + 1

        # 일반적인 주문 상태 순서
        status_order = ['신규주문', '발주확인', '상품준비중', '배송중', '배송완료', '취소', '반품', '교환']

        # 정렬된 리스트 생성
        status_list = []
        for status in status_order:
            if status in status_counts:
                status_list.append({
                    'status': status,
                    'count': status_counts[status]
                })

        # 나머지 상태 추가
        for status, count in status_counts.items():
            if status not in status_order:
                status_list.append({
                    'status': status,
                    'count': count
                })

        return {
            "success": True,
            "status_counts": status_list,
            "total_orders": len(orders)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태별 통계 조회 중 오류: {str(e)}")


@router.get("/orders/recent")
async def get_recent_orders(minutes: int = 30):
    """최근 주문 조회 (실시간 모니터링용)"""
    try:
        from datetime import datetime, timedelta

        orders_api = PlayautoOrdersAPI()

        # 최근 N분간의 주문 조회
        end_date = datetime.now()
        start_date = end_date - timedelta(minutes=minutes)

        result = await orders_api.fetch_orders(
            start_date=start_date.strftime('%Y-%m-%d %H:%M:%S'),
            end_date=end_date.strftime('%Y-%m-%d %H:%M:%S')
        )

        orders = result.get('orders', [])

        # 최신순 정렬
        orders.sort(key=lambda x: x.get('order_date', ''), reverse=True)

        return {
            "success": True,
            "orders": orders[:10],  # 최대 10개만 반환
            "total_count": len(orders),
            "check_time": end_date.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최근 주문 조회 중 오류: {str(e)}")

# Debug: Confirm monitoring routes added
sys.stderr.write(f"[PLAYAUTO] Monitoring routes added. Total routes now: {len(router.routes)}\n")
sys.stderr.flush()


@router.get("/stats", response_model=PlayautoStats)
@async_cached(ttl=60)  # 1분 캐싱
async def get_playauto_stats():
    """플레이오토 연동 통계"""
    try:
        db = get_db()
        stats = db.get_playauto_stats()

        return PlayautoStats(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류: {str(e)}")


# ========================================
# 주문 관리 엔드포인트 (상태변경, 수정, 삭제)
# ========================================

@router.patch("/orders/status")
async def update_order_status(
    bundle_codes: Optional[list] = None,
    unliqs: Optional[list] = None,
    status: str = "신규주문"
):
    """주문 상태 변경"""
    try:
        orders_api = PlayautoOrdersAPI()
        result = await orders_api.update_order_status(
            bundle_codes=bundle_codes,
            unliqs=unliqs,
            status=status
        )
        return result

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"주문 상태 변경 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 상태 변경 중 오류: {str(e)}")


@router.patch("/orders/{unliq}")
async def update_order(unliq: str, update_data: dict):
    """주문 정보 수정"""
    try:
        orders_api = PlayautoOrdersAPI()
        result = await orders_api.update_order(unliq, update_data)
        return result

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"주문 수정 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 수정 중 오류: {str(e)}")


@router.delete("/orders")
async def delete_orders(unliq_list: list):
    """주문 삭제"""
    try:
        orders_api = PlayautoOrdersAPI()
        result = await orders_api.delete_orders(unliq_list)
        return result

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"주문 삭제 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 삭제 중 오류: {str(e)}")


@router.put("/orders/hold")
async def hold_orders(bundle_codes: list, hold_reason: str, status: str = "주문보류"):
    """주문 보류 처리"""
    try:
        orders_api = PlayautoOrdersAPI()
        result = await orders_api.hold_orders(bundle_codes, hold_reason, status)
        return result

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"주문 보류 처리 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 보류 처리 중 오류: {str(e)}")


@router.put("/orders/instruction")
async def send_order_instruction(
    bundle_codes: Optional[list] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auto_bundle: bool = False,
    dupl_doubt_except_yn: str = "N"
):
    """
    출고 지시 (신규주문 → 출고대기)

    Args:
        bundle_codes: 주문묶음번호 리스트 (선택)
        start_date: 조회 시작일 (YYYY-MM-DD) - bundle_codes 미입력시 필수
        end_date: 조회 종료일 (YYYY-MM-DD) - bundle_codes 미입력시 필수
        auto_bundle: 주문 묶음 여부 (true: 자동 묶음 처리)
        dupl_doubt_except_yn: 중복의심주문 제외 여부 ('Y' or 'N')

    Returns:
        {"results": "성공"} 또는 에러 응답
    """
    try:
        orders_api = PlayautoOrdersAPI()
        result = await orders_api.send_instruction(
            bundle_codes=bundle_codes,
            start_date=start_date,
            end_date=end_date,
            auto_bundle=auto_bundle,
            dupl_doubt_except_yn=dupl_doubt_except_yn
        )

        return {
            "success": True,
            "message": "출고 지시가 완료되었습니다",
            "result": result
        }

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"출고 지시 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"출고 지시 중 오류: {str(e)}")


@router.put("/orders/invoice")
async def update_order_invoice(request: InvoiceUpdateRequest):
    """
    배송정보 업데이트 (송장번호 입력 → 출고완료)

    Args:
        request: InvoiceUpdateRequest
            - orders: 변경할 주문 데이터 리스트
                    [{"bundle_no": "묶음번호", "carr_no": "택배사코드", "invoice_no": "송장번호"}]
            - overwrite: 이미 송장번호가 입력되어있는 주문일경우 덮어쓸지 여부
            - change_complete: 출고완료로 변경할지 여부
            - dupl_doubt_except_yn: 중복의심주문 제외 여부 ('Y' or 'N')

    Returns:
        [{"bundle_no": "묶음번호", "result": "성공", "message": ""}] 배열

    택배사 코드:
        4: CJ대한통운
        5: 한진택배
        8: 롯데택배
        1: 우체국택배
        6: 로젠택배
    """
    try:
        orders_api = PlayautoOrdersAPI()
        # Pydantic 모델을 dict로 변환
        orders_data = [order.dict() for order in request.orders]
        result = await orders_api.update_invoice(
            orders=orders_data,
            overwrite=request.overwrite,
            change_complete=request.change_complete,
            dupl_doubt_except_yn=request.dupl_doubt_except_yn
        )

        return {
            "success": True,
            "message": "송장번호가 업데이트되었습니다",
            "results": result
        }

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"송장 업데이트 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"송장 업데이트 중 오류: {str(e)}")


# ========================================
# 택배사 코드 조회 엔드포인트
# ========================================

@router.get("/carriers")
@async_cached(ttl=3600)  # 1시간 캐싱
async def get_carriers():
    """택배사 코드 조회"""
    try:
        carriers = await get_cached_carriers()
        return {
            "success": True,
            "carriers": carriers
        }

    except PlayautoAPIError as e:
        raise HTTPException(status_code=500, detail=f"택배사 조회 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"택배사 조회 중 오류: {str(e)}")


# ========================================
# 템플릿 관리 엔드포인트
# ========================================

@router.get("/templates")
async def get_templates():
    """플레이오토 템플릿 목록 조회"""
    try:
        from playauto.templates import PlayautoTemplatesAPI

        templates_api = PlayautoTemplatesAPI()
        result = await templates_api.get_templates()

        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "템플릿 조회 실패"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 조회 중 오류: {str(e)}")


@router.post("/templates/save-default")
async def save_default_template(request: dict):
    """
    기본 템플릿 설정 저장

    Args:
        request: {
            "templates": [
                {
                    "shop_cd": "쇼핑몰코드",
                    "shop_id": "쇼핑몰ID",
                    "template_no": 템플릿번호,
                    "template_name": "템플릿이름"
                }
            ]
        }
    """
    try:
        templates = request.get("templates", [])

        if not templates:
            raise HTTPException(status_code=400, detail="템플릿 정보가 필요합니다.")

        db = get_db()

        # JSON으로 저장
        import json
        db.save_playauto_setting(
            key="default_templates",
            value=json.dumps(templates, ensure_ascii=False),
            notes="상품 등록 시 사용할 기본 템플릿"
        )

        return {
            "success": True,
            "message": "기본 템플릿이 저장되었습니다.",
            "templates": templates
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 저장 실패: {str(e)}")


@router.get("/templates/default")
async def get_default_templates():
    """저장된 기본 템플릿 조회"""
    try:
        db = get_db()

        templates_json = db.get_playauto_setting("default_templates")

        if not templates_json:
            return {
                "success": True,
                "templates": []
            }

        import json
        templates = json.loads(templates_json)

        return {
            "success": True,
            "templates": templates
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기본 템플릿 조회 실패: {str(e)}")



