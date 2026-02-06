"""
내 판매 상품 관리 API
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
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
    detail_page_html: Optional[str] = None  # 렌더링된 HTML (우선 사용)
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
    c_sale_cd: Optional[str] = None  # 하위 호환성
    c_sale_cd_gmk: Optional[str] = None  # 지마켓/옥션용
    c_sale_cd_smart: Optional[str] = None  # 스마트스토어용


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

        # 썸네일 자동 업로드: original_thumbnail_url이 있으면 Supabase에 업로드
        thumbnail_url = request.thumbnail_url
        if request.original_thumbnail_url and not thumbnail_url:
            from utils.supabase_storage import upload_image_from_url
            import time

            # 고유한 파일명 생성 (타임스탬프 사용)
            timestamp = int(time.time())
            file_ext = request.original_thumbnail_url.split('?')[0].split('.')[-1]
            if file_ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                file_ext = 'jpg'

            storage_path = f"thumbnails/product_{timestamp}.{file_ext}"

            logger.info(f"[상품생성] 썸네일 다운로드 및 업로드 시작: {request.original_thumbnail_url[:100]}...")
            supabase_url = upload_image_from_url(request.original_thumbnail_url, storage_path)

            if supabase_url:
                thumbnail_url = supabase_url
                logger.info(f"[상품생성] 썸네일 업로드 성공: {storage_path}")
            else:
                logger.warning(f"[상품생성] 썸네일 업로드 실패, 원본 URL 사용")
                thumbnail_url = request.original_thumbnail_url

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
            thumbnail_url=thumbnail_url,
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

        # PlayAuto 동기화가 필요한 변경사항 추적
        playauto_changes = {}

        # 상품명 변경 확인
        if request.product_name and request.product_name != product.get('product_name'):
            playauto_changes['shop_sale_name'] = request.product_name

        # 판매가 변경 확인
        if request.selling_price is not None and request.selling_price != product.get('selling_price'):
            playauto_changes['sale_price'] = int(request.selling_price)

        # 썸네일 변경 확인
        if request.thumbnail_url and request.thumbnail_url != product.get('thumbnail_url'):
            playauto_changes['sale_img1'] = request.thumbnail_url

        # 카테고리 변경 시 자동 매핑
        sol_cate_no = None
        if request.category:
            sol_cate_no = get_playauto_category_code(request.category)
            if sol_cate_no:
                logger.info(f"[상품수정] 카테고리 자동 매핑: {request.category} -> {sol_cate_no}")
                # 카테고리가 변경된 경우 PlayAuto에도 반영
                if sol_cate_no != product.get('sol_cate_no'):
                    playauto_changes['sol_cate_no'] = sol_cate_no
            else:
                logger.warning(f"[상품수정] 카테고리 매핑 없음: {request.category}")

        # 채널별 c_sale_cd 처리
        c_sale_cd_gmk = request.c_sale_cd_gmk if request.c_sale_cd_gmk is not None else product.get('c_sale_cd_gmk')
        c_sale_cd_smart = request.c_sale_cd_smart if request.c_sale_cd_smart is not None else product.get('c_sale_cd_smart')

        if request.c_sale_cd_gmk is not None:
            logger.info(f"[상품수정] 지마켓/옥션 c_sale_cd 변경: {product.get('c_sale_cd_gmk')} -> {request.c_sale_cd_gmk}")
        if request.c_sale_cd_smart is not None:
            logger.info(f"[상품수정] 스마트스토어 c_sale_cd 변경: {product.get('c_sale_cd_smart')} -> {request.c_sale_cd_smart}")

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
            notes=request.notes,
            c_sale_cd_gmk=c_sale_cd_gmk,
            c_sale_cd_smart=c_sale_cd_smart
        )

        # 플레이오토 API 업데이트 (변경사항 + 플레이오토 상품인 경우)
        # 두 채널 모두 업데이트
        playauto_updated_gmk = False
        playauto_updated_smart = False

        if playauto_changes:
            from playauto.products import edit_playauto_product
            changed_fields = ', '.join(playauto_changes.keys())

            # 1. 지마켓/옥션 상품 업데이트
            if c_sale_cd_gmk:
                try:
                    logger.info(f"[상품수정] 지마켓/옥션 PlayAuto 업데이트 시작: c_sale_cd={c_sale_cd_gmk}, 변경항목={changed_fields}")

                    result_gmk = await edit_playauto_product(
                        c_sale_cd=c_sale_cd_gmk,
                        shop_cd="master",
                        shop_id="master",
                        edit_slave_all=True,
                        **playauto_changes
                    )

                    if result_gmk.get('success'):
                        playauto_updated_gmk = True
                        logger.info(f"[상품수정] 지마켓/옥션 PlayAuto 업데이트 성공")
                    else:
                        error_msg = result_gmk.get('message', '알 수 없는 오류')
                        logger.error(f"[상품수정] 지마켓/옥션 PlayAuto 업데이트 실패: {error_msg}")

                except Exception as e:
                    logger.error(f"[상품수정] 지마켓/옥션 PlayAuto 업데이트 실패: {str(e)}")

            # 2. 스마트스토어 상품 업데이트
            if c_sale_cd_smart:
                try:
                    logger.info(f"[상품수정] 스마트스토어 PlayAuto 업데이트 시작: c_sale_cd={c_sale_cd_smart}, 변경항목={changed_fields}")

                    result_smart = await edit_playauto_product(
                        c_sale_cd=c_sale_cd_smart,
                        shop_cd="master",
                        shop_id="master",
                        edit_slave_all=True,
                        **playauto_changes
                    )

                    if result_smart.get('success'):
                        playauto_updated_smart = True
                        logger.info(f"[상품수정] 스마트스토어 PlayAuto 업데이트 성공")
                    else:
                        error_msg = result_smart.get('message', '알 수 없는 오류')
                        logger.error(f"[상품수정] 스마트스토어 PlayAuto 업데이트 실패: {error_msg}")

                except Exception as e:
                    logger.error(f"[상품수정] 스마트스토어 PlayAuto 업데이트 실패: {str(e)}")

        # 캐시 무효화
        clear_all_cache()

        return {
            "success": True,
            "message": "상품이 수정되었습니다.",
            "playauto_updated_gmk": playauto_updated_gmk,
            "playauto_updated_smart": playauto_updated_smart,
            "playauto_changes": list(playauto_changes.keys()) if playauto_changes else []
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

                # site_list를 채널 종류별로 분리
                # 각 shop_cd 로깅
                logger.info(f"[상품등록] 원본 site_list: {site_list}")
                for site in site_list:
                    logger.info(f"[상품등록] 채널 정보 - shop_cd: {site.get('shop_cd')}, shop_id: {site.get('shop_id')}, template_no: {site.get('template_no')}")

                # 지마켓(GMK), 옥션(Auction) 관련 shop_cd
                # A001: 지마켓(GMK), A006: 옥션(Auction)
                gmk_auction_codes = ["GMK", "gmk", "A001", "a001", "A006", "a006", "AUCTION", "auction"]
                esm_codes = ["ESM", "esm", "Esm"]  # ESM은 제외

                # ESM 제외하고 채널 분리
                gmk_auction_sites = [site for site in site_list
                                     if site.get("shop_cd") in gmk_auction_codes
                                     and site.get("shop_cd") not in esm_codes]
                smartstore_sites = [site for site in site_list
                                   if site.get("shop_cd") not in gmk_auction_codes
                                   and site.get("shop_cd") not in esm_codes]

                # ESM 채널 확인 및 경고
                esm_sites = [site for site in site_list if site.get("shop_cd") in esm_codes]
                if esm_sites:
                    logger.warning(f"[상품등록] ESM 채널 {len(esm_sites)}개 감지 - ESM은 단일상품 제약이 있어 자동 등록에서 제외됩니다")

                logger.info(f"[상품등록] 채널 분리 완료:")
                logger.info(f"  - 지마켓/옥션: {len(gmk_auction_sites)}개 {[s.get('shop_cd') for s in gmk_auction_sites]}")
                logger.info(f"  - 스마트스토어 등: {len(smartstore_sites)}개 {[s.get('shop_cd') for s in smartstore_sites]}")
                logger.info(f"  - ESM 제외: {len(esm_sites)}개 {[s.get('shop_cd') for s in esm_sites]}")

                # 디버깅: 실제 전달 데이터 로그
                logger.info(f"[상품등록] product_id={product_id}, category='{product.get('category')}', sol_cate_no={product.get('sol_cate_no')}")

                # 플레이오토 등록 (채널별로 분리)
                result = {"success": False, "error": "등록 가능한 채널이 없습니다."}
                c_sale_cd_gmk = None
                c_sale_cd_smart = None

                # 1. 지마켓/옥션 등록 (있는 경우)
                if gmk_auction_sites:
                    logger.info(f"[상품등록] ===== 지마켓/옥션 등록 시작 =====")
                    logger.info(f"[상품등록] 채널 수: {len(gmk_auction_sites)}개")
                    logger.info(f"[상품등록] 설정: std_ol_yn=Y (단일상품), opt_type=옵션없음")
                    product_data_gmk = build_product_data_from_db(product, gmk_auction_sites, channel_type="gmk_auction")
                    result_gmk = await registration_api.register_product(product_data_gmk)

                    if result_gmk.get("success"):
                        c_sale_cd_gmk = result_gmk.get("c_sale_cd")
                        logger.info(f"[상품등록] ✓ 지마켓/옥션 등록 성공")
                        logger.info(f"[상품등록] c_sale_cd_gmk: {c_sale_cd_gmk}")
                        logger.info(f"[상품등록] 등록 결과: {result_gmk.get('site_list')}")
                        result = result_gmk
                    else:
                        logger.error(f"[상품등록] ✗ 지마켓/옥션 등록 실패: {result_gmk.get('error')}")
                        logger.error(f"[상품등록] 전체 응답: {result_gmk}")

                # 2. 스마트스토어 등 등록 (있는 경우)
                if smartstore_sites:
                    logger.info(f"[상품등록] ===== 스마트스토어 등 등록 시작 =====")
                    logger.info(f"[상품등록] 채널 수: {len(smartstore_sites)}개")
                    logger.info(f"[상품등록] 설정: std_ol_yn=N (단일상품 아님), opt_type=독립형")
                    product_data_smart = build_product_data_from_db(product, smartstore_sites, channel_type="smartstore")
                    result_smart = await registration_api.register_product(product_data_smart)

                    if result_smart.get("success"):
                        c_sale_cd_smart = result_smart.get("c_sale_cd")
                        logger.info(f"[상품등록] ✓ 스마트스토어 등 등록 성공")
                        logger.info(f"[상품등록] c_sale_cd_smart: {c_sale_cd_smart}")
                        logger.info(f"[상품등록] 등록 결과: {result_smart.get('site_list')}")
                        # 지마켓/옥션 결과와 병합
                        if result.get("success"):
                            # 두 결과 병합
                            result["site_list"] = result.get("site_list", []) + result_smart.get("site_list", [])
                        else:
                            result = result_smart
                    else:
                        logger.error(f"[상품등록] ✗ 스마트스토어 등 등록 실패: {result_smart.get('error')}")
                        logger.error(f"[상품등록] 전체 응답: {result_smart}")

                # ESM 에러 시 재시도 (ESM 채널 및 ESM 템플릿 사용 채널 제외)
                if not result.get("success") and result.get("error"):
                    error_msg = result.get("error", "")
                    if "ESM" in error_msg and "단일상품" in error_msg:
                        logger.warning(f"[상품등록] ESM 에러 감지 - 문제 채널 제외하고 재시도: {product.get('product_name')}")
                        logger.warning(f"[상품등록] 원본 에러: {error_msg}")

                        # site_list에서 ESM 채널 제외 (shop_cd가 ESM인 것 + A006 옥션도 제외)
                        # A006 (옥션)은 ESM 템플릿을 사용할 수 있으므로 함께 제외
                        filtered_site_list = [
                            site for site in product_data.get("site_list", [])
                            if site.get("shop_cd") not in ["ESM", "esm", "Esm", "A006"]
                        ]

                        if filtered_site_list:
                            product_data["site_list"] = filtered_site_list
                            logger.info(f"[상품등록] ESM/A006 제외 후 {len(filtered_site_list)}개 채널로 재시도")
                            result = await registration_api.register_product(product_data)
                        else:
                            logger.error(f"[상품등록] 등록 가능한 채널이 없어 재시도 불가")

                if result.get("success"):
                    # 플레이오토 상품 번호 및 쇼핑몰 번호 저장
                    site_list_result = result.get("site_list", [])

                    # 디버깅: site_list 전체 구조 로깅
                    logger.info(f"[상품등록] site_list 응답: {site_list_result}")

                    # ol_shop_no를 GMK와 SmartStore로 분리하여 저장
                    ol_shop_no_gmk = None
                    ol_shop_no_smart = None
                    ol_shop_no_fallback = None  # 하위 호환성

                    if site_list_result:
                        for site in site_list_result:
                            logger.info(f"[상품등록] site 확인: shop_cd={site.get('shop_cd')}, shop_name={site.get('shop_name')}, ol_shop_no={site.get('ol_shop_no')}")

                            # PlayAuto API 응답에서 site_list 내부에는 result 필드가 없음
                            # ol_shop_no가 있으면 성공한 것으로 처리
                            if site.get("ol_shop_no"):
                                shop_cd = site.get("shop_cd", "")
                                ol_no = site.get("ol_shop_no")

                                # 첫 번째 성공한 ol_shop_no를 fallback으로 저장 (하위 호환성)
                                if not ol_shop_no_fallback:
                                    ol_shop_no_fallback = ol_no

                                # 채널별로 분류하여 저장
                                # GMK 채널: Z000(마스터), A001(옥션), A002(지마켓)
                                # SmartStore 채널: A027(스마트스토어) 등
                                if shop_cd in ["Z000", "A001", "A002"] and c_sale_cd_gmk:
                                    # GMK 등록에서 나온 ol_shop_no
                                    if not ol_shop_no_gmk or shop_cd == "Z000":  # Z000(마스터) 우선
                                        ol_shop_no_gmk = ol_no
                                        logger.info(f"[상품등록] GMK ol_shop_no 발견: {ol_no} (shop_cd: {shop_cd})")
                                elif c_sale_cd_smart:
                                    # SmartStore 등록에서 나온 ol_shop_no
                                    if not ol_shop_no_smart or shop_cd == "Z000":  # Z000(마스터) 우선
                                        ol_shop_no_smart = ol_no
                                        logger.info(f"[상품등록] SmartStore ol_shop_no 발견: {ol_no} (shop_cd: {shop_cd})")

                    if not ol_shop_no_gmk and not ol_shop_no_smart:
                        logger.warning(f"[상품등록] ol_shop_no를 찾지 못했습니다. site_list: {site_list_result}")

                    # 등록 성공 시 is_active = True로 변경하고 PlayAuto ID 저장
                    update_params = {"product_id": product_id, "is_active": True}

                    # 채널별 c_sale_cd 저장
                    if c_sale_cd_gmk:
                        update_params["c_sale_cd_gmk"] = c_sale_cd_gmk
                        update_params["playauto_product_no"] = c_sale_cd_gmk  # 하위 호환성
                        logger.info(f"[상품등록] 지마켓/옥션 c_sale_cd 저장: {c_sale_cd_gmk}")
                    if c_sale_cd_smart:
                        update_params["c_sale_cd_smart"] = c_sale_cd_smart
                        if not c_sale_cd_gmk:  # gmk가 없으면 smart를 playauto_product_no에 저장
                            update_params["playauto_product_no"] = c_sale_cd_smart
                        logger.info(f"[상품등록] 스마트스토어 c_sale_cd 저장: {c_sale_cd_smart}")

                    # 채널별 ol_shop_no 저장
                    if ol_shop_no_gmk:
                        update_params["ol_shop_no_gmk"] = ol_shop_no_gmk
                        logger.info(f"[상품등록] GMK 온라인 쇼핑몰 번호 저장: {ol_shop_no_gmk}")
                    if ol_shop_no_smart:
                        update_params["ol_shop_no_smart"] = ol_shop_no_smart
                        logger.info(f"[상품등록] SmartStore 온라인 쇼핑몰 번호 저장: {ol_shop_no_smart}")

                    # 하위 호환성: ol_shop_no 필드에도 저장 (우선순위: gmk > smart)
                    if ol_shop_no_fallback:
                        update_params["ol_shop_no"] = ol_shop_no_fallback
                        logger.info(f"[상품등록] 온라인 쇼핑몰 번호 저장 (하위호환): {ol_shop_no_fallback}")

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
                    "c_sale_cd_gmk": c_sale_cd_gmk,
                    "c_sale_cd_smart": c_sale_cd_smart
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


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """
    이미지 파일을 Supabase Storage에 업로드

    Returns:
        업로드된 이미지의 공개 URL
    """
    try:
        from utils.supabase_storage import upload_image_from_bytes
        import time

        # 파일 내용 읽기
        contents = await file.read()

        # 파일 확장자 추출
        filename = file.filename or "image.jpg"
        file_ext = filename.split('.')[-1].lower()
        if file_ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            file_ext = 'jpg'

        # 고유한 파일명 생성
        timestamp = int(time.time())
        import random
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        storage_path = f"detail-pages/{timestamp}_{random_str}.{file_ext}"

        # Supabase에 업로드
        logger.info(f"[이미지업로드] 업로드 시작: {storage_path}")
        public_url = upload_image_from_bytes(contents, storage_path, content_type=file.content_type)

        if public_url:
            logger.info(f"[이미지업로드] 성공: {public_url}")
            return {
                "success": True,
                "url": public_url,
                "storage_path": storage_path
            }
        else:
            logger.error(f"[이미지업로드] 실패: upload_image_from_bytes returned None")
            raise HTTPException(status_code=500, detail="이미지 업로드에 실패했습니다")

    except Exception as e:
        logger.error(f"[이미지업로드] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 업로드 실패: {str(e)}")


@router.post("/{product_id}/sync-to-playauto")
async def sync_product_to_playauto(product_id: int):
    """
    상품 정보를 PlayAuto에 동기화 (수정)

    Args:
        product_id: 동기화할 상품 ID

    Returns:
        동기화 결과
    """
    try:
        db = get_db()
        conn = db.get_connection()

        # 상품 정보 조회
        cursor = conn.execute("""
            SELECT id, product_name, selling_price, sourcing_price,
                   category, thumbnail_url, detail_page_data,
                   playauto_product_no, c_sale_cd
            FROM selling_products
            WHERE id = ?
        """, (product_id,))
        product = cursor.fetchone()
        conn.close()

        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

        product_dict = {
            'id': product[0],
            'product_name': product[1],
            'selling_price': product[2],
            'sourcing_price': product[3],
            'category': product[4],
            'thumbnail_url': product[5],
            'detail_page_data': product[6],
            'playauto_product_no': product[7],
            'c_sale_cd': product[8]
        }

        # PlayAuto 상품 번호가 없으면 에러
        if not product_dict.get('c_sale_cd'):
            raise HTTPException(
                status_code=400,
                detail="PlayAuto에 등록되지 않은 상품입니다. 먼저 '상품등록'을 진행해주세요."
            )

        # PlayAuto 상품 수정 API 호출
        from playauto.products import edit_playauto_product

        # 카테고리 코드 조회
        sol_cate_no = None
        if product_dict.get('category'):
            from playauto.product_registration import get_sol_cate_no_for_category
            sol_cate_no = get_sol_cate_no_for_category(product_dict['category'])

        # 상품 수정 요청
        # 옵션은 수정하지 않음 (opts, opt_type 제외)
        result = await edit_playauto_product(
            c_sale_cd=product_dict['c_sale_cd'],
            shop_cd="master",  # 마스터 상품 수정
            shop_id="master",
            shop_sale_name=product_dict['product_name'],
            sale_price=int(product_dict['selling_price']),
            sol_cate_no=sol_cate_no,
            edit_slave_all=True,  # 하위 쇼핑몰 상품도 함께 수정
            sale_img1=product_dict.get('thumbnail_url')
        )

        if result.get('success'):
            logger.info(f"[상품동기화] PlayAuto 동기화 성공: product_id={product_id}, c_sale_cd={product_dict['c_sale_cd']}")

            # 캐시 무효화
            clear_all_cache()

            return {
                "success": True,
                "message": "PlayAuto에 상품 정보가 동기화되었습니다.",
                "product_name": product_dict['product_name'],
                "selling_price": product_dict['selling_price']
            }
        else:
            error_msg = result.get('message', '알 수 없는 오류')
            logger.error(f"[상품동기화] PlayAuto 동기화 실패: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PlayAuto 동기화 실패: {error_msg}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[상품동기화] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상품 동기화 실패: {str(e)}")


@router.post("/{product_id}/reset-playauto")
async def reset_playauto_info(product_id: int):
    """
    상품의 PlayAuto 등록 정보를 초기화
    PlayAuto에 존재하지 않는 상품의 정보를 DB에서 제거하여 다시 등록 가능하게 함

    Args:
        product_id: 초기화할 상품 ID

    Returns:
        초기화 결과
    """
    try:
        db = get_db()

        # 상품 존재 확인
        product = db.get_selling_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        logger.info(f"[PlayAuto초기화] 상품 {product_id}번 초기화 시작")
        logger.info(f"[PlayAuto초기화] 현재 c_sale_cd: {product.get('c_sale_cd')}")

        # PlayAuto 정보 초기화
        db.update_selling_product(
            product_id=product_id,
            playauto_product_no=None,
            c_sale_cd=None,
            ol_shop_no=None
        )

        # 캐시 무효화
        clear_all_cache()

        logger.info(f"[PlayAuto초기화] 상품 {product_id}번 초기화 완료")

        return {
            "success": True,
            "message": "PlayAuto 등록 정보가 초기화되었습니다. 이제 '상품등록' 버튼을 눌러 다시 등록하세요.",
            "product_name": product.get('product_name')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PlayAuto초기화] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PlayAuto 정보 초기화 실패: {str(e)}")


# ========================================
# 마켓 코드 관리 API
# ========================================

@router.get("/{product_id}/marketplace-codes")
async def get_product_marketplace_codes(product_id: int):
    """
    상품의 마켓별 상품번호 조회

    Args:
        product_id: 판매 상품 ID

    Returns:
        마켓별 shop_sale_no 목록
    """
    try:
        db = get_db()

        # 상품 존재 확인
        product = db.get_selling_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # 마켓 코드 조회
        codes = db.get_marketplace_codes_by_product(product_id)

        return {
            "success": True,
            "product_id": product_id,
            "product_name": product.get("product_name"),
            "ol_shop_no": product.get("ol_shop_no"),
            "marketplace_codes": codes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[마켓코드조회] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"마켓 코드 조회 실패: {str(e)}")


@router.post("/{product_id}/sync-marketplace-codes")
async def sync_product_marketplace_codes(product_id: int):
    """
    특정 상품의 마켓 코드 강제 동기화

    Args:
        product_id: 판매 상품 ID

    Returns:
        동기화 결과
    """
    try:
        db = get_db()

        # 상품 존재 확인
        product = db.get_selling_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # 채널별 ol_shop_no 확인 (신규 분리 필드 우선)
        ol_shop_no_gmk = product.get("ol_shop_no_gmk")
        ol_shop_no_smart = product.get("ol_shop_no_smart")
        ol_shop_no_legacy = product.get("ol_shop_no")  # 하위 호환성

        # ol_shop_no가 없으면 에러
        if not ol_shop_no_gmk and not ol_shop_no_smart and not ol_shop_no_legacy:
            c_sale_cd_gmk = product.get("c_sale_cd_gmk")
            c_sale_cd_smart = product.get("c_sale_cd_smart")

            logger.error(f"[마켓코드동기화] 상품 {product_id}번: ol_shop_no가 DB에 없습니다. 상품 재등록 필요")

            if c_sale_cd_gmk or c_sale_cd_smart:
                raise HTTPException(
                    status_code=400,
                    detail=f"ol_shop_no가 DB에 저장되지 않았습니다.\n\n해결 방법:\n1. PlayAuto에서 상품을 삭제하고 다시 등록\n2. 또는 관리자에게 문의하여 수동으로 ol_shop_no 입력\n\n(c_sale_cd_gmk: {c_sale_cd_gmk}, c_sale_cd_smart: {c_sale_cd_smart})"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="PlayAuto에 등록되지 않은 상품입니다. 먼저 상품을 등록하세요."
                )

        # PlayAuto API 호출 - 상품 리스트 API 사용 (shop_sale_no 직접 조회)
        from playauto.products import PlayautoProductAPI
        api = PlayautoProductAPI()

        logger.info(f"[마켓코드동기화] 상품 {product_id}번 동기화 시작")

        # c_sale_cd로 검색
        c_sale_cd_gmk = product.get("c_sale_cd_gmk")
        c_sale_cd_smart = product.get("c_sale_cd_smart")

        c_sale_cd_list = []
        if c_sale_cd_gmk:
            c_sale_cd_list.append(c_sale_cd_gmk)
        if c_sale_cd_smart:
            c_sale_cd_list.append(c_sale_cd_smart)

        if not c_sale_cd_list:
            return {
                "success": True,
                "message": "c_sale_cd가 없습니다. 상품을 먼저 등록하세요.",
                "synced_count": 0,
                "marketplace_codes": []
            }

        # 상품 리스트 API로 조회 (shop_sale_no 포함)
        all_shops = []
        try:
            result = await api.search_products_by_c_sale_cd(c_sale_cd_list)
            results = result.get("results", {})

            for c_sale_cd, items in results.items():
                for item in items:
                    shop_cd = item.get("shop_cd")
                    shop_sale_no = item.get("shop_sale_no")
                    shop_name = item.get("shop_name", "")

                    # Z000(마스터)은 shop_sale_no가 없으므로 스킵
                    if shop_cd and shop_cd != "Z000" and shop_sale_no:
                        all_shops.append({
                            "shop_cd": shop_cd,
                            "shop_sale_no": shop_sale_no,
                            "shop_name": shop_name
                        })
                        logger.info(f"[마켓코드동기화] 발견: {shop_name} ({shop_cd}): {shop_sale_no}")

        except Exception as e:
            logger.error(f"[마켓코드동기화] 상품 리스트 조회 실패: {e}")

        shops = all_shops

        if not shops:
            return {
                "success": True,
                "message": "아직 마켓에 전송되지 않은 상품입니다.",
                "synced_count": 0,
                "marketplace_codes": []
            }

        # DB에 저장
        synced_count = 0
        from datetime import datetime

        for shop in shops:
            shop_cd = shop.get("shop_cd")
            shop_name = shop.get("shop_name")
            shop_sale_no = shop.get("shop_sale_no")

            if shop_cd and shop_sale_no:
                db.upsert_marketplace_code(
                    product_id=product_id,
                    shop_cd=shop_cd,
                    shop_name=shop_name,
                    shop_sale_no=shop_sale_no,
                    transmitted_at=datetime.now()
                )
                synced_count += 1
                logger.info(f"[마켓코드동기화] {shop_name} ({shop_cd}): {shop_sale_no}")

        # 동기화된 코드 조회
        codes = db.get_marketplace_codes_by_product(product_id)

        return {
            "success": True,
            "message": f"{synced_count}개 마켓 코드 동기화 완료",
            "synced_count": synced_count,
            "marketplace_codes": codes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[마켓코드동기화] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"마켓 코드 동기화 실패: {str(e)}")


@router.post("/sync-all-marketplace-codes")
async def sync_all_marketplace_codes():
    """
    모든 상품의 마켓 코드 일괄 동기화 (이미 수집된 건 스킵)

    Returns:
        동기화 결과
    """
    try:
        db = get_db()

        logger.info("[일괄마켓코드동기화] 시작")

        # 마켓 코드가 없는 상품만 조회 (이미 있는 건 스킵)
        products = db.get_products_without_marketplace_codes(limit=500)

        if not products:
            return {
                "success": True,
                "message": "동기화할 상품이 없습니다. 모든 상품이 이미 수집되었습니다.",
                "total_products": 0,
                "synced_products": 0,
                "skipped_products": 0,
                "error_products": 0
            }

        logger.info(f"[일괄마켓코드동기화] 대상 상품: {len(products)}개")

        # PlayAuto API 클라이언트
        from playauto.products import PlayautoProductAPI
        api = PlayautoProductAPI()

        synced_products = 0
        skipped_products = 0
        error_products = 0
        from datetime import datetime

        # c_sale_cd 수집 및 매핑
        c_sale_cd_to_product = {}  # c_sale_cd -> product_id
        c_sale_cd_list = []

        for product in products:
            product_id = product.get("id")
            c_sale_cd_gmk = product.get("c_sale_cd_gmk") or product.get("playauto_product_no")
            c_sale_cd_smart = product.get("c_sale_cd_smart")

            if c_sale_cd_gmk:
                c_sale_cd_list.append(c_sale_cd_gmk)
                c_sale_cd_to_product[c_sale_cd_gmk] = product_id
            if c_sale_cd_smart:
                c_sale_cd_list.append(c_sale_cd_smart)
                c_sale_cd_to_product[c_sale_cd_smart] = product_id

        if not c_sale_cd_list:
            return {
                "success": True,
                "message": "c_sale_cd가 있는 상품이 없습니다.",
                "total_products": len(products),
                "synced_products": 0,
                "skipped_products": len(products),
                "error_products": 0
            }

        # 상품 리스트 API로 일괄 조회 (50개씩)
        try:
            for i in range(0, len(c_sale_cd_list), 50):
                batch = c_sale_cd_list[i:i+50]
                result = await api.search_products_by_c_sale_cd(batch)
                results = result.get("results", {})

                for c_sale_cd, items in results.items():
                    product_id = c_sale_cd_to_product.get(c_sale_cd)
                    if not product_id:
                        continue

                    codes_synced = 0
                    for item in items:
                        shop_cd = item.get("shop_cd")
                        shop_sale_no = item.get("shop_sale_no")
                        shop_name = item.get("shop_name", "")

                        # Z000(마스터)은 shop_sale_no가 없으므로 스킵
                        if shop_cd and shop_cd != "Z000" and shop_sale_no:
                            db.upsert_marketplace_code(
                                product_id=product_id,
                                shop_cd=shop_cd,
                                shop_name=shop_name,
                                shop_sale_no=shop_sale_no,
                                transmitted_at=datetime.now()
                            )
                            codes_synced += 1
                            logger.info(f"[일괄마켓코드동기화] 상품 {product_id}: {shop_name} ({shop_cd}): {shop_sale_no}")

                    if codes_synced > 0:
                        synced_products += 1
                    else:
                        skipped_products += 1

        except Exception as e:
            error_products += len(products)
            logger.error(f"[일괄마켓코드동기화] API 조회 실패: {e}")

        message = f"✅ {synced_products}개 상품 수집 완료"
        if skipped_products > 0:
            message += f", {skipped_products}개 스킵"
        if error_products > 0:
            message += f", {error_products}개 실패"

        logger.info(f"[일괄마켓코드동기화] 완료: {message}")

        return {
            "success": True,
            "message": message,
            "total_products": len(products),
            "synced_products": synced_products,
            "skipped_products": skipped_products,
            "error_products": error_products
        }

    except Exception as e:
        logger.error(f"[일괄마켓코드동기화] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일괄 마켓 코드 동기화 실패: {str(e)}")


@router.post("/recover-ol-shop-no")
async def recover_ol_shop_no():
    """
    ol_shop_no가 누락된 기존 상품들의 ol_shop_no를 PlayAuto API에서 복구

    c_sale_cd는 있지만 ol_shop_no가 없는 상품을 찾아서
    PlayAuto 상품 리스트 API로 ol_shop_no를 조회하여 DB 업데이트
    """
    try:
        db = get_db()
        from playauto.products import PlayautoProductAPI
        api = PlayautoProductAPI()

        # 활성 상품 전체 조회
        all_products = db.get_selling_products(is_active=True, limit=1000)

        # ol_shop_no가 없지만 c_sale_cd가 있는 상품 필터링
        products = []
        for p in all_products:
            c_sale_cd_gmk = p.get("c_sale_cd_gmk")
            c_sale_cd_smart = p.get("c_sale_cd_smart")
            ol_shop_no_gmk = p.get("ol_shop_no_gmk")
            ol_shop_no_smart = p.get("ol_shop_no_smart")

            needs_gmk = c_sale_cd_gmk and (not ol_shop_no_gmk or ol_shop_no_gmk == 0)
            needs_smart = c_sale_cd_smart and (not ol_shop_no_smart or ol_shop_no_smart == 0)

            if needs_gmk or needs_smart:
                products.append(p)

        if not products:
            return {
                "success": True,
                "message": "복구가 필요한 상품이 없습니다.",
                "recovered_count": 0
            }

        logger.info(f"[ol_shop_no 복구] {len(products)}개 상품 복구 시작")

        # c_sale_cd 목록 수집 (GMK와 Smart 분리)
        gmk_c_sale_cds = []
        smart_c_sale_cds = []
        product_map = {}  # c_sale_cd -> product_id 매핑

        for product in products:
            product_id = product["id"]
            c_sale_cd_gmk = product.get("c_sale_cd_gmk")
            c_sale_cd_smart = product.get("c_sale_cd_smart")
            ol_shop_no_gmk = product.get("ol_shop_no_gmk")
            ol_shop_no_smart = product.get("ol_shop_no_smart")

            # GMK 채널 복구 필요
            if c_sale_cd_gmk and (not ol_shop_no_gmk or ol_shop_no_gmk == 0):
                gmk_c_sale_cds.append(c_sale_cd_gmk)
                product_map[c_sale_cd_gmk] = {"product_id": product_id, "channel": "gmk"}

            # SmartStore 채널 복구 필요
            if c_sale_cd_smart and (not ol_shop_no_smart or ol_shop_no_smart == 0):
                smart_c_sale_cds.append(c_sale_cd_smart)
                product_map[c_sale_cd_smart] = {"product_id": product_id, "channel": "smart"}

        recovered_count = 0
        error_count = 0

        # GMK 채널 복구
        if gmk_c_sale_cds:
            logger.info(f"[ol_shop_no 복구] GMK 채널: {len(gmk_c_sale_cds)}개 조회")
            try:
                # 최대 50개씩 나눠서 조회
                for i in range(0, len(gmk_c_sale_cds), 50):
                    batch = gmk_c_sale_cds[i:i+50]
                    result = await api.search_products_by_c_sale_cd(batch)

                    results = result.get("results", {})
                    for c_sale_cd, items in results.items():
                        if c_sale_cd in product_map:
                            info = product_map[c_sale_cd]
                            product_id = info["product_id"]

                            # Z000(마스터) 상품의 ol_shop_no 찾기
                            ol_shop_no = None
                            for item in items:
                                if item.get("shop_cd") == "Z000":
                                    ol_shop_no = item.get("ol_shop_no")
                                    break
                            # Z000이 없으면 첫 번째 아이템 사용
                            if not ol_shop_no and items:
                                ol_shop_no = items[0].get("ol_shop_no")

                            if ol_shop_no:
                                db.update_selling_product(
                                    product_id=product_id,
                                    ol_shop_no_gmk=ol_shop_no
                                )
                                logger.info(f"[ol_shop_no 복구] 상품 {product_id}: GMK ol_shop_no={ol_shop_no} 복구")
                                recovered_count += 1

            except Exception as e:
                logger.error(f"[ol_shop_no 복구] GMK 채널 조회 실패: {e}")
                error_count += len(gmk_c_sale_cds)

        # SmartStore 채널 복구
        if smart_c_sale_cds:
            logger.info(f"[ol_shop_no 복구] SmartStore 채널: {len(smart_c_sale_cds)}개 조회")
            try:
                for i in range(0, len(smart_c_sale_cds), 50):
                    batch = smart_c_sale_cds[i:i+50]
                    result = await api.search_products_by_c_sale_cd(batch)

                    results = result.get("results", {})
                    for c_sale_cd, items in results.items():
                        if c_sale_cd in product_map:
                            info = product_map[c_sale_cd]
                            product_id = info["product_id"]

                            # Z000(마스터) 상품의 ol_shop_no 찾기
                            ol_shop_no = None
                            for item in items:
                                if item.get("shop_cd") == "Z000":
                                    ol_shop_no = item.get("ol_shop_no")
                                    break
                            if not ol_shop_no and items:
                                ol_shop_no = items[0].get("ol_shop_no")

                            if ol_shop_no:
                                db.update_selling_product(
                                    product_id=product_id,
                                    ol_shop_no_smart=ol_shop_no
                                )
                                logger.info(f"[ol_shop_no 복구] 상품 {product_id}: SmartStore ol_shop_no={ol_shop_no} 복구")
                                recovered_count += 1

            except Exception as e:
                logger.error(f"[ol_shop_no 복구] SmartStore 채널 조회 실패: {e}")
                error_count += len(smart_c_sale_cds)

        message = f"✅ {recovered_count}개 ol_shop_no 복구 완료"
        if error_count > 0:
            message += f", {error_count}개 실패"

        logger.info(f"[ol_shop_no 복구] 완료: {message}")

        return {
            "success": True,
            "message": message,
            "total_products": len(products),
            "recovered_count": recovered_count,
            "error_count": error_count
        }

    except Exception as e:
        logger.error(f"[ol_shop_no 복구] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ol_shop_no 복구 실패: {str(e)}")
