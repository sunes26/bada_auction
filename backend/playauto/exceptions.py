"""
플레이오토 API 커스텀 예외

API 호출 중 발생할 수 있는 다양한 예외 정의
"""


class PlayautoAPIError(Exception):
    """플레이오토 API 기본 예외"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        """
        Args:
            message: 에러 메시지
            status_code: HTTP 상태 코드
            response_data: API 응답 데이터
        """
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class PlayautoAuthError(PlayautoAPIError):
    """인증 실패 예외 (401, 403)"""

    def __init__(self, message: str = "플레이오토 API 인증 실패", status_code: int = 401, response_data: dict = None):
        super().__init__(message, status_code, response_data)


class PlayautoRateLimitError(PlayautoAPIError):
    """API 호출 제한 초과 예외 (429)"""

    def __init__(
        self,
        message: str = "API 호출 제한 초과",
        status_code: int = 429,
        response_data: dict = None,
        retry_after: int = None
    ):
        """
        Args:
            message: 에러 메시지
            status_code: HTTP 상태 코드
            response_data: API 응답 데이터
            retry_after: 재시도 가능 시간 (초)
        """
        super().__init__(message, status_code, response_data)
        self.retry_after = retry_after

    def __str__(self):
        if self.retry_after:
            return f"{self.message} (재시도 가능: {self.retry_after}초 후)"
        return self.message


class PlayautoDataError(PlayautoAPIError):
    """데이터 형식 오류 예외 (400)"""

    def __init__(
        self,
        message: str = "데이터 형식 오류",
        status_code: int = 400,
        response_data: dict = None,
        validation_errors: list = None
    ):
        """
        Args:
            message: 에러 메시지
            status_code: HTTP 상태 코드
            response_data: API 응답 데이터
            validation_errors: 유효성 검사 오류 목록
        """
        super().__init__(message, status_code, response_data)
        self.validation_errors = validation_errors or []

    def __str__(self):
        if self.validation_errors:
            errors = ", ".join(self.validation_errors)
            return f"{self.message}: {errors}"
        return self.message


class PlayautoNotFoundError(PlayautoAPIError):
    """리소스를 찾을 수 없음 예외 (404)"""

    def __init__(self, message: str = "리소스를 찾을 수 없습니다", status_code: int = 404, response_data: dict = None):
        super().__init__(message, status_code, response_data)


class PlayautoServerError(PlayautoAPIError):
    """서버 오류 예외 (500, 502, 503)"""

    def __init__(
        self,
        message: str = "플레이오토 서버 오류",
        status_code: int = 500,
        response_data: dict = None
    ):
        super().__init__(message, status_code, response_data)


class PlayautoNetworkError(PlayautoAPIError):
    """네트워크 연결 오류 예외"""

    def __init__(self, message: str = "네트워크 연결 실패", original_error: Exception = None):
        super().__init__(message, status_code=None)
        self.original_error = original_error

    def __str__(self):
        if self.original_error:
            return f"{self.message}: {str(self.original_error)}"
        return self.message


class PlayautoTimeoutError(PlayautoAPIError):
    """요청 타임아웃 예외"""

    def __init__(self, message: str = "API 요청 타임아웃", timeout: int = None):
        super().__init__(message, status_code=None)
        self.timeout = timeout

    def __str__(self):
        if self.timeout:
            return f"{self.message} ({self.timeout}초)"
        return self.message


def handle_http_error(status_code: int, response_data: dict = None) -> PlayautoAPIError:
    """
    HTTP 상태 코드에 따른 적절한 예외 반환

    Args:
        status_code: HTTP 상태 코드
        response_data: API 응답 데이터

    Returns:
        적절한 PlayautoAPIError 서브클래스 인스턴스
    """
    message = response_data.get("message", "") if response_data else ""

    if status_code == 401 or status_code == 403:
        return PlayautoAuthError(message or "인증 실패", status_code, response_data)
    elif status_code == 404:
        return PlayautoNotFoundError(message or "리소스를 찾을 수 없습니다", status_code, response_data)
    elif status_code == 429:
        retry_after = response_data.get("retry_after") if response_data else None
        return PlayautoRateLimitError(message or "API 호출 제한 초과", status_code, response_data, retry_after)
    elif status_code == 400:
        validation_errors = response_data.get("errors") if response_data else None
        return PlayautoDataError(message or "데이터 형식 오류", status_code, response_data, validation_errors)
    elif status_code >= 500:
        return PlayautoServerError(message or "서버 오류", status_code, response_data)
    else:
        return PlayautoAPIError(message or f"HTTP {status_code} 에러", status_code, response_data)
