"""
Monthly Transactions Tab - View consolidated monthly transactions from all accounts.
"""

from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict
import pandas as pd
from dateutil.relativedelta import relativedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigManager, Config


class MonthlyTransactionsTab(QWidget):
    """Tab for viewing consolidated monthly transactions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.config: Optional[Config] = None
        self.available_months: List[str] = []

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("Monthly Transactions")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QHBoxLayout()

        # Month selector
        filters_layout.addWidget(QLabel("Month:"))
        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(150)
        self.month_combo.currentTextChanged.connect(self.load_transactions)
        filters_layout.addWidget(self.month_combo)

        # Period selector (financial year)
        filters_layout.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("All Time")
        self.period_combo.setMinimumWidth(150)
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        filters_layout.addWidget(self.period_combo)

        # Category filter
        filters_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("All")
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.category_filter)

        filters_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        filters_layout.addWidget(refresh_btn)

        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels([
            "Date", "Description", "Amount", "Category", "Type", "Assigned User", "User", "Account"
        ])

        # Set column resize modes
        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Amount
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Assigned User
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # User
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Account

        self.transactions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.transactions_table.setAlternatingRowColors(True)
        self.transactions_table.setSortingEnabled(True)
        layout.addWidget(self.transactions_table, 1)

        # Summary footer
        summary_layout = QHBoxLayout()
        self.summary_label = QLabel("No transactions loaded")
        self.summary_label.setStyleSheet("font-weight: bold; padding: 5px;")
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Store full dataset for filtering
        self.full_transactions: List[Dict] = []

    def load_config(self):
        """Load configuration."""
        try:
            self.config = ConfigManager.load()
            self.scan_available_months()
            self.populate_period_filter()

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
        self.month_combo.clear()
        for month in self.available_months:
            # Format as "November 2024" for display
            try:
                month_date = datetime.strptime(month, "%Y-%m")
                display_text = month_date.strftime("%B %Y")
                self.month_combo.addItem(display_text, month)
            except:
                self.month_combo.addItem(month, month)

        if self.available_months:
            self.status_label.setText(f"Found {len(self.available_months)} month(s) with transactions")
        else:
            self.status_label.setText("No processed months found")

    def populate_period_filter(self):
        """Populate the period (financial year) filter."""
        if not self.config or not self.available_months:
            return

        # Get financial year start month from config
        fy_start_month = self.config.get_financial_year_start_month()

        # Determine unique financial years from available months
        fy_periods = set()
        for month_str in self.available_months:
            try:
                month_date = datetime.strptime(month_str, "%Y-%m").date()

                # Calculate which FY this month belongs to
                year = month_date.year
                if month_date.month < fy_start_month:
                    year -= 1

                fy_start = date(year, fy_start_month, 1)
                fy_end = fy_start + relativedelta(years=1) - relativedelta(days=1)

                if fy_start.year == fy_end.year:
                    fy_label = f"FY {fy_start.year}"
                else:
                    fy_label = f"FY {fy_start.year}-{fy_end.year}"

                fy_periods.add((fy_label, fy_start, fy_end))
            except:
                continue

        # Sort by start date (most recent first)
        sorted_periods = sorted(list(fy_periods), key=lambda x: x[1], reverse=True)

        # Populate combo
        self.period_combo.clear()
        self.period_combo.addItem("All Time", None)
        for label, start, end in sorted_periods:
            self.period_combo.addItem(label, (start, end))

    def on_period_changed(self):
        """Handle period filter change - update month combo."""
        period_data = self.period_combo.currentData()

        if period_data is None:
            # All Time - show all months
            filtered_months = self.available_months
        else:
            # Filter months within the FY period
            start_date, end_date = period_data
            filtered_months = []
            for month_str in self.available_months:
                try:
                    month_date = datetime.strptime(month_str, "%Y-%m").date()
                    if start_date <= month_date <= end_date:
                        filtered_months.append(month_str)
                except:
                    continue

        # Update month combo
        current_month = self.month_combo.currentData()
        self.month_combo.clear()
        for month in filtered_months:
            try:
                month_date = datetime.strptime(month, "%Y-%m")
                display_text = month_date.strftime("%B %Y")
                self.month_combo.addItem(display_text, month)
            except:
                self.month_combo.addItem(month, month)

        # Try to restore previous selection
        if current_month and current_month in filtered_months:
            index = self.month_combo.findData(current_month)
            if index >= 0:
                self.month_combo.setCurrentIndex(index)

    def refresh_all(self):
        """Refresh month list and reload transactions."""
        self.scan_available_months()
        self.populate_period_filter()
        if self.month_combo.count() > 0:
            self.load_transactions()

    def load_transactions(self):
        """Load transactions for the selected month."""
        selected_month = self.month_combo.currentData()
        if not selected_month or not self.config:
            self.transactions_table.setRowCount(0)
            self.full_transactions = []
            self.summary_label.setText("No month selected")
            return

        try:
            all_transactions = []
            categories_set = set()

            # Load transactions from all accounts for this month
            for user in self.config.users:
                for account in user.accounts:
                    trans_file = (
                        self.config.working_dir /
                        account.processed_folder /
                        "months" /
                        selected_month /
                        f"{account.name.replace(' ', '_')}_transactions.xlsx"
                    )

                    if trans_file.exists():
                        df = pd.read_excel(trans_file)
                        # Add user and account info
                        for _, row in df.iterrows():
                            trans_dict = row.to_dict()
                            trans_dict['_user'] = user.name
                            trans_dict['_account'] = account.name
                            all_transactions.append(trans_dict)

                            # Collect categories
                            if pd.notna(row.get('Category')):
                                categories_set.add(str(row['Category']))

            # Also load from shared accounts
            for account in self.config.shared_accounts:
                trans_file = (
                    self.config.working_dir /
                    account.processed_folder /
                    "months" /
                    selected_month /
                    f"{account.name.replace(' ', '_')}_transactions.xlsx"
                )

                if trans_file.exists():
                    df = pd.read_excel(trans_file)
                    for _, row in df.iterrows():
                        trans_dict = row.to_dict()
                        trans_dict['_user'] = "Shared"
                        trans_dict['_account'] = account.name
                        all_transactions.append(trans_dict)

                        if pd.notna(row.get('Category')):
                            categories_set.add(str(row['Category']))

            # Store full dataset
            self.full_transactions = all_transactions

            # Update category filter
            current_category = self.category_filter.currentText()
            self.category_filter.clear()
            self.category_filter.addItem("All")
            for category in sorted(categories_set):
                self.category_filter.addItem(category)

            # Restore previous category selection
            if current_category in categories_set:
                index = self.category_filter.findData(current_category)
                if index >= 0:
                    self.category_filter.setCurrentIndex(index)

            # Display transactions
            self.apply_filters()

            month_display = self.month_combo.currentText()
            self.status_label.setText(f"Loaded {len(all_transactions)} transaction(s) for {month_display}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Transactions",
                f"Failed to load transactions:\n\n{str(e)}"
            )

    def apply_filters(self):
        """Apply filters and display transactions."""
        # Filter by category
        category_filter = self.category_filter.currentText()

        if category_filter == "All":
            filtered = self.full_transactions
        else:
            filtered = [t for t in self.full_transactions
                       if str(t.get('Category', '')) == category_filter]

        # Update table
        self.transactions_table.setSortingEnabled(False)
        self.transactions_table.setRowCount(0)

        total_amount = 0
        household_amount = 0
        personal_amount = 0

        for trans in filtered:
            self._add_transaction_row(trans)

            # Calculate totals
            amount = trans.get('Amount', 0)
            if pd.notna(amount):
                total_amount += amount
                trans_type = str(trans.get('Type', '')).upper()
                if trans_type == "HOUSEHOLD":
                    household_amount += amount
                elif trans_type == "INDIVIDUAL":
                    personal_amount += amount

        self.transactions_table.setSortingEnabled(True)

        # Update summary
        summary_parts = [
            f"Total: {len(filtered)} transactions",
            f"Amount: R {total_amount:,.2f}",
            f"Household: R {household_amount:,.2f}",
            f"Personal: R {personal_amount:,.2f}"
        ]
        self.summary_label.setText(" | ".join(summary_parts))

    def _add_transaction_row(self, trans_dict: Dict):
        """Add a transaction row to the table."""
        row = self.transactions_table.rowCount()
        self.transactions_table.insertRow(row)

        # Date
        date_str = ""
        if pd.notna(trans_dict.get('Date')):
            try:
                date_obj = pd.to_datetime(trans_dict['Date'])
                date_str = date_obj.strftime("%Y-%m-%d")
            except:
                date_str = str(trans_dict.get('Date', ''))
        self.transactions_table.setItem(row, 0, QTableWidgetItem(date_str))

        # Description
        desc = str(trans_dict.get('Description', ''))
        self.transactions_table.setItem(row, 1, QTableWidgetItem(desc))

        # Amount
        amount = trans_dict.get('Amount', 0)
        amount_str = f"R {amount:,.2f}" if pd.notna(amount) else ""
        amount_item = QTableWidgetItem(amount_str)
        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Color based on amount
        if pd.notna(amount):
            if amount < 0:
                amount_item.setForeground(QBrush(QColor(200, 0, 0)))  # Red for expenses
            else:
                amount_item.setForeground(QBrush(QColor(0, 128, 0)))  # Green for income
        self.transactions_table.setItem(row, 2, amount_item)

        # Category
        category = str(trans_dict.get('Category', ''))
        self.transactions_table.setItem(row, 3, QTableWidgetItem(category))

        # Type (HOUSEHOLD/INDIVIDUAL)
        trans_type = str(trans_dict.get('Type', ''))
        type_item = QTableWidgetItem(trans_type)
        # Color based on type
        if trans_type == "HOUSEHOLD":
            type_item.setBackground(QBrush(QColor(173, 216, 230)))  # Light blue
        elif trans_type == "INDIVIDUAL":
            type_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow
        self.transactions_table.setItem(row, 4, type_item)

        # Assigned User
        assigned_user = str(trans_dict.get('Assigned User', ''))
        self.transactions_table.setItem(row, 5, QTableWidgetItem(assigned_user))

        # User (account owner)
        user = trans_dict.get('_user', '')
        self.transactions_table.setItem(row, 6, QTableWidgetItem(user))

        # Account
        account = trans_dict.get('_account', '')
        self.transactions_table.setItem(row, 7, QTableWidgetItem(account))
