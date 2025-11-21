"""
Main window for FairShare GUI application.
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QApplication, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from gui.settings_tab import SettingsTab
from gui.template_editor_tab import TemplateEditorTab
from gui.process_statements_tab import ProcessStatementsTab
from gui.view_transactions_tab import ViewTransactionsTab
from gui.monthly_transactions_tab import MonthlyTransactionsTab
from gui.classifier_tab import TransactionClassifierTab
from gui.calculate_tab import CalculateTab


class MainWindow(QMainWindow):
    """Main application window for FairShare GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FairShare - Household Finance Splitter")
        self.setGeometry(100, 100, 1000, 700)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)

        # Initialize tabs
        self.settings_tab = SettingsTab(self)
        self.template_editor_tab = TemplateEditorTab(self)
        self.process_statements_tab = ProcessStatementsTab(self)
        self.view_transactions_tab = ViewTransactionsTab(self)
        self.monthly_transactions_tab = MonthlyTransactionsTab(self)
        self.classifier_tab = TransactionClassifierTab(self)
        self.calculate_tab = CalculateTab(self)

        # Add tabs to widget in order
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.template_editor_tab, "Template Editor")
        self.tabs.addTab(self.process_statements_tab, "Process Statements")
        self.tabs.addTab(self.view_transactions_tab, "View Transactions")
        self.tabs.addTab(self.monthly_transactions_tab, "Monthly Transactions")
        self.tabs.addTab(self.classifier_tab, "Transaction Classifier")
        self.tabs.addTab(self.calculate_tab, "Calculate")

        # Set initial focus on settings tab
        self.tabs.setCurrentIndex(0)

    def on_tab_changed(self, index):
        """Handle tab change events - reload state to ensure tabs show current data."""
        tab_widget = self.tabs.widget(index)

        # Reload state when switching to Process Statements tab
        if tab_widget == self.process_statements_tab:
            if hasattr(tab_widget, 'processor') and tab_widget.processor:
                tab_widget.processor.reload_state()
                tab_widget.processor.sync_state_with_filesystem()
                if hasattr(tab_widget, 'refresh_table'):
                    tab_widget.refresh_table()

        # Reload state when switching to View Transactions tab
        elif tab_widget == self.view_transactions_tab:
            # The ViewTransactionsTab has subtabs, so we need to access the transactions widget
            if hasattr(tab_widget, 'transactions_widget'):
                trans_widget = tab_widget.transactions_widget
                if hasattr(trans_widget, 'processor') and trans_widget.processor:
                    trans_widget.processor.reload_state()
                    trans_widget.processor.sync_state_with_filesystem()
                    if hasattr(trans_widget, 'refresh_all'):
                        trans_widget.refresh_all()

    def refresh_all_tabs(self):
        """Refresh all tabs after data changes."""
        pass

    def show_error(self, title, message):
        """Show error dialog."""
        QMessageBox.critical(self, title, message)

    def show_info(self, title, message):
        """Show information dialog."""
        QMessageBox.information(self, title, message)

    def show_warning(self, title, message):
        """Show warning dialog."""
        QMessageBox.warning(self, title, message)

    def confirm_action(self, title, message):
        """Show confirmation dialog and return True if user confirms."""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes


def main():
    """Entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for consistent look across platforms

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
