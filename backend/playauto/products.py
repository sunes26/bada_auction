"""
플레이오토 온라인 상품 관리 API

온라인 상품 정보 조회, 수정, 가격 업데이트 등
"""

from typing import Dict, List, Optional
from .client import PlayautoClient
from logger import get_logger

logger = get_logger(__name__)


class PlayautoProductAPI:
    """플레이오토 온라인 상품 API"""

    def __init__(self):
        self.client = PlayautoClient()

    async def update_online_product_price(
        self,
        ol_shop_no: str,
        sale_price: int,
        consumer_price: Optional[int] = None
    ) -> Dict:
        """
        온라인 상품 판매가 업데이트

        Args:
            ol_shop_no: 온라인 상품 고유번호
            sale_price: 새 판매가
            consumer_price: 새 소비자가 (정가), 선택사항

        Returns:
            API 응답 결과
        """
        try:
            # 온라인 상품 수정 API 엔드포인트
            endpoint = "/product/online/edit"

            # 요청 데이터
            data = {
                "ol_shop_no": ol_shop_no,
                "sale_price": sale_price
            }

            # 소비자가도 함께 업데이트
            if consumer_price is not None:
                data["consumer_price"] = consumer_price

            logger.info(f"[플레이오토] 상품 가격 업데이트: ol_shop_no={ol_shop_no}, sale_price={sale_price:,}원")

            # API 호출
            async with self.client as client:
                result = await client.patch(endpoint, data=data)

            logger.info(f"[플레이오토] 가격 업데이트 성공: {result}")
            return result

        except Exception as e:
            logger.error(f"[플레이오토] 가격 업데이트 실패: {str(e)}")
            raise

    async def bulk_update_prices(
        self,
        updates: List[Dict[str, any]]
    ) -> Dict:
        """
        여러 상품의 가격을 일괄 업데이트

        Args:
            updates: 업데이트 목록
                [
                    {
                        "ol_shop_no": "상품번호",
                        "sale_price": 판매가,
                        "consumer_price": 소비자가 (선택)
                    },
                    ...
                ]

        Returns:
            API 응답 결과
        """
        try:
            endpoint = "/product/online/edit"

            logger.info(f"[플레이오토] 일괄 가격 업데이트 시작: {len(updates)}건")

            # 일괄 업데이트
            async with self.client as client:
                result = await client.patch(endpoint, data={"products": updates})

            logger.info(f"[플레이오토] 일괄 가격 업데이트 성공")
            return result

        except Exception as e:
            logger.error(f"[플레이오토] 일괄 가격 업데이트 실패: {str(e)}")
            raise

    async def get_online_product_info(
        self,
        ol_shop_no: str
    ) -> Dict:
        """
        온라인 상품 정보 조회

        Args:
            ol_shop_no: 온라인 상품 고유번호

        Returns:
            상품 정보
        """
        try:
            endpoint = "/product/online/info"
            params = {"ol_shop_no": ol_shop_no}

            async with self.client as client:
                result = await client.get(endpoint, params=params)

            return result

        except Exception as e:
            logger.error(f"[플레이오토] 상품 조회 실패: {str(e)}")
            raise

    async def search_products_by_c_sale_cd(
        self,
        c_sale_cd_list: List[str],
        sdate: str = "2020-01-01",
        edate: str = "2030-12-31"
    ) -> Dict:
        """
        판매자관리코드(c_sale_cd)로 상품 검색하여 ol_shop_no 조회

        POST /api/product/online/list/v1.2

        Args:
            c_sale_cd_list: 검색할 판매자관리코드 리스트
            sdate: 검색 시작일 (YYYY-MM-DD)
            edate: 검색 종료일 (YYYY-MM-DD)

        Returns:
            {
                "results": {
                    "c_sale_cd1": [
                        {"ol_shop_no": 12345, "shop_cd": "Z000", ...},
                        {"ol_shop_no": 12346, "shop_cd": "A001", ...}
                    ],
                    ...
                },
                "ol_count": 1,
                "normal_count": 1
            }
        """
        try:
            endpoint = "/product/online/list/v1.2"

            data = {
                "start": 0,
                "length": 300,
                "sdate": sdate,
                "edate": edate,
                "date_type": "wdate",
                "multi_type": "c_sale_cd",
                "multi_search_word": c_sale_cd_list,
                "view_master": True
            }

            logger.info(f"[플레이오토] c_sale_cd로 상품 검색: {len(c_sale_cd_list)}개")

            async with self.client as client:
                result = await client.post(endpoint, data=data)

            logger.info(f"[플레이오토] 검색 결과: ol_count={result.get('ol_count', 0)}")

            return result

        except Exception as e:
            logger.error(f"[플레이오토] 상품 검색 실패: {str(e)}")
            raise

    async def get_product_detail(
        self,
        ol_shop_no: str
    ) -> Dict:
        """
        온라인 상품 상세 정보 조회 (마켓별 shop_sale_no 포함)

        GET /api/products/:ol_shop_no/v1.2

        Args:
            ol_shop_no: 온라인 상품 고유번호

        Returns:
            {
                "c_sale_cd": "판매자관리코드",
                "ol_shop_no": "온라인상품번호",
                "shops": [
                    {
                        "shop_cd": "A001",  # 마켓 코드
                        "shop_sale_no": "B123456789",  # 쇼핑몰상품번호
                        "shop_name": "옥션",
                        "status": "판매중"
                    },
                    ...
                ]
            }
        """
        try:
            endpoint = f"/products/{ol_shop_no}/v1.2"

            logger.info(f"[플레이오토] 상품 상세 조회: ol_shop_no={ol_shop_no}")

            async with self.client as client:
                result = await client.get(endpoint)

            # 응답 구조 확인
            if "data" in result:
                data = result["data"]
            else:
                data = result

            logger.info(f"[플레이오토] 상품 상세 조회 성공: c_sale_cd={data.get('c_sale_cd')}")

            return data

        except Exception as e:
            logger.error(f"[플레이오토] 상품 상세 조회 실패: {str(e)}")
            raise


