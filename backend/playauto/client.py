"""
플레이오토 API 클라이언트 코어

httpx 기반 비동기 HTTP 클라이언트
재시도 로직, 에러 처리, 타임아웃 관리 포함
"""

import httpx
import asyncio
import time
from typing import Dict, Optional, Any
from .auth import load_api_credentials, generate_auth_headers, get_api_base_url
from .exceptions import (
    PlayautoAPIError,
    PlayautoNetworkError,
    PlayautoTimeoutError,
    handle_http_error
)


class PlayautoClient:
    """플레이오토 API HTTP 클라이언트"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Args:
            api_key: API 키 (제공되지 않으면 환경변수/DB에서 로드)
            base_url: API 기본 URL (제공되지 않으면 환경변수/DB에서 로드)
            timeout: 요청 타임아웃 (초, 기본값: 30)
            max_retries: 최대 재시도 횟수 (기본값: 3)
        """
        self.base_url = base_url or get_api_base_url()
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP 클라이언트 초기화
        self.client = None
        self._auth_headers = None  # 필요할 때 생성

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        # 인증 헤더 생성 (토큰 발급 포함)
        self._auth_headers = generate_auth_headers()

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._auth_headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()

    async def close(self):
        """클라이언트 종료"""
        if self.client:
            await self.client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        공통 요청 메서드 (재시도 로직 포함)

        Args:
            method: HTTP 메서드 (GET, POST, PUT, PATCH, DELETE)
            endpoint: API 엔드포인트 경로
            data: 요청 바디 데이터 (POST, PUT, PATCH, DELETE)
            params: 쿼리 파라미터 (GET)
            retry_count: 현재 재시도 횟수

        Returns:
            API 응답 데이터 (JSON)

        Raises:
            PlayautoAPIError: API 요청 실패
            PlayautoNetworkError: 네트워크 연결 실패
            PlayautoTimeoutError: 요청 타임아웃
        """
        # 클라이언트가 초기화되지 않은 경우
        if not self.client:
            # 인증 헤더 생성 (토큰 발급 포함)
            if not self._auth_headers:
                self._auth_headers = generate_auth_headers()

            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._auth_headers
            )

        try:
            # 요청 실행
            if method.upper() == "GET":
                response = await self.client.get(endpoint, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(endpoint, json=data)
            elif method.upper() == "PATCH":
                response = await self.client.patch(endpoint, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(endpoint, json=data)
            else:
                raise PlayautoAPIError(f"지원하지 않는 HTTP 메서드: {method}")

            # 응답 처리
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            else:
                # HTTP 에러 처리
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"message": response.text}

                raise handle_http_error(response.status_code, error_data)

        except httpx.TimeoutException as e:
            # 타임아웃 에러
            if retry_count < self.max_retries:
                # 재시도
                print(f"[WARN] 요청 타임아웃, 재시도 {retry_count + 1}/{self.max_retries}")
                await asyncio.sleep(2 ** retry_count)  # 지수 백오프
                return await self._request(method, endpoint, data, params, retry_count + 1)
            else:
                raise PlayautoTimeoutError(
                    f"API 요청 타임아웃 (최대 재시도 {self.max_retries}회 초과)",
                    timeout=self.timeout
                )

        except httpx.NetworkError as e:
            # 네트워크 에러
            if retry_count < self.max_retries:
                # 재시도
                print(f"[WARN] 네트워크 오류, 재시도 {retry_count + 1}/{self.max_retries}")
                await asyncio.sleep(2 ** retry_count)  # 지수 백오프
                return await self._request(method, endpoint, data, params, retry_count + 1)
            else:
                raise PlayautoNetworkError(
                    f"네트워크 연결 실패 (최대 재시도 {self.max_retries}회 초과)",
                    original_error=e
                )

        except PlayautoAPIError:
            # 이미 처리된 API 에러는 그대로 전달
            raise

        except Exception as e:
            # 기타 예외
            raise PlayautoAPIError(f"알 수 없는 오류: {str(e)}")

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET 요청

        Args:
            endpoint: API 엔드포인트 경로
            params: 쿼리 파라미터

        Returns:
            API 응답 데이터
        """
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        POST 요청

        Args:
            endpoint: API 엔드포인트 경로
            data: 요청 바디 데이터

        Returns:
            API 응답 데이터
        """
        return await self._request("POST", endpoint, data=data)

    async def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        PUT 요청

        Args:
            endpoint: API 엔드포인트 경로
            data: 요청 바디 데이터

        Returns:
            API 응답 데이터
        """
        return await self._request("PUT", endpoint, data=data)

    async def patch(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        PATCH 요청

        Args:
            endpoint: API 엔드포인트 경로
            data: 요청 바디 데이터

        Returns:
            API 응답 데이터
        """
        return await self._request("PATCH", endpoint, data=data)

    async def delete(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        DELETE 요청

        Args:
            endpoint: API 엔드포인트 경로
            data: 요청 바디 데이터 (선택)

        Returns:
            API 응답 데이터
        """
        return await self._request("DELETE", endpoint, data=data)

    def test_connection(self) -> bool:
        """
        API 연결 테스트 (동기)
        토큰 발급을 시도하여 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            from .auth import get_or_fetch_token
            # 토큰 발급 시도
            token, sol_no = get_or_fetch_token()
            print(f"[SUCCESS] API 연결 테스트 성공 (sol_no: {sol_no})")
            return True
        except Exception as e:
            print(f"[ERROR] API 연결 테스트 실패: {e}")
            return False
