#!/usr/bin/env python3
"""
현재 데이터베이스에서 사용 중인 카테고리 코드 확인

실제로 상품에 사용되고 있는 sol_cate_no를 조회하여
우선순위 매핑 대상을 파악합니다.
"""
import pandas as pd
from pathlib import Path
from collections import Counter
from database.database_manager import get_database_manager

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_FILE = PROJECT_ROOT / "backend" / "category_code_mapping.csv"
OLD_CATEGORY_FILE = PROJECT_ROOT / "Standard_category_list.xlsx"


def load_old_categories():
    """구 카테고리 시스템 로드"""
    df = pd.read_excel(OLD_CATEGORY_FILE)
    df.columns = ['code', 'l1', 'l2', 'l3', 'l4']

    # 카테고리 경로 생성
    def build_path(row):
        parts = []
        for col in ['l1', 'l2', 'l3', 'l4']:
            if pd.notna(row[col]):
                parts.append(str(row[col]))
        return ' > '.join(parts)

    df['path'] = df.apply(build_path, axis=1)

    # 딕셔너리로 변환
    return {int(row['code']): row['path'] for _, row in df.iterrows()}


def get_current_usage():
    """현재 사용 중인 sol_cate_no 조회"""
    db_manager = get_database_manager()
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    results = {}

    # 1. selling_products 테이블
    print("📊 판매 상품 테이블 조회 중...")
    cursor.execute("""
        SELECT sol_cate_no, COUNT(*) as count
        FROM selling_products
        WHERE sol_cate_no IS NOT NULL
        GROUP BY sol_cate_no
        ORDER BY count DESC
    """)
    products = {}
    for row in cursor.fetchall():
        code = int(row[0])
        count = int(row[1])
        products[code] = count

    # 2. category_playauto_mapping 테이블
    print("📊 카테고리 매핑 테이블 조회 중...")
    cursor.execute("""
        SELECT sol_cate_no, COUNT(*) as count
        FROM category_playauto_mapping
        WHERE sol_cate_no IS NOT NULL
        GROUP BY sol_cate_no
        ORDER BY count DESC
    """)
    category_mapping = {}
    for row in cursor.fetchall():
        code = int(row[0])
        count = int(row[1])
        category_mapping[code] = count

    conn.close()

    return {
        'products': products,
        'category_mapping': category_mapping
    }


def check_mapping_status(codes, mapping_df):
    """매핑 상태 확인"""
    mapped = []
    unmapped = []
    partial = []

    for code in codes:
        # 매핑 파일에서 해당 코드 찾기
        row = mapping_df[mapping_df['old_code'] == code]

        if len(row) == 0:
            unmapped.append(code)
        elif pd.isna(row.iloc[0]['new_code']):
            unmapped.append(code)
        else:
            status = row.iloc[0]['match_status']
            similarity = row.iloc[0]['similarity_score']
            if status in ['high_confidence', 'medium_confidence']:
                mapped.append((code, similarity, status))
            else:
                partial.append((code, similarity, status))

    return {
        'mapped': mapped,
        'partial': partial,
        'unmapped': unmapped
    }


