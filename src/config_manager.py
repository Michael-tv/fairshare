"""
Configuration Manager

Loads and validates the config.json file for the home finances system.

REFACTORED: Consolidated AccountConfig and SharedAccountConfig into single class.
"""

import json
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import List, Optional

from src.exceptions import ConfigurationError, ValidationError


class AccountType(Enum):
    """Valid account types"""
    PERSONAL = "personal"
    CREDIT_CARD = "credit_card"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    LOAN = "loan"
    OTHER = "other"


@dataclass
class AccountConfig:
    """
    Configuration for any account (personal or shared).

    Unified class that replaces the old AccountConfig and SharedAccountConfig
    duplication.
    """

    name: str
    statements_folder: str
    processed_folder: str
    account_type: str
    owner: Optional[str] = None  # None = shared account, else user ID/name
    household_patterns: List[str] = field(default_factory=list)
    individual_patterns: List[str] = field(default_factory=list)

    @property
    def is_shared(self) -> bool:
        """True if this is a shared account (no specific owner)."""
        return self.owner is None

    @property
    def owner_display(self) -> str:
        """Display name for owner (Shared or user name)."""
        return "Shared" if self.is_shared else self.owner


@dataclass
class UserConfig:
    """Configuration for a user (supports multiple accounts)"""

    id: str
    name: str
    person_sheet_path: str
    accounts: List[AccountConfig] = field(default_factory=list)


@dataclass
class MatchingConfig:
    """Configuration for transaction matching"""

    amount_tolerance: Decimal = Decimal("1.00")
    date_tolerance_days: int = 3
    merchant_similarity_threshold: float = 0.6


@dataclass
class ClassificationConfig:
    """Configuration for transaction classification"""

    enabled: bool = True
    default_shared_type: str = "SHARED"


@dataclass
class Config:
    """Main configuration object"""

    working_dir: Path
    users: List[UserConfig]
    shared_accounts: List[AccountConfig]  # Now same type as user accounts
    matching: MatchingConfig
    classification: ClassificationConfig

    def get_user_names(self) -> List[str]:
        """Get list of user names"""
        return [u.name for u in self.users]

    def get_all_accounts(self) -> List[AccountConfig]:
        """Get all accounts (both user and shared)."""
        accounts = []
        for user in self.users:
            accounts.extend(user.accounts)
        accounts.extend(self.shared_accounts)
        return accounts

    def get_statements_folders(self) -> List[Path]:
        """Get all statement folders"""
        folders = []
        for account in self.get_all_accounts():
            folders.append(self.working_dir / account.statements_folder)
        return folders

    def get_processed_folders(self) -> List[Path]:
        """Get all processed folders"""
        folders = []
        for account in self.get_all_accounts():
            folders.append(self.working_dir / account.processed_folder)
        return folders


