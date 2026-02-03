#!/usr/bin/env python3
"""Quick test of category mapping"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OLD_FILE = PROJECT_ROOT / "Standard_category_list.xlsx"
NEW_FILE = PROJECT_ROOT / "category.xlsx"

print("Testing category file loading...")
print()

# Test old file
print("1. Loading Standard_category_list.xlsx...")
old_df = pd.read_excel(OLD_FILE, engine='openpyxl')
old_df.columns = ['category_code', 'level1', 'level2', 'level3', 'level4']
print(f"   Loaded: {len(old_df)} rows")
print(f"   Sample row 0: code={old_df.iloc[0]['category_code']}, path={old_df.iloc[0]['level1']} > {old_df.iloc[0]['level2']}")
print()

# Test new file
print("2. Loading category.xlsx...")
new_df = pd.read_excel(NEW_FILE, engine='openpyxl')
new_df.columns = ['category_code', 'classification', 'category_path']
print(f"   Loaded: {len(new_df)} rows")
print(f"   Sample row 0: code={new_df.iloc[0]['category_code']}, path={new_df.iloc[0]['category_path']}")
print()

print("SUCCESS: Both files loaded correctly!")
