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


async def update_selling_products_sourcing_price():
    """
    판매 상품의 소싱가를 자동으로 업데이트하고 판매가를 자동 조정
    """
    print(f"\n[SELLING_MONITOR] ===== 판매 상품 소싱가 업데이트 시작: {datetime.now()} =====")

    try:
        db = get_db()

        # 동적 가격 조정 서비스 초기화
        from services.dynamic_pricing_service import DynamicPricingService
        pricing_service = DynamicPricingService(target_margin_rate=50.0)

        # 소싱 URL이 있는 활성 판매 상품 조회 (업데이트가 오래된 순서대로)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    product_name,
                    sourcing_url,
                    sourcing_source,
                    sourcing_price,
                    selling_price
                FROM my_selling_products
                WHERE is_active = 1
                  AND sourcing_url IS NOT NULL
                  AND sourcing_url != ''
                ORDER BY updated_at ASC
                LIMIT 20
            """)

            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row[0],
                    'product_name': row[1],
                    'sourcing_url': row[2],
                    'sourcing_source': row[3],
                    'sourcing_price': row[4],
                    'selling_price': row[5]
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

                new_price = result.get('price')

                if new_price and new_price > 0:
                    # 가격이 변경되었으면 업데이트
                    if old_price != new_price:
                        print(f"[SELLING_MONITOR] 가격 변동 감지: {old_price}원 → {new_price}원")

                        # 1. 소싱가 업데이트
                        with db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE my_selling_products
                                SET sourcing_price = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (new_price, product_id))
                            conn.commit()

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
                                print(f"[OK] 판매가 유지 (마진율 50% 이미 적용)")

                        except Exception as e:
                            print(f"[WARN] 판매가 자동 조정 실패: {str(e)}")
                            # 소싱가는 업데이트되었으므로 계속 진행

                        updated_count += 1
                        print(f"[OK] ID#{product_id}: 소싱가 업데이트 완료 ({old_price}원 → {new_price}원)")
                    else:
                        print(f"[OK] ID#{product_id}: 가격 변동 없음 ({new_price}원)")

                    success_count += 1
                else:
                    print(f"[WARN] ID#{product_id}: 가격 정보를 가져올 수 없습니다")
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
            print(f"[SELLING_MONITOR] [알림] {price_adjusted_count}개 상품의 판매가가 자동 조정되었습니다! (마진율 50% 유지)")

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
    """모니터링 스케줄러 시작"""
    try:
        db = get_db()

        # 모니터링 상품 체크 주기: 15분
        monitor_interval = 15

        # 판매 상품 소싱가 업데이트 주기: 30분 (좀 더 긴 주기)
        selling_product_interval = 30

        # 1. 모니터링 상품 자동 체크 작업 등록
        scheduler.add_job(
            auto_check_products_job,
            trigger=IntervalTrigger(minutes=monitor_interval),
            id="monitor_auto_check_products",
            name="모니터링 상품 자동 체크",
            replace_existing=True,
            misfire_grace_time=60
        )
        print(f"[MONITOR] 모니터링 상품 체크 작업 등록 ({monitor_interval}분마다)")

        # 2. 판매 상품 소싱가 업데이트 작업 등록
        scheduler.add_job(
            update_selling_products_sourcing_price,
            trigger=IntervalTrigger(minutes=selling_product_interval),
            id="monitor_selling_products_sourcing",
            name="판매 상품 소싱가 자동 업데이트",
            replace_existing=True,
            misfire_grace_time=120
        )
        print(f"[MONITOR] 판매 상품 소싱가 업데이트 작업 등록 ({selling_product_interval}분마다)")

        # 스케줄러 시작
        scheduler.start()
        print("[MONITOR] 스케줄러 시작 완료")

        # 즉시 첫 번째 체크 실행 (백그라운드)
        # 모니터링 상품이 있으면 실행
        products = db.get_all_monitored_products(active_only=True)
        if products:
            asyncio.create_task(auto_check_products_job())
            print("[MONITOR] 모니터링 상품 첫 번째 체크 작업 시작")

        # 판매 상품 소싱가 업데이트 (5초 후 실행)
        async def delayed_selling_update():
            await asyncio.sleep(5)
            await update_selling_products_sourcing_price()

        asyncio.create_task(delayed_selling_update())
        print("[MONITOR] 판매 상품 소싱가 업데이트 작업 예약 (5초 후)")

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
