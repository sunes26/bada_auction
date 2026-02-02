#!/usr/bin/env python3
"""
카테고리 자동 매칭 스크립트

우리 시스템의 카테고리를 플레이오토 표준 카테고리 코드와 자동으로 매칭합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from difflib import SequenceMatcher

# 우리 시스템 카테고리 (categories.ts에서 추출)
OUR_CATEGORIES = {
    # 간편식
    "간편식 > 밥류 > 즉석밥 > 흰밥": None,
    "간편식 > 밥류 > 즉석밥 > 흑미": None,
    "간편식 > 밥류 > 즉석밥 > 잡곡": None,
    "간편식 > 밥류 > 즉석밥 > 현미": None,
    "간편식 > 밥류 > 즉석밥 > 렌틸콩현미": None,
    "간편식 > 밥류 > 즉석밥 > 채소영양": None,
    "간편식 > 밥류 > 즉석밥 > 버섯영양": None,
    "간편식 > 밥류 > 덮밥 > 스팸김치": None,
    "간편식 > 밥류 > 덮밥 > 참치마요": None,
    "간편식 > 밥류 > 덮밥 > 치킨마요": None,
    "간편식 > 밥류 > 죽 > 팥죽": None,
    "간편식 > 밥류 > 죽 > 야채죽": None,
    "간편식 > 밥류 > 죽 > 소고기죽": None,
    "간편식 > 밥류 > 죽 > 전복죽": None,

    # 통조림
    "간편식 > 통조림 > 햄 > 햄": None,
    "간편식 > 통조림 > 햄 > 닭": None,
    "간편식 > 통조림 > 참치 > 일반참치": None,
    "간편식 > 통조림 > 참치 > 고추참치": None,
    "간편식 > 통조림 > 참치 > 꽁치": None,
    "간편식 > 통조림 > 참치 > 고등어": None,
    "간편식 > 통조림 > 과일 > 파인애플": None,
    "간편식 > 통조림 > 과일 > 황도": None,
    "간편식 > 통조림 > 과일 > 후르츠칵테일": None,
    "간편식 > 통조림 > 과일 > 스위트콘": None,

    # 카레/짜장/덮밥
    "간편식 > 카레/짜장/덮밥 > 카레 > 카레": None,
    "간편식 > 카레/짜장/덮밥 > 짜장 > 짜장": None,
    "간편식 > 카레/짜장/덮밥 > 마파두부 > 마파두부": None,

    # 국/찌개
    "간편식 > 국/찌개 > 곰탕류 > 곰탕류": None,
    "간편식 > 국/찌개 > 미역국 > 미역국": None,
    "간편식 > 국/찌개 > 육개장 > 육개장": None,
    "간편식 > 국/찌개 > 청국장 > 청국장": None,
    "간편식 > 국/찌개 > 추어탕 > 추어탕": None,
    "간편식 > 국/찌개 > 삼계탕 > 삼계탕": None,
    "간편식 > 국/찌개 > 무국 > 무국": None,
    "간편식 > 국/찌개 > 황태국 > 황태국": None,
    "간편식 > 국/찌개 > 갈비탕 > 갈비탕": None,
    "간편식 > 국/찌개 > 순두부찌개 > 순두부찌개": None,
    "간편식 > 국/찌개 > 부대찌개 > 부대찌개": None,

    # 면
    "간편식 > 면 > 라면 > 라면": None,
    "간편식 > 면 > 짜파게티 > 짜파게티": None,
    "간편식 > 면 > 비빔면 > 비빔면": None,
    "간편식 > 면 > 칼국수 > 칼국수": None,
    "간편식 > 면 > 물냉면 > 물냉면": None,
    "간편식 > 면 > 비빔냉면 > 비빔냉면": None,
    "간편식 > 면 > 소바 > 소바": None,
    "간편식 > 면 > 우동 > 우동": None,

    # 냉동식
    "냉동식 > 만두 > 고기만두 > 고기만두": None,
    "냉동식 > 만두 > 김치만두 > 김치만두": None,
    "냉동식 > 만두 > 새우만두 > 새우만두": None,
    "냉동식 > 떡볶이 > 빨간떡볶이 > 빨간떡볶이": None,
    "냉동식 > 떡볶이 > 크림떡볶이 > 크림떡볶이": None,
    "냉동식 > 떡볶이 > 짜장떡볶이 > 짜장떡볶이": None,
    "냉동식 > 치킨 > 허니치킨 > 허니치킨": None,
    "냉동식 > 치킨 > 양념치킨 > 양념치킨": None,
    "냉동식 > 피자 > 피자 > 피자": None,
    "냉동식 > 돈까스 > 돈까스 > 돈까스": None,

    # 음료
    "음료 > 커피 > 라떼 > 라떼": None,
    "음료 > 커피 > 아메리카노 > 아메리카노": None,
    "음료 > 커피 > 블랙 > 블랙": None,
    "음료 > 차류 > 보리 > 보리": None,
    "음료 > 차류 > 녹차 > 녹차": None,
    "음료 > 차류 > 유자 > 유자": None,
    "음료 > 생수 > 생수 > 생수": None,
    "음료 > 전통음료 > 식혜 > 식혜": None,
    "음료 > 전통음료 > 수정과 > 수정과": None,

    # 생활용품
    "생활용품 > 헤어케어 > 샴푸 > 샴푸": None,
    "생활용품 > 헤어케어 > 린스/트리트먼트 > 린스/트리트먼트": None,
    "생활용품 > 바디케어 > 바디워시/바디로션 > 바디워시/바디로션": None,
    "생활용품 > 바디케어 > 핸드워시/핸드크림 > 핸드워시/핸드크림": None,
    "생활용품 > 휴지/티슈 > 롤화장지 > 롤화장지": None,
    "생활용품 > 휴지/티슈 > 키친타월 > 키친타월": None,
    "생활용품 > 휴지/티슈 > 티슈 > 티슈": None,
    "생활용품 > 휴지/티슈 > 물티슈 > 물티슈": None,
    "생활용품 > 위생용품 > 생리대 > 생리대": None,
    "생활용품 > 구강케어 > 치약 > 치약": None,
    "생활용품 > 구강케어 > 칫솔 > 칫솔": None,
    "생활용품 > 구강케어 > 가글 > 가글": None,
    "생활용품 > 세제 > 세탁세제 > 세탁세제": None,
    "생활용품 > 세제 > 섬유유연제 > 섬유유연제": None,
    "생활용품 > 세제 > 욕실세제 > 욕실세제": None,
    "생활용품 > 세제 > 주방세제 > 주방세제": None,
}


def similarity(a: str, b: str) -> float:
    """두 문자열의 유사도 계산 (0~1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_best_match(our_category: str, playauto_df: pd.DataFrame, threshold: float = 0.5):
    """
    우리 카테고리와 가장 유사한 플레이오토 카테고리 찾기

    Args:
        our_category: 우리 카테고리 (예: "간편식 > 밥류 > 즉석밥 > 흰밥")
        playauto_df: 플레이오토 카테고리 DataFrame
        threshold: 최소 유사도 (0.5 = 50%)

    Returns:
        (카테고리코드, 매칭된 카테고리명, 유사도)
    """
    # 우리 카테고리에서 키워드 추출 (마지막 소분류가 가장 중요)
    keywords = our_category.split(" > ")
    main_keyword = keywords[-1]  # 마지막 키워드 (가장 구체적)

    best_match = None
    best_score = 0

    for idx, row in playauto_df.iterrows():
        # 플레이오토 카테고리 전체 경로 생성
        parts = []
        if pd.notna(row['대분류명']):
            parts.append(row['대분류명'])
        if pd.notna(row['중분류명']):
            parts.append(row['중분류명'])
        if pd.notna(row['소분류명']):
            parts.append(row['소분류명'])
        if pd.notna(row['세분류명']):
            parts.append(row['세분류명'])

        playauto_category = " > ".join(parts)

        # 유사도 계산 (전체 경로 + 마지막 키워드에 가중치)
        score1 = similarity(our_category, playauto_category)
        score2 = similarity(main_keyword, parts[-1] if parts else "")

        # 최종 점수 (마지막 키워드에 더 높은 가중치)
        final_score = score1 * 0.3 + score2 * 0.7

        if final_score > best_score:
            best_score = final_score
            best_match = (
                int(row['카테고리코드']),
                playauto_category,
                final_score
            )

    if best_score >= threshold:
        return best_match

    return None


def auto_match_categories(excel_path: str):
    """카테고리 자동 매칭 실행"""
    print("=" * 80)
    print("플레이오토 카테고리 자동 매칭 스크립트")
    print("=" * 80)
    print()

    # Excel 파일 로드
    print(f"[1/4] Excel 파일 로드 중... ({excel_path})")
    df = pd.read_excel(excel_path)
    print(f"[OK] {len(df):,}개 카테고리 로드 완료")
    print()

    # 식품 관련 카테고리만 필터링
    print("[2/4] 식품/생활용품 관련 카테고리 필터링 중...")
    food_keywords = ['식품', '가공식품', '음료', '생필품', '생활용품', '세제', '화장지']
    food_df = df[df['대분류명'].str.contains('|'.join(food_keywords), na=False)]
    print(f"[OK] {len(food_df):,}개 카테고리 필터링 완료")
    print()

    # 자동 매칭 시작
    print("[3/4] 자동 매칭 시작...")
    print()

    results = []
    success_count = 0
    uncertain_count = 0
    fail_count = 0

    for our_category in OUR_CATEGORIES.keys():
        match_result = find_best_match(our_category, food_df, threshold=0.5)

        if match_result:
            code, playauto_cat, score = match_result

            if score >= 0.7:
                status = "[OK] 확신"
                success_count += 1
            else:
                status = "[WARN] 확인필요"
                uncertain_count += 1

            results.append({
                "our_category": our_category,
                "sol_cate_no": code,
                "playauto_category": playauto_cat,
                "similarity": f"{score:.1%}",
                "status": status
            })

            print(f"{status} {our_category}")
            print(f"      -> {code} ({playauto_cat}) [{score:.1%}]")
            print()
        else:
            status = "[FAIL] 실패"
            fail_count += 1
            results.append({
                "our_category": our_category,
                "sol_cate_no": 38,  # 기타 재화 (기본값)
                "playauto_category": "기타 재화",
                "similarity": "0%",
                "status": status
            })

            print(f"{status} {our_category}")
            print(f"      -> 기본값 사용 (38 - 기타 재화)")
            print()

    # 결과 저장
    print("[4/4] 결과 저장 중...")
    result_df = pd.DataFrame(results)
    output_path = project_root / "backend" / "category_mapping_result.csv"
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"[OK] 결과 저장 완료: {output_path}")
    print()

    # 요약
    print("=" * 80)
    print("매칭 결과 요약")
    print("=" * 80)
    print(f"[OK] 자동 매칭 성공 (70% 이상): {success_count}개")
    print(f"[WARN] 확인 필요 (50~70%):      {uncertain_count}개")
    print(f"[FAIL] 매칭 실패 (기본값 사용):   {fail_count}개")
    print(f"[INFO] 전체:                       {len(OUR_CATEGORIES)}개")
    print()
    print(f"다음 단계:")
    print(f"   1. {output_path} 파일을 열어서 매칭 결과 확인")
    print(f"   2. [WARN] 표시된 항목들은 수동으로 검토 필요")
    print(f"   3. 확인 후 DB에 입력하시겠습니까?")
    print("=" * 80)

    return result_df


if __name__ == "__main__":
    excel_path = project_root / "Standard_category_list.xlsx"

    if not excel_path.exists():
        print(f"❌ Excel 파일을 찾을 수 없습니다: {excel_path}")
        sys.exit(1)

    result_df = auto_match_categories(str(excel_path))
