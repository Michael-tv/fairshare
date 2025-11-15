"""
Column mapper utility for intelligent DataFrame column detection.

Eliminates duplicate column-finding logic across importers.
"""

from typing import Optional, List
import pandas as pd


class ColumnMapper:
    """
    Intelligent DataFrame column mapping with fuzzy matching.

    Handles case-insensitive partial matching to find columns by
    various possible names.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize mapper with a DataFrame.

        Args:
            df: DataFrame to map columns from
        """
        self.df = df
        # Create lowercase mapping for efficient lookup
        self.columns_lower = {
            str(col).lower().strip(): col
            for col in df.columns
        }

    def find(self, *possible_names: str) -> Optional[str]:
        """
        Find column by trying multiple possible names.

        Uses case-insensitive partial matching - if any possible name
        is contained in a column name, that column is returned.

        Args:
            *possible_names: Possible column names to try

        Returns:
            Actual column name if found, None otherwise

        Examples:
            >>> mapper = ColumnMapper(df)
            >>> mapper.find('description', 'desc', 'item')
            'Description'  # if df has 'Description' column
        """
        for col_lower, col_original in self.columns_lower.items():
            for possible in possible_names:
                if possible.lower() in col_lower:
                    return col_original
        return None

    def require(self, *possible_names: str, field_name: Optional[str] = None) -> str:
        """
        Find column or raise descriptive error.

        Args:
            *possible_names: Possible column names to try
            field_name: Human-readable field name for error message

        Returns:
            Actual column name

        Raises:
            ValueError: If column not found

        Examples:
            >>> mapper.require('amount', 'value', field_name='Amount')
            'Amount'  # or raises ValueError with helpful message
        """
        col = self.find(*possible_names)
        if col is None:
            names = ", ".join(f"'{name}'" for name in possible_names)
            field = field_name or possible_names[0]
            available = ", ".join(f"'{c}'" for c in self.df.columns)
            raise ValueError(
                f"Could not find '{field}' column (tried: {names}). "
                f"Available columns: {available}"
            )
        return col

    def get_columns(self) -> List[str]:
        """Get list of all column names."""
        return list(self.df.columns)

    def has_column(self, *possible_names: str) -> bool:
        """Check if any of the possible column names exist."""
        return self.find(*possible_names) is not None
