"""
JSON file repository base class.

Eliminates duplicate JSON load/save patterns across the codebase.
Supports both account-scoped and global data storage.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, TypeVar, Generic


T = TypeVar('T')


class JsonRepository(Generic[T]):
    """
    Base class for JSON file persistence with optional account-scoped data.

    This class provides a consistent interface for storing and retrieving
    data from JSON files. It supports two modes:

    1. Account-scoped: Data is organized by account_id within the file
       {
           "account_1": {...},
           "account_2": {...}
       }

    2. Global: All data is stored at the root level
       {...}

    Automatically handles:
    - File creation if it doesn't exist
    - JSON encoding/decoding
    - Error handling with warnings
    - Directory creation
    """

    def __init__(
        self,
        file_path: Path,
        account_id: Optional[str] = None,
        auto_save: bool = True
    ):
        """
        Initialize repository.

        Args:
            file_path: Path to JSON file
            account_id: Optional account ID for scoped data
            auto_save: If True, save after each modification
        """
        self.file_path = Path(file_path)
        self.account_id = account_id
        self.auto_save = auto_save

        # Internal storage
        self._all_data: Dict[str, Any] = {}  # All accounts (if scoped)
        self._data: Dict[str, Any] = {}      # This account's/global data

        # Load existing data
        self._load()

    def _load(self) -> None:
        """Load data from JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._all_data = json.load(f)

                # Extract this account's data if scoped
                if self.account_id:
                    self._data = self._all_data.get(self.account_id, {})
                else:
                    self._data = self._all_data

            except (json.JSONDecodeError, IOError) as e:
                print(f"[!] Warning: Could not load {self.file_path}: {e}")
                self._all_data = {}
                self._data = {}
        else:
            self._all_data = {}
            self._data = {}

    def _save(self) -> None:
        """Save data to JSON file."""
        # Update all_data with this account's data
        if self.account_id:
            self._all_data[self.account_id] = self._data
        else:
            self._all_data = self._data

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._all_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[!] Error: Could not save {self.file_path}: {e}")

    def save(self) -> None:
        """Manually save data (useful when auto_save=False)."""
        self._save()

    def reload(self) -> None:
        """Reload data from file, discarding any unsaved changes."""
        self._load()

    # Dictionary-like interface

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value and optionally auto-save."""
        self._data[key] = value
        if self.auto_save:
            self._save()

    def delete(self, key: str) -> bool:
        """Delete a key and optionally auto-save. Returns True if key existed."""
        if key in self._data:
            del self._data[key]
            if self.auto_save:
                self._save()
            return True
        return False

    def has(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data

    def keys(self):
        """Get all keys."""
        return self._data.keys()

    def values(self):
        """Get all values."""
        return self._data.values()

    def items(self):
        """Get all key-value pairs."""
        return self._data.items()

    def clear(self) -> None:
        """Clear all data for this account/globally."""
        self._data.clear()
        if self.auto_save:
            self._save()

    def update(self, data: Dict[str, Any]) -> None:
        """Update with multiple key-value pairs."""
        self._data.update(data)
        if self.auto_save:
            self._save()

    # Direct data access (for compatibility with existing code)

    @property
    def data(self) -> Dict[str, Any]:
        """Direct access to the underlying data dictionary."""
        return self._data

    @data.setter
    def data(self, value: Dict[str, Any]):
        """Set the entire data dictionary."""
        self._data = value
        if self.auto_save:
            self._save()

    # Account management (for scoped repositories)

    def get_all_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Get data for all accounts (if using account scoping)."""
        return self._all_data.copy()

    def switch_account(self, account_id: str) -> None:
        """
        Switch to a different account.

        Args:
            account_id: New account ID to switch to
        """
        if not self.account_id:
            raise ValueError("Cannot switch accounts in non-scoped repository")

        # Save current account's data
        self._all_data[self.account_id] = self._data

        # Switch to new account
        self.account_id = account_id
        self._data = self._all_data.get(account_id, {})

    def delete_account(self, account_id: str) -> bool:
        """
        Delete an entire account's data.

        Args:
            account_id: Account ID to delete

        Returns:
            True if account existed and was deleted
        """
        if account_id in self._all_data:
            del self._all_data[account_id]
            if self.auto_save:
                self._save()
            return True
        return False

    # Utility methods

    def __len__(self) -> int:
        """Return number of keys in current scope."""
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        """Check if key exists using 'in' operator."""
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        """Get item using dict syntax: repo[key]."""
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item using dict syntax: repo[key] = value."""
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        """Delete item using dict syntax: del repo[key]."""
        if key not in self._data:
            raise KeyError(key)
        self.delete(key)

    def __repr__(self) -> str:
        """String representation."""
        scope = f"account={self.account_id}" if self.account_id else "global"
        return f"JsonRepository({self.file_path}, {scope}, {len(self._data)} keys)"
