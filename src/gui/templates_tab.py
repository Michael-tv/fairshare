"""
Templates tab - Create Excel templates for new people.
"""

from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QTextEdit, QCheckBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from person_sheet_importer import PersonSheetImporter


class TemplatesTab(QWidget):
    """Tab for creating person Excel templates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Create Person Templates")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Instructions
        instructions_group = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout()

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setMaximumHeight(150)
        instructions.setHtml("""
        <p>Create Excel templates for tracking monthly income and expenses.</p>
        <p><b>Steps:</b></p>
        <ol>
            <li>Enter names for both people in the household</li>
            <li>Choose where to save the template files</li>
            <li>Click "Create Templates" to generate Excel files</li>
            <li>Fill in the templates each month with income and expense data</li>
            <li>Use the "Process Month" tab to calculate the fair share split</li>
        </ol>
        <p><b>Note:</b> Template names should follow the pattern: PersonName_Month_Year.xlsx</p>
        """)
        instructions_layout.addWidget(instructions)

        instructions_group.setLayout(instructions_layout)
        layout.addWidget(instructions_group)

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))

        self.use_config_checkbox = QCheckBox("Use Settings Configuration")
        self.use_config_checkbox.setChecked(False)
        self.use_config_checkbox.stateChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.use_config_checkbox)

        self.load_config_btn = QPushButton("Load from Settings")
        self.load_config_btn.clicked.connect(self.load_from_config)
        self.load_config_btn.setEnabled(False)
        mode_layout.addWidget(self.load_config_btn)

        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Person names group
        names_group = QGroupBox("Person Names")
        self.names_layout = QVBoxLayout()

        # Manual input mode (default)
        self.manual_names_widget = QWidget()
        manual_layout = QVBoxLayout()

        # Person 1 name
        p1_layout = QHBoxLayout()
        p1_layout.addWidget(QLabel("Person 1 Name:"))
        self.person1_name = QLineEdit()
        self.person1_name.setPlaceholderText("e.g., Michael")
        p1_layout.addWidget(self.person1_name, 1)
        manual_layout.addLayout(p1_layout)

        # Person 2 name
        p2_layout = QHBoxLayout()
        p2_layout.addWidget(QLabel("Person 2 Name:"))
        self.person2_name = QLineEdit()
        self.person2_name.setPlaceholderText("e.g., Jacqui")
        p2_layout.addWidget(self.person2_name, 1)
        manual_layout.addLayout(p2_layout)

        self.manual_names_widget.setLayout(manual_layout)
        self.names_layout.addWidget(self.manual_names_widget)

        # Config mode - user selection list
        self.config_names_widget = QWidget()
        config_layout = QVBoxLayout()

        config_info = QLabel("Select users to create templates for:")
        config_layout.addWidget(config_info)

        self.users_list = QListWidget()
        self.users_list.setSelectionMode(QListWidget.MultiSelection)
        config_layout.addWidget(self.users_list)

        self.config_names_widget.setLayout(config_layout)
        self.config_names_widget.setVisible(False)
        self.names_layout.addWidget(self.config_names_widget)

        names_group.setLayout(self.names_layout)
        layout.addWidget(names_group)

        # Output directory group
        output_group = QGroupBox("Output Location")
        output_layout = QHBoxLayout()

        output_layout.addWidget(QLabel("Save to:"))
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select folder to save templates...")
        self.output_path.setText(str(Path.cwd()))  # Default to current directory
        output_layout.addWidget(self.output_path, 1)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(self.browse_btn)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Create button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.create_btn = QPushButton("Create Templates")
        self.create_btn.setMinimumHeight(40)
        self.create_btn.clicked.connect(self.create_templates)
        button_layout.addWidget(self.create_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Result area
        result_group = QGroupBox("Template Details")
        result_layout = QVBoxLayout()

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Created templates will be listed here...")
        result_layout.addWidget(self.result_text)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 1)

        # Add stretch at bottom
        layout.addStretch()

    def browse_output(self):
        """Browse for output directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.output_path.text()
        )
        if folder:
            self.output_path.setText(folder)

    def on_mode_changed(self, state):
        """Handle mode change between config and manual."""
        use_config = (state == Qt.Checked)
        self.load_config_btn.setEnabled(use_config)

        # Toggle visibility
        self.manual_names_widget.setVisible(not use_config)
        self.config_names_widget.setVisible(use_config)

        if use_config:
            self.load_from_config()

    def load_from_config(self):
        """Load user list from settings configuration."""
        try:
            # Get config from settings tab
            if not hasattr(self.main_window, 'settings_tab'):
                self.main_window.show_error(
                    "Configuration Error",
                    "Settings tab not available. Please configure users in Settings first."
                )
                self.use_config_checkbox.setChecked(False)
                return

            config_data = self.main_window.settings_tab.get_config_data()
            users = config_data.get('users', [])

            if len(users) == 0:
                self.main_window.show_warning(
                    "No Users",
                    "No users configured.\n\nPlease add users in the Settings tab first."
                )
                self.use_config_checkbox.setChecked(False)
                return

            # Populate list
            self.users_list.clear()
            for user in users:
                item = QListWidgetItem(user['name'])
                item.setData(Qt.UserRole, user)
                self.users_list.addItem(item)

            # Select all by default
            for i in range(self.users_list.count()):
                self.users_list.item(i).setSelected(True)

        except Exception as e:
            self.main_window.show_error(
                "Load Error",
                f"Error loading configuration:\n\n{str(e)}"
            )
            self.use_config_checkbox.setChecked(False)

    def create_templates(self):
        """Create Excel templates for selected people."""
        output_dir = self.output_path.text().strip()

        if not output_dir:
            self.main_window.show_error("Missing Path", "Please select an output folder.")
            return

        output_path = Path(output_dir)
        if not output_path.exists():
            self.main_window.show_error(
                "Invalid Path",
                f"Output folder does not exist:\n{output_dir}"
            )
            return

        # Get names based on mode
        names_to_create = []

        if self.use_config_checkbox.isChecked():
            # Config mode - get selected users
            selected_items = self.users_list.selectedItems()
            if not selected_items:
                self.main_window.show_error(
                    "No Selection",
                    "Please select at least one user to create templates for."
                )
                return

            names_to_create = [item.text() for item in selected_items]
        else:
            # Manual mode - get entered names
            person1_name = self.person1_name.text().strip()
            person2_name = self.person2_name.text().strip()

            if not person1_name:
                self.main_window.show_error("Missing Name", "Please enter a name for Person 1.")
                return

            if not person2_name:
                self.main_window.show_error("Missing Name", "Please enter a name for Person 2.")
                return

            names_to_create = [person1_name, person2_name]

        try:
            importer = PersonSheetImporter()
            created_files = []

            # Create template for each person
            for name in names_to_create:
                template_file = output_path / f"{name}_Template.xlsx"
                importer.create_template_sheets(name, str(template_file))
                created_files.append(template_file)

            # Display results
            result_text = "✓ Templates created successfully!\n\n"
            result_text += "Created files:\n"
            for file in created_files:
                result_text += f"  • {file.name}\n"

            result_text += f"\nLocation: {output_path}\n\n"

            result_text += "Next steps:\n"
            result_text += "1. Rename templates to include the month/year (e.g., Michael_January_2024.xlsx)\n"
            result_text += "2. Fill in the Income sheet with monthly income sources\n"
            result_text += "3. Fill in the Expenses sheet with monthly expenses\n"
            result_text += "4. Use the 'Process Month' tab to calculate the fair share split\n\n"

            result_text += "Template structure:\n"
            result_text += "• Income sheet: Description, Amount, Type (Salary/Rental/Business/Investment/Other)\n"
            result_text += "• Expenses sheet: Description, Amount, Category, Type (Household/Personal)\n"

            self.result_text.setPlainText(result_text)

            # Show success dialog
            names_str = ", ".join(names_to_create)
            self.main_window.show_info(
                "Templates Created",
                f"Successfully created {len(created_files)} template(s) for:\n{names_str}\n\n"
                f"Files saved to:\n{output_path}"
            )

            # Open the folder in file explorer
            if self.main_window.confirm_action(
                "Open Folder",
                "Would you like to open the folder containing the templates?"
            ):
                import os
                import platform
                if platform.system() == "Windows":
                    os.startfile(output_path)
                elif platform.system() == "Darwin":  # macOS
                    os.system(f'open "{output_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{output_path}"')

        except Exception as e:
            self.main_window.show_error(
                "Creation Error",
                f"Error creating templates:\n\n{str(e)}"
            )
