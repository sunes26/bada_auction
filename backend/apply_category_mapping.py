#!/usr/bin/env python3
"""
카테고리 코드 매핑 적용 스크립트

수동으로 편집한 category_code_mapping.csv 파일을 읽어서
데이터베이스의 sol_cate_no 값을 업데이트합니다.
"""
import pandas as pd
import sys
from pathlib import Path
from database.database_manager import get_database_manager

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
MAPPING_FILE = PROJECT_ROOT / "backend" / "category_code_mapping.csv"


def load_mapping():
    """매핑 파일 로드"""
    if not MAPPING_FILE.exists():
        print(f"❌ 매핑 파일이 없습니다: {MAPPING_FILE}")
        sys.exit(1)

    df = pd.read_csv(MAPPING_FILE, encoding='utf-8-sig')

    # new_code가 있는 것만 필터링 (매핑된 것만)
    df = df[df['new_code'].notna()].copy()

    # 딕셔너리로 변환 (old_code -> new_code)
    mapping = {}
    for _, row in df.iterrows():
        old_code = int(row['old_code'])
        new_code = int(float(row['new_code']))
        mapping[old_code] = new_code

    return mapping


def get_current_usage(db_manager):
    """현재 데이터베이스에서 사용 중인 sol_cate_no 조회"""
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()

    # 판매 상품 테이블
    cursor.execute("SELECT DISTINCT sol_cate_no FROM selling_products WHERE sol_cate_no IS NOT NULL")
    products = {int(row[0]) for row in cursor.fetchall()}

    # 카테고리 매핑 테이블
    cursor.execute("SELECT DISTINCT sol_cate_no FROM category_playauto_mapping WHERE sol_cate_no IS NOT NULL")
    category_mapping = {int(row[0]) for row in cursor.fetchall()}

    conn.close()

    return {
        'products': products,
        'category_mapping': category_mapping,
        'all': products | category_mapping
    }


def update_database(mapping, dry_run=True):
    """데이터베이스 업데이트"""
    db_manager = get_database_manager()

    # 현재 사용 중인 코드 조회
    print("📊 현재 사용 중인 sol_cate_no 조회 중...")
    usage = get_current_usage(db_manager)

    print(f"  - 판매 상품: {len(usage['products'])}개 고유 코드")
    print(f"  - 카테고리 매핑: {len(usage['category_mapping'])}개 고유 코드")
    print(f"  - 전체: {len(usage['all'])}개 고유 코드")
    print()

    # 매핑 가능한 코드 확인
    mappable = usage['all'] & set(mapping.keys())
    unmappable = usage['all'] - set(mapping.keys())

    print("=" * 80)
    print("매핑 가능 여부")
    print("=" * 80)
    print(f"✅ 매핑 가능: {len(mappable)}개")
    print(f"❌ 매핑 불가: {len(unmappable)}개")

    if unmappable:
        print("\n⚠️  매핑되지 않은 코드들:")
        for code in sorted(unmappable)[:10]:
            print(f"  - {code}")
        if len(unmappable) > 10:
            print(f"  ... 외 {len(unmappable) - 10}개")
    print()

    if not mappable:
        print("❌ 업데이트할 데이터가 없습니다.")
        return

    if dry_run:
        print("=" * 80)
        print("🔍 DRY RUN 모드 - 실제 업데이트는 하지 않습니다")
        print("=" * 80)
        print("\n업데이트 예정:")
        for old_code in sorted(mappable)[:10]:
            new_code = mapping[old_code]
            print(f"  {old_code} → {new_code}")
        if len(mappable) > 10:
            print(f"  ... 외 {len(mappable) - 10}개")
        print()
        print("실제 업데이트를 하려면: python apply_category_mapping.py --apply")
        return

    # 실제 업데이트 수행
    print("=" * 80)
    print("🚀 데이터베이스 업데이트 시작")
    print("=" * 80)

    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    placeholder = "?" if db_manager.is_sqlite else "%s"

    try:
        # 1. selling_products 테이블 업데이트
        print("\n[1/2] selling_products 테이블 업데이트 중...")
        update_count = 0
        for old_code in usage['products'] & mappable:
            new_code = mapping[old_code]
            cursor.execute(
                f"UPDATE selling_products SET sol_cate_no = {placeholder} WHERE sol_cate_no = {placeholder}",
                (new_code, old_code)
            )
            update_count += cursor.rowcount
        print(f"  ✅ {update_count}개 행 업데이트")

        # 2. category_playauto_mapping 테이블 업데이트
        print("\n[2/2] category_playauto_mapping 테이블 업데이트 중...")
        update_count = 0
        for old_code in usage['category_mapping'] & mappable:
            new_code = mapping[old_code]
            cursor.execute(
                f"UPDATE category_playauto_mapping SET sol_cate_no = {placeholder} WHERE sol_cate_no = {placeholder}",
                (new_code, old_code)
            )
            update_count += cursor.rowcount
        print(f"  ✅ {update_count}개 행 업데이트")

        # 커밋
        conn.commit()
        print("\n" + "=" * 80)
        print("✅ 업데이트 완료!")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 에러 발생: {str(e)}")
        raise
    finally:
        conn.close()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='카테고리 코드 매핑 적용')
    parser.add_argument('--apply', action='store_true', help='실제로 데이터베이스 업데이트')
    args = parser.parse_args()

    print("=" * 80)
    print("카테고리 코드 매핑 적용 스크립트")
    print("=" * 80)
    print()

    # 매핑 파일 로드
    print(f"📂 매핑 파일 로드 중: {MAPPING_FILE.name}")
    mapping = load_mapping()
    print(f"  ✅ {len(mapping):,}개 매핑 로드됨")
    print()

    # 데이터베이스 업데이트
    update_database(mapping, dry_run=not args.apply)


if __name__ == "__main__":
    main()
