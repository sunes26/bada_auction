"""
암호화 유틸리티

API 키 및 민감한 정보를 암호화/복호화하는 모듈
Fernet (대칭키 암호화) 사용
"""

import os
from cryptography.fernet import Fernet
from typing import Optional


class Crypto:
    """암호화/복호화 클래스"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Args:
            encryption_key: 암호화 키 (base64 인코딩된 문자열)
                          제공되지 않으면 환경변수 ENCRYPTION_KEY 사용
        """
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # 환경변수에서 키 로드
            env_key = os.getenv("ENCRYPTION_KEY")
            if env_key:
                self.key = env_key.encode()
            else:
                # 키가 없으면 새로 생성 (권장하지 않음 - 환경변수 사용 필요)
                self.key = Fernet.generate_key()
                print("[WARN] ENCRYPTION_KEY 환경변수가 없어 임시 키 생성. 프로덕션 환경에서는 환경변수 설정 필요!")

        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """
        데이터 암호화

        Args:
            data: 암호화할 평문 문자열

        Returns:
            암호화된 문자열 (base64 인코딩)
        """
        encrypted_data = self.fernet.encrypt(data.encode())
        return encrypted_data.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        데이터 복호화

        Args:
            encrypted_data: 암호화된 문자열 (base64 인코딩)

        Returns:
            복호화된 평문 문자열
        """
        decrypted_data = self.fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()

    @staticmethod
    def generate_key() -> str:
        """
        새로운 암호화 키 생성

        Returns:
            base64 인코딩된 Fernet 키
        """
        return Fernet.generate_key().decode()


# 전역 Crypto 인스턴스
_crypto_instance = None


def get_crypto() -> Crypto:
    """
    전역 Crypto 인스턴스 가져오기

    Returns:
        Crypto 싱글톤 인스턴스
    """
    global _crypto_instance
    if _crypto_instance is None:
        _crypto_instance = Crypto()
    return _crypto_instance


def encrypt_api_key(api_key: str) -> str:
    """
    API 키 암호화 헬퍼 함수

    Args:
        api_key: 암호화할 API 키

    Returns:
        암호화된 API 키
    """
    crypto = get_crypto()
    return crypto.encrypt(api_key)


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    API 키 복호화 헬퍼 함수

    Args:
        encrypted_api_key: 암호화된 API 키

    Returns:
        복호화된 API 키
    """
    crypto = get_crypto()
    return crypto.decrypt(encrypted_api_key)


if __name__ == "__main__":
    # 테스트용
    print("암호화 키 생성 테스트")
    print("새 암호화 키:", Crypto.generate_key())
    print("\n암호화/복호화 테스트")

    # 테스트 데이터
    test_api_key = "test_api_key_12345"

    # 암호화
    crypto = Crypto()
    encrypted = crypto.encrypt(test_api_key)
    print(f"원본: {test_api_key}")
    print(f"암호화: {encrypted}")

    # 복호화
    decrypted = crypto.decrypt(encrypted)
    print(f"복호화: {decrypted}")
    print(f"일치 여부: {test_api_key == decrypted}")