def calculate_selling_price_with_margin(
    sourcing_price: float,
    margin_rate: float = 50.0
) -> int:
    """
    마진율을 적용한 판매가 계산

    Args:
        sourcing_price: 소싱가
        margin_rate: 마진율 (%, 기본값 50%)

    Returns:
        계산된 판매가 (정수)

    Example:
        소싱가 10,000원, 마진율 50% → 판매가 15,000원
        계산식: 10,000 + (10,000 * 0.5) = 15,000
    """
    if sourcing_price <= 0:
        raise ValueError("소싱가는 0보다 커야 합니다")

    if margin_rate < 0:
        raise ValueError("마진율은 0 이상이어야 합니다")

    # 마진 금액 계산
    margin_amount = sourcing_price * (margin_rate / 100)

    # 판매가 = 소싱가 + 마진
    selling_price = sourcing_price + margin_amount

    # 100원 단위 반올림 (선택사항)
    selling_price = round(selling_price / 100) * 100

    return int(selling_price)


def calculate_required_margin_rate(
    sourcing_price: float,
    selling_price: float
) -> float:
    """
    현재 가격으로 마진율 계산

    Args:
        sourcing_price: 소싱가
        selling_price: 판매가

    Returns:
        마진율 (%)

    Example:
        소싱가 10,000원, 판매가 15,000원 → 마진율 50%
    """
    if sourcing_price <= 0:
        return 0.0

    margin = selling_price - sourcing_price
    margin_rate = (margin / sourcing_price) * 100

    return round(margin_rate, 2)


