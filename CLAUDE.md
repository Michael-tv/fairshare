# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ IMPORTANT: Simplified Codebase

**This codebase has been streamlined to focus on core fair share functionality.**

**Features REMOVED (moved to separate project):**
- Tax calculation (GROSS mode) - `tax_calculator.py` deleted
- Invoice slip matching & OCR - `invoice_slip_parser.py`, `transaction_matcher.py`, `slip_matcher_exporter.py` deleted
- Automated transaction processing pipeline - `transaction_processor.py`, `workspace_manager.py` deleted
- Dynamic category management - `category_manager.py` deleted (now uses static categories)
- Home & History GUI tabs - `home_tab.py`, `history_tab.py` deleted

**Core Features KEPT:**
- Fair share splitting logic (NET income mode only)
- Bank statement parsing (`bank_statement_parser.py`)
- Person sheet workflow (`person_sheet_importer.py`)
- Transaction classification - Household vs Personal (`transaction_classifier.py`)
- Learned classification rules with fuzzy matching (`learned_classifier.py`)
- Checkpoint system (`checkpoint_manager.py`)
- Deferred payment tracking (`deferred_payment_manager.py`)
- Month validation (`month_validator.py`)
- Excel importers (`excel_importer.py`)
- Core GUI tabs: Process Month, Templates, Settings

## Project Overview

A Python-based household finance splitting system that fairly divides expenses between partners based on proportional income.

**Key Concept**: Instead of 50/50 splits, expenses are divided proportionally based on each person's income (e.g., if one person earns 70% of household income, they pay 70% of shared costs).

## Core Architecture

### Data Flow
```
Person Excel Sheets → PersonSheetImporter → FinancialPeriod (models)
→ FinancialSplitter (split_calculator) → SplitResult
→ ReportGenerator → Console Output + CheckpointManager (persistent state)
```

### Key Components

**Data Models** ([models.py](src/models.py))
- `Person`: Represents each partner in the household
- `Income`: Income sources (salary, rental, business, investment, other)
- `Expense`: Expense items with three types:
  - `SHARED`: Split proportionally between partners (groceries, utilities, etc.)
  - `INDIVIDUAL`: Belongs to one person only (personal car payment)
  - `DEDUCTION`: Tax/UIF deductions from gross income
- `FinancialPeriod`: Container for a month's income and expenses
- `SplitResult`: Complete calculation result with settlement details

**Split Logic** ([split_calculator.py](src/split_calculator.py))
- **NET mode**: Income is take-home pay, no tax calculations
- Proportional splitting based on net income
- Settlement algorithm: compares what each person should pay vs. actually paid

**Import System**
- [person_sheet_importer.py](src/person_sheet_importer.py): New workflow - each person has their own Excel file
- [excel_importer.py](src/excel_importer.py): Legacy importer for old combined spreadsheet format
- [bank_statement_parser.py](src/bank_statement_parser.py): Template-driven PDF bank statement parser supporting any bank
- [bank_template.py](src/bank_template.py): YAML-based template system for multi-bank support

**Checkpoint System** ([checkpoint_manager.py](src/checkpoint_manager.py))
- Saves each month's results to `financial_checkpoint.json`
- Tracks cumulative transfers across all months
- Auto-detects next month's files based on naming patterns (e.g., `Name_April_2024.xlsx` → `Name_May_2024.xlsx`)
- Prevents duplicate month processing

**Reports** ([reports.py](src/reports.py))
- Summary report: Income, proportions, settlement
- Expense breakdown: Detailed expense listing
- Category summary: Expenses grouped by category

## Configuration & Account Structure

**Config File** ([config.json](config.json))
The system uses a centralized configuration file managed by [config_manager.py](src/config_manager.py) that defines:
- Working directory for all data files
- Users and their accounts
- Shared accounts (joint accounts between users)
- Matching and classification settings

**User Structure**
Each user has:
- `id`: Unique identifier (e.g., "user_1")
- `name`: Display name
- `person_sheet_path`: Path to their monthly Excel file
- `accounts`: List of account configurations

**Account Structure**
Each account (both user and shared) requires:
- `name`: Account name (e.g., "Main Bank Account", "Credit Card")
- `account_type`: Type from enum - `personal`, `credit_card`, `savings`, `investment`, `loan`, or `other`
- `statements_folder`: Path to raw bank statement PDFs (relative to working_dir)
- `processed_folder`: Path for processed transaction files (relative to working_dir)

**Account Types** ([config_manager.py](src/config_manager.py))
```python
class AccountType(Enum):
    PERSONAL = "personal"        # Personal bank accounts
    CREDIT_CARD = "credit_card"  # Credit cards
    SAVINGS = "savings"          # Savings accounts
    INVESTMENT = "investment"    # Investment/brokerage accounts
    LOAN = "loan"                # Loans, mortgages
    OTHER = "other"              # Other account types
```

