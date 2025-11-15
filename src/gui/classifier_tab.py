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
        self.tabs.addTab(self.create_type_patterns_tab(), "Type Patterns")
        self.tabs.addTab(self.create_learned_rules_tab(), "Learned Rules")
        self.tabs.addTab(self.create_one_time_mappings_tab(), "One-Time Mappings")
        self.tabs.addTab(self.create_split_mappings_tab(), "Split Mappings")
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

    def create_type_patterns_tab(self):
        """Create the type patterns tab (account-specific)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info = QLabel(
            "Type patterns determine whether a transaction is HOUSEHOLD (shared) or INDIVIDUAL (personal).\n"
            "Patterns are account-specific - each account can have its own classification rules.\n"
            "Select an account below to view and edit its patterns."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Account selection
        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("Account:"))
        self.type_patterns_account_combo = QComboBox()
        self.type_patterns_account_combo.currentIndexChanged.connect(self.on_type_patterns_account_changed)
        account_layout.addWidget(self.type_patterns_account_combo)
        account_layout.addStretch()
        layout.addLayout(account_layout)

        # Household patterns
        household_group = QGroupBox("Household/Shared Patterns")
        household_layout = QVBoxLayout()

        self.household_patterns_text = QTextEdit()
        self.household_patterns_text.setPlaceholderText("Enter regex patterns for household expenses, one per line...")
        household_layout.addWidget(self.household_patterns_text)

        household_group.setLayout(household_layout)
        layout.addWidget(household_group)

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

        save_btn = QPushButton("Save Patterns to Config")
        save_btn.clicked.connect(self.save_type_patterns_to_config)
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

    def create_one_time_mappings_tab(self):
        """Create the one-time mappings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info = QLabel(
            "One-time mappings allow you to specify the classification for a specific transaction.\n"
            "These mappings have the highest priority and only apply to exact matches (date + description + amount).\n"
            "Use these for transactions that should be classified differently from similar transactions."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Account selection
        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("Account:"))
        self.one_time_account_combo = QComboBox()
        self.one_time_account_combo.currentIndexChanged.connect(self.on_one_time_account_changed)
        account_layout.addWidget(self.one_time_account_combo)
        account_layout.addStretch()
        layout.addLayout(account_layout)

        # Mappings table
        self.one_time_mappings_table = QTableWidget()
        self.one_time_mappings_table.setColumnCount(5)
        self.one_time_mappings_table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Type", "Actions"])
        self.one_time_mappings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.one_time_mappings_table)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_one_time_mappings)
        button_layout.addWidget(refresh_btn)

        add_btn = QPushButton("Add Mapping...")
        add_btn.clicked.connect(self.add_one_time_mapping_dialog)
        button_layout.addWidget(add_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        return widget

    def create_split_mappings_tab(self):
        """Create the split mappings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info = QLabel(
            "Split mappings allow you to split a single transaction into multiple parts.\n"
            "Example: A R350 grocery store transaction split as R280 HOUSEHOLD + R70 INDIVIDUAL.\n"
            "These mappings have the highest priority and only apply to exact matches (date + description + amount)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Account selection
        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("Account:"))
        self.split_account_combo = QComboBox()
        self.split_account_combo.currentIndexChanged.connect(self.on_split_account_changed)
        account_layout.addWidget(self.split_account_combo)
        account_layout.addStretch()
        layout.addLayout(account_layout)

        # Mappings table
        self.split_mappings_table = QTableWidget()
        self.split_mappings_table.setColumnCount(5)
        self.split_mappings_table.setHorizontalHeaderLabels(["Date", "Description", "Total Amount", "Split Details", "Actions"])
        self.split_mappings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.split_mappings_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.split_mappings_table)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_split_mappings)
        button_layout.addWidget(refresh_btn)

        add_btn = QPushButton("Add Split Mapping...")
        add_btn.clicked.connect(self.add_split_mapping_dialog)
        button_layout.addWidget(add_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

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

        self.result_type_label = QLabel("-")
        self.result_type_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
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

            # Populate account combos
            self.populate_account_combos()

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

            # Create classifier with default account_id for testing purposes
            # Note: For account-specific operations, individual classifiers are created per account
            self.classifier = TransactionClassifier(
                account_id="default",  # Placeholder for general testing
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
            self.populate_account_combos()
            self.load_type_patterns()
            self.refresh_learned_stats()
            self.load_one_time_mappings()
            self.load_split_mappings()

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

    def populate_account_combos(self):
        """Populate account combo boxes with accounts from config."""
        if not self.config:
            return

        # Clear combos
        self.type_patterns_account_combo.clear()
        self.one_time_account_combo.clear()
        self.split_account_combo.clear()

        # Add user accounts
        for user in self.config.users:
            for account in user.accounts:
                account_id = f"{user.id}_{account.name}"
                display_name = f"{user.name} - {account.name}"
                self.type_patterns_account_combo.addItem(display_name, account_id)
                self.one_time_account_combo.addItem(display_name, account_id)
                self.split_account_combo.addItem(display_name, account_id)

        # Add shared accounts
        for account in self.config.shared_accounts:
            account_id = f"shared_{account.name}"
            display_name = f"Shared - {account.name}"
            self.type_patterns_account_combo.addItem(display_name, account_id)
            self.one_time_account_combo.addItem(display_name, account_id)
            self.split_account_combo.addItem(display_name, account_id)

    def on_type_patterns_account_changed(self):
        """Handle account selection change in type patterns tab."""
        self.load_type_patterns()

    def on_one_time_account_changed(self):
        """Handle account selection change in one-time mappings tab."""
        self.load_one_time_mappings()

    def on_split_account_changed(self):
        """Handle account selection change in split mappings tab."""
        self.load_split_mappings()

    def load_type_patterns(self):
        """Load type patterns for the selected account from config."""
        if not self.config:
            return

        account_id = self.type_patterns_account_combo.currentData()
        if not account_id:
            self.household_patterns_text.clear()
            self.individual_patterns_text.clear()
            return

        # Find the account in config
        account_config = self._get_account_config(account_id)
        if not account_config:
            self.household_patterns_text.clear()
            self.individual_patterns_text.clear()
            return

        # Load patterns
        self.household_patterns_text.setPlainText(
            '\n'.join(account_config.household_patterns or [])
        )
        self.individual_patterns_text.setPlainText(
            '\n'.join(account_config.individual_patterns or [])
        )

    def _get_account_config(self, account_id: str):
        """Get account config by ID."""
        if not self.config:
            return None

        # Check shared accounts
        if account_id.startswith("shared_"):
            account_name = account_id.replace("shared_", "")
            for account in self.config.shared_accounts:
                if account.name == account_name:
                    return account
        else:
            # User account
            parts = account_id.split("_", 1)
            if len(parts) == 2:
                user_id, account_name = parts
                for user in self.config.users:
                    if user.id == user_id:
                        for account in user.accounts:
                            if account.name == account_name:
                                return account
        return None

    def save_type_patterns_to_config(self):
        """Save type patterns to config file."""
        account_id = self.type_patterns_account_combo.currentData()
        if not account_id:
            QMessageBox.warning(
                self,
                "No Account Selected",
                "Please select an account first."
            )
            return

        # Get patterns from text areas
        household_text = self.household_patterns_text.toPlainText()
        household_patterns = [line.strip() for line in household_text.split('\n') if line.strip()]

        individual_text = self.individual_patterns_text.toPlainText()
        individual_patterns = [line.strip() for line in individual_text.split('\n') if line.strip()]

        try:
            # Load current config
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Update the account's patterns
            updated = False
            if account_id.startswith("shared_"):
                account_name = account_id.replace("shared_", "")
                for account in config_data.get("shared_accounts", []):
                    if account["name"] == account_name:
                        account["household_patterns"] = household_patterns
                        account["individual_patterns"] = individual_patterns
                        updated = True
                        break
            else:
                parts = account_id.split("_", 1)
                if len(parts) == 2:
                    user_id, account_name = parts
                    for user in config_data.get("users", []):
                        if user.get("id") == user_id:
                            for account in user.get("accounts", []):
                                if account["name"] == account_name:
                                    account["household_patterns"] = household_patterns
                                    account["individual_patterns"] = individual_patterns
                                    updated = True
                                    break

            if not updated:
                QMessageBox.warning(
                    self,
                    "Account Not Found",
                    f"Could not find account '{account_id}' in config."
                )
                return

            # Save config
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            # Reload config
            self.config = ConfigManager.load()

            QMessageBox.information(
                self,
                "Patterns Saved",
                f"Type patterns saved to config:\n"
                f"Household patterns: {len(household_patterns)}\n"
                f"Individual patterns: {len(individual_patterns)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save patterns: {e}"
            )

    def refresh_learned_stats(self):
        """Refresh learned rules statistics."""
        if not self.learned_classifier:
            self.total_rules_label.setText("0")
            self.rules_file_label.setText("-")
            self.type_stats_text.clear()
            return

        # Get statistics
        stats = self.learned_classifier.get_statistics()

        # Update labels
        self.total_rules_label.setText(str(stats['total_rules']))
        self.rules_file_label.setText(str(self.learned_classifier.rules_path))

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

    def load_one_time_mappings(self):
        """Load one-time mappings for the selected account."""
        self.one_time_mappings_table.setRowCount(0)

        account_id = self.one_time_account_combo.currentData()
        if not account_id:
            return

        # Load mappings from file
        mappings_path = Path(self.config.working_dir) / "one_time_transaction_mappings.json"
        if not mappings_path.exists():
            return

        try:
            with open(mappings_path, 'r', encoding='utf-8') as f:
                all_mappings = json.load(f)

            account_mappings = all_mappings.get(account_id, {})

            for txn_key, exp_type in account_mappings.items():
                # Parse the key (date|description|amount)
                parts = txn_key.split('|', 2)
                if len(parts) != 3:
                    continue

                date, description, amount = parts

                row = self.one_time_mappings_table.rowCount()
                self.one_time_mappings_table.insertRow(row)

                # Date
                self.one_time_mappings_table.setItem(row, 0, QTableWidgetItem(date))
                # Description
                self.one_time_mappings_table.setItem(row, 1, QTableWidgetItem(description))
                # Amount
                self.one_time_mappings_table.setItem(row, 2, QTableWidgetItem(amount))
                # Type
                self.one_time_mappings_table.setItem(row, 3, QTableWidgetItem(exp_type))

                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(
                    lambda checked, d=date, desc=description, a=amount: self.delete_one_time_mapping(d, desc, a)
                )
                self.one_time_mappings_table.setCellWidget(row, 4, delete_btn)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load one-time mappings: {e}"
            )

    def add_one_time_mapping_dialog(self):
        """Show dialog to add a new one-time mapping."""
        account_id = self.one_time_account_combo.currentData()
        if not account_id:
            QMessageBox.warning(
                self,
                "No Account Selected",
                "Please select an account first."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add One-Time Mapping")
        layout = QFormLayout(dialog)

        # Input fields
        date_edit = QLineEdit()
        date_edit.setPlaceholderText("YYYY-MM-DD")
        layout.addRow("Date:", date_edit)

        description_edit = QLineEdit()
        description_edit.setPlaceholderText("Transaction description")
        layout.addRow("Description:", description_edit)

        amount_edit = QLineEdit()
        amount_edit.setPlaceholderText("123.45")
        layout.addRow("Amount:", amount_edit)

        type_combo = QComboBox()
        type_combo.addItem("HOUSEHOLD", "HOUSEHOLD")
        type_combo.addItem("INDIVIDUAL", "INDIVIDUAL")
        layout.addRow("Type:", type_combo)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        if dialog.exec_() == QDialog.Accepted:
            # Add the mapping
            date = date_edit.text().strip()
            description = description_edit.text().strip()
            amount = amount_edit.text().strip()
            exp_type = type_combo.currentData()

            if not date or not description or not amount:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "All fields are required."
                )
                return

            try:
                from decimal import Decimal
                amount_decimal = Decimal(amount)

                # Create transaction key
                txn_key = f"{date}|{description.lower().strip()}|{amount_decimal}"

                # Load mappings
                mappings_path = Path(self.config.working_dir) / "one_time_transaction_mappings.json"
                all_mappings = {}
                if mappings_path.exists():
                    with open(mappings_path, 'r', encoding='utf-8') as f:
                        all_mappings = json.load(f)

                # Update
                if account_id not in all_mappings:
                    all_mappings[account_id] = {}
                all_mappings[account_id][txn_key] = exp_type

                # Save
                mappings_path.parent.mkdir(parents=True, exist_ok=True)
                with open(mappings_path, 'w', encoding='utf-8') as f:
                    json.dump(all_mappings, indent=2, fp=f)

                # Refresh
                self.load_one_time_mappings()

                QMessageBox.information(
                    self,
                    "Mapping Added",
                    f"One-time mapping added successfully."
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Add Error",
                    f"Failed to add mapping: {e}"
                )

    def delete_one_time_mapping(self, date: str, description: str, amount: str):
        """Delete a one-time mapping."""
        account_id = self.one_time_account_combo.currentData()
        if not account_id:
            return

        reply = QMessageBox.question(
            self,
            "Delete Mapping",
            f"Are you sure you want to delete this mapping?\n\n"
            f"Date: {date}\n"
            f"Description: {description}\n"
            f"Amount: {amount}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from decimal import Decimal
                amount_decimal = Decimal(amount)
                txn_key = f"{date}|{description.lower().strip()}|{amount_decimal}"

                # Load mappings
                mappings_path = Path(self.config.working_dir) / "one_time_transaction_mappings.json"
                if not mappings_path.exists():
                    return

                with open(mappings_path, 'r', encoding='utf-8') as f:
                    all_mappings = json.load(f)

                # Delete
                if account_id in all_mappings and txn_key in all_mappings[account_id]:
                    del all_mappings[account_id][txn_key]

                    # Save
                    with open(mappings_path, 'w', encoding='utf-8') as f:
                        json.dump(all_mappings, indent=2, fp=f)

                    # Refresh
                    self.load_one_time_mappings()

                    QMessageBox.information(
                        self,
                        "Mapping Deleted",
                        "One-time mapping deleted successfully."
                    )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Error",
                    f"Failed to delete mapping: {e}"
                )

    def load_split_mappings(self):
        """Load split mappings for the selected account."""
        self.split_mappings_table.setRowCount(0)

        account_id = self.split_account_combo.currentData()
        if not account_id:
            return

        # Load mappings from file
        mappings_path = Path(self.config.working_dir) / "split_transaction_mappings.json"
        if not mappings_path.exists():
            return

        try:
            import json
            with open(mappings_path, 'r', encoding='utf-8') as f:
                all_mappings = json.load(f)

            account_mappings = all_mappings.get(account_id, {})

            for txn_key, split_parts in account_mappings.items():
                # Parse the key (date|description|amount)
                parts = txn_key.split('|', 2)
                if len(parts) != 3:
                    continue

                date, description, amount = parts

                # Format split details
                split_details = []
                for part in split_parts:
                    split_details.append(f"{part['type']}: R{part['amount']}" +
                                       (f" ({part['note']})" if part.get('note') else ""))
                split_text = "\n".join(split_details)

                row = self.split_mappings_table.rowCount()
                self.split_mappings_table.insertRow(row)

                # Date
                self.split_mappings_table.setItem(row, 0, QTableWidgetItem(date))
                # Description
                self.split_mappings_table.setItem(row, 1, QTableWidgetItem(description))
                # Total Amount
                self.split_mappings_table.setItem(row, 2, QTableWidgetItem(f"R{amount}"))
                # Split Details
                self.split_mappings_table.setItem(row, 3, QTableWidgetItem(split_text))

                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(
                    lambda checked, d=date, desc=description, a=amount: self.delete_split_mapping(d, desc, a)
                )
                self.split_mappings_table.setCellWidget(row, 4, delete_btn)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load split mappings: {e}"
            )

    def add_split_mapping_dialog(self):
        """Show dialog to add a new split mapping."""
        account_id = self.split_account_combo.currentData()
        if not account_id:
            QMessageBox.warning(
                self,
                "No Account Selected",
                "Please select an account first."
            )
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Split Mapping")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)

        # Transaction details
        trans_group = QGroupBox("Transaction Details")
        trans_layout = QFormLayout()

        date_edit = QLineEdit()
        date_edit.setPlaceholderText("YYYY-MM-DD")
        trans_layout.addRow("Date:", date_edit)

        description_edit = QLineEdit()
        description_edit.setPlaceholderText("Transaction description")
        trans_layout.addRow("Description:", description_edit)

        amount_edit = QLineEdit()
        amount_edit.setPlaceholderText("350.00")
        trans_layout.addRow("Total Amount:", amount_edit)

        trans_group.setLayout(trans_layout)
        layout.addWidget(trans_group)

        # Split parts
        split_group = QGroupBox("Split Parts (must sum to total amount)")
        split_layout = QVBoxLayout()

        # Create a container for split part widgets
        split_parts_container = QWidget()
        split_parts_layout = QVBoxLayout(split_parts_container)
        split_parts = []  # List to store split part widgets

        def add_split_part():
            """Add a new split part row."""
            part_widget = QWidget()
            part_layout = QHBoxLayout(part_widget)

            type_combo = QComboBox()
            type_combo.addItem("HOUSEHOLD", "HOUSEHOLD")
            type_combo.addItem("INDIVIDUAL", "INDIVIDUAL")
            part_layout.addWidget(QLabel("Type:"))
            part_layout.addWidget(type_combo)

            part_layout.addWidget(QLabel("Amount:"))
            amount_input = QLineEdit()
            amount_input.setPlaceholderText("0.00")
            amount_input.setMaximumWidth(100)
            part_layout.addWidget(amount_input)

            part_layout.addWidget(QLabel("Note:"))
            note_input = QLineEdit()
            note_input.setPlaceholderText("Optional note")
            part_layout.addWidget(note_input)

            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda: remove_split_part(part_widget))
            part_layout.addWidget(remove_btn)

            split_parts_layout.addWidget(part_widget)
            split_parts.append({
                'widget': part_widget,
                'type_combo': type_combo,
                'amount': amount_input,
                'note': note_input
            })

        def remove_split_part(widget):
            """Remove a split part row."""
            for i, part in enumerate(split_parts):
                if part['widget'] == widget:
                    split_parts_layout.removeWidget(widget)
                    widget.deleteLater()
                    split_parts.pop(i)
                    break

        # Add initial split parts
        add_split_part()
        add_split_part()

        split_layout.addWidget(split_parts_container)

        add_part_btn = QPushButton("Add Another Part")
        add_part_btn.clicked.connect(add_split_part)
        split_layout.addWidget(add_part_btn)

        split_group.setLayout(split_layout)
        layout.addWidget(split_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            # Validate and save the mapping
            date = date_edit.text().strip()
            description = description_edit.text().strip()
            total_amount_str = amount_edit.text().strip()

            if not date or not description or not total_amount_str:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Date, description, and total amount are required."
                )
                return

            try:
                from decimal import Decimal
                from src.transaction_classifier import SplitPart

                total_amount = Decimal(total_amount_str)

                # Build split parts
                split_parts_data = []
                for part in split_parts:
                    amount_str = part['amount'].text().strip()
                    if not amount_str:
                        continue

                    split_parts_data.append(SplitPart(
                        expense_type=part['type_combo'].currentData(),
                        amount=Decimal(amount_str),
                        note=part['note'].text().strip()
                    ))

                if len(split_parts_data) < 2:
                    QMessageBox.warning(
                        self,
                        "Invalid Split",
                        "At least 2 split parts are required."
                    )
                    return

                # Validate sum
                parts_sum = sum(p.amount for p in split_parts_data)
                if parts_sum != total_amount:
                    QMessageBox.warning(
                        self,
                        "Invalid Split",
                        f"Split parts sum (R{parts_sum}) does not match total amount (R{total_amount})."
                    )
                    return

                # Save to JSON file
                mappings_path = Path(self.config.working_dir) / "split_transaction_mappings.json"

                # Load existing mappings
                all_mappings = {}
                if mappings_path.exists():
                    import json
                    with open(mappings_path, 'r', encoding='utf-8') as f:
                        all_mappings = json.load(f)

                # Create transaction key
                txn_key = f"{date}|{description.lower().strip()}|{total_amount}"

                # Update
                if account_id not in all_mappings:
                    all_mappings[account_id] = {}
                all_mappings[account_id][txn_key] = [part.to_dict() for part in split_parts_data]

                # Save
                mappings_path.parent.mkdir(parents=True, exist_ok=True)
                import json
                with open(mappings_path, 'w', encoding='utf-8') as f:
                    json.dump(all_mappings, indent=2, fp=f)

                # Refresh
                self.load_split_mappings()

                QMessageBox.information(
                    self,
                    "Mapping Added",
                    f"Split mapping added successfully:\n"
                    f"Transaction: R{total_amount}\n"
                    f"Parts: {len(split_parts_data)}"
                )

            except ValueError as e:
                QMessageBox.critical(
                    self,
                    "Invalid Input",
                    f"Invalid amount value: {e}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Add Error",
                    f"Failed to add split mapping: {e}"
                )

    def delete_split_mapping(self, date: str, description: str, amount: str):
        """Delete a split mapping."""
        account_id = self.split_account_combo.currentData()
        if not account_id:
            return

        reply = QMessageBox.question(
            self,
            "Delete Split Mapping",
            f"Are you sure you want to delete this split mapping?\n\n"
            f"Date: {date}\n"
            f"Description: {description}\n"
            f"Amount: {amount}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from decimal import Decimal
                import json

                # Remove 'R' prefix if present
                amount_str = amount.replace('R', '').strip()
                amount_decimal = Decimal(amount_str)
                txn_key = f"{date}|{description.lower().strip()}|{amount_decimal}"

                # Load mappings
                mappings_path = Path(self.config.working_dir) / "split_transaction_mappings.json"
                if not mappings_path.exists():
                    return

                with open(mappings_path, 'r', encoding='utf-8') as f:
                    all_mappings = json.load(f)

                # Delete
                if account_id in all_mappings and txn_key in all_mappings[account_id]:
                    del all_mappings[account_id][txn_key]

                    # Save
                    with open(mappings_path, 'w', encoding='utf-8') as f:
                        json.dump(all_mappings, indent=2, fp=f)

                    # Refresh
                    self.load_split_mappings()

                    QMessageBox.information(
                        self,
                        "Mapping Deleted",
                        "Split mapping deleted successfully."
                    )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Error",
                    f"Failed to delete split mapping: {e}"
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

            # Classify (returns only type now, no category)
            exp_type = self.classifier.classify_transaction(
                description,
                Decimal("0"),  # Amount doesn't affect most classifications
                is_shared
            )

            # Determine source
            source = "Keyword patterns"
            confidence = 0.7

            # Check one-time mappings
            # (We'd need date for this, so skip for test)

            # Check learned rules
            if self.classifier.learned_classifier:
                learned_result = self.classifier.learned_classifier.classify(description)
                if learned_result:
                    source = "Learned rules (from user corrections)"
                    confidence = 0.95

            # Update results
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
