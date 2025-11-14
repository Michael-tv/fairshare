#!/usr/bin/env python3
"""
FairShare GUI Application Entry Point

Launch the PyQt5 graphical interface for the FairShare household finance splitting system.

Usage:
    python gui_main.py

Requirements:
    - PyQt5 >= 5.15.0
    - All FairShare dependencies (pandas, openpyxl, etc.)

For more information, see docs/README.md
"""

import sys
from pathlib import Path

# Add src directory to path so we can import modules
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
except ImportError:
    print("Error: PyQt5 is not installed.")
    print("Please install it using: pip install PyQt5")
    sys.exit(1)

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"Error importing FairShare GUI modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Main entry point for the FairShare GUI application."""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("FairShare")
    app.setOrganizationName("FairShare")

    # Use Fusion style for consistent look across platforms
    app.setStyle('Fusion')

    # Set application-wide font
    from PyQt5.QtGui import QFont
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    try:
        # Create and show main window
        window = MainWindow()
        window.show()

        # Start event loop
        sys.exit(app.exec_())

    except Exception as e:
        # Show error dialog if something goes wrong
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("FairShare Error")
        error_dialog.setText("An error occurred while starting FairShare:")
        error_dialog.setDetailedText(str(e))
        error_dialog.exec_()
        sys.exit(1)


if __name__ == "__main__":
    main()
