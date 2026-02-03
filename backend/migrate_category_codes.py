#!/usr/bin/env python3
"""
Category Code Mapping Generator

This script creates a mapping table between:
- Old system: Standard_category_list.xlsx (PlayAuto standard categories)
- New system: category.xlsx (our internal category system)

Outputs:
1. CSV file: category_code_mapping.csv
2. JSON file: category_code_mapping.json

The mapping helps migrate from old category codes to new ones.
"""
import sys
from pathlib import Path
import pandas as pd
import json
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
OLD_SYSTEM_FILE = PROJECT_ROOT / "Standard_category_list.xlsx"
NEW_SYSTEM_FILE = PROJECT_ROOT / "category.xlsx"
OUTPUT_CSV = PROJECT_ROOT / "backend" / "category_code_mapping.csv"
OUTPUT_JSON = PROJECT_ROOT / "backend" / "category_code_mapping.json"


def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def build_category_path(row: pd.Series, columns: List[str]) -> str:
    """Build full category path from DataFrame row"""
    parts = []
    for col in columns:
        if pd.notna(row.get(col)):
            parts.append(str(row[col]).strip())
    return " > ".join(parts)


def load_old_system() -> pd.DataFrame:
    """Load old system categories from Standard_category_list.xlsx"""
    print("[1/6] Loading old system (Standard_category_list.xlsx)...")

    df = pd.read_excel(OLD_SYSTEM_FILE, engine='openpyxl')

    print(f"   Shape: {df.shape}")
    print(f"   Columns (count): {len(df.columns)}")

    # The Excel has 5 columns: 카테고리코드, 대분류명, 중분류명, 소분류명, 세분류명
    # Use column indices instead of names to avoid encoding issues
    df.columns = ['category_code', 'level1', 'level2', 'level3', 'level4']

    # Build full category paths
    category_columns = ['level1', 'level2', 'level3', 'level4']
    df['category_path'] = df.apply(
        lambda row: build_category_path(row, category_columns),
        axis=1
    )

    # Create a mapping with category code as key
    old_categories = {}
    for idx, row in df.iterrows():
        code = row.get('category_code')
        if pd.notna(code):
            old_categories[int(code)] = {
                'code': int(code),
                'path': row['category_path'],
                'level1': str(row.get('level1', '')),
                'level2': str(row.get('level2', '')),
                'level3': str(row.get('level3', '')),
                'level4': str(row.get('level4', ''))
            }

    print(f"   Loaded {len(old_categories):,} old categories")
    return old_categories


def load_new_system() -> Dict[str, dict]:
    """Load new system categories from category.xlsx"""
    print("[2/6] Loading new system (category.xlsx)...")

    df = pd.read_excel(NEW_SYSTEM_FILE, engine='openpyxl')

    print(f"   Shape: {df.shape}")
    print(f"   Columns (count): {len(df.columns)}")

    # The Excel has 3 columns: 카테고리코드, 분류, 카테고리명
    # Column 0: category_code
    # Column 1: classification (분류)
    # Column 2: full category path (카테고리명)

    df.columns = ['category_code', 'classification', 'category_path']

    # Build category paths and mappings
    new_categories = {}

    for idx, row in df.iterrows():
        code = row['category_code']
        path = str(row['category_path']).strip()

        # Parse the category path to extract levels
        # Path format: "level1 > level2 > level3 > level4"
        parts = [p.strip() for p in path.split('>')]

        # Pad with empty strings if less than 4 levels
        while len(parts) < 4:
            parts.append('')

        new_categories[path] = {
            'code': int(code) if pd.notna(code) else None,
            'path': path,
            'level1': parts[0] if len(parts) > 0 else '',
            'level2': parts[1] if len(parts) > 1 else '',
            'level3': parts[2] if len(parts) > 2 else '',
            'level4': parts[3] if len(parts) > 3 else ''
        }

    print(f"   Loaded {len(new_categories):,} new categories")

    # Show sample
    sample_keys = list(new_categories.keys())[:3]
    print(f"   Sample categories:")
    for key in sample_keys:
        cat = new_categories[key]
        print(f"      {cat['code']}: {cat['path']}")

    return new_categories


def find_best_match(old_cat: dict, new_categories: Dict[str, dict], threshold: float = 0.4) -> Optional[Tuple[str, dict, float]]:
    """Find best matching new category for an old category"""
    old_path = old_cat['path']

    # Extract keywords from old path (last level is most important)
    old_parts = old_path.split(' > ')
    main_keyword = old_parts[-1] if old_parts else ''

    best_match = None
    best_score = 0

    for new_path, new_cat in new_categories.items():
        new_parts = new_path.split(' > ')
        new_keyword = new_parts[-1] if new_parts else ''

        # Calculate similarity scores
        # Full path similarity
        path_score = similarity(old_path, new_path)

        # Keyword similarity (more weight)
        keyword_score = similarity(main_keyword, new_keyword)

        # Level-by-level similarity
        level_scores = []
        for i in range(min(len(old_parts), len(new_parts))):
            old_level = old_parts[i] if i < len(old_parts) else ''
            new_level = new_parts[i] if i < len(new_parts) else ''
            level_scores.append(similarity(old_level, new_level))

        avg_level_score = sum(level_scores) / len(level_scores) if level_scores else 0

        # Combined score (keyword weighted highest, then levels, then full path)
        final_score = keyword_score * 0.5 + avg_level_score * 0.3 + path_score * 0.2

        if final_score > best_score:
            best_score = final_score
            best_match = (new_path, new_cat, final_score)

    if best_score >= threshold:
        return best_match

    return None


