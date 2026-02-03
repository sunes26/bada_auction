import json

with open('category_code_mapping.json', encoding='utf-8') as f:
    data = json.load(f)

print('Metadata:')
for key, value in data['metadata'].items():
    print(f'  {key}: {value}')

print('\nSample mapping (old_code 100300):')
if '100300' in data['mappings']:
    mapping = data['mappings']['100300']
    for key, value in mapping.items():
        print(f'  {key}: {value}')

print(f'\nTotal mappings in JSON: {len(data["mappings"]):,}')

# Show a few high confidence mappings
print('\nSample high confidence codes:')
count = 0
for code, mapping in data['mappings'].items():
    if mapping['match_status'] == 'high_confidence' and count < 5:
        print(f'\nOld code {code}:')
        print(f'  Old path: {mapping["old_category_path"]}')
        print(f'  New code: {mapping["new_code"]}')
        print(f'  New path: {mapping["new_category_path"]}')
        print(f'  Similarity: {mapping["similarity_score"]}')
        count += 1
