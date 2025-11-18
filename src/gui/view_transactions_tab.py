"""
View Transactions Tab - View processed/classified transactions by statement.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List
import pandas as pd

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QSplitter, QAbstractItemView, QTabWidget,
    QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigManager, Config
from statement_processor import StatementProcessor, StatementRecord, ProcessingStatus
from gui.template_validation_tab import TemplateValidationTab
from gui.parser_diagnostics_tab import ParserDiagnosticsTab
from learned_classifier import LearnedClassifier
from decimal import Decimal


class TransactionsViewWidget(QWidget):
    """Widget for viewing processed/classified transactions by statement."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.processor: Optional[StatementProcessor] = None
        self.config: Optional[Config] = None
        self.current_statement_id: Optional[str] = None

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("View Transactions")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QHBoxLayout()

        # User filter
        filters_layout.addWidget(QLabel("User:"))
        self.user_filter = QComboBox()
        self.user_filter.addItem("All")
        self.user_filter.currentTextChanged.connect(self.on_user_filter_changed)
        filters_layout.addWidget(self.user_filter)

        # Account filter
        filters_layout.addWidget(QLabel("Account:"))
        self.account_filter = QComboBox()
        self.account_filter.addItem("All")
        self.account_filter.currentTextChanged.connect(self.refresh_statements)
        filters_layout.addWidget(self.account_filter)

        # Status filter
        filters_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "Extracted & Classified",  # Keep as convenience default
            "All",
            "Unprocessed",
            "Extracted",
            "Classified",
            "Error"
        ])
        self.status_filter.setCurrentIndex(0)  # Default to "Extracted & Classified"
        self.status_filter.currentTextChanged.connect(self.refresh_statements)
        filters_layout.addWidget(self.status_filter)

        filters_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        filters_layout.addWidget(refresh_btn)

        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        # Create split view
        splitter = QSplitter(Qt.Horizontal)

        # LEFT PANEL: Statements list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        statements_label = QLabel("Statements")
        statements_label_font = QFont()
        statements_label_font.setPointSize(10)
        statements_label_font.setBold(True)
        statements_label.setFont(statements_label_font)
        left_layout.addWidget(statements_label)

        # Statements table
        self.statements_table = QTableWidget()
        self.statements_table.setColumnCount(6)
        self.statements_table.setHorizontalHeaderLabels([
            "Account", "Owner", "Statement File", "Date", "Status", "Transactions"
        ])
        self.statements_table.horizontalHeader().setStretchLastSection(False)
        self.statements_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.statements_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.statements_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.statements_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.statements_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.statements_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.statements_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.statements_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.statements_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.statements_table.itemSelectionChanged.connect(self.on_statement_selected)
        left_layout.addWidget(self.statements_table)

        splitter.addWidget(left_panel)

        # RIGHT PANEL: Transaction details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        transactions_label = QLabel("Transactions (select a statement)")
        transactions_label_font = QFont()
        transactions_label_font.setPointSize(10)
        transactions_label_font.setBold(True)
        transactions_label.setFont(transactions_label_font)
        self.transactions_label = transactions_label
        right_layout.addWidget(transactions_label)

        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels([
            "Learn", "Date", "Description", "Amount", "Category", "Type", "Assigned User", "Modified"
        ])
        self.transactions_table.horizontalHeader().setStretchLastSection(False)
        self.transactions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Learn checkbox
        self.transactions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Description
        self.transactions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.transactions_table)

        # Add action buttons below the transactions table
        button_layout = QHBoxLayout()

        self.save_changes_btn = QPushButton("Save Changes")
        self.save_changes_btn.clicked.connect(self.save_transaction_changes)
        self.save_changes_btn.setEnabled(False)
        button_layout.addWidget(self.save_changes_btn)

        self.save_learned_btn = QPushButton("Save Selected as Learned Rules")
        self.save_learned_btn.clicked.connect(self.save_learned_rules)
        self.save_learned_btn.setEnabled(False)
        button_layout.addWidget(self.save_learned_btn)

        button_layout.addStretch()
        right_layout.addLayout(button_layout)

        splitter.addWidget(right_panel)

        # Set initial splitter sizes (40% left, 60% right)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter, 1)

        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

    def load_config(self):
        """Load configuration and initialize processor."""
        try:
            self.config = ConfigManager.load()
            self.processor = StatementProcessor(self.config)

            # Reload state from disk to get latest changes from other tabs
            self.processor.reload_state()
            # Then sync with filesystem to catch any extracted→classified updates
            self.processor.sync_state_with_filesystem()

            # Populate user filter
            self.user_filter.clear()
            self.user_filter.addItem("All")
            for user in self.config.users:
                self.user_filter.addItem(user.name)

            # Add shared option
            if self.config.shared_accounts:
                self.user_filter.addItem("Shared")

            self.refresh_all()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"Failed to load configuration:\n\n{str(e)}"
            )

    def on_user_filter_changed(self):
        """Handle user filter change."""
        # Update account filter based on selected user
        self.account_filter.clear()
        self.account_filter.addItem("All")

        user_filter = self.user_filter.currentText()

        if user_filter == "All":
            # Show all accounts
            for user in self.config.users:
                for account in user.accounts:
                    self.account_filter.addItem(f"{user.name} - {account.name}")
            for account in self.config.shared_accounts:
                self.account_filter.addItem(f"Shared - {account.name}")
        elif user_filter == "Shared":
            # Show only shared accounts
            for account in self.config.shared_accounts:
                self.account_filter.addItem(account.name)
        else:
            # Show accounts for selected user
            for user in self.config.users:
                if user.name == user_filter:
                    for account in user.accounts:
                        self.account_filter.addItem(account.name)

        self.refresh_statements()

    def refresh_all(self):
        """Refresh both statements and transactions."""
        self.refresh_statements()

    def refresh_statements(self):
        """Refresh the statements list based on current filters."""
        if not self.processor:
            return

        # Get all statements
        all_statements = self.processor.get_all_statements()

        # Apply status filter
        status_filter = self.status_filter.currentText()
        if status_filter == "Extracted & Classified":
            # Convenience filter: show both extracted and classified
            status_filtered = [s for s in all_statements
                             if s.status in [ProcessingStatus.EXTRACTED.value, ProcessingStatus.CLASSIFIED.value]]
        elif status_filter != "All":
            # Standard status filters: convert filter text to enum value
            status_value = ProcessingStatus[status_filter.upper()].value
            status_filtered = [s for s in all_statements if s.status == status_value]
        else:  # "All"
            status_filtered = all_statements

        # Apply user and account filters
        filtered_statements = self._apply_filters(status_filtered)

        # Update table
        self.statements_table.setRowCount(0)

        for record in filtered_statements:
            self._add_statement_row(record)

        self.status_label.setText(f"Showing {len(filtered_statements)} processed statement(s)")

        # Clear transactions table
        self.transactions_table.setRowCount(0)
        self.transactions_label.setText("Transactions (select a statement)")
        self.current_statement_id = None

    def _apply_filters(self, statements: List[StatementRecord]) -> List[StatementRecord]:
        """Apply current filters to statements."""
        filtered = statements

        user_filter = self.user_filter.currentText()
        account_filter = self.account_filter.currentText()

        if user_filter != "All":
            if user_filter == "Shared":
                filtered = [s for s in filtered if s.account_owner == "Shared"]
            else:
                filtered = [s for s in filtered if s.account_owner == user_filter]

        if account_filter != "All":
            # If user is selected, account filter is just account name
            # If user is "All", account filter is "User - Account Name"
            if user_filter == "All":
                # Parse "Owner - Account Name"
                if " - " in account_filter:
                    owner, account_name = account_filter.split(" - ", 1)
                    filtered = [s for s in filtered
                               if s.account_owner == owner and s.account_name == account_name]
            else:
                filtered = [s for s in filtered if s.account_name == account_filter]

        return filtered

    def _add_statement_row(self, record: StatementRecord):
        """Add a statement row to the table."""
        row = self.statements_table.rowCount()
        self.statements_table.insertRow(row)

        # Account
        self.statements_table.setItem(row, 0, QTableWidgetItem(record.account_name))

        # Owner
        self.statements_table.setItem(row, 1, QTableWidgetItem(record.account_owner or ""))

        # Statement File
        self.statements_table.setItem(row, 2, QTableWidgetItem(record.filename))

        # Date (use period end)
        date_str = ""
        if record.statement_period_end:
            try:
                end = datetime.fromisoformat(record.statement_period_end)
                date_str = end.strftime("%Y-%m-%d")
            except:
                date_str = "Unknown"
        self.statements_table.setItem(row, 3, QTableWidgetItem(date_str))

        # Status
        status_item = QTableWidgetItem(record.status.upper())
        # Color based on status
        if record.status == ProcessingStatus.CLASSIFIED.value:
            status_item.setBackground(QBrush(QColor(144, 238, 144)))  # Light green for classified
        elif record.status == ProcessingStatus.EXTRACTED.value:
            status_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow for extracted
        elif record.status == ProcessingStatus.ERROR.value:
            status_item.setBackground(QBrush(QColor(255, 200, 200)))  # Light red for error
        self.statements_table.setItem(row, 4, status_item)

        # Transaction count
        count_item = QTableWidgetItem(str(record.transaction_count))
        count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.statements_table.setItem(row, 5, count_item)

        # Store statement ID in the row
        self.statements_table.item(row, 0).setData(Qt.UserRole, record.id)

    def on_statement_selected(self):
        """Handle statement selection - load its transactions."""
        selected_items = self.statements_table.selectedItems()
        if not selected_items:
            return

        # Get statement ID from first column of selected row
        row = selected_items[0].row()
        statement_id = self.statements_table.item(row, 0).data(Qt.UserRole)
        account_name = self.statements_table.item(row, 0).text()

        if statement_id:
            self.current_statement_id = statement_id
            self.load_transactions(statement_id, account_name)

    def load_transactions(self, statement_id: str, account_name: str):
        """Load transactions for the selected statement."""
        try:
            # Get statement record to find the classified file
            statement = self.processor.get_statement(statement_id)
            if not statement:
                QMessageBox.warning(self, "Error", "Statement not found")
                return

            # Construct path to classified file
            account = None
            for user in self.config.users:
                for acc in user.accounts:
                    if acc.name == statement.account_name:
                        account = acc
                        break
                if account:
                    break

            if not account:
                for acc in self.config.shared_accounts:
                    if acc.name == statement.account_name:
                        account = acc
                        break

            if not account:
                QMessageBox.warning(self, "Error", "Account configuration not found")
                return

            # Determine which file to load based on status
            statements_dir = self.config.working_dir / account.processed_folder / "statements"

            if statement.status == ProcessingStatus.CLASSIFIED.value:
                # Try classified file first
                transactions_file = statements_dir / f"{statement_id}_classified.xlsx"
            else:
                # For extracted status, use raw file
                transactions_file = statements_dir / f"{statement_id}_raw.xlsx"

            # Fallback: if preferred file doesn't exist, try the other
            if not transactions_file.exists():
                if statement.status == ProcessingStatus.CLASSIFIED.value:
                    transactions_file = statements_dir / f"{statement_id}_raw.xlsx"
                else:
                    transactions_file = statements_dir / f"{statement_id}_classified.xlsx"

            if not transactions_file.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Transactions file not found:\n{transactions_file}\n\n"
                    f"Expected in: {statements_dir}"
                )
                return

            # Load transactions from Excel
            df = pd.read_excel(transactions_file)

            # Update transactions table
            self.transactions_table.setRowCount(0)

            for _, row_data in df.iterrows():
                self._add_transaction_row(row_data)

            # Update label
            self.transactions_label.setText(
                f"Transactions for {account_name} ({len(df)} transactions)"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Transactions",
                f"Failed to load transactions:\n\n{str(e)}"
            )

    def _add_transaction_row(self, row_data):
        """Add a transaction row to the table."""
        row = self.transactions_table.rowCount()
        self.transactions_table.insertRow(row)

        # Column 0: Learn checkbox
        checkbox = QCheckBox()
        checkbox.setStyleSheet("margin-left:50%; margin-right:50%;")
        checkbox.stateChanged.connect(self.on_learn_checkbox_changed)
        self.transactions_table.setCellWidget(row, 0, checkbox)

        # Column 1: Date
        date_str = ""
        if pd.notna(row_data.get('Date')):
            try:
                date_obj = pd.to_datetime(row_data['Date'])
                date_str = date_obj.strftime("%Y-%m-%d")
            except:
                date_str = str(row_data.get('Date', ''))
        self.transactions_table.setItem(row, 1, QTableWidgetItem(date_str))

        # Column 2: Description
        desc = str(row_data.get('Description', ''))
        self.transactions_table.setItem(row, 2, QTableWidgetItem(desc))

        # Column 3: Amount
        amount = row_data.get('Amount', 0)
        is_credit = row_data.get('Is Credit', False)
        amount_str = f"R {amount:,.2f}" if pd.notna(amount) else ""
        amount_item = QTableWidgetItem(amount_str)
        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Store raw amount for later use
        amount_item.setData(Qt.UserRole, amount)
        # Color based on Is Credit flag - vibrant colors for better visibility
        if pd.notna(amount):
            if is_credit:  # Money IN
                amount_item.setForeground(QBrush(QColor(34, 139, 34)))  # Forest green for money IN
            else:  # Money OUT
                amount_item.setForeground(QBrush(QColor(220, 20, 60)))  # Crimson red for money OUT
        self.transactions_table.setItem(row, 3, amount_item)

        # Column 4: Category
        category = str(row_data.get('Category', ''))
        self.transactions_table.setItem(row, 4, QTableWidgetItem(category))

        # Column 5: Type (HOUSEHOLD/INDIVIDUAL) - editable dropdown
        trans_type = str(row_data.get('Type', ''))
        type_combo = QComboBox()
        type_combo.addItems(["HOUSEHOLD", "INDIVIDUAL"])
        type_combo.setCurrentText(trans_type)
        # Store original value
        type_combo.setProperty("original_value", trans_type)
        type_combo.currentTextChanged.connect(self.on_type_changed)
        # Color based on type
        if trans_type == "HOUSEHOLD":
            type_combo.setStyleSheet("background-color: #ADD8E6;")  # Light blue
        elif trans_type == "INDIVIDUAL":
            type_combo.setStyleSheet("background-color: #FFFFE0;")  # Light yellow
        self.transactions_table.setCellWidget(row, 5, type_combo)

        # Column 6: Assigned User
        assigned_user = str(row_data.get('Assigned User', ''))
        self.transactions_table.setItem(row, 6, QTableWidgetItem(assigned_user))

        # Column 7: Modified flag (initially empty)
        modified_item = QTableWidgetItem("")
        modified_item.setTextAlignment(Qt.AlignCenter)
        self.transactions_table.setItem(row, 7, modified_item)

    def on_type_changed(self, new_value):
        """Handle type dropdown change."""
        sender = self.sender()
        if sender and sender.property("original_value") != new_value:
            # Mark row as modified
            row = self._get_row_for_widget(sender)
            if row is not None:
                modified_item = self.transactions_table.item(row, 7)
                if modified_item:
                    modified_item.setText("✓")
                    modified_item.setForeground(QBrush(QColor(0, 128, 0)))  # Green
                # Update color based on new type
                if new_value == "HOUSEHOLD":
                    sender.setStyleSheet("background-color: #ADD8E6;")  # Light blue
                else:
                    sender.setStyleSheet("background-color: #FFFFE0;")  # Light yellow
                self.save_changes_btn.setEnabled(True)

    def on_learn_checkbox_changed(self):
        """Handle learn checkbox state change."""
        # Enable/disable the save learned rules button based on whether any checkboxes are checked
        has_selection = False
        for row in range(self.transactions_table.rowCount()):
            checkbox = self.transactions_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                has_selection = True
                break
        self.save_learned_btn.setEnabled(has_selection)

    def _get_row_for_widget(self, widget):
        """Get the row number for a given widget."""
        for row in range(self.transactions_table.rowCount()):
            if self.transactions_table.cellWidget(row, 5) == widget:
                return row
        return None

    def _get_account_id(self, statement: StatementRecord) -> str:
        """Generate unique account ID from statement record."""
        owner = statement.account_owner or "Shared"
        return f"{owner}_{statement.account_name}"

    def save_transaction_changes(self):
        """Save transaction changes back to the Excel file."""
        try:
            if not self.current_statement_id:
                QMessageBox.warning(self, "Error", "No statement selected")
                return

            # Get statement record
            statement = self.processor.get_statement(self.current_statement_id)
            if not statement:
                QMessageBox.warning(self, "Error", "Statement not found")
                return

            # Find the account config
            account = None
            for user in self.config.users:
                for acc in user.accounts:
                    if acc.name == statement.account_name:
                        account = acc
                        break
                if account:
                    break

            if not account:
                for acc in self.config.shared_accounts:
                    if acc.name == statement.account_name:
                        account = acc
                        break

            if not account:
                QMessageBox.warning(self, "Error", "Account configuration not found")
                return

            # Determine file path
            statements_dir = self.config.working_dir / account.processed_folder / "statements"
            if statement.status == ProcessingStatus.CLASSIFIED.value:
                transactions_file = statements_dir / f"{self.current_statement_id}_classified.xlsx"
            else:
                transactions_file = statements_dir / f"{self.current_statement_id}_raw.xlsx"

            if not transactions_file.exists():
                QMessageBox.warning(self, "Error", f"Transactions file not found: {transactions_file}")
                return

            # Load transactions
            df = pd.read_excel(transactions_file)

            # Update modified rows
            modified_count = 0
            for row in range(self.transactions_table.rowCount()):
                modified_item = self.transactions_table.item(row, 7)
                if modified_item and modified_item.text() == "✓":
                    # This row was modified
                    type_combo = self.transactions_table.cellWidget(row, 5)
                    if type_combo:
                        new_type = type_combo.currentText()
                        df.at[row, 'Type'] = new_type
                        # Update original value
                        type_combo.setProperty("original_value", new_type)
                        # Clear modified flag
                        modified_item.setText("")
                        modified_count += 1

            if modified_count == 0:
                QMessageBox.information(self, "No Changes", "No changes to save")
                return

            # Save back to Excel
            df.to_excel(transactions_file, index=False)

            # Update statement processor state if needed
            self.processor.sync_state_with_filesystem()

            QMessageBox.information(
                self,
                "Success",
                f"Saved {modified_count} transaction changes to:\n{transactions_file.name}"
            )

            self.save_changes_btn.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Changes",
                f"Failed to save changes:\n\n{str(e)}"
            )

    def save_learned_rules(self):
        """Save selected transactions as learned classification rules."""
        try:
            if not self.current_statement_id:
                QMessageBox.warning(self, "Error", "No statement selected")
                return

            # Get statement record
            statement = self.processor.get_statement(self.current_statement_id)
            if not statement:
                QMessageBox.warning(self, "Error", "Statement not found")
                return

            # Create account-specific LearnedClassifier
            account_id = self._get_account_id(statement)
            learned_rules_path = self.config.working_dir / "learned_rules.json"
            classifier = LearnedClassifier(
                learned_rules_path=learned_rules_path,
                account_id=account_id
            )

            # Collect selected transactions
            selected_count = 0
            new_rules = 0
            updated_rules = 0

            for row in range(self.transactions_table.rowCount()):
                checkbox = self.transactions_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    # Get transaction data
                    description_item = self.transactions_table.item(row, 2)
                    type_combo = self.transactions_table.cellWidget(row, 5)

                    if description_item and type_combo:
                        description = description_item.text().lower().strip()
                        exp_type = type_combo.currentText()

                        # Check if rule exists
                        if description in classifier.rules:
                            existing = classifier.rules[description]
                            if existing['type'] != exp_type:
                                # Update existing rule
                                classifier.rules[description] = {
                                    'type': exp_type,
                                    'count': existing.get('count', 1) + 1,
                                    'confidence': 100
                                }
                                updated_rules += 1
                            else:
                                # Same rule, just increment count
                                existing['count'] = existing.get('count', 1) + 1
                        else:
                            # New rule
                            classifier.rules[description] = {
                                'type': exp_type,
                                'count': 1,
                                'confidence': 100
                            }
                            new_rules += 1

                        selected_count += 1
                        # Uncheck the checkbox
                        checkbox.setChecked(False)

            if selected_count == 0:
                QMessageBox.information(self, "No Selection", "No transactions selected")
                return

            # Save rules
            classifier.repo.save()

            QMessageBox.information(
                self,
                "Success",
                f"Saved {selected_count} learned rules for account: {account_id}\n\n"
                f"New rules: {new_rules}\n"
                f"Updated rules: {updated_rules}\n"
                f"Total rules for this account: {len(classifier.rules)}"
            )

            self.save_learned_btn.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Learned Rules",
                f"Failed to save learned rules:\n\n{str(e)}"
            )


class ViewTransactionsTab(QWidget):
    """Parent tab with subtabs for viewing transactions, template validation, and parser diagnostics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface with subtabs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget for subtabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Add subtabs
        self.transactions_widget = TransactionsViewWidget(self.main_window)
        self.tabs.addTab(self.transactions_widget, "Transactions")

        self.template_validation_widget = TemplateValidationTab(self.main_window)
        self.tabs.addTab(self.template_validation_widget, "Template Validation")

        self.parser_diagnostics_widget = ParserDiagnosticsTab(self.main_window)
        self.tabs.addTab(self.parser_diagnostics_widget, "Parser Diagnostics")
