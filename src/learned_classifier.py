"""
Learned Classifier - Learn from user corrections using fuzzy matching.

This module stores user corrections to auto-classifications and uses fuzzy
string matching to apply learned rules to similar transactions.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

from src.models import ExpenseType, DEFAULT_EXPENSE_CATEGORIES


class LearnedClassifier:
    """
    Learns classification rules from user corrections.

    Stores learned rules in JSON format:
    {
        "woolworths rondebosch": {
            "category": "GROCERIES",
            "type": "HOUSEHOLD",
            "count": 5,  # Number of times this correction was made
            "confidence": 100  # Confidence in this rule (100 = user explicitly set it)
        }
    }

    Uses fuzzy matching to handle variations like:
    - "Woolworths Rondebosch" vs "WOOLWORTHS RONDEBOSCH"
    - "Woolworths Rondebosch 123" vs "Woolworths Rondebosch 456"
    - Typos and slight variations
    """

    def __init__(self, learned_rules_path: Path, similarity_threshold: int = 85):
        """
        Initialize learned classifier.

        Args:
            learned_rules_path: Path to JSON file storing learned rules
            similarity_threshold: Minimum fuzzy match score (0-100) to consider a match
        """
        self.rules_path = learned_rules_path
        self.similarity_threshold = similarity_threshold
        self.rules: Dict[str, Dict] = {}
        self._load_rules()

    @staticmethod
    def _normalize_category(category: str) -> Optional[str]:
        """
        Normalize and validate a category string.

        Args:
            category: Category string to normalize

        Returns:
            Normalized category key (e.g., "GROCERIES") or None if invalid
        """
        if not category:
            return None

        # Convert to uppercase and strip whitespace
        category_upper = category.upper().strip().replace(" ", "_")

        # Check if it's already a valid key
        if category_upper in DEFAULT_EXPENSE_CATEGORIES:
            return category_upper

        # Try to find by display name (case-insensitive)
        for key, display_name in DEFAULT_EXPENSE_CATEGORIES.items():
            if display_name.upper() == category_upper.replace("_", " "):
                return key

        # Default to OTHER if not found
        return "OTHER"

    def _load_rules(self) -> None:
        """Load learned rules from JSON file."""
        if self.rules_path.exists():
            try:
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[!] Warning: Could not load learned rules: {e}")
                self.rules = {}
        else:
            self.rules = {}

    def _save_rules(self) -> None:
        """Save learned rules to JSON file."""
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rules_path, 'w', encoding='utf-8') as f:
            json.dump(self.rules, indent=2, fp=f)

    def classify(self, description: str) -> Optional[Tuple[str, str]]:
        """
        Classify a transaction using learned rules with fuzzy matching.

        Args:
            description: Transaction description

        Returns:
            Tuple of (category, type) if match found, None otherwise
        """
        if not self.rules:
            return None

        # Normalize description for matching
        normalized = description.lower().strip()

        # Try exact match first (fastest)
        if normalized in self.rules:
            rule = self.rules[normalized]
            return (rule['category'], rule['type'])

        # Try fuzzy match
        match = process.extractOne(
            normalized,
            self.rules.keys(),
            scorer=fuzz.ratio,
            score_cutoff=self.similarity_threshold
        )

        if match:
            matched_key, score, _ = match
            rule = self.rules[matched_key]
            return (rule['category'], rule['type'])

        return None

    def learn_from_corrections(
        self,
        transaction_file: Path,
        verbose: bool = True
    ) -> Dict[str, int]:
        """
        Learn from user corrections in a transaction file.

        Args:
            transaction_file: Path to Excel file with user corrections
            verbose: Print progress messages

        Returns:
            Dictionary with statistics: {'new_rules': X, 'updated_rules': Y}
        """
        if not transaction_file.exists():
            raise FileNotFoundError(f"Transaction file not found: {transaction_file}")

        # Read transaction file
        df = pd.read_excel(transaction_file)

        # Find rows with user corrections
        # User corrections are where user_category or user_type is not empty
        has_category_correction = df['user_category'].notna() & (df['user_category'] != '')
        has_type_correction = df['user_type'].notna() & (df['user_type'] != '')
        corrections = df[has_category_correction | has_type_correction].copy()

        if len(corrections) == 0:
            if verbose:
                print(f"  No user corrections found in {transaction_file.name}")
            return {'new_rules': 0, 'updated_rules': 0}

        new_rules = 0
        updated_rules = 0

        for _, row in corrections.iterrows():
            description = str(row['description']).lower().strip()

            # Get final category and type (user override takes priority)
            category = row['user_category'] if pd.notna(row['user_category']) and row['user_category'] != '' else row['auto_category']
            exp_type = row['user_type'] if pd.notna(row['user_type']) and row['user_type'] != '' else row['auto_type']

            # Normalize and validate category
            normalized_category = self._normalize_category(category)
            if not normalized_category:
                if verbose:
                    print(f"  [!] Skipping invalid category: {category}")
                continue
            category = normalized_category

            # Normalize and validate expense type (handle both "HOUSEHOLD" and "Household")
            exp_type_normalized = exp_type.upper().replace(" ", "_")
            try:
                ExpenseType[exp_type_normalized]
                exp_type = exp_type_normalized
            except KeyError:
                if verbose:
                    print(f"  [!] Skipping invalid expense type: {exp_type}")
                continue

            # Check if rule exists
            if description in self.rules:
                # Update existing rule
                existing = self.rules[description]
                if existing['category'] != category or existing['type'] != exp_type:
                    # User changed their mind, update the rule
                    self.rules[description] = {
                        'category': category,
                        'type': exp_type,
                        'count': existing.get('count', 1) + 1,
                        'confidence': 100
                    }
                    updated_rules += 1
                else:
                    # Same rule, just increment count
                    existing['count'] = existing.get('count', 1) + 1
            else:
                # New rule
                self.rules[description] = {
                    'category': category,
                    'type': exp_type,
                    'count': 1,
                    'confidence': 100
                }
                new_rules += 1

        # Save updated rules
        self._save_rules()

        if verbose:
            print(f"  Learned from {len(corrections)} corrections")
            if new_rules > 0:
                print(f"    [+] {new_rules} new rules")
            if updated_rules > 0:
                print(f"    [~] {updated_rules} updated rules")
            print(f"  Total rules: {len(self.rules)}")

        return {'new_rules': new_rules, 'updated_rules': updated_rules}

    def learn_from_all_files(
        self,
        transaction_files: list[Path],
        verbose: bool = True
    ) -> Dict[str, int]:
        """
        Learn from user corrections across multiple transaction files.

        Args:
            transaction_files: List of Excel transaction files
            verbose: Print progress messages

        Returns:
            Dictionary with combined statistics
        """
        total_new = 0
        total_updated = 0

        for file_path in transaction_files:
            if verbose:
                print(f"\nProcessing: {file_path.name}")

            stats = self.learn_from_corrections(file_path, verbose=verbose)
            total_new += stats['new_rules']
            total_updated += stats['updated_rules']

        return {'new_rules': total_new, 'updated_rules': total_updated}

    def get_statistics(self) -> Dict:
        """Get statistics about learned rules."""
        if not self.rules:
            return {
                'total_rules': 0,
                'categories': {},
                'types': {}
            }

        categories = {}
        types = {}

        for rule in self.rules.values():
            cat = rule['category']
            typ = rule['type']
            categories[cat] = categories.get(cat, 0) + 1
            types[typ] = types.get(typ, 0) + 1

        return {
            'total_rules': len(self.rules),
            'categories': categories,
            'types': types
        }

    def export_rules(self, output_file: Path) -> None:
        """
        Export learned rules to an Excel file for review.

        Args:
            output_file: Path to output Excel file
        """
        if not self.rules:
            print("  No learned rules to export")
            return

        data = []
        for description, rule in sorted(self.rules.items()):
            data.append({
                'description': description,
                'category': rule['category'],
                'type': rule['type'],
                'count': rule.get('count', 1),
                'confidence': rule.get('confidence', 100)
            })

        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"  Exported {len(data)} rules to: {output_file}")

    def apply_to_transactions(
        self,
        transaction_file: Path,
        verbose: bool = True
    ) -> Dict[str, int]:
        """
        Apply learned rules to re-classify transactions in an existing file.

        This updates the auto_category and auto_type columns based on learned rules,
        while preserving any user_category and user_type corrections.

        Args:
            transaction_file: Path to Excel file with transactions
            verbose: Print progress messages

        Returns:
            Dictionary with statistics: {'reclassified': X, 'unchanged': Y}
        """
        if not transaction_file.exists():
            raise FileNotFoundError(f"Transaction file not found: {transaction_file}")

        if not self.rules:
            if verbose:
                print(f"  No learned rules available - skipping {transaction_file.name}")
            return {'reclassified': 0, 'unchanged': 0}

        # Read transaction file
        df = pd.read_excel(transaction_file)

        reclassified = 0
        unchanged = 0

        for idx, row in df.iterrows():
            description = str(row['description'])

            # Try to classify using learned rules
            result = self.classify(description)

            if result:
                new_category, new_type = result
                old_category = row['auto_category']
                old_type = row['auto_type']
                old_final_category = row['final_category']
                old_final_type = row['final_type']

                # Calculate what final values should be
                user_cat = row['user_category']
                user_typ = row['user_type']

                # Determine correct final_category
                if pd.isna(user_cat) or user_cat == '':
                    correct_final_category = new_category
                else:
                    # User has override - normalize it to ensure it's in key format
                    normalized_user_cat = self._normalize_category(user_cat)
                    correct_final_category = normalized_user_cat if normalized_user_cat else new_category

                # Determine correct final_type
                if pd.isna(user_typ) or user_typ == '':
                    correct_final_type = new_type
                else:
                    # User has override - normalize it
                    normalized_user_typ = user_typ.upper().replace(" ", "_")
                    try:
                        ExpenseType[normalized_user_typ]
                        correct_final_type = normalized_user_typ
                    except KeyError:
                        correct_final_type = new_type

                # Check if any values need updating
                needs_update = (
                    old_category != new_category or
                    old_type != new_type or
                    old_final_category != correct_final_category or
                    old_final_type != correct_final_type
                )

                if needs_update:
                    df.at[idx, 'auto_category'] = new_category
                    df.at[idx, 'auto_type'] = new_type
                    df.at[idx, 'final_category'] = correct_final_category
                    df.at[idx, 'final_type'] = correct_final_type
                    reclassified += 1
                else:
                    unchanged += 1
            else:
                unchanged += 1

        if reclassified > 0:
            # Save updated file
            df.to_excel(transaction_file, index=False)
            if verbose:
                print(f"  {transaction_file.name}: {reclassified} reclassified, {unchanged} unchanged")

        return {'reclassified': reclassified, 'unchanged': unchanged}

    def apply_to_all_files(
        self,
        transaction_files: list[Path],
        verbose: bool = True
    ) -> Dict[str, int]:
        """
        Apply learned rules to multiple transaction files.

        Args:
            transaction_files: List of Excel transaction files
            verbose: Print progress messages

        Returns:
            Dictionary with combined statistics
        """
        total_reclassified = 0
        total_unchanged = 0
        files_updated = 0

        for file_path in transaction_files:
            if verbose:
                print(f"\nProcessing: {file_path.parent.name}/{file_path.name}")

            stats = self.apply_to_transactions(file_path, verbose=verbose)
            total_reclassified += stats['reclassified']
            total_unchanged += stats['unchanged']

            if stats['reclassified'] > 0:
                files_updated += 1

        return {
            'reclassified': total_reclassified,
            'unchanged': total_unchanged,
            'files_updated': files_updated
        }
