"""
Process Statements Tab - Manage bank statement processing pipeline.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QComboBox, QMessageBox, QProgressDialog,
    QAbstractItemView, QSizePolicy, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor, QBrush, QDesktopServices
from PyQt5.QtCore import QUrl

import sys
import os
import subprocess
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigManager, Config
from statement_processor import StatementProcessor, StatementRecord, ProcessingStatus


class ProcessingThread(QThread):
    """Background thread for statement processing."""

    finished = pyqtSignal(bool, str)  # success, message
    progress = pyqtSignal(str)

    def __init__(self, processor: StatementProcessor, statement_id: str, force: bool = False):
        super().__init__()
        self.processor = processor
        self.statement_id = statement_id
        self.force = force

    def run(self):
        """Run the processing in background."""
        try:
            self.progress.emit("Processing statement...")
            success, error = self.processor.process_statement(self.statement_id, self.force)

            if success:
                self.finished.emit(True, "Statement processed successfully")
            else:
                self.finished.emit(False, error or "Unknown error")

        except Exception as e:
            self.finished.emit(False, str(e))


class ScanThread(QThread):
    """Background thread for scanning statements."""

    finished = pyqtSignal(int, dict)  # count of new statements, diagnostics
    progress = pyqtSignal(str)

    def __init__(self, processor: StatementProcessor):
        super().__init__()
        self.processor = processor

    def run(self):
        """Run the scan in background."""
        try:
            self.progress.emit("Scanning for statements...")
            new_statements, diagnostics = self.processor.scan_for_statements()
            self.finished.emit(len(new_statements), diagnostics)
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.finished.emit(0, {})


class TransactionsViewerDialog(QDialog):
    """Dialog for viewing statement transactions."""

    def __init__(self, record: StatementRecord, excel_path: Path, is_classified: bool, parent=None):
        super().__init__(parent)
        self.record = record
        self.excel_path = excel_path
        self.is_classified = is_classified

        self.setWindowTitle(f"Transactions - {record.filename}")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        self.init_ui()
        self.load_transactions()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QVBoxLayout()

        # Title
        title = QLabel(f"Statement: {self.record.filename}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        # Account info
        info_text = f"Account: {self.record.account_name}"
        if self.record.account_owner:
            info_text += f" ({self.record.account_owner})"
        info_label = QLabel(info_text)
        header_layout.addWidget(info_label)

        # Status
        status_text = "Status: "
        if self.is_classified:
            status_text += "Classified (Household/Personal assignments complete)"
        else:
            status_text += "Extracted Only (Not yet classified - Type and Category columns will be blank)"
        status_label = QLabel(status_text)
        status_label.setWordWrap(True)
        header_layout.addWidget(status_label)

        layout.addLayout(header_layout)

        # Summary section
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("background-color: #e8f4f8; padding: 10px; border-radius: 5px;")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        # Transactions table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def load_transactions(self):
        """Load and display transactions from Excel file."""
        try:
            if not self.excel_path.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Transactions file not found:\n{self.excel_path}"
                )
                return

            # Load Excel file
            df = pd.read_excel(self.excel_path, sheet_name=0)

            # Update summary
            total_in = self.record.total_in
            total_out = self.record.total_out
            summary_parts = [
                f"Transactions: {len(df)}",
                f"Total In: R{total_in:,.2f}",
                f"Total Out: R{total_out:,.2f}",
                f"Net: R{(total_in - total_out):,.2f}"
            ]

            if self.record.breakdown and self.is_classified:
                breakdown_text = " | ".join([f"{k.title()}: R{v:,.2f}" for k, v in self.record.breakdown.items()])
                summary_parts.append(f"Breakdown: {breakdown_text}")

            self.summary_label.setText(" | ".join(summary_parts))

            # Setup table columns
            columns = list(df.columns)
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)

            # Populate table
            self.table.setRowCount(len(df))
            for row_idx, row in df.iterrows():
                for col_idx, col_name in enumerate(columns):
                    value = row[col_name]

                    # Format value
                    if pd.isna(value):
                        display_value = ""
                    elif col_name == 'Amount':
                        try:
                            display_value = f"R{float(value):,.2f}"
                        except:
                            display_value = str(value)
                    else:
                        display_value = str(value)

                    item = QTableWidgetItem(display_value)

                    # Right-align amounts
                    if col_name == 'Amount':
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    # Color-code Type column if classified
                    if col_name == 'Type' and self.is_classified and not pd.isna(value):
                        if str(value).lower() in ['household', 'shared']:
                            item.setBackground(QBrush(QColor(200, 255, 200)))
                        elif str(value).lower() in ['personal', 'individual']:
                            item.setBackground(QBrush(QColor(255, 255, 200)))

                    self.table.setItem(row_idx, col_idx, item)

            # Resize columns
            header = self.table.horizontalHeader()
            for i in range(len(columns)):
                if columns[i] == 'Description':
                    header.setSectionResizeMode(i, QHeaderView.Stretch)
                else:
                    header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Transactions",
                f"Failed to load transactions:\n{str(e)}"
            )


class ProcessStatementsTab(QWidget):
    """Tab for processing bank statements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.processor: Optional[StatementProcessor] = None
        self.config: Optional[Config] = None
        self.processing_thread = None
        self.scan_thread = None

        # Expanded rows tracking
        self.expanded_rows = set()

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Process Bank Statements")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Scan for new statements, process PDFs to extract transactions, "
            "and classify expenses as Household or Personal."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Filters group
        filters_group = self._create_filters_group()
        layout.addWidget(filters_group)

        # Actions group
        actions_group = self._create_actions_group()
        layout.addWidget(actions_group)

        # Statements table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Account", "Owner", "Statement File", "Status",
            "Period", "Transactions", "Total In", "Total Out", "Actions"
        ])

        # Table settings
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.Fixed)
        header.resizeSection(8, 150)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        # Connect row click for expansion
        self.table.cellClicked.connect(self.on_row_clicked)

        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

    def _create_filters_group(self) -> QGroupBox:
        """Create filter controls group."""
        group = QGroupBox("Filters")
        layout = QHBoxLayout()

        # Account filter
        layout.addWidget(QLabel("Account:"))
        self.account_filter = QComboBox()
        self.account_filter.addItem("All")
        self.account_filter.currentTextChanged.connect(self.refresh_table)
        layout.addWidget(self.account_filter)

        layout.addSpacing(20)

        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All",
            "Unprocessed",
            "Extracted",
            "Classified",
            "Error"
        ])
        self.status_filter.currentTextChanged.connect(self.refresh_table)
        layout.addWidget(self.status_filter)

        layout.addSpacing(20)

        # Date range filter
        layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-3))
        self.date_from.dateChanged.connect(self.refresh_table)
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addMonths(1))
        self.date_to.dateChanged.connect(self.refresh_table)
        layout.addWidget(self.date_to)

        layout.addStretch()

        # Clear filters button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(clear_btn)

        group.setLayout(layout)
        return group

    def _create_actions_group(self) -> QGroupBox:
        """Create action buttons group."""
        group = QGroupBox("Actions")
        layout = QHBoxLayout()

        # Scan button
        self.scan_btn = QPushButton("Scan for New Statements")
        self.scan_btn.clicked.connect(self.scan_statements)
        layout.addWidget(self.scan_btn)

        # Reprocess all button
        self.reprocess_all_btn = QPushButton("Reprocess All")
        self.reprocess_all_btn.clicked.connect(self.reprocess_all)
        layout.addWidget(self.reprocess_all_btn)

        layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_table)
        layout.addWidget(refresh_btn)

        group.setLayout(layout)
        return group

    def load_config(self):
        """Load configuration and initialize processor."""
        try:
            self.config = ConfigManager.load()
            self.processor = StatementProcessor(
                self.config,
                templates_dir=Path("bank_templates"),
                learned_rules_path=self.config.working_dir / "learned_classifications.json"
            )

            # Populate account filter
            self._populate_account_filter()

            self.refresh_table()
            self.status_label.setText("Ready")
        except Exception as e:
            self.status_label.setText(f"Error loading config: {str(e)}")
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"Failed to load configuration:\n{str(e)}"
            )

    def _populate_account_filter(self):
        """Populate account filter dropdown with available accounts."""
        # Clear existing items (except "All")
        self.account_filter.clear()
        self.account_filter.addItem("All")

        if not self.config:
            return

        accounts = set()

        # Add user accounts
        for user in self.config.users:
            for account in user.accounts:
                # Format: "Owner - Account Name"
                accounts.add(f"{user.name} - {account.name}")

        # Add shared accounts
        for account in self.config.shared_accounts:
            accounts.add(f"Shared - {account.name}")

        # Sort and add to combobox
        for account_name in sorted(accounts):
            self.account_filter.addItem(account_name)

    def scan_statements(self):
        """Scan for new statements."""
        if not self.processor:
            QMessageBox.warning(self, "Error", "Processor not initialized")
            return

        # Disable button
        self.scan_btn.setEnabled(False)
        self.status_label.setText("Scanning...")

        # Start scan thread
        self.scan_thread = ScanThread(self.processor)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.start()

    def on_scan_finished(self, count: int, diagnostics: dict):
        """Handle scan completion."""
        self.scan_btn.setEnabled(True)

        # Build status message
        status_parts = [f"Scanned {diagnostics.get('accounts_scanned', 0)} account(s)"]
        status_parts.append(f"Found {diagnostics.get('pdfs_found', 0)} PDF(s)")
        status_parts.append(f"{count} new")

        self.status_label.setText(" | ".join(status_parts))
        self.refresh_table()

        # Build detailed message
        message_parts = [
            f"Scan Results:",
            f"• Accounts scanned: {diagnostics.get('accounts_scanned', 0)}",
            f"• PDF files found: {diagnostics.get('pdfs_found', 0)}",
            f"• New statements: {diagnostics.get('new_statements', 0)}",
            f"• Existing statements: {diagnostics.get('existing_statements', 0)}"
        ]

        # Add warnings for missing folders
        if diagnostics.get('folders_missing'):
            message_parts.append("\n⚠️ Missing folders:")
            for folder in diagnostics['folders_missing']:
                message_parts.append(f"  • {folder}")

        # Add info for empty folders
        if diagnostics.get('folders_empty'):
            message_parts.append("\nℹ️ Empty folders (no PDFs):")
            for folder in diagnostics['folders_empty']:
                message_parts.append(f"  • {folder}")

        # Show message if there are any issues or new statements
        if count > 0 or diagnostics.get('folders_missing') or diagnostics.get('folders_empty'):
            QMessageBox.information(
                self,
                "Scan Complete",
                "\n".join(message_parts)
            )

    def refresh_table(self):
        """Refresh the statements table."""
        if not self.processor:
            return

        # Get all statements
        all_statements = self.processor.get_all_statements()

        # Apply filters
        filtered_statements = self._apply_filters(all_statements)

        # Update table
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for record in filtered_statements:
            self._add_statement_row(record)

        self.table.setSortingEnabled(True)
        self.status_label.setText(f"Showing {len(filtered_statements)} statement(s)")

    def _apply_filters(self, statements: List[StatementRecord]) -> List[StatementRecord]:
        """Apply current filters to statements."""
        filtered = statements

        # Account filter
        account_filter = self.account_filter.currentText()
        if account_filter != "All":
            # Parse filter format: "Owner - Account Name"
            parts = account_filter.split(" - ", 1)
            if len(parts) == 2:
                owner, account_name = parts
                filtered = [s for s in filtered
                           if s.account_owner == owner and s.account_name == account_name]

        # Status filter
        status_filter = self.status_filter.currentText()
        if status_filter != "All":
            status_value = ProcessingStatus[status_filter.upper()].value
            filtered = [s for s in filtered if s.status == status_value]

        # Date range filter
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        def in_date_range(record):
            if not record.statement_period_end:
                return True
            try:
                stmt_date = datetime.fromisoformat(record.statement_period_end).date()
                return date_from <= stmt_date <= date_to
            except:
                return True

        filtered = [s for s in filtered if in_date_range(s)]

        return filtered

    def _add_statement_row(self, record: StatementRecord):
        """Add a statement row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Account
        self.table.setItem(row, 0, QTableWidgetItem(record.account_name))

        # Owner
        self.table.setItem(row, 1, QTableWidgetItem(record.account_owner or ""))

        # Filename
        self.table.setItem(row, 2, QTableWidgetItem(record.filename))

        # Status
        status_item = QTableWidgetItem(record.status.upper())
        status_item.setBackground(self._get_status_color(record.status))
        self.table.setItem(row, 3, status_item)

        # Period
        period_str = ""
        if record.statement_period_start and record.statement_period_end:
            try:
                start = datetime.fromisoformat(record.statement_period_start)
                end = datetime.fromisoformat(record.statement_period_end)
                if start.date() == end.date():
                    period_str = start.strftime("%Y-%m-%d")
                else:
                    period_str = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
            except:
                period_str = "Unknown"
        self.table.setItem(row, 4, QTableWidgetItem(period_str))

        # Transaction count
        count_item = QTableWidgetItem(str(record.transaction_count))
        count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 5, count_item)

        # Total In
        total_in_item = QTableWidgetItem(f"R{record.total_in:,.2f}")
        total_in_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 6, total_in_item)

        # Total Out
        total_out_item = QTableWidgetItem(f"R{record.total_out:,.2f}")
        total_out_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 7, total_out_item)

        # Actions
        actions_widget = self._create_actions_widget(record)
        self.table.setCellWidget(row, 8, actions_widget)

        # Store statement ID in row
        self.table.item(row, 0).setData(Qt.UserRole, record.id)

    def _create_actions_widget(self, record: StatementRecord) -> QWidget:
        """Create action buttons for a statement row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        if record.status == ProcessingStatus.UNPROCESSED.value:
            # Process button
            process_btn = QPushButton("Process")
            process_btn.clicked.connect(lambda: self.process_statement(record.id))
            layout.addWidget(process_btn)
        else:
            # Re-extract button
            reextract_btn = QPushButton("Re-extract")
            reextract_btn.clicked.connect(lambda: self.reextract_statement(record.id))
            layout.addWidget(reextract_btn)

        return widget

    def _get_status_color(self, status: str) -> QBrush:
        """Get color for status."""
        colors = {
            ProcessingStatus.UNPROCESSED.value: QColor(240, 240, 240),
            ProcessingStatus.EXTRACTED.value: QColor(255, 255, 200),
            ProcessingStatus.CLASSIFIED.value: QColor(200, 255, 200),
            ProcessingStatus.ERROR.value: QColor(255, 200, 200)
        }
        return QBrush(colors.get(status, QColor(255, 255, 255)))

    def on_row_clicked(self, row: int, column: int):
        """Handle row click to show/hide details."""
        if column == 8:  # Actions column
            return

        statement_id = self.table.item(row, 0).data(Qt.UserRole)
        record = self.processor.get_statement(statement_id)

        if not record or record.status == ProcessingStatus.UNPROCESSED.value:
            return

        # Toggle expansion
        if row in self.expanded_rows:
            self._collapse_row(row)
        else:
            self._expand_row(row, record)

    def _expand_row(self, row: int, record: StatementRecord):
        """Expand row to show breakdown details."""
        self.expanded_rows.add(row)

        # Insert detail row below
        detail_row = row + 1
        self.table.insertRow(detail_row)

        # Create detail widget
        detail_widget = self._create_detail_widget(record)

        # Span all columns
        self.table.setSpan(detail_row, 0, 1, 9)
        self.table.setCellWidget(detail_row, 0, detail_widget)

        # Set row height
        self.table.setRowHeight(detail_row, 120)

    def _collapse_row(self, row: int):
        """Collapse expanded row."""
        self.expanded_rows.discard(row)

        # Remove detail row
        detail_row = row + 1
        if detail_row < self.table.rowCount():
            self.table.removeRow(detail_row)

    def _create_detail_widget(self, record: StatementRecord) -> QWidget:
        """Create detail widget showing breakdown."""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f0f0f0; color: #000000; padding: 10px;")
        layout = QVBoxLayout(widget)

        # Title
        title = QLabel("Expense Breakdown")
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Breakdown
        breakdown_text = []
        if record.breakdown:
            for key, value in record.breakdown.items():
                breakdown_text.append(f"{key.title()}: R{value:,.2f}")

        if breakdown_text:
            breakdown_label = QLabel(" | ".join(breakdown_text))
            layout.addWidget(breakdown_label)
        else:
            layout.addWidget(QLabel("No breakdown available"))

        # Months covered
        if record.months_covered:
            months_label = QLabel(f"Months: {', '.join(record.months_covered)}")
            layout.addWidget(months_label)

        # Error message if any
        if record.error_message:
            error_label = QLabel(f"Error: {record.error_message}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        # Open PDF button
        pdf_btn = QPushButton("Open PDF Statement")
        pdf_btn.clicked.connect(lambda: self.open_pdf_statement(record))
        buttons_layout.addWidget(pdf_btn)

        # View Transactions button (only if processed)
        if record.status != ProcessingStatus.UNPROCESSED.value:
            view_txn_btn = QPushButton("View Transactions")
            view_txn_btn.clicked.connect(lambda: self.view_transactions(record))
            buttons_layout.addWidget(view_txn_btn)

        layout.addLayout(buttons_layout)

        return widget

    def process_statement(self, statement_id: str):
        """Process a single statement."""
        if not self.processor:
            return

        # Start processing thread
        self.status_label.setText("Processing statement...")
        self.processing_thread = ProcessingThread(self.processor, statement_id, force=False)
        self.processing_thread.finished.connect(
            lambda success, msg: self.on_processing_finished(success, msg, statement_id)
        )
        self.processing_thread.start()

    def reextract_statement(self, statement_id: str):
        """Re-extract a statement with confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Re-extraction",
            "This will delete existing processed data and re-extract from the PDF. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Delete existing data
            success, error = self.processor.delete_statement_data(statement_id)
            if not success:
                QMessageBox.warning(self, "Error", f"Failed to delete data: {error}")
                return

            # Process again
            self.process_statement(statement_id)

    def on_processing_finished(self, success: bool, message: str, statement_id: str):
        """Handle processing completion."""
        if success:
            self.status_label.setText(message)
        else:
            self.status_label.setText(f"Error: {message}")
            QMessageBox.warning(self, "Processing Error", message)

        self.refresh_table()

    def reprocess_all(self):
        """Reprocess all statements."""
        reply = QMessageBox.question(
            self,
            "Confirm Reprocess All",
            "This will reprocess all statements. This may take a while. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # TODO: Implement batch processing
            QMessageBox.information(
                self,
                "Not Implemented",
                "Batch reprocessing will be implemented soon. "
                "For now, please reprocess statements individually."
            )

    def clear_filters(self):
        """Clear all filters."""
        self.account_filter.setCurrentText("All")
        self.status_filter.setCurrentText("All")
        self.date_from.setDate(QDate.currentDate().addMonths(-3))
        self.date_to.setDate(QDate.currentDate().addMonths(1))
        self.refresh_table()

    def _get_statements_dir(self, record: StatementRecord) -> Path:
        """Get statements directory for an account."""
        if not self.config:
            return Path()

        # Find the account's processed folder
        for user in self.config.users:
            for account in user.accounts:
                if account.name == record.account_name:
                    base_dir = self.config.working_dir / account.processed_folder
                    return base_dir / "statements"

        for account in self.config.shared_accounts:
            if account.name == record.account_name:
                base_dir = self.config.working_dir / account.processed_folder
                return base_dir / "statements"

        # Fallback
        return self.config.working_dir / "processed" / "statements"

    def _get_pdf_path(self, record: StatementRecord) -> Path:
        """Get PDF file path for a statement."""
        return Path(record.file_path)

    def _get_raw_excel_path(self, record: StatementRecord) -> Path:
        """Get raw Excel file path for a statement."""
        statements_dir = self._get_statements_dir(record)
        return statements_dir / f"{record.id}_raw.xlsx"

    def _get_classified_excel_path(self, record: StatementRecord) -> Path:
        """Get classified Excel file path for a statement."""
        statements_dir = self._get_statements_dir(record)
        return statements_dir / f"{record.id}_classified.xlsx"

    def open_pdf_statement(self, record: StatementRecord):
        """Open PDF statement in default viewer."""
        pdf_path = self._get_pdf_path(record)

        if not pdf_path.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"PDF file not found:\n{pdf_path}"
            )
            return

        try:
            # Try platform-specific methods
            if sys.platform == 'win32':
                os.startfile(str(pdf_path))
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', str(pdf_path)], check=True)
            else:  # Linux and other Unix-like
                subprocess.run(['xdg-open', str(pdf_path)], check=True)

            self.status_label.setText(f"Opened: {record.filename}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening PDF",
                f"Failed to open PDF file:\n{str(e)}\n\nFile: {pdf_path}"
            )

    def view_transactions(self, record: StatementRecord):
        """View transactions in a dialog."""
        # Determine which file to open (prefer classified, fallback to raw)
        classified_path = self._get_classified_excel_path(record)
        raw_path = self._get_raw_excel_path(record)

        if classified_path.exists():
            excel_path = classified_path
            is_classified = True
        elif raw_path.exists():
            excel_path = raw_path
            is_classified = False
        else:
            QMessageBox.warning(
                self,
                "No Transactions",
                f"No transaction files found for this statement.\n\n"
                f"Expected:\n{classified_path}\nor\n{raw_path}"
            )
            return

        # Open dialog
        dialog = TransactionsViewerDialog(record, excel_path, is_classified, self)
        dialog.exec_()
