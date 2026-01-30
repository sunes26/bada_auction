"""
Discord 알림 테스트 스크립트

각 알림 타입별로 테스트 메시지를 Discord로 전송합니다.
"""

import time
import sys
import io
from notifications.notifier import send_notification

# Windows 콘솔 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("Discord 알림 테스트 시작")
print("=" * 60)

# 1. 가격 변동 알림 (인상)
print("\n[1/8] 가격 인상 알림 전송 중...")
send_notification(
    'price_change',
    '가격 변동 테스트',
    product_name='[테스트] CJ 비비고 왕교자 만두 1kg',
    old_price=15900,
    new_price=18900,
    change_percent=18.87
)
print("OK 전송 완료")
time.sleep(2)

# 2. 가격 변동 알림 (인하)
print("\n[2/8] 가격 인하 알림 전송 중...")
send_notification(
    'price_change',
    '가격 변동 테스트',
    product_name='[테스트] 풀무원 탱탱쫄면 4입',
    old_price=12900,
    new_price=9900,
    change_percent=-23.26
)
print("OK 전송 완료")
time.sleep(2)

# 3. 역마진 경고
print("\n[3/8] 역마진 경고 알림 전송 중...")
send_notification(
    'margin_alert',
    '역마진 발생 테스트',
    product_name='[테스트] 오뚜기 진라면 5입',
    sourcing_price=8900,
    selling_price=7500,
    loss=1400
)
print("OK 전송 완료")
time.sleep(2)

# 4. 주문 동기화 완료
print("\n[4/8] 주문 동기화 완료 알림 전송 중...")
send_notification(
    'order_sync',
    '주문 동기화 테스트',
    market='플레이오토',
    collected_count=25,
    success_count=23,
    fail_count=2
)
print("OK 전송 완료")
time.sleep(2)

# 5. 품절 감지
print("\n[5/8] 품절 감지 알림 전송 중...")
send_notification(
    'inventory_out_of_stock',
    '품절 감지 테스트',
    product_name='[테스트] 농심 신라면 5입'
)
print("OK 전송 완료")
time.sleep(2)

# 6. 재입고 감지
print("\n[6/8] 재입고 감지 알림 전송 중...")
send_notification(
    'inventory_restock',
    '재입고 감지 테스트',
    product_name='[테스트] 농심 신라면 5입',
    current_price=4200
)
print("OK 전송 완료")
time.sleep(2)

# 7. RPA 자동 발주 성공
print("\n[7/8] RPA 발주 성공 알림 전송 중...")
send_notification(
    'rpa_success',
    'RPA 성공 테스트',
    order_number='TEST-20260124-001',
    source='11st',
    execution_time=12.5,
    product_name='[테스트] CJ 햇반 210g X 24입'
)
print("OK 전송 완료")
time.sleep(2)

# 8. RPA 자동 발주 실패
print("\n[8/8] RPA 발주 실패 알림 전송 중...")
send_notification(
    'rpa_failure',
    'RPA 실패 테스트',
    order_number='TEST-20260124-002',
    source='ssg',
    execution_time=8.3,
    product_name='[테스트] 동원 양반김 10봉',
    error='재고 부족으로 주문을 완료할 수 없습니다.'
)
print("OK 전송 완료")

print("\n" + "=" * 60)
print("모든 테스트 알림 전송 완료!")
print("Discord 채널을 확인하세요.")
print("=" * 60)
