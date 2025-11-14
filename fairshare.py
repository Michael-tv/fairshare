"""
Main CLI interface for the home finance splitting system.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from decimal import Decimal
from datetime import date
import argparse
from pathlib import Path

from models import Person, Income, Expense, FinancialPeriod, IncomeType, ExpenseType, ExpenseCategory
from split_calculator import FinancialSplitter
from reports import ReportGenerator
from excel_importer import ExcelImporter, quick_import
from person_sheet_importer import PersonSheetImporter, import_household_month, create_template_sheets
from checkpoint_manager import CheckpointManager, auto_detect_next_month_files
from bank_statement_parser import BankStatementParser
from config_manager import ConfigManager
from deferred_payment_manager import DeferredPaymentManager


def demo_example():
    """Run a demo example to show how the system works."""
    print("\n" + "=" * 80)
    print("DEMO: Financial Splitting System")
    print("=" * 80 + "\n")

    # Create two people
    michael = Person(name="Michael")
    jacqui = Person(name="Jacqui")

    # Create a financial period
    period = FinancialPeriod(
        period=date(2024, 4, 1),
        people=[michael, jacqui]
    )

    # Add incomes
    print("Adding income data...")
    period.add_income(Income(
        person=michael,
        amount=Decimal("70000"),
        income_type=IncomeType.SALARY,
        description="Michael's Salary",
        period=date(2024, 4, 1)
    ))

    period.add_income(Income(
        person=jacqui,
        amount=Decimal("30000"),
        income_type=IncomeType.SALARY,
        description="Jacqui's Salary",
        period=date(2024, 4, 1)
    ))

    # Add shared expenses
    print("Adding shared expenses...")
    shared_expenses = [
        ("Groceries", Decimal("8000"), ExpenseCategory.GROCERIES),
        ("Electricity", Decimal("2000"), ExpenseCategory.UTILITIES),
        ("Internet", Decimal("899"), ExpenseCategory.UTILITIES),
        ("Property Levies", Decimal("1200"), ExpenseCategory.LEVIES),
    ]

    for desc, amount, category in shared_expenses:
        period.add_expense(Expense(
            description=desc,
            amount=amount,
            category=category,
            expense_type=ExpenseType.HOUSEHOLD,
            paid_by=michael  # Michael paid for all in this demo
        ))

    # Add individual expenses
    print("Adding individual expenses...")
    period.add_expense(Expense(
        description="Michael's Car Payment",
        amount=Decimal("5000"),
        category=ExpenseCategory.LOANS,
        expense_type=ExpenseType.INDIVIDUAL,
        belongs_to=michael
    ))

    period.add_expense(Expense(
        description="Jacqui's Medical Insurance",
        amount=Decimal("1500"),
        category=ExpenseCategory.INSURANCE,
        expense_type=ExpenseType.INDIVIDUAL,
        belongs_to=jacqui
    ))

    # Calculate split
    print("\nCalculating split...\n")
    splitter = FinancialSplitter(2024)
    result = splitter.calculate_split(
        period,
        michael,
        jacqui,
        person1_age=35,
        person2_age=32
    )

    # Generate reports
    reporter = ReportGenerator()

    print(reporter.generate_summary_report(result))
    print("\n" + "=" * 80 + "\n")
    print(reporter.generate_expense_breakdown(period, result))
    print("\n" + "=" * 80 + "\n")
    print(reporter.generate_category_summary(period))


def import_from_excel(excel_path: str):
    """Import and analyze data from existing Excel file."""
    print(f"\nImporting from Excel: {excel_path}\n")

    try:
        # Initialize classifier
        from transaction_classifier import TransactionClassifier
        from category_manager import CategoryManager
        cat_mgr = CategoryManager()
        classifier = TransactionClassifier(cat_mgr, use_learned=False)

        importer = ExcelImporter(excel_path, classifier)

        print("Importing Expense Balance Sheet...")
        period, michael, jacqui = importer.import_from_expense_balance_sheet()

        print(f"\nImported data for period: {period.period}")
        print(f"Total incomes: {len(period.incomes)}")
        print(f"Total expenses: {len(period.expenses)}")
        print(f"\nIncome breakdown:")
        print(f"  {michael.name}: R{period.get_total_income(michael):,.2f}")
        print(f"  {jacqui.name}: R{period.get_total_income(jacqui):,.2f}")

        # Calculate split
        print("\nCalculating financial split...")
        splitter = FinancialSplitter(2024)
        result = splitter.calculate_split(
            period,
            michael,
            jacqui,
            person1_age=35,
            person2_age=32
        )

        # Generate reports
        reporter = ReportGenerator()

        print("\n" + reporter.generate_summary_report(result))
        print("\n" + reporter.generate_category_summary(period))

        # Ask if user wants detailed breakdown
        response = input("\nShow detailed expense breakdown? (y/n): ")
        if response.lower() == 'y':
            print("\n" + reporter.generate_expense_breakdown(period, result))

    except Exception as e:
        print(f"Error importing Excel file: {e}")
        import traceback
        traceback.print_exc()


def calculate_tax_demo():
    """Demonstrate tax calculation."""
    print("\n" + "=" * 80)
    print("TAX CALCULATOR DEMO")
    print("=" * 80 + "\n")

    calculator = TaxCalculator(2024)

    # Example incomes
    incomes = [
        Decimal("50000"),
        Decimal("70000"),
        Decimal("100000"),
        Decimal("150000"),
    ]

    for monthly_income in incomes:
        annual_income = monthly_income * 12
        result = calculator.calculate_monthly_tax(monthly_income)

        print(f"Monthly Income: R{monthly_income:,.2f} (Annual: R{annual_income:,.2f})")
        print(f"  Monthly Tax: R{result.tax_after_rebate:,.2f}")
        print(f"  Monthly UIF: R{result.uif:,.2f}")
        print(f"  Total Deductions: R{result.total_deductions:,.2f}")
        print(f"  Net Income: R{result.net_income:,.2f}")
        print(f"  Effective Rate: {result.effective_tax_rate:.2f}%")
        print()


def interactive_mode():
    """Interactive mode to create a custom financial period."""
    print("\n" + "=" * 80)
    print("INTERACTIVE FINANCIAL SPLIT CALCULATOR")
    print("=" * 80 + "\n")

    # Get person names
    person1_name = input("Enter first person's name: ").strip() or "Person1"
    person2_name = input("Enter second person's name: ").strip() or "Person2"

    person1 = Person(name=person1_name)
    person2 = Person(name=person2_name)

    # Get incomes
    try:
        person1_income = Decimal(input(f"\nEnter {person1_name}'s monthly income (R): ").strip())
        person2_income = Decimal(input(f"Enter {person2_name}'s monthly income (R): ").strip())
    except:
        print("Invalid income amount. Exiting.")
        return

    # Create period
    period = FinancialPeriod(
        period=date.today(),
        people=[person1, person2]
    )

    period.add_income(Income(
        person=person1,
        amount=person1_income,
        income_type=IncomeType.SALARY,
        description="Salary",
        period=date.today()
    ))

    period.add_income(Income(
        person=person2,
        amount=person2_income,
        income_type=IncomeType.SALARY,
        description="Salary",
        period=date.today()
    ))

    # Get shared expenses
    print("\nEnter shared expenses (leave description empty to finish):")
    while True:
        desc = input("  Description: ").strip()
        if not desc:
            break

        try:
            amount = Decimal(input("  Amount (R): ").strip())
            paid_by_name = input(f"  Paid by ({person1_name}/{person2_name}): ").strip()

            paid_by = person1 if paid_by_name.lower() == person1_name.lower() else person2

            period.add_expense(Expense(
                description=desc,
                amount=amount,
                category=ExpenseCategory.OTHER,
                expense_type=ExpenseType.HOUSEHOLD,
                paid_by=paid_by
            ))
            print("  Added!\n")
        except:
            print("  Invalid input, skipping...\n")

    # Calculate and display
    splitter = FinancialSplitter(2024)
    result = splitter.calculate_split(period, person1, person2)

    reporter = ReportGenerator()
    print("\n" + reporter.generate_summary_report(result))


def import_person_sheets(
    person1_file: str,
    person2_file: str,
    person1_name: str = None,
    person2_name: str = None,
    use_checkpoint: bool = True,
    checkpoint_file: str = "financial_checkpoint.json",
    use_net_income: bool = True
):
    """Import from two separate person sheets and generate split report."""
    # Auto-detect names from filenames if not provided
    if not person1_name:
        person1_name = Path(person1_file).stem.split('_')[0]
    if not person2_name:
        person2_name = Path(person2_file).stem.split('_')[0]

    print(f"\n{'='*80}")
    print("IMPORTING HOUSEHOLD FINANCES FROM INDIVIDUAL SHEETS")
    print(f"{'='*80}\n")

    try:
        # Import both sheets
        period = import_household_month(
            person1_file,
            person1_name,
            person2_file,
            person2_name
        )

        # Get person objects
        person1 = period.people[0]
        person2 = period.people[1]

        # Check if this month already exists in checkpoint
        if use_checkpoint:
            manager = CheckpointManager(checkpoint_file)
            if manager.month_exists(period.period):
                print(f"\nWARNING: {period.period.strftime('%B %Y')} already exists in checkpoint!")
                try:
                    response = input("Overwrite existing data? (y/n): ")
                    if response.lower() != 'y':
                        print("Cancelled. Use --force to skip this check.")
                        return
                except EOFError:
                    print("Cancelled (non-interactive mode).")
                    return

        # Calculate split
        print("\nCalculating financial split...\n")
        if use_net_income:
            print("Mode: NET income (take-home pay from payslips)")
            print("Tax calculations skipped - income treated as after-tax\n")
        else:
            print("Mode: GROSS income (before tax)")
            print("Tax will be calculated automatically\n")

        splitter = FinancialSplitter(2024)
        result = splitter.calculate_split(
            period,
            person1,
            person2,
            skip_tax_calculation=use_net_income,
            use_gross_income_for_split=not use_net_income
        )

        # Save to checkpoint
        if use_checkpoint:
            manager.add_monthly_result(result, person1_file, person2_file)
            print(f"\n[OK] Checkpoint saved: {checkpoint_file}")

        # Generate reports
        reporter = ReportGenerator()
        print(reporter.generate_summary_report(result))
        print("\n" + reporter.generate_category_summary(period))

        # Show cumulative summary if checkpoint is used
        if use_checkpoint:
            print("\n" + manager.get_monthly_summary())

        # Offer detailed breakdown
        try:
            response = input("\nShow detailed expense breakdown? (y/n): ")
            if response.lower() == 'y':
                print("\n" + reporter.generate_expense_breakdown(period, result))
        except EOFError:
            pass  # Non-interactive mode

    except Exception as e:
        print(f"Error importing person sheets: {e}")
        import traceback
        traceback.print_exc()


def create_templates(person1_name: str, person2_name: str):
    """Create template Excel files for both people."""
    print(f"\n{'='*80}")
    print("CREATING TEMPLATE SPREADSHEETS")
    print(f"{'='*80}\n")

    from pathlib import Path

    # Create templates
    template1 = f"{person1_name}_Template.xlsx"
    template2 = f"{person2_name}_Template.xlsx"

    create_template_sheets(person1_name, template1)
    create_template_sheets(person2_name, template2)

    print(f"\n{'='*80}")
    print("TEMPLATES CREATED!")
    print(f"{'='*80}")
    print(f"\nNext steps:")
    print(f"1. {person1_name}: Fill in {template1} with your income and expenses")
    print(f"2. {person2_name}: Fill in {template2} with your income and expenses")
    print(f"3. Save as: PersonName_Month_Year.xlsx (e.g., {person1_name}_April_2024.xlsx)")
    print(f"4. Run: python main.py --person-sheets {person1_name}_April_2024.xlsx {person2_name}_April_2024.xlsx")
    print(f"\nIMPORTANT: In 'Expenses' sheet, only list shared costs that YOU paid!")


def parse_bank_statement_cmd(pdf_path: str, template_name: str = None):
    """Parse and display bank statement report."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return

    print(f"\nParsing bank statement: {pdf_path}")
    print("=" * 80)

    try:
        parser = BankStatementParser.create(Path(pdf_path), template_name)
        summary, transactions = parser.parse()
        print(parser.generate_report())
    except Exception as e:
        print(f"Error parsing bank statement: {e}")
        import traceback
        traceback.print_exc()


