#!/usr/bin/env python3
"""
수동 매핑용 엑셀 템플릿 생성

현재 사용 중인 카테고리를 우선순위로 정렬하고
검색 키워드 힌트를 제공합니다.
"""
import pandas as pd
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CATEGORIES_CSV = Path(__file__).parent / "categories_list.csv"
OUTPUT_TEMPLATE = Path(__file__).parent / "manual_mapping_template.xlsx"


def get_usage_priority():
    """현재 사용 중인 카테고리 우선순위"""
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()

    # category_playauto_mapping에서 사용 빈도 확인
    cursor.execute("""
        SELECT category_id, COUNT(*) as usage_count
        FROM category_playauto_mapping
        GROUP BY category_id
    """)
    usage = {int(row[0]): int(row[1]) for row in cursor.fetchall()}

    conn.close()
    return usage


def extract_search_keywords(category_path):
    """카테고리 경로에서 검색 키워드 추출"""
    parts = category_path.split(' > ')

    # 마지막 레벨 (가장 구체적)
    last = parts[-1].strip()

    # 마지막에서 두 번째 레벨
    second_last = parts[-2].strip() if len(parts) >= 2 else ""

    # 검색 키워드 조합
    keywords = []

    # 1. 마지막 레벨
    keywords.append(last)

    # 2. 마지막 두 레벨 조합
    if second_last:
        keywords.append(f"{second_last} {last}")

    # 3. 첫 번째 레벨 (대분류)
    if len(parts) >= 1:
        keywords.append(parts[0].strip())

    return " / ".join(keywords[:2])  # 상위 2개만


def main():
    print("=" * 80)
    print("수동 매핑 템플릿 생성")
    print("=" * 80)
    print()

    # 카테고리 로드
    print("[1/3] 카테고리 로드 중...")
    categories = pd.read_csv(CATEGORIES_CSV, encoding='utf-8-sig')
    print(f"  {len(categories)}개 카테고리")

    # 사용 빈도 조회
    print("[2/3] 사용 빈도 조회 중...")
    usage = get_usage_priority()
    print(f"  {len(usage)}개 카테고리가 사용 중")

    # 템플릿 데이터 생성
    print("[3/3] 템플릿 생성 중...")
    template_data = []

    for idx, row in categories.iterrows():
        cat_id = row['ID']
        folder = row['Folder']
        full_path = row['Full Path']

        # 사용 빈도
        usage_count = usage.get(cat_id, 0)
        priority = "★★★ 필수" if usage_count > 0 else ""

        # 검색 키워드
        search_hint = extract_search_keywords(full_path)

        template_data.append({
            'ID': cat_id,
            '우선순위': priority,
            '사용빈도': usage_count,
            '폴더명': folder,
            '카테고리 전체 경로': full_path,
            '검색 키워드 힌트': search_hint,
            'new_code': '',  # 여기를 채워야 함
            '확인': ''  # 매핑 완료 체크용
        })

    df = pd.DataFrame(template_data)

    # 우선순위 정렬: 사용빈도 높은 것 먼저
    df = df.sort_values(['사용빈도', 'ID'], ascending=[False, True])

    # 엑셀로 저장
    with pd.ExcelWriter(OUTPUT_TEMPLATE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='카테고리 매핑', index=False)

        # 열 너비 조정
        worksheet = writer.sheets['카테고리 매핑']
        worksheet.column_dimensions['A'].width = 8   # ID
        worksheet.column_dimensions['B'].width = 12  # 우선순위
        worksheet.column_dimensions['C'].width = 10  # 사용빈도
        worksheet.column_dimensions['D'].width = 20  # 폴더명
        worksheet.column_dimensions['E'].width = 50  # 카테고리 전체 경로
        worksheet.column_dimensions['F'].width = 30  # 검색 키워드
        worksheet.column_dimensions['G'].width = 12  # new_code
        worksheet.column_dimensions['H'].width = 8   # 확인

    print()
    print("=" * 80)
    print("템플릿 생성 완료!")
    print("=" * 80)
    print()
    print(f"파일: {OUTPUT_TEMPLATE}")
    print()
    print("사용 방법:")
    print("1. Excel에서 manual_mapping_template.xlsx 열기")
    print("2. '★★★ 필수' 표시된 48개부터 매핑")
    print("3. 검색 키워드로 category.xlsx에서 찾기:")
    print("   python search_category.py <키워드>")
    print("4. 찾은 코드를 'new_code' 컬럼에 입력")
    print("5. '확인' 컬럼에 'O' 표시")
    print("6. 저장 후 적용:")
    print("   python apply_manual_mapping.py")
    print()

    # 통계 출력
    priority_count = len(df[df['우선순위'] != ''])
    print(f"우선순위 카테고리: {priority_count}개")
    print(f"기타 카테고리: {len(df) - priority_count}개")
    print()


if __name__ == "__main__":
    main()
