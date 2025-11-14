"""
Bank statement template system for multi-bank support.

This module provides infrastructure for loading and managing YAML-based
bank statement parsing templates, enabling support for any bank without
code changes.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
from PyPDF2 import PdfReader


@dataclass
class BankTemplate:
    """
    Represents a bank statement parsing template loaded from YAML.

    Attributes:
        bank_name: Name of the bank (e.g., "FNB", "ABSA")
        account_type: Type of account (e.g., "Credit Card", "Cheque Account")
        config: Complete YAML configuration dictionary
        template_name: Name of the template file (without .yaml extension)
    """
    bank_name: str
    account_type: str
    config: Dict[str, Any]
    template_name: str

    @classmethod
    def load(cls, template_path: Path) -> 'BankTemplate':
        """
        Load a bank template from a YAML file.

        Args:
            template_path: Path to the YAML template file

        Returns:
            BankTemplate instance

        Raises:
            FileNotFoundError: If template file doesn't exist
            yaml.YAMLError: If YAML is malformed
            KeyError: If required fields are missing
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Validate required fields
        if 'bank_name' not in config:
            raise KeyError(f"Template {template_path} missing 'bank_name' field")
        if 'account_type' not in config:
            raise KeyError(f"Template {template_path} missing 'account_type' field")

        return cls(
            bank_name=config['bank_name'],
            account_type=config['account_type'],
            config=config,
            template_name=template_path.stem
        )

    def matches_pdf(self, pdf_first_page: str) -> bool:
        """
        Check if this template's detection markers are found in the PDF.

        Args:
            pdf_first_page: Text content from the first page of the PDF

        Returns:
            True if any detection marker is found in the PDF text
        """
        markers = self.config.get('detection', {}).get('markers', [])
        pdf_upper = pdf_first_page.upper()

        return any(marker.upper() in pdf_upper for marker in markers)

    @property
    def priority(self) -> int:
        """
        Detection priority for this template.

        Higher priority templates are checked first during auto-detection.
        Default priority is 0.

        Returns:
            Priority value from template config
        """
        return self.config.get('detection', {}).get('priority', 0)

    def __str__(self) -> str:
        """String representation of the template."""
        return f"{self.bank_name} - {self.account_type} ({self.template_name})"


class TemplateRegistry:
    """
    Registry for managing and discovering bank statement templates.

    Loads all YAML templates from a directory and provides methods for
    auto-detection and manual template selection.
    """

    def __init__(self, templates_dir: Path):
        """
        Initialize the template registry.

        Args:
            templates_dir: Directory containing YAML template files
        """
        self.templates: List[BankTemplate] = []
        self.templates_dir = templates_dir
        self._load_all_templates()

    def _load_all_templates(self):
        """
        Load all YAML templates from the templates directory.

        Templates are loaded and sorted by priority (highest first).
        Invalid templates are skipped with a warning.
        """
        if not self.templates_dir.exists():
            print(f"⚠️  Templates directory does not exist: {self.templates_dir}")
            print(f"   Creating directory: {self.templates_dir}")
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            return

        yaml_files = list(self.templates_dir.glob("*.yaml"))

        if not yaml_files:
            print(f"⚠️  No template files found in {self.templates_dir}")
            return

        for yaml_file in yaml_files:
            try:
                template = BankTemplate.load(yaml_file)
                self.templates.append(template)
                print(f"✓ Loaded template: {template}")
            except Exception as e:
                print(f"⚠️  Failed to load {yaml_file.name}: {e}")

        # Sort by priority (highest first) for auto-detection
        self.templates.sort(key=lambda t: t.priority, reverse=True)

        if self.templates:
            print(f"\n✓ Loaded {len(self.templates)} template(s)")

    def get(self, name: str) -> Optional[BankTemplate]:
        """
        Get a template by name.

        Args:
            name: Template name (filename without .yaml extension)

        Returns:
            BankTemplate if found, None otherwise
        """
        for template in self.templates:
            if template.template_name == name:
                return template
        return None

    def auto_detect(self, pdf_path: Path) -> Optional[BankTemplate]:
        """
        Auto-detect the appropriate template for a PDF statement.

        Reads the first page of the PDF and checks detection markers
        from all templates in priority order.

        Args:
            pdf_path: Path to the PDF statement file

        Returns:
            BankTemplate if a match is found, None otherwise
        """
        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                if len(reader.pages) == 0:
                    print("⚠️  PDF has no pages")
                    return None

                first_page_text = reader.pages[0].extract_text()
        except Exception as e:
            print(f"⚠️  Error reading PDF: {e}")
            return None

        # Check templates in priority order
        for template in self.templates:
            if template.matches_pdf(first_page_text):
                return template

        return None

    def list_all(self) -> List[Tuple[str, str, str]]:
        """
        List all available templates.

        Returns:
            List of tuples: (template_name, bank_name, account_type)
        """
        return [
            (t.template_name, t.bank_name, t.account_type)
            for t in self.templates
        ]

    def validate_selection(self, pdf_path: Path,
                          specified_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a user-specified template matches auto-detection.

        This helps catch cases where the user specified the wrong template
        for their PDF file.

        Args:
            pdf_path: Path to the PDF statement file
            specified_name: Template name specified by the user

        Returns:
            Tuple of (is_valid, warning_message)
            - is_valid: True if template exists (even if mismatch)
            - warning_message: None if OK, warning string if mismatch or not found
        """
        specified = self.get(specified_name)

        if not specified:
            return False, f"Template '{specified_name}' not found"

        auto_detected = self.auto_detect(pdf_path)

        if auto_detected and auto_detected.template_name != specified_name:
            return True, (
                f"Auto-detected '{auto_detected.template_name}' "
                f"but you specified '{specified_name}'. "
                f"Proceeding with your choice..."
            )

        return True, None
