"""
내 판매 상품 관리 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database.db_wrapper import get_db
from utils.cache import async_cached, clear_all_cache
from utils.category_mapper import get_playauto_category_code
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])


# Request 모델
class CreateProductRequest(BaseModel):
    """판매 상품 생성 요청"""
    product_name: str
    selling_price: float
    monitored_product_id: Optional[int] = None
    sourcing_url: Optional[str] = None
    sourcing_product_name: Optional[str] = None
    sourcing_price: Optional[float] = None
    sourcing_source: Optional[str] = None
    detail_page_data: Optional[str] = None
    category: Optional[str] = None
    thumbnail_url: Optional[str] = None
    original_thumbnail_url: Optional[str] = None  # 원본 외부 URL
    notes: Optional[str] = None


class UpdateProductRequest(BaseModel):
    """판매 상품 수정 요청"""
    product_name: Optional[str] = None
    selling_price: Optional[float] = None
    monitored_product_id: Optional[int] = None
    sourcing_url: Optional[str] = None
    sourcing_product_name: Optional[str] = None
    sourcing_price: Optional[float] = None
    sourcing_source: Optional[str] = None
    detail_page_data: Optional[str] = None
    category: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


# API 엔드포인트

@router.post("/create")
async def create_product(request: CreateProductRequest):
    """판매 상품 생성"""
    try:
        db = get_db()

        # 카테고리 자동 매핑
        sol_cate_no = None
        category_warning = None
        if request.category:
            sol_cate_no = get_playauto_category_code(request.category)
            if sol_cate_no:
                logger.info(f"[상품생성] 카테고리 자동 매핑: {request.category} -> {sol_cate_no}")
            else:
                category_warning = "PlayAuto 카테고리 매핑이 없습니다. 관리자 페이지에서 매핑을 추가해주세요."
                logger.warning(f"[상품생성] 카테고리 매핑 없음: {request.category}")

        product_id = db.add_selling_product(
            product_name=request.product_name,
            selling_price=request.selling_price,
            monitored_product_id=request.monitored_product_id,
            sourcing_url=request.sourcing_url,
            sourcing_product_name=request.sourcing_product_name,
            sourcing_price=request.sourcing_price,
            sourcing_source=request.sourcing_source,
            detail_page_data=request.detail_page_data,
            category=request.category,
            thumbnail_url=request.thumbnail_url,
            original_thumbnail_url=request.original_thumbnail_url,
            sol_cate_no=sol_cate_no,
            notes=request.notes
        )

        # 캐시 무효화
        clear_all_cache()

        response = {
            "success": True,
            "product_id": product_id,
            "message": "판매 상품이 추가되었습니다.",
            "sol_cate_no": sol_cate_no
        }

        if category_warning:
            response["warning"] = category_warning

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 생성 실패: {str(e)}")


@router.get("/list")
@async_cached(ttl=30)  # 30초 캐싱
async def get_products(is_active: Optional[bool] = None, limit: int = 100):
    """판매 상품 목록 조회"""
    try:
        db = get_db()
        products = db.get_selling_products(is_active=is_active, limit=limit)

        return {
            "success": True,
            "data": products,
            "total": len(products)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 조회 실패: {str(e)}")


@router.get("/margin/logs")
async def get_margin_logs(product_id: Optional[int] = None, limit: int = 50):
    """마진 변동 이력 조회"""
    try:
        db = get_db()
        logs = db.get_margin_change_logs(selling_product_id=product_id, limit=limit)

        return {
            "success": True,
            "logs": logs,
            "total": len(logs)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"마진 이력 조회 실패: {str(e)}")


@router.get("/stats")
@async_cached(ttl=60)  # 1분 캐싱
async def get_product_stats():
    """판매 상품 통계"""
    try:
        db = get_db()

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 총 상품 수
            cursor.execute("SELECT COUNT(*) FROM my_selling_products WHERE is_active = TRUE")
            total_products = cursor.fetchone()[0]

            # 평균 마진
            cursor.execute("""
                SELECT AVG(sp.selling_price - COALESCE(mp.current_price, 0)) as avg_margin
                FROM my_selling_products sp
                LEFT JOIN monitored_products mp ON sp.monitored_product_id = mp.id
                WHERE sp.is_active = TRUE AND mp.current_price IS NOT NULL
            """)
            avg_margin = cursor.fetchone()[0] or 0

            # 평균 마진율
            cursor.execute("""
                SELECT AVG(
                    CASE
                        WHEN mp.current_price > 0 THEN
                            ((sp.selling_price - mp.current_price) / mp.current_price * 100)
                        ELSE 0
                    END
                ) as avg_margin_rate
                FROM my_selling_products sp
                LEFT JOIN monitored_products mp ON sp.monitored_product_id = mp.id
                WHERE sp.is_active = TRUE AND mp.current_price IS NOT NULL
            """)
            avg_margin_rate = cursor.fetchone()[0] or 0

            # 최근 7일 마진 변동 건수
            cursor.execute("""
                SELECT COUNT(*) FROM margin_change_logs
                WHERE created_at >= datetime('now', '-7 days')
            """)
            recent_margin_changes = cursor.fetchone()[0]

        return {
            "success": True,
            "stats": {
                "total_products": total_products,
                "avg_margin": round(avg_margin, 2),
                "avg_margin_rate": round(avg_margin_rate, 2),
                "recent_margin_changes": recent_margin_changes
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/detail-page/{product_id}")
async def get_detail_page(product_id: int):
    """상세페이지 조회"""
    try:
        db = get_db()
        product = db.get_selling_product(product_id)

        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        return {
            "success": True,
            "has_detail_page": bool(product.get('detail_page_data')),
            "detail_page_data": product.get('detail_page_data')
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상세페이지 조회 실패: {str(e)}")


class GenerateDetailPageRequest(BaseModel):
    """상세페이지 생성 요청"""
    force_regenerate: Optional[bool] = False


@router.post("/detail-page/{product_id}/generate")
async def generate_detail_page(product_id: int, request: GenerateDetailPageRequest):
    """상세페이지 자동 생성"""
    try:
        import os
        import json

        db = get_db()
        product = db.get_selling_product(product_id)

        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # 이미 상세페이지가 있고, force_regenerate가 False이면 기존 데이터 반환
        if product.get('detail_page_data') and not request.force_regenerate:
            return {
                "success": True,
                "message": "이미 상세페이지가 존재합니다.",
                "detail_page_data": product['detail_page_data']
            }

        # OpenAI API 키 확인
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            logger.info("OpenAI API 키 확인 완료")
            logger.debug(f"API 키 접두사: {openai_api_key[:10]}...")
        else:
            logger.error("OpenAI API 키가 설정되지 않았습니다")

        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API 키가 설정되지 않았습니다. 환경 변수를 확인해주세요.")

        # AI를 사용하여 상세페이지 HTML 생성
        product_name = product['product_name']
        category = product.get('category', '')
        sourcing_product_name = product.get('sourcing_product_name', '')

        prompt = f"""당신은 전문 쇼핑몰 상세페이지 HTML 제작자입니다.

