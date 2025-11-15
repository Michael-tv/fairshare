"""
Calculate tab - Fair share split calculation.
"""

from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QRadioButton,
    QButtonGroup, QFileDialog, QTextEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from person_sheet_importer import PersonSheetImporter
from split_calculator import FinancialSplitter
from checkpoint_manager import CheckpointManager
from reports import ReportGenerator
from gui.dialogs import ResultsDialog


class CalculationThread(QThread):
    """Background thread for performing calculations."""

    finished = pyqtSignal(object, object)  # result, error
    progress = pyqtSignal(str)

    def __init__(self, person1_file, person2_file, use_gross_mode):
        super().__init__()
        self.person1_file = person1_file
        self.person2_file = person2_file
        self.use_gross_mode = use_gross_mode

    def run(self):
        """Run the calculation in background."""
        try:
            self.progress.emit("Loading Person 1 data...")
            importer = PersonSheetImporter()

            # Get person names from filenames
            person1_name = Path(self.person1_file).stem.split('_')[0]
            person2_name = Path(self.person2_file).stem.split('_')[0]

            self.progress.emit("Loading Person 2 data...")

            # Import household month
            period = importer.import_household_month(
                self.person1_file,
                person1_name,
                self.person2_file,
                person2_name
            )

            self.progress.emit("Calculating fair share split...")

            # Calculate split
            splitter = FinancialSplitter()
            result = splitter.calculate_split(
                period,
                period.people[0],
                period.people[1],
                skip_tax_calculation=not self.use_gross_mode
            )

            self.progress.emit("Saving to checkpoint...")

            # Save to checkpoint
            checkpoint = CheckpointManager()
            checkpoint.add_monthly_result(result, self.person1_file, self.person2_file)

            self.progress.emit("Complete!")
            self.finished.emit(result, None)

        except Exception as e:
            self.finished.emit(None, str(e))


