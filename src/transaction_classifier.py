"""
Transaction Classifier

Auto-classifies transactions into types (HOUSEHOLD/INDIVIDUAL).

Note: Category classification has been removed - fairshare only needs to distinguish
between HOUSEHOLD (shared) and INDIVIDUAL (personal) expenses.

Now supports split mappings - transactions that should be split between HOUSEHOLD and INDIVIDUAL.

REFACTORED: Uses JsonRepository for one_time_mappings and split_mappings persistence.
"""

import re
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict

from src.models import ExpenseType
from src.learned_classifier import LearnedClassifier
from src.utils import JsonRepository


@dataclass
class SplitPart:
    """Represents one part of a split transaction."""
    expense_type: str  # HOUSEHOLD or INDIVIDUAL
    amount: Decimal
    note: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.expense_type,
            'amount': str(self.amount),
            'note': self.note
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SplitPart':
        """Create from dictionary."""
        return cls(
            expense_type=data['type'],
            amount=Decimal(data['amount']),
            note=data.get('note', '')
        )


class TransactionClassifier:
    """Classifies transactions based on merchant name and patterns"""

    def __init__(
        self,
        account_id: str,
        learned_rules_path: Optional[Path] = None,
        use_learned: bool = True,
        type_patterns_config: Optional[Dict[str, List[str]]] = None,
        one_time_mappings_path: Optional[Path] = None,
        split_mappings_path: Optional[Path] = None
    ):
        """
        Initialize classifier with classification rules

        Args:
            account_id: Unique identifier for the account (used for account-specific rules)
            learned_rules_path: Path to learned rules JSON file (optional)
            use_learned: Enable learned classifier (default: True)
            type_patterns_config: Dict with 'household' and 'individual' pattern lists
            one_time_mappings_path: Path to one-time transaction mappings JSON file
            split_mappings_path: Path to split transaction mappings JSON file
        """
        self.account_id = account_id

        # Initialize learned classifier if enabled (account-specific)
        self.use_learned = use_learned
        if use_learned and learned_rules_path:
            self.learned_classifier = LearnedClassifier(
                learned_rules_path,
                account_id=account_id
            )
        else:
            self.learned_classifier = None

        # Patterns for determining if household or individual (account-specific)
        # These can be customized per account via config
        if type_patterns_config:
            self.household_patterns = type_patterns_config.get('household', [])
            self.individual_patterns = type_patterns_config.get('individual', [])
        else:
            # Default patterns (can be overridden via config)
            self.household_patterns = [
                r"(?i)(groceries|spar|woolworths|checkers)",
                r"(?i)(electricity|water|rates|levies)",
                r"(?i)(internet|dstv|netflix)",
                r"(?i)(restaurant|takeaway|uber\s*eats)",
            ]

            self.individual_patterns = [
                r"(?i)(pharmacy.*prescription)",
                r"(?i)(clothing|fashion)",
                r"(?i)(personal|private)",
                r"(?i)(gym|fitness)",
            ]

        # Use JsonRepository for one-time mappings (account-scoped)
        if one_time_mappings_path:
            self.one_time_repo = JsonRepository(one_time_mappings_path, account_id)
            self.one_time_mappings = self.one_time_repo.data
        else:
            self.one_time_repo = None
            self.one_time_mappings = {}

        # Use JsonRepository for split mappings (account-scoped)
        # Note: Split mappings need special handling for SplitPart objects
        if split_mappings_path:
            self.split_repo = JsonRepository(split_mappings_path, account_id)
            # Convert stored dicts to SplitPart objects
            self.split_mappings = {}
            for txn_key, split_data in self.split_repo.data.items():
                self.split_mappings[txn_key] = [
                    SplitPart.from_dict(part) for part in split_data
                ]
        else:
            self.split_repo = None
            self.split_mappings = {}

    def _get_transaction_key(
        self, date: str, description: str, amount: Decimal
    ) -> str:
        """
        Create a unique key for a transaction.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount

        Returns:
            Unique key string
        """
        return f"{date}|{description.lower().strip()}|{amount}"

    def classify_type(
        self, description: str, amount: Decimal, is_shared_account: bool = False
    ) -> ExpenseType:
        """
        Classify transaction type (HOUSEHOLD or INDIVIDUAL)

        Args:
            description: Transaction description
            amount: Transaction amount
            is_shared_account: True if from shared account (e.g., credit card)

        Returns:
            ExpenseType enum value
        """
        # Shared accounts default to HOUSEHOLD unless specifically individual
        if is_shared_account:
            # Check for individual patterns
            for pattern in self.individual_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return ExpenseType.INDIVIDUAL

            return ExpenseType.HOUSEHOLD

        # Personal accounts: check for household patterns
        for pattern in self.household_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return ExpenseType.HOUSEHOLD

        # Default to INDIVIDUAL for personal accounts
        return ExpenseType.INDIVIDUAL

    def classify_transaction(
        self,
        description: str,
        amount: Decimal,
        is_shared_account: bool = False,
        date: Optional[str] = None
    ) -> str:
        """
        Classify transaction type (HOUSEHOLD or INDIVIDUAL)

        Priority order:
        1. Split mappings (highest priority) - returns "SPLIT" if transaction should be split
        2. One-time transaction mappings - exact match only
        3. Learned rules (from user corrections) - fuzzy match
        4. Keyword patterns - fallback

        Note: If this returns "SPLIT", use get_split_mapping() to get the split parts.

        Args:
            description: Transaction description
            amount: Transaction amount
            is_shared_account: True if from shared account
            date: Transaction date (YYYY-MM-DD format) for mappings

        Returns:
            Type string (HOUSEHOLD, INDIVIDUAL, or SPLIT)
        """
        # 1. Check split mappings first (highest priority)
        if date and self.split_mappings:
            txn_key = self._get_transaction_key(date, description, amount)
            if txn_key in self.split_mappings:
                return "SPLIT"

        # 2. Check one-time mappings (second priority)
        if date and self.one_time_mappings:
            txn_key = self._get_transaction_key(date, description, amount)
            if txn_key in self.one_time_mappings:
                return self.one_time_mappings[txn_key]

        # 3. Try learned classifier (third priority)
        if self.learned_classifier:
            learned_result = self.learned_classifier.classify(description)
            if learned_result:
                return learned_result

        # 4. Fall back to keyword-based classification
        expense_type = self.classify_type(description, amount, is_shared_account)
        return expense_type.name

    def add_one_time_mapping(
        self,
        date: str,
        description: str,
        amount: Decimal,
        expense_type: str
    ) -> None:
        """
        Add a one-time transaction mapping for a specific transaction.

        This mapping will only apply to this exact transaction (date + description + amount).

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount
            expense_type: Type to assign (HOUSEHOLD or INDIVIDUAL)
        """
        txn_key = self._get_transaction_key(date, description, amount)
        self.one_time_mappings[txn_key] = expense_type
        if self.one_time_repo:
            self.one_time_repo.save()

    def remove_one_time_mapping(
        self, date: str, description: str, amount: Decimal
    ) -> bool:
        """
        Remove a one-time transaction mapping.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount

        Returns:
            True if mapping was removed, False if it didn't exist
        """
        txn_key = self._get_transaction_key(date, description, amount)
        if txn_key in self.one_time_mappings:
            del self.one_time_mappings[txn_key]
            if self.one_time_repo:
                self.one_time_repo.save()
            return True
        return False

    def get_one_time_mapping(
        self, date: str, description: str, amount: Decimal
    ) -> Optional[str]:
        """
        Get the one-time mapping for a specific transaction.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount

        Returns:
            Expense type (HOUSEHOLD or INDIVIDUAL) if mapping exists, None otherwise
        """
        txn_key = self._get_transaction_key(date, description, amount)
        return self.one_time_mappings.get(txn_key)

    def add_split_mapping(
        self,
        date: str,
        description: str,
        amount: Decimal,
        split_parts: List[SplitPart]
    ) -> None:
        """
        Add a split mapping for a specific transaction.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount
            split_parts: List of SplitPart objects defining the split
        """
        # Validate that split parts sum to total amount
        total = sum(part.amount for part in split_parts)
        if total != amount:
            raise ValueError(
                f"Split parts total ({total}) does not match transaction amount ({amount})"
            )

        txn_key = self._get_transaction_key(date, description, amount)
        self.split_mappings[txn_key] = split_parts

        # Save to repo (convert SplitPart objects to dicts)
        if self.split_repo:
            self.split_repo.data[txn_key] = [part.to_dict() for part in split_parts]
            self.split_repo.save()

    def remove_split_mapping(
        self, date: str, description: str, amount: Decimal
    ) -> bool:
        """
        Remove a split mapping.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount

        Returns:
            True if mapping was removed, False if it didn't exist
        """
        txn_key = self._get_transaction_key(date, description, amount)
        if txn_key in self.split_mappings:
            del self.split_mappings[txn_key]
            if self.split_repo:
                self.split_repo.delete(txn_key)
            return True
        return False

    def get_split_mapping(
        self, date: str, description: str, amount: Decimal
    ) -> Optional[List[SplitPart]]:
        """
        Get the split mapping for a specific transaction.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount

        Returns:
            List of SplitPart objects if mapping exists, None otherwise
        """
        txn_key = self._get_transaction_key(date, description, amount)
        return self.split_mappings.get(txn_key)

    def has_split_mapping(
        self, date: str, description: str, amount: Decimal
    ) -> bool:
        """
        Check if a transaction has a split mapping.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount

        Returns:
            True if split mapping exists, False otherwise
        """
        txn_key = self._get_transaction_key(date, description, amount)
        return txn_key in self.split_mappings

    def expand_transaction_if_split(
        self,
        date: str,
        description: str,
        amount: Decimal,
        **other_fields
    ) -> List[Dict]:
        """
        Expand a transaction into multiple parts if it has a split mapping.

        Args:
            date: Transaction date (YYYY-MM-DD format)
            description: Transaction description
            amount: Transaction amount
            **other_fields: Other transaction fields to preserve (e.g., category, account)

        Returns:
            List of transaction dictionaries. If no split mapping exists, returns
            a single-item list with the original transaction. If split mapping exists,
            returns multiple transaction dictionaries with split amounts.
        """
        # Check if transaction has a split mapping
        split_parts = self.get_split_mapping(date, description, amount)

        if not split_parts:
            # No split mapping - return original transaction as single-item list
            return [{
                'date': date,
                'description': description,
                'amount': amount,
                **other_fields
            }]

        # Has split mapping - expand into multiple transactions
        transactions = []
        for idx, part in enumerate(split_parts, 1):
            split_desc = f"{description} ({idx}/{len(split_parts)})"
            if part.note:
                split_desc += f" - {part.note}"

            transactions.append({
                'date': date,
                'description': split_desc,
                'amount': part.amount,
                'type': part.expense_type,
                'split_id': f"{date}_{description}_{amount}",  # Common ID for all parts
                'split_part': f"{idx}/{len(split_parts)}",
                **other_fields
            })

        return transactions

    def add_custom_pattern(
        self, pattern: str, expense_type: ExpenseType
    ):
        """
        Add a custom classification pattern

        Args:
            pattern: Regex pattern to match
            expense_type: Type to assign (HOUSEHOLD/INDIVIDUAL)
        """
        if expense_type == ExpenseType.HOUSEHOLD:
            self.household_patterns.append(pattern)
        elif expense_type == ExpenseType.INDIVIDUAL:
            self.individual_patterns.append(pattern)
