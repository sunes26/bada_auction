"""
플레이오토 택배사 코드 조회 API

플레이오토 표준 택배사 코드 리스트 조회
"""

from typing import Dict, List, Optional
from .client import PlayautoClient
from .exceptions import PlayautoAPIError


class PlayautoCarriersAPI:
    """플레이오토 택배사 코드 조회 API"""

    def __init__(self, client: Optional[PlayautoClient] = None):
        """
        Args:
            client: PlayautoClient 인스턴스 (제공되지 않으면 새로 생성)
        """
        self.client = client

    async def get_carriers(self) -> List[Dict]:
        """
        플레이오토 표준 택배사 코드 리스트 조회

        Returns:
            택배사 목록
            [
                {"carrier_code": 1, "carrier_name": "CJ대한통운"},
                {"carrier_code": 2, "carrier_name": "한진택배"},
                ...
            ]
        """
        if not self.client:
            async with PlayautoClient() as client:
                response = await client.get("/carriers")
        else:
            response = await self.client.get("/carriers")

        # 응답이 리스트인 경우 그대로 반환
        if isinstance(response, list):
            return response

        # 응답이 딕셔너리인 경우 data 키에서 추출
        return response.get("data", response.get("carriers", []))

    async def get_carrier_code(self, carrier_name: str) -> Optional[int]:
        """
        택배사명으로 택배사 코드 조회

        Args:
            carrier_name: 택배사명 (예: "CJ대한통운")

        Returns:
            택배사 코드 (carr_no) 또는 None
        """
        carriers = await self.get_carriers()

        for carrier in carriers:
            if carrier.get("carrier_name") == carrier_name:
                return carrier.get("carrier_code")

        return None

    async def get_carrier_name(self, carrier_code: int) -> Optional[str]:
        """
        택배사 코드로 택배사명 조회

        Args:
            carrier_code: 택배사 코드 (carr_no)

        Returns:
            택배사명 또는 None
        """
        carriers = await self.get_carriers()

        for carrier in carriers:
            if carrier.get("carrier_code") == carrier_code:
                return carrier.get("carrier_name")

        return None


# 캐시된 택배사 목록 (선택사항)
_carriers_cache: Optional[List[Dict]] = None


async def get_cached_carriers() -> List[Dict]:
    """
    캐시된 택배사 목록 조회 (없으면 API 호출)

    Returns:
        택배사 목록
    """
    global _carriers_cache

    if _carriers_cache is None:
        api = PlayautoCarriersAPI()
        _carriers_cache = await api.get_carriers()

    return _carriers_cache


def clear_carriers_cache():
    """택배사 캐시 초기화"""
    global _carriers_cache
    _carriers_cache = None
