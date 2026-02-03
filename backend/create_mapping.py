#!/usr/bin/env python3
"""
Simplified Category Code Mapping Generator
Creates mapping between old and new category systems
"""
import pandas as pd
import json
from pathlib import Path
from difflib import SequenceMatcher

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OLD_FILE = PROJECT_ROOT / "Standard_category_list.xlsx"
NEW_FILE = PROJECT_ROOT / "category.xlsx"
OUTPUT_CSV = PROJECT_ROOT / "backend" / "category_code_mapping.csv"
OUTPUT_JSON = PROJECT_ROOT / "backend" / "category_code_mapping.json"


def similarity(a, b):
    """Calculate string similarity (0-1)"""
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def build_path(parts):
    """Build category path from parts"""
    return " > ".join([str(p) for p in parts if pd.notna(p) and str(p) != 'nan'])


print("=" * 80)
print("CATEGORY CODE MAPPING GENERATOR")
print("=" * 80)
print()

# Load old system
print("[1/6] Loading old system (Standard_category_list.xlsx)...")
old_df = pd.read_excel(OLD_FILE, engine='openpyxl')
old_df.columns = ['code', 'l1', 'l2', 'l3', 'l4']
old_df['path'] = old_df.apply(lambda r: build_path([r['l1'], r['l2'], r['l3'], r['l4']]), axis=1)
print(f"   Loaded {len(old_df):,} categories")

# Load new system
print("[2/6] Loading new system (category.xlsx)...")
new_df = pd.read_excel(NEW_FILE, engine='openpyxl')
new_df.columns = ['code', 'classification', 'path']
print(f"   Loaded {len(new_df):,} categories")

# Create mapping
print("[3/6] Creating mappings...")
mappings = []

for idx, old_row in old_df.iterrows():
    if idx % 1000 == 0:
        print(f"   Processing {idx:,}/{len(old_df):,}...")

    old_code = int(old_row['code'])
    old_path = old_row['path']

    # Find best match in new system
    best_score = 0
    best_new_code = None
    best_new_path = 'UNMAPPED'

    for _, new_row in new_df.iterrows():
        new_code = int(new_row['code'])
        new_path = new_row['path']

        # Calculate similarity
        score = similarity(old_path, new_path)

        # Also check last part (most specific level)
        old_parts = old_path.split(' > ')
        new_parts = new_path.split(' > ')
        if old_parts and new_parts:
            last_score = similarity(old_parts[-1], new_parts[-1])
            # Weighted score: 70% last level, 30% full path
            score = last_score * 0.7 + score * 0.3

        if score > best_score:
            best_score = score
            best_new_code = new_code
            best_new_path = new_path

    # Determine match status
    if best_score >= 0.7:
        status = 'high_confidence'
    elif best_score >= 0.5:
        status = 'medium_confidence'
    elif best_score >= 0.4:
        status = 'low_confidence'
    else:
        status = 'unmapped'
        best_new_code = None
        best_new_path = 'UNMAPPED'

    mappings.append({
        'old_code': old_code,
        'old_category_path': old_path,
        'new_code': best_new_code,
        'new_category_path': best_new_path,
        'similarity_score': f"{best_score:.2%}",
        'match_status': status
    })

print(f"   Created {len(mappings):,} mappings")

# Calculate statistics
print("[4/6] Analyzing results...")
total = len(mappings)
high = sum(1 for m in mappings if m['match_status'] == 'high_confidence')
medium = sum(1 for m in mappings if m['match_status'] == 'medium_confidence')
low = sum(1 for m in mappings if m['match_status'] == 'low_confidence')
unmapped = sum(1 for m in mappings if m['match_status'] == 'unmapped')
success_rate = ((high + medium) / total * 100) if total > 0 else 0

print()
print("=" * 80)
print("STATISTICS")
print("=" * 80)
print(f"Total:               {total:,}")
print(f"High conf (>=70%):   {high:,} ({high/total*100:.1f}%)")
print(f"Medium conf (50-70%): {medium:,} ({medium/total*100:.1f}%)")
print(f"Low conf (40-50%):   {low:,} ({low/total*100:.1f}%)")
print(f"Unmapped (<40%):     {unmapped:,} ({unmapped/total*100:.1f}%)")
print(f"Success rate:        {success_rate:.1f}%")
print("=" * 80)
print()

# Save CSV
print("[5/6] Saving CSV...")
df_out = pd.DataFrame(mappings)
df_out = df_out.sort_values('similarity_score', ascending=False)
df_out.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"   Saved: {OUTPUT_CSV}")

# Save JSON
print("[6/6] Saving JSON...")
json_data = {
    'metadata': {
        'total': total,
        'high_confidence': high,
        'medium_confidence': medium,
        'low_confidence': low,
        'unmapped': unmapped,
        'success_rate': f"{success_rate:.1f}%"
    },
    'mappings': {str(m['old_code']): {
        'old_category_path': m['old_category_path'],
        'new_code': m['new_code'],
        'new_category_path': m['new_category_path'],
        'similarity_score': m['similarity_score'],
        'match_status': m['match_status']
    } for m in mappings}
}

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
print(f"   Saved: {OUTPUT_JSON}")

print()
print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"\nOutput files:")
print(f"  CSV: {OUTPUT_CSV}")
print(f"  JSON: {OUTPUT_JSON}")
print()
