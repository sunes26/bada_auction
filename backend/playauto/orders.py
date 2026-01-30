"""
플레이오토 주문 수집 API

여러 마켓에서 주문을 자동으로 수집하는 기능
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .client import PlayautoClient
from .models import PlayautoOrder, OrderItem
from .exceptions import PlayautoAPIError


class PlayautoOrdersAPI:
    """플레이오토 주문 수집 API"""

    def __init__(self, client: Optional[PlayautoClient] = None):
        """
        Args:
            client: PlayautoClient 인스턴스 (제공되지 않으면 새로 생성)
        """
        self.client = client

    async def fetch_orders(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        order_status: Optional[str] = None,
        market: Optional[str] = None,
        page: int = 1,
        limit: int = 100
    ) -> Dict:
        """
        주문 목록 수집

        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            order_status: 주문 상태 필터
            market: 마켓 필터 (coupang, naver, 11st 등)
            page: 페이지 번호
            limit: 페이지당 항목 수

        Returns:
            주문 목록 응답
        """
        # 날짜 기본값 설정 (최근 7일)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 쿼리 파라미터 구성
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
            "limit": limit
        }

        if order_status:
            params["order_status"] = order_status
        if market:
            params["market"] = market

        # 클라이언트가 없으면 새로 생성
        if not self.client:
            async with PlayautoClient() as client:
                response = await client.get("/order", params=params)
        else:
            response = await self.client.get("/order", params=params)

        # 응답 데이터 파싱
        return self._parse_orders_response(response)

    async def get_order_detail(self, playauto_order_id: str) -> PlayautoOrder:
        """
        주문 상세 조회

        Args:
            playauto_order_id: 플레이오토 주문 ID

        Returns:
            주문 상세 정보
        """
        # 클라이언트가 없으면 새로 생성
        if not self.client:
            async with PlayautoClient() as client:
                response = await client.get(f"/order", params={"unliq": playauto_order_id})
        else:
            response = await self.client.get(f"/order", params={"unliq": playauto_order_id})

        # 응답 데이터 파싱
        return self._parse_order(response.get("order", {}))

    def _parse_orders_response(self, response: Dict) -> Dict:
        """
        주문 목록 응답 파싱

        Args:
            response: API 응답 데이터

        Returns:
            파싱된 주문 목록
        """
        try:
            # API 응답 구조에 맞게 파싱 (플레이오토 API 문서 참조)
            orders_data = response.get("data", {}).get("orders", [])
            total = response.get("data", {}).get("total", 0)
            page = response.get("data", {}).get("page", 1)

            # 주문 목록 파싱
            orders = [self._parse_order(order_data) for order_data in orders_data]

            return {
                "success": True,
                "total": total,
                "page": page,
                "orders": [order.dict() for order in orders]
            }

        except Exception as e:
            print(f"[ERROR] 주문 목록 파싱 실패: {e}")
            return {
                "success": False,
                "total": 0,
                "page": 1,
                "orders": []
            }

    def _parse_order(self, order_data: Dict) -> PlayautoOrder:
        """
        개별 주문 데이터 파싱

        Args:
            order_data: 주문 원본 데이터

        Returns:
            PlayautoOrder 인스턴스
        """
        try:
            # 주문 상품 목록 파싱
            items_data = order_data.get("items", [])
            items = []

            for item_data in items_data:
                item = OrderItem(
                    product_name=item_data.get("product_name", "Unknown"),
                    product_url=item_data.get("product_url", ""),
                    quantity=item_data.get("quantity", 1),
                    price=float(item_data.get("price", 0)),
                    option=item_data.get("option", "")
                )
                items.append(item)

            # 주문 일시 파싱
            order_date_str = order_data.get("order_date")
            order_date = None
            if order_date_str:
                try:
                    order_date = datetime.fromisoformat(order_date_str)
                except Exception:
                    pass

            # PlayautoOrder 인스턴스 생성
            order = PlayautoOrder(
                playauto_order_id=order_data.get("playauto_order_id", ""),
                market=order_data.get("market", "unknown"),
                order_number=order_data.get("order_number", ""),
                customer_name=order_data.get("customer_name", ""),
                customer_phone=order_data.get("customer_phone", ""),
                customer_address=order_data.get("customer_address", ""),
                customer_zipcode=order_data.get("customer_zipcode", ""),
                total_amount=float(order_data.get("total_amount", 0)),
                order_date=order_date,
                order_status=order_data.get("order_status", "pending"),
                items=items
            )

            return order

        except Exception as e:
            print(f"[ERROR] 주문 데이터 파싱 실패: {e}")
            # 기본 주문 반환 (에러 방지)
            return PlayautoOrder(
                playauto_order_id=order_data.get("playauto_order_id", "ERROR"),
                market=order_data.get("market", "unknown"),
                order_number=order_data.get("order_number", "ERROR"),
                customer_name="ERROR",
                customer_address="ERROR",
                total_amount=0,
                items=[]
            )

    async def update_order_status(
        self,
        bundle_codes: Optional[List[str]] = None,
        unliqs: Optional[List[str]] = None,
        status: str = "신규주문"
    ) -> Dict:
        """
        주문 상태 변경

        Args:
            bundle_codes: 묶음 번호 리스트
            unliqs: 주문 고유번호 리스트
            status: 변경할 상태 (신규주문, 배송중, 배송완료, 고취소 등)

        Returns:
            상태 변경 결과
        """
        data = {"status": status}
        if bundle_codes:
            data["bundle_codes"] = bundle_codes
        if unliqs:
            data["unlqs"] = unliqs

        if not self.client:
            async with PlayautoClient() as client:
                response = await client.patch("/orders/status", data=data)
        else:
            response = await self.client.patch("/orders/status", data=data)

        return response

    async def update_order(self, unliq: str, update_data: Dict) -> Dict:
        """
        주문 정보 수정

        Args:
            unliq: 주문 고유번호
            update_data: 수정할 데이터 (수령인, 주소, 전화번호 등)

        Returns:
            수정 결과
        """
        data = {"unliq": unliq, **update_data}

        if not self.client:
            async with PlayautoClient() as client:
                response = await client.patch("/order/edit", data=data)
        else:
            response = await self.client.patch("/order/edit", data=data)

        return response

    async def delete_orders(self, unliq_list: List[str]) -> Dict:
        """
        주문 삭제

        Args:
            unliq_list: 삭제할 주문 고유번호 리스트

        Returns:
            삭제 결과
        """
        data = {"unliqList": unliq_list}

        if not self.client:
            async with PlayautoClient() as client:
                response = await client.delete("/order/delete", data=data)
        else:
            response = await self.client.delete("/order/delete", data=data)

        return response

    async def hold_orders(
        self,
        bundle_codes: List[str],
        hold_reason: str,
        status: str = "주문보류"
    ) -> Dict:
        """
        주문 보류 처리

        Args:
            bundle_codes: 보류 처리할 묶음 번호 리스트
            hold_reason: 보류 사유
            status: 처리할 상태 (출고대기, 주문보류 등)

        Returns:
            보류 처리 결과
        """
        data = {
            "bundle_codes": bundle_codes,
            "holdReason": hold_reason,
            "status": status
        }

        if not self.client:
            async with PlayautoClient() as client:
                response = await client.put("/order/hold", data=data)
        else:
            response = await self.client.put("/order/hold", data=data)

        return response


async def fetch_and_sync_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market: Optional[str] = None
) -> Dict:
    """
    주문 수집 및 로컬 DB 동기화

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        market: 마켓 필터

    Returns:
        동기화 결과
    """
    from database.db import get_db

    try:
        # 주문 수집
        orders_api = PlayautoOrdersAPI()
        result = await orders_api.fetch_orders(
            start_date=start_date,
            end_date=end_date,
            market=market
        )

        if not result.get("success"):
            return {
                "success": False,
                "message": "주문 수집 실패",
                "synced_count": 0
            }

        # 로컬 DB에 동기화
        db = get_db()
        synced_count = 0
        fail_count = 0

        for order_data in result.get("orders", []):
            try:
                # 중복 확인
                playauto_order_id = order_data.get("playauto_order_id")
                existing = db.get_playauto_setting(f"synced_order_{playauto_order_id}")

                if not existing:
                    # 로컬 DB에 저장
                    db.sync_playauto_order_to_local(order_data)
                    # 동기화 완료 표시
                    db.save_playauto_setting(f"synced_order_{playauto_order_id}", "true")
                    synced_count += 1

                    # 개별 주문 알림 발송
                    try:
                        from notifications.notifier import send_notification

                        # 주문 상품 정보 준비
                        items = []
                        for item in order_data.get("items", []):
                            items.append({
                                "product_name": item.get("product_name", "알 수 없음"),
                                "quantity": item.get("quantity", 1),
                                "price": item.get("price", 0)
                            })

                        send_notification(
                            notification_type="new_order",
                            message=f"플레이오토에서 새로운 주문이 수집되었습니다: {order_data.get('order_number')}",
                            order_number=order_data.get("order_number", ""),
                            market=order_data.get("market", ""),
                            customer_name=order_data.get("customer_name", ""),
                            total_amount=order_data.get("total_amount", 0),
                            items=items
                        )
                    except Exception as e:
                        print(f"[WARN] 개별 주문 알림 발송 실패 ({playauto_order_id}): {e}")

            except Exception as e:
                print(f"[ERROR] 주문 동기화 실패 ({playauto_order_id}): {e}")
                fail_count += 1

        return {
            "success": True,
            "message": f"{synced_count}개 주문 동기화 완료",
            "total_orders": result.get("total", 0),
            "synced_count": synced_count
        }

    except Exception as e:
        print(f"[ERROR] 주문 수집 및 동기화 실패: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}",
            "synced_count": 0
        }
