import asyncio
import os
from dotenv import load_dotenv
from playauto.client import PlayautoClient

async def main():
    # 환경변수 로드
    load_dotenv("../.env.local")
    
    async with PlayautoClient() as client:
        # 템플릿 조회 (infoCode 정보가 포함되어 있을 수 있음)
        print("=== 템플릿 조회 ===")
        templates = await client.get("/templates")
        print(f"템플릿 응답: {templates}")
        
        # 카테고리 조회 (상품 정보 고시 코드가 포함되어 있을 수 있음)
        print("\n=== 카테고리 조회 ===")
        categories = await client.get("/categorys", params={"start": 0, "length": 10})
        print(f"카테고리 응답: {categories}")

if __name__ == "__main__":
    asyncio.run(main())
