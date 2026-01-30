"""
기존 평문 비밀번호를 암호화된 형태로 마이그레이션

소싱처 계정 비밀번호를 Fernet 암호화로 보호합니다.
"""
import sqlite3
from playauto.crypto import get_crypto
from logger import get_logger

logger = get_logger(__name__)


def is_encrypted(password: str) -> bool:
    """
    비밀번호가 이미 암호화되어 있는지 확인

    Fernet 암호화된 문자열은 'gAAAAA'로 시작합니다.
    """
    return password.startswith('gAAAAA') if password else False


def migrate_passwords(db_path: str = "monitoring.db"):
    """평문 비밀번호를 암호화된 형태로 변환"""
    crypto = get_crypto()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 모든 계정 조회
        cursor.execute("SELECT id, source, account_id, account_password FROM sourcing_accounts")
        accounts = cursor.fetchall()

        if not accounts:
            logger.info("소싱처 계정이 없습니다. 마이그레이션 불필요.")
            return

        migrated = 0
        skipped = 0

        for account in accounts:
            account_id = account['id']
            source = account['source']
            username = account['account_id']
            plain_password = account['account_password']

            if not plain_password:
                logger.warning(f"계정 ID {account_id} ({source}): 비밀번호가 비어있음 - 건너뜀")
                skipped += 1
                continue

            # 이미 암호화된 것인지 확인
            if is_encrypted(plain_password):
                logger.info(f"계정 ID {account_id} ({source}): 이미 암호화됨 - 건너뜀")
                skipped += 1
                continue

            # 평문 비밀번호 → 암호화
            try:
                encrypted_password = crypto.encrypt(plain_password)

                cursor.execute("""
                    UPDATE sourcing_accounts
                    SET account_password = ?
                    WHERE id = ?
                """, (encrypted_password, account_id))

                migrated += 1
                logger.info(f"✅ 계정 ID {account_id} ({source}, {username}) 비밀번호 암호화 완료")

            except Exception as e:
                logger.error(f"❌ 계정 ID {account_id} ({source}) 암호화 실패: {e}")

        conn.commit()

        logger.info(f"""
========================================
마이그레이션 완료
========================================
총 계정 수: {len(accounts)}
암호화 완료: {migrated}
건너뜀: {skipped}
========================================
        """)

        if migrated > 0:
            logger.info("✅ 비밀번호 암호화가 완료되었습니다. 이제 안전하게 저장됩니다.")

    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {e}", exc_info=True)
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    print("""
╔══════════════════════════════════════════════════════════╗
║  소싱처 계정 비밀번호 암호화 마이그레이션                ║
╚══════════════════════════════════════════════════════════╝

평문으로 저장된 비밀번호를 Fernet 암호화로 보호합니다.

⚠️  주의사항:
1. 백업을 먼저 수행하는 것을 권장합니다.
2. ENCRYPTION_KEY 환경변수가 설정되어 있어야 합니다.
3. 마이그레이션 후에는 복구할 수 없습니다.

계속하시겠습니까? (y/N): """, end="")

    response = input().strip().lower()

    if response != 'y':
        print("❌ 마이그레이션이 취소되었습니다.")
        sys.exit(0)

    print("\n마이그레이션 시작...\n")

    try:
        migrate_passwords()
        print("\n✅ 마이그레이션이 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        sys.exit(1)
