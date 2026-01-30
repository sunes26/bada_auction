"""
플레이오토 템플릿 조회 API

솔루션에 등록된 템플릿 목록 조회
"""

from typing import Dict, List, Optional
from .client import PlayautoClient
from logger import get_logger

logger = get_logger(__name__)


class PlayautoTemplatesAPI:
    """플레이오토 템플릿 API"""

    def __init__(self):
        self.client = None

    async def get_templates(self, masking_yn: bool = False) -> Dict:
        """
        템플릿 목록 조회

        Args:
            masking_yn: 개인정보 마스킹 처리 여부 (기본값: False)

        Returns:
            템플릿 목록
            {
                "shop_cd": "A001",
                "shop_name": "스마트스토어",
                "shop_id": "my_smart_store",
                "template_info": [
                    {
                        "template_no": 1001,
                        "name": "기본 의류 배송 템플릿",
                        "apply_prod_cnt": 150,
                        "wdate": "2024-01-01 10:00:00",
                        "mdate": "2024-01-02 14:30:00",
                        "register_name": "관리자"
                    }
                ]
            }
        """
        try:
            endpoint = f"/templates/?masking_yn={str(masking_yn).lower()}"

            logger.info(f"[플레이오토] 템플릿 조회 시작")

            # API 호출
            if not self.client:
                async with PlayautoClient() as client:
                    result = await client.get(endpoint)
            else:
                result = await self.client.get(endpoint)

            # API 응답은 list 형태 (쇼핑몰별로 그룹화됨)
            # 모든 템플릿을 하나의 리스트로 통합
            all_templates = []
            if isinstance(result, list):
                for shop_data in result:
                    shop_cd = shop_data.get('shop_cd', '')
                    shop_name = shop_data.get('shop_name', '')
                    shop_id = shop_data.get('shop_id', '')
                    templates = shop_data.get('template_info', [])

                    # 각 템플릿에 쇼핑몰 정보 추가
                    for template in templates:
                        template['shop_cd'] = shop_cd
                        template['shop_name'] = shop_name
                        template['shop_id'] = shop_id
                        all_templates.append(template)

            logger.info(f"[플레이오토] 템플릿 조회 성공: {len(all_templates)}개")

            return {
                "success": True,
                "data": {
                    "template_info": all_templates
                }
            }

        except Exception as e:
            logger.error(f"[플레이오토] 템플릿 조회 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_template_by_no(self, template_no: int) -> Optional[Dict]:
        """
        특정 템플릿 정보 조회

        Args:
            template_no: 템플릿 번호

        Returns:
            템플릿 정보 또는 None
        """
        try:
            result = await self.get_templates()

            if not result.get("success"):
                return None

            templates = result.get("data", {}).get("template_info", [])

            for template in templates:
                if template.get("template_no") == template_no:
                    return template

            return None

        except Exception as e:
            logger.error(f"[플레이오토] 템플릿 조회 실패: {str(e)}")
            return None
