"""
자동 가격 조정 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database.db_wrapper import get_db
from logger import get_logger
from playauto.products import edit_playauto_product

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auto-pricing", tags=["auto-pricing"])


class AutoPricingSettings(BaseModel):
    """자동 가격 조정 설정"""
    enabled: bool = False
    target_margin: float = 30.0  # 목표 마진율 (%)
    min_margin: float = 15.0  # 최소 마진율 (%) - 이하면 판매 중단
    price_unit: int = 100  # 가격 올림 단위 (100원 단위)
    auto_disable_on_low_margin: bool = True  # 최소 마진 이하 시 자동 비활성화


@router.get("/settings")
async def get_auto_pricing_settings():
    """자동 가격 조정 설정 조회"""
    try:
        db = get_db()
        setting_value = db.get_playauto_setting('auto_pricing_settings')

        if setting_value:
            import json
            settings = json.loads(setting_value)
            return {
                "success": True,
                "settings": settings
            }
        else:
            # 기본 설정 반환
            return {
                "success": True,
                "settings": {
                    "enabled": False,
                    "target_margin": 30.0,
                    "min_margin": 15.0,
                    "price_unit": 100,
                    "auto_disable_on_low_margin": True
                }
            }

    except Exception as e:
        logger.error(f"[자동가격] 설정 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자동 가격 조정 설정 조회 실패: {str(e)}")


@router.post("/settings")
async def update_auto_pricing_settings(settings: AutoPricingSettings):
    """자동 가격 조정 설정 업데이트"""
    try:
        import json
        db = get_db()

        settings_json = json.dumps(settings.dict())

        # playauto_settings 테이블에 저장
        db.save_playauto_setting('auto_pricing_settings', settings_json, encrypted=False, notes='자동 가격 조정 설정')

        logger.info(f"[자동가격] 설정 업데이트: enabled={settings.enabled}, target_margin={settings.target_margin}%")

        return {
            "success": True,
            "message": "자동 가격 조정 설정이 업데이트되었습니다.",
            "settings": settings.dict()
        }

    except Exception as e:
        logger.error(f"[자동가격] 설정 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자동 가격 조정 설정 업데이트 실패: {str(e)}")


async def calculate_new_price(sourcing_price: float, target_margin: float, price_unit: int) -> int:
    """
    새 판매가 계산 (소싱가 기준 마진율)

    Args:
        sourcing_price: 소싱가
        target_margin: 목표 마진율 (%, 소싱가 기준)
        price_unit: 가격 올림 단위

    Returns:
        조정된 판매가

    Example:
        소싱가 10,000원, 목표 마진율 30% → 판매가 13,000원
        계산: 10,000 + (10,000 × 0.3) = 13,000원
    """
    # 목표 마진율로 판매가 계산 (소싱가 기준)
    # 마진율 = (판매가 - 소싱가) / 소싱가 * 100
    # 판매가 = 소싱가 * (1 + 마진율/100)

    target_price = sourcing_price * (1 + target_margin / 100)

    # 가격 올림 단위로 반올림
    adjusted_price = round(target_price / price_unit) * price_unit

    # 최소 가격: 소싱가 + 단위
    if adjusted_price < sourcing_price + price_unit:
        adjusted_price = sourcing_price + price_unit

    return int(adjusted_price)


@router.post("/adjust-product/{product_id}")
async def adjust_product_price(product_id: int):
    """
    특정 상품의 가격 자동 조정
    """
    try:
        db = get_db()

        # 자동 가격 조정 설정 확인
        setting_value = db.get_playauto_setting('auto_pricing_settings')

        if not setting_value:
            return {"success": False, "message": "자동 가격 조정이 설정되지 않았습니다."}

        import json
        settings = json.loads(setting_value)

        if not settings.get('enabled'):
            return {"success": False, "message": "자동 가격 조정이 비활성화되어 있습니다."}

        # 상품 정보 조회
        product = db.get_selling_product(product_id)

        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        product_name = product.get('product_name')
        sourcing_price = product.get('effective_sourcing_price') or product.get('sourcing_price', 0)
        old_selling_price = product.get('selling_price')
        is_active = product.get('is_active')

        if sourcing_price == 0:
            return {"success": False, "message": "소싱가가 설정되지 않았습니다."}

        # 새 판매가 계산
        new_selling_price = await calculate_new_price(
            sourcing_price,
            settings['target_margin'],
            settings['price_unit']
        )

        # 마진율 계산 (소싱가 기준)
        new_margin = ((new_selling_price - sourcing_price) / sourcing_price) * 100

        # 최소 마진율 체크
        should_disable = False
        if new_margin < settings['min_margin'] and settings['auto_disable_on_low_margin']:
            should_disable = True
            logger.warning(f"[자동가격] {product_name}: 최소 마진율 미달 ({new_margin:.1f}% < {settings['min_margin']}%) - 판매 중단")

        # 로컬 DB 가격 업데이트
        db.update_selling_product(
            product_id=product_id,
            selling_price=new_selling_price,
            is_active=False if should_disable else is_active
        )

        logger.info(f"[자동가격] {product_name}: {old_selling_price:,}원 → {new_selling_price:,}원 (마진 {new_margin:.1f}%)")

        # PlayAuto 가격 업데이트
        playauto_updated = False
        c_sale_cd_gmk = product.get('c_sale_cd_gmk')
        c_sale_cd_smart = product.get('c_sale_cd_smart')
        c_sale_cd_coupang = product.get('c_sale_cd_coupang')

        playauto_changes = {'sale_price': new_selling_price}

        # GMK (지마켓/옥션) 업데이트
        if c_sale_cd_gmk:
            try:
                result_gmk = await edit_playauto_product(
                    c_sale_cd=c_sale_cd_gmk,
                    shop_cd="master",
                    shop_id="master",
                    edit_slave_all=True,
                    **playauto_changes
                )
                if result_gmk.get('success'):
                    playauto_updated = True
                    logger.info(f"[자동가격] PlayAuto GMK 업데이트 성공: {c_sale_cd_gmk}")
                else:
                    logger.error(f"[자동가격] PlayAuto GMK 업데이트 실패: {result_gmk.get('message')}")
            except Exception as e:
                logger.error(f"[자동가격] PlayAuto GMK 업데이트 오류: {str(e)}")

        # 스마트스토어 업데이트
        if c_sale_cd_smart:
            try:
                result_smart = await edit_playauto_product(
                    c_sale_cd=c_sale_cd_smart,
                    shop_cd="master",
                    shop_id="master",
                    edit_slave_all=True,
                    **playauto_changes
                )
                if result_smart.get('success'):
                    playauto_updated = True
                    logger.info(f"[자동가격] PlayAuto 스마트스토어 업데이트 성공: {c_sale_cd_smart}")
                else:
                    logger.error(f"[자동가격] PlayAuto 스마트스토어 업데이트 실패: {result_smart.get('message')}")
            except Exception as e:
                logger.error(f"[자동가격] PlayAuto 스마트스토어 업데이트 오류: {str(e)}")

        # 쿠팡 업데이트
        if c_sale_cd_coupang:
            try:
                result_coupang = await edit_playauto_product(
                    c_sale_cd=c_sale_cd_coupang,
                    shop_cd="master",
                    shop_id="master",
                    edit_slave_all=True,
                    **playauto_changes
                )
                if result_coupang.get('success'):
                    playauto_updated = True
                    logger.info(f"[자동가격] PlayAuto 쿠팡 업데이트 성공: {c_sale_cd_coupang}")
                else:
                    logger.error(f"[자동가격] PlayAuto 쿠팡 업데이트 실패: {result_coupang.get('message')}")
            except Exception as e:
                logger.error(f"[자동가격] PlayAuto 쿠팡 업데이트 오류: {str(e)}")

        if not (c_sale_cd_gmk or c_sale_cd_smart or c_sale_cd_coupang):
            logger.warning(f"[자동가격] {product_name}: PlayAuto 판매자관리코드 없음 - 로컬 DB만 업데이트됨")

        # WebSocket 알림
        try:
            from api.websocket import notify_price_alert
            await notify_price_alert(
                product_name=product_name,
                old_price=old_selling_price,
                new_price=new_selling_price,
                margin=new_margin
            )
        except Exception as e:
            logger.warning(f"[자동가격] WebSocket 알림 실패: {e}")

        return {
            "success": True,
            "message": "가격이 자동 조정되었습니다.",
            "product_name": product_name,
            "old_price": old_selling_price,
            "new_price": new_selling_price,
            "margin": new_margin,
            "disabled": should_disable,
            "playauto_updated": playauto_updated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[자동가격] 가격 조정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자동 가격 조정 실패: {str(e)}")


@router.post("/adjust-all")
async def adjust_all_products():
    """
    모든 활성 상품의 가격 자동 조정
    """
    try:
        db = get_db()

        # 자동 가격 조정 설정 확인
        setting_value = db.get_playauto_setting('auto_pricing_settings')

        if not setting_value:
            return {"success": False, "message": "자동 가격 조정이 설정되지 않았습니다."}

        import json
        settings = json.loads(setting_value)

        if not settings.get('enabled'):
            return {"success": False, "message": "자동 가격 조정이 비활성화되어 있습니다."}

        # 모든 활성 상품 조회
        products = db.get_selling_products(is_active=True)

        # 각 상품 가격 조정
        adjusted_count = 0
        disabled_count = 0

        for product in products:
            product_id = product['id']
            try:
                result = await adjust_product_price(product_id)
                if result['success']:
                    adjusted_count += 1
                    if result.get('disabled'):
                        disabled_count += 1
            except Exception as e:
                logger.error(f"[자동가격] 상품 {product_id} 조정 실패: {str(e)}")
                continue

        logger.info(f"[자동가격] 일괄 조정 완료: {adjusted_count}개 조정, {disabled_count}개 비활성화")

        return {
            "success": True,
            "message": f"{adjusted_count}개 상품의 가격이 조정되었습니다.",
            "adjusted_count": adjusted_count,
            "disabled_count": disabled_count
        }

    except Exception as e:
        logger.error(f"[자동가격] 일괄 조정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자동 가격 조정 일괄 처리 실패: {str(e)}")
