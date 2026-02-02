"""
자동 송장 업로드 서비스

로컬 DB에서 송장이 등록된 주문을 찾아 플레이오토로 자동 업로드합니다.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from database.db_wrapper import get_db
from playauto.tracking import PlayautoTrackingAPI
import json


class TrackingUploadService:
    """자동 송장 업로드 서비스"""

    def __init__(self):
        self.db = get_db()
        self.tracking_api = PlayautoTrackingAPI()

    async def execute_upload(
        self,
        job_type: str = 'manual',
        retry_count: int = 3,
        notify_discord: bool = False,
        notify_slack: bool = False
    ) -> Dict:
        """
        송장 자동 업로드 실행

        Args:
            job_type: 'scheduled' 또는 'manual'
            retry_count: 재시도 횟수
            notify_discord: Discord 알림 여부
            notify_slack: Slack 알림 여부

        Returns:
            작업 결과
        """
        # 1. 작업 생성
        job_id = self._create_job(job_type)

        try:
            # 2. 업로드할 주문 조회 (송장이 등록되었지만 아직 플레이오토에 업로드되지 않은 주문)
            orders = self._get_pending_orders()

            if not orders:
                self._update_job_status(
                    job_id,
                    status='completed',
                    total_count=0,
                    success_count=0,
                    failed_count=0,
                    progress_percent=100
                )
                return {
                    'success': True,
                    'job_id': job_id,
                    'total_count': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'message': '업로드할 송장이 없습니다'
                }

            # 3. 작업 상태 업데이트
            self._update_job_status(
                job_id,
                status='running',
                total_count=len(orders)
            )

            # 4. 각 주문별로 업로드 시도
            success_count = 0
            failed_count = 0

            for idx, order in enumerate(orders):
                try:
                    # 개별 송장 업로드
                    result = await self._upload_single_tracking(
                        job_id=job_id,
                        order=order,
                        retry_count=retry_count
                    )

                    if result['success']:
                        success_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    print(f"[ERROR] 주문 {order.get('order_number')} 업로드 실패: {e}")
                    failed_count += 1
                    self._log_upload_detail(
                        job_id=job_id,
                        order=order,
                        status='failed',
                        error_message=str(e)
                    )

                # 진행률 업데이트
                progress = ((idx + 1) / len(orders)) * 100
                self._update_job_progress(job_id, progress)

            # 5. 작업 완료
            self._update_job_status(
                job_id,
                status='completed',
                total_count=len(orders),
                success_count=success_count,
                failed_count=failed_count,
                progress_percent=100
            )

            # 6. 알림 발송
            if notify_discord or notify_slack:
                await self._send_notifications(
                    job_id=job_id,
                    total_count=len(orders),
                    success_count=success_count,
                    failed_count=failed_count,
                    notify_discord=notify_discord,
                    notify_slack=notify_slack
                )

            return {
                'success': True,
                'job_id': job_id,
                'total_count': len(orders),
                'success_count': success_count,
                'failed_count': failed_count,
                'message': f'송장 업로드 완료 (성공: {success_count}, 실패: {failed_count})'
            }

        except Exception as e:
            print(f"[ERROR] 송장 업로드 작업 실패: {e}")
            self._update_job_status(
                job_id,
                status='failed',
                error_message=str(e)
            )
            raise

    async def _upload_single_tracking(
        self,
        job_id: int,
        order: Dict,
        retry_count: int = 3
    ) -> Dict:
        """
        개별 송장 업로드 (재시도 포함)

        Args:
            job_id: 작업 ID
            order: 주문 정보
            retry_count: 재시도 횟수

        Returns:
            업로드 결과
        """
        for attempt in range(retry_count + 1):
            try:
                # 플레이오토 API로 송장 업로드
                tracking_data = [{
                    'order_no': order.get('order_number'),
                    'carrier_code': order.get('carrier_code', 'UNKNOWN'),
                    'tracking_number': order.get('tracking_number')
                }]

                result = await self.tracking_api.upload_tracking(tracking_data)

                if result.get('success'):
                    # 성공 로그
                    self._log_upload_detail(
                        job_id=job_id,
                        order=order,
                        status='success',
                        retry_attempt=attempt
                    )

                    # 로컬 DB에 업로드 완료 표시
                    self._mark_order_uploaded(order.get('id'))

                    return {'success': True}
                else:
                    # 실패했지만 재시도
                    if attempt < retry_count:
                        print(f"[WARN] 주문 {order.get('order_number')} 업로드 실패, 재시도 {attempt + 1}/{retry_count}")
                        await asyncio.sleep(2 ** attempt)  # 지수 백오프
                        continue
                    else:
                        # 최종 실패
                        error_msg = result.get('message', '알 수 없는 오류')
                        self._log_upload_detail(
                            job_id=job_id,
                            order=order,
                            status='failed',
                            retry_attempt=attempt,
                            error_message=error_msg
                        )
                        return {'success': False, 'error': error_msg}

            except Exception as e:
                if attempt < retry_count:
                    print(f"[WARN] 주문 {order.get('order_number')} 업로드 중 오류, 재시도 {attempt + 1}/{retry_count}: {e}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # 최종 실패
                    self._log_upload_detail(
                        job_id=job_id,
                        order=order,
                        status='failed',
                        retry_attempt=attempt,
                        error_message=str(e)
                    )
                    return {'success': False, 'error': str(e)}

        return {'success': False, 'error': '최대 재시도 횟수 초과'}

    def _get_pending_orders(self) -> List[Dict]:
        """
        업로드 대기 중인 주문 조회
        (송장번호가 입력되었지만 아직 플레이오토에 업로드되지 않은 주문)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT
                    o.id,
                    o.order_number,
                    oi.tracking_number,
                    o.customer_name
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE oi.tracking_number IS NOT NULL
                  AND oi.tracking_number != ''
                  AND (o.tracking_uploaded_at IS NULL OR o.synced_to_playauto = 0)
                  AND o.order_status NOT IN ('취소', '반품', '교환', 'cancelled', 'failed')
                ORDER BY o.created_at ASC
            """)

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            orders = []
            for row in rows:
                order = dict(zip(columns, row))
                orders.append(order)

            return orders

    def _create_job(self, job_type: str) -> int:
        """작업 생성"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tracking_upload_jobs (job_type, status)
                VALUES (?, 'pending')
            """, (job_type,))
            conn.commit()
            return cursor.lastrowid

    def _update_job_status(
        self,
        job_id: int,
        status: str,
        total_count: int = None,
        success_count: int = None,
        failed_count: int = None,
        progress_percent: float = None,
        error_message: str = None
    ):
        """작업 상태 업데이트"""
        updates = ['status = ?']
        params = [status]

        if total_count is not None:
            updates.append('total_count = ?')
            params.append(total_count)

        if success_count is not None:
            updates.append('success_count = ?')
            params.append(success_count)

        if failed_count is not None:
            updates.append('failed_count = ?')
            params.append(failed_count)

        if progress_percent is not None:
            updates.append('progress_percent = ?')
            params.append(progress_percent)

        if error_message is not None:
            updates.append('error_message = ?')
            params.append(error_message)

        if status == 'completed' or status == 'failed':
            updates.append('completed_at = CURRENT_TIMESTAMP')

        params.append(job_id)

        query = f"""
            UPDATE tracking_upload_jobs
            SET {', '.join(updates)}
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def _update_job_progress(self, job_id: int, progress: float):
        """진행률만 업데이트"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tracking_upload_jobs
                SET progress_percent = ?
                WHERE id = ?
            """, (progress, job_id))
            conn.commit()

    def _log_upload_detail(
        self,
        job_id: int,
        order: Dict,
        status: str,
        retry_attempt: int = 0,
        error_message: str = None
    ):
        """개별 송장 업로드 로그"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tracking_upload_details
                (job_id, order_id, order_no, carrier_code, tracking_number, status, retry_attempt, error_message, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                job_id,
                order.get('id'),
                order.get('order_number'),
                order.get('carrier_code', 'UNKNOWN'),
                order.get('tracking_number'),
                status,
                retry_attempt,
                error_message
            ))
            conn.commit()

    def _mark_order_uploaded(self, order_id: int):
        """주문을 업로드 완료로 표시"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orders
                SET tracking_uploaded_at = CURRENT_TIMESTAMP,
                    synced_to_playauto = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (order_id,))
            conn.commit()

    async def _send_notifications(
        self,
        job_id: int,
        total_count: int,
        success_count: int,
        failed_count: int,
        notify_discord: bool,
        notify_slack: bool
    ):
        """알림 발송"""
        try:
            # 스케줄러 설정에서 웹훅 URL 가져오기
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT discord_webhook, slack_webhook
                    FROM tracking_upload_scheduler
                    WHERE id = 1
                """)
                row = cursor.fetchone()

                if not row:
                    return

                discord_webhook, slack_webhook = row

            # 알림 메시지 생성
            message = f"""
