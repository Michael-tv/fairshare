"""
Transaction Classifier Tab - Manage classification rules and settings.
"""

import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QFormLayout, QSpinBox, QCheckBox, QTextEdit,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from src.transaction_classifier import TransactionClassifier
from src.learned_classifier import LearnedClassifier
from src.config_manager import ConfigManager
from src.models import ExpenseType, DEFAULT_EXPENSE_CATEGORIES


class CategoryPatternDialog(QDialog):
    """Dialog for editing category patterns."""

    def __init__(self, parent=None, category=None, patterns=None):
        super().__init__(parent)
        self.category = category
        self.patterns = patterns or []
        self.setWindowTitle(f"Edit Patterns - {category}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            f"Regex patterns for category: {self.category}\n"
            "Each pattern should be a valid regular expression."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Pattern list
        self.pattern_list = QTextEdit()
        self.pattern_list.setPlainText('\n'.join(self.patterns))
        self.pattern_list.setPlaceholderText("Enter regex patterns, one per line...")
        layout.addWidget(self.pattern_list)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_patterns(self):
        """Get the edited patterns."""
        text = self.pattern_list.toPlainText()
        return [line.strip() for line in text.split('\n') if line.strip()]


class TransactionClassifierTab(QWidget):
    """Tab for managing transaction classification settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.config = None
        self.classifier = None
        self.learned_classifier = None

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Create tab widget for different sections
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Add tabs
        self.tabs.addTab(self.create_settings_tab(), "Settings")
        self.tabs.addTab(self.create_patterns_tab(), "Category Patterns")
        self.tabs.addTab(self.create_type_patterns_tab(), "Type Patterns")
        self.tabs.addTab(self.create_learned_rules_tab(), "Learned Rules")
        self.tabs.addTab(self.create_test_tab(), "Test Classification")

    def create_settings_tab(self):
        """Create the settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Learned Classifier Settings
        learned_group = QGroupBox("Learned Classifier Settings")
        learned_layout = QFormLayout()

        # Enable learned classifier
        self.enable_learned_checkbox = QCheckBox("Enable learned classification")
        self.enable_learned_checkbox.setChecked(True)
        self.enable_learned_checkbox.stateChanged.connect(self.on_settings_changed)
        learned_layout.addRow("Enabled:", self.enable_learned_checkbox)

        # Similarity threshold
        threshold_layout = QHBoxLayout()
        self.similarity_threshold_spin = QSpinBox()
        self.similarity_threshold_spin.setRange(0, 100)
        self.similarity_threshold_spin.setValue(85)
        self.similarity_threshold_spin.setSuffix("%")
        self.similarity_threshold_spin.valueChanged.connect(self.on_settings_changed)
        threshold_layout.addWidget(self.similarity_threshold_spin)
        threshold_layout.addWidget(QLabel("(Higher = more strict matching)"))
        threshold_layout.addStretch()
        learned_layout.addRow("Similarity Threshold:", threshold_layout)

        # Learned rules file path
        rules_path_layout = QHBoxLayout()
        self.rules_path_edit = QLineEdit()
        self.rules_path_edit.setPlaceholderText("data/learned_classification_rules.json")
        self.rules_path_edit.textChanged.connect(self.on_settings_changed)
        rules_path_layout.addWidget(self.rules_path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_rules_file)
        rules_path_layout.addWidget(browse_btn)
        learned_layout.addRow("Rules File:", rules_path_layout)

        learned_group.setLayout(learned_layout)
        layout.addWidget(learned_group)

        # Classification Settings
        classif_group = QGroupBox("Classification Settings")
        classif_layout = QFormLayout()

        # Default shared type
        self.default_shared_combo = QComboBox()
        self.default_shared_combo.addItem("SHARED - Household expenses", "SHARED")
        self.default_shared_combo.addItem("INDIVIDUAL - Personal expenses", "INDIVIDUAL")
        self.default_shared_combo.currentIndexChanged.connect(self.on_settings_changed)
        classif_layout.addRow("Default Type for Shared Accounts:", self.default_shared_combo)

        classif_group.setLayout(classif_layout)
        layout.addWidget(classif_group)

        # Buttons
        button_layout = QHBoxLayout()

        reload_btn = QPushButton("Reload Classifier")
        reload_btn.clicked.connect(self.reload_classifier)
        button_layout.addWidget(reload_btn)

        save_btn = QPushButton("Save Settings to Config")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        return widget

    def create_patterns_tab(self):
        """Create the category patterns tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info = QLabel(
            "Category patterns define which transactions match which expense categories.\n"
            "These are regex patterns matched against transaction descriptions."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Pattern table
        self.category_patterns_table = QTableWidget()
        self.category_patterns_table.setColumnCount(3)
        self.category_patterns_table.setHorizontalHeaderLabels(["Category", "Pattern Count", "Actions"])
        self.category_patterns_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.category_patterns_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.category_patterns_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.category_patterns_table)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_category_patterns)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        return widget

    def create_type_patterns_tab(self):
        """Create the type patterns tab (shared vs individual)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info = QLabel(
            "Type patterns determine whether a transaction is HOUSEHOLD (shared) or INDIVIDUAL (personal).\n"
            "These patterns are applied when the classifier needs to determine the expense type."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Shared patterns
        shared_group = QGroupBox("Household/Shared Patterns")
        shared_layout = QVBoxLayout()

        self.shared_patterns_text = QTextEdit()
        self.shared_patterns_text.setPlaceholderText("Enter regex patterns for household expenses, one per line...")
        shared_layout.addWidget(self.shared_patterns_text)

        shared_group.setLayout(shared_layout)
        layout.addWidget(shared_group)

        # Individual patterns
        individual_group = QGroupBox("Individual/Personal Patterns")
        individual_layout = QVBoxLayout()

        self.individual_patterns_text = QTextEdit()
        self.individual_patterns_text.setPlaceholderText("Enter regex patterns for personal expenses, one per line...")
        individual_layout.addWidget(self.individual_patterns_text)

        individual_group.setLayout(individual_layout)
        layout.addWidget(individual_group)

        # Buttons
        button_layout = QHBoxLayout()

        load_btn = QPushButton("Load Current Patterns")
        load_btn.clicked.connect(self.load_type_patterns)
        button_layout.addWidget(load_btn)

        save_btn = QPushButton("Save Patterns")
        save_btn.clicked.connect(self.save_type_patterns)
        button_layout.addWidget(save_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        return widget

    def create_learned_rules_tab(self):
        """Create the learned rules management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout()

        self.total_rules_label = QLabel("0")
        stats_layout.addRow("Total Rules:", self.total_rules_label)

        self.rules_file_label = QLabel("-")
        stats_layout.addRow("Rules File:", self.rules_file_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Category distribution
        self.category_stats_text = QTextEdit()
        self.category_stats_text.setReadOnly(True)
        self.category_stats_text.setMaximumHeight(150)
        layout.addWidget(QLabel("Category Distribution:"))
        layout.addWidget(self.category_stats_text)

        # Type distribution
        self.type_stats_text = QTextEdit()
        self.type_stats_text.setReadOnly(True)
        self.type_stats_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Type Distribution:"))
        layout.addWidget(self.type_stats_text)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_learned_stats)
        button_layout.addWidget(refresh_btn)

        export_btn = QPushButton("Export Rules to Excel")
        export_btn.clicked.connect(self.export_learned_rules)
        button_layout.addWidget(export_btn)

        clear_btn = QPushButton("Clear All Rules")
        clear_btn.clicked.connect(self.clear_learned_rules)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Apply rules section
        apply_group = QGroupBox("Apply Rules to Transactions")
        apply_layout = QVBoxLayout()

        apply_info = QLabel(
            "Apply learned rules to re-classify existing transaction files.\n"
            "This will update auto_category and auto_type columns."
        )
        apply_info.setWordWrap(True)
        apply_layout.addWidget(apply_info)

        apply_btn_layout = QHBoxLayout()
        apply_file_btn = QPushButton("Apply to Single File...")
        apply_file_btn.clicked.connect(self.apply_rules_to_file)
        apply_btn_layout.addWidget(apply_file_btn)

        apply_all_btn = QPushButton("Apply to All Files in Folder...")
        apply_all_btn.clicked.connect(self.apply_rules_to_folder)
        apply_btn_layout.addWidget(apply_all_btn)

        apply_btn_layout.addStretch()
        apply_layout.addLayout(apply_btn_layout)

        apply_group.setLayout(apply_layout)
        layout.addWidget(apply_group)

        layout.addStretch()
        return widget

    def create_test_tab(self):
        """Create the test classification tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info = QLabel(
            "Test how the classifier would categorize a transaction description.\n"
            "This helps you verify your patterns and learned rules."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Input section
        input_group = QGroupBox("Test Input")
        input_layout = QFormLayout()

        self.test_description_edit = QLineEdit()
        self.test_description_edit.setPlaceholderText("e.g., WOOLWORTHS RONDEBOSCH")
        input_layout.addRow("Description:", self.test_description_edit)

        self.test_is_shared_checkbox = QCheckBox("From shared account")
        input_layout.addRow("Account Type:", self.test_is_shared_checkbox)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Test button
        test_btn = QPushButton("Test Classification")
        test_btn.clicked.connect(self.test_classification)
        layout.addWidget(test_btn)

        # Results section
        results_group = QGroupBox("Classification Results")
        results_layout = QFormLayout()

        self.result_category_label = QLabel("-")
        self.result_category_label.setStyleSheet("font-weight: bold;")
        results_layout.addRow("Category:", self.result_category_label)

        self.result_type_label = QLabel("-")
        self.result_type_label.setStyleSheet("font-weight: bold;")
        results_layout.addRow("Type:", self.result_type_label)

        self.result_source_label = QLabel("-")
        results_layout.addRow("Source:", self.result_source_label)

        self.result_confidence_label = QLabel("-")
        results_layout.addRow("Confidence:", self.result_confidence_label)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        layout.addStretch()
        return widget

    def load_config(self):
        """Load configuration."""
        try:
            self.config = ConfigManager.load()

            # Set default values from config
            if self.config.classification:
                default_type = self.config.classification.default_shared_type
                index = self.default_shared_combo.findData(default_type)
                if index >= 0:
                    self.default_shared_combo.setCurrentIndex(index)

            # Set default rules path
            rules_path = self.config.working_dir / "learned_classification_rules.json"
            self.rules_path_edit.setText(str(rules_path))

            # Initialize classifier
            self.reload_classifier()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Config Load Error",
                f"Could not load configuration: {e}\n\n"
                "Using default settings."
            )

    def reload_classifier(self):
        """Reload the classifier with current settings."""
        try:
            # Get settings
            use_learned = self.enable_learned_checkbox.isChecked()
            rules_path = Path(self.rules_path_edit.text()) if self.rules_path_edit.text() else None
            similarity_threshold = self.similarity_threshold_spin.value()

            # Create classifier
            self.classifier = TransactionClassifier(
                learned_rules_path=rules_path,
                use_learned=use_learned
            )

            # Create learned classifier separately for management operations
            if rules_path:
                self.learned_classifier = LearnedClassifier(
                    rules_path,
                    similarity_threshold=similarity_threshold
                )

            # Refresh displays
            self.load_category_patterns()
            self.load_type_patterns()
            self.refresh_learned_stats()

            QMessageBox.information(
                self,
                "Classifier Reloaded",
                "Transaction classifier has been reloaded with current settings."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Reload Error",
                f"Failed to reload classifier: {e}"
            )

    def load_category_patterns(self):
        """Load category patterns into the table."""
        if not self.classifier:
            return

        self.category_patterns_table.setRowCount(0)

        for category, patterns in sorted(self.classifier.category_patterns.items()):
            row = self.category_patterns_table.rowCount()
            self.category_patterns_table.insertRow(row)

            # Category name
            category_item = QTableWidgetItem(category)
            self.category_patterns_table.setItem(row, 0, category_item)

            # Pattern count
            count_item = QTableWidgetItem(str(len(patterns)))
            self.category_patterns_table.setItem(row, 1, count_item)

            # Edit button
            edit_btn = QPushButton("Edit Patterns")
            edit_btn.clicked.connect(
                lambda checked, c=category, p=patterns: self.edit_category_patterns(c, p)
            )
            self.category_patterns_table.setCellWidget(row, 2, edit_btn)

    def edit_category_patterns(self, category, patterns):
        """Open dialog to edit category patterns."""
        dialog = CategoryPatternDialog(self, category, patterns)
        if dialog.exec_() == QDialog.Accepted:
            new_patterns = dialog.get_patterns()
            if self.classifier:
                self.classifier.category_patterns[category] = new_patterns
                self.load_category_patterns()
                QMessageBox.information(
                    self,
                    "Patterns Updated",
                    f"Updated patterns for category: {category}\n"
                    f"New pattern count: {len(new_patterns)}"
                )

    def load_type_patterns(self):
        """Load type patterns into text areas."""
        if not self.classifier:
            return

        # Load shared patterns
        self.shared_patterns_text.setPlainText(
            '\n'.join(self.classifier.shared_patterns)
        )

        # Load individual patterns
        self.individual_patterns_text.setPlainText(
            '\n'.join(self.classifier.individual_patterns)
        )

    def save_type_patterns(self):
        """Save type patterns from text areas."""
        if not self.classifier:
            QMessageBox.warning(
                self,
                "No Classifier",
                "Please reload the classifier first."
            )
            return

        # Get patterns from text areas
        shared_text = self.shared_patterns_text.toPlainText()
        shared_patterns = [line.strip() for line in shared_text.split('\n') if line.strip()]

        individual_text = self.individual_patterns_text.toPlainText()
        individual_patterns = [line.strip() for line in individual_text.split('\n') if line.strip()]

        # Update classifier
        self.classifier.shared_patterns = shared_patterns
        self.classifier.individual_patterns = individual_patterns

        QMessageBox.information(
            self,
            "Patterns Saved",
            f"Type patterns updated:\n"
            f"Shared patterns: {len(shared_patterns)}\n"
            f"Individual patterns: {len(individual_patterns)}"
        )

    def refresh_learned_stats(self):
        """Refresh learned rules statistics."""
        if not self.learned_classifier:
            self.total_rules_label.setText("0")
            self.rules_file_label.setText("-")
            self.category_stats_text.clear()
            self.type_stats_text.clear()
            return

        # Get statistics
        stats = self.learned_classifier.get_statistics()

        # Update labels
        self.total_rules_label.setText(str(stats['total_rules']))
        self.rules_file_label.setText(str(self.learned_classifier.rules_path))

        # Category distribution
        if stats['categories']:
            cat_text = []
            for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
                cat_text.append(f"{category}: {count}")
            self.category_stats_text.setPlainText('\n'.join(cat_text))
        else:
            self.category_stats_text.setPlainText("No rules learned yet")

        # Type distribution
        if stats['types']:
            type_text = []
            for typ, count in sorted(stats['types'].items()):
                type_text.append(f"{typ}: {count}")
            self.type_stats_text.setPlainText('\n'.join(type_text))
        else:
            self.type_stats_text.setPlainText("No rules learned yet")

    def export_learned_rules(self):
        """Export learned rules to Excel."""
        if not self.learned_classifier:
            QMessageBox.warning(
                self,
                "No Learned Classifier",
                "Please configure and reload the classifier first."
            )
            return

        # Ask for output file
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Export Learned Rules",
            "learned_rules_export.xlsx",
            "Excel Files (*.xlsx)"
        )

        if output_file:
            try:
                self.learned_classifier.export_rules(Path(output_file))
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Learned rules exported to:\n{output_file}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export rules: {e}"
                )

    def clear_learned_rules(self):
        """Clear all learned rules."""
        if not self.learned_classifier:
            return

        reply = QMessageBox.question(
            self,
            "Clear All Rules",
            "Are you sure you want to clear ALL learned rules?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear rules
                self.learned_classifier.rules = {}
                self.learned_classifier._save_rules()

                # Refresh stats
                self.refresh_learned_stats()

                QMessageBox.information(
                    self,
                    "Rules Cleared",
                    "All learned rules have been cleared."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Clear Error",
                    f"Failed to clear rules: {e}"
                )

    def apply_rules_to_file(self):
        """Apply learned rules to a single transaction file."""
        if not self.learned_classifier:
            QMessageBox.warning(
                self,
                "No Learned Classifier",
                "Please configure and reload the classifier first."
            )
            return

        # Ask for transaction file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Transaction File",
            "",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            try:
                stats = self.learned_classifier.apply_to_transactions(
                    Path(file_path),
                    verbose=True
                )

                QMessageBox.information(
                    self,
                    "Rules Applied",
                    f"Applied learned rules to: {Path(file_path).name}\n\n"
                    f"Reclassified: {stats['reclassified']}\n"
                    f"Unchanged: {stats['unchanged']}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Apply Error",
                    f"Failed to apply rules: {e}"
                )

    def apply_rules_to_folder(self):
        """Apply learned rules to all transaction files in a folder."""
        if not self.learned_classifier:
            QMessageBox.warning(
                self,
                "No Learned Classifier",
                "Please configure and reload the classifier first."
            )
            return

        # Ask for folder
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Transaction Files"
        )

        if folder_path:
            try:
                # Find all Excel files
                folder = Path(folder_path)
                excel_files = list(folder.glob("**/*classified.xlsx"))

                if not excel_files:
                    QMessageBox.warning(
                        self,
                        "No Files Found",
                        f"No classified transaction files found in:\n{folder_path}"
                    )
                    return

                # Apply rules
                stats = self.learned_classifier.apply_to_all_files(
                    excel_files,
                    verbose=True
                )

                QMessageBox.information(
                    self,
                    "Rules Applied",
                    f"Applied learned rules to {len(excel_files)} file(s)\n\n"
                    f"Total reclassified: {stats['reclassified']}\n"
                    f"Total unchanged: {stats['unchanged']}\n"
                    f"Files updated: {stats['files_updated']}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Apply Error",
                    f"Failed to apply rules: {e}"
                )

    def test_classification(self):
        """Test classification on the input description."""
        if not self.classifier:
            QMessageBox.warning(
                self,
                "No Classifier",
                "Please reload the classifier first."
            )
            return

        description = self.test_description_edit.text().strip()
        if not description:
            QMessageBox.warning(
                self,
                "No Input",
                "Please enter a transaction description to test."
            )
            return

        is_shared = self.test_is_shared_checkbox.isChecked()

        try:
            from decimal import Decimal

            # Classify
            category, exp_type = self.classifier.classify_transaction(
                description,
                Decimal("0"),  # Amount doesn't affect most classifications
                is_shared
            )

            # Get confidence
            confidence = self.classifier.get_classification_confidence(description, category)

            # Determine source
            source = "Keyword patterns"
            if self.classifier.learned_classifier:
                learned_result = self.classifier.learned_classifier.classify(description)
                if learned_result:
                    source = "Learned rules (from user corrections)"

            # Update results
            self.result_category_label.setText(category)
            self.result_type_label.setText(exp_type)
            self.result_source_label.setText(source)
            self.result_confidence_label.setText(f"{confidence:.0%}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Classification Error",
                f"Failed to classify transaction: {e}"
            )

    def browse_rules_file(self):
        """Browse for learned rules file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Learned Rules File",
            self.rules_path_edit.text() or "learned_classification_rules.json",
            "JSON Files (*.json)"
        )

        if file_path:
            self.rules_path_edit.setText(file_path)

    def save_settings(self):
        """Save settings to config file."""
        try:
            # Load current config
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Update classification settings
            if "classification" not in config_data:
                config_data["classification"] = {}

            config_data["classification"]["enabled"] = self.enable_learned_checkbox.isChecked()
            config_data["classification"]["default_shared_type"] = self.default_shared_combo.currentData()

            # Save config
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            QMessageBox.information(
                self,
                "Settings Saved",
                "Classification settings have been saved to config.json"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save settings: {e}"
            )

    def on_settings_changed(self):
        """Handle settings changes."""
        # Just mark that settings have changed
        # User needs to click reload to apply
        pass
