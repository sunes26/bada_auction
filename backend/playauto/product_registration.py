"""
플레이오토 상품 등록 API

판매 상품을 플레이오토를 통해 여러 마켓에 자동 등록
"""

from typing import Dict, List, Optional
from .client import PlayautoClient
from logger import get_logger

logger = get_logger(__name__)


def get_infocode_for_category(category: str) -> str:
    """
    카테고리에 맞는 infoCode를 조회

    Args:
        category: 상품 카테고리 (예: "간편식 > 밥류 > 즉석밥 > 흰밥")

    Returns:
        infoCode (예: "ProcessedFood2023")
    """
    if not category:
        logger.warning("[플레이오토] 카테고리가 없습니다. 기본값(Etc2023) 사용")
        return "Etc2023"

    # category에서 level1 추출 (첫 번째 부분)
    # 예: "간편식 > 밥류 > 즉석밥 > 흰밥" -> "간편식"
    level1 = category.split(">")[0].strip() if ">" in category else category.strip()

    try:
        # DB에서 infoCode 조회 (PostgreSQL/SQLite 자동 선택)
        from database.database_manager import get_database_manager

        db_manager = get_database_manager()
        conn = db_manager.engine.raw_connection()
        cursor = conn.cursor()

        placeholder = "?" if db_manager.is_sqlite else "%s"
        cursor.execute(
            f"SELECT info_code FROM category_infocode_mapping WHERE level1 = {placeholder}",
            (level1,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            info_code = result[0]
            logger.info(f"[플레이오토] 카테고리 '{level1}' → infoCode '{info_code}'")
            return info_code
        else:
            logger.warning(f"[플레이오토] '{level1}' 카테고리에 대한 매핑을 찾을 수 없습니다. 기본값(Etc2023) 사용")
            return "Etc2023"

    except Exception as e:
        logger.error(f"[플레이오토] infoCode 조회 실패: {str(e)}")
        return "Etc2023"


class PlayautoProductRegistration:
    """플레이오토 상품 등록"""

    def __init__(self):
        self.client = None

    async def register_product(
        self,
        product_data: Dict
    ) -> Dict:
        """
        단일 상품 등록

        Args:
            product_data: 상품 정보
                {
                    "c_sale_cd": "판매자관리코드",
                    "sol_cate_no": 카테고리번호,
                    "shop_sale_name": "상품명",
                    "sale_price": 15000,
                    "sale_cnt_limit": 100,
                    "site_list": [...],
                    "opt_type": "옵션없음",
                    "opts": [],
                    "tax_type": "과세",
                    "madein": {...},
                    "detail_desc": "상세설명",
                    "sale_img1": "이미지URL",
                    "prod_info": [...],
                    "ship_price_type": "무료"
                }

        Returns:
            등록 결과
        """
        try:
            endpoint = "/products/add/v1.2"

            logger.info(f"[플레이오토] 상품 등록 시작: {product_data.get('shop_sale_name')}")
            logger.info(f"[플레이오토] 요청 데이터 - sol_cate_no: {product_data.get('sol_cate_no')}, c_sale_cd: {product_data.get('c_sale_cd')}")
            logger.info(f"[플레이오토] 요청 데이터 - site_list: {product_data.get('site_list')}")

            # API 호출
            if not self.client:
                async with PlayautoClient() as client:
                    result = await client.post(endpoint, data=product_data)
            else:
                result = await self.client.post(endpoint, data=product_data)

            logger.info(f"[플레이오토] 상품 등록 응답: {result}")

            # 플레이오토 API 응답의 result 필드 확인
            # '성공' 또는 '실패'로 반환됨
            api_result = result.get("result", "")

            if api_result == "성공":
                return {
                    "success": True,
                    "data": result,
                    "c_sale_cd": result.get("c_sale_cd"),
                    "site_list": result.get("site_list", [])
                }
            else:
                # 실패 처리
                error_msg = ", ".join(result.get("messages", ["알 수 없는 오류"]))
                logger.error(f"[플레이오토] 상품 등록 실패: {error_msg}")
                return {
                    "success": False,
                    "error": f"플레이오토 API 오류: {error_msg}",
                    "error_code": result.get("error_code"),
                    "data": result
                }

        except Exception as e:
            logger.error(f"[플레이오토] 상품 등록 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def register_multiple_products(
        self,
        products: List[Dict]
    ) -> Dict:
        """
        여러 상품 일괄 등록

        Args:
            products: 상품 정보 리스트

        Returns:
            일괄 등록 결과
        """
        try:
            logger.info(f"[플레이오토] 일괄 등록 시작: {len(products)}개 상품")

            results = []
            success_count = 0
            fail_count = 0

            for product in products:
                result = await self.register_product(product)
                results.append(result)

                if result.get("success"):
                    success_count += 1
                else:
                    fail_count += 1

            logger.info(f"[플레이오토] 일괄 등록 완료: 성공 {success_count}개, 실패 {fail_count}개")

            return {
                "success": True,
                "total": len(products),
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results
            }

        except Exception as e:
            logger.error(f"[플레이오토] 일괄 등록 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


def convert_detail_page_json_to_html(detail_page_data: str, product_name: str) -> str:
    """
    detail_page_data JSON을 HTML로 변환

    Args:
        detail_page_data: JSON 형태의 상세페이지 데이터
        product_name: 상품명 (fallback용)

    Returns:
        HTML 문자열
    """
    if not detail_page_data:
        return f"<div><h1>{product_name}</h1><p>상품 상세 정보</p></div>"

    try:
        import json
        data = json.loads(detail_page_data)

        # images 추출
        images = data.get("images", {})
        content = data.get("content", {})

        # HTML 생성
        html_parts = [f"<div style='max-width: 800px; margin: 0 auto;'>"]
        html_parts.append(f"<h1>{content.get('productName', product_name)}</h1>")

        # 이미지들 추가
        for key, value in images.items():
            if isinstance(value, str) and value.startswith("http"):
                html_parts.append(f"<img src='{value}' style='width: 100%; margin: 10px 0;' />")

        # 텍스트 컨텐츠 추가
        if "coreMessage1" in content:
            html_parts.append(f"<p>{content['coreMessage1']}</p>")
        if "subtitle" in content:
            html_parts.append(f"<p>{content['subtitle']}</p>")

        html_parts.append("</div>")

        return "\n".join(html_parts)

    except json.JSONDecodeError:
        # JSON이 아니면 그대로 반환 (이미 HTML일 수도 있음)
        if detail_page_data.strip().startswith("<"):
            return detail_page_data
        else:
            return f"<div><h1>{product_name}</h1><p>{detail_page_data}</p></div>"
    except Exception as e:
        logger.error(f"[플레이오토] detail_page_data 변환 실패: {e}")
        return f"<div><h1>{product_name}</h1><p>상품 상세 정보</p></div>"


def build_product_data_from_db(product: Dict, site_list: List[Dict]) -> Dict:
    """
    DB 상품 정보를 플레이오토 API 형식으로 변환

    Args:
        product: DB 상품 정보
        site_list: 등록할 쇼핑몰 목록
            [
                {
                    "shop_cd": "스마트스토어 코드",
                    "shop_id": "쇼핑몰 아이디",
                    "template_no": 템플릿번호
                }
            ]

    Returns:
        플레이오토 API 형식 데이터
    """
    # 썸네일 URL 처리
    # 1. thumbnail_url (Supabase Storage) 우선 사용 - 안정적인 외부 접근
    # 2. 없으면 original_thumbnail_url 사용 (외부 URL, CDN 차단 가능성)
    # 3. 로컬 경로면 절대 URL로 변환 (localhost - 플레이오토가 접근 불가)
    thumbnail_url = product.get("thumbnail_url") or product.get("original_thumbnail_url") or ""

    # // 로 시작하는 URL은 https: 추가
    if thumbnail_url.startswith("//"):
        thumbnail_url = f"https:{thumbnail_url}"

    # 로컬 경로인 경우 (플레이오토가 접근할 수 없음 - 경고 로그)
    if thumbnail_url and thumbnail_url.startswith("/static"):
        import os
        logger.warning(f"[플레이오토] 썸네일이 로컬 경로입니다. 플레이오토가 접근할 수 없습니다: {thumbnail_url}")
        # 서버 URL로 변환 시도 (하지만 localhost면 여전히 접근 불가)
        server_url = os.getenv("SERVER_URL", "http://localhost:8000")
        thumbnail_url = f"{server_url}{thumbnail_url}"

    # 카테고리에 맞는 infoCode 조회
    category = product.get("category", "")
    info_code = get_infocode_for_category(category)

    # sol_cate_no 처리
    # 1. 상품에 sol_cate_no가 지정되어 있으면 사용
    # 2. 없으면 None (플레이오토 계정에 카테고리 설정 필요)
    sol_cate_no = product.get("sol_cate_no")

    if not sol_cate_no:
        logger.warning(
            f"[플레이오토] 상품 '{product.get('product_name')}'에 sol_cate_no가 없습니다. "
            "플레이오토 웹에서 카테고리를 먼저 설정하고 sol_cate_no를 지정해주세요. "
            "자세한 내용은 PLAYAUTO_CATEGORY_ISSUE.md 참고"
        )
        # 임시로 None 반환 - API 호출 시 오류 발생 예상
        sol_cate_no = None

    return {
        # 기본 정보
        "c_sale_cd": product.get("c_sale_cd") or "__AUTO__",
        "sol_cate_no": sol_cate_no,
        "shop_sale_name": product.get("product_name"),
        "adult_yn": False,
        "sale_price": int(product.get("selling_price", 0)),
        "sale_cnt_limit": 999,
        "site_list": site_list,
        "std_ol_yn": "Y",  # 단일상품 (지마켓/옥션 등록 필수 - PlayAuto 지원팀 안내)

        # 옵션 정보
        "opt_type": "옵션없음",  # 현재는 옵션 없음으로 처리 (추후 확장 가능)
        "opts": [],

        # 상세 및 기타 정보
        "tax_type": "과세",
        "madein": {
            "madein_no": 1,  # 국내 (기본값, 실제로는 상품별로 설정 필요)
            "multi_yn": False
        },
        # detail_page_data를 HTML로 변환 (JSON 형태일 경우 자동 변환)
        "detail_desc": convert_detail_page_json_to_html(
            product.get("detail_page_data", ""),
            product.get("product_name", "상품")
        ),
        "brand": "",
        "model": "",
        "maker": "",
        "keywords": [],

        # 이미지
        "sale_img1": thumbnail_url,

        # 상품정보제공고시
        # infoCode: 전자상거래법에 따른 상품정보제공고시 분류코드
        # 카테고리별로 동적으로 조회된 infoCode 사용
        # is_desc_referred: true로 설정하여 상세페이지 참조 (간소화)
        "prod_info": [
            {
                "infoCode": info_code,  # 카테고리별 동적 infoCode
                "infoDetail": {},  # 빈 객체
                "is_desc_referred": True  # 상세페이지 참조
            }
        ],

        # 배송 정보 (선결제 3000원)
        "ship_price_type": "선결제",
        "ship_price": 3000,

        # 가격 정보
        "supply_price": int(product.get("sourcing_price", 0)),
        "cost_price": int(product.get("sourcing_price", 0)),
        "street_price": int(product.get("selling_price", 0))
    }
