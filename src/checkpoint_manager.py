"""
Checkpoint manager for tracking monthly financial data and cumulative transfers.
"""
import json
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from models import SplitResult, Person


@dataclass
class MonthlyCheckpoint:
    """Checkpoint data for a single month."""
    period: str  # YYYY-MM format
    person1_file: str
    person2_file: str
    person1_gross: str  # Stored as string for JSON
    person2_gross: str
    person1_net: str
    person2_net: str
    total_shared_expenses: str
    person1_paid: str
    person2_paid: str
    transfer_amount: str
    transfer_from: str  # Person name
    transfer_to: str
    person1_remaining: str
    person2_remaining: str
    calculated_date: str  # ISO format


@dataclass
class CumulativeState:
    """Cumulative financial state across all months."""
    total_transfers_person1_to_person2: str  # Running total
    total_transfers_person2_to_person1: str
    net_transfer_amount: str  # Who owes whom overall
    net_transfer_from: str
    net_transfer_to: str
    months_processed: int
    last_updated: str


@dataclass
class ProcessedFile:
    """Metadata for a processed file."""
    file_path: str
    last_modified: str  # ISO timestamp
    file_size: int
    transaction_count: int
    processed_at: str  # ISO timestamp


class CheckpointManager:
    """
    Manages checkpoint data for monthly financial calculations.

    Stores:
    - Monthly calculation results
    - Cumulative transfer amounts
    - File references for each month
    - Running totals
    """

    def __init__(self, checkpoint_file: str = "financial_checkpoint.json"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_file: Path to checkpoint JSON file
        """
        self.checkpoint_file = Path(checkpoint_file)
        self.data: Dict = self._load_checkpoint()

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint data from file."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "person1_name": None,
                "person2_name": None,
                "monthly_data": {},
                "cumulative": None,
                "processed_files": {},  # Track processed files
                "processed_months": []  # Track which complete months have been processed
            }

    def _save_checkpoint(self):
        """Save checkpoint data to file."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def reset(self):
        """Reset all checkpoint data."""
        self.data = {
            "person1_name": None,
            "person2_name": None,
            "monthly_data": {},
            "cumulative": None
        }
        self._save_checkpoint()
        print(f"Checkpoint reset: {self.checkpoint_file}")

    def add_monthly_result(
        self,
        result: SplitResult,
        person1_file: str,
        person2_file: str
    ):
        """
        Add a monthly calculation result to checkpoint.

        Args:
            result: SplitResult from split calculation
            person1_file: Path to person 1's file
            person2_file: Path to person 2's file
        """
        # Store person names if not set
        if self.data["person1_name"] is None:
            self.data["person1_name"] = result.person1.name
            self.data["person2_name"] = result.person2.name

        # Create checkpoint for this month
        period_key = result.period.strftime("%Y-%m")

        checkpoint = MonthlyCheckpoint(
            period=period_key,
            person1_file=str(person1_file),
            person2_file=str(person2_file),
            person1_gross=str(result.person1_gross_income),
            person2_gross=str(result.person2_gross_income),
            person1_net=str(result.person1_net_income),
            person2_net=str(result.person2_net_income),
            total_shared_expenses=str(result.total_shared_expenses),
            person1_paid=str(result.person1_actually_paid),
            person2_paid=str(result.person2_actually_paid),
            transfer_amount=str(result.transfer_amount),
            transfer_from=result.transfer_from.name,
            transfer_to=result.transfer_to.name,
            person1_remaining=str(result.person1_remaining),
            person2_remaining=str(result.person2_remaining),
            calculated_date=datetime.now().isoformat()
        )

        # Store in monthly data
        self.data["monthly_data"][period_key] = asdict(checkpoint)

        # Update cumulative
        self._update_cumulative()

        # Save
        self._save_checkpoint()

    def _update_cumulative(self):
        """Update cumulative state based on all monthly data."""
        person1_name = self.data["person1_name"]
        person2_name = self.data["person2_name"]

        if not person1_name or not person2_name:
            return

        # Calculate running totals
        p1_to_p2 = Decimal("0")
        p2_to_p1 = Decimal("0")

        for month_key in sorted(self.data["monthly_data"].keys()):
            month_data = self.data["monthly_data"][month_key]
            transfer_amount = Decimal(month_data["transfer_amount"])
            transfer_from = month_data["transfer_from"]

            if transfer_from == person1_name:
                p1_to_p2 += transfer_amount
            else:
                p2_to_p1 += transfer_amount

        # Calculate net
        net_amount = abs(p1_to_p2 - p2_to_p1)
        if p1_to_p2 > p2_to_p1:
            net_from = person1_name
            net_to = person2_name
        else:
            net_from = person2_name
            net_to = person1_name

        cumulative = CumulativeState(
            total_transfers_person1_to_person2=str(p1_to_p2),
            total_transfers_person2_to_person1=str(p2_to_p1),
            net_transfer_amount=str(net_amount),
            net_transfer_from=net_from,
            net_transfer_to=net_to,
            months_processed=len(self.data["monthly_data"]),
            last_updated=datetime.now().isoformat()
        )

        self.data["cumulative"] = asdict(cumulative)

    def get_latest_month(self) -> Optional[str]:
        """
        Get the latest month in checkpoint.

        Returns:
            Period key (YYYY-MM) or None if no data
        """
        if not self.data["monthly_data"]:
            return None
        return max(self.data["monthly_data"].keys())

    def get_latest_files(self) -> Optional[Tuple[str, str]]:
        """
        Get the file paths from the latest month.

        Returns:
            Tuple of (person1_file, person2_file) or None
        """
        latest = self.get_latest_month()
        if not latest:
            return None

        month_data = self.data["monthly_data"][latest]
        return (month_data["person1_file"], month_data["person2_file"])

    def get_expected_next_files(self) -> Optional[Tuple[str, str]]:
        """
        Get the expected file paths for the next month based on pattern.

        Returns:
            Tuple of (person1_file, person2_file) or None
        """
        latest_files = self.get_latest_files()
        if not latest_files:
            return None

        person1_file, person2_file = latest_files

        # Try to increment the month
        from datetime import datetime
        latest_month = self.get_latest_month()
        if latest_month:
            # Parse YYYY-MM
            year, month = map(int, latest_month.split('-'))

            # Increment month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year

            next_date = date(next_year, next_month, 1)

            # Try to infer filename pattern
            p1_path = Path(person1_file)
            p2_path = Path(person2_file)

            # Replace month/year in filename
            # Assumes format like "Name_Month_Year.xlsx"
            next_p1 = self._increment_filename(person1_file, next_date)
            next_p2 = self._increment_filename(person2_file, next_date)

            return (next_p1, next_p2)

        return None

    def _increment_filename(self, filepath: str, next_date: date) -> str:
        """
        Increment filename to next month.

        Handles formats like:
        - Name_April_2024.xlsx -> Name_May_2024.xlsx
        - Name_2024_04.xlsx -> Name_2024_05.xlsx
        """
        path = Path(filepath)
        name_parts = path.stem.split('_')

        # Try to find and replace month/year
        new_parts = []
        month_name = next_date.strftime("%B")
        month_num = f"{next_date.month:02d}"
        year = str(next_date.year)

        for part in name_parts:
            # Check if it's a year
            if part.isdigit() and len(part) == 4:
                new_parts.append(year)
            # Check if it's a month number
            elif part.isdigit() and 1 <= int(part) <= 12:
                new_parts.append(month_num)
            # Check if it's a month name (case insensitive)
            elif any(part.lower() == m.lower() for m in [
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ]):
                new_parts.append(month_name)
            else:
                new_parts.append(part)

        return str(path.parent / f"{'_'.join(new_parts)}{path.suffix}")

    def get_monthly_summary(self) -> str:
        """Get a formatted summary of all monthly data."""
        if not self.data["monthly_data"]:
            return "No monthly data recorded."

        lines = []
        lines.append("=" * 100)
        lines.append("MONTHLY CHECKPOINT SUMMARY")
        lines.append("=" * 100)
        lines.append("")

        person1_name = self.data["person1_name"]
        person2_name = self.data["person2_name"]

        # Header
        lines.append(f"{'Month': <12} {'Gross Income': >30} {'Shared Exp': >15} {'Transfer': >25}")
        lines.append(f"{'': <12} {person1_name: >13}  {person2_name: >13} {'': >15} {'Amount': >12} {'From -> To': >12}")
        lines.append("-" * 100)

        # Monthly rows
        total_p1_gross = Decimal("0")
        total_p2_gross = Decimal("0")
        total_expenses = Decimal("0")

        for month_key in sorted(self.data["monthly_data"].keys()):
            month_data = self.data["monthly_data"][month_key]

            p1_gross = Decimal(month_data["person1_gross"])
            p2_gross = Decimal(month_data["person2_gross"])
            expenses = Decimal(month_data["total_shared_expenses"])
            transfer = Decimal(month_data["transfer_amount"])
            transfer_from = month_data["transfer_from"]
            transfer_to = month_data["transfer_to"]

            total_p1_gross += p1_gross
            total_p2_gross += p2_gross
            total_expenses += expenses

            # Abbreviate names for transfer display
            from_abbrev = transfer_from[:3]
            to_abbrev = transfer_to[:3]

            lines.append(
                f"{month_key: <12} "
                f"R{p1_gross: >12,.2f}  R{p2_gross: >12,.2f} "
                f"R{expenses: >13,.2f} "
                f"R{transfer: >11,.2f} {from_abbrev}->{to_abbrev: <8}"
            )

        lines.append("-" * 100)
        lines.append(
            f"{'TOTAL': <12} "
            f"R{total_p1_gross: >12,.2f}  R{total_p2_gross: >12,.2f} "
            f"R{total_expenses: >13,.2f}"
        )

        # Cumulative section
        if self.data["cumulative"]:
            lines.append("")
            lines.append("=" * 100)
            lines.append("CUMULATIVE TRANSFERS")
            lines.append("=" * 100)

            cum = self.data["cumulative"]
            p1_to_p2 = Decimal(cum["total_transfers_person1_to_person2"])
            p2_to_p1 = Decimal(cum["total_transfers_person2_to_person1"])
            net_amount = Decimal(cum["net_transfer_amount"])
            net_from = cum["net_transfer_from"]
            net_to = cum["net_transfer_to"]

            lines.append(f"Total {person1_name} -> {person2_name}: R{p1_to_p2:,.2f}")
            lines.append(f"Total {person2_name} -> {person1_name}: R{p2_to_p1:,.2f}")
            lines.append("")
            lines.append(f"** NET: {net_from} should transfer R{net_amount:,.2f} to {net_to} **")
            lines.append("")
            lines.append(f"Months processed: {cum['months_processed']}")
            lines.append(f"Last updated: {datetime.fromisoformat(cum['last_updated']).strftime('%Y-%m-%d %H:%M')}")

        lines.append("=" * 100)

        return "\n".join(lines)

    def month_exists(self, period: date) -> bool:
        """Check if a month already exists in checkpoint."""
        period_key = period.strftime("%Y-%m")
        return period_key in self.data["monthly_data"]

    def get_month_data(self, period: date) -> Optional[Dict]:
        """Get checkpoint data for a specific month."""
        period_key = period.strftime("%Y-%m")
        return self.data["monthly_data"].get(period_key)

    def get_cumulative_state(self) -> Optional[Dict]:
        """Get the current cumulative state."""
        return self.data["cumulative"]

    def mark_file_processed(
        self,
        file_path: str,
        transaction_count: int = 0
    ) -> None:
        """
        Mark a file as processed.

        Args:
            file_path: Path to the processed file
            transaction_count: Number of transactions extracted
        """
        path = Path(file_path)
        if not path.exists():
            return

        file_metadata = ProcessedFile(
            file_path=str(path),
            last_modified=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            file_size=path.stat().st_size,
            transaction_count=transaction_count,
            processed_at=datetime.now().isoformat()
        )

        if "processed_files" not in self.data:
            self.data["processed_files"] = {}

        self.data["processed_files"][str(path)] = asdict(file_metadata)
        self._save_checkpoint()

    def is_file_processed(self, file_path: str) -> bool:
        """
        Check if a file has been processed and hasn't changed.

        Args:
            file_path: Path to check

        Returns:
            True if file is already processed and unchanged
        """
        if "processed_files" not in self.data:
            return False

        path = Path(file_path)
        if not path.exists():
            return False

        file_key = str(path)
        if file_key not in self.data["processed_files"]:
            return False

        # Check if file has been modified since processing
        stored = self.data["processed_files"][file_key]
        current_mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()

        return stored["last_modified"] == current_mtime

    def get_unprocessed_files(self, file_list: List[str]) -> List[str]:
        """
        Filter file list to only unprocessed or modified files.

        Args:
            file_list: List of file paths to check

        Returns:
            List of files that need processing
        """
        return [f for f in file_list if not self.is_file_processed(f)]

    def clear_processed_files(self) -> None:
        """Clear all processed file tracking (for force mode)."""
        if "processed_files" in self.data:
            self.data["processed_files"] = {}
            self._save_checkpoint()
        print("Cleared processed file tracking")

    def mark_month_processed(self, year: int, month: int) -> None:
        """
        Mark a complete month as processed.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
        """
        if "processed_months" not in self.data:
            self.data["processed_months"] = []

        month_key = f"{year}-{month:02d}"
        if month_key not in self.data["processed_months"]:
            self.data["processed_months"].append(month_key)
            self.data["processed_months"].sort()  # Keep sorted
            self._save_checkpoint()

    def is_month_processed(self, year: int, month: int) -> bool:
        """
        Check if a complete month has been processed.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            True if month has been processed
        """
        if "processed_months" not in self.data:
            return False

        month_key = f"{year}-{month:02d}"
        return month_key in self.data["processed_months"]

    def get_processed_months(self) -> List[Tuple[int, int]]:
        """
        Get list of all processed months.

        Returns:
            List of (year, month) tuples
        """
        if "processed_months" not in self.data:
            return []

        months = []
        for month_key in self.data["processed_months"]:
            year, month = map(int, month_key.split('-'))
            months.append((year, month))
        return months

    def get_unprocessed_months(self, available_months: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Get list of available months that haven't been processed yet.

        Args:
            available_months: List of (year, month) tuples that have complete data

        Returns:
            List of (year, month) tuples that need processing
        """
        processed = set(self.get_processed_months())
        available_set = set(available_months)
        unprocessed = available_set - processed
        return sorted(list(unprocessed))

    def clear_processed_months(self) -> None:
        """Clear all processed month tracking (for force mode)."""
        if "processed_months" in self.data:
            self.data["processed_months"] = []
            self._save_checkpoint()
        print("Cleared processed month tracking")


def auto_detect_next_month_files(
    checkpoint_file: str = "financial_checkpoint.json"
) -> Optional[Tuple[str, str]]:
    """
    Auto-detect the next month's files based on checkpoint.

    Args:
        checkpoint_file: Path to checkpoint file

    Returns:
        Tuple of (person1_file, person2_file) or None
    """
    manager = CheckpointManager(checkpoint_file)
    return manager.get_expected_next_files()