**Folder Structure**
Each account's processed_folder contains month-specific subfolders:
```
{processed_folder}/
  ├── {YYYY-MM}/
  │   ├── raw/
  │   │   └── {account_name}_raw_extracted.xlsx
  │   └── classified/
  │       └── {account_name}_classified.xlsx
```

**Example Configuration**
```json
{
  "working_dir": "data",
  "users": [
    {
      "id": "user_1",
      "name": "Michael",
      "person_sheet_path": "data/person_sheets/Michael_2024_11.xlsx",
      "accounts": [
        {
          "name": "Main Bank Account",
          "account_type": "personal",
          "statements_folder": "data/raw/statements/Michael/Bank",
          "processed_folder": "data/processed/transactions/Michael/Bank"
        },
        {
          "name": "Credit Card",
          "account_type": "credit_card",
          "statements_folder": "data/raw/statements/Michael/CreditCard",
          "processed_folder": "data/processed/transactions/Michael/CreditCard"
        }
      ]
    }
  ],
  "shared_accounts": [
    {
      "name": "Joint Credit Card",
      "account_type": "credit_card",
      "statements_folder": "data/raw/statements/Shared/CreditCard",
      "processed_folder": "data/processed/transactions/Shared/CreditCard"
    }
  ]
}
```

**Settings UI** ([src/gui/settings_tab.py](src/gui/settings_tab.py))
The GUI provides a tabbed interface for configuration:
- **Users Tab**: Add/edit/delete users, import from checkpoint
- **Accounts Tab**: Manage user accounts with type and folder settings
- **Shared & Global Tab**: Shared accounts, working directory, save/reload

## Development Commands

### Basic Usage
```bash
# Run tests
python -m unittest tests.test_calculations -v

# Create new person templates
python main.py --create-templates Person1 Person2

# Process a month (NET mode - default)
python main.py --person-sheets Person1_April_2024.xlsx Person2_April_2024.xlsx

# Process a month (GROSS mode - calculate tax)
python main.py --person-sheets Person1_April_2024.xlsx Person2_April_2024.xlsx --use-gross

# Auto-detect and process next month
python main.py --next

# View checkpoint summary (all months + cumulative)
python main.py --checkpoint-summary

# Run demo
python main.py --demo
```

### Bank Statement Operations
```bash
# List available bank templates
python main.py --list-templates

# Parse bank statement (auto-detect template)
python main.py --parse-bank-statement statement.pdf

# Parse with specific template
python main.py --parse-bank-statement statement.pdf --bank-template fnb_credit_card

# Export bank statement to Excel
python main.py --export-bank-statement statement.pdf Person_Month_Year.xlsx

# Export with specific template
python main.py --export-bank-statement statement.pdf output.xlsx --bank-template absa_cheque
```

### Testing
```bash
# Run all tests
python -m unittest tests.test_calculations -v

# Run specific test
python -m unittest tests.test_calculations.TestTaxCalculator.test_middle_income_tax -v
```

## Critical Implementation Details

### The Settlement Algorithm
Located in `split_calculator.py`:
1. Calculate net income for each person (after deductions in GROSS mode, or as-is in NET mode)
2. Determine proportion: `person1_proportion = person1_net / total_net`
3. Calculate what each should pay: `person1_should_pay = total_shared * person1_proportion`
4. Compare to what was actually paid: `person1_paid` (from expense `paid_by` field)
5. Balance: `person1_balance = person1_paid - person1_should_pay`
6. If balance is positive, they overpaid and should receive money; if negative, they should pay

### Person Sheet Format
Each person maintains a simple Excel file with two sheets:
- **Income Sheet**: Columns: Description, Amount, Type
  - NET mode (default): Enter take-home pay from payslips
  - GROSS mode: Enter gross salary, system calculates tax
- **Expenses Sheet**: Columns: Description, Amount, Category, Type
  - **Type column** distinguishes Personal vs Household expenses:
    - "Household" or "Shared": Split fairly with partner (included in fair share calculation)
    - "Personal" or "Individual": This person's expense only (excluded from fair share calculation)
  - All expenses can be included (both personal and household)
  - System automatically filters based on Type column

### Checkpoint State Management
- File: `financial_checkpoint.json`
- Stores: person names, monthly results, cumulative transfers
- Filename pattern detection: `Name_Month_Year.xlsx` or `Name_YYYY_MM.xlsx`
- Month increment logic in `_increment_filename()` handles both formats

## Common Modification Patterns

### Adding a New Income Type
1. Add to `IncomeType` enum in [models.py](src/models.py)
2. Add keyword mapping in `PersonSheetImporter.__init__()` in [person_sheet_importer.py](src/person_sheet_importer.py)

