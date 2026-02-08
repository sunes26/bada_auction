from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from models.product import Product, ProductCreate
from scrapers import TradersScraper, CJTheMarketScraper
from scrapers.ssg_scraper_selenium import SSGSeleniumScraper

router = APIRouter(prefix="/api/sourcing", tags=["sourcing"])

# 스크래퍼 인스턴스
scrapers = {
    "traders": TradersScraper(),
    "ssg": SSGSeleniumScraper(),
    "cjthemarket": CJTheMarketScraper(),
}


@router.post("/search", response_model=dict)
async def search_products(
    source: str = Query(..., description="소싱처 (traders, ssg, all)"),
    category: Optional[str] = Query(None, description="카테고리"),
    keyword: Optional[str] = Query(None, description="검색 키워드"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """
    상품 검색

    지정된 소싱처에서 상품을 검색합니다.
    """
    try:
        all_products: List[ProductCreate] = []

        if source == "all":
            # 모든 소싱처에서 검색
            for scraper in scrapers.values():
                products = await scraper.search_products(
                    category=category,
                    keyword=keyword,
                    page=page,
                    page_size=page_size // len(scrapers)
                )
                all_products.extend(products)
        elif source in scrapers:
            # 특정 소싱처에서 검색
            scraper = scrapers[source]
            products = await scraper.search_products(
                category=category,
                keyword=keyword,
                page=page,
                page_size=page_size
            )
            all_products.extend(products)
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 소싱처: {source}")

        # ProductCreate를 Product로 변환 (ID, 타임스탬프 추가)
        result_products = []
        for idx, product in enumerate(all_products):
            product_dict = product.model_dump()
            product_dict['id'] = f"{product.source}_{datetime.now().timestamp()}_{idx}"
            product_dict['created_at'] = datetime.now()
            product_dict['updated_at'] = datetime.now()
            product_dict['margin_rate'] = 30.0  # 기본 30% 마진
            product_dict['selling_price'] = product.price * 1.3  # 마진 포함 판매가

            result_products.append(product_dict)

        return {
            "products": result_products,
            "total": len(result_products),
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상품 검색 중 오류 발생: {str(e)}")


@router.get("/price-check", response_model=dict)
async def check_price(
    source: str = Query(..., description="소싱처"),
    product_url: str = Query(..., description="상품 URL")
):
    """
    가격 확인

    지정된 상품의 현재 가격을 확인합니다.
    """
    try:
        if source not in scrapers:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 소싱처: {source}")

        scraper = scrapers[source]
        current_price = await scraper.check_price(product_url)

        return {
            "source": source,
            "product_url": product_url,
            "current_price": current_price,
            "checked_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가격 확인 중 오류 발생: {str(e)}")
