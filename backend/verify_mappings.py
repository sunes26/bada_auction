import json
import pandas as pd

# Verify CSV
csv_df = pd.read_csv('category_code_mapping.csv')
print('CSV FILE VERIFICATION')
print('=' * 60)
print(f'Total rows: {len(csv_df):,}')
print(f'Columns: {list(csv_df.columns)}')
print()

# Verify JSON
with open('category_code_mapping.json', encoding='utf-8') as f:
    json_data = json.load(f)

print('JSON FILE VERIFICATION')
print('=' * 60)
print(f'Total mappings: {len(json_data["mappings"]):,}')
print(f'Metadata keys: {list(json_data["metadata"].keys())}')
print()

print('MAPPING STATISTICS')
print('=' * 60)
print(f'Total categories:     {json_data["metadata"]["total_mappings"]:,}')
stats = json_data['metadata']['statistics']
for key, val in stats.items():
    print(f'{key:25s} {val}')
print()

print('SAMPLE MAPPINGS')
print('=' * 60)
print('\nHigh confidence (first 3):')
high_conf = csv_df[csv_df['match_status'] == 'high_confidence'].head(3)
for idx, row in high_conf.iterrows():
    print(f"\nOld: {row['old_code']} - {row['old_category_path']}")
    print(f"New: {row['new_code']} - {row['new_category_path']}")
    print(f"Similarity: {row['similarity_score']}")

print('\n\nUnmapped (first 3):')
unmapped = csv_df[csv_df['match_status'] == 'unmapped'].head(3)
for idx, row in unmapped.iterrows():
    print(f"\nOld: {row['old_code']} - {row['old_category_path']}")
    print(f"Status: {row['match_status']}")
