"""
플레이오토 API 인증 관리

토큰 발급, 갱신, 인증 헤더 생성
"""

import os
import httpx
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from database.db_wrapper import get_db
from .crypto import decrypt_api_key, encrypt_api_key
from .exceptions import PlayautoAuthError


# 토큰 캐시 (메모리)
_token_cache = {
    "token": None,
    "sol_no": None,
    "expires_at": None
}


def load_api_credentials() -> Tuple[str, str, str]:
    """
    API 자격 증명 로드 (환경변수 우선, DB 대체)

    Returns:
        (api_key, email, password) 튜플

    Raises:
        PlayautoAuthError: API 키를 찾을 수 없는 경우
    """
    # 1. 환경변수에서 로드 (최우선)
    api_key = os.getenv("PLAYAUTO_API_KEY")
    email = os.getenv("PLAYAUTO_EMAIL")
    password = os.getenv("PLAYAUTO_PASSWORD")

    if api_key and email and password:
        return api_key, email, password

    # 2. DB에서 로드 (환경변수가 없는 경우)
    try:
        db = get_db()

        if not api_key:
            encrypted_api_key = db.get_playauto_setting("api_key")
            if encrypted_api_key:
                is_encrypted = (db.get_playauto_setting("api_key_encrypted") or "").lower() == "true"
                api_key = decrypt_api_key(encrypted_api_key) if is_encrypted else encrypted_api_key

        if not email:
            encrypted_email = db.get_playauto_setting("email")
            if encrypted_email:
                is_encrypted = (db.get_playauto_setting("email_encrypted") or "").lower() == "true"
                email = decrypt_api_key(encrypted_email) if is_encrypted else encrypted_email

        if not password:
            encrypted_password = db.get_playauto_setting("password")
            if encrypted_password:
                is_encrypted = (db.get_playauto_setting("password_encrypted") or "").lower() == "true"
                password = decrypt_api_key(encrypted_password) if is_encrypted else encrypted_password

        if api_key and email and password:
            return api_key, email, password

    except Exception as e:
        print(f"[WARN] DB에서 API 자격 증명 로드 실패: {e}")

    # 3. 찾지 못한 경우
    raise PlayautoAuthError(
        "플레이오토 API 자격 증명을 찾을 수 없습니다. "
        "환경변수 PLAYAUTO_API_KEY, PLAYAUTO_EMAIL, PLAYAUTO_PASSWORD를 설정하세요."
    )


def get_api_base_url() -> str:
    """
    API 기본 URL 조회

    Returns:
        API 기본 URL
    """
    # 환경변수에서 로드
    base_url = os.getenv("PLAYAUTO_API_URL", "https://openapi.playauto.io/api")

    # DB에서 로드 (환경변수가 없는 경우)
    if base_url == "https://openapi.playauto.io/api":
        try:
            db = get_db()
            db_url = db.get_playauto_setting("api_base_url")
            if db_url:
                base_url = db_url
        except Exception:
            pass

    return base_url


def fetch_token(api_key: str, email: str, password: str, base_url: str) -> Tuple[str, int]:
    """
    플레이오토 API 토큰 발급

    Args:
        api_key: x-api-key 헤더용 API 키
        email: 이메일
        password: 비밀번호
        base_url: API Base URL

    Returns:
        (token, sol_no) 튜플

    Raises:
        PlayautoAuthError: 토큰 발급 실패
    """
    try:
        print(f"[INFO] 플레이오토 토큰 발급 시도: {email}")

        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{base_url}/auth",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "password": password
                }
            )

            if response.status_code == 200:
                data = response.json()

                # 응답이 list인 경우 처리 (플레이오토 API는 list로 응답)
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]

                token = data.get("token")
                sol_no = data.get("sol_no")

                if token:
                    print(f"[SUCCESS] 토큰 발급 성공: sol_no={sol_no}")
                    return token, sol_no
                else:
                    raise PlayautoAuthError("토큰이 응답에 포함되지 않았습니다")

            else:
                error_message = response.text
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", error_message)
                except:
                    pass

                raise PlayautoAuthError(
                    f"토큰 발급 실패 (HTTP {response.status_code}): {error_message}"
                )

    except httpx.HTTPError as e:
        raise PlayautoAuthError(f"네트워크 오류로 토큰 발급 실패: {str(e)}")
    except PlayautoAuthError:
        raise
    except Exception as e:
        raise PlayautoAuthError(f"토큰 발급 중 알 수 없는 오류: {str(e)}")


