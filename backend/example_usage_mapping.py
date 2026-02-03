#!/usr/bin/env python3
"""
Example Usage: Category Code Mapping

This script demonstrates how to use the category_code_mapping files
to translate old category codes to new category codes.
"""
import json
import pandas as pd
from pathlib import Path

# File paths
MAPPING_JSON = Path(__file__).parent / "category_code_mapping.json"
MAPPING_CSV = Path(__file__).parent / "category_code_mapping.csv"


class CategoryMapper:
    """Helper class to map old category codes to new ones"""

    def __init__(self, json_path=MAPPING_JSON):
        """Load the mapping data"""
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.mappings = self.data['mappings']
        self.metadata = self.data['metadata']

    def get_new_code(self, old_code):
        """
        Get new category code from old category code

        Args:
            old_code: Old category code (int or str)

        Returns:
            New category code (int) or None if unmapped
        """
        old_code_str = str(old_code)
        if old_code_str in self.mappings:
            return self.mappings[old_code_str]['new_code']
        return None

    def get_mapping_info(self, old_code):
        """
        Get complete mapping information for an old code

        Args:
            old_code: Old category code (int or str)

        Returns:
            dict with mapping details or None if not found
        """
        old_code_str = str(old_code)
        if old_code_str in self.mappings:
            return self.mappings[old_code_str]
        return None

    def get_statistics(self):
        """Get mapping statistics"""
        return self.metadata['statistics']


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("CATEGORY CODE MAPPING - USAGE EXAMPLES")
    print("=" * 80)
    print()

    # Initialize mapper
    mapper = CategoryMapper()

    # Example 1: Get new code from old code
    print("Example 1: Map old code to new code")
    print("-" * 80)
    old_code = 23110300
    new_code = mapper.get_new_code(old_code)
    print(f"Old code: {old_code}")
    print(f"New code: {new_code}")
    print()

    # Example 2: Get complete mapping info
    print("Example 2: Get complete mapping information")
    print("-" * 80)
    old_code = 58031000
    info = mapper.get_mapping_info(old_code)
    if info:
        print(f"Old code: {old_code}")
        print(f"Old category: {info['old_category_path']}")
        print(f"New code: {info['new_code']}")
        print(f"New category: {info['new_category_path']}")
        print(f"Similarity: {info['similarity_score']}")
        print(f"Match status: {info['match_status']}")
    print()

    # Example 3: Handle unmapped categories
    print("Example 3: Handle unmapped category")
    print("-" * 80)
    old_code = 100300  # This one is unmapped
    info = mapper.get_mapping_info(old_code)
    if info:
        print(f"Old code: {old_code}")
        print(f"Old category: {info['old_category_path']}")
        print(f"Match status: {info['match_status']}")
        if info['match_status'] == 'unmapped':
            print(f"Note: This category needs manual mapping!")
    print()

    # Example 4: Get statistics
    print("Example 4: View mapping statistics")
    print("-" * 80)
    stats = mapper.get_statistics()
    print(f"High confidence mappings: {stats['high_confidence']}")
    print(f"Medium confidence mappings: {stats['medium_confidence']}")
    print(f"Low confidence mappings: {stats['low_confidence']}")
    print(f"Unmapped categories: {stats['unmapped']}")
    print(f"Success rate: {stats['success_rate']}")
    print()

    # Example 5: Batch processing with CSV
    print("Example 5: Batch process using CSV")
    print("-" * 80)
    df = pd.read_csv(MAPPING_CSV)

    # Get all high confidence mappings
    high_conf = df[df['match_status'] == 'high_confidence']
    print(f"Found {len(high_conf)} high confidence mappings")

    # Get all unmapped that need manual review
    unmapped = df[df['match_status'] == 'unmapped']
    print(f"Found {len(unmapped)} unmapped categories needing manual review")

    # Filter by similarity score
    good_matches = df[df['similarity_score'].str.rstrip('%').astype(float) >= 60.0]
    print(f"Found {len(good_matches)} mappings with ≥60% similarity")
    print()

    # Example 6: Create a lookup dictionary for fast access
    print("Example 6: Create fast lookup dictionary")
    print("-" * 80)
    # For high-confidence mappings only
    lookup = {
        int(row['old_code']): int(row['new_code'])
        for _, row in df[df['match_status'] == 'high_confidence'].iterrows()
        if pd.notna(row['new_code'])
    }
    print(f"Created lookup dictionary with {len(lookup)} entries")
    print(f"Example lookup: {23110300} -> {lookup.get(23110300)}")
    print()

    print("=" * 80)
    print("For more information, see:")
    print(f"  - CSV file: {MAPPING_CSV}")
    print(f"  - JSON file: {MAPPING_JSON}")
    print("=" * 80)
