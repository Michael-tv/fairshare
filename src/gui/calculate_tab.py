"""
Calculate tab - Fair share split calculation from processed transactions.
"""

from pathlib import Path
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import pandas as pd
from typing import List, Dict, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from config_manager import ConfigManager, Config
from models import Person, Income, Expense, FinancialPeriod, IncomeType, ExpenseType, ExpenseCategory
from split_calculator import FinancialSplitter
from checkpoint_manager import CheckpointManager
from reports import ReportGenerator
from gui.dialogs import ResultsDialog


class CalculationThread(QThread):
    """Background thread for performing calculations from processed transactions."""

    finished = pyqtSignal(object, object)  # result, error
    progress = pyqtSignal(str)

    def __init__(self, config: Config, selected_month: str, use_gross_mode: bool):
        super().__init__()
        self.config = config
        self.selected_month = selected_month
        self.use_gross_mode = use_gross_mode

    def run(self):
        """Run the calculation in background."""
        try:
            self.progress.emit("Loading transactions from processed files...")

            # Load all transactions for the selected month
            all_transactions = self._load_monthly_transactions()

            self.progress.emit("Analyzing transactions and calculating income...")

            # Build financial period from transactions
            period = self._build_financial_period(all_transactions)

            if len(period.people) < 2:
                raise Exception("Need at least 2 users with transactions to calculate fair share")

            self.progress.emit("Calculating fair share split...")

            # Calculate split
            splitter = FinancialSplitter()
            result = splitter.calculate_split(
                period,
                period.people[0],
                period.people[1],
                skip_tax_calculation=not self.use_gross_mode
            )

            self.progress.emit("Saving to checkpoint...")

            # Save to checkpoint
            checkpoint = CheckpointManager()
            # Create placeholder file paths for checkpoint (using month as identifier)
            file1 = f"{period.people[0].name}_{self.selected_month}.xlsx"
            file2 = f"{period.people[1].name}_{self.selected_month}.xlsx"
            checkpoint.add_monthly_result(result, file1, file2)

            self.progress.emit("Complete!")
            self.finished.emit(result, None)

        except Exception as e:
            import traceback
            full_error = f"{str(e)}\n\nStack trace:\n{traceback.format_exc()}"
            self.finished.emit(None, full_error)

    def _load_monthly_transactions(self) -> List[Dict]:
        """Load all transactions for the selected month from all accounts."""
        all_transactions = []

        # Load from user accounts
        for user in self.config.users:
            for account in user.accounts:
                trans_file = (
                    self.config.working_dir /
                    account.processed_folder /
                    "months" /
                    self.selected_month /
                    f"{account.name.replace(' ', '_')}_transactions.xlsx"
                )

                if trans_file.exists():
                    df = pd.read_excel(trans_file)
                    for _, row in df.iterrows():
                        trans_dict = row.to_dict()
                        trans_dict['_user'] = user.name
                        trans_dict['_user_id'] = user.id
                        trans_dict['_account'] = account.name
                        all_transactions.append(trans_dict)

        # Load from shared accounts
        for account in self.config.shared_accounts:
            trans_file = (
                self.config.working_dir /
                account.processed_folder /
                "months" /
                self.selected_month /
                f"{account.name.replace(' ', '_')}_transactions.xlsx"
            )

            if trans_file.exists():
                df = pd.read_excel(trans_file)
                for _, row in df.iterrows():
                    trans_dict = row.to_dict()
                    trans_dict['_user'] = "Shared"
                    trans_dict['_user_id'] = "shared"
                    trans_dict['_account'] = account.name
                    all_transactions.append(trans_dict)

        if not all_transactions:
            raise Exception(f"No transactions found for month {self.selected_month}")

        return all_transactions

    def _build_financial_period(self, transactions: List[Dict]) -> FinancialPeriod:
        """Build a FinancialPeriod object from transaction data."""
        # Group transactions by user
        user_transactions = {}
        for trans in transactions:
            user_id = trans.get('_user_id', 'unknown')
            if user_id not in user_transactions:
                user_transactions[user_id] = []
            user_transactions[user_id].append(trans)

        # Create Person objects for each user
        people = []
        for user_id, user_trans in user_transactions.items():
            if user_id == "shared":
                continue  # Skip shared account for person creation

            # Get user name
            user_name = user_trans[0].get('_user', user_id)

            # Separate income and expenses
            income_items = []
            expense_items = []

            for trans in user_trans:
                amount = trans.get('Amount', 0)
                if pd.isna(amount):
                    continue

                amount_decimal = Decimal(str(abs(amount)))
                description = str(trans.get('Description', 'Transaction'))
                trans_type = str(trans.get('Type', '')).upper()
                assigned_user = str(trans.get('Assigned User', user_name))

                # Determine if it's income or expense based on amount sign
                # Positive = income, Negative = expense
                if amount > 0:
                    # Income
                    income_items.append(Income(
                        description=description,
                        amount=amount_decimal,
                        income_type=IncomeType.OTHER
                    ))
                else:
                    # Expense
                    # Map transaction type to expense type
                    if trans_type == "HOUSEHOLD":
                        expense_type = ExpenseType.SHARED
                    elif trans_type == "INDIVIDUAL":
                        expense_type = ExpenseType.INDIVIDUAL
                    else:
                        expense_type = ExpenseType.SHARED  # Default to shared

                    # Try to map category
                    category_str = str(trans.get('Category', '')).upper()
                    try:
                        category = ExpenseCategory[category_str] if category_str else ExpenseCategory.OTHER
                    except KeyError:
                        category = ExpenseCategory.OTHER

                    expense_items.append(Expense(
                        description=description,
                        amount=amount_decimal,
                        category=category,
                        expense_type=expense_type,
                        paid_by=assigned_user  # Who actually paid for this
                    ))

            # Create Person object
            person = Person(
                name=user_name,
                income=income_items,
                expenses=expense_items
            )
            people.append(person)

        # Handle shared account transactions - distribute to users
        if "shared" in user_transactions:
            for trans in user_transactions["shared"]:
                amount = trans.get('Amount', 0)
                if pd.isna(amount) or amount >= 0:
                    continue  # Only process expenses from shared accounts

                amount_decimal = Decimal(str(abs(amount)))
                description = str(trans.get('Description', 'Shared Transaction'))
                assigned_user = str(trans.get('Assigned User', ''))

                # Determine which person to assign this to
                target_person = None
                for person in people:
                    if person.name == assigned_user:
                        target_person = person
                        break

                if not target_person and people:
                    target_person = people[0]  # Default to first person if not assigned

                if target_person:
                    category_str = str(trans.get('Category', '')).upper()
                    try:
                        category = ExpenseCategory[category_str] if category_str else ExpenseCategory.OTHER
                    except KeyError:
                        category = ExpenseCategory.OTHER

                    trans_type = str(trans.get('Type', '')).upper()
                    expense_type = ExpenseType.SHARED if trans_type == "HOUSEHOLD" else ExpenseType.INDIVIDUAL

                    target_person.expenses.append(Expense(
                        description=description,
                        amount=amount_decimal,
                        category=category,
                        expense_type=expense_type,
                        paid_by=assigned_user or target_person.name
                    ))

        if not people:
            raise Exception("No users found with transactions")

        # Create FinancialPeriod
        period = FinancialPeriod(people=people)
        return period


