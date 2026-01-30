"""
플레이오토 카테고리 관리 API
"""
from fastapi import APIRouter, HTTPException
from playauto.client import PlayautoClient
from logger import get_logger

router = APIRouter(prefix="/api/playauto", tags=["Playauto Categories"])
logger = get_logger(__name__)


@router.get("/categories")
async def get_playauto_categories():
    """
    플레이오토에 설정된 카테고리 목록 조회

    Returns:
        카테고리 목록 (sol_cate_no, sol_cate_name, shop_cd 등)
    """
    try:
        async with PlayautoClient() as client:
            # 첫 1000개 카테고리 조회
            categories = await client.get("/categorys", params={
                "start": 0,
                "length": 1000
            })

            logger.info(f"[플레이오토] 카테고리 {len(categories)}개 조회 완료")

            if not categories or len(categories) == 0:
                return {
                    "success": True,
                    "count": 0,
                    "categories": [],
                    "message": "카테고리가 없습니다. 플레이오토 웹(https://playauto.io)에서 카테고리를 먼저 설정해주세요.",
                    "setup_guide": {
                        "step1": "https://playauto.io 로그인",
                        "step2": "설정 > 카테고리 관리",
                        "step3": "쇼핑몰별 카테고리 매핑 설정",
                        "step4": "설정 완료 후 이 API로 다시 조회"
                    }
                }

            return {
                "success": True,
                "count": len(categories),
                "categories": categories
            }

    except Exception as e:
        logger.error(f"[플레이오토] 카테고리 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"카테고리 조회 실패: {str(e)}"
        )


@router.get("/categories/food")
async def get_food_categories():
    """
    식품 관련 카테고리만 필터링하여 조회
    """
    try:
        async with PlayautoClient() as client:
            categories = await client.get("/categorys", params={
                "start": 0,
                "length": 1000
            })

            # 식품 관련 키워드로 필터링
            food_keywords = ["식품", "식료품", "가공식품", "즉석", "밥", "쌀", "간편식"]
            food_categories = []

            for cat in categories:
                cat_name = cat.get("sol_cate_name", "")
                if any(keyword in cat_name for keyword in food_keywords):
                    food_categories.append(cat)

            return {
                "success": True,
                "count": len(food_categories),
                "categories": food_categories
            }

    except Exception as e:
        logger.error(f"[플레이오토] 식품 카테고리 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"식품 카테고리 조회 실패: {str(e)}"
        )
