"""
Transaction Classifier

Auto-classifies transactions into types (HOUSEHOLD/INDIVIDUAL).

Note: Category classification has been removed - fairshare only needs to distinguish
between HOUSEHOLD (shared) and INDIVIDUAL (personal) expenses.
"""

import re
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, List

from models import ExpenseType
from src.learned_classifier import LearnedClassifier


class TransactionClassifier:
    """Classifies transactions based on merchant name and patterns"""

    def __init__(
        self,
        account_id: str,
        learned_rules_path: Optional[Path] = None,
        use_learned: bool = True,
        type_patterns_config: Optional[Dict[str, List[str]]] = None,
        one_time_mappings_path: Optional[Path] = None
    ):
        """
        Initialize classifier with classification rules

        Args:
            account_id: Unique identifier for the account (used for account-specific rules)
            learned_rules_path: Path to learned rules JSON file (optional)
            use_learned: Enable learned classifier (default: True)
            type_patterns_config: Dict with 'household' and 'individual' pattern lists
            one_time_mappings_path: Path to one-time transaction mappings JSON file
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

        # Load one-time transaction mappings
        self.one_time_mappings = {}
        self.one_time_mappings_path = one_time_mappings_path
        if one_time_mappings_path and one_time_mappings_path.exists():
            self._load_one_time_mappings()

    def _load_one_time_mappings(self) -> None:
        """Load one-time transaction mappings from JSON file."""
        import json
        try:
            with open(self.one_time_mappings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Filter for this account's mappings
                self.one_time_mappings = data.get(self.account_id, {})
        except (json.JSONDecodeError, IOError) as e:
            print(f"[!] Warning: Could not load one-time mappings: {e}")
            self.one_time_mappings = {}

    def _save_one_time_mappings(self) -> None:
        """Save one-time transaction mappings to JSON file."""
        import json
        if not self.one_time_mappings_path:
            return

        # Load all accounts' mappings
        all_mappings = {}
        if self.one_time_mappings_path.exists():
            try:
                with open(self.one_time_mappings_path, 'r', encoding='utf-8') as f:
                    all_mappings = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Update this account's mappings
        all_mappings[self.account_id] = self.one_time_mappings

        # Save
        self.one_time_mappings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.one_time_mappings_path, 'w', encoding='utf-8') as f:
            json.dump(all_mappings, indent=2, fp=f)

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
        1. One-time transaction mappings (highest priority) - exact match only
        2. Learned rules (from user corrections) - fuzzy match
        3. Keyword patterns - fallback

        Args:
            description: Transaction description
            amount: Transaction amount
            is_shared_account: True if from shared account
            date: Transaction date (YYYY-MM-DD format) for one-time mappings

        Returns:
            Type string (HOUSEHOLD or INDIVIDUAL)
        """
        # 1. Check one-time mappings first (highest priority)
        if date and self.one_time_mappings:
            txn_key = self._get_transaction_key(date, description, amount)
            if txn_key in self.one_time_mappings:
                return self.one_time_mappings[txn_key]

        # 2. Try learned classifier (second priority)
        if self.learned_classifier:
            learned_result = self.learned_classifier.classify(description)
            if learned_result:
                return learned_result

        # 3. Fall back to keyword-based classification
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
        self._save_one_time_mappings()

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
            self._save_one_time_mappings()
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
