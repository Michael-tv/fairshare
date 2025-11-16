"""
Template Validator - Validates bank statement templates for correctness and completeness.

This module provides comprehensive validation of YAML bank templates to catch
configuration errors before they cause parsing failures.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import yaml
from src.bank_template import BankTemplate


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Critical - will cause parsing failures
    WARNING = "warning"  # Important - may cause issues
    INFO = "info"        # Informational - best practices


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a template."""
    severity: ValidationSeverity
    field: str
    message: str
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the issue."""
        severity_symbol = {
            ValidationSeverity.ERROR: "❌",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.INFO: "ℹ️"
        }
        symbol = severity_symbol.get(self.severity, "•")

        result = f"{symbol} [{self.severity.value.upper()}] {self.field}: {self.message}"
        if self.suggestion:
            result += f"\n   💡 Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """Result of template validation."""
    template_name: str
    is_valid: bool
    issues: List[ValidationIssue]
    score: float  # 0-100, confidence score

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def infos(self) -> List[ValidationIssue]:
        """Get only info-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.INFO]

    def summary(self) -> str:
        """Generate a summary string."""
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        return (
            f"Template: {self.template_name}\n"
            f"Status: {status} (Score: {self.score:.1f}/100)\n"
            f"Errors: {len(self.errors)}, Warnings: {len(self.warnings)}, Info: {len(self.infos)}"
        )

    def detailed_report(self) -> str:
        """Generate a detailed validation report."""
        lines = [
            "=" * 80,
            f"TEMPLATE VALIDATION REPORT: {self.template_name}",
            "=" * 80,
            "",
            f"Overall Status: {'✓ VALID' if self.is_valid else '✗ INVALID'}",
            f"Confidence Score: {self.score:.1f}/100",
            f"Total Issues: {len(self.issues)} ({len(self.errors)} errors, {len(self.warnings)} warnings, {len(self.infos)} info)",
            ""
        ]

        if self.errors:
            lines.append("ERRORS (must fix):")
            lines.append("-" * 80)
            for issue in self.errors:
                lines.append(str(issue))
                lines.append("")

        if self.warnings:
            lines.append("WARNINGS (should fix):")
            lines.append("-" * 80)
            for issue in self.warnings:
                lines.append(str(issue))
                lines.append("")

        if self.infos:
            lines.append("INFORMATION (optional improvements):")
            lines.append("-" * 80)
            for issue in self.infos:
                lines.append(str(issue))
                lines.append("")

        if not self.issues:
            lines.append("✓ No issues found! Template looks good.")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)


