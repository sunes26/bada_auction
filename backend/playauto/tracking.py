"""
플레이오토 송장 등록 API

여러 마켓에 송장번호를 일괄 등록하는 기능
"""

from typing import Dict, List, Optional
from .client import PlayautoClient
from .models import TrackingItem
from .exceptions import PlayautoAPIError


class PlayautoTrackingAPI:
    """플레이오토 송장 등록 API"""

    def __init__(self, client: Optional[PlayautoClient] = None):
        """
        Args:
            client: PlayautoClient 인스턴스 (제공되지 않으면 새로 생성)
        """
        self.client = client

    async def upload_tracking(self, tracking_data: List[Dict], overwrite: bool = False, change_complete: bool = False) -> Dict:
        """
        송장번호 일괄 등록

        Args:
            tracking_data: 송장 정보 목록
                [{
                    "bundle_no": "묶음번호",
                    "carr_no": 택배사번호(숫자),
                    "invoice_no": "송장번호"
                }]
            overwrite: 송장번호 덮어쓰기 여부 (기본값: False)
            change_complete: 배송완료 상태로 즉시 변경 여부 (기본값: False)

        Returns:
            업로드 결과
        """
        # 플레이오토 API 문서에 따른 요청 데이터 구성
        request_data = {
            "orders": tracking_data,
            "overwrite": overwrite,
            "change_complete": change_complete
        }

        # 클라이언트가 없으면 새로 생성
        if not self.client:
            async with PlayautoClient() as client:
                response = await client.put("/order/setnotice", data=request_data)
        else:
            response = await self.client.put("/order/setnotice", data=request_data)

        # 응답 처리
        return self._parse_upload_response(response, len(tracking_data))

    async def upload_single_tracking(
        self,
        bundle_no: str,
        invoice_no: str,
        carr_no: int,
        overwrite: bool = False,
        change_complete: bool = False
    ) -> Dict:
        """
        단일 송장 등록

        Args:
            bundle_no: 묶음번호
            invoice_no: 송장번호
            carr_no: 택배사번호 (숫자, 예: CJ대한통운=1)
            overwrite: 송장번호 덮어쓰기 여부
            change_complete: 배송완료 상태로 즉시 변경 여부

        Returns:
            업로드 결과
        """
        # 단일 항목을 리스트로 변환
        tracking_data = [{
            "bundle_no": bundle_no,
            "carr_no": carr_no,
            "invoice_no": invoice_no
        }]

        return await self.upload_tracking(tracking_data, overwrite, change_complete)

    def _parse_upload_response(self, response: Dict, total_count: int) -> Dict:
        """
        송장 업로드 응답 파싱

        Args:
            response: API 응답 데이터
            total_count: 총 업로드 시도 수

        Returns:
            파싱된 업로드 결과
        """
        try:
            # API 응답 구조에 맞게 파싱 (플레이오토 API 문서 참조)
            data = response.get("data", {})
            success_count = data.get("success_count", 0)
            fail_count = data.get("fail_count", 0)
            failed_items = data.get("failed_items", [])

            return {
                "success": True,
                "total_count": total_count,
                "success_count": success_count,
                "fail_count": fail_count,
                "failed_items": failed_items
            }

        except Exception as e:
            print(f"[ERROR] 송장 업로드 응답 파싱 실패: {e}")
            return {
                "success": False,
                "total_count": total_count,
                "success_count": 0,
                "fail_count": total_count,
                "failed_items": []
            }

    def _get_courier_name(self, courier_code: str) -> str:
        """
        택배사 코드에서 택배사명 조회

        Args:
            courier_code: 택배사 코드

        Returns:
            택배사명
        """
        courier_mapping = {
            "CJ": "CJ대한통운",
            "HANJIN": "한진택배",
            "LOTTE": "롯데택배",
            "LOGEN": "로젠택배",
            "KDEXP": "경동택배",
            "CVSNET": "CVSnet 편의점택배",
            "EPOST": "우체국택배",
            "GSPOSTBOX": "GS편의점택배",
            "CHUNIL": "천일택배",
            "HDEXP": "합동택배",
            "HONAM": "호남택배",
            "DAESIN": "대신택배",
            "ILYANG": "일양로지스",
            "KGLOGIS": "KG로지스",
            "KUNYOUNG": "건영택배",
            "SLX": "SLX택배",
            "HOMEPICK": "홈픽택배",
            "HANJINJINJU": "한진택배(진주)",
        }

        return courier_mapping.get(courier_code.upper(), courier_code)

    @staticmethod
    def get_carrier_code_number(carrier_name_or_code: str) -> int:
        """
        택배사명/코드를 플레이오토 carr_no(숫자)로 변환

        플레이오토 API는 숫자 택배사 코드를 사용합니다.
        실제 매핑은 GET /api/carriers API로 조회해야 하지만,
        자주 사용되는 택배사의 기본값을 제공합니다.

        Args:
            carrier_name_or_code: 택배사명 또는 코드 (예: "CJ", "CJ대한통운", "1")

        Returns:
            플레이오토 택배사 번호 (carr_no)
        """
        # 이미 숫자인 경우
        if isinstance(carrier_name_or_code, int):
            return carrier_name_or_code

        if carrier_name_or_code.isdigit():
            return int(carrier_name_or_code)

        # 택배사명/코드 → carr_no 매핑 (추정값, 실제로는 API로 확인 필요)
        carrier_mapping = {
            "CJ": 1,
            "CJ대한통운": 1,
            "한진택배": 2,
            "HANJIN": 2,
            "롯데택배": 3,
            "LOTTE": 3,
            "로젠택배": 4,
            "LOGEN": 4,
            "우체국택배": 5,
            "EPOST": 5,
            "경동택배": 6,
            "KDEXP": 6,
        }

        return carrier_mapping.get(carrier_name_or_code.upper(), 1)  # 기본값: CJ대한통운


