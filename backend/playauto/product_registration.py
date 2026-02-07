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

    우선순위:
    1. detailImageUrl이 있으면 JPG 이미지만 사용 (모든 CSS 보존)
    2. 없으면 기존 방식 (이미지 나열)

    Args:
        detail_page_data: JSON 형태의 상세페이지 데이터
        product_name: 상품명 (fallback용)

    Returns:
        HTML 문자열
    """
    if not detail_page_data:
        return f"<div style='padding: 20px;'><h1>{product_name}</h1><p>상품 상세 정보</p></div>"

    try:
        import json
        data = json.loads(detail_page_data)

        # 1. JPG 이미지가 있으면 그것만 사용 (최고 품질)
        detail_image_url = data.get("detailImageUrl")
        if detail_image_url:
            logger.info(f"[플레이오토] 상세페이지 JPG 이미지 사용: {detail_image_url[:80]}...")
            return f"""<div style='max-width: 1000px; margin: 0 auto; text-align: center;'>
<img src='{detail_image_url}' style='width: 100%; height: auto; display: block;' alt='{product_name} 상세페이지' />
</div>"""

        # 데이터 추출
        content = data.get("content", {})
        images = data.get("images", {})
        template = data.get("template", "")

        # HTML 생성
        html_parts = [f"<div style='max-width: 1000px; margin: 0 auto; padding: 20px;'>"]

        # 상품명
        html_parts.append(f"<h1 style='font-size: 32px; font-weight: bold; margin-bottom: 30px; color: #333; text-align: center;'>{content.get('productName', product_name)}</h1>")

        # 메인 이미지 (템플릿별)
        main_image_keys = ['template1_bg', 'template2_main', 'food_template1_bg', 'food_template2_main']
        for key in main_image_keys:
            if key in images and images[key]:
                url = images[key]

                # 로컬 경로를 Supabase URL로 변환
                if isinstance(url, str) and url.startswith("/supabase-images/"):
                    # /supabase-images/1_흰밥/image.jpg -> cat-1/image.jpg
                    import re
                    import urllib.parse

                    # 카테고리 ID 추출 (1_흰밥 -> 1)
                    match = re.match(r'/supabase-images/(\d+)_[^/]+/(.+)', url)
                    if match:
                        cat_id = match.group(1)
                        filename = match.group(2)
                        # URL 디코딩 (한글 파일명 처리)
                        filename = urllib.parse.unquote(filename)
                        # Supabase Storage URL 생성
                        url = f"https://spkeunlwkrqkdwunkufy.supabase.co/storage/v1/object/public/product-images/cat-{cat_id}/{urllib.parse.quote(filename)}"
                        logger.info(f"[플레이오토] 로컬 경로 → Supabase URL 변환: cat-{cat_id}/{filename[:50]}")
                    else:
                        logger.warning(f"[플레이오토] 로컬 경로 패턴 불일치, 제외: {url}")
                        continue

                # 다른 로컬 경로(/static, /uploads 등)는 제외
                elif isinstance(url, str) and url.startswith("/"):
                    logger.warning(f"[플레이오토] 접근 불가 로컬 경로 제외: {url}")
                    continue

                # 외부 URL 처리
                if isinstance(url, str) and (url.startswith("http") or url.startswith("//")):
                    if url.startswith("//"):
                        url = f"https:{url}"
                    html_parts.append(f"<div style='text-align: center; margin: 30px 0;'><img src='{url}' style='max-width: 100%; height: auto;' /></div>")

        # 텍스트 컨텐츠
        if "coreMessage1" in content:
            html_parts.append(f"<h2 style='font-size: 26px; font-weight: bold; margin: 40px 0 20px; color: #444; text-align: center;'>{content['coreMessage1']}</h2>")

        if "subtitle" in content:
            html_parts.append(f"<p style='font-size: 18px; color: #666; margin: 20px 0; line-height: 1.8; text-align: center;'>{content['subtitle']}</p>")

        # 태그
        if "tag1" in content:
            tags = [content.get(f'tag{i}', '') for i in range(1, 4) if content.get(f'tag{i}')]
            if tags:
                tag_html = ' '.join([f"<span style='display: inline-block; background: #f0f0f0; padding: 10px 20px; margin: 5px; border-radius: 25px; font-size: 16px;'>{tag}</span>" for tag in tags])
                html_parts.append(f"<div style='margin: 30px 0; text-align: center;'>{tag_html}</div>")

        # 나머지 이미지들 (서브 이미지, 상세 이미지 등)
        sub_images = []
        for key, url in images.items():
            if key not in main_image_keys and isinstance(url, str):
                # 로컬 경로를 Supabase URL로 변환
                if url.startswith("/supabase-images/"):
                    import re
                    import urllib.parse

                    match = re.match(r'/supabase-images/(\d+)_[^/]+/(.+)', url)
                    if match:
                        cat_id = match.group(1)
                        filename = match.group(2)
                        filename = urllib.parse.unquote(filename)
                        url = f"https://spkeunlwkrqkdwunkufy.supabase.co/storage/v1/object/public/product-images/cat-{cat_id}/{urllib.parse.quote(filename)}"
                    else:
                        continue
                # 다른 로컬 경로 제외
                elif url.startswith("/"):
                    continue

                # 외부 URL 추가
                if url.startswith("http") or url.startswith("//"):
                    if url.startswith("//"):
                        url = f"https:{url}"
                    sub_images.append(url)

        # 서브 이미지 출력
        for url in sub_images:
            html_parts.append(f"<div style='text-align: center; margin: 20px 0;'><img src='{url}' style='max-width: 100%; height: auto;' /></div>")

        # 상품 안내
        html_parts.append("<div style='margin-top: 50px; padding: 30px; background: #f9f9f9; border-radius: 10px; border-left: 4px solid #4CAF50;'>")
        html_parts.append("<h3 style='font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #333;'>상품 안내</h3>")
        html_parts.append("<ul style='font-size: 16px; color: #555; line-height: 2; padding-left: 20px;'>")
        html_parts.append("<li>신선하고 품질 좋은 상품을 제공합니다</li>")
        html_parts.append("<li>빠른 배송으로 신속하게 받아보실 수 있습니다</li>")
        html_parts.append("<li>궁금하신 사항은 언제든지 문의해주세요</li>")
        html_parts.append("</ul>")
        html_parts.append("</div>")

        html_parts.append("</div>")

        return "\n".join(html_parts)

    except json.JSONDecodeError:
        # JSON이 아니면 그대로 반환 (이미 HTML일 수도 있음)
        if detail_page_data.strip().startswith("<"):
            return detail_page_data
        else:
            return f"<div style='padding: 20px;'><h1>{product_name}</h1><p>{detail_page_data}</p></div>"
    except Exception as e:
        logger.error(f"[플레이오토] detail_page_data 변환 실패: {e}")
        return f"<div style='padding: 20px;'><h1>{product_name}</h1><p>상품 상세 정보</p></div>"


def extract_images_from_detail_page(detail_page_data: str) -> List[str]:
    """
    detail_page_data JSON에서 이미지 URL 목록 추출

    Args:
        detail_page_data: JSON 형태의 상세페이지 데이터

    Returns:
        이미지 URL 리스트 (최대 10개)
    """
    if not detail_page_data:
        return []

    try:
        import json
        data = json.loads(detail_page_data)
        images = data.get("images", {})

        # 우선순위 이미지 먼저
        priority_keys = ['template1_bg', 'template2_main', 'food_template1_bg', 'food_template2_main']
        image_urls = []

        # 우선순위 이미지
        for key in priority_keys:
            if len(image_urls) >= 10:
                break
            if key in images:
                url = images[key]

                # 로컬 경로를 Supabase URL로 변환
                if isinstance(url, str) and url.startswith("/supabase-images/"):
                    import re
                    import urllib.parse

                    match = re.match(r'/supabase-images/(\d+)_[^/]+/(.+)', url)
                    if match:
                        cat_id = match.group(1)
                        filename = match.group(2)
                        filename = urllib.parse.unquote(filename)
                        url = f"https://spkeunlwkrqkdwunkufy.supabase.co/storage/v1/object/public/product-images/cat-{cat_id}/{urllib.parse.quote(filename)}"
                    else:
                        continue
                # 다른 로컬 경로 제외
                elif isinstance(url, str) and url.startswith("/"):
                    continue

                # 외부 URL 추가
                if isinstance(url, str) and (url.startswith("http") or url.startswith("//")):
                    if url.startswith("//"):
                        url = f"https:{url}"
                    image_urls.append(url)

        # 나머지 이미지
        for key, url in images.items():
            if len(image_urls) >= 10:
                break
            if key not in priority_keys and isinstance(url, str):
                # 로컬 경로를 Supabase URL로 변환
                if url.startswith("/supabase-images/"):
                    import re
                    import urllib.parse

                    match = re.match(r'/supabase-images/(\d+)_[^/]+/(.+)', url)
                    if match:
                        cat_id = match.group(1)
                        filename = match.group(2)
                        filename = urllib.parse.unquote(filename)
                        url = f"https://spkeunlwkrqkdwunkufy.supabase.co/storage/v1/object/public/product-images/cat-{cat_id}/{urllib.parse.quote(filename)}"
                    else:
                        continue
                # 다른 로컬 경로 제외
                elif url.startswith("/"):
                    continue

                # 외부 URL 추가
                if url.startswith("http") or url.startswith("//"):
                    if url.startswith("//"):
                        url = f"https:{url}"
                    image_urls.append(url)

        return image_urls

    except Exception as e:
        logger.error(f"[플레이오토] 이미지 추출 실패: {e}")
        return []


def build_product_data_from_db(product: Dict, site_list: List[Dict], channel_type: str = "smartstore") -> Dict:
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
        channel_type: 채널 타입 ("gmk_auction", "coupang", "smartstore")
            - "gmk_auction": 옥션/지마켓 (std_ol_yn="Y", opt_type="옵션없음", 단일상품)
            - "coupang": 쿠팡 (std_ol_yn="N", opt_type="조립형", 일반상품)
            - "smartstore": 스마트스토어 등 (std_ol_yn="N", opt_type="독립형", 일반상품)

    Returns:
        플레이오토 API 형식 데이터
    """
    # 썸네일 URL 처리
    # 1. thumbnail_url (Supabase Storage) 우선 사용 - 안정적인 외부 접근
    # 2. 없으면 original_thumbnail_url 사용 (외부 URL, CDN 차단 가능성)
    # 3. 로컬 경로는 사용 불가 (플레이오토가 접근 불가)
    thumbnail_url = product.get("thumbnail_url") or product.get("original_thumbnail_url") or ""

    # // 로 시작하는 URL은 https: 추가
    if thumbnail_url.startswith("//"):
        thumbnail_url = f"https:{thumbnail_url}"

    # 로컬 경로인 경우 무시 (플레이오토가 접근할 수 없음)
    if thumbnail_url and thumbnail_url.startswith("/"):
        logger.error(f"[플레이오토] 썸네일이 로컬 경로라서 사용할 수 없습니다: {thumbnail_url}")
        logger.error(f"[플레이오토] 상세페이지 생성기에서 이미지를 Supabase Storage에 업로드하도록 수정이 필요합니다")
        thumbnail_url = ""  # 빈 값으로 설정하여 오류 방지

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

    # 이미지 필드 준비 (sale_img1만 사용 - 썸네일)
    # sale_img2~11은 전송하지 않음 (상세페이지는 JPG로 detail_desc에 포함됨)
    image_fields = {"sale_img1": thumbnail_url}

    # 채널 타입에 따른 옵션 설정
    product_name = product.get("product_name", "기본")
    option_value = product_name.replace(",", " ").replace("  ", " ").strip()

    if channel_type == "gmk_auction":
        # 지마켓/옥션: 단일상품 필수, 옵션없음
        std_ol_yn = "Y"
        opt_type = "옵션없음"
        opts = []
        logger.info(f"[플레이오토] 지마켓/옥션 설정: std_ol_yn=Y, opt_type=옵션없음")
    elif channel_type == "coupang":
        # 쿠팡: 조립형 옵션 필수
        std_ol_yn = "N"
        opt_type = "조립형"
        opts = [
            {
                "opt_sort1": "상품선택",
                "opt_sort1_desc": option_value,
                "stock_cnt": 999,
                "status": "정상"
            }
        ]
        logger.info(f"[플레이오토] 쿠팡 설정: std_ol_yn=N, opt_type=조립형, 옵션값='{option_value}'")
    else:
        # 스마트스토어 등: 독립형 옵션
        std_ol_yn = "N"
        opt_type = "독립형"
        opts = [
            {
                "opt_sort1": "상품선택",
                "opt_sort1_desc": option_value,
                "stock_cnt": 999,
                "status": "정상"
            }
        ]
        logger.info(f"[플레이오토] 스마트스토어 설정: std_ol_yn=N, opt_type=독립형, 옵션값='{option_value}'")

    return {
        # 기본 정보
        "c_sale_cd": product.get("c_sale_cd") or "__AUTO__",
        "sol_cate_no": sol_cate_no,
        "shop_sale_name": product.get("product_name"),
        "adult_yn": False,
        "sale_price": int(product.get("selling_price", 0)),
        "sale_cnt_limit": 999,
        "site_list": site_list,
        "std_ol_yn": std_ol_yn,

        # 옵션 정보 (채널 타입에 따라 다르게 설정)
        "opt_type": opt_type,
        "opts": opts,

        # 상세 및 기타 정보
        "tax_type": "과세",
        "madein": {
            "madein_no": 1,  # 국내
            "madein_etc": "경기도",  # 상세 원산지
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

        # 이미지 (sale_img1만 사용)
        # sale_img1: 썸네일 (상품 추출 시 저장된 이미지)
        # 상세 이미지는 JPG로 변환되어 detail_desc에 포함됨
        **image_fields,

        # 상품정보제공고시
        # infoCode: 전자상거래법에 따른 상품정보제공고시 분류코드
        # 카테고리별로 동적으로 조회된 infoCode 사용
        # is_desc_referred: true로 설정하여 상세페이지 참조 (간소화)
        #
        # 스마트스토어는 일부 필드를 명시적으로 요구함 (예: 유전자변형식품 표시)
        "prod_info": [
            {
                "infoCode": info_code,  # 카테고리별 동적 infoCode
                "infoDetail": {
                    # 스마트스토어 필수 필드들
                    "유전자변형식품의 경우의 표시": "N",  # 유전자변형식품 아님
                    "유전자변형식품에 해당하는 경우의 표시": "N",  # 동일 필드명 다른 버전
                },
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
