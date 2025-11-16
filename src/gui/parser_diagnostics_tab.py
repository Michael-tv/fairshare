"""
Parser Diagnostics Tab - View parser logs, errors, and statistics.
"""

from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QGroupBox, QSplitter, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QComboBox, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QBrush

from src.parser_diagnostics import (
    get_diagnostics_collector, configure_parser_logging,
    ParsingSession
)
import logging


class ParserDiagnosticsTab(QWidget):
    """Tab for viewing parser diagnostics, logs, and errors."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.collector = get_diagnostics_collector()

        # Configure logging
        configure_parser_logging(logging.INFO)

        self.init_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Parser Diagnostics & Logging")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        description_label = QLabel(
            "Monitor bank statement parsing operations, view logs, and investigate errors.\n"
            "This helps troubleshoot parsing issues and understand what's being processed."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        # Controls
        controls_layout = QHBoxLayout()

        # Session selector
        controls_layout.addWidget(QLabel("Session:"))
        self.session_combo = QComboBox()
        self.session_combo.currentIndexChanged.connect(self.on_session_changed)
        controls_layout.addWidget(self.session_combo, stretch=1)

        # Auto-refresh checkbox
        self.auto_refresh_checkbox = QCheckBox("Auto-refresh")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_checkbox)

        # Refresh button
        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.clicked.connect(self.refresh_display)
        controls_layout.addWidget(refresh_btn)

        # Clear button
        clear_btn = QPushButton("Clear All Sessions")
        clear_btn.clicked.connect(self.clear_all_sessions)
        controls_layout.addWidget(clear_btn)

        # Export button
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_report)
        controls_layout.addWidget(export_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Main content tabs
        self.content_tabs = QTabWidget()
        layout.addWidget(self.content_tabs, stretch=1)

        # Add tabs
        self.content_tabs.addTab(self.create_statistics_tab(), "Statistics")
        self.content_tabs.addTab(self.create_logs_tab(), "Logs")
        self.content_tabs.addTab(self.create_failed_lines_tab(), "Failed Lines")
        self.content_tabs.addTab(self.create_unmatched_lines_tab(), "Unmatched Lines")
        self.content_tabs.addTab(self.create_settings_tab(), "Settings")

        # Initial refresh
        self.refresh_display()

    def create_statistics_tab(self):
        """Create the statistics display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Summary text
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.stats_text)

        return widget

    def create_logs_tab(self):
        """Create the logs display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Log level filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Show:"))

        self.show_debug_checkbox = QCheckBox("DEBUG")
        filter_layout.addWidget(self.show_debug_checkbox)

        self.show_info_checkbox = QCheckBox("INFO")
        self.show_info_checkbox.setChecked(True)
        filter_layout.addWidget(self.show_info_checkbox)

        self.show_warning_checkbox = QCheckBox("WARNING")
        self.show_warning_checkbox.setChecked(True)
        filter_layout.addWidget(self.show_warning_checkbox)

        self.show_error_checkbox = QCheckBox("ERROR")
        self.show_error_checkbox.setChecked(True)
        filter_layout.addWidget(self.show_error_checkbox)

        filter_layout.addStretch()
        apply_filter_btn = QPushButton("Apply Filter")
        apply_filter_btn.clicked.connect(self.refresh_logs)
        filter_layout.addWidget(apply_filter_btn)

        layout.addLayout(filter_layout)

        # Log display
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.logs_text)

        return widget

    def create_failed_lines_tab(self):
        """Create the failed lines display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel("Lines that matched the pattern but failed to create transactions:")
        layout.addWidget(info_label)

        # Table for failed lines
        self.failed_lines_table = QTableWidget()
        self.failed_lines_table.setColumnCount(4)
        self.failed_lines_table.setHorizontalHeaderLabels(["Line #", "Line Text", "Reason", "Error"])
        self.failed_lines_table.horizontalHeader().setStretchLastSection(True)
        self.failed_lines_table.setAlternatingRowColors(True)
        layout.addWidget(self.failed_lines_table)

        return widget

    def create_unmatched_lines_tab(self):
        """Create the unmatched lines display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel("Lines that didn't match the transaction pattern (showing first 100):")
        layout.addWidget(info_label)

        # Unmatched lines display
        self.unmatched_text = QTextEdit()
        self.unmatched_text.setReadOnly(True)
        self.unmatched_text.setFont(QFont("Courier", 8))
        layout.addWidget(self.unmatched_text)

        return widget

    def create_settings_tab(self):
        """Create the settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Logging settings
        logging_group = QGroupBox("Logging Settings")
        logging_layout = QVBoxLayout(logging_group)

        # Log level
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Log Level:"))

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("DEBUG", logging.DEBUG)
        self.log_level_combo.addItem("INFO", logging.INFO)
        self.log_level_combo.addItem("WARNING", logging.WARNING)
        self.log_level_combo.addItem("ERROR", logging.ERROR)
        self.log_level_combo.setCurrentIndex(1)  # INFO
        self.log_level_combo.currentIndexChanged.connect(self.on_log_level_changed)
        level_layout.addWidget(self.log_level_combo)
        level_layout.addStretch()

        logging_layout.addLayout(level_layout)

        # Max sessions to keep
        sessions_layout = QHBoxLayout()
        sessions_layout.addWidget(QLabel("Max sessions to keep:"))

        self.max_sessions_spin = QSpinBox()
        self.max_sessions_spin.setRange(1, 100)
        self.max_sessions_spin.setValue(10)
        sessions_layout.addWidget(self.max_sessions_spin)
        sessions_layout.addStretch()

        logging_layout.addLayout(sessions_layout)

        layout.addWidget(logging_group)

        # Diagnostics settings
        diag_group = QGroupBox("Diagnostics Collection")
        diag_layout = QVBoxLayout(diag_group)

        self.collect_line_attempts_checkbox = QCheckBox("Collect line-by-line parse attempts")
        self.collect_line_attempts_checkbox.setChecked(True)
        diag_layout.addWidget(self.collect_line_attempts_checkbox)

        self.collect_logs_checkbox = QCheckBox("Collect log messages")
        self.collect_logs_checkbox.setChecked(True)
        diag_layout.addWidget(self.collect_logs_checkbox)

        layout.addWidget(diag_group)

        layout.addStretch()

        return widget

    def refresh_display(self):
        """Refresh all displays."""
        self.refresh_sessions()
        self.refresh_statistics()
        self.refresh_logs()
        self.refresh_failed_lines()
        self.refresh_unmatched_lines()

    def refresh_sessions(self):
        """Refresh the sessions dropdown."""
        current_text = self.session_combo.currentText()

        self.session_combo.clear()

        # Get all sessions
        sessions = self.collector.sessions.copy()
        if self.collector.current_session:
            sessions.append(self.collector.current_session)

        if not sessions:
            self.session_combo.addItem("No sessions yet")
            return

        # Add sessions to dropdown (most recent first)
        for i, session in enumerate(reversed(sessions)):
            pdf_name = Path(session.statistics.pdf_path).name if session.statistics.pdf_path else "Unknown"
            label = f"#{len(sessions)-i}: {pdf_name} ({session.statistics.template_name})"
            self.session_combo.addItem(label, session)

        # Try to restore selection
        idx = self.session_combo.findText(current_text)
        if idx >= 0:
            self.session_combo.setCurrentIndex(idx)
        else:
            self.session_combo.setCurrentIndex(0)

    def on_session_changed(self):
        """Handle session selection change."""
        self.refresh_statistics()
        self.refresh_logs()
        self.refresh_failed_lines()
        self.refresh_unmatched_lines()

    def get_current_session(self) -> ParsingSession:
        """Get the currently selected session."""
        return self.session_combo.currentData()

    def refresh_statistics(self):
        """Refresh statistics display."""
        session = self.get_current_session()

        if not session:
            self.stats_text.setPlainText("No session selected")
            return

        self.stats_text.setPlainText(session.statistics.detailed_report())

    def refresh_logs(self):
        """Refresh logs display."""
        session = self.get_current_session()

        if not session or not session.log_messages:
            self.logs_text.setPlainText("No log messages")
            return

        # Filter logs by level
        show_levels = set()
        if self.show_debug_checkbox.isChecked():
            show_levels.add('DEBUG')
        if self.show_info_checkbox.isChecked():
            show_levels.add('INFO')
        if self.show_warning_checkbox.isChecked():
            show_levels.add('WARNING')
        if self.show_error_checkbox.isChecked():
            show_levels.add('ERROR')

        # Build log text with color coding
        self.logs_text.clear()

        for log in session.log_messages:
            if log['level'] not in show_levels:
                continue

            timestamp = log['timestamp'].strftime('%H:%M:%S.%f')[:-3]
            level = log['level']
            message = log['message']

            # Color code by level
            if level == 'ERROR':
                color = QColor("#E74C3C")
            elif level == 'WARNING':
                color = QColor("#F39C12")
            elif level == 'INFO':
                color = QColor("#3498DB")
            else:  # DEBUG
                color = QColor("#95A5A6")

            # Create formatted line
            cursor = self.logs_text.textCursor()
            cursor.movePosition(cursor.End)

            # Timestamp
            fmt = QTextCharFormat()
            fmt.setForeground(QBrush(QColor("#7F8C8D")))
            cursor.setCharFormat(fmt)
            cursor.insertText(f"[{timestamp}] ")

            # Level
            fmt = QTextCharFormat()
            fmt.setForeground(QBrush(color))
            fmt.setFontWeight(QFont.Bold)
            cursor.setCharFormat(fmt)
            cursor.insertText(f"{level:8s} ")

            # Message
            fmt = QTextCharFormat()
            fmt.setForeground(QBrush(QColor("#2C3E50")))
            cursor.setCharFormat(fmt)
            cursor.insertText(f"{message}\n")

    def refresh_failed_lines(self):
        """Refresh failed lines table."""
        session = self.get_current_session()

        if not session:
            self.failed_lines_table.setRowCount(0)
            return

        failed = session.get_failed_lines()
        self.failed_lines_table.setRowCount(len(failed))

        for row, attempt in enumerate(failed):
            # Line number
            item = QTableWidgetItem(str(attempt.line_number))
            self.failed_lines_table.setItem(row, 0, item)

            # Line text (truncated)
            text = attempt.line_text[:80] + "..." if len(attempt.line_text) > 80 else attempt.line_text
            item = QTableWidgetItem(text)
            self.failed_lines_table.setItem(row, 1, item)

            # Reason
            item = QTableWidgetItem(attempt.skip_reason or "")
            self.failed_lines_table.setItem(row, 2, item)

            # Error
            item = QTableWidgetItem(attempt.error or "")
            self.failed_lines_table.setItem(row, 3, item)

        # Resize columns
        self.failed_lines_table.resizeColumnsToContents()
        self.failed_lines_table.horizontalHeader().setStretchLastSection(True)

    def refresh_unmatched_lines(self):
        """Refresh unmatched lines display."""
        session = self.get_current_session()

        if not session:
            self.unmatched_text.setPlainText("No session selected")
            return

        unmatched = session.get_unmatched_lines()

        if not unmatched:
            self.unmatched_text.setPlainText("No unmatched lines (all lines matched the pattern)")
            return

        lines = [f"Total unmatched lines: {len(unmatched)}\n"]
        lines.append("Showing first 100:\n")
        lines.append("=" * 80 + "\n\n")

        for attempt in unmatched[:100]:
            lines.append(f"Line {attempt.line_number}: {attempt.line_text}\n")

        self.unmatched_text.setPlainText("".join(lines))

    def toggle_auto_refresh(self):
        """Toggle auto-refresh."""
        if self.auto_refresh_checkbox.isChecked():
            self.refresh_timer.start(2000)
        else:
            self.refresh_timer.stop()

    def on_log_level_changed(self):
        """Handle log level change."""
        level = self.log_level_combo.currentData()
        configure_parser_logging(level)
        QMessageBox.information(self, "Log Level Changed", f"Parser logging level set to {self.log_level_combo.currentText()}")

    def clear_all_sessions(self):
        """Clear all diagnostic sessions."""
        reply = QMessageBox.question(
            self,
            "Clear Sessions",
            "Are you sure you want to clear all diagnostic sessions?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.collector.clear_sessions()
            self.refresh_display()
            QMessageBox.information(self, "Cleared", "All diagnostic sessions cleared")

    def export_report(self):
        """Export current session report."""
        session = self.get_current_session()

        if not session:
            QMessageBox.information(self, "No Session", "No session selected to export")
            return

        pdf_name = Path(session.statistics.pdf_path).stem if session.statistics.pdf_path else "unknown"
        default_name = f"parser_diagnostics_{pdf_name}.txt"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Diagnostics Report",
            default_name,
            "Text Files (*.txt);;All Files (*)"
        )

        if not filename:
            return

        try:
            session.export_to_file(Path(filename))
            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error exporting report:\n{str(e)}")
