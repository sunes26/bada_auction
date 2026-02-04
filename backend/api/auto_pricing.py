"""
자동 가격 조정 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database.db_wrapper import get_db
from logger import get_logger

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
        conn = db.get_connection()

        cursor = conn.execute("""
            SELECT setting_value FROM settings
            WHERE setting_key = 'auto_pricing_settings'
        """)
        row = cursor.fetchone()
        conn.close()

        if row:
            import json
            settings = json.loads(row[0])
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings")
async def update_auto_pricing_settings(settings: AutoPricingSettings):
    """자동 가격 조정 설정 업데이트"""
    try:
        import json
        db = get_db()
        conn = db.get_connection()

        settings_json = json.dumps(settings.dict())

        # settings 테이블에 저장
        cursor = conn.execute("""
            INSERT OR REPLACE INTO settings (setting_key, setting_value)
            VALUES ('auto_pricing_settings', ?)
        """, (settings_json,))
        conn.commit()
        conn.close()

        logger.info(f"[자동가격] 설정 업데이트: enabled={settings.enabled}, target_margin={settings.target_margin}%")

        return {
            "success": True,
            "message": "자동 가격 조정 설정이 업데이트되었습니다.",
            "settings": settings.dict()
        }

    except Exception as e:
        logger.error(f"[자동가격] 설정 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def calculate_new_price(sourcing_price: float, target_margin: float, price_unit: int) -> int:
    """
    새 판매가 계산

    Args:
        sourcing_price: 소싱가
        target_margin: 목표 마진율 (%)
        price_unit: 가격 올림 단위

    Returns:
        조정된 판매가
    """
    # 목표 마진율로 판매가 계산
    # 마진율 = (판매가 - 소싱가) / 판매가 * 100
    # 판매가 = 소싱가 / (1 - 마진율/100)

    target_price = sourcing_price / (1 - target_margin / 100)

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
        conn = db.get_connection()
        cursor = conn.execute("""
            SELECT setting_value FROM settings
            WHERE setting_key = 'auto_pricing_settings'
        """)
        row = cursor.fetchone()

        if not row:
            return {"success": False, "message": "자동 가격 조정이 설정되지 않았습니다."}

        import json
        settings = json.loads(row[0])

        if not settings.get('enabled'):
            return {"success": False, "message": "자동 가격 조정이 비활성화되어 있습니다."}

        # 상품 정보 조회
        cursor = conn.execute("""
            SELECT id, product_name, sourcing_price, selling_price, is_active
            FROM selling_products
            WHERE id = ?
        """, (product_id,))
        product = cursor.fetchone()

        if not product:
            conn.close()
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        product_id, product_name, sourcing_price, old_selling_price, is_active = product

        # 새 판매가 계산
        new_selling_price = await calculate_new_price(
            sourcing_price,
            settings['target_margin'],
            settings['price_unit']
        )

        # 마진율 계산
        new_margin = ((new_selling_price - sourcing_price) / new_selling_price) * 100

        # 최소 마진율 체크
        should_disable = False
        if new_margin < settings['min_margin'] and settings['auto_disable_on_low_margin']:
            should_disable = True
            logger.warning(f"[자동가격] {product_name}: 최소 마진율 미달 ({new_margin:.1f}% < {settings['min_margin']}%) - 판매 중단")

        # 가격 업데이트
        cursor = conn.execute("""
            UPDATE selling_products
            SET selling_price = ?,
                is_active = ?
            WHERE id = ?
        """, (new_selling_price, 0 if should_disable else is_active, product_id))
        conn.commit()
        conn.close()

        logger.info(f"[자동가격] {product_name}: {old_selling_price:,}원 → {new_selling_price:,}원 (마진 {new_margin:.1f}%)")

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
            "disabled": should_disable
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[자동가격] 가격 조정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adjust-all")
async def adjust_all_products():
    """
    모든 활성 상품의 가격 자동 조정
    """
    try:
        db = get_db()

        # 자동 가격 조정 설정 확인
        conn = db.get_connection()
        cursor = conn.execute("""
            SELECT setting_value FROM settings
            WHERE setting_key = 'auto_pricing_settings'
        """)
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {"success": False, "message": "자동 가격 조정이 설정되지 않았습니다."}

        import json
        settings = json.loads(row[0])

        if not settings.get('enabled'):
            conn.close()
            return {"success": False, "message": "자동 가격 조정이 비활성화되어 있습니다."}

        # 모든 활성 상품 조회
        cursor = conn.execute("""
            SELECT id FROM selling_products
            WHERE is_active = 1
        """)
        products = cursor.fetchall()
        conn.close()

        # 각 상품 가격 조정
        adjusted_count = 0
        disabled_count = 0

        for product in products:
            product_id = product[0]
            result = await adjust_product_price(product_id)
            if result['success']:
                adjusted_count += 1
                if result.get('disabled'):
                    disabled_count += 1

        logger.info(f"[자동가격] 일괄 조정 완료: {adjusted_count}개 조정, {disabled_count}개 비활성화")

        return {
            "success": True,
            "message": f"{adjusted_count}개 상품의 가격이 조정되었습니다.",
            "adjusted_count": adjusted_count,
            "disabled_count": disabled_count
        }

    except Exception as e:
        logger.error(f"[자동가격] 일괄 조정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
