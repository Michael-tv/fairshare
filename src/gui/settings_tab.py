"""
Settings tab - Configure users, accounts, and file paths.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QSplitter, QFormLayout, QComboBox, QDialog,
    QDialogButtonBox, QTextEdit, QScrollArea, QTabWidget, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from checkpoint_manager import CheckpointManager
from config_manager import AccountType


class AccountDialog(QDialog):
    """Dialog for adding/editing account information."""

    def __init__(self, parent=None, account_data=None, users=None, current_owner=None):
        super().__init__(parent)
        self.account_data = account_data or {}
        self.users = users or []
        self.current_owner = current_owner  # "Shared" or user name
        self.setWindowTitle("Edit Account" if account_data else "Add Account")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Account name
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.account_data.get('name', ''))
        self.name_edit.setPlaceholderText("e.g., Primary Bank Account, Credit Card")
        form.addRow("Account Name:", self.name_edit)

        # Account type dropdown
        self.type_combo = QComboBox()
        for account_type in AccountType:
            self.type_combo.addItem(account_type.value.replace('_', ' ').title(), account_type.value)

        # Set current type if editing
        current_type = self.account_data.get('account_type', 'personal')
        index = self.type_combo.findData(current_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        form.addRow("Account Type:", self.type_combo)

        # Owner dropdown
        self.owner_combo = QComboBox()
        self.owner_combo.addItem("-- Select Owner --", None)  # Placeholder
        self.owner_combo.addItem("Shared", "Shared")
        for user in self.users:
            self.owner_combo.addItem(user['name'], user['name'])

        # Set current owner if editing
        if self.current_owner:
            index = self.owner_combo.findData(self.current_owner)
            if index >= 0:
                self.owner_combo.setCurrentIndex(index)

        form.addRow("Owner:", self.owner_combo)

        # Default expense type dropdown
        self.default_expense_type_combo = QComboBox()
        self.default_expense_type_combo.addItem("SHARED - Household expenses (split fairly)", "SHARED")
        self.default_expense_type_combo.addItem("INDIVIDUAL - Personal expenses (not split)", "INDIVIDUAL")

        # Set default based on current value or owner type
        is_shared_owner = self.current_owner == "Shared"
        current_default = self.account_data.get('default_expense_type', 'SHARED' if is_shared_owner else 'INDIVIDUAL')
        index = self.default_expense_type_combo.findData(current_default)
        if index >= 0:
            self.default_expense_type_combo.setCurrentIndex(index)

        form.addRow("Default Expense Type:", self.default_expense_type_combo)

        # Statements folder
        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setText(self.account_data.get('statements_folder', ''))
        self.folder_edit.setPlaceholderText("e.g., data/raw/statements/Michael/Bank")
        folder_layout.addWidget(self.folder_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_statements_folder)
        folder_layout.addWidget(browse_btn)

        form.addRow("Statements Folder:", folder_layout)

        # Processed folder
        processed_layout = QHBoxLayout()
        self.processed_edit = QLineEdit()
        self.processed_edit.setText(self.account_data.get('processed_folder', ''))
        self.processed_edit.setPlaceholderText("e.g., data/processed/transactions/Michael/Bank")
        processed_layout.addWidget(self.processed_edit)

        processed_browse_btn = QPushButton("Browse...")
        processed_browse_btn.clicked.connect(self.browse_processed_folder)
        processed_layout.addWidget(processed_browse_btn)

        form.addRow("Processed Folder:", processed_layout)

        layout.addLayout(form)

        # Info label
        info = QLabel(
            "The statements folder contains raw bank statement PDFs. "
            "The processed folder will contain extracted and classified transactions "
            "organized by year-month."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 9pt; padding: 10px;")
        layout.addWidget(info)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_statements_folder(self):
        """Browse for statements folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Statements Folder",
            self.folder_edit.text() or ""
        )
        if folder:
            self.folder_edit.setText(folder)

    def browse_processed_folder(self):
        """Browse for processed folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Processed Folder",
            self.processed_edit.text() or ""
        )
        if folder:
            self.processed_edit.setText(folder)

    def get_account_data(self):
        """Get the account data from dialog."""
        return {
            'name': self.name_edit.text().strip(),
            'account_type': self.type_combo.currentData(),
            'default_expense_type': self.default_expense_type_combo.currentData(),
            'statements_folder': self.folder_edit.text().strip(),
            'processed_folder': self.processed_edit.text().strip(),
            'owner': self.owner_combo.currentData()
        }

    def accept(self):
        """Validate and accept dialog."""
        data = self.get_account_data()
        if not data['owner']:
            QMessageBox.warning(self, "Validation Error", "Please select an owner for this account.")
            return
        if not data['name']:
            QMessageBox.warning(self, "Validation Error", "Account name is required.")
            return
        if not data['statements_folder']:
            QMessageBox.warning(self, "Validation Error", "Statements folder is required.")
            return
        if not data['processed_folder']:
            QMessageBox.warning(self, "Validation Error", "Processed folder is required.")
            return
        if data['statements_folder'] == data['processed_folder']:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Statements folder and processed folder must be different."
            )
            return
        super().accept()


class UserDialog(QDialog):
    """Dialog for adding/editing user information."""

    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.setWindowTitle("Edit User" if user_data else "Add User")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # User name
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.user_data.get('name', ''))
        self.name_edit.setPlaceholderText("e.g., Michael, Jacqui")
        form.addRow("User Name:", self.name_edit)

        layout.addLayout(form)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_user_data(self):
        """Get the user data from dialog."""
        return {
            'name': self.name_edit.text().strip(),
            'person_sheet_path': ''
        }

    def accept(self):
        """Validate and accept dialog."""
        data = self.get_user_data()
        if not data['name']:
            QMessageBox.warning(self, "Validation Error", "User name is required.")
            return
        # Person sheet path is optional - can be set later
        super().accept()


class SettingsTab(QWidget):
    """Tab for configuring application settings."""

    config_changed = pyqtSignal()  # Signal when config is modified

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.config_file = Path("config.json")
        self.config_data = self._load_config()

        self.init_ui()
        self.load_config_to_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Application Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # === TAB 0: GENERAL ===
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        # Calculation Mode
        mode_group = QGroupBox("Calculation Mode")
        mode_layout = QFormLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("NET - Income is take-home pay (default)", "NET")
        self.mode_combo.addItem("GROSS - Calculate tax from gross income", "GROSS")
        mode_layout.addRow("Income Mode:", self.mode_combo)

        mode_info = QLabel(
            "NET mode: Enter your take-home pay from payslips.\n"
            "GROSS mode: Enter gross salary, system will calculate tax deductions."
        )
        mode_info.setWordWrap(True)
        mode_info.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        mode_layout.addRow(mode_info)

        mode_group.setLayout(mode_layout)
        general_layout.addWidget(mode_group)

        # Financial Year Configuration
        fy_group = QGroupBox("Financial Year Configuration")
        fy_layout = QFormLayout()

        # Financial year start month dropdown
        self.fy_start_month_combo = QComboBox()
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        for i, month in enumerate(months, 1):
            self.fy_start_month_combo.addItem(month, i)
        fy_layout.addRow("Financial Year Start Month:", self.fy_start_month_combo)

        # Current financial year label (read-only display)
        self.current_fy_label = QLabel("FY 2024-2025")
        self.current_fy_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 5px;")
        fy_layout.addRow("Current Financial Year:", self.current_fy_label)

        # Connect signal to update label when month changes
        self.fy_start_month_combo.currentIndexChanged.connect(self.update_fy_label)

        fy_info = QLabel(
            "The financial year determines the period for fair share calculations.\n"
            "Example: If set to April, FY 2024-2025 runs from April 2024 to March 2025."
        )
        fy_info.setWordWrap(True)
        fy_info.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        fy_layout.addRow(fy_info)

        fy_group.setLayout(fy_layout)
        general_layout.addWidget(fy_group)

        # Working Directory
        working_dir_group = QGroupBox("Working Directory")
        working_dir_layout = QHBoxLayout()

        self.working_dir_edit = QLineEdit()
        self.working_dir_edit.setPlaceholderText("e.g., data")
        working_dir_layout.addWidget(self.working_dir_edit, 1)

        working_dir_btn = QPushButton("Browse...")
        working_dir_btn.clicked.connect(self.browse_working_dir)
        working_dir_layout.addWidget(working_dir_btn)

        working_dir_group.setLayout(working_dir_layout)
        general_layout.addWidget(working_dir_group)

        # Matching Settings
        matching_group = QGroupBox("Transaction Matching Settings")
        matching_layout = QFormLayout()

        self.amount_tolerance_edit = QLineEdit()
        self.amount_tolerance_edit.setPlaceholderText("1.00")
        matching_layout.addRow("Amount Tolerance (R):", self.amount_tolerance_edit)

        self.date_tolerance_edit = QLineEdit()
        self.date_tolerance_edit.setPlaceholderText("3")
        matching_layout.addRow("Date Tolerance (days):", self.date_tolerance_edit)

        self.merchant_similarity_edit = QLineEdit()
        self.merchant_similarity_edit.setPlaceholderText("0.6")
        matching_layout.addRow("Merchant Similarity (0-1):", self.merchant_similarity_edit)

        matching_info = QLabel(
            "Used when matching transactions between bank statements and person sheets."
        )
        matching_info.setWordWrap(True)
        matching_info.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        matching_layout.addRow(matching_info)

        matching_group.setLayout(matching_layout)
        general_layout.addWidget(matching_group)

        # Classification Settings
        classification_group = QGroupBox("Transaction Classification Settings")
        classification_layout = QFormLayout()

        self.classification_enabled_check = QCheckBox("Enable automatic classification")
        self.classification_enabled_check.setChecked(True)
        classification_layout.addRow(self.classification_enabled_check)

        classification_info = QLabel(
            "Controls how transactions are classified as household vs. personal expenses.\n"
            "Default expense type is now configured per-account in the Accounts tab."
        )
        classification_info.setWordWrap(True)
        classification_info.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        classification_layout.addRow(classification_info)

        classification_group.setLayout(classification_layout)
        general_layout.addWidget(classification_group)

        general_layout.addStretch()
        self.tab_widget.addTab(general_tab, "General")

        # === TAB 1: USERS ===
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)

        users_label = QLabel("Users")
        users_label_font = QFont()
        users_label_font.setPointSize(11)
        users_label_font.setBold(True)
        users_label.setFont(users_label_font)
        users_layout.addWidget(users_label)

        self.users_list = QListWidget()
        self.users_list.currentItemChanged.connect(self.on_user_selected)
        users_layout.addWidget(self.users_list)

        # User buttons
        user_btn_layout = QHBoxLayout()
        self.add_user_btn = QPushButton("Add User")
        self.add_user_btn.clicked.connect(self.add_user)
        user_btn_layout.addWidget(self.add_user_btn)

        self.edit_user_btn = QPushButton("Edit User")
        self.edit_user_btn.clicked.connect(self.edit_user)
        self.edit_user_btn.setEnabled(False)
        user_btn_layout.addWidget(self.edit_user_btn)

        self.delete_user_btn = QPushButton("Delete User")
        self.delete_user_btn.clicked.connect(self.delete_user)
        self.delete_user_btn.setEnabled(False)
        user_btn_layout.addWidget(self.delete_user_btn)

        users_layout.addLayout(user_btn_layout)

        # Migration section
        migration_group = QGroupBox("Migration")
        migration_layout = QVBoxLayout()

        migrate_info = QLabel(
            "Import users from existing checkpoint data:"
        )
        migrate_info.setWordWrap(True)
        migration_layout.addWidget(migrate_info)

        self.migrate_btn = QPushButton("Import from Checkpoint")
        self.migrate_btn.clicked.connect(self.migrate_from_checkpoint)
        migration_layout.addWidget(self.migrate_btn)

        migration_group.setLayout(migration_layout)
        users_layout.addWidget(migration_group)

        self.tab_widget.addTab(users_tab, "Users")

        # === TAB 2: ACCOUNTS ===
        accounts_tab = QWidget()
        accounts_layout = QVBoxLayout(accounts_tab)

        # All accounts section
        all_accounts_group = QGroupBox("All Accounts")
        all_accounts_layout = QVBoxLayout()

        # Info label
        info_label = QLabel("Manage accounts for all users and shared accounts:")
        info_label.setStyleSheet("color: #666; padding: 5px;")
        all_accounts_layout.addWidget(info_label)

        # Accounts list
        self.accounts_list = QListWidget()
        self.accounts_list.currentItemChanged.connect(self.on_account_selected)
        all_accounts_layout.addWidget(self.accounts_list)

        # Account buttons
        account_btn_layout = QHBoxLayout()
        self.add_account_btn = QPushButton("Add Account")
        self.add_account_btn.clicked.connect(self.add_account)
        account_btn_layout.addWidget(self.add_account_btn)

        self.edit_account_btn = QPushButton("Edit Account")
        self.edit_account_btn.clicked.connect(self.edit_account)
        self.edit_account_btn.setEnabled(False)
        account_btn_layout.addWidget(self.edit_account_btn)

        self.delete_account_btn = QPushButton("Delete Account")
        self.delete_account_btn.clicked.connect(self.delete_account)
        self.delete_account_btn.setEnabled(False)
        account_btn_layout.addWidget(self.delete_account_btn)

        all_accounts_layout.addLayout(account_btn_layout)

        all_accounts_group.setLayout(all_accounts_layout)
        accounts_layout.addWidget(all_accounts_group)

        # Save/Reload buttons at bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)

        self.reload_btn = QPushButton("Reload from File")
        self.reload_btn.clicked.connect(self.reload_config)
        button_layout.addWidget(self.reload_btn)

        button_layout.addStretch()
        accounts_layout.addLayout(button_layout)

        self.tab_widget.addTab(accounts_tab, "Accounts")

        # Add tab widget to main layout
        layout.addWidget(self.tab_widget)

    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._default_config()
        else:
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration structure."""
        return {
            "working_dir": "data",
            "mode": "NET",  # NET or GROSS
            "users": [],
            "shared_accounts": [],
            "matching": {
                "amount_tolerance": 1.00,
                "date_tolerance_days": 3,
                "merchant_similarity_threshold": 0.6
            },
            "classification": {
                "enabled": True,
                "default_shared_type": "SHARED"
            }
        }

    def load_config_to_ui(self):
        """Load configuration data into UI widgets."""
        # Load general settings
        self.working_dir_edit.setText(self.config_data.get('working_dir', 'data'))

        # Load mode
        mode = self.config_data.get('mode', 'NET')
        index = self.mode_combo.findData(mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)

        # Load financial year start month
        fy_start_month = self.config_data.get('financial_year_start_month', 1)
        index = self.fy_start_month_combo.findData(fy_start_month)
        if index >= 0:
            self.fy_start_month_combo.setCurrentIndex(index)
        self.update_fy_label()

        # Load matching settings
        matching = self.config_data.get('matching', {})
        self.amount_tolerance_edit.setText(str(matching.get('amount_tolerance', 1.00)))
        self.date_tolerance_edit.setText(str(matching.get('date_tolerance_days', 3)))
        self.merchant_similarity_edit.setText(str(matching.get('merchant_similarity_threshold', 0.6)))

        # Load classification settings
        classification = self.config_data.get('classification', {})
        self.classification_enabled_check.setChecked(classification.get('enabled', True))

        # Load users in Users tab
        self.users_list.clear()
        for user in self.config_data.get('users', []):
            item = QListWidgetItem(user['name'])
            item.setData(Qt.UserRole, user)
            self.users_list.addItem(item)

        # Load all accounts (both user and shared) into unified list
        self.accounts_list.clear()

        # Load shared accounts first
        for account in self.config_data.get('shared_accounts', []):
            account_type = account.get('account_type', 'personal').replace('_', ' ').title()
            default_type = account.get('default_expense_type', 'SHARED')
            display_text = f"[Shared] [{account_type}] {account['name']} → {default_type}"
            item = QListWidgetItem(display_text)
            # Store both account data and owner info
            item.setData(Qt.UserRole, {'account': account, 'owner': 'Shared'})
            self.accounts_list.addItem(item)

        # Load each user's accounts
        for user in self.config_data.get('users', []):
            user_name = user['name']
            for account in user.get('accounts', []):
                account_type = account.get('account_type', 'personal').replace('_', ' ').title()
                default_type = account.get('default_expense_type', 'INDIVIDUAL')
                display_text = f"[{user_name}] [{account_type}] {account['name']} → {default_type}"
                item = QListWidgetItem(display_text)
                # Store both account data and owner info
                item.setData(Qt.UserRole, {'account': account, 'owner': user_name, 'user_id': user['id']})
                self.accounts_list.addItem(item)

    def refresh_accounts_list(self):
        """Refresh the accounts list with all accounts."""
        self.accounts_list.clear()

        # Load shared accounts first
        for account in self.config_data.get('shared_accounts', []):
            account_type = account.get('account_type', 'personal').replace('_', ' ').title()
            default_type = account.get('default_expense_type', 'SHARED')
            display_text = f"[Shared] [{account_type}] {account['name']} → {default_type}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, {'account': account, 'owner': 'Shared'})
            self.accounts_list.addItem(item)

        # Load each user's accounts
        for user in self.config_data.get('users', []):
            user_name = user['name']
            for account in user.get('accounts', []):
                account_type = account.get('account_type', 'personal').replace('_', ' ').title()
                default_type = account.get('default_expense_type', 'INDIVIDUAL')
                display_text = f"[{user_name}] [{account_type}] {account['name']} → {default_type}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, {'account': account, 'owner': user_name, 'user_id': user['id']})
                self.accounts_list.addItem(item)

    def on_user_selected(self, current, previous):
        """Handle user selection change in Users tab."""
        if current:
            self.edit_user_btn.setEnabled(True)
            self.delete_user_btn.setEnabled(True)
        else:
            self.edit_user_btn.setEnabled(False)
            self.delete_user_btn.setEnabled(False)

    def on_account_selected(self, current, previous):
        """Handle account selection change."""
        if current:
            self.edit_account_btn.setEnabled(True)
            self.delete_account_btn.setEnabled(True)
        else:
            self.edit_account_btn.setEnabled(False)
            self.delete_account_btn.setEnabled(False)

    def add_user(self):
        """Add a new user."""
        dialog = UserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            user_data = dialog.get_user_data()
            user_data['id'] = f"user_{len(self.config_data.get('users', [])) + 1}"
            user_data['accounts'] = []

            # Add to config
            if 'users' not in self.config_data:
                self.config_data['users'] = []
            self.config_data['users'].append(user_data)

            # Add to Users tab list
            item = QListWidgetItem(user_data['name'])
            item.setData(Qt.UserRole, user_data)
            self.users_list.addItem(item)

            self.config_changed.emit()

    def edit_user(self):
        """Edit selected user."""
        current = self.users_list.currentItem()
        if not current:
            return

        user_data = current.data(Qt.UserRole)
        dialog = UserDialog(self, user_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_user_data()
            user_data['name'] = updated_data['name']
            user_data['person_sheet_path'] = updated_data['person_sheet_path']

            # Update Users tab list item
            current.setText(user_data['name'])
            current.setData(Qt.UserRole, user_data)

            # Refresh accounts list to show updated user name
            self.refresh_accounts_list()

            self.config_changed.emit()

    def delete_user(self):
        """Delete selected user."""
        current = self.users_list.currentItem()
        if not current:
            return

        user_data = current.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user '{user_data['name']}'?\n\n"
            f"This will also delete all associated accounts.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove from config
            self.config_data['users'] = [
                u for u in self.config_data.get('users', [])
                if u['id'] != user_data['id']
            ]

            # Remove from Users tab list
            row = self.users_list.row(current)
            self.users_list.takeItem(row)

            # Refresh accounts list to remove deleted user's accounts
            self.refresh_accounts_list()

            self.config_changed.emit()

    def add_account(self):
        """Add account with owner selection."""
        users = self.config_data.get('users', [])
        dialog = AccountDialog(self, users=users)
        if dialog.exec_() == QDialog.Accepted:
            account_data = dialog.get_account_data()
            owner = account_data.pop('owner', None)  # Remove owner field (not stored in account data)

            if not owner:
                QMessageBox.warning(self, "Error", "No owner selected.")
                return

            # Add to appropriate location based on owner
            if owner == "Shared":
                # Add to shared accounts
                if 'shared_accounts' not in self.config_data:
                    self.config_data['shared_accounts'] = []
                self.config_data['shared_accounts'].append(account_data)
            else:
                # Add to specific user's accounts
                user = self._find_user_by_name(owner)
                if not user:
                    QMessageBox.warning(self, "Error", f"User '{owner}' not found.")
                    return

                if 'accounts' not in user:
                    user['accounts'] = []
                user['accounts'].append(account_data)

            # Refresh accounts list
            self.refresh_accounts_list()
            self.config_changed.emit()

    def edit_account(self):
        """Edit selected account with owner change support."""
        account_item = self.accounts_list.currentItem()
        if not account_item:
            return

        item_data = account_item.data(Qt.UserRole)
        account_data = item_data['account']
        current_owner = item_data['owner']
        old_account_name = account_data['name']

        users = self.config_data.get('users', [])
        dialog = AccountDialog(self, account_data=account_data, users=users, current_owner=current_owner)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_account_data()
            new_owner = updated_data.pop('owner', None)

            if not new_owner:
                QMessageBox.warning(self, "Error", "No owner selected.")
                return

            # Check if owner changed
            if new_owner != current_owner:
                # Remove from old location
                if current_owner == "Shared":
                    self.config_data['shared_accounts'] = [
                        a for a in self.config_data.get('shared_accounts', [])
                        if a['name'] != old_account_name
                    ]
                else:
                    old_user = self._find_user_by_name(current_owner)
                    if old_user:
                        old_user['accounts'] = [
                            a for a in old_user.get('accounts', [])
                            if a['name'] != old_account_name
                        ]

                # Add to new location
                if new_owner == "Shared":
                    if 'shared_accounts' not in self.config_data:
                        self.config_data['shared_accounts'] = []
                    self.config_data['shared_accounts'].append(updated_data)
                else:
                    new_user = self._find_user_by_name(new_owner)
                    if not new_user:
                        QMessageBox.warning(self, "Error", f"User '{new_owner}' not found.")
                        return
                    if 'accounts' not in new_user:
                        new_user['accounts'] = []
                    new_user['accounts'].append(updated_data)
            else:
                # Same owner - update in place
                account_data.update(updated_data)

            # Refresh accounts list
            self.refresh_accounts_list()
            self.config_changed.emit()

    def delete_account(self):
        """Delete selected account."""
        account_item = self.accounts_list.currentItem()
        if not account_item:
            return

        item_data = account_item.data(Qt.UserRole)
        account_data = item_data['account']
        owner = item_data['owner']

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete account '{account_data['name']}' owned by '{owner}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove from appropriate location
            if owner == "Shared":
                self.config_data['shared_accounts'] = [
                    a for a in self.config_data.get('shared_accounts', [])
                    if a['name'] != account_data['name']
                ]
            else:
                user = self._find_user_by_name(owner)
                if user:
                    user['accounts'] = [
                        a for a in user.get('accounts', [])
                        if a['name'] != account_data['name']
                    ]

            # Refresh accounts list
            self.refresh_accounts_list()
            self.config_changed.emit()

    def _find_user_by_name(self, name: str) -> Optional[Dict]:
        """Find a user by name in the config data."""
        for user in self.config_data.get('users', []):
            if user['name'] == name:
                return user
        return None

    def browse_working_dir(self):
        """Browse for working directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Working Directory",
            self.working_dir_edit.text() or ""
        )
        if folder:
            self.working_dir_edit.setText(folder)

    def migrate_from_checkpoint(self):
        """Import users from existing checkpoint file."""
        try:
            checkpoint = CheckpointManager()

            if not checkpoint.data.get('person1_name') or not checkpoint.data.get('person2_name'):
                QMessageBox.warning(
                    self,
                    "No Checkpoint Data",
                    "No user data found in checkpoint file.\n\n"
                    "Process at least one month first, or add users manually."
                )
                return

            person1_name = checkpoint.data.get('person1_name')
            person2_name = checkpoint.data.get('person2_name')

            # Check if users already exist
            existing_names = [u['name'] for u in self.config_data.get('users', [])]

            users_to_add = []
            if person1_name and person1_name not in existing_names:
                users_to_add.append(person1_name)
            if person2_name and person2_name not in existing_names:
                users_to_add.append(person2_name)

            if not users_to_add:
                QMessageBox.information(
                    self,
                    "Already Imported",
                    "All users from checkpoint already exist in configuration."
                )
                return

            # Add users
            if 'users' not in self.config_data:
                self.config_data['users'] = []

            for name in users_to_add:
                user_data = {
                    'id': f"user_{len(self.config_data['users']) + 1}",
                    'name': name,
                    'person_sheet_path': '',
                    'accounts': []
                }
                self.config_data['users'].append(user_data)

                # Add to list
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, user_data)
                self.users_list.addItem(item)

            QMessageBox.information(
                self,
                "Import Successful",
                f"Imported {len(users_to_add)} user(s) from checkpoint:\n\n" +
                "\n".join(users_to_add) +
                "\n\nYou can now add their Excel sheet paths and accounts."
            )

            self.config_changed.emit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing from checkpoint:\n\n{str(e)}"
            )

    def save_config(self):
        """Save configuration to file."""
        try:
            # Update config data from UI - General settings
            self.config_data['working_dir'] = self.working_dir_edit.text().strip()
            self.config_data['mode'] = self.mode_combo.currentData()
            self.config_data['financial_year_start_month'] = self.fy_start_month_combo.currentData()

            # Update matching settings
            try:
                amount_tolerance = float(self.amount_tolerance_edit.text())
                date_tolerance = int(self.date_tolerance_edit.text())
                merchant_similarity = float(self.merchant_similarity_edit.text())

                if not (0 <= merchant_similarity <= 1):
                    raise ValueError("Merchant similarity must be between 0 and 1")

                self.config_data['matching'] = {
                    'amount_tolerance': amount_tolerance,
                    'date_tolerance_days': date_tolerance,
                    'merchant_similarity_threshold': merchant_similarity
                }
            except ValueError as e:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"Invalid matching settings:\n{str(e)}\n\nPlease check your values."
                )
                return

            # Update classification settings
            # Keep default_shared_type in config for backward compatibility (as global fallback)
            # but don't update it from UI anymore (now per-account setting)
            if 'classification' not in self.config_data:
                self.config_data['classification'] = {}
            self.config_data['classification']['enabled'] = self.classification_enabled_check.isChecked()
            # Preserve existing default_shared_type if present
            if 'default_shared_type' not in self.config_data['classification']:
                self.config_data['classification']['default_shared_type'] = 'SHARED'

            # Validate
            if len(self.config_data.get('users', [])) < 2:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Configuration must have at least 2 users."
                )
                return

            # Save to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2)

            QMessageBox.information(
                self,
                "Success",
                f"Configuration saved to {self.config_file}"
            )

            self.config_changed.emit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Error saving configuration:\n\n{str(e)}"
            )

    def reload_config(self):
        """Reload configuration from file."""
        reply = QMessageBox.question(
            self,
            "Confirm Reload",
            "Reload configuration from file?\n\n"
            "Any unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.config_data = self._load_config()
            self.load_config_to_ui()
            QMessageBox.information(
                self,
                "Reloaded",
                "Configuration reloaded from file."
            )

    def get_config_data(self):
        """Get current configuration data."""
        return self.config_data

    def get_user_names(self) -> List[str]:
        """Get list of all user names."""
        return [u['name'] for u in self.config_data.get('users', [])]

    def get_user_by_name(self, name: str) -> Optional[Dict]:
        """Get user data by name."""
        for user in self.config_data.get('users', []):
            if user['name'] == name:
                return user
        return None

    def get_mode(self) -> str:
        """Get the current calculation mode (NET or GROSS)."""
        return self.config_data.get('mode', 'NET')

    def is_gross_mode(self) -> bool:
        """Check if GROSS mode is enabled."""
        return self.get_mode() == 'GROSS'

    def get_financial_year_start_month(self) -> int:
        """Get the financial year start month (1-12)."""
        return self.config_data.get('financial_year_start_month', 1)

    def update_fy_label(self):
        """Update the financial year label based on current selection."""
        from datetime import date
        from dateutil.relativedelta import relativedelta

        start_month = self.fy_start_month_combo.currentData()
        if start_month is None:
            return

        today = date.today()
        year = today.year

        # If we're before the start month, the FY started last year
        if today.month < start_month:
            year -= 1

        start_date = date(year, start_month, 1)
        end_date = start_date + relativedelta(years=1) - relativedelta(days=1)

        if start_date.year == end_date.year:
            fy_label = f"FY {start_date.year}: {start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
        else:
            fy_label = f"FY {start_date.year}-{end_date.year}: {start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"

        self.current_fy_label.setText(fy_label)