def main():
    """메인 함수"""
    print("=" * 80)
    print("현재 사용 중인 카테고리 코드 확인")
    print("=" * 80)
    print()

    # 구 카테고리 시스템 로드
    print("📂 구 카테고리 시스템 로드 중...")
    old_categories = load_old_categories()
    print(f"  ✅ {len(old_categories):,}개 카테고리 로드됨")
    print()

    # 매핑 파일 로드
    print("📂 매핑 파일 로드 중...")
    if not MAPPING_FILE.exists():
        print(f"  ⚠️  매핑 파일이 없습니다: {MAPPING_FILE}")
        print("  먼저 create_mapping.py를 실행하세요.")
        return

    mapping_df = pd.read_csv(MAPPING_FILE, encoding='utf-8-sig')
    print(f"  ✅ {len(mapping_df):,}개 매핑 로드됨")
    print()

    # 현재 사용 중인 카테고리 조회
    usage = get_current_usage()

    print()
    print("=" * 80)
    print("사용 통계")
    print("=" * 80)

    # 판매 상품
    print("\n📦 판매 상품 (selling_products)")
    print(f"  총 고유 카테고리: {len(usage['products'])}개")
    if usage['products']:
        total_products = sum(usage['products'].values())
        print(f"  총 상품 개수: {total_products}개")
        print()
        print("  TOP 20 카테고리 (사용 빈도 높은 순):")
        print("  " + "-" * 76)
        for i, (code, count) in enumerate(sorted(usage['products'].items(), key=lambda x: x[1], reverse=True)[:20], 1):
            path = old_categories.get(code, "❓ 알 수 없음")
            print(f"  {i:2d}. [{code}] {path}")
            print(f"      사용: {count}개 상품")

    # 카테고리 매핑
    print("\n📋 카테고리 매핑 (category_playauto_mapping)")
    print(f"  총 고유 카테고리: {len(usage['category_mapping'])}개")
    if usage['category_mapping']:
        total_mappings = sum(usage['category_mapping'].values())
        print(f"  총 매핑 개수: {total_mappings}개")

    # 전체 고유 카테고리
    all_codes = set(usage['products'].keys()) | set(usage['category_mapping'].keys())
    print(f"\n📊 전체 고유 카테고리: {len(all_codes)}개")

    # 매핑 상태 확인
    print()
    print("=" * 80)
    print("매핑 상태")
    print("=" * 80)

    status = check_mapping_status(all_codes, mapping_df)

    print(f"\n✅ 완전 매핑 (high/medium confidence): {len(status['mapped'])}개")
    print(f"⚠️  부분 매핑 (low confidence): {len(status['partial'])}개")
    print(f"❌ 미매핑: {len(status['unmapped'])}개")

    # 미매핑 카테고리 상세 출력
    if status['unmapped']:
        print()
        print("=" * 80)
        print("⚠️  미매핑 카테고리 (우선 매핑 필요!)")
        print("=" * 80)
        print()

        # 사용 빈도로 정렬
        unmapped_with_usage = []
        for code in status['unmapped']:
            usage_count = usage['products'].get(code, 0) + usage['category_mapping'].get(code, 0)
            unmapped_with_usage.append((code, usage_count))

        unmapped_with_usage.sort(key=lambda x: x[1], reverse=True)

        for i, (code, usage_count) in enumerate(unmapped_with_usage[:30], 1):
            path = old_categories.get(code, "❓ 알 수 없음")
            print(f"{i:2d}. [{code}] {path}")
            if usage_count > 0:
                print(f"    📊 사용: {usage_count}회")
            print()

        if len(status['unmapped']) > 30:
            print(f"... 외 {len(status['unmapped']) - 30}개")

    # 부분 매핑 카테고리
    if status['partial']:
        print()
        print("=" * 80)
        print("⚠️  부분 매핑 카테고리 (검토 필요)")
        print("=" * 80)
        print()

        for i, (code, similarity, match_status) in enumerate(status['partial'][:20], 1):
            path = old_categories.get(code, "❓ 알 수 없음")
            usage_count = usage['products'].get(code, 0) + usage['category_mapping'].get(code, 0)
            print(f"{i:2d}. [{code}] {path}")
            print(f"    유사도: {similarity} ({match_status})")
            if usage_count > 0:
                print(f"    사용: {usage_count}회")
            print()

        if len(status['partial']) > 20:
            print(f"... 외 {len(status['partial']) - 20}개")

    # 다음 단계 안내
    print()
    print("=" * 80)
    print("📝 다음 단계")
    print("=" * 80)
    print()
    print("1. backend/category_code_mapping.csv 파일을 Excel로 열기")
    print("2. 미매핑 카테고리부터 수동으로 매핑")
    print("3. 부분 매핑 카테고리 검토 및 수정")
    print("4. 매핑 적용:")
    print("   python backend/apply_category_mapping.py        # Dry run")
    print("   python backend/apply_category_mapping.py --apply  # 실제 적용")
    print()
    print("자세한 가이드: backend/CATEGORY_MAPPING_GUIDE.md")
    print()


if __name__ == "__main__":
    main()
