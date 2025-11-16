"""
Parser Diagnostics - Capture and analyze bank statement parsing operations.

This module provides diagnostic capabilities for troubleshooting parsing issues:
- Detailed logging of parsing operations
- Statistics about what was parsed, skipped, and failed
- Line-by-line analysis of parsing attempts
- Balance validation and mismatch detection
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from pathlib import Path
from collections import defaultdict


@dataclass
class LineParseAttempt:
    """Record of an attempt to parse a line."""
    line_number: int
    line_text: str
    matched: bool
    transaction_created: bool
    skip_reason: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ParsingStatistics:
    """Statistics from a parsing run."""
    pdf_path: str
    template_name: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Line statistics
    total_lines: int = 0
    lines_in_section: int = 0
    lines_matched_pattern: int = 0
    lines_skipped: int = 0

    # Transaction statistics
    transactions_created: int = 0
    transactions_failed: int = 0
    credits_count: int = 0
    debits_count: int = 0

    # Amount statistics
    total_credits: Decimal = Decimal('0')
    total_debits: Decimal = Decimal('0')

    # Skip reasons
    skip_reasons: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Validation
    balance_validation: Optional[Dict[str, Any]] = None

    @property
    def duration_seconds(self) -> float:
        """Get parsing duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def match_rate(self) -> float:
        """Get percentage of lines that matched pattern."""
        if self.lines_in_section == 0:
            return 0.0
        return (self.lines_matched_pattern / self.lines_in_section) * 100

    @property
    def success_rate(self) -> float:
        """Get percentage of matched lines that created transactions."""
        if self.lines_matched_pattern == 0:
            return 0.0
        return (self.transactions_created / self.lines_matched_pattern) * 100

    def summary(self) -> str:
        """Generate a summary string."""
        return (
            f"Parsing Statistics for {Path(self.pdf_path).name}\n"
            f"Template: {self.template_name}\n"
            f"Duration: {self.duration_seconds:.2f}s\n"
            f"\n"
            f"Lines:\n"
            f"  Total: {self.total_lines}\n"
            f"  In section: {self.lines_in_section}\n"
            f"  Matched pattern: {self.lines_matched_pattern} ({self.match_rate:.1f}%)\n"
            f"  Skipped: {self.lines_skipped}\n"
            f"\n"
            f"Transactions:\n"
            f"  Created: {self.transactions_created}\n"
            f"  Failed: {self.transactions_failed}\n"
            f"  Credits: {self.credits_count} (R{self.total_credits:,.2f})\n"
            f"  Debits: {self.debits_count} (R{self.total_debits:,.2f})\n"
            f"  Success rate: {self.success_rate:.1f}%\n"
        )

    def detailed_report(self) -> str:
        """Generate a detailed report."""
        lines = [
            "=" * 80,
            "PARSER DIAGNOSTICS REPORT",
            "=" * 80,
            "",
            f"PDF: {self.pdf_path}",
            f"Template: {self.template_name}",
            f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if self.end_time:
            lines.append(f"Finished: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Duration: {self.duration_seconds:.2f} seconds")

        lines.extend([
            "",
            "LINE PROCESSING:",
            "-" * 80,
            f"Total lines in PDF: {self.total_lines}",
            f"Lines in transaction section: {self.lines_in_section}",
            f"Lines matching pattern: {self.lines_matched_pattern} ({self.match_rate:.1f}%)",
            f"Lines skipped: {self.lines_skipped}",
            "",
        ])

        if self.skip_reasons:
            lines.append("Skip Reasons:")
            for reason, count in sorted(self.skip_reasons.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {reason}: {count}")
            lines.append("")

        lines.extend([
            "TRANSACTION RESULTS:",
            "-" * 80,
            f"Transactions created: {self.transactions_created}",
            f"Transactions failed: {self.transactions_failed}",
            f"Success rate: {self.success_rate:.1f}%",
            "",
            f"Credits (payments in): {self.credits_count} transactions, R{self.total_credits:,.2f}",
            f"Debits (payments out): {self.debits_count} transactions, R{self.total_debits:,.2f}",
            f"Net: R{(self.total_credits - self.total_debits):,.2f}",
            "",
        ])

        if self.balance_validation:
            lines.extend([
                "BALANCE VALIDATION:",
                "-" * 80,
            ])

            val = self.balance_validation
            if val.get('valid'):
                lines.append("✓ Balance validation PASSED")
            else:
                lines.append("✗ Balance validation FAILED")

            if 'opening_balance' in val:
                lines.append(f"Opening balance: R{val['opening_balance']:,.2f}")
            if 'closing_balance' in val:
                lines.append(f"Closing balance: R{val['closing_balance']:,.2f}")
            if 'calculated_balance' in val:
                lines.append(f"Calculated balance: R{val['calculated_balance']:,.2f}")
            if 'difference' in val:
                lines.append(f"Difference: R{val['difference']:,.2f}")

            if val.get('warnings'):
                lines.append("\nWarnings:")
                for warning in val['warnings']:
                    lines.append(f"  ⚠️  {warning}")

            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)


@dataclass
class ParsingSession:
    """A complete parsing session with all diagnostics."""
    statistics: ParsingStatistics
    line_attempts: List[LineParseAttempt] = field(default_factory=list)
    log_messages: List[Dict[str, Any]] = field(default_factory=list)

    def add_log_message(self, level: str, message: str, context: Optional[Dict] = None):
        """Add a log message."""
        self.log_messages.append({
            'timestamp': datetime.now(),
            'level': level,
            'message': message,
            'context': context or {}
        })

    def get_failed_lines(self) -> List[LineParseAttempt]:
        """Get all lines that matched but failed to create transactions."""
        return [
            attempt for attempt in self.line_attempts
            if attempt.matched and not attempt.transaction_created
        ]

    def get_unmatched_lines(self) -> List[LineParseAttempt]:
        """Get all lines that didn't match the pattern."""
        return [attempt for attempt in self.line_attempts if not attempt.matched]

    def export_to_file(self, output_path: Path):
        """Export session data to a file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write statistics
            f.write(self.statistics.detailed_report())
            f.write("\n\n")

            # Write failed lines
            failed = self.get_failed_lines()
            if failed:
                f.write("=" * 80 + "\n")
                f.write(f"FAILED TO PARSE ({len(failed)} lines)\n")
                f.write("=" * 80 + "\n\n")
                for attempt in failed:
                    f.write(f"Line {attempt.line_number}:\n")
                    f.write(f"  Text: {attempt.line_text[:100]}\n")
                    f.write(f"  Reason: {attempt.skip_reason or attempt.error or 'Unknown'}\n\n")

            # Write unmatched lines sample
            unmatched = self.get_unmatched_lines()
            if unmatched:
                f.write("=" * 80 + "\n")
                f.write(f"UNMATCHED LINES ({len(unmatched)} total, showing first 50)\n")
                f.write("=" * 80 + "\n\n")
                for attempt in unmatched[:50]:
                    f.write(f"Line {attempt.line_number}: {attempt.line_text[:100]}\n")

            # Write log messages
            if self.log_messages:
                f.write("\n\n")
                f.write("=" * 80 + "\n")
                f.write(f"LOG MESSAGES ({len(self.log_messages)} total)\n")
                f.write("=" * 80 + "\n\n")
                for log in self.log_messages:
                    timestamp = log['timestamp'].strftime('%H:%M:%S.%f')[:-3]
                    f.write(f"[{timestamp}] {log['level']}: {log['message']}\n")


class ParserDiagnosticsCollector(logging.Handler):
    """Logging handler that collects parser diagnostics."""

    def __init__(self):
        super().__init__()
        self.current_session: Optional[ParsingSession] = None
        self.sessions: List[ParsingSession] = []
        self.enabled = False

    def start_session(self, pdf_path: str, template_name: str):
        """Start a new diagnostics session."""
        stats = ParsingStatistics(
            pdf_path=pdf_path,
            template_name=template_name,
            start_time=datetime.now()
        )
        self.current_session = ParsingSession(statistics=stats)
        self.enabled = True

    def end_session(self):
        """End the current session."""
        if self.current_session:
            self.current_session.statistics.end_time = datetime.now()
            self.sessions.append(self.current_session)
            self.current_session = None
        self.enabled = False

    def emit(self, record: logging.LogRecord):
        """Capture log records."""
        if not self.enabled or not self.current_session:
            return

        try:
            message = self.format(record)
            context = getattr(record, 'context', {})

            self.current_session.add_log_message(
                level=record.levelname,
                message=message,
                context=context
            )
        except Exception:
            self.handleError(record)

    def record_line_attempt(self, attempt: LineParseAttempt):
        """Record a line parse attempt."""
        if self.current_session:
            self.current_session.line_attempts.append(attempt)

    def update_statistics(self, **kwargs):
        """Update statistics for current session."""
        if self.current_session:
            stats = self.current_session.statistics
            for key, value in kwargs.items():
                if hasattr(stats, key):
                    if key in ['total_credits', 'total_debits']:
                        # Decimal fields - add to existing value
                        current = getattr(stats, key)
                        setattr(stats, key, current + value)
                    elif key == 'skip_reasons' and isinstance(value, dict):
                        # Merge skip reasons
                        for reason, count in value.items():
                            stats.skip_reasons[reason] += count
                    else:
                        setattr(stats, key, value)

    def get_latest_session(self) -> Optional[ParsingSession]:
        """Get the most recent session."""
        if self.sessions:
            return self.sessions[-1]
        return self.current_session

    def clear_sessions(self):
        """Clear all collected sessions."""
        self.sessions = []
        self.current_session = None


# Global diagnostics collector
_diagnostics_collector = ParserDiagnosticsCollector()


def get_diagnostics_collector() -> ParserDiagnosticsCollector:
    """Get the global diagnostics collector."""
    return _diagnostics_collector


def configure_parser_logging(level: int = logging.INFO):
    """Configure logging for bank statement parser."""
    logger = logging.getLogger('src.bank_statement_parser')
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Add diagnostics collector
    logger.addHandler(_diagnostics_collector)

    # Add console handler for display
    console = logging.StreamHandler()
    console.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger
