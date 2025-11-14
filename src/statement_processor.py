"""
Statement Processor

Orchestrates the complete statement processing pipeline:
1. Scans account folders for PDF statements
2. Extracts transactions using BankStatementParser
3. Classifies transactions using TransactionClassifier
4. Manages dual-layer architecture (statement storage + month views)
5. Tracks processing state
"""

import json
import hashlib
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

import pandas as pd

from src.bank_statement_parser import BankStatementParser, BankTransaction, BankStatementSummary
from src.bank_template import TemplateRegistry
from src.transaction_classifier import TransactionClassifier
from src.config_manager import Config, UserConfig, AccountConfig, SharedAccountConfig


class ProcessingStatus(Enum):
    """Processing status for statements"""
    UNPROCESSED = "unprocessed"
    EXTRACTED = "extracted"
    CLASSIFIED = "classified"
    ERROR = "error"


@dataclass
class StatementRecord:
    """Record for tracking statement processing state"""
    id: str  # Unique ID: hash of account_name + filename
    account_name: str
    account_owner: Optional[str]  # User name or "Shared"
    is_shared_account: bool
    filename: str
    file_path: str
    status: str  # ProcessingStatus value
    statement_period_start: Optional[str]  # ISO date
    statement_period_end: Optional[str]  # ISO date
    months_covered: List[str]  # ["YYYY-MM", ...]
    transaction_count: int
    total_in: float
    total_out: float
    breakdown: Dict[str, float]  # {"household": 0, "michael": 0, "sarah": 0}
    last_processed: Optional[str]  # ISO datetime
    error_message: Optional[str] = None


