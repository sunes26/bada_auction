"""
자동 재고 관리 시스템

품절 상품 자동 비활성화 및 재입고 알림 기능
"""

from database.db_wrapper import get_db
from notifications.notifier import send_notification
from typing import Optional


def check_and_update_inventory(
    product_id: int,
    old_status: str,
    new_status: str,
    product_name: Optional[str] = None,
    current_price: Optional[float] = None
):
    """
    상태 변경에 따른 자동 재고 관리

    Args:
        product_id: 상품 ID
        old_status: 이전 상태
        new_status: 새 상태
        product_name: 상품명 (선택)
        current_price: 현재 가격 (선택)
    """
    db = get_db()

    # 상품 정보 조회 (product_name이나 current_price가 없는 경우)
    if not product_name or current_price is None:
        product = db.get_monitored_product(product_id)
        if product:
            product_name = product_name or product.get('product_name', 'N/A')
            current_price = current_price if current_price is not None else product.get('current_price')

    # Case 1: 재고 있음 → 품절
    if old_status == 'available' and new_status == 'out_of_stock':
        auto_disable_out_of_stock(product_id, product_name)

    # Case 2: 품절 → 재입고
    elif old_status == 'out_of_stock' and new_status == 'available':
        handle_restock(product_id, product_name, current_price)

    # Case 3: 기타 상태 변경 (discontinued, unavailable 등)
    # 현재는 특별한 액션 없음


def auto_disable_out_of_stock(product_id: int, product_name: str):
    """
    품절 시 자동 비활성화

    Args:
        product_id: 상품 ID
        product_name: 상품명
    """
    db = get_db()

    try:
        # 현재 활성화 상태 확인
        product = db.get_monitored_product(product_id)
        if not product:
            print(f"[WARN] 상품 ID {product_id}를 찾을 수 없습니다")
            return

        is_active_before = product.get('is_active', True)

        # 이미 비활성화되어 있으면 스킵
        if not is_active_before:
            print(f"[INFO] 상품 '{product_name}'은 이미 비활성화되어 있습니다")
            return

        # 자동 비활성화
        db.update_product_active_status(product_id, False)

        # 로그 기록
        db.add_inventory_auto_log(
            product_id=product_id,
            action='auto_disable',
            old_status='available',
            new_status='out_of_stock',
            is_active_before=True,
            is_active_after=False
        )

        print(f"[INFO] 품절 감지: '{product_name}' 자동 비활성화 완료")

        # Slack/Discord 알림 발송
        try:
            send_notification(
                'inventory_out_of_stock',
                f"🚫 품절 감지: {product_name} (자동 비활성화됨)",
                product_name=product_name
            )
        except Exception as e:
            print(f"[WARN] 품절 알림 발송 실패: {e}")

    except Exception as e:
        print(f"[ERROR] 자동 비활성화 실패: {e}")


def handle_restock(
    product_id: int,
    product_name: str,
    current_price: Optional[float] = None
):
    """
    재입고 감지 시 알림 발송

    Args:
        product_id: 상품 ID
        product_name: 상품명
        current_price: 현재 가격 (선택)
    """
    db = get_db()

    try:
        # 로그 기록
        db.add_inventory_auto_log(
            product_id=product_id,
            action='restock_detected',
            old_status='out_of_stock',
            new_status='available',
            is_active_before=False,
            is_active_after=False  # 수동으로 재활성화 필요
        )

        print(f"[INFO] 재입고 감지: '{product_name}'")

        # 재입고 알림 발송
        try:
            send_notification(
                'inventory_restock',
                f"✅ 재입고 감지: {product_name}",
                product_name=product_name,
                current_price=current_price
            )
        except Exception as e:
            print(f"[WARN] 재입고 알림 발송 실패: {e}")

        # 선택적: 자동 재활성화 (현재는 수동으로 재활성화하도록 설정)
        # auto_enable_restock(product_id, product_name)

    except Exception as e:
        print(f"[ERROR] 재입고 처리 실패: {e}")


def auto_enable_restock(product_id: int, product_name: str):
    """
    재입고 시 자동 재활성화 (선택적 기능)

    Args:
        product_id: 상품 ID
        product_name: 상품명
    """
    db = get_db()

    try:
        # 현재 활성화 상태 확인
        product = db.get_monitored_product(product_id)
        if not product:
            print(f"[WARN] 상품 ID {product_id}를 찾을 수 없습니다")
            return

        is_active_before = product.get('is_active', False)

        # 이미 활성화되어 있으면 스킵
        if is_active_before:
            print(f"[INFO] 상품 '{product_name}'은 이미 활성화되어 있습니다")
            return

        # 자동 재활성화
        db.update_product_active_status(product_id, True)

        # 로그 기록
        db.add_inventory_auto_log(
            product_id=product_id,
            action='auto_enable',
            old_status='out_of_stock',
            new_status='available',
            is_active_before=False,
            is_active_after=True
        )

        print(f"[INFO] 재입고: '{product_name}' 자동 재활성화 완료")

    except Exception as e:
        print(f"[ERROR] 자동 재활성화 실패: {e}")