class ConfigManager:
    """Manages configuration loading and validation"""

    @staticmethod
    def _validate_account_type(account_type: str, account_name: str) -> None:
        """Validate account type is valid"""
        valid_types = [t.value for t in AccountType]
        if account_type not in valid_types:
            raise ValidationError(
                "account_type",
                f"Invalid type for account '{account_name}'. Must be one of: {', '.join(valid_types)}",
                account_type
            )

    @staticmethod
    def _validate_folders(statements_folder: str, processed_folder: str, account_name: str) -> None:
        """Validate folder paths are distinct"""
        if statements_folder == processed_folder:
            raise ValidationError(
                "folders",
                f"Account '{account_name}': statements_folder and processed_folder must be different"
            )

    @staticmethod
    def _parse_account(account_data: dict, owner: Optional[str] = None, context: str = "") -> AccountConfig:
        """
        Parse an account configuration from JSON data.

        Args:
            account_data: Dictionary with account config
            owner: Owner ID/name (None for shared accounts)
            context: Context string for error messages (e.g., "user 'Michael'")

        Returns:
            AccountConfig instance
        """
        # Validate required fields
        required_fields = ["name", "statements_folder", "processed_folder", "account_type"]
        for field_name in required_fields:
            if field_name not in account_data:
                raise ConfigurationError(
                    f"{context} account config is missing required field: '{field_name}'"
                )

        account_name = account_data["name"]

        # Validate account type
        ConfigManager._validate_account_type(account_data["account_type"], account_name)

        # Validate folders
        ConfigManager._validate_folders(
            account_data["statements_folder"],
            account_data["processed_folder"],
            account_name
        )

        return AccountConfig(
            name=account_name,
            statements_folder=account_data["statements_folder"],
            processed_folder=account_data["processed_folder"],
            account_type=account_data["account_type"],
            owner=owner,
            household_patterns=account_data.get("household_patterns", []),
            individual_patterns=account_data.get("individual_patterns", [])
        )

    @staticmethod
    def load(config_path: str = "config.json") -> Config:
        """
        Load configuration from JSON file

        Args:
            config_path: Path to config file (default: config.json)

        Returns:
            Config object

        Raises:
            ConfigurationError: If config file doesn't exist or is invalid
            ValidationError: If config validation fails
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigurationError(
                f"Config file not found: {config_path}. "
                f"Create one from config.json.example",
                config_path
            )

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}", config_path)

        # Validate required fields
        if "working_dir" not in data:
            raise ConfigurationError("Missing required field: working_dir", config_path)

        if "users" not in data or len(data.get("users", [])) == 0:
            raise ConfigurationError(
                "Config must have 'users' array with at least one user",
                config_path
            )

        # Parse users structure
        users = []
        for u_data in data.get("users", []):
            if "name" not in u_data:
                raise ConfigurationError("User config must have 'name'", config_path)

            user_name = u_data["name"]
            user_id = u_data.get("id", f"user_{len(users) + 1}")

            # Parse user's accounts
            accounts = []
            for a_data in u_data.get("accounts", []):
                account = ConfigManager._parse_account(
                    a_data,
                    owner=user_id,
                    context=f"User '{user_name}'"
                )
                accounts.append(account)

            users.append(
                UserConfig(
                    id=user_id,
                    name=user_name,
                    person_sheet_path=u_data.get("person_sheet_path", ""),
                    accounts=accounts
                )
            )

        # Validate minimum users
        if len(users) < 2:
            raise ValidationError(
                "users",
                "Config must have at least 2 users for fair share calculations"
            )

        # Parse shared accounts (same structure, just owner=None)
        shared_accounts = []
        for s_data in data.get("shared_accounts", []):
            account = ConfigManager._parse_account(
                s_data,
                owner=None,  # Shared account
                context="Shared"
            )
            shared_accounts.append(account)

        # Parse matching config
        matching_data = data.get("matching", {})
        matching = MatchingConfig(
            amount_tolerance=Decimal(str(matching_data.get("amount_tolerance", 1.00))),
            date_tolerance_days=matching_data.get("date_tolerance_days", 3),
            merchant_similarity_threshold=matching_data.get(
                "merchant_similarity_threshold", 0.6
            ),
        )

        # Parse classification config
        classif_data = data.get("classification", {})
        classification = ClassificationConfig(
            enabled=classif_data.get("enabled", True),
            default_shared_type=classif_data.get("default_shared_type", "SHARED"),
        )

        working_dir = Path(data["working_dir"])

        return Config(
            working_dir=working_dir,
            users=users,
            shared_accounts=shared_accounts,
            matching=matching,
            classification=classification,
        )

    @staticmethod
    def create_default(output_path: str = "config.json"):
        """Create a default config file"""
        default_config = {
            "working_dir": "data",
            "users": [
                {
                    "id": "user_1",
                    "name": "Person1",
                    "person_sheet_path": "data/person_sheets/Person1_2024_11.xlsx",
                    "accounts": [
                        {
                            "name": "Main Bank Account",
                            "account_type": "personal",
                            "statements_folder": "data/raw/statements/Person1/Bank",
                            "processed_folder": "data/processed/transactions/Person1/Bank"
                        }
                    ]
                },
                {
                    "id": "user_2",
                    "name": "Person2",
                    "person_sheet_path": "data/person_sheets/Person2_2024_11.xlsx",
                    "accounts": [
                        {
                            "name": "Main Bank Account",
                            "account_type": "personal",
                            "statements_folder": "data/raw/statements/Person2/Bank",
                            "processed_folder": "data/processed/transactions/Person2/Bank"
                        }
                    ]
                }
            ],
            "shared_accounts": [
                {
                    "name": "Joint Credit Card",
                    "account_type": "credit_card",
                    "statements_folder": "data/raw/statements/Shared/CreditCard",
                    "processed_folder": "data/processed/transactions/Shared/CreditCard"
                }
            ],
            "matching": {
                "amount_tolerance": 1.00,
                "date_tolerance_days": 3,
                "merchant_similarity_threshold": 0.6,
            },
            "classification": {"enabled": True, "default_shared_type": "SHARED"},
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

        print(f"Created default config: {output_path}")
        print("Edit this file to customize your configuration.")
