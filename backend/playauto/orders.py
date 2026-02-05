"""
플레이오토 주문 수집 API

여러 마켓에서 주문을 자동으로 수집하는 기능
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .client import PlayautoClient
from .models import PlayautoOrder, OrderItem, OrdererInfo, ReceiverInfo, DeliveryInfo, PaymentInfo
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
        order_status: Optional[List[str]] = None,
        market: Optional[str] = None,
        start: int = 0,
        length: int = 500,
        bundle_yn: bool = False,
        search_key: Optional[str] = None,
        search_word: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        **kwargs
    ) -> Dict:
        """
        주문 목록 수집 (공식 API - POST /orders)

        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            order_status: 주문 상태 필터 (리스트)
            market: 마켓 필터 (쇼핑몰 코드)
            start: 시작 인덱스 (offset)
            length: 조회 개수
            bundle_yn: 묶음 주문 그룹화
            search_key: 검색 필드
            search_word: 검색어
            page: 페이지 번호 (레거시, start 계산용)
            limit: 페이지당 항목 수 (레거시, length로 변환)
            **kwargs: 추가 파라미터

        Returns:
            주문 목록 응답
        """
        # 날짜 기본값 설정 (최근 7일)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 레거시 파라미터 호환성 처리
        if page > 1 and start == 0:
            start = (page - 1) * limit
        if limit != 100 and length == 500:
            length = limit

        # Request Body 구성 (POST)
        body = {
            "start": start,
            "length": length,
            "orderby": "wdate desc",
            "date_type": "wdate",
            "sdate": start_date,
            "edate": end_date,
            "status": order_status or ["ALL"],
            "bundle_yn": bundle_yn
        }

        # 선택적 필터 추가
        if market:
            body["shop_cd"] = market
        if search_key and search_word:
            body["search_key"] = search_key
            body["search_word"] = search_word
            body["search_type"] = kwargs.get("search_type", "partial")

        # POST 요청으로 변경
        if not self.client:
            async with PlayautoClient() as client:
                response = await client.post("/orders", data=body)
        else:
            response = await self.client.post("/orders", data=body)

        # 응답 데이터 파싱
        return self._parse_orders_response(response)

    async def get_order_detail(self, playauto_order_id: str) -> PlayautoOrder:
        """
        주문 상세 조회 (공식 API - GET /order/:unliq)

        Args:
            playauto_order_id: 플레이오토 주문 ID (uniq)

        Returns:
            주문 상세 정보
        """
        # Path Parameter 사용으로 변경
        if not self.client:
            async with PlayautoClient() as client:
                response = await client.get(f"/order/{playauto_order_id}")
        else:
            response = await self.client.get(f"/order/{playauto_order_id}")

        # 응답 데이터 파싱
        order_data = response.get("data", {})
        if not order_data:
            order_data = response.get("order", {})
        return self._parse_order(order_data)

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

    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """
        날짜 문자열 파싱

        Args:
            datetime_str: 날짜 문자열 (YYYY-MM-DD HH:MM:SS 또는 ISO format)

        Returns:
            datetime 객체 또는 None
        """
        if not datetime_str:
            return None
        try:
            # YYYY-MM-DD HH:MM:SS 형식
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                # ISO format
                return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            except Exception:
                return None

    def _parse_order(self, order_data: Dict) -> PlayautoOrder:
        """
        개별 주문 데이터 파싱 (80+ 필드)

        Args:
            order_data: 주문 원본 데이터

        Returns:
            PlayautoOrder 인스턴스
        """
        try:
            # 1. 주문 상품 목록 파싱
            items_data = order_data.get("items", [])
            items = []
            for item_data in items_data:
                item = OrderItem(
                    product_name=item_data.get("product_name") or item_data.get("shop_sale_name", "Unknown"),
                    product_url=item_data.get("product_url", ""),
                    quantity=item_data.get("quantity") or item_data.get("sale_cnt", 1),
                    price=float(item_data.get("price") or item_data.get("pay_amt", 0)),
                    option=item_data.get("option") or item_data.get("shop_opt_name", "")
                )
                items.append(item)

            # 2. 날짜 필드 파싱
            ord_time = self._parse_datetime(order_data.get("ord_time"))
            pay_time = self._parse_datetime(order_data.get("pay_time"))
            ord_confirm_time = self._parse_datetime(order_data.get("ord_confirm_time"))
            invoice_send_time = self._parse_datetime(order_data.get("invoice_send_time"))

            # 레거시 order_date 필드 처리
            order_date = ord_time or self._parse_datetime(order_data.get("order_date"))

            # 3. 주문자 정보
            orderer = OrdererInfo(
                order_name=order_data.get("order_name"),
                order_id=order_data.get("order_id"),
                order_tel=order_data.get("order_tel"),
                order_htel=order_data.get("order_htel"),
                order_email=order_data.get("order_email")
            )

            # 4. 수령인 정보
            receiver = ReceiverInfo(
                to_name=order_data.get("to_name"),
                to_tel=order_data.get("to_tel"),
                to_htel=order_data.get("to_htel"),
                to_zipcd=order_data.get("to_zipcd"),
                to_addr1=order_data.get("to_addr1"),
                to_addr2=order_data.get("to_addr2")
            )

            # 5. 배송 정보
            delivery = DeliveryInfo(
                ship_cost=order_data.get("ship_cost"),
                ship_method=order_data.get("ship_method"),
                ship_msg=order_data.get("ship_msg"),
                carr_name=order_data.get("carr_name"),
                carr_no=order_data.get("carr_no"),
                invoice_no=order_data.get("invoice_no"),
                invoice_send_time=invoice_send_time
            )

            # 6. 결제 정보
            payment = PaymentInfo(
                pay_amt=order_data.get("pay_amt"),
                discount_amt=order_data.get("discount_amt"),
                sales=order_data.get("sales"),
                pay_method=order_data.get("pay_method"),
                pay_time=pay_time
            )

            # 7. PlayautoOrder 생성 (80+ 필드)
            # 하위 호환성을 위한 필드 매핑
            playauto_order_id = order_data.get("uniq") or order_data.get("playauto_order_id", "")
            market = order_data.get("shop_name") or order_data.get("market", "unknown")
            order_number = order_data.get("shop_ord_no") or order_data.get("order_number", "")
            customer_name = order_data.get("to_name") or order_data.get("customer_name", "")
            customer_phone = order_data.get("to_htel") or order_data.get("customer_phone")
            customer_address = f"{order_data.get('to_addr1', '')} {order_data.get('to_addr2', '')}".strip() or order_data.get("customer_address", "")
            customer_zipcode = order_data.get("to_zipcd") or order_data.get("customer_zipcode")
            total_amount = float(order_data.get("pay_amt") or order_data.get("total_amount", 0))
            order_status = order_data.get("ord_status") or order_data.get("order_status", "pending")

            order = PlayautoOrder(
                # 기존 필드 (하위 호환성)
                playauto_order_id=playauto_order_id,
                market=market,
                order_number=order_number,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_address=customer_address,
                customer_zipcode=customer_zipcode,
                total_amount=total_amount,
                order_date=order_date,
                order_status=order_status,
                items=items,

                # 신규 필드
                uniq=order_data.get("uniq"),
                bundle_no=order_data.get("bundle_no"),
                sol_no=order_data.get("sol_no"),
                shop_cd=order_data.get("shop_cd"),
                shop_name=order_data.get("shop_name"),
                shop_id=order_data.get("shop_id"),
                shop_ord_no=order_data.get("shop_ord_no"),
                ord_status=order_data.get("ord_status"),
                ord_time=ord_time,
                ord_confirm_time=ord_confirm_time,

                # 중첩 객체
                orderer=orderer,
                receiver=receiver,
                delivery=delivery,
                payment=payment,

                # 상품 정보
                shop_sale_no=order_data.get("shop_sale_no"),
                shop_sale_name=order_data.get("shop_sale_name"),
                shop_opt_name=order_data.get("shop_opt_name"),
                sale_cnt=order_data.get("sale_cnt"),
                c_sale_cd=order_data.get("c_sale_cd"),

                # 매칭 정보
                map_yn=order_data.get("map_yn"),
                sku_cd=order_data.get("sku_cd"),
                prod_name=order_data.get("prod_name")
            )

            return order

        except Exception as e:
            print(f"[ERROR] 주문 파싱 실패: {e}")
            import traceback
            traceback.print_exc()

            # 기본 주문 반환 (에러 방지)
            fallback_id = order_data.get("uniq") or order_data.get("playauto_order_id", "ERROR")
            fallback_market = order_data.get("shop_name") or order_data.get("market", "unknown")
            fallback_number = order_data.get("shop_ord_no") or order_data.get("order_number", "ERROR")

            return PlayautoOrder(
                playauto_order_id=fallback_id,
                market=fallback_market,
                order_number=fallback_number,
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
    from database.db_wrapper import get_db

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
