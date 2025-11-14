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

from gui.process_month_tab import ProcessMonthTab
from gui.templates_tab import TemplatesTab
from gui.settings_tab import SettingsTab


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
        layout.addWidget(self.tabs)

        # Initialize tabs
        self.settings_tab = SettingsTab(self)
        self.process_tab = ProcessMonthTab(self)
        self.templates_tab = TemplatesTab(self)

        # Add tabs to widget (Settings first)
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.process_tab, "Process Month")
        self.tabs.addTab(self.templates_tab, "Create Templates")

        # Set initial focus on settings tab
        self.tabs.setCurrentIndex(0)

    def on_tab_changed(self, index):
        """Handle tab change events."""
        # Settings tab doesn't need refresh (it manages its own state)
        pass

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
