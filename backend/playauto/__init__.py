"""
플레이오토 API 통합 모듈

이 패키지는 플레이오토(Playauto) 2.0 API를 통합하여
여러 판매 마켓에서 주문을 자동으로 수집하고
송장번호를 일괄 등록하는 기능을 제공합니다.
"""

from .client import PlayautoClient
from .orders import PlayautoOrdersAPI
from .tracking import PlayautoTrackingAPI
from .exceptions import (
    PlayautoAPIError,
    PlayautoAuthError,
    PlayautoRateLimitError,
    PlayautoDataError
)

__version__ = "1.0.0"

__all__ = [
    "PlayautoClient",
    "PlayautoOrdersAPI",
    "PlayautoTrackingAPI",
    "PlayautoAPIError",
    "PlayautoAuthError",
    "PlayautoRateLimitError",
    "PlayautoDataError"
]
