"""
플레이오토 카테고리 조회 테스트
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from playauto.client import PlayautoClient
from logger import get_logger

logger = get_logger(__name__)


async def get_categories():
    """플레이오토 카테고리 목록 조회"""
    try:
        async with PlayautoClient() as client:
            # 파라미터 없이 조회
            print("\n=== 1. 파라미터 없이 조회 ===")
            result1 = await client.get("/categorys")
            print(f"타입: {type(result1)}")
            print(f"길이: {len(result1) if isinstance(result1, list) else 'N/A'}")
            print(f"응답: {result1[:5] if isinstance(result1, list) and len(result1) > 0 else result1}")

            # 파라미터와 함께 조회
            print("\n=== 2. 파라미터와 함께 조회 (start=0, length=1000) ===")
            result2 = await client.get("/categorys", params={
                "start": 0,
                "length": 1000
            })
            print(f"타입: {type(result2)}")
            print(f"길이: {len(result2) if isinstance(result2, list) else 'N/A'}")
            print(f"응답: {result2[:5] if isinstance(result2, list) and len(result2) > 0 else result2}")

            # result1 사용
            categories = result1 if isinstance(result1, list) else []
            logger.info(f"카테고리 조회 성공")
            logger.info(f"총 카테고리 수: {len(categories)}")

            # 식품 관련 카테고리 찾기 (햇반 상품이므로)
            food_categories = []
            for cat in categories:
                cat_name = cat.get("sol_cate_name", "")
                if any(keyword in cat_name for keyword in ["식품", "식료품", "가공식품", "즉석", "밥", "쌀"]):
                    food_categories.append({
                        "sol_cate_no": cat.get("sol_cate_no"),
                        "sol_cate_name": cat_name,
                        "shop_cd": cat.get("shop_cd")
                    })

            print("\n=== 식품 관련 카테고리 ===")
            for cat in food_categories[:20]:  # 처음 20개만
                print(f"번호: {cat['sol_cate_no']}, 이름: {cat['sol_cate_name']}, 쇼핑몰: {cat['shop_cd']}")

            # 전체 카테고리 중 일부 출력
            print("\n=== 전체 카테고리 샘플 (처음 20개) ===")
            for cat in categories[:20]:
                print(f"번호: {cat.get('sol_cate_no')}, 이름: {cat.get('sol_cate_name')}, 쇼핑몰: {cat.get('shop_cd')}")

            return result

    except Exception as e:
        logger.error(f"카테고리 조회 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(get_categories())
