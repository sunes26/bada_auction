#!/usr/bin/env python3
"""
138개 카테고리를 category.xlsx에 매핑하는 스크립트

기존 방식: 13,366개 구 카테고리 -> 신 카테고리 매핑 (복잡)
새 방식: 138개 현재 카테고리 -> category.xlsx 직접 매핑 (간단)
"""
import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

# 경로
PROJECT_ROOT = Path(__file__).parent.parent
CATEGORIES_CSV = PROJECT_ROOT / "backend" / "categories_list.csv"
NEW_CATEGORY_FILE = PROJECT_ROOT / "category.xlsx"
OUTPUT_MAPPING = PROJECT_ROOT / "backend" / "category_138_mapping.csv"


def similarity(a, b):
    """문자열 유사도 계산"""
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def main():
    print("=" * 80)
    print("138개 카테고리 매핑 생성기")
    print("=" * 80)
    print()

    # 1. 현재 138개 카테고리 로드
    print("[1/4] 현재 시스템 카테고리 로드 중...")
    our_cats = pd.read_csv(CATEGORIES_CSV, encoding='utf-8-sig')
    print(f"  ✅ {len(our_cats)}개 카테고리 로드")
    print()

    # 2. category.xlsx 로드
    print("[2/4] category.xlsx 로드 중...")
    new_cats = pd.read_excel(NEW_CATEGORY_FILE, engine='openpyxl')
    new_cats.columns = ['code', 'classification', 'name']
    print(f"  ✅ {len(new_cats):,}개 카테고리 로드")
    print()

    # 3. 각 카테고리 매핑
    print("[3/4] 카테고리 매핑 중...")
    mappings = []

    for idx, our_cat in our_cats.iterrows():
        if idx % 10 == 0:
            print(f"  진행: {idx}/{len(our_cats)}...")

        our_id = our_cat['ID']
        our_folder = our_cat['Folder']
        our_path = our_cat['Full Path']
        our_l1 = our_cat['Level1']
        our_l2 = our_cat['Level2']
        our_l3 = our_cat['Level3']
        our_l4 = our_cat['Level4']

        # category.xlsx에서 가장 유사한 카테고리 찾기
        best_score = 0
        best_code = None
        best_name = "UNMAPPED"
        best_classification = ""

        for _, new_cat in new_cats.iterrows():
            new_code = int(new_cat['code'])
            new_name = new_cat['name']
            new_classification = new_cat['classification']

            # 전체 경로 유사도
            score1 = similarity(our_path, new_name)

            # 마지막 레벨 유사도 (가중치 높임)
            our_last = our_l4
            new_parts = new_name.split(' > ')
            new_last = new_parts[-1] if new_parts else ""
            score2 = similarity(our_last, new_last)

            # 첫 번째 레벨(대분류) 유사도
            score3 = similarity(our_l1, new_classification)

            # 가중 평균: 마지막 레벨 50%, 전체 경로 30%, 대분류 20%
            weighted_score = score2 * 0.5 + score1 * 0.3 + score3 * 0.2

            if weighted_score > best_score:
                best_score = weighted_score
                best_code = new_code
                best_name = new_name
                best_classification = new_classification

        # 신뢰도 결정
        if best_score >= 0.7:
            confidence = 'high'
        elif best_score >= 0.5:
            confidence = 'medium'
        elif best_score >= 0.3:
            confidence = 'low'
        else:
            confidence = 'unmapped'
            best_code = None
            best_name = "UNMAPPED"

        mappings.append({
            'id': our_id,
            'folder': our_folder,
            'our_category': our_path,
            'level1': our_l1,
            'level2': our_l2,
            'level3': our_l3,
            'level4': our_l4,
            'new_code': best_code,
            'new_category': best_name,
            'new_classification': best_classification,
            'similarity': f"{best_score:.2%}",
            'confidence': confidence
        })

    print(f"  ✅ {len(mappings)}개 매핑 완료")
    print()

    # 4. 통계 및 저장
    print("[4/4] 결과 저장 중...")

    df = pd.DataFrame(mappings)
    df = df.sort_values('similarity', ascending=False)

    # 통계
    high = len(df[df['confidence'] == 'high'])
    medium = len(df[df['confidence'] == 'medium'])
    low = len(df[df['confidence'] == 'low'])
    unmapped = len(df[df['confidence'] == 'unmapped'])

    print()
    print("=" * 80)
    print("매핑 결과")
    print("=" * 80)
    print(f"총 카테고리:       {len(mappings)}개")
    print(f"높은 신뢰도 (≥70%): {high}개 ({high/len(mappings)*100:.1f}%)")
    print(f"중간 신뢰도 (50-70%): {medium}개 ({medium/len(mappings)*100:.1f}%)")
    print(f"낮은 신뢰도 (30-50%): {low}개 ({low/len(mappings)*100:.1f}%)")
    print(f"미매핑 (<30%):     {unmapped}개 ({unmapped/len(mappings)*100:.1f}%)")
    print(f"성공률 (≥50%):     {(high+medium)/len(mappings)*100:.1f}%")
    print("=" * 80)
    print()

    # CSV 저장
    df.to_csv(OUTPUT_MAPPING, index=False, encoding='utf-8-sig')
    print(f"✅ 저장 완료: {OUTPUT_MAPPING}")
    print()

    # 미매핑 카테고리 출력
    if unmapped > 0:
        print("⚠️  수동 매핑 필요한 카테고리:")
        print("-" * 80)
        unmapped_df = df[df['confidence'] == 'unmapped']
        for idx, row in unmapped_df.iterrows():
            print(f"{row['id']:3d}. {row['our_category']}")
        print()

    # 낮은 신뢰도 카테고리
    if low > 0:
        print("⚠️  검토 필요한 카테고리 (낮은 신뢰도, 처음 10개):")
        print("-" * 80)
        low_df = df[df['confidence'] == 'low'].head(10)
        for idx, row in low_df.iterrows():
            print(f"{row['id']:3d}. {row['our_category']}")
            print(f"     -> {row['new_category']} ({row['similarity']})")
        print()

    print("=" * 80)
    print("다음 단계")
    print("=" * 80)
    print()
    print("1. backend/category_138_mapping.csv 파일을 Excel로 열기")
    print("2. 미매핑 또는 낮은 신뢰도 카테고리 검토")
    print("3. 필요시 new_code 컬럼 수정")
    print("4. 적용 스크립트 실행:")
    print("   python backend/apply_138_mapping.py")
    print()


if __name__ == "__main__":
    main()