def get_cached_token() -> Optional[Tuple[str, int]]:
    """
    캐시된 토큰 조회

    Returns:
        (token, sol_no) 또는 None (만료됨)
    """
    global _token_cache

    if _token_cache["token"] and _token_cache["expires_at"]:
        # 토큰이 아직 유효한지 확인
        if datetime.now() < _token_cache["expires_at"]:
            return _token_cache["token"], _token_cache["sol_no"]
        else:
            print("[INFO] 캐시된 토큰이 만료되었습니다")
            _token_cache = {"token": None, "sol_no": None, "expires_at": None}

    return None


def cache_token(token: str, sol_no: int):
    """
    토큰 캐싱 (24시간 유효)

    Args:
        token: 발급받은 토큰
        sol_no: 솔루션 번호
    """
    global _token_cache

    # 24시간 - 1시간 (안전 마진)
    expires_at = datetime.now() + timedelta(hours=23)

    _token_cache = {
        "token": token,
        "sol_no": sol_no,
        "expires_at": expires_at
    }

    print(f"[INFO] 토큰 캐싱 완료 (만료: {expires_at.strftime('%Y-%m-%d %H:%M:%S')})")


def get_or_fetch_token() -> Tuple[str, int]:
    """
    토큰 조회 (캐시 확인 → 없으면 새로 발급)

    Returns:
        (token, sol_no) 튜플

    Raises:
        PlayautoAuthError: 토큰 발급 실패
    """
    # 1. 캐시된 토큰 확인
    cached = get_cached_token()
    if cached:
        return cached

    # 2. 새로 발급
    api_key, email, password = load_api_credentials()
    base_url = get_api_base_url()

    token, sol_no = fetch_token(api_key, email, password, base_url)

    # 3. 캐싱
    cache_token(token, sol_no)

    return token, sol_no


def generate_auth_headers() -> Dict[str, str]:
    """
    인증 헤더 생성

    플레이오토 API는 다음 헤더를 요구합니다:
    - x-api-key: API 키
    - Authorization: Token {발급받은_토큰}

    Returns:
        인증 헤더 딕셔너리

    Raises:
        PlayautoAuthError: 토큰 발급 실패
    """
    # API 키 로드
    api_key, _, _ = load_api_credentials()

    # 토큰 조회 (캐시 or 새로 발급)
    token, sol_no = get_or_fetch_token()

    headers = {
        "x-api-key": api_key,
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    return headers


def validate_api_key(api_key: str) -> bool:
    """
    API 키 형식 검증

    Args:
        api_key: 검증할 API 키

    Returns:
        유효하면 True, 아니면 False
    """
    if not api_key:
        return False

    # API 키 길이 확인 (최소 10자)
    if len(api_key) < 10:
        return False

    # API 키 형식 확인 (영문자, 숫자만 허용)
    import re
    if not re.match(r'^[a-zA-Z0-9]+$', api_key):
        return False

    return True


def save_api_credentials_to_db(
    api_key: str,
    email: str,
    password: str,
    encrypt: bool = True
) -> bool:
    """
    API 자격 증명을 DB에 저장

    Args:
        api_key: API 키
        email: 이메일
        password: 비밀번호
        encrypt: 암호화 여부 (기본값: True)

    Returns:
        저장 성공 여부
    """
    try:
        db = get_db()

        # API 키 저장
        if encrypt:
            encrypted_key = encrypt_api_key(api_key)
            db.save_playauto_setting("api_key", encrypted_key, encrypted=True)
            db.save_playauto_setting("api_key_encrypted", "true", encrypted=False)

            encrypted_email = encrypt_api_key(email)
            db.save_playauto_setting("email", encrypted_email, encrypted=True)
            db.save_playauto_setting("email_encrypted", "true", encrypted=False)

            encrypted_password = encrypt_api_key(password)
            db.save_playauto_setting("password", encrypted_password, encrypted=True)
            db.save_playauto_setting("password_encrypted", "true", encrypted=False)
        else:
            db.save_playauto_setting("api_key", api_key, encrypted=False)
            db.save_playauto_setting("api_key_encrypted", "false", encrypted=False)

            db.save_playauto_setting("email", email, encrypted=False)
            db.save_playauto_setting("email_encrypted", "false", encrypted=False)

            db.save_playauto_setting("password", password, encrypted=False)
            db.save_playauto_setting("password_encrypted", "false", encrypted=False)

        return True

    except Exception as e:
        print(f"[ERROR] API 자격 증명 DB 저장 실패: {e}")
        return False


def mask_api_key(api_key: str) -> str:
    """
    API 키 마스킹 (보안)

    Args:
        api_key: 원본 API 키

    Returns:
        마스킹된 API 키 (앞 4자, 뒤 4자만 표시)
    """
    if not api_key or len(api_key) < 8:
        return "****"

    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def clear_token_cache():
    """토큰 캐시 초기화"""
    global _token_cache
    _token_cache = {"token": None, "sol_no": None, "expires_at": None}
    print("[INFO] 토큰 캐시가 초기화되었습니다")