class StatementProcessor:
    """
    Manages statement processing pipeline and state tracking.
    """

    def __init__(
        self,
        config: Config,
        templates_dir: Path = Path("bank_templates"),
        learned_rules_path: Optional[Path] = None
    ):
        """
        Initialize statement processor.

        Args:
            config: Application configuration
            templates_dir: Directory containing bank templates
            learned_rules_path: Path to learned classification rules
        """
        self.config = config
        self.working_dir = config.working_dir
        self.templates_dir = templates_dir
        self.template_registry = TemplateRegistry(templates_dir)

        # Initialize classifier
        self.classifier = TransactionClassifier(
            learned_rules_path=learned_rules_path,
            use_learned=True
        )

        # State file path
        self.state_file = self.working_dir / "statements_processing_state.json"

        # Load existing state
        self.statements: Dict[str, StatementRecord] = self._load_state()

    def _generate_statement_id(self, account_name: str, filename: str) -> str:
        """Generate unique ID for statement"""
        key = f"{account_name}_{filename}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def _load_state(self) -> Dict[str, StatementRecord]:
        """Load processing state from JSON file"""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            statements = {}
            for stmt_data in data.get('statements', []):
                stmt = StatementRecord(**stmt_data)
                statements[stmt.id] = stmt

            return statements
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
            return {}

    def _save_state(self):
        """Save processing state to JSON file"""
        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'last_updated': datetime.now().isoformat(),
            'statements': [asdict(stmt) for stmt in self.statements.values()]
        }

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def scan_for_statements(self) -> List[StatementRecord]:
        """
        Scan all account folders for PDF statements.

        Returns:
            List of new or updated statement records
        """
        new_statements = []

        # Scan user accounts
        for user in self.config.users:
            for account in user.accounts:
                statements = self._scan_account_folder(
                    account_name=account.name,
                    account_owner=user.name,
                    statements_folder=self.working_dir / account.statements_folder,
                    processed_folder=self.working_dir / account.processed_folder,
                    is_shared=False
                )
                new_statements.extend(statements)

        # Scan shared accounts
        for account in self.config.shared_accounts:
            statements = self._scan_account_folder(
                account_name=account.name,
                account_owner="Shared",
                statements_folder=self.working_dir / account.statements_folder,
                processed_folder=self.working_dir / account.processed_folder,
                is_shared=True
            )
            new_statements.extend(statements)

        # Save state
        self._save_state()

        return new_statements

    def _scan_account_folder(
        self,
        account_name: str,
        account_owner: str,
        statements_folder: Path,
        processed_folder: Path,
        is_shared: bool
    ) -> List[StatementRecord]:
        """Scan a single account folder for PDF statements"""
        new_statements = []

        if not statements_folder.exists():
            return new_statements

        # Find all PDF files
        pdf_files = list(statements_folder.glob("*.pdf")) + list(statements_folder.glob("*.PDF"))

        for pdf_path in pdf_files:
            stmt_id = self._generate_statement_id(account_name, pdf_path.name)

            # Check if already exists and is processed
            if stmt_id in self.statements:
                existing = self.statements[stmt_id]
                # Update file path in case it moved
                if existing.file_path != str(pdf_path):
                    existing.file_path = str(pdf_path)
                continue

            # Create new record
            record = StatementRecord(
                id=stmt_id,
                account_name=account_name,
                account_owner=account_owner,
                is_shared_account=is_shared,
                filename=pdf_path.name,
                file_path=str(pdf_path),
                status=ProcessingStatus.UNPROCESSED.value,
                statement_period_start=None,
                statement_period_end=None,
                months_covered=[],
                transaction_count=0,
                total_in=0.0,
                total_out=0.0,
                breakdown={},
                last_processed=None
            )

            self.statements[stmt_id] = record
            new_statements.append(record)

        return new_statements

    def process_statement(
        self,
        statement_id: str,
        force: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a single statement through extraction and classification.

        Args:
            statement_id: Statement ID to process
            force: If True, reprocess even if already processed

        Returns:
            Tuple of (success, error_message)
        """
        if statement_id not in self.statements:
            return False, "Statement not found"

        record = self.statements[statement_id]

        # Check if already processed
        if not force and record.status == ProcessingStatus.CLASSIFIED.value:
            return True, None

        try:
            # Step 1: Extract transactions from PDF
            success, error = self._extract_statement(record)
            if not success:
                record.status = ProcessingStatus.ERROR.value
                record.error_message = error
                self._save_state()
                return False, error

            # Step 2: Classify transactions
            success, error = self._classify_statement(record)
            if not success:
                record.status = ProcessingStatus.ERROR.value
                record.error_message = error
                self._save_state()
                return False, error

            # Update status
            record.status = ProcessingStatus.CLASSIFIED.value
            record.last_processed = datetime.now().isoformat()
            record.error_message = None
            self._save_state()

            return True, None

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            record.status = ProcessingStatus.ERROR.value
            record.error_message = error_msg
            self._save_state()
            return False, error_msg

    def _extract_statement(self, record: StatementRecord) -> Tuple[bool, Optional[str]]:
        """Extract transactions from PDF"""
        try:
            pdf_path = Path(record.file_path)

            # Parse PDF using template auto-detection
            parser = BankStatementParser.create(pdf_path, templates_dir=self.templates_dir)
            summary, transactions = parser.parse()

            if not transactions:
                return False, "No transactions found in statement"

            # Update record with statement info
            record.statement_period_start = summary.statement_date.isoformat()
            record.statement_period_end = summary.statement_date.isoformat()
            record.transaction_count = len(transactions)

            # Calculate totals
            total_in = sum(t.amount for t in transactions if t.is_credit)
            total_out = sum(t.amount for t in transactions if not t.is_credit)
            record.total_in = float(total_in)
            record.total_out = float(total_out)

            # Determine months covered
            months = set()
            for trans in transactions:
                month_str = trans.date.strftime("%Y-%m")
                months.add(month_str)
            record.months_covered = sorted(list(months))

            # Save to statements folder (Layer 1: Statement storage)
            statements_dir = self._get_statements_dir(record)
            statements_dir.mkdir(parents=True, exist_ok=True)

            raw_excel_path = statements_dir / f"{record.id}_raw.xlsx"
            self._save_raw_transactions(transactions, summary, raw_excel_path)

            record.status = ProcessingStatus.EXTRACTED.value
            self._save_state()

            return True, None

        except Exception as e:
            return False, f"Extraction failed: {str(e)}"

    def _classify_statement(self, record: StatementRecord) -> Tuple[bool, Optional[str]]:
        """Classify transactions"""
        try:
            # Load raw transactions
            statements_dir = self._get_statements_dir(record)
            raw_excel_path = statements_dir / f"{record.id}_raw.xlsx"

            if not raw_excel_path.exists():
                return False, "Raw transactions file not found"

            # Read raw Excel
            df = pd.read_excel(raw_excel_path, sheet_name="Transactions")

            # Classify each transaction
            categories = []
            types = []
            assigned_users = []

            user_names = self.config.get_user_names() if self.config else []
            if not user_names:
                print("Warning: No users configured")

            for _, row in df.iterrows():
                description = row['Description']
                amount = Decimal(str(row['Amount']))

                # Classify
                category, exp_type = self.classifier.classify_transaction(
                    description,
                    amount,
                    is_shared_account=record.is_shared_account
                )

                categories.append(category)
                types.append(exp_type)

                # Assign user (for personal expenses on shared accounts)
                if record.is_shared_account and exp_type == "INDIVIDUAL":
                    # Default to first user for now (can be corrected in UI)
                    assigned_users.append(user_names[0] if user_names else "Unassigned")
                else:
                    assigned_users.append("")

            # Add classification columns
            df['Category'] = categories
            df['Type'] = types
            df['Assigned User'] = assigned_users

            # Calculate breakdown
            breakdown = {"household": 0.0}
            if user_names:
                for user_name in user_names:
                    breakdown[user_name.lower()] = 0.0

            for _, row in df.iterrows():
                amount = float(row['Amount'])
                exp_type = row['Type']
                assigned_user = row['Assigned User']

                if not row['Is Credit']:  # Only count expenses
                    if exp_type == "HOUSEHOLD" or exp_type == "SHARED":
                        breakdown["household"] += amount
                    elif exp_type == "INDIVIDUAL" and assigned_user:
                        user_key = assigned_user.lower()
                        if user_key in breakdown:
                            breakdown[user_key] += amount

            record.breakdown = breakdown

            # Save classified Excel
            classified_excel_path = statements_dir / f"{record.id}_classified.xlsx"
            df.to_excel(classified_excel_path, index=False, sheet_name="Transactions")

            # Also save to month folders (Layer 2: Month views)
            self._save_to_month_folders(df, record)

            record.status = ProcessingStatus.CLASSIFIED.value
            self._save_state()

            return True, None

        except Exception as e:
            return False, f"Classification failed: {str(e)}"

    def _save_raw_transactions(
        self,
        transactions: List[BankTransaction],
        summary: BankStatementSummary,
        output_path: Path
    ):
        """Save raw extracted transactions to Excel"""
        data = {
            'Date': [t.date for t in transactions],
            'Description': [t.description for t in transactions],
            'Amount': [float(t.amount) for t in transactions],
            'Is Credit': [t.is_credit for t in transactions],
            'Account Type': [t.account_type for t in transactions],
            'Card Last Digits': [t.card_last_digits or '' for t in transactions],
            'Location': [t.location or '' for t in transactions]
        }

        df = pd.DataFrame(data)

        # Create Excel with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Transactions", index=False)

            # Add summary sheet
            summary_data = {
                'Field': ['Statement Date', 'Opening Balance', 'Closing Balance',
                         'Total Expenses', 'Total Payments', 'Interest/Fees'],
                'Value': [
                    summary.statement_date.strftime('%Y-%m-%d'),
                    float(summary.opening_balance),
                    float(summary.closing_balance),
                    float(summary.total_expenses),
                    float(summary.total_payments),
                    float(summary.interest_fees)
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

    def _save_to_month_folders(self, df: pd.DataFrame, record: StatementRecord):
        """Save transactions to month-specific folders"""
        # Group by month
        df['Month'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m')

        for month in df['Month'].unique():
            month_df = df[df['Month'] == month].copy()
            month_df = month_df.drop(columns=['Month'])

            # Create month folder
            months_dir = self._get_months_dir(record)
            month_dir = months_dir / month
            month_dir.mkdir(parents=True, exist_ok=True)

            # Save consolidated transactions
            month_file = month_dir / f"{record.account_name.replace(' ', '_')}_transactions.xlsx"
            month_df.to_excel(month_file, index=False, sheet_name="Transactions")

    def _get_statements_dir(self, record: StatementRecord) -> Path:
        """Get statements directory for an account"""
        # Find the account's processed folder
        for user in self.config.users:
            for account in user.accounts:
                if account.name == record.account_name:
                    base_dir = self.working_dir / account.processed_folder
                    return base_dir / "statements"

        for account in self.config.shared_accounts:
            if account.name == record.account_name:
                base_dir = self.working_dir / account.processed_folder
                return base_dir / "statements"

        # Fallback
        return self.working_dir / "processed" / "statements"

    def _get_months_dir(self, record: StatementRecord) -> Path:
        """Get months directory for an account"""
        # Find the account's processed folder
        for user in self.config.users:
            for account in user.accounts:
                if account.name == record.account_name:
                    base_dir = self.working_dir / account.processed_folder
                    return base_dir / "months"

        for account in self.config.shared_accounts:
            if account.name == record.account_name:
                base_dir = self.working_dir / account.processed_folder
                return base_dir / "months"

        # Fallback
        return self.working_dir / "processed" / "months"

    def get_all_statements(self) -> List[StatementRecord]:
        """Get all statement records"""
        return list(self.statements.values())

    def get_statements_by_status(self, status: ProcessingStatus) -> List[StatementRecord]:
        """Get statements filtered by status"""
        return [s for s in self.statements.values() if s.status == status.value]

    def get_statement(self, statement_id: str) -> Optional[StatementRecord]:
        """Get a specific statement record"""
        return self.statements.get(statement_id)

    def delete_statement_data(self, statement_id: str) -> Tuple[bool, Optional[str]]:
        """Delete processed data for a statement (keeps the record as UNPROCESSED)"""
        if statement_id not in self.statements:
            return False, "Statement not found"

        record = self.statements[statement_id]

        try:
            # Delete statement files
            statements_dir = self._get_statements_dir(record)
            raw_file = statements_dir / f"{record.id}_raw.xlsx"
            classified_file = statements_dir / f"{record.id}_classified.xlsx"

            if raw_file.exists():
                raw_file.unlink()
            if classified_file.exists():
                classified_file.unlink()

            # Delete month files (more complex - need to track which files belong to this statement)
            # For now, we'll leave month files alone as they may contain data from multiple statements

            # Reset record
            record.status = ProcessingStatus.UNPROCESSED.value
            record.statement_period_start = None
            record.statement_period_end = None
            record.months_covered = []
            record.transaction_count = 0
            record.total_in = 0.0
            record.total_out = 0.0
            record.breakdown = {}
            record.last_processed = None
            record.error_message = None

            self._save_state()

            return True, None

        except Exception as e:
            return False, f"Failed to delete data: {str(e)}"