상품명: {product_name}
카테고리: {category}
소싱 상품명: {sourcing_product_name}

위 상품에 대한 전문적인 상세페이지 HTML을 생성해주세요.

요구사항:
1. 반응형 디자인 (모바일 친화적)
2. 깔끔하고 현대적인 스타일
3. 상품의 주요 특징 3-5가지
4. 상품 사용법 또는 보관법
5. 주의사항
6. 스타일은 inline CSS 또는 <style> 태그 사용
7. 이미지는 placeholder로 처리 (실제 이미지 URL은 나중에 교체)

완성된 HTML만 출력하세요. 설명이나 코멘트는 제외하고 순수 HTML만 출력하세요."""

        try:
            import openai
            print(f"[INFO] OpenAI 라이브러리 버전: {openai.__version__}")

            client = openai.OpenAI(api_key=openai_api_key)
            print(f"[INFO] OpenAI API 호출 시작...")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional e-commerce product detail page HTML generator. Generate clean, modern, responsive HTML code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )

            print(f"[INFO] OpenAI API 호출 완료")
            html_content = response.choices[0].message.content.strip()

            # HTML 태그로 시작하지 않으면 코드 블록 제거
            if html_content.startswith('```'):
                html_content = html_content.split('```')[1]
                if html_content.startswith('html'):
                    html_content = html_content[4:]
                html_content = html_content.strip()

            # DB에 저장
            db.update_selling_product(
                product_id=product_id,
                detail_page_data=html_content
            )

            print(f"[INFO] 상세페이지 DB 저장 완료")

            # 캐시 무효화
            clear_all_cache()

            return {
                "success": True,
                "message": "상세페이지가 생성되었습니다.",
                "detail_page_data": html_content
            }

        except Exception as e:
            print(f"[ERROR] AI 상세페이지 생성 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"AI 상세페이지 생성 실패: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 상세페이지 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"상세페이지 생성 실패: {str(e)}")


@router.get("/{product_id}")
async def get_product(product_id: int):
    """판매 상품 상세 조회"""
    try:
        db = get_db()
        product = db.get_selling_product(product_id)

        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # 가격 이력 조회
        price_history = []
        if product.get('monitored_product_id'):
            price_history = db.get_price_history(product['monitored_product_id'], limit=30)

        # 마진 변동 이력 조회
        margin_logs = db.get_margin_change_logs(selling_product_id=product_id, limit=10)

        return {
            "success": True,
            "data": product,
            "price_history": price_history,
            "margin_logs": margin_logs
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 조회 실패: {str(e)}")


@router.put("/{product_id}")
async def update_product(product_id: int, request: UpdateProductRequest):
    """판매 상품 수정"""
    try:
        db = get_db()

        # 상품 존재 확인
        product = db.get_selling_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # 판매가 변경 확인 (플레이오토 API 호출용)
        old_selling_price = product.get('selling_price')
        new_selling_price = request.selling_price
        price_changed = new_selling_price is not None and old_selling_price != new_selling_price
        playauto_product_no = product.get('playauto_product_no')

        # 카테고리 변경 시 자동 매핑
        sol_cate_no = None
        if request.category:
            sol_cate_no = get_playauto_category_code(request.category)
            if sol_cate_no:
                logger.info(f"[상품수정] 카테고리 자동 매핑: {request.category} -> {sol_cate_no}")
            else:
                logger.warning(f"[상품수정] 카테고리 매핑 없음: {request.category}")

        # 로컬 DB 수정
        db.update_selling_product(
            product_id=product_id,
            product_name=request.product_name,
            selling_price=request.selling_price,
            monitored_product_id=request.monitored_product_id,
            sourcing_url=request.sourcing_url,
            sourcing_product_name=request.sourcing_product_name,
            sourcing_price=request.sourcing_price,
            sourcing_source=request.sourcing_source,
            detail_page_data=request.detail_page_data,
            category=request.category,
            thumbnail_url=request.thumbnail_url,
            is_active=request.is_active,
            sol_cate_no=sol_cate_no,
            notes=request.notes
        )

        # 플레이오토 API 업데이트 (판매가 변경 + 플레이오토 상품인 경우)
        playauto_updated = False
        if price_changed and playauto_product_no:
            try:
                from playauto.products import PlayautoProductAPI
                playauto_api = PlayautoProductAPI()

                logger.info(f"[상품수정] 플레이오토 가격 업데이트 시작: ol_shop_no={playauto_product_no}, {old_selling_price:,}원 → {new_selling_price:,}원")

                await playauto_api.update_online_product_price(
                    ol_shop_no=playauto_product_no,
                    sale_price=int(new_selling_price)
                )

                playauto_updated = True
                logger.info(f"[상품수정] 플레이오토 가격 업데이트 성공")

            except Exception as e:
                logger.error(f"[상품수정] 플레이오토 가격 업데이트 실패: {str(e)}")
                # 플레이오토 업데이트 실패해도 로컬 DB는 업데이트되었으므로 계속 진행

        # 캐시 무효화
        clear_all_cache()

        return {
            "success": True,
            "message": "상품이 수정되었습니다.",
            "playauto_updated": playauto_updated,
            "price_changed": price_changed
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 수정 실패: {str(e)}")


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """판매 상품 삭제"""
    try:
        db = get_db()

        # 상품 존재 확인
        product = db.get_selling_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # 썸네일 삭제 (있는 경우)
        if product.get('thumbnail_url'):
            try:
                from utils.image_downloader import delete_thumbnail
                delete_thumbnail(product['thumbnail_url'])
            except Exception as e:
                print(f"[WARN] 썸네일 삭제 실패: {e}")

        db.delete_selling_product(product_id)

        # 캐시 무효화
        clear_all_cache()

        return {
            "success": True,
            "message": "상품이 삭제되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 삭제 실패: {str(e)}")


@router.post("/{product_id}/update-sourcing-price")
async def update_product_sourcing_price(product_id: int):
    """
    수동으로 상품의 소싱가 업데이트

    소싱처 URL에서 현재 가격을 다시 체크하여 업데이트합니다.
    """
    try:
        db = get_db()

        # 상품 조회
        product = db.get_selling_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        sourcing_url = product.get('sourcing_url')
        if not sourcing_url:
            raise HTTPException(status_code=400, detail="소싱 URL이 없는 상품입니다.")

        # 상품 모니터링으로 가격 체크
        from monitor.product_monitor import ProductMonitor

        monitor = ProductMonitor()

        logger.info(f"[소싱가 업데이트] 상품 ID: {product_id}")
        logger.info(f"[소싱가 업데이트] 소싱처: {product.get('sourcing_source')}")
        logger.info(f"[소싱가 업데이트] 소싱 URL: {sourcing_url}")

        try:
            result = monitor.check_product_status(
                product_url=sourcing_url,
                source=product.get('sourcing_source') or 'unknown'
            )
        except Exception as e:
            logger.error(f"가격 체크 실패: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"소싱처에서 가격을 가져올 수 없습니다.\n\n원인: {str(e)}\n\n소싱 URL이 올바른지 확인해주세요."
            )

        logger.info(f"[소싱가 업데이트] 체크 결과: {result}")

        new_price = result.get('price')
        logger.info(f"[소싱가 업데이트] 추출된 가격: {new_price}")

        if not new_price or new_price <= 0:
            error_detail = result.get('details', '알 수 없음')
            status = result.get('status', 'error')

            logger.error(f"[소싱가 업데이트] 가격 추출 실패 - 상태: {status}, 상세: {error_detail}")

            raise HTTPException(
                status_code=400,
                detail=f"소싱처에서 가격을 가져올 수 없습니다.\n\n상태: {status}\n상세: {error_detail}\n\n페이지 구조가 변경되었거나 접근이 차단되었을 수 있습니다."
            )

        old_price = product.get('sourcing_price', 0)
        selling_price = product.get('selling_price', 0)

        logger.info(f"[소싱가 업데이트] DB 저장 가격: {old_price}원")
        logger.info(f"[소싱가 업데이트] 새로 추출한 가격: {new_price}원")
        logger.info(f"[소싱가 업데이트] 가격 차이: {new_price - old_price}원")

        # 가격이 변경되었으면 업데이트
        if old_price != new_price:
            # DB 업데이트
            db.update_selling_product(
                product_id=product_id,
                sourcing_price=new_price
            )

            # 마진 변동 로그
            old_margin = selling_price - old_price
            new_margin = selling_price - new_price
            old_margin_rate = ((selling_price - old_price) / old_price * 100) if old_price > 0 else 0
            new_margin_rate = ((selling_price - new_price) / new_price * 100) if new_price > 0 else 0

            db.log_margin_change(
                selling_product_id=product_id,
                old_margin=old_margin,
                new_margin=new_margin,
                old_margin_rate=old_margin_rate,
                new_margin_rate=new_margin_rate,
                change_reason='manual_sourcing_price_update',
                old_selling_price=selling_price,
                new_selling_price=selling_price,
                old_sourcing_price=old_price,
                new_sourcing_price=new_price
            )

            # 캐시 무효화
            clear_all_cache()

            return {
                "success": True,
                "message": f"소싱가가 업데이트되었습니다 ({old_price:,}원 → {new_price:,}원)",
                "old_price": old_price or 0,
                "new_price": new_price or 0,
                "price_diff": (new_price or 0) - (old_price or 0),
                "new_margin": new_margin,
                "new_margin_rate": round(new_margin_rate, 2)
            }
        else:
            return {
                "success": True,
                "message": "가격 변동이 없습니다.",
                "current_price": new_price or 0,
                "old_price": old_price or 0,
                "new_price": new_price or 0,
                "price_diff": 0
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"소싱가 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"소싱가 업데이트 실패: {str(e)}")


@router.post("/register-to-playauto")
async def register_products_to_playauto(request: dict):
    """
    선택한 상품들을 플레이오토를 통해 여러 마켓에 등록

    Args:
        request: {
            "product_ids": [1, 2, 3],
            "site_list": [
                {
                    "shop_cd": "쇼핑몰코드",
                    "shop_id": "쇼핑몰 아이디",
                    "template_no": 템플릿번호
                }
            ]
        }

    Returns:
        등록 결과
    """
    try:
        product_ids = request.get("product_ids", [])
        site_list = request.get("site_list", [])

        if not product_ids:
            raise HTTPException(status_code=400, detail="상품 ID가 필요합니다.")

        db = get_db()

        # site_list가 없으면 기본 템플릿 사용
        if not site_list:
            import json
            default_templates_json = db.get_playauto_setting("default_templates")

            if not default_templates_json:
                raise HTTPException(status_code=400, detail="등록할 쇼핑몰 정보가 없습니다. 설정에서 기본 템플릿을 등록해주세요.")

            default_templates = json.loads(default_templates_json)

            # 템플릿 정보를 site_list 형식으로 변환
            # ESM 채널은 제외 (ESM은 단일상품만 등록 가능하며 카테고리 제약이 있음)
            site_list = [
                {
                    "shop_cd": t.get("shop_cd"),
                    "shop_id": t.get("shop_id"),
                    "template_no": t.get("template_no")
                }
                for t in default_templates
                if t.get("shop_cd") not in ["ESM", "esm"]  # ESM 채널 제외
            ]

            logger.info(f"[상품등록] 기본 템플릿 사용: {len(site_list)}개 쇼핑몰 (ESM 제외)")

        # 플레이오토 API 클라이언트
        from playauto.product_registration import PlayautoProductRegistration, build_product_data_from_db
        registration_api = PlayautoProductRegistration()

        logger.info(f"[상품등록] 플레이오토 등록 시작: {len(product_ids)}개 상품")

        success_count = 0
        fail_count = 0
        results = []

        for product_id in product_ids:
            try:
                # 상품 조회
                product = db.get_selling_product(product_id)
                if not product:
                    logger.warning(f"[상품등록] 상품을 찾을 수 없음: ID {product_id}")
                    results.append({
                        "product_id": product_id,
                        "success": False,
                        "error": "상품을 찾을 수 없습니다."
                    })
                    fail_count += 1
                    continue

                # 플레이오토 API 형식으로 변환
                product_data = build_product_data_from_db(product, site_list)

                # 디버깅: 실제 전달 데이터 로그
                logger.info(f"[상품등록] product_id={product_id}, category='{product.get('category')}', sol_cate_no={product.get('sol_cate_no')}")
                logger.info(f"[상품등록] product_data sol_cate_no={product_data.get('sol_cate_no')}")

                # 플레이오토 등록
                result = await registration_api.register_product(product_data)

                # ESM 에러 시 재시도 (ESM 채널 제외)
                if not result.get("success") and result.get("error"):
                    error_msg = result.get("error", "")
                    if "ESM" in error_msg and "단일상품" in error_msg:
                        logger.warning(f"[상품등록] ESM 에러 감지 - ESM 제외하고 재시도: {product.get('product_name')}")

                        # site_list에서 ESM 제외
                        filtered_site_list = [
                            site for site in product_data.get("site_list", [])
                            if site.get("shop_cd") not in ["ESM", "esm", "Esm"]
                        ]

                        if filtered_site_list:
                            product_data["site_list"] = filtered_site_list
                            logger.info(f"[상품등록] ESM 제외 후 {len(filtered_site_list)}개 채널로 재시도")
                            result = await registration_api.register_product(product_data)
                        else:
                            logger.error(f"[상품등록] ESM만 있어서 재시도 불가")

                if result.get("success"):
                    # 플레이오토 상품 번호 및 쇼핑몰 번호 저장
                    c_sale_cd = result.get("c_sale_cd")
                    site_list_result = result.get("site_list", [])

                    # ol_shop_no는 첫 번째 등록 성공한 쇼핑몰 번호를 저장
                    ol_shop_no = None
                    if site_list_result:
                        for site in site_list_result:
                            if site.get("result") == "성공" and site.get("ol_shop_no"):
                                ol_shop_no = site.get("ol_shop_no")
                                break

                    # 등록 성공 시 is_active = True로 변경하고 PlayAuto ID 저장
                    update_params = {"product_id": product_id, "is_active": True}
                    if c_sale_cd:
                        update_params["playauto_product_no"] = c_sale_cd
                        logger.info(f"[상품등록] PlayAuto 상품번호 저장: {c_sale_cd}")
                    if ol_shop_no:
                        update_params["ol_shop_no"] = ol_shop_no
                        logger.info(f"[상품등록] 온라인 쇼핑몰 번호 저장: {ol_shop_no}")

                    db.update_selling_product(**update_params)

                    success_count += 1
                    logger.info(f"[상품등록] 성공: {product.get('product_name')}")
                else:
                    fail_count += 1
                    logger.error(f"[상품등록] 실패: {product.get('product_name')} - {result.get('error')}")

                results.append({
                    "product_id": product_id,
                    "product_name": product.get("product_name"),
                    "success": result.get("success"),
                    "error": result.get("error"),
                    "c_sale_cd": result.get("c_sale_cd")
                })

            except Exception as e:
                logger.error(f"[상품등록] 상품 등록 중 오류: ID {product_id} - {str(e)}")
                results.append({
                    "product_id": product_id,
                    "success": False,
                    "error": str(e)
                })
                fail_count += 1

        # 캐시 무효화
        clear_all_cache()

        logger.info(f"[상품등록] 완료: 성공 {success_count}개, 실패 {fail_count}개")

        return {
            "success": True,
            "total": len(product_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[상품등록] 플레이오토 등록 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"플레이오토 등록 실패: {str(e)}")
