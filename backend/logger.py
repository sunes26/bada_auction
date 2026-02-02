"""
로깅 시스템 설정

애플리케이션 전체에서 사용할 로거 설정
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 환경 변수 체크 (production vs development)
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# 로그 포맷
LOG_FORMAT = '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 메인 로거 설정
logger = logging.getLogger("onbaek-ai")
logger.setLevel(logging.INFO)

# 기존 핸들러 제거 (중복 방지)
if logger.hasHandlers():
    logger.handlers.clear()

# 콘솔 핸들러 (stdout) - 모든 환경에서 사용
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 에러 핸들러 (stderr) - 모든 환경에서 사용
error_console_handler = logging.StreamHandler(sys.stderr)
error_console_handler.setLevel(logging.ERROR)
error_console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
error_console_handler.setFormatter(error_console_formatter)
logger.addHandler(error_console_handler)

# 로컬 개발 환경에서만 파일 핸들러 사용
if ENVIRONMENT != 'production':
    try:
        # logs 디렉토리 생성 (개발 환경에서만)
        LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(LOGS_DIR, exist_ok=True)

        # 로그 파일 경로
        LOG_FILE = os.path.join(LOGS_DIR, 'app.log')
        ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'error.log')

        # 파일 핸들러 (INFO 이상, 최대 10MB, 5개 백업)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 에러 로그 파일 핸들러 (ERROR 이상만)
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)

        logger.info(f"로컬 개발 환경: 파일 로깅 활성화 ({LOG_FILE})")
    except Exception as e:
        # 파일 생성 실패시 stdout만 사용 (에러 무시)
        logger.warning(f"파일 핸들러 생성 실패 (stdout만 사용): {e}")
else:
    logger.info("프로덕션 환경: stdout/stderr 로깅 사용 (Railway 자동 수집)")


def get_logger(name: str = None):
    """
    로거 인스턴스 반환

    Args:
        name: 로거 이름 (모듈명 등)

    Returns:
        logging.Logger: 로거 인스턴스
    """
    if name:
        return logging.getLogger(f"onbaek-ai.{name}")
    return logger


# 사용 예시 함수
def test_logging():
    """로깅 테스트"""
    logger.debug("디버그 메시지 (출력 안됨)")
    logger.info("정보 메시지")
    logger.warning("경고 메시지")
    logger.error("에러 메시지")
    logger.critical("치명적 오류 메시지")


if __name__ == "__main__":
    # 테스트 실행
    print(f"환경: {ENVIRONMENT}")
    if ENVIRONMENT != 'production':
        print(f"로그 파일 경로: {LOG_FILE}")
        print(f"에러 로그 파일 경로: {ERROR_LOG_FILE}")
    else:
        print("프로덕션 환경: stdout/stderr만 사용")
    test_logging()
