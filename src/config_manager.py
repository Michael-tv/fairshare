"""
Configuration Manager

Loads and validates the config.json file for the home finances system.
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import List, Optional


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
    """Configuration for an account"""

    name: str
    statements_folder: str
    processed_folder: str
    account_type: str
    household_patterns: List[str] = None  # Account-specific household patterns
    individual_patterns: List[str] = None  # Account-specific individual patterns

    def __post_init__(self):
        """Initialize default values for optional fields"""
        if self.household_patterns is None:
            self.household_patterns = []
        if self.individual_patterns is None:
            self.individual_patterns = []


@dataclass
class UserConfig:
    """Configuration for a user (supports multiple accounts)"""

    id: str
    name: str
    person_sheet_path: str
    accounts: List['AccountConfig']


@dataclass
class SharedAccountConfig:
    """Configuration for a shared account"""

    name: str
    statements_folder: str
    processed_folder: str
    account_type: str
    household_patterns: List[str] = None  # Account-specific household patterns
    individual_patterns: List[str] = None  # Account-specific individual patterns

    def __post_init__(self):
        """Initialize default values for optional fields"""
        if self.household_patterns is None:
            self.household_patterns = []
        if self.individual_patterns is None:
            self.individual_patterns = []


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
    shared_accounts: List[SharedAccountConfig]
    matching: MatchingConfig
    classification: ClassificationConfig

    def get_user_names(self) -> List[str]:
        """Get list of user names"""
        return [u.name for u in self.users]

    def get_statements_folders(self) -> List[Path]:
        """Get all statement folders"""
        folders = []
        # User accounts
        for user in self.users:
            for account in user.accounts:
                folders.append(self.working_dir / account.statements_folder)
        # Shared accounts
        for account in self.shared_accounts:
            folders.append(self.working_dir / account.statements_folder)
        return folders

    def get_processed_folders(self) -> List[Path]:
        """Get all processed folders"""
        folders = []
        # User accounts
        for user in self.users:
            for account in user.accounts:
                folders.append(self.working_dir / account.processed_folder)
        # Shared accounts
        for account in self.shared_accounts:
            folders.append(self.working_dir / account.processed_folder)
        return folders


class ConfigManager:
    """Manages configuration loading and validation"""

    @staticmethod
    def _validate_account_type(account_type: str, account_name: str) -> None:
        """Validate account type is valid"""
        valid_types = [t.value for t in AccountType]
        if account_type not in valid_types:
            raise ValueError(
                f"Invalid account_type '{account_type}' for account '{account_name}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )

    @staticmethod
    def _validate_folders(statements_folder: str, processed_folder: str, account_name: str) -> None:
        """Validate folder paths are distinct"""
        if statements_folder == processed_folder:
            raise ValueError(
                f"Account '{account_name}': statements_folder and processed_folder must be different"
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
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                f"Create one from config.json.example"
            )

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

        # Validate required fields
        if "working_dir" not in data:
            raise ValueError("Missing required field in config: working_dir")

        if "users" not in data or len(data.get("users", [])) == 0:
            raise ValueError("Config must have 'users' array with at least one user")

        # Parse users structure
        users = []
        for u_data in data.get("users", []):
            if "name" not in u_data:
                raise ValueError("User config must have 'name'")

            # Parse user's accounts
            accounts = []
            for a_data in u_data.get("accounts", []):
                # Validate required fields
                required_fields = ["name", "statements_folder", "processed_folder", "account_type"]
                for field in required_fields:
                    if field not in a_data:
                        raise ValueError(
                            f"Account config for user '{u_data['name']}' is missing required field: '{field}'"
                        )

                # Validate account type
                ConfigManager._validate_account_type(a_data["account_type"], a_data["name"])

                # Validate folders
                ConfigManager._validate_folders(
                    a_data["statements_folder"],
                    a_data["processed_folder"],
                    a_data["name"]
                )

                accounts.append(
                    AccountConfig(
                        name=a_data["name"],
                        statements_folder=a_data["statements_folder"],
                        processed_folder=a_data["processed_folder"],
                        account_type=a_data["account_type"],
                        household_patterns=a_data.get("household_patterns", []),
                        individual_patterns=a_data.get("individual_patterns", [])
                    )
                )

            users.append(
                UserConfig(
                    id=u_data.get("id", f"user_{len(users) + 1}"),
                    name=u_data["name"],
                    person_sheet_path=u_data.get("person_sheet_path", ""),
                    accounts=accounts
                )
            )

        # Validate minimum users
        if len(users) < 2:
            raise ValueError("Config must have at least 2 users")

        # Parse shared accounts
        shared_accounts = []
        for s_data in data.get("shared_accounts", []):
            # Validate required fields
            required_fields = ["name", "statements_folder", "processed_folder", "account_type"]
            for field in required_fields:
                if field not in s_data:
                    raise ValueError(
                        f"Shared account config is missing required field: '{field}'"
                    )

            # Validate account type
            ConfigManager._validate_account_type(s_data["account_type"], s_data["name"])

            # Validate folders
            ConfigManager._validate_folders(
                s_data["statements_folder"],
                s_data["processed_folder"],
                s_data["name"]
            )

            shared_accounts.append(
                SharedAccountConfig(
                    name=s_data["name"],
                    statements_folder=s_data["statements_folder"],
                    processed_folder=s_data["processed_folder"],
                    account_type=s_data["account_type"],
                    household_patterns=s_data.get("household_patterns", []),
                    individual_patterns=s_data.get("individual_patterns", [])
                )
            )

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
