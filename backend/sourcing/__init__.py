"""
상품 소싱 모듈

각 쇼핑몰의 상품 정보를 추출하는 스크래퍼 모듈

지원 마켓:
- Traders (홈플러스 트레이더스)
- SSG (신세계몰)
- 11st (11번가)
- Homeplus (홈플러스)
- Gmarket (G마켓) ⭐ NEW!
- Smartstore (네이버 스마트스토어) ⭐ NEW!
"""

from .gmarket import GmarketScraper
from .smartstore import SmartstoreScraper

__all__ = ['GmarketScraper', 'SmartstoreScraper']