### Adding a New Expense Category
1. Add to `ExpenseCategory` enum in [models.py](src/models.py)
2. Add keyword mapping in `PersonSheetImporter.__init__()` for auto-detection
3. Update template in `create_template_sheets()` in [person_sheet_importer.py](src/person_sheet_importer.py)

### Updating Tax Brackets (New Tax Year)
1. Edit [tax_calculator.py](src/tax_calculator.py)
2. Add new `SA_TAX_BRACKETS_YYYY_YYYY` list with updated rates from SARS
3. Update rebates dictionary if rebate amounts changed
4. Update `TaxCalculator.__init__()` to use new year

### Adding Bank Templates (New Bank or Account Type)

The system uses YAML-based templates for parsing any bank's PDF statements. Templates are stored in `bank_templates/` directory.

**Creating a New Template:**

1. **Start with an example**: Copy an existing template (e.g., `fnb_credit_card.yaml`) as a starting point
2. **Examine your statement**: Open your PDF and identify the transaction line format
3. **Update the template**:
   - `bank_name`: Name of the bank (e.g., "Capitec", "Standard Bank")
   - `account_type`: Account type (e.g., "Credit Card", "Cheque Account")
   - `detection.markers`: Unique text from the first page for auto-detection
   - `parsing.transaction_pattern`: Regex pattern matching your transaction lines (use named groups)
   - `sections`: Start/end markers and lines to skip
   - `summary`: Patterns to extract statement metadata

4. **Test the template**:
   ```bash
   python main.py --parse-bank-statement statement.pdf --bank-template your_template
   ```

**Example Template Structure:**
```yaml
bank_name: "MyBank"
account_type: "Credit Card"

detection:
  markers: ["MYBANK", "CREDIT CARD"]
  priority: 5

parsing:
  # Pattern with named groups: day, month, description, amount
  transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+(?P<description>.+?)\s+(?P<amount>[\d,.]+)'

  date:
    day_group: "day"
    month_group: "month"
    format: "%d %b"
    year_source: "statement"

  amount:
    group: "amount"
    decimal_separator: "."
    thousands_separator: ","

sections:
  start_markers: ["Transaction Date"]
  end_markers: ["Closing Balance"]
  skip_lines: ["Opening Balance", "Page "]

output:
  account_type: "mybank_credit_card"
```

**Available Templates:**
- `fnb_credit_card.yaml` - FNB Credit Card statements
- `fnb_personal.yaml` - FNB Personal/Cheque accounts (bilingual)
- `fnb_fusion.yaml` - FNB Fusion Private Clients accounts (bilingual)
- `absa_cheque.yaml` - ABSA Cheque Account (example/template)
- `absa_credit_card.yaml` - ABSA Credit Card (example/template)

**For detailed documentation**, see [docs/BANK_TEMPLATES.md](docs/BANK_TEMPLATES.md).

### Changing Split Strategy
- To split based on gross income instead of net: set `use_gross_income_for_split=True` in `calculate_split()` call
- To implement custom split logic: modify `FinancialSplitter.calculate_split()` in [split_calculator.py](src/split_calculator.py)

## File Naming Conventions

The system expects this pattern for person sheets:
- Format: `PersonName_Month_Year.xlsx` or `PersonName_YYYY_MM.xlsx`
- Examples: `Michael_April_2024.xlsx`, `Jacqui_September_2025.xlsx`
- The checkpoint system uses this to auto-detect next month's files

## Important Gotchas

1. **SHARED vs INDIVIDUAL expenses**: Only SHARED expenses contribute to the settlement calculation. INDIVIDUAL expenses are tracked but don't affect who owes whom.

2. **NET vs GROSS mode**: The mode is set via `--use-gross` flag (or `skip_tax_calculation` parameter). In NET mode, income values are treated as after-tax. In GROSS mode, tax is calculated.

3. **Decimal precision**: All monetary calculations use Python's `Decimal` type to avoid floating-point errors. Always use `Decimal("123.45")` not `123.45`.

4. **Month detection**: The checkpoint system increments month in filenames. Ensure consistent naming or the `--next` command won't find files.

5. **Tax refunds**: Should be added as income (type: OTHER) in the month they are received, not adjusted retroactively.

## Testing Philosophy

Tests focus on calculation accuracy:
- Tax bracket calculations
- UIF caps
- Split proportions
- Settlement amounts
- Edge cases (zero income, equal split)

When modifying calculations, always run tests to verify accuracy.

## Dependencies

- `pandas`: Excel file reading/writing
- `openpyxl`: Excel file engine for pandas
- `PyPDF2`: Bank statement PDF parsing
- `pycryptodome`: PDF decryption support
- `PyYAML`: YAML template file parsing for bank statement templates

Install with: `pip install -r requirements.txt`