def create_mapping(old_categories: Dict[int, dict], new_categories: Dict[str, dict]) -> List[dict]:
    """Create mapping between old and new categories"""
    print("[3/6] Creating category mappings...")

    mappings = []

    for old_code, old_cat in old_categories.items():
        match = find_best_match(old_cat, new_categories, threshold=0.4)

        if match:
            new_path, new_cat, score = match
            status = 'high_confidence' if score >= 0.7 else 'medium_confidence' if score >= 0.5 else 'low_confidence'
        else:
            new_path = 'UNMAPPED'
            new_cat = {'code': None}
            score = 0.0
            status = 'unmapped'

        mappings.append({
            'old_code': old_code,
            'old_category_path': old_cat['path'],
            'new_code': new_cat['code'],
            'new_category_path': new_path,
            'similarity_score': f"{score:.2%}",
            'match_status': status
        })

    print(f"   Created {len(mappings):,} mappings")
    return mappings


def analyze_and_save(mappings: List[dict]):
    """Analyze mapping results and save to files"""
    print("[4/6] Analyzing mapping results...")

    # Statistics
    total = len(mappings)
    high_conf = sum(1 for m in mappings if m['match_status'] == 'high_confidence')
    medium_conf = sum(1 for m in mappings if m['match_status'] == 'medium_confidence')
    low_conf = sum(1 for m in mappings if m['match_status'] == 'low_confidence')
    unmapped = sum(1 for m in mappings if m['match_status'] == 'unmapped')

    success_rate = ((high_conf + medium_conf) / total * 100) if total > 0 else 0

    print(f"\n{'=' * 80}")
    print("MAPPING STATISTICS")
    print(f"{'=' * 80}")
    print(f"Total categories:        {total:,}")
    print(f"High confidence (≥70%):  {high_conf:,} ({high_conf/total*100:.1f}%)")
    print(f"Medium confidence (50-70%): {medium_conf:,} ({medium_conf/total*100:.1f}%)")
    print(f"Low confidence (40-50%): {low_conf:,} ({low_conf/total*100:.1f}%)")
    print(f"Unmapped (<40%):         {unmapped:,} ({unmapped/total*100:.1f}%)")
    print(f"\nSuccess rate (≥50%):     {success_rate:.1f}%")
    print(f"{'=' * 80}\n")

    # Save CSV
    print("[5/6] Saving CSV file...")
    df = pd.DataFrame(mappings)
    df = df.sort_values('similarity_score', ascending=False)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"   Saved to: {OUTPUT_CSV}")

    # Save JSON
    print("[6/6] Saving JSON file...")
    # Create a more structured JSON for easy lookup
    json_data = {
        'metadata': {
            'total_mappings': total,
            'statistics': {
                'high_confidence': high_conf,
                'medium_confidence': medium_conf,
                'low_confidence': low_conf,
                'unmapped': unmapped,
                'success_rate': f"{success_rate:.1f}%"
            }
        },
        'mappings': {}
    }

    # Index by old code for quick lookup
    for mapping in mappings:
        old_code = str(mapping['old_code'])
        json_data['mappings'][old_code] = {
            'old_category_path': mapping['old_category_path'],
            'new_code': mapping['new_code'],
            'new_category_path': mapping['new_category_path'],
            'similarity_score': mapping['similarity_score'],
            'match_status': mapping['match_status']
        }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"   Saved to: {OUTPUT_JSON}")

    return {
        'total': total,
        'high_confidence': high_conf,
        'medium_confidence': medium_conf,
        'low_confidence': low_conf,
        'unmapped': unmapped,
        'success_rate': success_rate
    }


def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("CATEGORY CODE MAPPING GENERATOR")
    print("=" * 80 + "\n")

    # Check if input files exist
    if not OLD_SYSTEM_FILE.exists():
        print(f"ERROR: Old system file not found: {OLD_SYSTEM_FILE}")
        return 1

    if not NEW_SYSTEM_FILE.exists():
        print(f"ERROR: New system file not found: {NEW_SYSTEM_FILE}")
        return 1

    try:
        # Load categories
        old_categories = load_old_system()
        new_categories = load_new_system()

        # Create mappings
        mappings = create_mapping(old_categories, new_categories)

        # Analyze and save
        stats = analyze_and_save(mappings)

        print("\n" + "=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"\nNext steps:")
        print(f"1. Review the CSV file: {OUTPUT_CSV}")
        print(f"2. Check low confidence mappings and adjust manually if needed")
        print(f"3. Use the JSON file for programmatic access: {OUTPUT_JSON}")
        print(f"\nTo load the JSON in Python:")
        print(f"  import json")
        print(f"  with open('{OUTPUT_JSON}') as f:")
        print(f"      mappings = json.load(f)")
        print(f"  old_code = '123'")
        print(f"  new_info = mappings['mappings'][old_code]")
        print("=" * 80 + "\n")

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
