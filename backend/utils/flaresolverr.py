"""
FlareSolverr 클라이언트
Cloudflare 보호를 우회하기 위한 프록시 서비스 연동
"""
import os
import requests
from typing import Optional, Dict, Any
from logger import get_logger

logger = get_logger(__name__)

# FlareSolverr 서버 URL (환경변수로 설정)
FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "http://localhost:8191/v1")


class FlareSolverrClient:
    """FlareSolverr API 클라이언트"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or FLARESOLVERR_URL
        self.session_id = None

    def is_available(self) -> bool:
        """FlareSolverr 서버 연결 가능 여부 확인"""
        try:
            response = requests.get(
                self.base_url.replace("/v1", "/health"),
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"FlareSolverr 연결 실패: {e}")
            return False

    def create_session(self) -> Optional[str]:
        """세션 생성 (브라우저 인스턴스 재사용)"""
        try:
            response = requests.post(
                self.base_url,
                json={
                    "cmd": "sessions.create"
                },
                timeout=60
            )
            data = response.json()
            if data.get("status") == "ok":
                self.session_id = data.get("session")
                logger.info(f"FlareSolverr 세션 생성: {self.session_id}")
                return self.session_id
            else:
                logger.error(f"세션 생성 실패: {data.get('message')}")
                return None
        except Exception as e:
            logger.error(f"세션 생성 오류: {e}")
            return None

    def destroy_session(self, session_id: str = None):
        """세션 종료"""
        sid = session_id or self.session_id
        if not sid:
            return

        try:
            requests.post(
                self.base_url,
                json={
                    "cmd": "sessions.destroy",
                    "session": sid
                },
                timeout=30
            )
            logger.info(f"FlareSolverr 세션 종료: {sid}")
            if sid == self.session_id:
                self.session_id = None
        except Exception as e:
            logger.warning(f"세션 종료 오류: {e}")

    def get_page(
        self,
        url: str,
        session_id: str = None,
        max_timeout: int = 60000,
        cookies: list = None
    ) -> Optional[Dict[str, Any]]:
        """
        페이지 요청 (Cloudflare 우회)

        Args:
            url: 요청할 URL
            session_id: 세션 ID (재사용 시)
            max_timeout: 최대 대기 시간 (밀리초)
            cookies: 추가할 쿠키 목록

        Returns:
            {
                "solution": {
                    "url": str,
                    "status": int,
                    "headers": dict,
                    "cookies": list,
                    "userAgent": str,
                    "response": str  # HTML 내용
                },
                "status": str,
                "message": str
            }
        """
        try:
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": max_timeout
            }

            # 세션 사용 (브라우저 재사용)
            if session_id or self.session_id:
                payload["session"] = session_id or self.session_id

            # 쿠키 추가
            if cookies:
                payload["cookies"] = cookies

            logger.info(f"FlareSolverr 요청: {url}")

            response = requests.post(
                self.base_url,
                json=payload,
                timeout=max_timeout / 1000 + 10  # 약간의 여유
            )

            data = response.json()

            if data.get("status") == "ok":
                solution = data.get("solution", {})
                logger.info(f"FlareSolverr 성공: status={solution.get('status')}")
                return data
            else:
                logger.error(f"FlareSolverr 실패: {data.get('message')}")
                return None

        except requests.Timeout:
            logger.error(f"FlareSolverr 타임아웃: {url}")
            return None
        except Exception as e:
            logger.error(f"FlareSolverr 오류: {e}")
            return None

    def extract_cookies_for_requests(self, flaresolverr_cookies: list) -> Dict[str, str]:
        """
        FlareSolverr 쿠키를 requests 라이브러리용으로 변환

        Args:
            flaresolverr_cookies: FlareSolverr에서 반환한 쿠키 목록

        Returns:
            requests 라이브러리에서 사용할 수 있는 쿠키 딕셔너리
        """
        cookies = {}
        for cookie in flaresolverr_cookies:
            cookies[cookie["name"]] = cookie["value"]
        return cookies

    def extract_cookies_for_selenium(self, flaresolverr_cookies: list) -> list:
        """
        FlareSolverr 쿠키를 Selenium용으로 변환

        Args:
            flaresolverr_cookies: FlareSolverr에서 반환한 쿠키 목록

        Returns:
            Selenium driver.add_cookie()에 사용할 수 있는 쿠키 목록
        """
        selenium_cookies = []
        for cookie in flaresolverr_cookies:
            selenium_cookie = {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
            }
            if cookie.get("expiry"):
                selenium_cookie["expiry"] = int(cookie["expiry"])
            selenium_cookies.append(selenium_cookie)
        return selenium_cookies


# 싱글톤 인스턴스
_client = None


def get_flaresolverr_client() -> FlareSolverrClient:
    """FlareSolverr 클라이언트 인스턴스 반환"""
    global _client
    if _client is None:
        _client = FlareSolverrClient()
    return _client


def solve_cloudflare(url: str) -> Optional[Dict[str, Any]]:
    """
    Cloudflare 보호 우회하여 페이지 내용 가져오기

    Args:
        url: 요청할 URL

    Returns:
        {
            "html": str,  # 페이지 HTML
            "cookies": dict,  # requests용 쿠키
            "user_agent": str,  # User-Agent
            "status": int  # HTTP 상태 코드
        }
        실패 시 None
    """
    client = get_flaresolverr_client()

    if not client.is_available():
        logger.warning("FlareSolverr 사용 불가")
        return None

    result = client.get_page(url)

    if result and result.get("status") == "ok":
        solution = result.get("solution", {})
        return {
            "html": solution.get("response", ""),
            "cookies": client.extract_cookies_for_requests(solution.get("cookies", [])),
            "selenium_cookies": client.extract_cookies_for_selenium(solution.get("cookies", [])),
            "user_agent": solution.get("userAgent", ""),
            "status": solution.get("status", 200)
        }

    return None
