"""
플레이오토 상품정보제공고시 코드 테스트

여러 infoCode 값을 시도하여 어떤 값이 유효한지 확인
"""

import asyncio
from playauto.client import PlayautoClient
from playauto.product_registration import build_product_data_from_db
from database.db import get_db
from dotenv import load_dotenv
import os

# 테스트할 infoCode 목록
TEST_CODES = [
    "38",  # 기타 재화
    "22",  # 가공식품
    "01",  # 식품
    "",    # 빈 문자열
    # 또는 플레이오토 특정 코드
]

async def test_product_registration(product_id: int, info_code: str):
    """특정 infoCode로 상품 등록 테스트"""
    print(f"\n{'='*60}")
    print(f"테스트 infoCode: '{info_code}'")
    print(f"{'='*60}")

    # 환경변수 로드
    env_path = "../.env.local"
    if os.path.exists(env_path):
        load_dotenv(env_path)

    # DB에서 상품 조회
    db = get_db()
    product = db.get_selling_product(product_id)

    if not product:
        print(f"❌ 상품을 찾을 수 없습니다: ID {product_id}")
        return False

    # 상품 데이터 구성
    site_list = [
        {
            "shop_cd": "A001",
            "shop_id": "oceancode",
            "template_no": 2235976
        }
    ]

    product_data = build_product_data_from_db(product, site_list)

    # infoCode 변경
    if info_code:
        product_data["prod_info"] = [
            {
                "infoCode": info_code,
                "infoDetail": {
                    "제품명": product.get("product_name", ""),
                    "제조자/수입자": "테스트",
                    "원산지": "국내산",
                    "제조일자": "2026-01-01",
                    "품질보증기준": "제조사 기준",
                    "A/S책임자와 전화번호": "010-1234-5678"
                }
            }
        ]
    else:
        product_data["prod_info"] = []

    # API 호출
    try:
        async with PlayautoClient() as client:
            endpoint = "/products/add/v1.2"
            result = await client.post(endpoint, data=product_data)

            api_result = result.get("result", "")

            if api_result == "성공":
                print(f"✅ 성공! infoCode '{info_code}' 사용 가능")
                print(f"   c_sale_cd: {result.get('c_sale_cd')}")
                return True
            else:
                error_code = result.get("error_code", "")
                messages = result.get("messages", [])
                print(f"❌ 실패: {error_code}")
                print(f"   메시지: {', '.join(messages)}")
                return False

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return False

async def main():
    """모든 infoCode 테스트"""
    print("플레이오토 상품정보제공고시 코드 테스트")
    print("=" * 60)

    # 테스트할 상품 ID (DB에서 실제 상품 ID 사용)
    product_id = 15  # CJ 비비고 왕만두

    results = {}

    for code in TEST_CODES:
        success = await test_product_registration(product_id, code)
        results[code] = success

        # API 부하 방지를 위해 대기
        await asyncio.sleep(2)

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for code, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"infoCode '{code}': {status}")

    print("\n✅ 성공한 코드를 사용하시면 됩니다!")

if __name__ == "__main__":
    asyncio.run(main())
