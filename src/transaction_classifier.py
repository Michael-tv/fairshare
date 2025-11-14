"""
Transaction Classifier

Auto-classifies transactions into categories and types (SHARED/INDIVIDUAL).
"""

import re
from decimal import Decimal
from pathlib import Path
from typing import Optional, Tuple

from models import ExpenseType
from src.learned_classifier import LearnedClassifier


class TransactionClassifier:
    """Classifies transactions based on merchant name and patterns"""

    def __init__(
        self,
        learned_rules_path: Optional[Path] = None,
        use_learned: bool = True
    ):
        """
        Initialize classifier with classification rules

        Args:
            learned_rules_path: Path to learned rules JSON file (optional)
            use_learned: Enable learned classifier (default: True)
        """
        # Initialize learned classifier if enabled
        self.use_learned = use_learned
        if use_learned and learned_rules_path:
            self.learned_classifier = LearnedClassifier(learned_rules_path)
        else:
            self.learned_classifier = None

        # Merchant patterns for category classification (using string keys now)
        self.category_patterns = {
            "GROCERIES": [
                r"(?i)(spar|woolworths|checkers|pick\s*n\s*pay|pnp|makro|food|supermarket|grocery)",
                r"(?i)(fruit|veg|fresh|tops)",
            ],
            "FUEL": [
                r"(?i)(engen|shell|bp|sasol|total|caltex|fuel|petrol|diesel)",
            ],
            "ENTERTAINMENT": [
                r"(?i)(cinema|movie|netflix|dstv|spotify|showmax|mnet|zoo)",
                r"(?i)(restaurant|cafe|coffee|pizza|burger|sushi)",
                r"(?i)(bar|pub|entertainment)",
            ],
            "UTILITIES": [
                r"(?i)(electricity|water|municipal|city\s*of)",
                r"(?i)(internet|wifi|afrihost|mweb|telkom|vodacom|mtn|cell\s*c|payfast|gas)",
            ],
            "INSURANCE": [
                r"(?i)(insurance|insure|outsurance|discovery|momentum)",
            ],
            "MEDICAL_AID": [
                r"(?i)(pharmacy|chemist|clicks|dis-chem|medicross)",
                r"(?i)(doctor|dr\s|drs\s|hospital|clinic|medical|gap\s*cover)",
                r"(?i)(dentist|optometrist|animal)",
            ],
            "CLOTHING": [
                r"(?i)(clothing|fashion|edgars|truworths|mr\s*price|ackermans|shoes|baby\s*city)",
                r"(?i)(sport\s*scene|nike|adidas|puma)",
            ],
            "HOUSEHOLD": [
                r"(?i)(game|builders|leroy|cashbuild|hardware|mica|chamberlain)",
                r"(?i)(home|furniture|@home|crazy\s*plastics|outdoor|4x4)",
            ],
            "TRANSPORT": [
                r"(?i)(uber|bolt|taxi)",
                r"(?i)(toll|parking|plaza)",
                r"(?i)(car\s*wash|service)",
            ],
            "SCHOOL_FEES": [
                r"(?i)(school|university|college|tuition|fees)",
                r"(?i)(book|stationery)",
            ],
            "SUBSCRIPTIONS": [
                r"(?i)(netflix|dstv|subscription|spotify|showmax)",
            ],
            "LEVIES": [
                r"(?i)(levie|levy)",
            ],
            "RATES": [
                r"(?i)(rates)",
            ],
            "DOMESTIC_HELP": [
                r"(?i)(cleaning|cleaner|garden|domestic|petrus|marta)",
            ],
            "MAINTENANCE": [
                r"(?i)(maintenance|repair)",
            ],
            "BANK_CHARGES": [
                r"(?i)(bank|account\s*fee|fnb|absa)",
            ],
            "LOANS": [
                r"(?i)(bond|loan|finance|mortgage)",
            ],
            "TAX": [
                r"(?i)(tax|paye)",
            ],
            "UIF": [
                r"(?i)(uif)",
            ],
        }

        # Patterns for determining if shared or individual
        self.shared_patterns = [
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

    def classify_category(self, description: str) -> str:
        """
        Classify transaction category based on description

        Args:
            description: Transaction description

        Returns:
            Category string (e.g., "GROCERIES", "FUEL", etc.)
        """
        description_lower = description.lower()

        # Check each category's patterns
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    return category

        # Default to OTHER if no match
        return "OTHER"

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
        for pattern in self.shared_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return ExpenseType.HOUSEHOLD

        # Default to INDIVIDUAL for personal accounts
        return ExpenseType.INDIVIDUAL

    def classify_transaction(
        self, description: str, amount: Decimal, is_shared_account: bool = False
    ) -> Tuple[str, str]:
        """
        Classify both category and type

        Priority order:
        1. Learned rules (from user corrections) - highest priority
        2. Keyword patterns - fallback

        Args:
            description: Transaction description
            amount: Transaction amount
            is_shared_account: True if from shared account

        Returns:
            Tuple of (category_string, type_string)
        """
        # Try learned classifier first (priority)
        if self.learned_classifier:
            learned_result = self.learned_classifier.classify(description)
            if learned_result:
                return learned_result

        # Fall back to keyword-based classification
        category = self.classify_category(description)
        expense_type = self.classify_type(description, amount, is_shared_account)

        return category, expense_type.name

    def get_classification_confidence(self, description: str, category: str) -> float:
        """
        Get confidence score for classification

        Args:
            description: Transaction description
            category: Classified category string

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if category == "OTHER":
            return 0.3  # Low confidence for default category

        # Check how many patterns matched
        patterns = self.category_patterns.get(category, [])
        matches = sum(
            1 for pattern in patterns if re.search(pattern, description, re.IGNORECASE)
        )

        if matches > 0:
            # More matches = higher confidence
            return min(0.7 + (matches * 0.15), 1.0)

        return 0.5  # Medium confidence

    def add_custom_rule(
        self, pattern: str, category: str, expense_type: Optional[ExpenseType] = None
    ):
        """
        Add a custom classification rule

        Args:
            pattern: Regex pattern to match
            category: Category string to assign
            expense_type: Optional type to assign (SHARED/INDIVIDUAL)
        """
        if category not in self.category_patterns:
            self.category_patterns[category] = []

        self.category_patterns[category].append(pattern)

        if expense_type == ExpenseType.SHARED:
            self.shared_patterns.append(pattern)
        elif expense_type == ExpenseType.INDIVIDUAL:
            self.individual_patterns.append(pattern)
