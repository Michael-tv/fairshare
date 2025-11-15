"""
Domain-specific exceptions for fairshare.

Replaces generic ValueError/RuntimeError with specific exception types
for better error handling and debugging.
"""

from datetime import date
from typing import Optional


class FairshareError(Exception):
    """Base exception for all fairshare domain errors."""
    pass


class ConfigurationError(FairshareError):
    """Configuration is invalid or missing."""

    def __init__(self, message: str, config_path: Optional[str] = None):
        self.config_path = config_path
        if config_path:
            message = f"{message} (config: {config_path})"
        super().__init__(message)


class ValidationError(FairshareError):
    """Data validation failed."""

    def __init__(self, field: str, message: str, value: Optional[str] = None):
        self.field = field
        self.value = value
        full_message = f"{field}: {message}"
        if value is not None:
            full_message += f" (got: {value})"
        super().__init__(full_message)


class MonthAlreadyProcessedError(FairshareError):
    """Attempting to process a month that was already processed."""

    def __init__(self, period: date):
        self.period = period
        super().__init__(
            f"Month {period:%Y-%m} has already been processed. "
            f"Use --force to reprocess."
        )


class MonthIncompleteError(FairshareError):
    """Month has incomplete transaction data."""

    def __init__(self, year: int, month: int, missing_days: int):
        self.year = year
        self.month = month
        self.missing_days = missing_days
        super().__init__(
            f"Month {year}-{month:02d} is incomplete "
            f"({missing_days} days missing)"
        )


class InsufficientDataError(FairshareError):
    """Not enough data to perform calculation."""

    def __init__(self, message: str, required: Optional[str] = None):
        self.required = required
        full_message = f"Insufficient data: {message}"
        if required:
            full_message += f". Required: {required}"
        super().__init__(full_message)


class FileNotFoundError(FairshareError):
    """Required file not found."""

    def __init__(self, file_path: str, file_type: Optional[str] = None):
        self.file_path = file_path
        self.file_type = file_type
        message = f"File not found: {file_path}"
        if file_type:
            message = f"{file_type} file not found: {file_path}"
        super().__init__(message)


class ParseError(FairshareError):
    """Error parsing a file or data."""

    def __init__(self, source: str, message: str, line_number: Optional[int] = None):
        self.source = source
        self.line_number = line_number
        full_message = f"Parse error in {source}: {message}"
        if line_number is not None:
            full_message += f" (line {line_number})"
        super().__init__(full_message)


class TemplateNotFoundError(FairshareError):
    """Bank template not found or could not be auto-detected."""

    def __init__(self, template_name: Optional[str] = None):
        self.template_name = template_name
        if template_name:
            message = f"Template '{template_name}' not found"
        else:
            message = "Could not auto-detect bank template"
        super().__init__(message)


class CalculationError(FairshareError):
    """Error during financial calculation."""

    def __init__(self, message: str, context: Optional[dict] = None):
        self.context = context or {}
        super().__init__(message)


class ClassificationError(FairshareError):
    """Error during transaction classification."""

    def __init__(self, transaction: str, message: str):
        self.transaction = transaction
        super().__init__(f"Classification error for '{transaction}': {message}")


class SplitMappingError(FairshareError):
    """Error in split mapping configuration."""

    def __init__(self, message: str, transaction_key: Optional[str] = None):
        self.transaction_key = transaction_key
        full_message = message
        if transaction_key:
            full_message += f" (transaction: {transaction_key})"
        super().__init__(full_message)
