"""
Interactive Bank Template Editor Tab

Provides a user-friendly interface for creating and editing bank statement templates
with real-time validation and side-by-side preview of results.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QComboBox, QLabel, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QGroupBox, QHeaderView, QFrame,
    QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QTextCursor
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import yaml
import re
import traceback
from decimal import Decimal
from datetime import datetime

from bank_template import BankTemplate, TemplateRegistry
from bank_statement_parser import BankStatementParser, BankTransaction, BankStatementSummary
from template_validator import TemplateValidator, ValidationResult, ValidationIssue


class YAMLHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for YAML files"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define highlighting rules
        self.highlighting_rules = []

        # Keys (word followed by colon)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor(0, 0, 200))
        key_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'^\s*[\w_]+:', key_format))

        # Strings (quoted)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(0, 150, 0))
        self.highlighting_rules.append((r'"[^"]*"', string_format))
        self.highlighting_rules.append((r"'[^']*'", string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(128, 128, 128))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'#[^\n]*', comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(200, 0, 200))
        self.highlighting_rules.append((r'\b\d+\b', number_format))

        # Boolean values
        bool_format = QTextCharFormat()
        bool_format.setForeground(QColor(200, 100, 0))
        bool_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'\b(true|false|True|False|yes|no)\b', bool_format))

    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""
        for pattern, format in self.highlighting_rules:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)


class TemplateEditorTab(QWidget):
    """Interactive template editor with side-by-side preview"""

    # Signal emitted when template is saved
    template_saved = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # State
        self.current_template_name: Optional[str] = None
        self.current_pdf_path: Optional[Path] = None
        self.template_registry = TemplateRegistry(Path(__file__).parent.parent.parent / "bank_templates")
        self.validator = TemplateValidator()

        # Debounce timer for auto-validation
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_and_parse)

        self.init_ui()
        self._load_template_list()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("📝 Bank Template Editor")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Create and edit bank statement templates with real-time validation and preview"
        )
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        # Control bar
        control_layout = QHBoxLayout()

        # Template selector
        control_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(200)
        self.template_combo.currentTextChanged.connect(self._on_template_selected)
        control_layout.addWidget(self.template_combo)

        # New template button
        self.new_btn = QPushButton("➕ New Template")
        self.new_btn.clicked.connect(self._create_new_template)
        control_layout.addWidget(self.new_btn)

        # Save template button
        self.save_btn = QPushButton("💾 Save Template")
        self.save_btn.clicked.connect(self._save_template)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)

        control_layout.addStretch()

        # Load PDF button
        self.load_pdf_btn = QPushButton("📄 Load Sample PDF")
        self.load_pdf_btn.clicked.connect(self._load_pdf)
        control_layout.addWidget(self.load_pdf_btn)

        # Parse button
        self.parse_btn = QPushButton("▶️ Parse")
        self.parse_btn.clicked.connect(self._validate_and_parse)
        self.parse_btn.setEnabled(False)
        control_layout.addWidget(self.parse_btn)

        # Validation status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            "padding: 5px 10px; background: #e0e0e0; border-radius: 3px;"
        )
        control_layout.addWidget(self.status_label)

        layout.addLayout(control_layout)

        # Main splitter (3 panels)
        splitter = QSplitter(Qt.Horizontal)

        # LEFT PANEL: Template YAML Editor
        left_panel = self._create_editor_panel()
        splitter.addWidget(left_panel)

        # MIDDLE PANEL: PDF Preview
        middle_panel = self._create_pdf_preview_panel()
        splitter.addWidget(middle_panel)

        # RIGHT PANEL: Parsed Output & Validation
        right_panel = self._create_output_panel()
        splitter.addWidget(right_panel)

        # Set initial sizes (30% / 35% / 35%)
        splitter.setSizes([400, 450, 450])

        layout.addWidget(splitter, stretch=1)

        # Bottom info bar
        info_layout = QHBoxLayout()
        self.info_label = QLabel("💡 Tip: Edit the template on the left and see results update in real-time")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()

        # Validation progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)

        layout.addLayout(info_layout)

    def _create_editor_panel(self) -> QWidget:
        """Create the left panel (YAML editor)"""
        panel = QGroupBox("Template Rules (YAML)")
        layout = QVBoxLayout(panel)

        # YAML text editor
        self.yaml_editor = QTextEdit()
        self.yaml_editor.setFont(QFont("Courier New", 10))
        self.yaml_editor.setLineWrapMode(QTextEdit.NoWrap)
        self.yaml_editor.textChanged.connect(self._on_yaml_changed)

        # Apply syntax highlighting
        self.highlighter = YAMLHighlighter(self.yaml_editor.document())

        layout.addWidget(self.yaml_editor)

        # Editor info
        info = QLabel("💡 Edit directly or load an existing template")
        info.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(info)

        return panel

    def _create_pdf_preview_panel(self) -> QWidget:
        """Create the middle panel (PDF text preview)"""
        panel = QGroupBox("Statement Preview")
        layout = QVBoxLayout(panel)

        # PDF info
        self.pdf_info_label = QLabel("No PDF loaded")
        self.pdf_info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.pdf_info_label)

        # PDF text preview
        self.pdf_preview = QTextEdit()
        self.pdf_preview.setFont(QFont("Courier New", 9))
        self.pdf_preview.setReadOnly(True)
        self.pdf_preview.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.pdf_preview)

        # Legend
        legend = QLabel(
            "🟢 Matched transactions | 🔴 Skipped lines | 🟡 Section markers"
        )
        legend.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(legend)

        return panel

    def _create_output_panel(self) -> QWidget:
        """Create the right panel (parsed output & validation)"""
        panel = QGroupBox("Parsed Output & Validation")
        layout = QVBoxLayout(panel)

        # Validation section
        validation_group = QGroupBox("Validation Results")
        validation_layout = QVBoxLayout(validation_group)

        self.validation_text = QTextEdit()
        self.validation_text.setMaximumHeight(150)
        self.validation_text.setReadOnly(True)
        self.validation_text.setFont(QFont("Courier New", 9))
        validation_layout.addWidget(self.validation_text)

        layout.addWidget(validation_group)

        # Summary section
        summary_group = QGroupBox("Statement Summary")
        summary_layout = QVBoxLayout(summary_group)

        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(100)
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Courier New", 9))
        summary_layout.addWidget(self.summary_text)

        layout.addWidget(summary_group)

        # Transactions table
        transactions_group = QGroupBox("Parsed Transactions")
        transactions_layout = QVBoxLayout(transactions_group)

        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels([
            "Date", "Description", "Amount", "Type", "Card"
        ])
        self.transactions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.transactions_table.setAlternatingRowColors(True)
        transactions_layout.addWidget(self.transactions_table)

        layout.addWidget(transactions_group)

        # Export button
        self.export_btn = QPushButton("📊 Export to Excel")
        self.export_btn.clicked.connect(self._export_transactions)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        return panel

    def _load_template_list(self):
        """Load available templates into combo box"""
        self.template_combo.clear()
        self.template_combo.addItem("-- Select Template --", None)

        templates = self.template_registry.list_all()
        for template_name, bank_name, account_type in sorted(templates):
            display_name = f"{bank_name} - {account_type} ({template_name})"
            self.template_combo.addItem(display_name, template_name)

    def _on_template_selected(self, display_name: str):
        """Handle template selection from dropdown"""
        template_name = self.template_combo.currentData()
        if not template_name:
            self.yaml_editor.clear()
            self.current_template_name = None
            self.save_btn.setEnabled(False)
            return

        # Load template YAML
        template_path = Path(__file__).parent.parent.parent / "bank_templates" / f"{template_name}.yaml"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()

            # Block signals to avoid triggering validation during load
            self.yaml_editor.blockSignals(True)
            self.yaml_editor.setPlainText(yaml_content)
            self.yaml_editor.blockSignals(False)

            self.current_template_name = template_name
            self.save_btn.setEnabled(True)
            self._update_status(f"Loaded template: {template_name}", "info")

            # Trigger validation
            self._validate_and_parse()

    def _on_yaml_changed(self):
        """Handle YAML editor text changes (debounced validation)"""
        self.save_btn.setEnabled(True)
        self._update_status("Template modified (unsaved)", "warning")

        # Debounce: wait 1 second after user stops typing
        self.validation_timer.stop()
        self.validation_timer.start(1000)

    def _validate_and_parse(self):
        """Validate template and parse PDF if available"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
            # Get YAML content
            yaml_content = self.yaml_editor.toPlainText().strip()
            if not yaml_content:
                self._update_validation("No template content", [])
                self.progress_bar.setVisible(False)
                return

            self.progress_bar.setValue(20)

            # Parse YAML
            try:
                template_dict = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                self._update_validation(f"YAML Syntax Error: {str(e)}", [])
                self._update_status("YAML syntax error", "error")
                self.progress_bar.setVisible(False)
                return

            self.progress_bar.setValue(40)

            # Validate template structure
            template_name = self.current_template_name or template_dict.get('bank_name', 'template')
            validation_result = self.validator.validate(template_dict, template_name)
            self._update_validation_results(validation_result)

            self.progress_bar.setValue(60)

            # If PDF is loaded and template is valid, parse it
            if self.current_pdf_path and validation_result.is_valid:
                self._parse_pdf_with_template(template_dict)

            self.progress_bar.setValue(100)

            # Update status based on validation
            if validation_result.is_valid:
                self._update_status(f"✅ Valid (Score: {validation_result.score:.0f}/100)", "success")
            else:
                self._update_status(f"❌ Invalid ({len(validation_result.errors)} errors)", "error")

        except Exception as e:
            self._update_validation(f"Validation Error: {str(e)}", [])
            self._update_status("Validation failed", "error")
            print(f"Validation error: {traceback.format_exc()}")

        finally:
            self.progress_bar.setVisible(False)

    def _update_validation_results(self, result: ValidationResult):
        """Update validation text with results"""
        lines = []
        lines.append(f"Validation Score: {result.score:.0f}/100")
        lines.append(f"Status: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
        lines.append("")

        if result.errors:
            lines.append(f"🔴 ERRORS ({len(result.errors)}):")
            for issue in result.errors:
                lines.append(f"  • {issue.message}")
                if issue.field:
                    lines.append(f"    Field: {issue.field}")
            lines.append("")

        if result.warnings:
            lines.append(f"🟡 WARNINGS ({len(result.warnings)}):")
            for issue in result.warnings:
                lines.append(f"  • {issue.message}")
                if issue.field:
                    lines.append(f"    Field: {issue.field}")
            lines.append("")

        if result.infos:
            lines.append(f"ℹ️  INFO ({len(result.infos)}):")
            for issue in result.infos:
                lines.append(f"  • {issue.message}")
            lines.append("")

        if result.is_valid and not result.warnings:
            lines.append("✅ Template is valid and ready to use!")

        self.validation_text.setPlainText("\n".join(lines))

    def _update_validation(self, message: str, issues: List[ValidationIssue]):
        """Update validation display (simple version)"""
        text = message + "\n"
        for issue in issues:
            text += f"  • {issue.message}\n"
        self.validation_text.setPlainText(text)

    def _load_pdf(self):
        """Load a PDF for testing the template"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Bank Statement PDF",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )

        if not file_path:
            return

        self.current_pdf_path = Path(file_path)
        self.parse_btn.setEnabled(True)

        # Extract and display PDF text
        try:
            import pdfplumber
            with pdfplumber.open(self.current_pdf_path) as pdf:
                text_parts = []
                for i, page in enumerate(pdf.pages):
                    text_parts.append(f"--- PAGE {i+1} ---\n")
                    text_parts.append(page.extract_text())
                    text_parts.append("\n\n")

                full_text = "".join(text_parts)
                self.pdf_preview.setPlainText(full_text)

                self.pdf_info_label.setText(
                    f"📄 {self.current_pdf_path.name} ({len(pdf.pages)} pages, {len(full_text)} chars)"
                )

                self._update_status(f"Loaded PDF: {self.current_pdf_path.name}", "info")

                # Trigger parsing if template is loaded
                if self.yaml_editor.toPlainText().strip():
                    self._validate_and_parse()

        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Failed to load PDF:\n{str(e)}")
            print(f"PDF loading error: {traceback.format_exc()}")

    def _parse_pdf_with_template(self, template_dict: dict):
        """Parse the loaded PDF using the template"""
        if not self.current_pdf_path:
            return

        try:
            # Create temporary template
            template_name = template_dict.get('bank_name', 'temp').lower().replace(' ', '_')
            template = BankTemplate(
                bank_name=template_dict.get('bank_name', 'Unknown'),
                account_type=template_dict.get('account_type', 'Unknown'),
                config=template_dict,
                template_name=template_name
            )

            # Parse PDF
            parser = BankStatementParser(self.current_pdf_path, template)
            summary, transactions = parser.parse()

            # Update summary
            self._update_summary(summary, transactions)

            # Update transactions table
            self._update_transactions_table(transactions)

            # Highlight matched lines in PDF preview
            self._highlight_pdf_matches(transactions, template_dict)

            self.export_btn.setEnabled(len(transactions) > 0)

        except Exception as e:
            self._update_summary_error(f"Parsing Error: {str(e)}")
            print(f"Parsing error: {traceback.format_exc()}")

    def _update_summary(self, summary: BankStatementSummary, transactions: List[BankTransaction]):
        """Update summary text"""
        lines = []
        lines.append(f"Statement Date: {summary.statement_date.strftime('%Y-%m-%d')}")
        lines.append(f"Opening Balance: R {summary.opening_balance:,.2f}")
        lines.append(f"Closing Balance: R {summary.closing_balance:,.2f}")
        lines.append("")
        lines.append(f"Total Expenses: R {summary.total_expenses:,.2f} ({summary.debit_count} transactions)")
        lines.append(f"Total Payments: R {summary.total_payments:,.2f} ({summary.credit_count} transactions)")
        lines.append("")
        lines.append(f"✅ Successfully parsed {len(transactions)} transactions")

        self.summary_text.setPlainText("\n".join(lines))

    def _update_summary_error(self, error_msg: str):
        """Update summary with error message"""
        self.summary_text.setPlainText(f"❌ {error_msg}")

    def _update_transactions_table(self, transactions: List[BankTransaction]):
        """Update transactions table"""
        self.transactions_table.setRowCount(len(transactions))

        for row, txn in enumerate(transactions):
            # Date
            date_item = QTableWidgetItem(txn.date.strftime('%Y-%m-%d'))
            self.transactions_table.setItem(row, 0, date_item)

            # Description
            desc_item = QTableWidgetItem(txn.description)
            self.transactions_table.setItem(row, 1, desc_item)

            # Amount
            amount_item = QTableWidgetItem(f"R {txn.amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Color code: green for credits, red for debits
            if txn.is_credit:
                amount_item.setForeground(QColor(0, 150, 0))
            else:
                amount_item.setForeground(QColor(200, 0, 0))

            self.transactions_table.setItem(row, 2, amount_item)

            # Type
            type_item = QTableWidgetItem("Credit" if txn.is_credit else "Debit")
            self.transactions_table.setItem(row, 3, type_item)

            # Card
            card_item = QTableWidgetItem(txn.card_last_digits or "")
            self.transactions_table.setItem(row, 4, card_item)

    def _highlight_pdf_matches(self, transactions: List[BankTransaction], template_dict: dict):
        """Highlight matched transaction lines in PDF preview"""
        # This is a simplified version - could be enhanced with actual line matching
        # For now, we'll just add a note at the top
        current_text = self.pdf_preview.toPlainText()

        # Count matched lines (transactions have raw_line if available)
        matched_count = sum(1 for txn in transactions if txn.raw_line)

        note = f"✅ Matched {matched_count} transaction lines from {len(transactions)} total transactions\n"
        note += "=" * 80 + "\n\n"

        self.pdf_preview.setPlainText(note + current_text)

    def _create_new_template(self):
        """Create a new template from scratch"""
        template_name, ok = QMessageBox.getText(
            self,
            "New Template",
            "Enter template name (e.g., 'mybank_credit_card'):"
        )

        if not ok or not template_name:
            return

        # Create template skeleton
        skeleton = """bank_name: "MyBank"
account_type: "Credit Card"

detection:
  markers:
    - "MYBANK"
    - "CREDIT CARD"
  priority: 5

parsing:
  transaction_pattern: '(?P<day>\\d{2})\\s+(?P<month>\\w{3})\\s+(?P<description>.+?)\\s+(?P<amount>[\\d,.]+)'

  date:
    day_group: "day"
    month_group: "month"
    format: "%d %b"
    year_source: "statement"

  amount:
    group: "amount"
    decimal_separator: "."
    thousands_separator: ","

  description:
    group: "description"
    min_length: 3

sections:
  start_markers:
    - "Transaction Date"
  end_markers:
    - "Closing Balance"
  skip_lines:
    - "Page "

summary:
  statement_date:
    pattern: 'Statement Date\\s+(?P<date>\\d{2}\\s+\\w+\\s+\\d{4})'
    format: "%d %b %Y"

output:
  account_type: "credit_card"
"""

        self.yaml_editor.setPlainText(skeleton)
        self.current_template_name = template_name
        self.save_btn.setEnabled(True)
        self._update_status("New template created", "info")

    def _save_template(self):
        """Save the current template"""
        if not self.current_template_name:
            self._create_new_template()
            return

        try:
            # Validate YAML first
            yaml_content = self.yaml_editor.toPlainText()
            template_dict = yaml.safe_load(yaml_content)

            # Save to file
            template_path = Path(__file__).parent.parent.parent / "bank_templates" / f"{self.current_template_name}.yaml"
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            self._update_status(f"✅ Saved: {self.current_template_name}.yaml", "success")

            # Reload template registry
            self.template_registry = TemplateRegistry(Path(__file__).parent.parent.parent / "bank_templates")
            self._load_template_list()

            # Emit signal
            self.template_saved.emit(self.current_template_name)

            QMessageBox.information(
                self,
                "Template Saved",
                f"Template '{self.current_template_name}' has been saved successfully!"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save template:\n{str(e)}"
            )

    def _export_transactions(self):
        """Export parsed transactions to Excel"""
        if not self.current_pdf_path:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Transactions",
            f"{self.current_pdf_path.stem}_transactions.xlsx",
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Re-parse and export
            yaml_content = self.yaml_editor.toPlainText()
            template_dict = yaml.safe_load(yaml_content)

            template = BankTemplate(
                bank_name=template_dict.get('bank_name', 'Unknown'),
                account_type=template_dict.get('account_type', 'Unknown'),
                config=template_dict,
                template_name='temp'
            )

            parser = BankStatementParser(self.current_pdf_path, template)
            parser.parse()
            parser.export_to_excel(Path(file_path))

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

    def _update_status(self, message: str, status_type: str = "info"):
        """Update status label"""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336"
        }

        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }

        color = colors.get(status_type, colors["info"])
        icon = icons.get(status_type, "")

        self.status_label.setText(f"{icon} {message}")
        self.status_label.setStyleSheet(
            f"padding: 5px 10px; background: {color}; color: white; "
            f"border-radius: 3px; font-weight: bold;"
        )
