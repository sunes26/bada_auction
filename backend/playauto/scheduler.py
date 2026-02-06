"""
플레이오토 백그라운드 작업 스케줄러

주기적 주문 수집 및 송장 업로드 자동화
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from database.db_wrapper import get_db
from .orders import fetch_and_sync_orders
from .tracking import auto_upload_tracking_from_local
from .products import PlayautoProductAPI


# 스케줄러 인스턴스
scheduler = AsyncIOScheduler()


async def auto_fetch_orders_job():
    """주문 자동 수집 작업 (30분마다)"""
    print(f"[PLAYAUTO] 주문 자동 수집 시작: {datetime.now()}")

    try:
        # 설정 확인
        db = get_db()
        enabled = db.get_playauto_setting("enabled") == "true"
        auto_sync_enabled = db.get_playauto_setting("auto_sync_enabled") == "true"

        if not enabled or not auto_sync_enabled:
            print("[PLAYAUTO] 자동 동기화가 비활성화되어 있습니다")
            return

        # 주문 수집 및 동기화
        result = await fetch_and_sync_orders()

        if result.get("success"):
            synced_count = result.get('synced_count', 0)
            print(f"[PLAYAUTO] 주문 수집 성공: {synced_count}개 동기화")

            # 새 주문이 있을 때만 Slack/Discord 알림 발송
            if synced_count > 0:
                try:
                    from notifications.notifier import send_notification
                    send_notification(
                        'order_sync',
                        f"📦 새 주문 {synced_count}건이 수집되었습니다",
                        market='전체',
                        collected_count=result.get('total', synced_count),
                        success_count=synced_count,
                        fail_count=0
                    )
                except Exception as e:
                    print(f"[WARN] 주문 동기화 알림 발송 실패: {e}")
        else:
            print(f"[PLAYAUTO] 주문 수집 실패: {result.get('message')}")

    except Exception as e:
        print(f"[ERROR] 주문 자동 수집 중 오류: {e}")


async def auto_upload_tracking_job():
    """송장 자동 업로드 작업 (매일 오전 9시)"""
    print(f"[PLAYAUTO] 송장 자동 업로드 시작: {datetime.now()}")

    try:
        # 설정 확인
        db = get_db()
        enabled = db.get_playauto_setting("enabled") == "true"

        if not enabled:
            print("[PLAYAUTO] 플레이오토가 비활성화되어 있습니다")
            return

        # 송장 업로드 (최근 7일)
        result = await auto_upload_tracking_from_local(days=7)

        if result.get("success"):
            print(f"[PLAYAUTO] 송장 업로드 성공: {result.get('success_count')}개 업로드")
        else:
            print(f"[PLAYAUTO] 송장 업로드 실패: {result.get('message')}")

    except Exception as e:
        print(f"[ERROR] 송장 자동 업로드 중 오류: {e}")


async def sync_marketplace_codes_job():
    """마켓별 상품번호 자동 동기화 작업 (1시간마다)"""
    print(f"[PLAYAUTO] 마켓 코드 동기화 시작: {datetime.now()}")

    try:
        # 설정 확인
        db = get_db()
        enabled = db.get_playauto_setting("enabled") == "true"

        if not enabled:
            print("[PLAYAUTO] 플레이오토가 비활성화되어 있습니다")
            return

        # 동기화 대상 상품 조회 (최근 24시간 동안 확인 안 된 상품)
        products = db.get_products_for_marketplace_sync(hours=24, limit=100)

        if not products:
            print("[PLAYAUTO] 동기화할 상품이 없습니다")
            return

        print(f"[PLAYAUTO] 동기화 대상 상품: {len(products)}개")

        # PlayAuto API 클라이언트
        api = PlayautoProductAPI()

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
            print("[PLAYAUTO] c_sale_cd가 있는 상품이 없습니다")
            return

        success_count = 0
        error_count = 0

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

                    for item in items:
                        shop_cd = item.get("shop_cd")
                        shop_name = item.get("shop_name", "")
                        shop_sale_no = item.get("shop_sale_no")

                        # Z000(마스터)은 shop_sale_no가 없으므로 스킵
                        if shop_cd and shop_cd != "Z000" and shop_sale_no:
                            db.upsert_marketplace_code(
                                product_id=product_id,
                                shop_cd=shop_cd,
                                shop_name=shop_name,
                                shop_sale_no=shop_sale_no,
                                transmitted_at=datetime.now()
                            )
                            print(f"[OK] 상품 {product_id}: {shop_name} ({shop_cd}) -> {shop_sale_no}")
                            success_count += 1

        except Exception as e:
            error_count += 1
            print(f"[ERROR] API 조회 실패: {e}")

        print(f"[PLAYAUTO] 마켓 코드 동기화 완료: 성공 {success_count}개, 실패 {error_count}개")

    except Exception as e:
        print(f"[ERROR] 마켓 코드 동기화 중 오류: {e}")


def start_scheduler():
    """스케줄러 시작"""
    try:
        # 설정 확인
        db = get_db()
        import os

        # ===== 무조건 활성화 (디버깅용) =====
        # TODO: 나중에 환경 변수나 DB 설정으로 제어 가능하도록 수정
        enabled = True
        auto_sync_enabled = True
        print("[PLAYAUTO] 강제 활성화 모드 (무조건 시작)")
        # ===================================

        auto_sync_interval = int(db.get_playauto_setting("auto_sync_interval") or "30")

        if not enabled:
            print("[PLAYAUTO] 플레이오토가 비활성화되어 있어 스케줄러를 시작하지 않습니다")
            return

        # 주문 자동 수집 작업 등록 (설정된 주기마다)
        if auto_sync_enabled:
            scheduler.add_job(
                auto_fetch_orders_job,
                trigger=IntervalTrigger(minutes=auto_sync_interval),
                id="playauto_auto_fetch_orders",
                name="플레이오토 주문 자동 수집",
                replace_existing=True,
                misfire_grace_time=60
            )
            print(f"[PLAYAUTO] 주문 자동 수집 작업 등록 ({auto_sync_interval}분마다)")

        # 송장 자동 업로드 작업 등록 (매일 오전 9시)
        scheduler.add_job(
            auto_upload_tracking_job,
            trigger=CronTrigger(hour=9, minute=0),
            id="playauto_auto_upload_tracking",
            name="플레이오토 송장 자동 업로드",
            replace_existing=True,
            misfire_grace_time=300
        )
        print("[PLAYAUTO] 송장 자동 업로드 작업 등록 (매일 오전 9시)")

        # 마켓 코드 동기화 작업 등록 (1시간마다)
        scheduler.add_job(
            sync_marketplace_codes_job,
            trigger=IntervalTrigger(hours=1),
            id="playauto_sync_marketplace_codes",
            name="플레이오토 마켓 코드 동기화",
            replace_existing=True,
            misfire_grace_time=300
        )
        print("[PLAYAUTO] 마켓 코드 동기화 작업 등록 (1시간마다)")

        # 스케줄러 시작
        scheduler.start()
        print("[PLAYAUTO] 스케줄러 시작 완료")

    except Exception as e:
        print(f"[ERROR] 스케줄러 시작 실패: {e}")


def stop_scheduler():
    """스케줄러 중지"""
    try:
        scheduler.shutdown()
        print("[PLAYAUTO] 스케줄러 중지 완료")
    except Exception as e:
        print(f"[ERROR] 스케줄러 중지 실패: {e}")


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
