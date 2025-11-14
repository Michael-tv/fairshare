"""
Month Validator

Validates that transaction data covers complete months only.
Prevents partial month data from being included in processing.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

import pandas as pd

from transaction_matcher import BankStatementParser, BankTransaction


class MonthValidator:
    """Validates transaction data completeness by month"""

    def __init__(self):
        pass

    def get_transaction_date_range(self, transactions: List[BankTransaction]) -> Tuple[Optional[date], Optional[date]]:
        """
        Get the min and max dates from a list of transactions.

        Args:
            transactions: List of bank transactions

        Returns:
            Tuple of (min_date, max_date) or (None, None) if no transactions
        """
        if not transactions:
            return None, None

        dates = [t.date.date() if isinstance(t.date, datetime) else t.date for t in transactions]
        return min(dates), max(dates)

    def get_complete_months(self, min_date: date, max_date: date) -> List[Tuple[int, int]]:
        """
        Determine which complete months are covered by a date range.

        A complete month is one where we have data from the 1st to the last day.

        IMPORTANT: This method only checks the min and max dates, not whether
        transactions exist on every day. Use get_complete_months_from_transactions()
        for actual transaction validation.

        Args:
            min_date: Earliest transaction date
            max_date: Latest transaction date

        Returns:
            List of (year, month) tuples for complete months
        """
        if not min_date or not max_date:
            return []

        complete_months = []

        # Start from the first complete month after min_date
        if min_date.day == 1:
            start_year, start_month = min_date.year, min_date.month
        else:
            # If data doesn't start on the 1st, skip this month
            if min_date.month == 12:
                start_year, start_month = min_date.year + 1, 1
            else:
                start_year, start_month = min_date.year, min_date.month + 1

        # End at the last complete month before max_date
        # A month is complete if max_date is the last day of that month
        end_year, end_month = max_date.year, max_date.month

        # Check if max_date is the last day of its month
        if max_date.month == 12:
            next_month_start = date(max_date.year + 1, 1, 1)
        else:
            next_month_start = date(max_date.year, max_date.month + 1, 1)

        from datetime import timedelta
        last_day_of_month = next_month_start - timedelta(days=1)

        if max_date != last_day_of_month:
            # If data doesn't end on the last day, exclude this month
            if end_month == 1:
                end_year, end_month = end_year - 1, 12
            else:
                end_month = end_month - 1

        # Build list of complete months
        current_year, current_month = start_year, start_month
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            complete_months.append((current_year, current_month))

            if current_month == 12:
                current_year += 1
                current_month = 1
            else:
                current_month += 1

        return complete_months

    def get_complete_months_from_statements(self, statement_files: List[Path]) -> List[Tuple[int, int]]:
        """
        Determine which complete calendar months are covered by bank statement files.

        A calendar month is complete if it is fully covered by statements with NO GAPS.
        This is conservative: we check that statements form a continuous chain with
        consecutive statements overlapping or being adjacent (max 1 day gap to account
        for statement generation timing).

        Args:
            statement_files: List of PDF paths for bank statements

        Returns:
            List of (year, month) tuples for complete months
        """
        if not statement_files:
            return []

        from datetime import timedelta

        # Parse all statements and get their date ranges
        statement_ranges = []
        for pdf_file in statement_files:
            try:
                # Determine statement type by detecting format markers
                import PyPDF2
                transactions = None

                try:
                    with open(pdf_file, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        if len(reader.pages) > 0:
                            first_page = reader.pages[0].extract_text()
                        else:
                            first_page = ""
                except Exception:
                    first_page = ""

                # Check for FNB Fusion format (Afrikaans or English)
                if ("FUSION PRIVATE CLIENTS" in first_page.upper() or
                    "Datum Beskrywing Bedrag" in first_page or
                    "Date Description Amount" in first_page):
                    transactions = BankStatementParser.parse_fnb_fusion_account_statement(str(pdf_file))
                # Check for credit card format
                elif "CREDIT_CARD" in pdf_file.name.upper() or "CREDIT CARD" in first_page.upper():
                    transactions = BankStatementParser.parse_fnb_credit_card_statement(str(pdf_file))
                # Default to personal account format
                else:
                    transactions = BankStatementParser.parse_fnb_personal_account_statement(str(pdf_file))

                if transactions:
                    dates = [t.date.date() if isinstance(t.date, datetime) else t.date for t in transactions]
                    min_date = min(dates)
                    max_date = max(dates)
                    statement_ranges.append((min_date, max_date))
            except Exception:
                # Skip files that can't be parsed
                continue

        if not statement_ranges:
            return []

        # Sort statements by start date
        statement_ranges.sort()

        # Build coverage periods by merging consecutive/overlapping statements
        # Allow up to 1 day gap to account for statement generation timing
        coverage_periods = []
        current_start, current_end = statement_ranges[0]

        for i in range(1, len(statement_ranges)):
            stmt_start, stmt_end = statement_ranges[i]

            # Check if this statement continues from the previous one
            # Allow overlap or up to 1 day gap
            gap = (stmt_start - current_end).days

            if gap <= 1:
                # Extend the current coverage period
                current_end = max(current_end, stmt_end)
            else:
                # Gap detected - save current period and start new one
                coverage_periods.append((current_start, current_end))
                current_start, current_end = stmt_start, stmt_end

        # Don't forget the last period
        coverage_periods.append((current_start, current_end))

        # Now check which complete months are covered by these continuous periods
        complete_months = []

        for period_start, period_end in coverage_periods:
            # Check each month within this continuous coverage period
            current_date = date(period_start.year, period_start.month, 1)

            while current_date <= period_end:
                year = current_date.year
                month = current_date.month

                # Calculate first and last day of this month
                first_day = date(year, month, 1)
                if month == 12:
                    last_day = date(year, 12, 31)
                    next_month = date(year + 1, 1, 1)
                else:
                    next_month = date(year, month + 1, 1)
                    last_day = next_month - timedelta(days=1)

                # Check if this continuous period covers the entire month
                if period_start <= first_day and period_end >= last_day:
                    if (year, month) not in complete_months:
                        complete_months.append((year, month))

                # Move to next month
                current_date = next_month

        return sorted(complete_months)

    def validate_statements_coverage(
        self,
        statement_files: Dict[str, List[Path]]
    ) -> Dict[str, Dict]:
        """
        Validate that statement files cover complete months.

        Args:
            statement_files: Dict mapping person/account names to list of PDF paths

        Returns:
            Dict with validation results per person/account:
            {
                'person_name': {
                    'transaction_count': int,
                    'date_range': (min_date, max_date),
                    'complete_months': [(year, month), ...],
                    'has_complete_data': bool
                }
            }
        """
        results = {}

        for name, pdf_files in statement_files.items():
            all_transactions = []

            for pdf_file in pdf_files:
                try:
                    # Determine statement type by detecting format markers
                    import PyPDF2
                    transactions = None

                    try:
                        with open(pdf_file, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            if len(reader.pages) > 0:
                                first_page = reader.pages[0].extract_text()
                            else:
                                first_page = ""
                    except Exception:
                        first_page = ""

                    # Check for FNB Fusion format (Afrikaans or English)
                    if ("FUSION PRIVATE CLIENTS" in first_page.upper() or
                        "Datum Beskrywing Bedrag" in first_page or
                        "Date Description Amount" in first_page):
                        transactions = BankStatementParser.parse_fnb_fusion_account_statement(str(pdf_file))
                    # Check for credit card format
                    elif "CREDIT_CARD" in pdf_file.name.upper() or "CREDIT CARD" in first_page.upper():
                        transactions = BankStatementParser.parse_fnb_credit_card_statement(str(pdf_file))
                    # Default to personal account format
                    else:
                        transactions = BankStatementParser.parse_fnb_personal_account_statement(str(pdf_file))

                    if transactions:
                        all_transactions.extend(transactions)
                except Exception as e:
                    # Skip files that can't be parsed
                    continue

            min_date, max_date = self.get_transaction_date_range(all_transactions)
            # Use statement-based validation that checks coverage per statement file
            complete_months = self.get_complete_months_from_statements(pdf_files)

            results[name] = {
                'transaction_count': len(all_transactions),
                'date_range': (min_date, max_date),
                'complete_months': complete_months,
                'has_complete_data': len(complete_months) > 0
            }

        return results

    def validate_manual_transactions_coverage(
        self,
        manual_file: Path
    ) -> Dict:
        """
        Validate that manual transaction file covers complete months.

        Args:
            manual_file: Path to Excel file with manual transactions

        Returns:
            Validation result dict
        """
        try:
            df = pd.read_excel(manual_file)

            if 'date' not in df.columns:
                return {
                    'transaction_count': 0,
                    'date_range': (None, None),
                    'complete_months': [],
                    'has_complete_data': False,
                    'error': 'No date column found'
                }

            # Convert dates
            df['date'] = pd.to_datetime(df['date'])
            dates = [d.date() for d in df['date']]

            min_date = min(dates)
            max_date = max(dates)
            complete_months = self.get_complete_months(min_date, max_date)

            return {
                'transaction_count': len(df),
                'date_range': (min_date, max_date),
                'complete_months': complete_months,
                'has_complete_data': len(complete_months) > 0
            }

        except Exception as e:
            return {
                'transaction_count': 0,
                'date_range': (None, None),
                'complete_months': [],
                'has_complete_data': False,
                'error': str(e)
            }

    def get_common_complete_months(
        self,
        validation_results: Dict[str, Dict]
    ) -> List[Tuple[int, int]]:
        """
        Get months that are complete across all persons/accounts.

        Args:
            validation_results: Dict from validate_statements_coverage()

        Returns:
            List of (year, month) tuples that all persons have complete data for
        """
        if not validation_results:
            return []

        # Get complete months for each person
        all_month_sets = []
        for name, result in validation_results.items():
            if result['has_complete_data']:
                month_set = set(result['complete_months'])
                all_month_sets.append(month_set)

        if not all_month_sets:
            return []

        # Find intersection - months that ALL people have
        common_months = set.intersection(*all_month_sets)

        # Sort by year, month
        return sorted(list(common_months))

    def filter_transactions_by_months(
        self,
        transactions: List[BankTransaction],
        valid_months: List[Tuple[int, int]]
    ) -> List[BankTransaction]:
        """
        Filter transactions to only include those from valid complete months.

        Args:
            transactions: List of transactions
            valid_months: List of (year, month) tuples to include

        Returns:
            Filtered list of transactions
        """
        if not valid_months:
            return []

        valid_month_set = set(valid_months)
        filtered = []

        for txn in transactions:
            txn_date = txn.date.date() if isinstance(txn.date, datetime) else txn.date
            txn_month = (txn_date.year, txn_date.month)

            if txn_month in valid_month_set:
                filtered.append(txn)

        return filtered

    def generate_validation_report(
        self,
        validation_results: Dict[str, Dict],
        common_months: List[Tuple[int, int]]
    ) -> str:
        """
        Generate a human-readable validation report.

        Args:
            validation_results: Results from validate_statements_coverage()
            common_months: Results from get_common_complete_months()

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("TRANSACTION DATA VALIDATION")
        lines.append("=" * 80)
        lines.append("")

        for name, result in validation_results.items():
            lines.append(f"{name}:")
            lines.append(f"  Transactions: {result['transaction_count']}")

            if result['date_range'][0]:
                min_date, max_date = result['date_range']
                lines.append(f"  Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
            else:
                lines.append(f"  Date range: No data")

            if result.get('error'):
                lines.append(f"  Error: {result['error']}")
            elif result['complete_months']:
                month_strs = [f"{y}-{m:02d}" for y, m in result['complete_months']]
                lines.append(f"  Complete months: {', '.join(month_strs)}")
            else:
                lines.append(f"  Complete months: None (partial month data)")

            lines.append("")

        lines.append("-" * 80)
        lines.append("COMMON COMPLETE MONTHS (all persons):")
        lines.append("-" * 80)

        if common_months:
            month_strs = [f"{y}-{m:02d}" for y, m in common_months]
            lines.append(f"  {', '.join(month_strs)}")
            lines.append(f"  Total: {len(common_months)} complete months")
        else:
            lines.append("  None - no complete months with data from all persons")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)
