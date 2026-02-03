#!/usr/bin/env python3
"""
category.xlsx 검색 도구

사용법:
  python search_category.py "라면"
  python search_category.py "만두"
"""
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CATEGORY_FILE = PROJECT_ROOT / "category.xlsx"


def search_category(keyword):
    """키워드로 카테고리 검색"""
    # category.xlsx 로드
    df = pd.read_excel(CATEGORY_FILE, engine='openpyxl')
    df.columns = ['code', 'classification', 'name']

    # 검색
    keyword = keyword.lower()
    results = []

    for idx, row in df.iterrows():
        code = int(row['code'])
        classification = str(row['classification']).lower()
        name = str(row['name']).lower()

        # 키워드가 카테고리명 또는 분류에 포함되어 있으면
        if keyword in name or keyword in classification:
            results.append({
                'code': code,
                'classification': row['classification'],
                'name': row['name'],
                'relevance': (
                    100 if keyword in name.split(' > ')[-1] else  # 마지막 레벨에 있으면 최고점
                    50 if keyword in name else  # 전체 경로에 있으면 중간점
                    25  # 분류에만 있으면 낮은 점수
                )
            })

    # 관련도순으로 정렬
    results.sort(key=lambda x: x['relevance'], reverse=True)

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python search_category.py <keyword>")
        print("Example: python search_category.py 라면")
        sys.exit(1)

    keyword = sys.argv[1]

    print(f"Searching for: '{keyword}'")
    print("=" * 80)

    results = search_category(keyword)

    if not results:
        print("No results found.")
    else:
        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results[:20], 1):
            print(f"{i:2d}. [{result['code']}] {result['name']}")
            print(f"    ({result['classification']})")

        if len(results) > 20:
            print(f"\n... and {len(results) - 20} more results")


if __name__ == "__main__":
    main()
