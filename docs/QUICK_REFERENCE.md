# Quick Reference Card

## Command Cheat Sheet

```bash
# RECOMMENDED WORKFLOW
# Create template spreadsheets
python main.py --create-templates Michael Jacqui

# Calculate from person sheets (NET mode - default)
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx

# Use GROSS mode (calculate tax automatically)
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx --use-gross

# Auto-detect next month (NET mode)
python main.py --next

# Auto-detect next month with GROSS mode
python main.py --next --use-gross

# View cumulative summary
python main.py --checkpoint-summary

# Reset checkpoint
python main.py --reset-checkpoint

# --- Other Commands ---

# Run demo
python main.py --demo

# Import old Excel file
python main.py --import "Finances 2024 04.xlsx"

# Show tax calculations
python main.py --tax

# Interactive mode
python main.py --interactive

# Run tests
python -m unittest tests.test_calculations -v

# Get help
python main.py --help
```

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Run this to use the system |
| `src/models.py` | Add expense categories here |
| `src/tax_calculator.py` | Update tax rates here |
| `src/split_calculator.py` | Splitting logic |
| `tests/test_calculations.py` | Run tests |
| `GETTING_STARTED.md` | Detailed guide |
| `README.md` | Full documentation |

## Common Tasks

### Add New Expense Category
Edit `src/models.py`, find `ExpenseCategory` enum:
```python
class ExpenseCategory(Enum):
    # ... existing ...
    YOUR_NEW_CATEGORY = "Your Category Name"
```

### Change Tax Year
Edit `src/tax_calculator.py`:
```python
# Add new tax brackets
SA_TAX_BRACKETS_2025_2026 = [...]
```

### Adjust Split Percentage Manually
In `src/split_calculator.py`, find `calculate_split()` and modify the proportion calculation.

### Export Report to File
```bash
python main.py --demo > report.txt
```

## NET vs GROSS Mode

### NET Mode (Default - Recommended)
```bash
python main.py --next  # No flag needed
```
- Enter take-home pay from payslips
- No tax calculation needed
- Simpler, fewer moving parts
- Tax refunds: Add as "Other" income when received

### GROSS Mode (Optional)
```bash
python main.py --next --use-gross
```
- Enter gross salary (before tax)
- System calculates SA tax automatically
- Shows detailed tax breakdowns
- More complex, but shows tax details

**Which to use?** NET mode is recommended for most people!

## Reading the Reports

### Settlement Line
```
** Michael should transfer R1,010.71 to Jacqui **
```
This means Michael needs to pay Jacqui R1,010.71 to settle shared expenses fairly.

### Proportions
```
Michael: 67.0%
Jacqui: 33.0%
```
Based on income, Michael should pay 67% of shared expenses, Jacqui pays 33%.

### Remaining Amount
```
Michael: R37,793.00
Jacqui: R19,550.51
```
How much each person has left after all expenses and settlement.

## Troubleshooting

### Import Fails
- Check filename is correct
- Ensure "Expense balance sheet" tab exists
- Check file is not open in Excel

### Weird Numbers
- Verify expenses are classified correctly (Shared/Individual)
- Check "paid_by" is set
- Review expense breakdown report

### Tests Fail
```bash
python -m unittest tests.test_calculations -v
```
If tests fail, something is broken. Check recent changes.

## Project Structure

```
src/
├── models.py           # Data structures
├── tax_calculator.py   # Tax logic
├── split_calculator.py # Split algorithm
├── excel_importer.py   # Excel import
└── reports.py          # Reports

tests/
└── test_calculations.py # Unit tests

main.py                 # CLI interface
```

## Quick Python Usage

```python
from decimal import Decimal
from datetime import date
from models import Person, Income, Expense, FinancialPeriod
from models import IncomeType, ExpenseType, ExpenseCategory
from split_calculator import FinancialSplitter
from reports import ReportGenerator

# Create people
person1 = Person(name="Person1")
person2 = Person(name="Person2")

# Create period
period = FinancialPeriod(
    period=date.today(),
    people=[person1, person2]
)

# Add income
period.add_income(Income(
    person=person1,
    amount=Decimal("70000"),
    income_type=IncomeType.SALARY,
    description="Salary",
    period=date.today()
))

# Add expense
period.add_expense(Expense(
    description="Groceries",
    amount=Decimal("5000"),
    category=ExpenseCategory.GROCERIES,
    expense_type=ExpenseType.SHARED,
    paid_by=person1
))

# Calculate
splitter = FinancialSplitter(2024)
result = splitter.calculate_split(period, person1, person2)

# Report
reporter = ReportGenerator()
print(reporter.generate_summary_report(result))
```

## Key Concepts

### Expense Types
- **Shared**: Split proportionally (groceries, utilities)
- **Individual**: Paid by one person only (car payment)
- **Deduction**: Already deducted (tax, UIF)

### The Algorithm
1. Calculate net income (after tax)
2. Determine proportions based on income
3. Apply proportions to shared expenses
4. Calculate who owes whom

### Tax Rates (2024/2025)
- R0 - R237k: 18%
- R237k - R370k: 26%
- R370k - R513k: 31%
- R513k - R673k: 36%
- R673k - R858k: 39%
- R858k - R1.8m: 41%
- R1.8m+: 45%
- Rebate: R17,235

## Support

- Check `README.md` for full docs
- Check `GETTING_STARTED.md` for tutorials
- Check `PROJECT_SUMMARY.md` for overview
- Check `recommendations.md` for analysis

## Version Control

```bash
# Initialize git
git init

# Add files
git add .

# First commit
git commit -m "Initial financial splitting system"

# Create GitHub repo and push
git remote add origin <your-repo-url>
git push -u origin main
```

---
**Quick Tip:** Run `python main.py --demo` first to see how everything works!
