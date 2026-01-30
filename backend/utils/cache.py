"""
API 응답 캐싱 유틸리티

TTL (Time To Live) 기반 캐싱을 제공합니다.
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple
import hashlib
import json


class TTLCache:
    """TTL(Time To Live) 기반 캐시"""

    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str, ttl: int) -> Optional[Any]:
        """
        캐시에서 값 조회

        Args:
            key: 캐시 키
            ttl: TTL (초)

        Returns:
            캐시된 값 또는 None
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]

        # TTL 만료 체크
        if time.time() - timestamp > ttl:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any):
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
        """
        self._cache[key] = (value, time.time())

    def clear(self):
        """캐시 전체 삭제"""
        self._cache.clear()

    def delete(self, key: str):
        """특정 키 삭제"""
        if key in self._cache:
            del self._cache[key]


# 전역 캐시 인스턴스
_global_cache = TTLCache()


def cached(ttl: int = 60):
    """
    함수 결과를 TTL 기간 동안 캐싱하는 데코레이터

    Args:
        ttl: 캐시 유효 시간 (초)

    Usage:
        @cached(ttl=300)  # 5분 캐싱
        def expensive_function(arg1, arg2):
            return ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성 (함수명 + 인자)
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = hashlib.md5(key_str.encode()).hexdigest()

            # 캐시 조회
            cached_value = _global_cache.get(cache_key, ttl)
            if cached_value is not None:
                return cached_value

            # 캐시 미스 - 함수 실행
            result = func(*args, **kwargs)

            # 결과 캐싱
            _global_cache.set(cache_key, result)

            return result

        # 캐시 수동 제어를 위한 메서드 추가
        wrapper.clear_cache = _global_cache.clear
        wrapper.cache = _global_cache

        return wrapper

    return decorator


def async_cached(ttl: int = 60):
    """
    비동기 함수 결과를 TTL 기간 동안 캐싱하는 데코레이터

    Args:
        ttl: 캐시 유효 시간 (초)

    Usage:
        @async_cached(ttl=300)  # 5분 캐싱
        async def expensive_async_function(arg1, arg2):
            return ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성 (함수명 + 인자)
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = hashlib.md5(key_str.encode()).hexdigest()

            # 캐시 조회
            cached_value = _global_cache.get(cache_key, ttl)
            if cached_value is not None:
                return cached_value

            # 캐시 미스 - 함수 실행
            result = await func(*args, **kwargs)

            # 결과 캐싱
            _global_cache.set(cache_key, result)

            return result

        # 캐시 수동 제어를 위한 메서드 추가
        wrapper.clear_cache = _global_cache.clear
        wrapper.cache = _global_cache

        return wrapper

    return decorator


# 전역 캐시 인스턴스 접근
def get_cache() -> TTLCache:
    """전역 캐시 인스턴스 반환"""
    return _global_cache


def clear_all_cache():
    """모든 캐시 삭제"""
    _global_cache.clear()
    print("[Cache] 전체 캐시 삭제됨")
