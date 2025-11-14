"""
Dialog windows for displaying results and detailed information.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from pathlib import Path


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