async def edit_playauto_product(
    c_sale_cd: str,
    shop_cd: str,
    shop_id: str,
    shop_sale_name: Optional[str] = None,
    sale_price: Optional[int] = None,
    sol_cate_no: Optional[int] = None,
    edit_slave_all: bool = True,
    detail_desc: Optional[str] = None,
    sale_img1: Optional[str] = None,
    opts: Optional[List[Dict]] = None,
    **kwargs
) -> Dict:
    """
    PlayAuto 온라인 상품 수정

    Args:
        c_sale_cd: 판매자관리코드 (필수)
        shop_cd: 쇼핑몰 코드 (필수) - 마스터 수정은 'master'
        shop_id: 쇼핑몰 아이디 (필수) - 마스터 수정은 'master'
        shop_sale_name: 상품명
        sale_price: 판매가 (10원 단위)
        sol_cate_no: 카테고리 코드
        edit_slave_all: 하위 쇼핑몰 상품 연동 수정 여부
        detail_desc: 상품 상세설명
        sale_img1: 기본 이미지 URL
        opts: 옵션 정보 리스트
        **kwargs: 기타 선택적 파라미터

    Returns:
        API 응답 결과

    Example:
        await edit_playauto_product(
            c_sale_cd="m20230101",
            shop_cd="master",
            shop_id="master",
            sale_price=15000,
            shop_sale_name="수정된 상품명"
        )
    """
    try:
        client = PlayautoClient()

        # 요청 데이터 구성
        data = {
            "c_sale_cd": c_sale_cd,
            "shop_cd": shop_cd,
            "shop_id": shop_id,
            "edit_slave_all": edit_slave_all
        }

        # 선택적 파라미터 추가
        if shop_sale_name:
            data["shop_sale_name"] = shop_sale_name
        if sale_price is not None:
            data["sale_price"] = sale_price
        if sol_cate_no is not None:
            data["sol_cate_no"] = sol_cate_no
        if detail_desc:
            data["detail_desc"] = detail_desc
        if sale_img1:
            data["sale_img1"] = sale_img1
        if opts:
            data["opts"] = opts

        # 추가 파라미터
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value

        logger.info(f"[플레이오토] 상품 수정 시작: c_sale_cd={c_sale_cd}, shop_cd={shop_cd}")
        logger.info(f"[플레이오토] 요청 데이터: {data}")

        # API 호출 - PUT 메서드 사용
        # base_url이 이미 /api로 끝나므로 /api 제외
        endpoint = "/products/edit/v1.2"
        async with client as c:
            result = await c.put(endpoint, data=data)

        # 전체 응답 로깅
        logger.info(f"[플레이오토] API 응답 전체: {result}")

        # PDF에 따르면 응답은 result (String, "성공"/"실패") 또는 status (Boolean)
        is_success = (
            result.get("result") == "성공" or
            result.get("status") == True or
            result.get("status") == "true"
        )

        if is_success:
            logger.info(f"[플레이오토] 상품 수정 성공: {c_sale_cd}")
            logger.info(f"[플레이오토] 반환된 c_sale_cd: {result.get('c_sale_cd')}")
            return {
                "success": True,
                "message": "상품 수정 완료",
                "data": result
            }
        else:
            # 오류 메시지 추출 (messages 배열 또는 message 필드)
            error_msg = result.get("message")
            if not error_msg and result.get("messages"):
                # messages 배열이 있는 경우 첫 번째 메시지 사용
                messages = result.get("messages", [])
                error_msg = messages[0] if messages else "알 수 없는 오류"
            elif not error_msg:
                error_msg = "알 수 없는 오류"

            logger.error(f"[플레이오토] 상품 수정 실패: {error_msg}")
            logger.error(f"[플레이오토] 실패 응답 전체: {result}")
            return {
                "success": False,
                "message": error_msg,
                "data": result
            }

    except Exception as e:
        logger.error(f"[플레이오토] 상품 수정 실패: {str(e)}")
        return {
            "success": False,
            "message": f"상품 수정 중 오류 발생: {str(e)}"
        }