class CalculateTab(QWidget):
    """Tab for calculating fair share split from processed transactions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.calculation_thread = None
        self.last_result = None
        self.config: Optional[Config] = None
        self.available_months: List[str] = []

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Calculate Fair Share Split")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Calculate fair share splits based on processed transactions from bank statements."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Period selection group
        period_group = QGroupBox("Select Period")
        period_layout = QVBoxLayout()

        # Month selector
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("Month:"))
        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(200)
        month_layout.addWidget(self.month_combo, 1)

        refresh_btn = QPushButton("Refresh Months")
        refresh_btn.clicked.connect(self.scan_available_months)
        month_layout.addWidget(refresh_btn)

        period_layout.addLayout(month_layout)

        # Info label showing income mode from settings
        self.mode_info_label = QLabel()
        self.mode_info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        period_layout.addWidget(self.mode_info_label)

        period_group.setLayout(period_layout)
        layout.addWidget(period_group)

        # Calculate button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.calculate_btn = QPushButton("Calculate Fair Share Split")
        self.calculate_btn.setMinimumHeight(40)
        self.calculate_btn.clicked.connect(self.calculate_split)
        button_layout.addWidget(self.calculate_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()

        # Summary text
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(300)
        results_layout.addWidget(self.results_text)

        # Action buttons
        action_layout = QHBoxLayout()
        self.view_details_btn = QPushButton("View Detailed Breakdown")
        self.view_details_btn.clicked.connect(self.view_details)
        self.view_details_btn.setEnabled(False)
        action_layout.addWidget(self.view_details_btn)

        self.view_categories_btn = QPushButton("View Category Summary")
        self.view_categories_btn.clicked.connect(self.view_categories)
        self.view_categories_btn.setEnabled(False)
        action_layout.addWidget(self.view_categories_btn)

        action_layout.addStretch()
        results_layout.addLayout(action_layout)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group, 1)

    def load_config(self):
        """Load configuration and scan for available months."""
        try:
            self.config = ConfigManager.load()

            # Update mode info label
            mode = self.config.get_mode()
            self.mode_info_label.setText(
                f"Income mode: {mode} (configured in Settings tab)"
            )

            self.scan_available_months()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"Failed to load configuration:\n\n{str(e)}"
            )

    def scan_available_months(self):
        """Scan for available month folders across all accounts."""
        if not self.config:
            return

        months_set = set()

        # Scan all accounts for month folders
        for user in self.config.users:
            for account in user.accounts:
                months_path = self.config.working_dir / account.processed_folder / "months"
                if months_path.exists():
                    for month_folder in months_path.iterdir():
                        if month_folder.is_dir() and len(month_folder.name) == 7:  # YYYY-MM format
                            months_set.add(month_folder.name)

        # Also check shared accounts
        for account in self.config.shared_accounts:
            months_path = self.config.working_dir / account.processed_folder / "months"
            if months_path.exists():
                for month_folder in months_path.iterdir():
                    if month_folder.is_dir() and len(month_folder.name) == 7:
                        months_set.add(month_folder.name)

        # Sort months in descending order (most recent first)
        self.available_months = sorted(list(months_set), reverse=True)

        # Populate month combo
        current_selection = self.month_combo.currentData()
        self.month_combo.clear()
        for month in self.available_months:
            # Format as "November 2024" for display
            try:
                month_date = datetime.strptime(month, "%Y-%m")
                display_text = month_date.strftime("%B %Y")
                self.month_combo.addItem(display_text, month)
            except:
                self.month_combo.addItem(month, month)

        # Restore previous selection if possible
        if current_selection in self.available_months:
            index = self.month_combo.findData(current_selection)
            if index >= 0:
                self.month_combo.setCurrentIndex(index)

        if self.available_months:
            self.calculate_btn.setEnabled(True)
        else:
            self.calculate_btn.setEnabled(False)
            QMessageBox.information(
                self,
                "No Months Found",
                "No processed transaction months found.\n\n"
                "Please process bank statements in the 'Process Statements' tab first."
            )

    def calculate_split(self):
        """Calculate the fair share split from processed transactions."""
        selected_month = self.month_combo.currentData()
        if not selected_month:
            QMessageBox.warning(
                self,
                "No Month Selected",
                "Please select a month to calculate."
            )
            return

        if not self.config:
            QMessageBox.critical(
                self,
                "Configuration Error",
                "Configuration not loaded. Please restart the application."
            )
            return

        # Disable UI during calculation
        self.calculate_btn.setEnabled(False)
        self.month_combo.setEnabled(False)

        # Clear previous results
        self.results_text.clear()
        self.view_details_btn.setEnabled(False)
        self.view_categories_btn.setEnabled(False)

        # Get income mode from settings
        use_gross = self.config.is_gross_mode()

        # Start calculation thread
        self.calculation_thread = CalculationThread(self.config, selected_month, use_gross)
        self.calculation_thread.progress.connect(self.on_progress)
        self.calculation_thread.finished.connect(self.on_calculation_finished)
        self.calculation_thread.start()

    def on_progress(self, message):
        """Update progress label."""
        self.progress_label.setText(message)

    def on_calculation_finished(self, result, error):
        """Handle calculation completion."""
        # Re-enable UI
        self.calculate_btn.setEnabled(True)
        self.month_combo.setEnabled(True)
        self.progress_label.setText("")

        if error:
            QMessageBox.critical(
                self,
                "Calculation Error",
                f"An error occurred during calculation:\n\n{error}"
            )
            return

        # Store result
        self.last_result = result

        # Generate and display summary report
        try:
            report_gen = ReportGenerator()
            summary = report_gen.generate_summary_report(result)
            self.results_text.setPlainText(summary)

            # Enable detail buttons
            self.view_details_btn.setEnabled(True)
            self.view_categories_btn.setEnabled(True)

            # Refresh other tabs
            if self.main_window:
                self.main_window.refresh_all_tabs()

            # Show success message
            person_from = result.person1_name if result.person1_balance < 0 else result.person2_name
            person_to = result.person2_name if result.person1_balance < 0 else result.person1_name
            transfer = abs(result.person1_balance)

            QMessageBox.information(
                self,
                "Calculation Complete",
                f"Month processed successfully!\n\n"
                f"{person_from} should pay {person_to}:\n"
                f"R{transfer:,.2f}"
            )

        except Exception as e:
            import traceback
            full_error = f"{str(e)}\n\nStack trace:\n{traceback.format_exc()}"
            QMessageBox.critical(
                self,
                "Report Error",
                f"Error generating report:\n\n{full_error}"
            )

    def view_details(self):
        """Show detailed expense breakdown."""
        if not self.last_result:
            return

        try:
            report_gen = ReportGenerator()
            breakdown = report_gen.generate_expense_breakdown(
                self.last_result.period,
                self.last_result
            )

            dialog = ResultsDialog("Detailed Expense Breakdown", breakdown, self)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error generating breakdown:\n\n{str(e)}"
            )

    def view_categories(self):
        """Show category summary."""
        if not self.last_result:
            return

        try:
            report_gen = ReportGenerator()
            category_summary = report_gen.generate_category_summary(self.last_result.period)

            dialog = ResultsDialog("Category Summary", category_summary, self)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error generating category summary:\n\n{str(e)}"
            )