def export_bank_statement_cmd(pdf_path: str, output_path: str, template_name: str = None):
    """Export bank statement to Excel expense sheet."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return

    print(f"\nExporting bank statement: {pdf_path}")
    print(f"Output file: {output_path}")
    print("=" * 80)

    try:
        parser = BankStatementParser.create(Path(pdf_path), template_name)
        summary, transactions = parser.parse()

        # Determine person name from output path if possible
        output_name = Path(output_path).stem
        person_name = output_name.split('_')[0] if '_' in output_name else "Person"

        parser.export_to_excel(Path(output_path), person_name)

        print(f"\n[OK] Bank statement exported successfully!")
        print(f"\nOutput: {output_path}")
        print(f"\nSummary:")
        print(f"  Total expenses:  R{summary.total_expenses:,.2f}")
        print(f"  Transactions:    {len(parser.get_expenses_only())}")
        print(f"  Statement date:  {summary.statement_date.strftime('%d %b %Y')}")

        print(f"\nNext steps:")
        print(f"1. Open {output_path} in Excel")
        print(f"2. Review the expenses and adjust categories as needed")
        print(f"3. Add income to the Income sheet")
        print(f"4. Use with --person-sheets to process")

    except Exception as e:
        print(f"Error exporting bank statement: {e}")
        import traceback
        traceback.print_exc()


def list_templates_cmd():
    """List all available bank statement templates."""
    from bank_template import TemplateRegistry

    print("\n" + "=" * 80)
    print("AVAILABLE BANK STATEMENT TEMPLATES")
    print("=" * 80 + "\n")

    try:
        registry = TemplateRegistry(Path("bank_templates"))
        templates = registry.list_all()

        if not templates:
            print("No templates found in bank_templates/ directory.")
            print("\nTo create templates, see: docs/BANK_TEMPLATES.md")
            return

        print(f"Found {len(templates)} template(s):\n")

        # Group by bank
        templates_by_bank = {}
        for name, bank, account_type in templates:
            if bank not in templates_by_bank:
                templates_by_bank[bank] = []
            templates_by_bank[bank].append((name, account_type))

        for bank in sorted(templates_by_bank.keys()):
            print(f"  {bank}:")
            for name, account_type in sorted(templates_by_bank[bank]):
                print(f"    • {name:<25} ({account_type})")
            print()

        print("=" * 80)
        print("\nUsage:")
        print("  # Auto-detect template:")
        print("  python main.py --parse-bank-statement statement.pdf")
        print()
        print("  # Specify template manually:")
        print("  python main.py --parse-bank-statement statement.pdf --bank-template fnb_credit_card")
        print()
        print("  # Export with template:")
        print("  python main.py --export-bank-statement statement.pdf output.xlsx --bank-template absa_cheque")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"Error listing templates: {e}")
        import traceback
        traceback.print_exc()


def match_slips_cmd(slips_dir: str, statements: list, output_file: str = None):
    """Parse invoice slips and match to bank statements."""
    print(f"\n{'='*80}")
    print("INVOICE SLIP MATCHING")
    print(f"{'='*80}\n")

    try:
        # Step 1: Parse all slips
        print(f"Step 1: Parsing invoice slips from {slips_dir}...")
        slip_parser = InvoiceSlipParser()
        slip_data = slip_parser.parse_directory(slips_dir)

        print(f"  Parsed {len(slip_data)} slips")

        # Step 2: Parse bank statements
        print(f"\nStep 2: Parsing bank statements...")
        all_transactions = []

        for stmt_path in statements:
            if not os.path.exists(stmt_path):
                print(f"  Warning: Statement not found: {stmt_path}")
                continue

            stmt_name = Path(stmt_path).name
            print(f"  Parsing {stmt_name}...")

            # Determine statement type
            if 'CREDIT_CARD' in stmt_name.upper():
                transactions = BankStmtParser.parse_fnb_credit_card_statement(stmt_path)
            else:
                transactions = BankStmtParser.parse_fnb_personal_account_statement(stmt_path)

            all_transactions.extend(transactions)
            print(f"    Found {len(transactions)} transactions")

        print(f"\n  Total transactions: {len(all_transactions)}")

        # Step 3: Match slips to transactions
        print(f"\nStep 3: Matching slips to transactions...")
        matcher = TransactionMatcher()
        matches, unmatched_slips, unmatched_transactions = matcher.match_slips_to_transactions(
            slip_data,
            all_transactions
        )

        print(f"  Matched: {len(matches)}")
        print(f"  Unmatched slips: {len(unmatched_slips)}")
        print(f"  Unmatched transactions: {len(unmatched_transactions)}")

        # Step 4: Export to Excel
        print(f"\nStep 4: Exporting results to Excel...")
        exporter = SlipMatcherExporter()
        output_path = exporter.export_matching_results(
            matches,
            unmatched_slips,
            unmatched_transactions,
            output_file
        )

        print(f"\n{'='*80}")
        print("MATCHING COMPLETE!")
        print(f"{'='*80}")
        print(f"\nResults saved to: {output_path}")
        print(f"\nSummary:")
        print(f"  Slips processed:      {len(slip_data)}")
        print(f"  Transactions:         {len(all_transactions)}")
        print(f"  Matches:              {len(matches)}")
        print(f"  Match rate:           {len(matches)/len(slip_data)*100:.1f}%" if slip_data else "  Match rate:           N/A")

        if unmatched_slips:
            print(f"\n  Unmatched slips:      {len(unmatched_slips)}")
            print(f"  Review 'Unmatched Slips' sheet in Excel for manual matching")

    except Exception as e:
        print(f"Error matching slips: {e}")
        import traceback
        traceback.print_exc()


def process_statements_cmd(config_path: str, user_dir: str = None, force: bool = False):
    """Process bank statements using config-driven workflow."""
    try:
        from transaction_processor import TransactionProcessor

        # Load config
        config = ConfigManager.load(config_path)

        # Initialize workspace
        workspace = WorkspaceManager(config.working_dir)

        # Create processor
        processor = TransactionProcessor(config, workspace)

        # Run processing
        processor.process_all(force=force, user_filter=user_dir)

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nCreate a config file:")
        print(f"  cp config.json.example config.json")
        print(f"  # Edit config.json with your settings")
        return
    except Exception as e:
        print(f"\nError processing: {e}")
        import traceback
        traceback.print_exc()


def init_workspace_cmd(config_path: str):
    """Initialize workspace folder structure."""
    try:
        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)
        workspace.initialize(create_folders=True)
        print(f"\n[OK] Workspace initialized successfully!")
        print(f"\nFolder structure created:")
        print(f"  {workspace.working_dir}/")
        print(f"  +-- raw/")
        print(f"  |   +-- slips/")
        print(f"  |   +-- statements/")
        print(f"  |   +-- person_sheets/")
        print(f"  +-- processed/")
        print(f"      +-- transactions/")
        print(f"      +-- slips/")
        print(f"      +-- matching/")
        print(f"      +-- monthly_splits/")
        print(f"      +-- checkpoint/")

    except Exception as e:
        print(f"\nError initializing workspace: {e}")


def status_cmd(config_path: str):
    """Show workspace status."""
    try:
        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        print(f"\n{'=' * 80}")
        print("WORKSPACE STATUS")
        print(f"{'=' * 80}\n")

        summary = workspace.get_workspace_summary()

        print(f"Working directory: {summary['working_dir']}")
        print(f"Slips found: {summary['slips']}")
        print(f"\nPersons:")

        for person_name, person_data in summary['persons'].items():
            print(f"  {person_name}:")
            print(f"    Statements: {person_data['statements']}")
            print(f"    Manual file: {'Yes' if person_data['has_manual_file'] else 'No'}")

        # Check processed files
        if workspace.get_all_transactions_file().exists():
            print(f"\n[OK] Processed transactions file exists")
        else:
            print(f"\n[!] No processed transactions yet - run --process-statements")

    except Exception as e:
        print(f"\nError: {e}")


def validate_months_cmd(config_path: str):
    """Validate transaction data completeness by month."""
    try:
        from month_validator import MonthValidator

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)
        validator = MonthValidator()

        # Collect all statement files
        statement_files = {}

        for person_config in config.users:
            folder = workspace.get_person_statements_folder(person_config.name)
            pdfs = workspace.find_statement_pdfs(folder)
            if pdfs:
                statement_files[person_config.name] = pdfs

        for account_config in config.shared_accounts:
            folder = workspace.working_dir / account_config.statements_folder
            pdfs = workspace.find_statement_pdfs(folder)
            if pdfs:
                statement_files[f"Shared: {account_config.name}"] = pdfs

        if not statement_files:
            print("\n[!] No statement files found to validate")
            print("Add PDFs to the statements folders or run --init-workspace first")
            return

        # Validate coverage
        validation_results = validator.validate_statements_coverage(statement_files)

        # Get common complete months
        common_months = validator.get_common_complete_months(validation_results)

        # Generate and print report
        report = validator.generate_validation_report(validation_results, common_months)
        print(f"\n{report}")

        if not common_months:
            print("\n[!] No complete months found")
            print("Ensure all persons/accounts have statement data covering full months")
            print("(from 1st to last day of the month)")
        else:
            print(f"\n[OK] {len(common_months)} complete months ready for processing")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def create_config_cmd(output_path: str = "config.json"):
    """Create a default config file."""
    if Path(output_path).exists():
        response = input(f"{output_path} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    ConfigManager.create_default(output_path)


def add_deferred_payment_cmd(config_path: str):
    """Add a new deferred payment interactively."""
    try:
        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)
        deferred_file = workspace.processed / "deferred_payments.xlsx"

        manager = DeferredPaymentManager(deferred_file)

        print(f"\n{'=' * 80}")
        print("ADD DEFERRED PAYMENT")
        print(f"{'=' * 80}\n")

        # Get input
        description = input("Description: ")
        amount = Decimal(input("Amount (R): "))

        # Category
        print("\nCategories:")
        for i, cat in enumerate(ExpenseCategory, 1):
            print(f"  {i}. {cat.name}")
        cat_choice = int(input("Category number: "))
        category = list(ExpenseCategory)[cat_choice - 1]

        # Expense type
        print("\nExpense type:")
        print("  1. SHARED")
        print("  2. INDIVIDUAL")
        type_choice = int(input("Type (1 or 2): "))
        expense_type = ExpenseType.HOUSEHOLD if type_choice == 1 else ExpenseType.INDIVIDUAL

        # Dates
        accrual_month_str = input("Accrual month (YYYY-MM): ")
        accrual_year, accrual_month = map(int, accrual_month_str.split('-'))
        accrual_month_date = date(accrual_year, accrual_month, 1)

        payment_month_str = input("Expected payment month (YYYY-MM): ")
        payment_year, payment_month = map(int, payment_month_str.split('-'))
        payment_month_date = date(payment_year, payment_month, 1)

        # Person
        print("\nResponsible person:")
        for i, person in enumerate(config.users, 1):
            print(f"  {i}. {person.name}")
        person_choice = int(input("Person number: "))
        responsible_person = config.users[person_choice - 1].name

        reason = input("Reason for deferral: ")
        notes = input("Notes (optional): ")

        # Add deferred payment
        payment = manager.add_deferred_payment(
            description=description,
            amount=amount,
            category=category,
            expense_type=expense_type,
            accrual_month=accrual_month_date,
            responsible_person=responsible_person,
            reason=reason,
            payment_month=payment_month_date,
            notes=notes
        )

        manager.save()

        print(f"\n[OK] Deferred payment added: {payment.payment_id}")
        print(f"File: {deferred_file}")

    except Exception as e:
        print(f"\nError adding deferred payment: {e}")
        import traceback
        traceback.print_exc()


def list_deferred_payments_cmd(config_path: str):
    """List all deferred payments."""
    try:
        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)
        deferred_file = workspace.processed / "deferred_payments.xlsx"

        if not deferred_file.exists():
            print(f"\n[!] No deferred payments file found: {deferred_file}")
            print("Use --add-deferred to create one")
            return

        manager = DeferredPaymentManager(deferred_file)
        print(manager.generate_report())

    except Exception as e:
        print(f"\nError listing deferred payments: {e}")


def calculate_split_cmd(config_path: str, excel_files: list = None):
    """Calculate fair share split from classified transaction files."""
    try:
        from split_calculator import FinancialSplitter
        from reports import ReportGenerator

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)
        checkpoint = CheckpointManager(
            str(workspace.processed / "checkpoint" / "split_checkpoint.json")
        )

        print(f"\n{'=' * 80}")
        print("FAIR SHARE CALCULATION")
        print(f"{'=' * 80}\n")

        # Determine which files to use
        if excel_files:
            # Use specified files
            if len(excel_files) != 2:
                print("[!] Error: Please specify exactly 2 transaction files")
                return
            file1, file2 = excel_files
            print(f"Using specified files:")
            print(f"  Person 1: {file1}")
            print(f"  Person 2: {file2}")
        else:
            # Use files from config
            if len(config.users) != 2:
                print("[!] Error: Config must have exactly 2 users for fair share calculation")
                return

            # For multi-account support, we need to aggregate all accounts per user
            print(f"Loading accounts for {config.users[0].name}...")
            user1_dfs = []
            for account in config.users[0].accounts:
                # Try to find classified transaction files for all months
                # Use a glob pattern to find all month folders
                processed_base = workspace.working_dir / account.processed_folder
                if processed_base.exists():
                    for month_folder in processed_base.glob("*"):
                        if month_folder.is_dir():
                            classified_folder = month_folder / "classified"
                            if classified_folder.exists():
                                for file in classified_folder.glob("*.xlsx"):
                                    print(f"  Loading: {file.name}")
                                    try:
                                        df = pd.read_excel(file)
                                        df['account'] = account.name
                                        user1_dfs.append(df)
                                    except Exception as e:
                                        print(f"  [!] Error loading {file}: {e}")

            print(f"Loading accounts for {config.users[1].name}...")
            user2_dfs = []
            for account in config.users[1].accounts:
                processed_base = workspace.working_dir / account.processed_folder
                if processed_base.exists():
                    for month_folder in processed_base.glob("*"):
                        if month_folder.is_dir():
                            classified_folder = month_folder / "classified"
                            if classified_folder.exists():
                                for file in classified_folder.glob("*.xlsx"):
                                    print(f"  Loading: {file.name}")
                                    try:
                                        df = pd.read_excel(file)
                                        df['account'] = account.name
                                        user2_dfs.append(df)
                                    except Exception as e:
                                        print(f"  [!] Error loading {file}: {e}")

            if not user1_dfs or not user2_dfs:
                print("[!] Error: No transaction files found. Run --process-statements first")
                return

        print("\nAggregating transaction data...")

        # Combine all accounts per user
        import pandas as pd
        df1 = pd.concat(user1_dfs, ignore_index=True) if user1_dfs else pd.DataFrame()
        df2 = pd.concat(user2_dfs, ignore_index=True) if user2_dfs else pd.DataFrame()

        print(f"  {config.users[0].name}: {len(df1)} transactions across {len(user1_dfs)} file(s)")
        print(f"  {config.users[1].name}: {len(df2)} transactions across {len(user2_dfs)} file(s)")

        # Group by month
        df1['month'] = pd.to_datetime(df1['date']).dt.to_period('M')
        df2['month'] = pd.to_datetime(df2['date']).dt.to_period('M')

        # Get unique months
        months1 = set(df1['month'].unique())
        months2 = set(df2['month'].unique())
        common_months = sorted(months1 & months2)

        if not common_months:
            print("\n[!] No common months found in transaction files")
            return

        print(f"Found {len(common_months)} common months: {', '.join(str(m) for m in common_months)}")

        # Calculate split for each month
        monthly_results = []
        cumulative_person1_paid = Decimal("0")
        cumulative_person2_paid = Decimal("0")

        for month_period in common_months:
            print(f"\nProcessing {month_period}...")

            # Filter transactions for this month
            month_df1 = df1[df1['month'] == month_period]
            month_df2 = df2[df2['month'] == month_period]

            # Calculate totals with split handling
            person1_income = month_df1[month_df1['final_type'] == 'INCOME']['amount'].sum() if 'final_type' in month_df1.columns else 0
            person2_income = month_df2[month_df2['final_type'] == 'INCOME']['amount'].sum() if 'final_type' in month_df2.columns else 0

            # Calculate household expenses with split handling
            # Person 1's household amount
            person1_household = 0
            for _, row in month_df1.iterrows():
                if row['final_type'] == 'HOUSEHOLD':
                    # Full amount is household
                    person1_household += row['amount']
                elif row['final_type'] == 'Individual' and pd.notna(row.get('split_amount', 0)) and row.get('split_to', '') == 'HOUSEHOLD':
                    # Part of individual transaction mapped to household
                    person1_household += row['split_amount']

            # Person 2's household amount
            person2_household = 0
            for _, row in month_df2.iterrows():
                if row['final_type'] == 'HOUSEHOLD':
                    # Full amount is household
                    person2_household += row['amount']
                elif row['final_type'] == 'Individual' and pd.notna(row.get('split_amount', 0)) and row.get('split_to', '') == 'HOUSEHOLD':
                    # Part of individual transaction mapped to household
                    person2_household += row['split_amount']

            total_income = Decimal(str(person1_income)) + Decimal(str(person2_income))
            total_household = Decimal(str(person1_household)) + Decimal(str(person2_household))

            if total_income > 0:
                person1_proportion = Decimal(str(person1_income)) / total_income
                person2_proportion = Decimal(str(person2_income)) / total_income
            else:
                person1_proportion = Decimal("0.5")
                person2_proportion = Decimal("0.5")

            person1_should_pay = total_household * person1_proportion
            person2_should_pay = total_household * person2_proportion

            person1_balance = Decimal(str(person1_household)) - person1_should_pay
            person2_balance = Decimal(str(person2_household)) - person2_should_pay

            # Determine transfer
            if person1_balance > 0:
                transfer_from = config.users[1].name if not excel_files else "Person 2"
                transfer_to = config.users[0].name if not excel_files else "Person 1"
                transfer_amount = abs(person1_balance)
            else:
                transfer_from = config.users[0].name if not excel_files else "Person 1"
                transfer_to = config.users[1].name if not excel_files else "Person 2"
                transfer_amount = abs(person2_balance)

            cumulative_person1_paid += Decimal(str(person1_household))
            cumulative_person2_paid += Decimal(str(person2_household))

            monthly_results.append({
                'month': str(month_period),
                'person1_income': person1_income,
                'person2_income': person2_income,
                'person1_proportion': float(person1_proportion),
                'person2_proportion': float(person2_proportion),
                'total_household': float(total_household),
                'person1_paid': float(person1_household),
                'person2_paid': float(person2_household),
                'person1_should_pay': float(person1_should_pay),
                'person2_should_pay': float(person2_should_pay),
                'transfer_from': transfer_from,
                'transfer_to': transfer_to,
                'transfer_amount': float(transfer_amount)
            })

        # Output results
        print(f"\n{'=' * 80}")
        print("MONTHLY BREAKDOWN")
        print(f"{'=' * 80}\n")

        for result in monthly_results:
            print(f"{result['month']}:")
            print(f"  Income: {config.users[0].name if not excel_files else 'Person 1'} R{result['person1_income']:,.2f} ({result['person1_proportion']:.1%}) | "
                  f"{config.users[1].name if not excel_files else 'Person 2'} R{result['person2_income']:,.2f} ({result['person2_proportion']:.1%})")
            print(f"  Total Household Expenses: R{result['total_household']:,.2f}")
            print(f"  Transfer: {result['transfer_from']} → {result['transfer_to']}: R{result['transfer_amount']:,.2f}")
            print()

        # Cumulative summary
        cumulative_diff = cumulative_person1_paid - cumulative_person2_paid
        print(f"{'=' * 80}")
        print("CUMULATIVE SUMMARY")
        print(f"{'=' * 80}\n")
        print(f"Total paid by {config.users[0].name if not excel_files else 'Person 1'}: R{cumulative_person1_paid:,.2f}")
        print(f"Total paid by {config.users[1].name if not excel_files else 'Person 2'}: R{cumulative_person2_paid:,.2f}")
        if cumulative_diff > 0:
            print(f"\n** NET: {config.users[1].name if not excel_files else 'Person 2'} should transfer R{abs(cumulative_diff):,.2f} to {config.users[0].name if not excel_files else 'Person 1'} **")
        else:
            print(f"\n** NET: {config.users[0].name if not excel_files else 'Person 1'} should transfer R{abs(cumulative_diff):,.2f} to {config.users[1].name if not excel_files else 'Person 2'} **")

        # Save to Excel
        output_file = workspace.processed / "fair_share_calculation.xlsx"
        results_df = pd.DataFrame(monthly_results)
        results_df.to_excel(output_file, index=False)
        print(f"\nResults saved to: {output_file}")

    except Exception as e:
        print(f"\nError calculating split: {e}")
        import traceback
        traceback.print_exc()


def mark_deferred_paid_cmd(config_path: str, payment_id: str):
    """Mark a deferred payment as paid."""
    try:
        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)
        deferred_file = workspace.processed / "deferred_payments.xlsx"

        if not deferred_file.exists():
            print(f"\n[!] No deferred payments file found: {deferred_file}")
            return

        manager = DeferredPaymentManager(deferred_file)

        # Find the payment
        payment = None
        for p in manager.payments:
            if p.payment_id == payment_id:
                payment = p
                break

        if not payment:
            print(f"\n[!] Payment not found: {payment_id}")
            return

        print(f"\nMarking as paid: {payment.description}")
        print(f"Amount: R{payment.amount}")

        # Get who paid
        print("\nWho paid?")
        for i, person in enumerate(config.users, 1):
            print(f"  {i}. {person.name}")
        person_choice = int(input("Person number: "))
        paid_by = config.users[person_choice - 1].name

        # Get payment month
        payment_month_str = input("Payment month (YYYY-MM, or Enter for current): ")
        if payment_month_str:
            payment_year, payment_month = map(int, payment_month_str.split('-'))
            payment_month_date = date(payment_year, payment_month, 1)
        else:
            today = date.today()
            payment_month_date = date(today.year, today.month, 1)

        manager.mark_as_paid(payment_id, paid_by, payment_month_date)
        manager.save()

        print(f"\n[OK] Payment marked as paid")
        print(f"Paid by: {paid_by}")
        print(f"Payment month: {payment_month_date.strftime('%Y-%m')}")

    except Exception as e:
        print(f"\nError marking payment as paid: {e}")
        import traceback
        traceback.print_exc()


def list_categories_cmd(config_path: str):
    """List all expense categories."""
    try:
        from category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        categories_file = workspace.processed / "categories.json"
        cat_mgr = CategoryManager(categories_file)

        cat_mgr.list_categories()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def add_category_cmd(config_path: str, key: str, display_name: str):
    """Add a new expense category."""
    try:
        from category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        categories_file = workspace.processed / "categories.json"
        cat_mgr = CategoryManager(categories_file)

        # Convert key to uppercase with underscores
        key = key.upper().replace(" ", "_").replace("-", "_")

        if cat_mgr.add_category(key, display_name):
            print(f"\n[OK] Added category: {key} => {display_name}")
            print(f"Total categories: {len(cat_mgr.get_all_categories())}")
        else:
            print(f"\n[!] Category '{key}' already exists")
            print(f"Use --remove-category {key} first, or use a different key")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def remove_category_cmd(config_path: str, key: str):
    """Remove an expense category."""
    try:
        from category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        categories_file = workspace.processed / "categories.json"
        cat_mgr = CategoryManager(categories_file)

        key = key.upper()

        if cat_mgr.remove_category(key):
            print(f"\n[OK] Removed category: {key}")
            print(f"Total categories: {len(cat_mgr.get_all_categories())}")
        else:
            print(f"\n[!] Category '{key}' not found")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def rename_category_cmd(config_path: str, old_key: str, new_key: str, new_display_name: str = None):
    """Rename an expense category."""
    try:
        from category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        categories_file = workspace.processed / "categories.json"
        cat_mgr = CategoryManager(categories_file)

        old_key = old_key.upper()
        new_key = new_key.upper().replace(" ", "_").replace("-", "_")

        if cat_mgr.rename_category(old_key, new_key, new_display_name):
            display = new_display_name or cat_mgr.get_category_display_name(new_key)
            print(f"\n[OK] Renamed category: {old_key} => {new_key} ({display})")
        else:
            print(f"\n[!] Could not rename category '{old_key}'")
            print(f"Make sure it exists and '{new_key}' is not already taken")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def learn_from_corrections_cmd(config_path: str):
    """Learn classification rules from user corrections."""
    try:
        from src.learned_classifier import LearnedClassifier
        from src.category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        print(f"\n{'=' * 80}")
        print("LEARN FROM USER CORRECTIONS")
        print(f"{'=' * 80}\n")

        # Initialize category manager and learned classifier
        categories_file = workspace.processed / "categories.json"
        category_manager = CategoryManager(categories_file)
        learned_rules_path = workspace.processed / "learned_rules.json"
        classifier = LearnedClassifier(learned_rules_path, category_manager)

        # Find all transaction files (monthly structure, multi-account)
        transaction_files = []

        # Add user account monthly transaction files
        for user in config.users:
            for account in user.accounts:
                processed_folder = workspace.working_dir / account.processed_folder
                if processed_folder.exists():
                    # Find all monthly classified files
                    for monthly_folder in sorted(processed_folder.glob("????-??")):
                        if monthly_folder.is_dir():
                            classified_folder = monthly_folder / "classified"
                            if classified_folder.exists():
                                for file in classified_folder.glob("*.xlsx"):
                                    transaction_files.append(file)

        # Add shared account monthly files
        for account in config.shared_accounts:
            shared_folder = workspace.get_shared_transactions_folder(account.name)
            if shared_folder.exists():
                # Find all monthly classified files
                for monthly_folder in sorted(shared_folder.glob("????-??")):
                    if monthly_folder.is_dir():
                        safe_name = account.name.replace(" ", "_").lower()
                        classified_file = monthly_folder / f"{safe_name}_classified.xlsx"
                        if classified_file.exists():
                            transaction_files.append(classified_file)

        if not transaction_files:
            print("[!] No transaction files found")
            print("Run --process-statements first to generate transaction files")
            return

        # Learn from all files
        stats = classifier.learn_from_all_files(transaction_files, verbose=True)

        print(f"\n{'=' * 80}")
        print("LEARNING COMPLETE")
        print(f"{'=' * 80}")
        print(f"\nNew rules learned: {stats['new_rules']}")
        print(f"Existing rules updated: {stats['updated_rules']}")
        print(f"\nLearned rules saved to: {learned_rules_path}")
        print("\nNext time you run --process-statements, these learned rules will be")
        print("automatically applied to classify similar transactions!")

    except Exception as e:
        print(f"\nError learning from corrections: {e}")
        import traceback
        traceback.print_exc()


def export_learned_rules_cmd(config_path: str, output_file: str):
    """Export learned rules to Excel for review."""
    try:
        from src.learned_classifier import LearnedClassifier
        from src.category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        categories_file = workspace.processed / "categories.json"
        category_manager = CategoryManager(categories_file)
        learned_rules_path = workspace.processed / "learned_rules.json"
        classifier = LearnedClassifier(learned_rules_path, category_manager)

        from pathlib import Path
        output_path = Path(output_file)
        classifier.export_rules(output_path)

        print(f"\nLearned rules exported to: {output_path}")

    except Exception as e:
        print(f"\nError exporting learned rules: {e}")
        import traceback
        traceback.print_exc()


def apply_learned_rules_cmd(config_path: str):
    """Apply learned rules to re-classify existing transaction files."""
    try:
        from src.learned_classifier import LearnedClassifier
        from src.category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        print(f"\n{'=' * 80}")
        print("APPLY LEARNED RULES TO EXISTING TRANSACTIONS")
        print(f"{'=' * 80}\n")

        # Initialize category manager and learned classifier
        categories_file = workspace.processed / "categories.json"
        category_manager = CategoryManager(categories_file)
        learned_rules_path = workspace.processed / "learned_rules.json"
        classifier = LearnedClassifier(learned_rules_path, category_manager)

        # Check if there are any learned rules
        if not classifier.rules:
            print("[!] No learned rules found in learned_rules.json")
            print("Run --learn-from-corrections first to create learned rules")
            return

        print(f"Loaded {len(classifier.rules)} learned rules")
        print()

        # Find all transaction files (monthly structure, multi-account)
        transaction_files = []

        # Add user account monthly transaction files
        for user in config.users:
            for account in user.accounts:
                processed_folder = workspace.working_dir / account.processed_folder
                if processed_folder.exists():
                    for monthly_folder in sorted(processed_folder.glob("????-??")):
                        if monthly_folder.is_dir():
                            classified_folder = monthly_folder / "classified"
                            if classified_folder.exists():
                                for file in classified_folder.glob("*.xlsx"):
                                    transaction_files.append(file)

        # Add shared account monthly files
        for account in config.shared_accounts:
            shared_folder = workspace.get_shared_transactions_folder(account.name)
            if shared_folder.exists():
                for monthly_folder in sorted(shared_folder.glob("????-??")):
                    if monthly_folder.is_dir():
                        safe_name = account.name.replace(" ", "_").lower()
                        classified_file = monthly_folder / f"{safe_name}_classified.xlsx"
                        if classified_file.exists():
                            transaction_files.append(classified_file)

        if not transaction_files:
            print("[!] No transaction files found")
            print("Run --process-statements first to generate transaction files")
            return

        print(f"Found {len(transaction_files)} transaction files to process")

        # Apply learned rules to all files
        stats = classifier.apply_to_all_files(transaction_files, verbose=True)

        print(f"\n{'=' * 80}")
        print("APPLICATION COMPLETE")
        print(f"{'=' * 80}\n")

        print(f"Files updated: {stats['files_updated']}")
        print(f"Transactions reclassified: {stats['reclassified']}")
        print(f"Transactions unchanged: {stats['unchanged']}")
        print()
        print("Auto-classifications have been updated in all transaction files.")
        print("User corrections were preserved and remain unchanged.")

    except Exception as e:
        print(f"\nError applying learned rules: {e}")
        import traceback
        traceback.print_exc()


def show_learned_stats_cmd(config_path: str):
    """Show statistics about learned classification rules."""
    try:
        from src.learned_classifier import LearnedClassifier
        from src.category_manager import CategoryManager

        config = ConfigManager.load(config_path)
        workspace = WorkspaceManager(config.working_dir)

        categories_file = workspace.processed / "categories.json"
        category_manager = CategoryManager(categories_file)
        learned_rules_path = workspace.processed / "learned_rules.json"
        classifier = LearnedClassifier(learned_rules_path, category_manager)

        stats = classifier.get_statistics()

        print(f"\n{'=' * 80}")
        print("LEARNED CLASSIFICATION RULES STATISTICS")
        print(f"{'=' * 80}\n")

        print(f"Total learned rules: {stats['total_rules']}")

        if stats['total_rules'] > 0:
            print(f"\nRules file: {learned_rules_path}")

            print("\nBy Category:")
            for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {category}: {count}")

            print("\nBy Type:")
            for exp_type, count in sorted(stats['types'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {exp_type}: {count}")

            print("\nTo export rules to Excel for review:")
            print(f"  uv run fairshare --export-learned-rules learned_rules.xlsx")
        else:
            print("\nNo learned rules yet!")
            print("Edit your transaction files and add corrections in the user_category")
            print("and user_type columns, then run:")
            print("  uv run fairshare --learn-from-corrections")

    except Exception as e:
        print(f"\nError showing statistics: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="FairShare - Household Finance Splitting System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  MAIN WORKFLOW:
  python fairshare.py --create-config                    Create config.json
  python fairshare.py --init-workspace                   Initialize folders
  python fairshare.py --validate-months                  Check data completeness
  python fairshare.py --process-statements               Process all users
  python fairshare.py --process-statements --user-dir Michael    Process one user
  python fairshare.py --calculate-split                  Calculate fair share

  DEFERRED PAYMENTS:
  python fairshare.py --add-deferred                     Add deferred payment
  python fairshare.py --list-deferred                    List pending payments
  python fairshare.py --mark-paid DEF202509150001        Mark payment as paid

  LEGACY COMMANDS:
  python fairshare.py --demo                             Run demo example
  python fairshare.py --person-sheets file1.xlsx file2.xlsx    Old workflow
        """
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo example"
    )

    parser.add_argument(
        "--import",
        dest="excel_file",
        type=str,
        help="Import from Excel file"
    )

    parser.add_argument(
        "--tax",
        action="store_true",
        help="Show tax calculation demo"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode"
    )

    parser.add_argument(
        "--create-templates",
        nargs=2,
        metavar=("PERSON1", "PERSON2"),
        help="Create template spreadsheets for two people"
    )

    parser.add_argument(
        "--person-sheets",
        nargs='*',
        metavar="FILE",
        help="Import from two separate person sheets (auto-detects if no files provided)"
    )

    parser.add_argument(
        "--next",
        action="store_true",
        help="Process next month automatically (uses checkpoint to find files)"
    )

    parser.add_argument(
        "--checkpoint-summary",
        action="store_true",
        help="Show checkpoint summary with cumulative transfers"
    )

    parser.add_argument(
        "--reset-checkpoint",
        action="store_true",
        help="Reset checkpoint data"
    )

    parser.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Don't save to checkpoint"
    )

    parser.add_argument(
        "--checkpoint-file",
        type=str,
        default="financial_checkpoint.json",
        help="Checkpoint file path (default: financial_checkpoint.json)"
    )

    parser.add_argument(
        "--use-gross",
        action="store_true",
        help="Use GROSS income mode (calculate tax automatically). Default is NET income mode."
    )

    parser.add_argument(
        "--parse-bank-statement",
        metavar="PDF_FILE",
        help="Parse a bank statement PDF and show expense report"
    )

    parser.add_argument(
        "--export-bank-statement",
        nargs=2,
        metavar=("PDF_FILE", "OUTPUT_XLSX"),
        help="Export bank statement to Excel expense sheet (PDF_FILE OUTPUT_XLSX)"
    )

    parser.add_argument(
        "--bank-template",
        metavar="TEMPLATE_NAME",
        help="Specify bank template for parsing (e.g., fnb_credit_card, absa_cheque)"
    )

    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List all available bank statement templates"
    )

    parser.add_argument(
        "--match-slips",
        action="store_true",
        help="Match invoice slips to bank statement transactions"
    )

    parser.add_argument(
        "--slips-dir",
        type=str,
        default="data/slips",
        help="Directory containing invoice slip PDFs/images (default: data/slips)"
    )

    parser.add_argument(
        "--statements",
        nargs='+',
        metavar="STATEMENT_PDF",
        help="Bank statement PDFs to match against"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output Excel file path for matching results"
    )

    # New config-driven commands
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to config file (default: config.json)"
    )

    parser.add_argument(
        "--process-statements",
        action="store_true",
        help="Process bank statements (parse, classify, export to Excel)"
    )

    parser.add_argument(
        "--user-dir",
        type=str,
        help="Process statements for specific user only (use with --process-statements)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of all files (use with --process-statements)"
    )

    parser.add_argument(
        "--init-workspace",
        action="store_true",
        help="Initialize workspace folder structure"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show workspace status"
    )

    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a default config.json file"
    )

    parser.add_argument(
        "--validate-months",
        action="store_true",
        help="Validate transaction data completeness by month"
    )

    # Deferred payment commands
    parser.add_argument(
        "--add-deferred",
        action="store_true",
        help="Add a new deferred payment interactively"
    )

    parser.add_argument(
        "--list-deferred",
        action="store_true",
        help="List all deferred payments"
    )

    parser.add_argument(
        "--mark-paid",
        metavar="PAYMENT_ID",
        type=str,
        help="Mark a deferred payment as paid (provide payment ID)"
    )

    # Fair share calculation
    parser.add_argument(
        "--calculate-split",
        nargs='*',
        metavar="EXCEL_FILE",
        help="Calculate fair share split from classified transactions (optionally specify files)"
    )

    # Category management
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all expense categories"
    )

    parser.add_argument(
        "--add-category",
        nargs=2,
        metavar=("KEY", "DISPLAY_NAME"),
        help="Add a new expense category (e.g., DISCRETIONARY_DINING \"Discretionary Dining\")"
    )

    parser.add_argument(
        "--remove-category",
        metavar="KEY",
        type=str,
        help="Remove an expense category"
    )

    parser.add_argument(
        "--rename-category",
        nargs='+',
        metavar="ARG",
        help="Rename a category: OLD_KEY NEW_KEY [NEW_DISPLAY_NAME] (display name optional)"
    )

    # Learning from corrections
    parser.add_argument(
        "--learn-from-corrections",
        action="store_true",
        help="Learn classification rules from user corrections in transaction files"
    )

    parser.add_argument(
        "--apply-learned-rules",
        action="store_true",
        help="Apply learned rules to re-classify existing transaction files"
    )

    parser.add_argument(
        "--export-learned-rules",
        metavar="OUTPUT_FILE",
        type=str,
        help="Export learned rules to Excel file for review"
    )

    parser.add_argument(
        "--show-learned-stats",
        action="store_true",
        help="Show statistics about learned classification rules"
    )

    args = parser.parse_args()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n" + "=" * 80)
        print("TIP: Quick start:")
        print("  1. python fairshare.py --create-config")
        print("  2. python fairshare.py --init-workspace")
        print("  3. Add your bank statements to data/raw/statements/")
        print("  4. python fairshare.py --process-statements")
        print("  5. python fairshare.py --calculate-split")
        print("=" * 80)
        return

    # Handle new config-driven commands first
    if args.create_config:
        create_config_cmd(args.config)
        return

    # NOTE: Commands below disabled - they use deleted modules (WorkspaceManager, CategoryManager, TransactionProcessor)
    # if args.init_workspace:
    #     init_workspace_cmd(args.config)
    #     return
    #
    # if args.status:
    #     status_cmd(args.config)
    #     return
    #
    # if args.validate_months:
    #     validate_months_cmd(args.config)
    #     return
    #
    # if args.process_statements:
    #     process_statements_cmd(args.config, user_dir=args.user_dir, force=args.force)
    #     return
    #
    # if args.calculate_split is not None:
    #     calculate_split_cmd(args.config, args.calculate_split if args.calculate_split else None)
    #     return
    #
    # # Handle deferred payment commands
    # if args.add_deferred:
    #     add_deferred_payment_cmd(args.config)
    #     return
    #
    # if args.list_deferred:
    #     list_deferred_payments_cmd(args.config)
    #     return
    #
    # if args.mark_paid:
    #     mark_deferred_paid_cmd(args.config, args.mark_paid)
    #     return
    #
    # # Handle category management commands
    # if args.list_categories:
    #     list_categories_cmd(args.config)
    #     return
    #
    # if args.add_category:
    #     add_category_cmd(args.config, args.add_category[0], args.add_category[1])
    #     return
    #
    # if args.remove_category:
    #     remove_category_cmd(args.config, args.remove_category)
    #     return
    #
    # if args.rename_category:
    #     if len(args.rename_category) < 2:
    #         print("[!] Error: --rename-category requires at least OLD_KEY and NEW_KEY")
    #         return
    #     old_key = args.rename_category[0]
    #     new_key = args.rename_category[1]
    #     new_display = args.rename_category[2] if len(args.rename_category) > 2 else None
    #     rename_category_cmd(args.config, old_key, new_key, new_display)
    #     return
    #
    # # Handle learning commands
    # if args.learn_from_corrections:
    #     learn_from_corrections_cmd(args.config)
    #     return
    #
    # if args.apply_learned_rules:
    #     apply_learned_rules_cmd(args.config)
    #     return
    #
    # if args.export_learned_rules:
    #     export_learned_rules_cmd(args.config, args.export_learned_rules)
    #     return
    #
    # if args.show_learned_stats:
    #     show_learned_stats_cmd(args.config)
    #     return

    # Handle checkpoint operations
    if args.reset_checkpoint:
        manager = CheckpointManager(args.checkpoint_file)
        manager.reset()
        return

    if args.checkpoint_summary:
        manager = CheckpointManager(args.checkpoint_file)
        print(manager.get_monthly_summary())
        return

    # Regular operations
    if args.demo:
        demo_example()

    if args.excel_file:
        import_from_excel(args.excel_file)

    # NOTE: --tax command disabled - uses TaxCalculator (deleted)
    # if args.tax:
    #     calculate_tax_demo()

    if args.interactive:
        interactive_mode()

    if args.create_templates:
        create_templates(args.create_templates[0], args.create_templates[1])

    if args.list_templates:
        list_templates_cmd()
        return

    if args.parse_bank_statement:
        template_name = getattr(args, 'bank_template', None)
        parse_bank_statement_cmd(args.parse_bank_statement, template_name)
        return

    if args.export_bank_statement:
        template_name = getattr(args, 'bank_template', None)
        export_bank_statement_cmd(args.export_bank_statement[0], args.export_bank_statement[1], template_name)
        return

    # NOTE: --match-slips command disabled - uses InvoiceSlipParser, TransactionMatcher, etc. (deleted)
    # if args.match_slips:
    #     if not args.statements:
    #         print("Error: --match-slips requires --statements to be specified")
    #         print("Usage: python main.py --match-slips --statements statement1.pdf statement2.pdf")
    #         return
    #     match_slips_cmd(args.slips_dir, args.statements, args.output)
    #     return

    if args.next or (args.person_sheets is not None and len(args.person_sheets) == 0):
        # Auto-detect next month's files
        print("\nAuto-detecting next month's files from checkpoint...")
        next_files = auto_detect_next_month_files(args.checkpoint_file)

        if next_files:
            file1, file2 = next_files
            print(f"  Expected files:")
            print(f"    - {file1}")
            print(f"    - {file2}")

            # Check if files exist
            if Path(file1).exists() and Path(file2).exists():
                print(f"  [OK] Files found!\n")
                import_person_sheets(
                    file1,
                    file2,
                    use_checkpoint=not args.no_checkpoint,
                    checkpoint_file=args.checkpoint_file,
                    use_net_income=True  # Always use NET mode (--use-gross removed)
                )
            else:
                print(f"\n  [X] Files not found.")
                if not Path(file1).exists():
                    print(f"    Missing: {file1}")
                if not Path(file2).exists():
                    print(f"    Missing: {file2}")
                print(f"\n  Create these files and run again, or specify files explicitly:")
                print(f"  python main.py --person-sheets FILE1 FILE2")
        else:
            print("  No checkpoint data found. Process at least one month first.")
            print("  Example: python main.py --person-sheets Person1_Jan_2024.xlsx Person2_Jan_2024.xlsx")

    elif args.person_sheets and len(args.person_sheets) == 2:
        import_person_sheets(
            args.person_sheets[0],
            args.person_sheets[1],
            use_checkpoint=not args.no_checkpoint,
            checkpoint_file=args.checkpoint_file,
            use_net_income=True  # Always use NET mode (--use-gross removed)
        )
    elif args.person_sheets and len(args.person_sheets) != 2:
        print("Error: --person-sheets requires exactly 2 files or no files (for auto-detect)")
        print("Usage:")
        print("  python main.py --person-sheets FILE1 FILE2")
        print("  python main.py --person-sheets    (auto-detect next month)")
        print("  python main.py --next             (auto-detect next month)")


if __name__ == "__main__":
    main()
