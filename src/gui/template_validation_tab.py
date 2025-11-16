"""
Template Validation Tab - Validate bank statement templates.
"""

from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QGroupBox,
    QSplitter, QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from src.template_validator import TemplateValidator, ValidationResult, ValidationSeverity


class ValidationWorker(QThread):
    """Worker thread for template validation."""
    finished = pyqtSignal(ValidationResult)
    error = pyqtSignal(str)

    def __init__(self, template_path: Path):
        super().__init__()
        self.template_path = template_path

    def run(self):
        """Run validation in background."""
        try:
            validator = TemplateValidator()
            result = validator.validate_template(self.template_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class TemplateValidationTab(QWidget):
    """Tab for validating bank statement templates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.templates_dir = Path("bank_templates")
        self.current_result = None
        self.validator = TemplateValidator()

        self.init_ui()
        self.refresh_templates()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Template Validation")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        description_label = QLabel(
            "Validate bank statement templates to ensure they're configured correctly.\n"
            "This helps catch configuration errors before parsing statements."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        # Main content area (splitter for templates list and results)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # Left side: Templates list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        templates_group = QGroupBox("Available Templates")
        templates_layout = QVBoxLayout(templates_group)

        # Templates directory info
        dir_label = QLabel(f"Directory: {self.templates_dir}")
        dir_label.setWordWrap(True)
        templates_layout.addWidget(dir_label)

        # Templates list
        self.templates_list = QListWidget()
        self.templates_list.itemSelectionChanged.connect(self.on_template_selected)
        self.templates_list.itemDoubleClicked.connect(self.validate_selected)
        templates_layout.addWidget(self.templates_list)

        # Buttons
        buttons_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_templates)
        buttons_layout.addWidget(refresh_btn)

        validate_btn = QPushButton("Validate Selected")
        validate_btn.clicked.connect(self.validate_selected)
        buttons_layout.addWidget(validate_btn)

        validate_all_btn = QPushButton("Validate All")
        validate_all_btn.clicked.connect(self.validate_all)
        buttons_layout.addWidget(validate_all_btn)

        buttons_layout.addStretch()
        templates_layout.addLayout(buttons_layout)

        left_layout.addWidget(templates_group)
        splitter.addWidget(left_widget)

        # Right side: Validation results
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout(results_group)

        # Summary area
        self.summary_label = QLabel("Select a template to validate")
        self.summary_label.setWordWrap(True)
        summary_font = QFont()
        summary_font.setPointSize(10)
        self.summary_label.setFont(summary_font)
        results_layout.addWidget(self.summary_label)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        results_layout.addWidget(self.progress_bar)

        # Detailed results
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier", 9))
        results_layout.addWidget(self.results_text)

        # Action buttons
        action_layout = QHBoxLayout()

        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_report)
        action_layout.addWidget(export_btn)

        clear_btn = QPushButton("Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        action_layout.addWidget(clear_btn)

        action_layout.addStretch()
        results_layout.addLayout(action_layout)

        right_layout.addWidget(results_group)
        splitter.addWidget(right_widget)

        # Set splitter proportions (30% left, 70% right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

    def refresh_templates(self):
        """Refresh the templates list."""
        self.templates_list.clear()

        if not self.templates_dir.exists():
            item = QListWidgetItem("⚠️ Templates directory not found")
            item.setForeground(QColor("#FF6B6B"))
            self.templates_list.addItem(item)
            return

        # Find all YAML templates
        templates = list(self.templates_dir.glob("*.yaml"))
        templates.extend(self.templates_dir.glob("*.yml"))

        if not templates:
            item = QListWidgetItem("ℹ️ No templates found")
            item.setForeground(QColor("#95A5A6"))
            self.templates_list.addItem(item)
            return

        # Add templates to list
        for template_path in sorted(templates):
            item = QListWidgetItem(f"📄 {template_path.stem}")
            item.setData(Qt.UserRole, template_path)
            self.templates_list.addItem(item)

        # Update summary
        self.summary_label.setText(f"Found {len(templates)} template(s)")

    def on_template_selected(self):
        """Handle template selection."""
        items = self.templates_list.selectedItems()
        if not items:
            return

        item = items[0]
        template_path = item.data(Qt.UserRole)

        if template_path:
            self.summary_label.setText(f"Selected: {template_path.name}\nDouble-click or click 'Validate Selected' to validate")

    def validate_selected(self):
        """Validate the selected template."""
        items = self.templates_list.selectedItems()
        if not items:
            QMessageBox.information(self, "No Selection", "Please select a template to validate")
            return

        item = items[0]
        template_path = item.data(Qt.UserRole)

        if not template_path:
            return

        self.validate_template(template_path)

    def validate_all(self):
        """Validate all templates."""
        templates = []
        for i in range(self.templates_list.count()):
            item = self.templates_list.item(i)
            template_path = item.data(Qt.UserRole)
            if template_path:
                templates.append(template_path)

        if not templates:
            QMessageBox.information(self, "No Templates", "No templates found to validate")
            return

        # Validate all and show combined results
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(templates))
        self.progress_bar.setValue(0)

        results = []
        for i, template_path in enumerate(templates):
            result = self.validator.validate_template(template_path)
            results.append(result)
            self.progress_bar.setValue(i + 1)

        self.progress_bar.setVisible(False)

        # Display combined results
        self.show_combined_results(results)

    def validate_template(self, template_path: Path):
        """Validate a single template."""
        self.summary_label.setText(f"Validating {template_path.name}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Run validation in background
        self.worker = ValidationWorker(template_path)
        self.worker.finished.connect(self.on_validation_finished)
        self.worker.error.connect(self.on_validation_error)
        self.worker.start()

    def on_validation_finished(self, result: ValidationResult):
        """Handle validation completion."""
        self.progress_bar.setVisible(False)
        self.current_result = result

        # Update summary
        status_color = "#27AE60" if result.is_valid else "#E74C3C"
        status_text = "VALID ✓" if result.is_valid else "INVALID ✗"

        summary_html = f"""
        <div style="padding: 10px; background-color: {status_color}22; border-left: 4px solid {status_color};">
            <h3 style="margin: 0; color: {status_color};">{status_text}</h3>
            <p style="margin: 5px 0;"><strong>Template:</strong> {result.template_name}</p>
            <p style="margin: 5px 0;"><strong>Score:</strong> {result.score:.1f}/100</p>
            <p style="margin: 5px 0;">
                <strong>Issues:</strong>
                {len(result.errors)} errors,
                {len(result.warnings)} warnings,
                {len(result.infos)} info
            </p>
        </div>
        """
        self.summary_label.setText(summary_html)

        # Display detailed results
        self.results_text.setPlainText(result.detailed_report())

    def on_validation_error(self, error_msg: str):
        """Handle validation error."""
        self.progress_bar.setVisible(False)
        self.summary_label.setText(f"❌ Validation failed: {error_msg}")
        self.results_text.setPlainText(f"Error during validation:\n{error_msg}")

    def show_combined_results(self, results: list):
        """Show combined results from multiple templates."""
        # Summary
        total = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total - valid_count

        summary = f"Validated {total} templates: {valid_count} valid, {invalid_count} invalid"
        self.summary_label.setText(summary)

        # Detailed results
        lines = [
            "=" * 80,
            "BATCH VALIDATION REPORT",
            "=" * 80,
            "",
            f"Total Templates: {total}",
            f"Valid: {valid_count}",
            f"Invalid: {invalid_count}",
            "",
        ]

        # Group by status
        valid_templates = [r for r in results if r.is_valid]
        invalid_templates = [r for r in results if not r.is_valid]

        if valid_templates:
            lines.append("✓ VALID TEMPLATES:")
            lines.append("-" * 80)
            for result in valid_templates:
                lines.append(f"  ✓ {result.template_name} (Score: {result.score:.1f}/100)")
            lines.append("")

        if invalid_templates:
            lines.append("✗ INVALID TEMPLATES:")
            lines.append("-" * 80)
            for result in invalid_templates:
                lines.append(f"  ✗ {result.template_name} (Score: {result.score:.1f}/100)")
                lines.append(f"     Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")
            lines.append("")

        # Detailed reports for each
        lines.append("")
        lines.append("=" * 80)
        lines.append("DETAILED REPORTS")
        lines.append("=" * 80)
        lines.append("")

        for result in results:
            lines.append(result.detailed_report())
            lines.append("\n")

        self.results_text.setPlainText("\n".join(lines))

    def export_report(self):
        """Export validation report to file."""
        if not self.current_result and not self.results_text.toPlainText():
            QMessageBox.information(self, "No Results", "No validation results to export")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Validation Report",
            f"validation_report.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.results_text.toPlainText())

            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error exporting report:\n{str(e)}")

    def clear_results(self):
        """Clear validation results."""
        self.current_result = None
        self.summary_label.setText("Select a template to validate")
        self.results_text.clear()