class CalculateTab(QWidget):
    """Tab for calculating fair share split."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.calculation_thread = None
        self.last_result = None
        self.user_file_inputs = []  # Store references to user file input widgets

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Calculate Fair Share Split")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Upload person Excel files to calculate fair share splits based on proportional income."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Mode selection - Config vs Manual
        mode_info_layout = QHBoxLayout()
        mode_info_label = QLabel("Mode:")
        mode_info_layout.addWidget(mode_info_label)

        self.use_config_checkbox = QCheckBox("Use Settings Configuration")
        self.use_config_checkbox.setChecked(False)
        self.use_config_checkbox.stateChanged.connect(self.on_mode_changed)
        mode_info_layout.addWidget(self.use_config_checkbox)

        self.reload_config_btn = QPushButton("Reload from Settings")
        self.reload_config_btn.clicked.connect(self.load_from_config)
        self.reload_config_btn.setEnabled(False)
        mode_info_layout.addWidget(self.reload_config_btn)

        mode_info_layout.addStretch()
        layout.addLayout(mode_info_layout)

        # File selection group (dynamic based on mode)
        self.file_group = QGroupBox("Select Person Excel Files")
        self.file_layout = QVBoxLayout()

        # Default: Person 1 file
        p1_layout = QHBoxLayout()
        p1_layout.addWidget(QLabel("Person 1:"))
        self.person1_path = QLineEdit()
        self.person1_path.setPlaceholderText("Select Excel file for Person 1...")
        p1_layout.addWidget(self.person1_path, 1)
        self.person1_btn = QPushButton("Browse...")
        self.person1_btn.clicked.connect(lambda: self.browse_person_file(0))
        p1_layout.addWidget(self.person1_btn)
        self.file_layout.addLayout(p1_layout)
        self.user_file_inputs.append((QLabel("Person 1:"), self.person1_path, self.person1_btn, p1_layout))

        # Default: Person 2 file
        p2_layout = QHBoxLayout()
        p2_layout.addWidget(QLabel("Person 2:"))
        self.person2_path = QLineEdit()
        self.person2_path.setPlaceholderText("Select Excel file for Person 2...")
        p2_layout.addWidget(self.person2_path, 1)
        self.person2_btn = QPushButton("Browse...")
        self.person2_btn.clicked.connect(lambda: self.browse_person_file(1))
        p2_layout.addWidget(self.person2_btn)
        self.file_layout.addLayout(p2_layout)
        self.user_file_inputs.append((QLabel("Person 2:"), self.person2_path, self.person2_btn, p2_layout))

        self.file_group.setLayout(self.file_layout)
        layout.addWidget(self.file_group)

        # Income mode selection
        mode_group = QGroupBox("Income Mode")
        mode_layout = QVBoxLayout()

        self.mode_group = QButtonGroup()
        self.net_mode = QRadioButton("NET Mode (Default) - Income is take-home pay")
        self.gross_mode = QRadioButton("GROSS Mode - Calculate tax from gross salary")
        self.net_mode.setChecked(True)

        self.mode_group.addButton(self.net_mode)
        self.mode_group.addButton(self.gross_mode)

        mode_layout.addWidget(self.net_mode)
        mode_layout.addWidget(self.gross_mode)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Calculate button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.calculate_btn = QPushButton("Calculate Fair Share Split")
        self.calculate_btn.setMinimumHeight(40)
        self.calculate_btn.clicked.connect(self.calculate_split)
        button_layout.addWidget(self.calculate_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()

        # Summary text
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(300)
        results_layout.addWidget(self.results_text)

        # Action buttons
        action_layout = QHBoxLayout()
        self.view_details_btn = QPushButton("View Detailed Breakdown")
        self.view_details_btn.clicked.connect(self.view_details)
        self.view_details_btn.setEnabled(False)
        action_layout.addWidget(self.view_details_btn)

        self.view_categories_btn = QPushButton("View Category Summary")
        self.view_categories_btn.clicked.connect(self.view_categories)
        self.view_categories_btn.setEnabled(False)
        action_layout.addWidget(self.view_categories_btn)

        action_layout.addStretch()
        results_layout.addLayout(action_layout)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group, 1)

    def browse_person_file(self, index):
        """Browse for person Excel file by index."""
        if index >= len(self.user_file_inputs):
            return

        _, line_edit, _, _ = self.user_file_inputs[index]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Excel File",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            line_edit.setText(file_path)

    def on_mode_changed(self, state):
        """Handle mode change between config and manual."""
        use_config = (state == Qt.Checked)
        self.reload_config_btn.setEnabled(use_config)

        if use_config:
            self.load_from_config()
        else:
            # Reset to 2-person manual mode
            self.reset_to_manual_mode()

    def load_from_config(self):
        """Load user configuration from settings tab."""
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

            if len(users) < 2:
                self.main_window.show_warning(
                    "Insufficient Users",
                    "Configuration must have at least 2 users.\n\n"
                    "Please add users in the Settings tab."
                )
                self.use_config_checkbox.setChecked(False)
                return

            # Clear existing inputs
            for _, line_edit, btn, layout in self.user_file_inputs:
                layout.setParent(None)

            self.user_file_inputs.clear()

            # Create inputs for each user from config
            for i, user in enumerate(users):
                user_layout = QHBoxLayout()
                label = QLabel(f"{user['name']}:")
                user_layout.addWidget(label)

                line_edit = QLineEdit()
                # Pre-fill with configured path if available
                sheet_path = user.get('person_sheet_path', '')
                line_edit.setText(sheet_path)
                line_edit.setPlaceholderText(f"Select Excel file for {user['name']}...")
                user_layout.addWidget(line_edit, 1)

                btn = QPushButton("Browse...")
                btn.clicked.connect(lambda checked, idx=i: self.browse_person_file(idx))
                user_layout.addWidget(btn)

                self.file_layout.addLayout(user_layout)
                self.user_file_inputs.append((label, line_edit, btn, user_layout))

            self.file_group.setTitle(f"User Excel Files ({len(users)} users from configuration)")

        except Exception as e:
            self.main_window.show_error(
                "Load Error",
                f"Error loading configuration:\n\n{str(e)}"
            )
            self.use_config_checkbox.setChecked(False)

    def reset_to_manual_mode(self):
        """Reset to default 2-person manual mode."""
        # Clear existing inputs
        for _, line_edit, btn, layout in self.user_file_inputs:
            layout.setParent(None)

        self.user_file_inputs.clear()

        # Recreate default 2-person layout
        # Person 1
        p1_layout = QHBoxLayout()
        p1_label = QLabel("Person 1:")
        p1_layout.addWidget(p1_label)
        self.person1_path = QLineEdit()
        self.person1_path.setPlaceholderText("Select Excel file for Person 1...")
        p1_layout.addWidget(self.person1_path, 1)
        self.person1_btn = QPushButton("Browse...")
        self.person1_btn.clicked.connect(lambda: self.browse_person_file(0))
        p1_layout.addWidget(self.person1_btn)
        self.file_layout.addLayout(p1_layout)
        self.user_file_inputs.append((p1_label, self.person1_path, self.person1_btn, p1_layout))

        # Person 2
        p2_layout = QHBoxLayout()
        p2_label = QLabel("Person 2:")
        p2_layout.addWidget(p2_label)
        self.person2_path = QLineEdit()
        self.person2_path.setPlaceholderText("Select Excel file for Person 2...")
        p2_layout.addWidget(self.person2_path, 1)
        self.person2_btn = QPushButton("Browse...")
        self.person2_btn.clicked.connect(lambda: self.browse_person_file(1))
        p2_layout.addWidget(self.person2_btn)
        self.file_layout.addLayout(p2_layout)
        self.user_file_inputs.append((p2_label, self.person2_path, self.person2_btn, p2_layout))

        self.file_group.setTitle("Select Person Excel Files")

    def calculate_split(self):
        """Calculate the fair share split."""
        # Collect all file paths
        file_paths = []
        for _, line_edit, _, _ in self.user_file_inputs:
            file_path = line_edit.text().strip()
            if file_path:
                file_paths.append(file_path)

        # Validate we have exactly 2 files (current system limitation)
        if len(file_paths) < 2:
            self.main_window.show_error(
                "Missing Files",
                "Please select Excel files for at least 2 people."
            )
            return

        if len(file_paths) > 2:
            self.main_window.show_warning(
                "Too Many Files",
                f"Selected {len(file_paths)} files, but the system currently only supports "
                "splitting between exactly 2 people.\n\n"
                "Only the first 2 files will be processed."
            )

        # Use first two files
        person1_file = file_paths[0]
        person2_file = file_paths[1]

        # Validate files exist
        if not Path(person1_file).exists():
            self.main_window.show_error(
                "File Not Found",
                f"First person file does not exist:\n{person1_file}"
            )
            return

        if not Path(person2_file).exists():
            self.main_window.show_error(
                "File Not Found",
                f"Second person file does not exist:\n{person2_file}"
            )
            return

        # Check for duplicate month
        try:
            checkpoint = CheckpointManager()
            # Try to extract period from filename
            person1_name = Path(person1_file).stem.split('_')[0]
            # This is a basic check - actual validation happens in the thread
        except Exception:
            pass  # Continue anyway

        # Disable UI during calculation
        self.calculate_btn.setEnabled(False)
        for _, _, btn, _ in self.user_file_inputs:
            btn.setEnabled(False)
        self.net_mode.setEnabled(False)
        self.gross_mode.setEnabled(False)

        # Clear previous results
        self.results_text.clear()
        self.view_details_btn.setEnabled(False)
        self.view_categories_btn.setEnabled(False)

        # Start calculation thread
        use_gross = self.gross_mode.isChecked()
        self.calculation_thread = CalculationThread(person1_file, person2_file, use_gross)
        self.calculation_thread.progress.connect(self.on_progress)
        self.calculation_thread.finished.connect(self.on_calculation_finished)
        self.calculation_thread.start()

    def on_progress(self, message):
        """Update progress label."""
        self.progress_label.setText(message)

    def on_calculation_finished(self, result, error):
        """Handle calculation completion."""
        # Re-enable UI
        self.calculate_btn.setEnabled(True)
        for _, _, btn, _ in self.user_file_inputs:
            btn.setEnabled(True)
        self.net_mode.setEnabled(True)
        self.gross_mode.setEnabled(True)
        self.progress_label.setText("")

        if error:
            self.main_window.show_error("Calculation Error", f"An error occurred:\n\n{error}")
            return

        # Store result
        self.last_result = result

        # Generate and display summary report
        try:
            report_gen = ReportGenerator()
            summary = report_gen.generate_summary_report(result)
            self.results_text.setPlainText(summary)

            # Enable detail buttons
            self.view_details_btn.setEnabled(True)
            self.view_categories_btn.setEnabled(True)

            # Refresh other tabs
            if self.main_window:
                self.main_window.refresh_all_tabs()

            # Show success message
            person_from = result.person1_name if result.person1_balance < 0 else result.person2_name
            person_to = result.person2_name if result.person1_balance < 0 else result.person1_name
            transfer = abs(result.person1_balance)

            self.main_window.show_info(
                "Calculation Complete",
                f"Month processed successfully!\n\n"
                f"{person_from} should pay {person_to}:\n"
                f"R{transfer:,.2f}"
            )

        except Exception as e:
            self.main_window.show_error("Report Error", f"Error generating report:\n\n{str(e)}")

    def view_details(self):
        """Show detailed expense breakdown."""
        if not self.last_result:
            return

        try:
            report_gen = ReportGenerator()
            breakdown = report_gen.generate_expense_breakdown(
                self.last_result.period,
                self.last_result
            )

            dialog = ResultsDialog("Detailed Expense Breakdown", breakdown, self)
            dialog.exec_()

        except Exception as e:
            self.main_window.show_error("Error", f"Error generating breakdown:\n\n{str(e)}")

    def view_categories(self):
        """Show category summary."""
        if not self.last_result:
            return

        try:
            report_gen = ReportGenerator()
            category_summary = report_gen.generate_category_summary(self.last_result.period)

            dialog = ResultsDialog("Category Summary", category_summary, self)
            dialog.exec_()

        except Exception as e:
            self.main_window.show_error("Error", f"Error generating category summary:\n\n{str(e)}")
