"""
플레이오토 실시간 모니터링 및 마켓별 통계 API
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional

from playauto.orders import PlayautoOrdersAPI

router = APIRouter(prefix="/api/playauto-monitoring", tags=["Playauto Monitoring"])


@router.get("/monitoring/test")
async def test_monitoring():
    """모니터링 API 테스트"""
    return {"message": "Monitoring API works!", "success": True}


@router.get("/monitoring/by-market")
@router.get("/stats/by-market")
async def get_market_stats(days: int = 7):
    """마켓별 통계 조회"""
    try:
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


@router.get("/monitoring/by-status")
@router.get("/stats/by-status")
async def get_status_stats():
    """주문 상태별 카운트 조회"""
    try:
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


@router.get("/monitoring/recent")
@router.get("/orders/recent")
async def get_recent_orders(minutes: int = 30):
    """최근 주문 조회 (실시간 모니터링용)"""
    try:
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
