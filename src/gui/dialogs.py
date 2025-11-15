"""
Dialog windows for displaying results and detailed information.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from pathlib import Path
import pandas as pd


class ResultsDialog(QDialog):
    """Dialog for displaying detailed results."""

    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.content = content
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 800, 600)

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Text display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlainText(self.content)

        # Use monospace font for better alignment
        font = QFont("Courier New", 9)
        self.text_display.setFont(font)

        layout.addWidget(self.text_display)

        # Buttons
        button_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export to Text File")
        self.export_btn.clicked.connect(self.export_to_file)
        button_layout.addWidget(self.export_btn)

        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def export_to_file(self):
        """Export content to a text file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to Text File",
            "fairshare_report.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.content)

                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Content exported to:\n{file_path}"
                )

            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Error exporting file:\n\n{str(e)}"
                )

    def copy_to_clipboard(self):
        """Copy content to clipboard."""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.content)

        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Copied",
            "Content copied to clipboard!"
        )


class TransactionViewerDialog(QDialog):
    """Dialog for viewing classified transactions from a statement."""

    def __init__(self, transactions_file: Path, statement_info: dict, parent=None):
        super().__init__(parent)
        self.transactions_file = transactions_file
        self.statement_info = statement_info
        self.df = None

        self.setWindowTitle(f"Transactions - {statement_info.get('account_name', 'Unknown')}")
        self.setGeometry(100, 100, 1200, 700)

        self.init_ui()
        self.load_transactions()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Header with statement info
        header_layout = QVBoxLayout()

        title = QLabel(f"Account: {self.statement_info.get('account_name', 'Unknown')}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        # Statement details
        details_text = []
        if self.statement_info.get('owner'):
            details_text.append(f"Owner: {self.statement_info['owner']}")
        if self.statement_info.get('filename'):
            details_text.append(f"Statement: {self.statement_info['filename']}")
        if self.statement_info.get('period_start') and self.statement_info.get('period_end'):
            details_text.append(f"Period: {self.statement_info['period_start']} to {self.statement_info['period_end']}")

        if details_text:
            details_label = QLabel(" | ".join(details_text))
            header_layout.addWidget(details_label)

        layout.addLayout(header_layout)

        # Transactions table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Summary info
        self.summary_label = QLabel("")
        layout.addWidget(self.summary_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        button_layout.addWidget(self.export_btn)

        self.open_file_btn = QPushButton("Open File in Excel")
        self.open_file_btn.clicked.connect(self.open_in_excel)
        button_layout.addWidget(self.open_file_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def load_transactions(self):
        """Load transactions from Excel file."""
        try:
            if not self.transactions_file.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Transactions file not found:\n{self.transactions_file}"
                )
                return

            # Read Excel file
            self.df = pd.read_excel(self.transactions_file, sheet_name="Transactions")

            # Configure table
            self.table.setRowCount(len(self.df))
            self.table.setColumnCount(len(self.df.columns))
            self.table.setHorizontalHeaderLabels(self.df.columns.tolist())

            # Populate table
            for row_idx, (_, row) in enumerate(self.df.iterrows()):
                for col_idx, (col_name, value) in enumerate(row.items()):
                    # Format value
                    if pd.isna(value):
                        display_value = ""
                    elif col_name == 'Amount':
                        display_value = f"R{float(value):,.2f}"
                    elif col_name == 'Date':
                        if hasattr(value, 'strftime'):
                            display_value = value.strftime('%Y-%m-%d')
                        else:
                            display_value = str(value)
                    elif isinstance(value, bool):
                        display_value = "Yes" if value else "No"
                    else:
                        display_value = str(value)

                    item = QTableWidgetItem(display_value)

                    # Color code expense types
                    if col_name == 'Expense Type':
                        if value == 'HOUSEHOLD' or value == 'SHARED':
                            item.setBackground(QColor(200, 255, 200))  # Light green
                        elif value == 'INDIVIDUAL':
                            item.setBackground(QColor(255, 255, 200))  # Light yellow
                        elif value == 'SPLIT':
                            item.setBackground(QColor(200, 220, 255))  # Light blue

                    # Right-align amounts
                    if col_name == 'Amount':
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    self.table.setItem(row_idx, col_idx, item)

            # Auto-resize columns
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            if 'Description' in self.df.columns:
                desc_col = self.df.columns.tolist().index('Description')
                self.table.horizontalHeader().setSectionResizeMode(desc_col, QHeaderView.Stretch)

            # Update summary
            total_transactions = len(self.df)
            household_count = len(self.df[self.df['Expense Type'].isin(['HOUSEHOLD', 'SHARED'])])
            individual_count = len(self.df[self.df['Expense Type'] == 'INDIVIDUAL'])

            summary_parts = [
                f"Total Transactions: {total_transactions}",
                f"Household: {household_count}",
                f"Individual: {individual_count}"
            ]

            if 'Amount' in self.df.columns and 'Is Credit' in self.df.columns:
                total_in = self.df[self.df['Is Credit'] == True]['Amount'].sum()
                total_out = self.df[self.df['Is Credit'] == False]['Amount'].sum()
                summary_parts.append(f"Total In: R{total_in:,.2f}")
                summary_parts.append(f"Total Out: R{total_out:,.2f}")

            self.summary_label.setText(" | ".join(summary_parts))

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load transactions:\n{str(e)}"
            )

    def export_to_excel(self):
        """Export transactions to a new Excel file."""
        if self.df is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Transactions",
            f"transactions_{self.statement_info.get('account_name', 'export')}.xlsx",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            try:
                self.df.to_excel(file_path, index=False, sheet_name="Transactions")
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Transactions exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export transactions:\n{str(e)}"
                )

    def open_in_excel(self):
        """Open the transactions file in Excel."""
        try:
            import subprocess
            import platform

            file_path = str(self.transactions_file)

            if platform.system() == 'Windows':
                subprocess.Popen(['start', file_path], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', file_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', file_path])

        except Exception as e:
            QMessageBox.warning(
                self,
                "Open Error",
                f"Could not open file:\n{str(e)}\n\n"
                f"File location:\n{self.transactions_file}"
            )
