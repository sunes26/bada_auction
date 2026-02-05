"""
ol_shop_no를 ol_shop_no_gmk와 ol_shop_no_smart로 분리하는 마이그레이션

문제:
- 플레이오토에 상품을 2번 등록함 (GMK용, 스마트스토어용)
- 각 등록마다 다른 ol_shop_no를 반환함
- 하지만 DB에는 ol_shop_no 하나만 저장 가능
- 마켓 코드 동기화 시 잘못된 ol_shop_no로 조회하면 실패

해결:
- ol_shop_no를 ol_shop_no_gmk, ol_shop_no_smart로 분리
- c_sale_cd와 동일한 구조로 변경
"""

import os
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import get_database_manager
from logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


def migrate_split_ol_shop_no():
    """ol_shop_no를 GMK/스마트스토어용으로 분리"""

    db_manager = get_database_manager()

    try:
        with db_manager.get_session() as session:
            logger.info("[마이그레이션] ol_shop_no 분리 시작...")

            # 1. 새 컬럼 추가
            if db_manager.is_sqlite:
                # SQLite
                session.execute(text("ALTER TABLE my_selling_products ADD COLUMN ol_shop_no_gmk TEXT"))
                session.execute(text("ALTER TABLE my_selling_products ADD COLUMN ol_shop_no_smart TEXT"))
            else:
                # PostgreSQL
                session.execute(text("""
                    ALTER TABLE my_selling_products
                    ADD COLUMN IF NOT EXISTS ol_shop_no_gmk TEXT,
                    ADD COLUMN IF NOT EXISTS ol_shop_no_smart TEXT
                """))

            session.commit()
            logger.info("[마이그레이션] ✓ 새 컬럼 추가 완료 (ol_shop_no_gmk, ol_shop_no_smart)")

            # 2. 기존 데이터 마이그레이션
            # ol_shop_no가 있는 경우, c_sale_cd 관계를 보고 어느 채널인지 추론
            # - c_sale_cd_gmk가 있으면 ol_shop_no → ol_shop_no_gmk
            # - c_sale_cd_smart가 있으면 ol_shop_no → ol_shop_no_smart
            # - 둘 다 있으면 일단 gmk로 이동 (정확한 매핑은 재등록 필요)

            result = session.execute(text("""
                UPDATE my_selling_products
                SET ol_shop_no_gmk = ol_shop_no
                WHERE ol_shop_no IS NOT NULL
                  AND c_sale_cd_gmk IS NOT NULL
            """))
            gmk_count = result.rowcount

            result = session.execute(text("""
                UPDATE my_selling_products
                SET ol_shop_no_smart = ol_shop_no
                WHERE ol_shop_no IS NOT NULL
                  AND c_sale_cd_gmk IS NULL
                  AND c_sale_cd_smart IS NOT NULL
            """))
            smart_count = result.rowcount

            session.commit()

            logger.info(f"[마이그레이션] ✓ 기존 데이터 마이그레이션 완료")
            logger.info(f"[마이그레이션]   - GMK: {gmk_count}개")
            logger.info(f"[마이그레이션]   - 스마트스토어: {smart_count}개")

            # 3. 기존 ol_shop_no 컬럼은 유지 (하위 호환성)
            logger.info("[마이그레이션] ℹ️  기존 ol_shop_no 컬럼은 하위 호환성을 위해 유지됩니다")

            logger.info("[마이그레이션] ✅ 마이그레이션 완료!")
            logger.info("[마이그레이션] 다음 단계:")
            logger.info("[마이그레이션]   1. 상품을 재등록하여 정확한 ol_shop_no_gmk, ol_shop_no_smart 값 수집")
            logger.info("[마이그레이션]   2. 마켓 코드 동기화 테스트")

    except Exception as e:
        logger.error(f"[마이그레이션] ✗ 마이그레이션 실패: {e}")
        raise


if __name__ == "__main__":
    migrate_split_ol_shop_no()