class TemplateValidator:
    """Validates bank statement templates."""

    # Required pattern groups for transactions
    REQUIRED_GROUPS = ['day', 'month', 'description', 'amount']

    # Optional but common groups
    OPTIONAL_GROUPS = ['year', 'credit', 'debit', 'indicator', 'balance', 'card']

    def __init__(self):
        """Initialize the validator."""
        self.issues: List[ValidationIssue] = []

    def validate_template(self, template_path: Path) -> ValidationResult:
        """
        Validate a template file.

        Args:
            template_path: Path to the YAML template file

        Returns:
            ValidationResult with all issues found
        """
        self.issues = []
        template_name = template_path.stem

        # Check file exists
        if not template_path.exists():
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "file",
                f"Template file not found: {template_path}"
            ))
            return self._create_result(template_name)

        # Load and parse YAML
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "yaml",
                f"YAML parsing error: {e}"
            ))
            return self._create_result(template_name)
        except Exception as e:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "file",
                f"Error reading file: {e}"
            ))
            return self._create_result(template_name)

        # Validate structure
        self._validate_basic_structure(config)
        self._validate_detection(config)
        self._validate_parsing(config)
        self._validate_sections(config)
        self._validate_summary(config)
        self._validate_output(config)

        return self._create_result(template_name)

    def _create_result(self, template_name: str) -> ValidationResult:
        """Create validation result from collected issues."""
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in self.issues)
        is_valid = not has_errors

        # Calculate score (100 - deductions for issues)
        score = 100.0
        for issue in self.issues:
            if issue.severity == ValidationSeverity.ERROR:
                score -= 20
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 5
            elif issue.severity == ValidationSeverity.INFO:
                score -= 1
        score = max(0, score)

        return ValidationResult(
            template_name=template_name,
            is_valid=is_valid,
            issues=self.issues,
            score=score
        )

    def _validate_basic_structure(self, config: Dict[str, Any]):
        """Validate basic required fields."""
        required_fields = ['bank_name', 'account_type']

        for field in required_fields:
            if field not in config:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.ERROR,
                    field,
                    f"Missing required field '{field}'"
                ))
            elif not config[field]:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.ERROR,
                    field,
                    f"Field '{field}' is empty"
                ))

        # Check if country is specified (informational)
        if 'country' not in config:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "country",
                "Country code not specified",
                "Add 'country' field for better documentation (e.g., 'ZA', 'US')"
            ))

    def _validate_detection(self, config: Dict[str, Any]):
        """Validate detection configuration."""
        if 'detection' not in config:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "detection",
                "No detection configuration - template cannot be auto-detected",
                "Add 'detection' section with 'markers' list"
            ))
            return

        detection = config['detection']

        # Check for markers
        if 'markers' not in detection:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "detection.markers",
                "No detection markers specified",
                "Add 'markers' list with unique text from first page"
            ))
        elif not detection['markers']:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "detection.markers",
                "Detection markers list is empty"
            ))
        elif len(detection['markers']) < 2:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "detection.markers",
                "Only one detection marker - consider adding more for reliability",
                "Add 2-3 unique markers from the PDF for better detection"
            ))

        # Check priority
        if 'priority' not in detection:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "detection.priority",
                "No priority specified (will default to 0)",
                "Add 'priority' field to control detection order"
            ))

    def _validate_parsing(self, config: Dict[str, Any]):
        """Validate parsing configuration."""
        if 'parsing' not in config:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "parsing",
                "Missing 'parsing' section - cannot parse transactions"
            ))
            return

        parsing = config['parsing']

        # Validate transaction pattern
        self._validate_transaction_pattern(parsing)

        # Validate date configuration
        if 'date' in parsing:
            self._validate_date_config(parsing['date'])
        else:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "parsing.date",
                "No date configuration - may have parsing issues"
            ))

        # Validate amount configuration
        if 'amount' in parsing:
            self._validate_amount_config(parsing['amount'])
        else:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "parsing.amount",
                "No amount configuration - using defaults"
            ))

        # Validate description configuration
        if 'description' not in parsing:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "parsing.description",
                "No description configuration - using defaults"
            ))

    def _validate_transaction_pattern(self, parsing: Dict[str, Any]):
        """Validate the transaction regex pattern."""
        if 'transaction_pattern' not in parsing:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "parsing.transaction_pattern",
                "Missing transaction_pattern - cannot parse transactions"
            ))
            return

        pattern = parsing['transaction_pattern']

        # Check if pattern is a string
        if not isinstance(pattern, str):
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "parsing.transaction_pattern",
                "transaction_pattern must be a string"
            ))
            return

        # Try to compile regex
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "parsing.transaction_pattern",
                f"Invalid regex pattern: {e}"
            ))
            return

        # Check for required named groups
        groups = compiled.groupindex.keys()
        missing_groups = []
        for required in self.REQUIRED_GROUPS:
            if required not in groups:
                missing_groups.append(required)

        if missing_groups:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "parsing.transaction_pattern",
                f"Missing required regex groups: {', '.join(missing_groups)}",
                f"Pattern must include named groups: {', '.join(self.REQUIRED_GROUPS)}"
            ))

        # Check if pattern is too permissive
        if '.+' in pattern and '.*' in pattern:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "parsing.transaction_pattern",
                "Pattern uses both .+ and .* - may be too permissive",
                "Consider making pattern more specific to avoid false matches"
            ))

    def _validate_date_config(self, date_cfg: Dict[str, Any]):
        """Validate date parsing configuration."""
        # Check for required groups
        if 'day_group' not in date_cfg:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "parsing.date.day_group",
                "No day_group specified (will default to 'day')"
            ))

        if 'month_group' not in date_cfg:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "parsing.date.month_group",
                "No month_group specified (will default to 'month')"
            ))

        # Check date format
        if 'format' not in date_cfg:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "parsing.date.format",
                "No date format specified (will default to '%d %b')"
            ))

        # Check year source
        if 'year_source' not in date_cfg:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "parsing.date.year_source",
                "No year_source specified (will default to 'statement')"
            ))

    def _validate_amount_config(self, amount_cfg: Dict[str, Any]):
        """Validate amount parsing configuration."""
        # Check for credit indicator (important for Credit/Debit detection)
        if 'credit_indicator' not in amount_cfg:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "parsing.amount.credit_indicator",
                "No credit_indicator configuration - cannot determine Credit vs Debit",
                "Add credit_indicator config to properly classify transaction direction"
            ))
        else:
            credit_cfg = amount_cfg['credit_indicator']

            # Validate credit indicator structure
            if 'group' not in credit_cfg:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    "parsing.amount.credit_indicator.group",
                    "No group specified for credit indicator"
                ))

            if 'value' not in credit_cfg:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    "parsing.amount.credit_indicator.value",
                    "No value specified for credit indicator"
                ))

            # Check for invert flag explanation
            if credit_cfg.get('invert') and 'debit_value' not in credit_cfg:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.INFO,
                    "parsing.amount.credit_indicator",
                    "Using 'invert' flag - ensure this is correct for your statement",
                    "Add 'debit_value' field for clarity"
                ))

    def _validate_sections(self, config: Dict[str, Any]):
        """Validate section boundaries."""
        if 'sections' not in config:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "sections",
                "No sections configuration - will parse entire document",
                "Add sections with start_markers and end_markers"
            ))
            return

        sections = config['sections']

        # Check for start markers
        if 'start_markers' not in sections or not sections['start_markers']:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "sections.start_markers",
                "No start_markers - will parse from beginning of document",
                "Add start_markers to identify where transactions begin"
            ))

        # Check for end markers
        if 'end_markers' not in sections or not sections['end_markers']:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "sections.end_markers",
                "No end_markers specified",
                "Add end_markers to identify where transactions end"
            ))

        # Check for skip_lines
        if 'skip_lines' not in sections or not sections['skip_lines']:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "sections.skip_lines",
                "No skip_lines specified",
                "Add skip_lines to filter out headers and summaries"
            ))

    def _validate_summary(self, config: Dict[str, Any]):
        """Validate summary extraction configuration."""
        if 'summary' not in config:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "summary",
                "No summary configuration - statement metadata won't be extracted",
                "Add summary section to extract balances and totals for validation"
            ))
            return

        summary = config['summary']
        recommended_fields = [
            'statement_date', 'opening_balance', 'closing_balance',
            'total_expenses', 'total_payments'
        ]

        missing = [f for f in recommended_fields if f not in summary]
        if missing:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "summary",
                f"Missing recommended summary fields: {', '.join(missing)}",
                "Add these fields to enable balance validation"
            ))

    def _validate_output(self, config: Dict[str, Any]):
        """Validate output configuration."""
        if 'output' not in config:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "output",
                "No output configuration"
            ))
            return

        output = config['output']

        if 'account_type' not in output:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "output.account_type",
                "No account_type specified in output"
            ))