📦 송장 자동 업로드 완료!

총 {total_count}건
✅ 성공: {success_count}건
❌ 실패: {failed_count}건

작업 ID: #{job_id}
완료 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            # Discord 알림
            if notify_discord and discord_webhook:
                await self._send_discord_notification(discord_webhook, message)

            # Slack 알림
            if notify_slack and slack_webhook:
                await self._send_slack_notification(slack_webhook, message)

        except Exception as e:
            print(f"[ERROR] 알림 발송 실패: {e}")

    async def _send_discord_notification(self, webhook_url: str, message: str):
        """Discord 웹훅으로 알림 발송"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'content': message
                }
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 204:
                        print("[OK] Discord 알림 발송 성공")
                    else:
                        print(f"[WARN] Discord 알림 발송 실패: {response.status}")
        except Exception as e:
            print(f"[ERROR] Discord 알림 발송 중 오류: {e}")

    async def _send_slack_notification(self, webhook_url: str, message: str):
        """Slack 웹훅으로 알림 발송"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'text': message
                }
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        print("[OK] Slack 알림 발송 성공")
                    else:
                        print(f"[WARN] Slack 알림 발송 실패: {response.status}")
        except Exception as e:
            print(f"[ERROR] Slack 알림 발송 중 오류: {e}")

    def get_job_status(self, job_id: int) -> Optional[Dict]:
        """작업 상태 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    job_type,
                    status,
                    total_count,
                    success_count,
                    failed_count,
                    retry_count,
                    progress_percent,
                    error_message,
                    started_at,
                    completed_at
                FROM tracking_upload_jobs
                WHERE id = ?
            """, (job_id,))

            row = cursor.fetchone()
            if not row:
                return None

            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

    def get_recent_jobs(self, limit: int = 10) -> List[Dict]:
        """최근 작업 목록 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    job_type,
                    status,
                    total_count,
                    success_count,
                    failed_count,
                    progress_percent,
                    started_at,
                    completed_at
                FROM tracking_upload_jobs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            jobs = []
            for row in rows:
                job = dict(zip(columns, row))
                jobs.append(job)

            return jobs
