"""
API 응답 캐싱 유틸리티

TTL (Time To Live) 기반 캐싱을 제공합니다.
Redis가 설치되어 있으면 Redis를 사용하고, 없으면 메모리 캐시를 사용합니다.
"""

import time
import os
import pickle
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple
import hashlib
import json

# Redis 사용 가능 여부 확인
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class TTLCache:
    """TTL(Time To Live) 기반 메모리 캐시"""

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


class RedisCache:
    """Redis 기반 분산 캐시"""

    def __init__(self, redis_url: str):
        """
        Args:
            redis_url: Redis 연결 URL (예: redis://localhost:6379/0)
        """
        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=False,  # pickle 사용 시 False
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 연결 테스트
            self.client.ping()
            self.available = True
            print(f"[Cache] Redis 연결 성공: {redis_url}")
        except Exception as e:
            self.available = False
            self.client = None
            print(f"[Cache] Redis 연결 실패: {e}")
            print(f"[Cache] 메모리 캐시로 폴백합니다")

    def get(self, key: str, ttl: int) -> Optional[Any]:
        """
        캐시에서 값 조회

        Args:
            key: 캐시 키
            ttl: TTL (초) - Redis에서는 무시됨 (set 시 이미 설정)

        Returns:
            캐시된 값 또는 None
        """
        if not self.available:
            return None

        try:
            cached = self.client.get(key)
            if cached is None:
                return None

            # pickle로 역직렬화
            return pickle.loads(cached)
        except Exception as e:
            print(f"[Cache] Redis get 오류: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: TTL (초) - 기본 300초 (5분)
        """
        if not self.available:
            return

        try:
            # pickle로 직렬화
            serialized = pickle.dumps(value)
            self.client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"[Cache] Redis set 오류: {e}")

    def clear(self):
        """캐시 전체 삭제"""
        if not self.available:
            return

        try:
            self.client.flushdb()
            print("[Cache] Redis 전체 캐시 삭제됨")
        except Exception as e:
            print(f"[Cache] Redis clear 오류: {e}")

    def delete(self, key: str):
        """특정 키 삭제"""
        if not self.available:
            return

        try:
            self.client.delete(key)
        except Exception as e:
            print(f"[Cache] Redis delete 오류: {e}")


# 캐시 초기화 (Redis 우선, 없으면 메모리 캐시)
def _init_cache():
    """캐시 초기화 - Redis 우선, 없으면 메모리 캐시"""
    redis_url = os.getenv('REDIS_URL', os.getenv('REDIS_PRIVATE_URL'))

    if REDIS_AVAILABLE and redis_url:
        print(f"[Cache] Redis 초기화 시도...")
        cache = RedisCache(redis_url)
        if cache.available:
            print(f"[Cache] Redis 캐시 사용")
            return cache
        else:
            print(f"[Cache] Redis 사용 불가, 메모리 캐시로 폴백")

    print(f"[Cache] 메모리 캐시 사용 (Redis 미설치 또는 미설정)")
    return TTLCache()


# 전역 캐시 인스턴스
_global_cache = _init_cache()


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

            # 결과 캐싱 (Redis는 TTL 포함)
            if isinstance(_global_cache, RedisCache):
                _global_cache.set(cache_key, result, ttl)
            else:
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

            # 결과 캐싱 (Redis는 TTL 포함)
            if isinstance(_global_cache, RedisCache):
                _global_cache.set(cache_key, result, ttl)
            else:
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
