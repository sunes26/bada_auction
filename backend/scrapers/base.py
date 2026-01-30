from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from models.product import ProductCreate


class BaseScraper(ABC):
    """
    스크래퍼 기본 클래스

    모든 스크래퍼는 이 클래스를 상속받아 구현해야 합니다.
    """

    def __init__(self):
        self.source_name = ""
        self.base_url = ""

    @abstractmethod
    async def search_products(
        self,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[ProductCreate]:
        """
        상품 검색

        Args:
            category: 카테고리 (선택)
            keyword: 검색 키워드 (선택)
            page: 페이지 번호
            page_size: 페이지당 항목 수

        Returns:
            ProductCreate 객체 리스트
        """
        pass

    @abstractmethod
    async def get_product_detail(self, product_url: str) -> Dict:
        """
        상품 상세 정보 가져오기

        Args:
            product_url: 상품 URL

        Returns:
            상품 상세 정보 딕셔너리
        """
        pass

    @abstractmethod
    async def check_price(self, product_url: str) -> float:
        """
        상품 가격 확인 (가격 동기화용)

        Args:
            product_url: 상품 URL

        Returns:
            현재 가격
        """
        pass

    def calculate_margin(self, cost_price: float, margin_rate: float = 30.0) -> float:
        """
        마진 계산

        Args:
            cost_price: 원가
            margin_rate: 마진율 (기본 30%)

        Returns:
            판매가
        """
        return cost_price * (1 + margin_rate / 100)
