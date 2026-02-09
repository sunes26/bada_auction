"""
상품 모니터링 백그라운드 작업 스케줄러

주기적으로 활성화된 모니터링 상품의 가격과 상태를 자동으로 체크합니다.
판매 상품의 소싱가도 함께 모니터링합니다.
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from database.db_wrapper import get_db
from monitor.product_monitor import ProductMonitor


# 스케줄러 인스턴스
scheduler = AsyncIOScheduler()

# 상품별 연속 가격 추출 실패 횟수 추적
price_fetch_fail_counts: dict[int, int] = {}

# 연속 실패 알림 임계값 (20회 = 30분 × 20 = 10시간 연속 실패 시 알림)
CONSECUTIVE_FAIL_THRESHOLD = 20


async def update_selling_products_sourcing_price():
    """
    판매 상품의 소싱가를 자동으로 업데이트하고 판매가를 자동 조정
    """
    print(f"\n[SELLING_MONITOR] ===== 판매 상품 소싱가 업데이트 시작: {datetime.now()} =====")

    try:
        db = get_db()

        # 동적 가격 조정 서비스 초기화
        from services.dynamic_pricing_service import DynamicPricingService
        pricing_service = DynamicPricingService(target_margin_rate=30.0)

        # 소싱 URL이 있는 활성 판매 상품 조회 (업데이트가 오래된 순서대로)
        with db.db_manager.get_session() as session:
            from database.models import MySellingProduct
            from sqlalchemy import and_

            query_results = session.query(MySellingProduct).filter(
                and_(
                    MySellingProduct.is_active == True,
                    MySellingProduct.sourcing_url.isnot(None),
                    MySellingProduct.sourcing_url != ''
                )
            ).order_by(MySellingProduct.updated_at.asc()).limit(20).all()

            products = []
            for row in query_results:
                products.append({
                    'id': row.id,
                    'product_name': row.product_name,
                    'sourcing_url': row.sourcing_url,
                    'sourcing_source': row.sourcing_source,
                    'sourcing_price': float(row.sourcing_price) if row.sourcing_price else None,
                    'selling_price': float(row.selling_price) if row.selling_price else None
                })

        if not products:
            print("[SELLING_MONITOR] 소싱 URL이 있는 활성 판매 상품이 없습니다")
            return

        print(f"[SELLING_MONITOR] 체크할 상품 수: {len(products)}개")

        monitor = ProductMonitor()
        success_count = 0
        updated_count = 0
        price_adjusted_count = 0
        error_count = 0

        for product in products:
            product_id = product['id']
            product_name = product['product_name']
            sourcing_url = product['sourcing_url']
            source = product['sourcing_source']
            old_price = product['sourcing_price']

            try:
                print(f"[SELLING_MONITOR] 체크 중: ID#{product_id} - {product_name[:40]}...")

                # 상품 가격 체크
                result = monitor.check_product_status(
                    product_url=sourcing_url,
                    source=source or 'unknown'
                )

                status = result.get('status', 'available')
                new_price = result.get('price')
                details = result.get('details', '')

                # 판매종료/품절/삭제 상태 감지 시 알림
                if status in ['discontinued', 'out_of_stock', 'unavailable']:
                    print(f"[ALERT] ID#{product_id}: 상품 상태 이상 - {status} ({details})")
                    try:
                        from notifications.notifier import send_notification
                        send_notification(
                            notification_type='product_unavailable',
                            message=f"소싱 상품 상태 이상: {product_name}",
                            product_id=product_id,
                            product_name=product_name,
                            sourcing_url=sourcing_url,
                            status=status,
                            details=details
                        )
                        print(f"[ALERT] ID#{product_id}: 상품 상태 알림 발송됨")
                    except Exception as notify_err:
                        print(f"[WARN] 알림 발송 실패: {notify_err}")

                if new_price and new_price > 0:
                    # 가격 추출 성공 - 실패 카운트 초기화
                    if product_id in price_fetch_fail_counts:
                        del price_fetch_fail_counts[product_id]

                    # 가격이 변경되었으면 업데이트
                    if old_price != new_price:
                        print(f"[SELLING_MONITOR] 가격 변동 감지: {old_price}원 → {new_price}원")

                        # 1. 소싱가 업데이트
                        db.update_selling_product(
                            product_id=product_id,
                            sourcing_price=new_price
                        )

                        # 2. 동적 가격 조정 (판매가 자동 조정)
                        try:
                            adjust_result = await pricing_service.auto_adjust_prices_on_sourcing_change(
                                product_id=product_id,
                                old_sourcing_price=old_price or 0,
                                new_sourcing_price=new_price
                            )

                            if adjust_result.get('success') and adjust_result.get('changed'):
                                price_adjusted_count += 1
                                print(f"[OK] 판매가 자동 조정: {adjust_result['old_selling_price']:,}원 → {adjust_result['new_selling_price']:,}원 (마진율 {adjust_result['new_margin_rate']}%)")
                            else:
                                print(f"[OK] 판매가 유지 (마진율 30% 이미 적용)")

                        except Exception as e:
                            print(f"[WARN] 판매가 자동 조정 실패: {str(e)}")
                            # 소싱가는 업데이트되었으므로 계속 진행

                        updated_count += 1
                        print(f"[OK] ID#{product_id}: 소싱가 업데이트 완료 ({old_price}원 → {new_price}원)")
                    else:
                        print(f"[OK] ID#{product_id}: 가격 변동 없음 ({new_price}원)")

                    success_count += 1
                else:
                    # 가격 추출 실패 - 실패 카운트 증가
                    price_fetch_fail_counts[product_id] = price_fetch_fail_counts.get(product_id, 0) + 1
                    fail_count = price_fetch_fail_counts[product_id]

                    print(f"[WARN] ID#{product_id}: 가격 정보를 가져올 수 없습니다 (연속 {fail_count}회 실패)")

                    # 연속 5회 실패 시 디스코드 알림
                    if fail_count == CONSECUTIVE_FAIL_THRESHOLD:
                        try:
                            from notifications.notifier import send_notification
                            send_notification(
                                notification_type='price_fetch_fail',
                                message=f"가격 추출 {fail_count}회 연속 실패: {product_name}",
                                product_id=product_id,
                                product_name=product_name,
                                sourcing_url=sourcing_url,
                                fail_count=fail_count
                            )
                            print(f"[ALERT] ID#{product_id}: 연속 {fail_count}회 실패 알림 발송됨")
                        except Exception as notify_err:
                            print(f"[WARN] 알림 발송 실패: {notify_err}")

                    error_count += 1

                await asyncio.sleep(3)

            except Exception as e:
                print(f"[ERROR] ID#{product_id} 체크 실패: {str(e)}")
                error_count += 1

        print(f"\n[SELLING_MONITOR] ===== 소싱가 업데이트 완료 =====")
        print(f"[SELLING_MONITOR] 성공: {success_count}건, 소싱가 업데이트: {updated_count}건, 판매가 조정: {price_adjusted_count}건, 실패: {error_count}건")
        print(f"[SELLING_MONITOR] ==========================================\n")

        if updated_count > 0:
            print(f"[SELLING_MONITOR] [알림] {updated_count}개 상품의 소싱가가 업데이트되었습니다!")
        if price_adjusted_count > 0:
            print(f"[SELLING_MONITOR] [알림] {price_adjusted_count}개 상품의 판매가가 자동 조정되었습니다! (마진율 30% 유지)")

    except Exception as e:
        print(f"[ERROR] 판매 상품 소싱가 업데이트 중 오류: {e}")
        import traceback
        traceback.print_exc()


async def auto_check_products_job():
    """활성화된 모든 모니터링 상품 자동 체크"""
    print(f"\n[MONITOR] ===== 자동 상품 체크 시작: {datetime.now()} =====")

    try:
        db = get_db()

        # 활성화된 모니터링 상품 목록 가져오기
        products = db.get_all_monitored_products(active_only=True)

        if not products:
            print("[MONITOR] 활성화된 모니터링 상품이 없습니다")
            return

        print(f"[MONITOR] 체크할 상품 수: {len(products)}개")

        # 모니터 인스턴스 생성
        monitor = ProductMonitor()

        success_count = 0
        error_count = 0

        # 각 상품 체크
        for product in products:
            product_id = product['id']
            product_name = product['product_name']
            product_url = product['product_url']
            source = product['source']

            try:
                print(f"[MONITOR] 체크 중: ID#{product_id} - {product_name[:40]}...")

                # 상품 상태 및 가격 체크
                result = monitor.check_product_status(
                    product_url=product_url,
                    source=source
                )

                # DB 업데이트
                db.update_product_status(
                    product_id=product_id,
                    new_status=result['status'],
                    new_price=result['price'],
                    details=result['details']
                )

                print(f"[OK] ID#{product_id}: {result['status']}, {result['price']}원")
                success_count += 1

                # 각 상품 체크 사이에 약간의 지연 (서버 부하 방지)
                await asyncio.sleep(2)

            except Exception as e:
                print(f"[ERROR] ID#{product_id} 체크 실패: {str(e)}")
                error_count += 1

                # 오류 상태로 업데이트
                try:
                    db.update_product_status(
                        product_id=product_id,
                        new_status='error',
                        details=f"체크 실패: {str(e)}"
                    )
                except:
                    pass

        print(f"\n[MONITOR] ===== 자동 체크 완료: 성공 {success_count}건, 실패 {error_count}건 =====\n")

        # 체크 완료 알림은 보내지 않음 (15분마다 알림이 너무 많아서)
        # 가격 변동, 역마진, 품절/재입고 등 중요한 이벤트만 알림 발송

    except Exception as e:
        print(f"[ERROR] 자동 상품 체크 중 오류: {e}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    """모니터링 스케줄러 시작 (자동가격조정만 활성화)"""
    try:
        db = get_db()

        # 판매 상품 소싱가 업데이트 주기: 30분
        selling_product_interval = 30

        # 모니터링 상품 자동 체크는 비활성화 (필요 없음)
        # scheduler.add_job(
        #     auto_check_products_job,
        #     trigger=IntervalTrigger(minutes=15),
        #     id="monitor_auto_check_products",
        #     ...
        # )

        # 판매 상품 소싱가 업데이트 작업 등록 (자동가격조정)
        scheduler.add_job(
            update_selling_products_sourcing_price,
            trigger=IntervalTrigger(minutes=selling_product_interval),
            id="monitor_selling_products_sourcing",
            name="판매 상품 소싱가 자동 업데이트 (자동가격조정)",
            replace_existing=True,
            misfire_grace_time=120
        )
        print(f"[MONITOR] 판매 상품 자동가격조정 작업 등록 ({selling_product_interval}분마다)")

        # 스케줄러 시작
        scheduler.start()
        print("[MONITOR] 스케줄러 시작 완료")

        # 판매 상품 소싱가 업데이트 (5초 후 실행)
        async def delayed_selling_update():
            await asyncio.sleep(5)
            await update_selling_products_sourcing_price()

        asyncio.create_task(delayed_selling_update())
        print("[MONITOR] 판매 상품 자동가격조정 작업 예약 (5초 후)")

    except Exception as e:
        print(f"[ERROR] 모니터링 스케줄러 시작 실패: {e}")
        import traceback
        traceback.print_exc()


def stop_scheduler():
    """모니터링 스케줄러 중지"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            print("[MONITOR] 스케줄러 중지 완료")
    except Exception as e:
        print(f"[ERROR] 모니터링 스케줄러 중지 실패: {e}")


def get_scheduler_status():
    """스케줄러 상태 조회"""
    try:
        if scheduler.running:
            jobs = scheduler.get_jobs()
            return {
                "running": True,
                "jobs": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": str(job.next_run_time) if job.next_run_time else None
                    }
                    for job in jobs
                ]
            }
        else:
            return {
                "running": False,
                "jobs": []
            }
    except Exception as e:
        print(f"[ERROR] 스케줄러 상태 조회 실패: {e}")
        return {
            "running": False,
            "jobs": [],
            "error": str(e)
        }
