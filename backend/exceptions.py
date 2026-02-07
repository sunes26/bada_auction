"""
커스텀 예외 클래스

API 에러 처리 통일을 위한 예외 클래스 정의
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any


class APIError(HTTPException):
    """
    API 에러 기본 클래스

    사용 예시:
        raise APIError(404, "상품을 찾을 수 없습니다", {"product_id": 123})
    """
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error": True,
                "message": message,
                "details": self.details
            }
        )


class NotFoundError(APIError):
    """리소스를 찾을 수 없음 (404)"""
    def __init__(self, resource: str, identifier: Any = None):
        details = {"resource": resource}
        if identifier is not None:
            details["identifier"] = identifier
        super().__init__(404, f"{resource}을(를) 찾을 수 없습니다", details)


class ValidationError(APIError):
    """유효성 검사 실패 (400)"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(400, message, details)


class AuthenticationError(APIError):
    """인증 실패 (401)"""
    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(401, message)


class PermissionError(APIError):
    """권한 없음 (403)"""
    def __init__(self, message: str = "권한이 없습니다"):
        super().__init__(403, message)


class ExternalServiceError(APIError):
    """외부 서비스 오류 (502)"""
    def __init__(self, service: str, message: str = None):
        msg = f"{service} 서비스 오류가 발생했습니다"
        if message:
            msg = f"{msg}: {message}"
        super().__init__(502, msg, {"service": service})