async def auto_upload_tracking_from_local(days: int = 7) -> Dict:
    """
    로컬 DB에서 완료된 주문의 송장번호를 자동으로 업로드

    Args:
        days: 최근 N일 이내 완료 주문만 대상

    Returns:
        업로드 결과
    """
    from database.db_wrapper import get_db

    try:
        db = get_db()

        # 송장번호가 있는 완료 주문 조회
        orders = db.get_completed_orders_with_tracking(days=days)

        if not orders:
            return {
                "success": True,
                "message": "업로드할 송장번호가 없습니다",
                "total_count": 0,
                "success_count": 0,
                "fail_count": 0
            }

        # 송장 데이터 구성
        tracking_data = []
        for order in orders:
            # bundle_no가 있는 경우만 업로드
            bundle_no = order.get("bundle_no") or order.get("playauto_order_id")
            if bundle_no:
                # carr_no 추출 (DB에 저장되어 있어야 함, 없으면 기본값 1 = CJ대한통운)
                carr_no = order.get("carr_no") or 1

                tracking_data.append({
                    "bundle_no": bundle_no,
                    "carr_no": carr_no,
                    "invoice_no": order["tracking_number"]
                })

        if not tracking_data:
            return {
                "success": True,
                "message": "플레이오토 묶음번호가 없는 주문만 있습니다",
                "total_count": 0,
                "success_count": 0,
                "fail_count": 0
            }

        # 송장 업로드
        tracking_api = PlayautoTrackingAPI()
        result = await tracking_api.upload_tracking(tracking_data)

        # 업로드 성공한 주문 표시
        if result.get("success"):
            for i, order in enumerate(orders):
                if i < result.get("success_count", 0):
                    db.mark_tracking_uploaded(order["id"])

        return result

    except Exception as e:
        print(f"[ERROR] 자동 송장 업로드 실패: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}",
            "total_count": 0,
            "success_count": 0,
            "fail_count": 0
        }
