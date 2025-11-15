"""
Parsing utilities for amounts, dates, and other data types.

Centralizes parsing logic to ensure consistency across the codebase.
"""

from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Optional, List, Union
import pandas as pd


class AmountParser:
    """
    Centralized amount parsing with consistent error handling.

    Handles various input formats:
    - Currency symbols: R 1,234.56 → 1234.56
    - Parentheses: (100) → -100
    - Thousands separators: 1,234.56
    - NaN/empty values → 0
    """

    DEFAULT_CURRENCY_SYMBOLS = "R$€£¥"

    @staticmethod
    def parse(
        value: Union[str, int, float, Decimal],
        currency_symbols: str = DEFAULT_CURRENCY_SYMBOLS,
        default: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Parse amount from various formats.

        Args:
            value: Value to parse (string, number, or pandas value)
            currency_symbols: String of currency symbols to strip
            default: Default value if parsing fails

        Returns:
            Decimal value

        Examples:
            >>> AmountParser.parse("R 1,234.56")
            Decimal('1234.56')
            >>> AmountParser.parse("(100)")
            Decimal('-100')
            >>> AmountParser.parse(None)
            Decimal('0')
        """
        # Handle NaN/None values
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default

        # Already a Decimal
        if isinstance(value, Decimal):
            return value

        # Convert to string for processing
        value_str = str(value).strip()

        # Empty string
        if not value_str:
            return default

        # Remove currency symbols and spaces
        for symbol in currency_symbols:
            value_str = value_str.replace(symbol, "")
        value_str = value_str.replace(",", "").replace(" ", "")

        # Handle parentheses as negative (accounting format)
        if value_str.startswith("(") and value_str.endswith(")"):
            value_str = "-" + value_str[1:-1]

        # Parse to Decimal
        try:
            return Decimal(value_str)
        except (ValueError, InvalidOperation):
            return default

    @staticmethod
    def format_currency(amount: Decimal, currency: str = "R") -> str:
        """
        Format a Decimal amount as currency string.

        Args:
            amount: Amount to format
            currency: Currency symbol

        Returns:
            Formatted string like "R 1,234.56"
        """
        return f"{currency}{amount:,.2f}"


class DateParser:
    """
    Centralized date parsing with multiple format support.
    """

    # Common date formats to try
    DEFAULT_FORMATS = [
        "%Y-%m-%d",      # 2024-04-15
        "%d/%m/%Y",      # 15/04/2024
        "%d-%m-%Y",      # 15-04-2024
        "%Y/%m/%d",      # 2024/04/15
        "%d %b %Y",      # 15 Apr 2024
        "%d %B %Y",      # 15 April 2024
        "%b %d %Y",      # Apr 15 2024
        "%B %d %Y",      # April 15 2024
    ]

    @staticmethod
    def parse(
        value: Union[str, datetime, date],
        formats: Optional[List[str]] = None,
        default: Optional[date] = None
    ) -> Optional[date]:
        """
        Parse date from various formats with fallback.

        Args:
            value: Value to parse
            formats: List of date format strings to try (uses defaults if None)
            default: Default value if parsing fails

        Returns:
            date object or default

        Examples:
            >>> DateParser.parse("2024-04-15")
            datetime.date(2024, 4, 15)
            >>> DateParser.parse("15/04/2024")
            datetime.date(2024, 4, 15)
        """
        # Handle None/NaN
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default

        # Already a date object
        if isinstance(value, date):
            return value

        # datetime object
        if isinstance(value, datetime):
            return value.date()

        # Parse string
        value_str = str(value).strip()
        if not value_str:
            return default

        # Try each format
        formats_to_try = formats or DateParser.DEFAULT_FORMATS
        for fmt in formats_to_try:
            try:
                return datetime.strptime(value_str, fmt).date()
            except ValueError:
                continue

        # All formats failed
        return default

    @staticmethod
    def parse_month_year(value: str) -> Optional[date]:
        """
        Parse month/year strings like "April 2024" or "2024-04".

        Returns first day of the month.
        """
        formats = [
            "%B %Y",    # April 2024
            "%b %Y",    # Apr 2024
            "%Y-%m",    # 2024-04
            "%m/%Y",    # 04/2024
        ]
        return DateParser.parse(value, formats=formats)
