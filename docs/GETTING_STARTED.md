# Getting Started with Home Finance Splitting System

## What You Now Have

A complete Python-based financial splitting system with:
- **NET Income Mode** (Default): Use take-home pay from payslips - simpler!
- **GROSS Mode** (Optional): South African tax calculator (2024/2025 tax year)
- Fair splitting logic based on proportional income
- Person sheet workflow - each person has their own Excel file
- Checkpoint system - auto-detects next month
- Multiple report types
- Unit tests (all passing!)
- CLI interface

## Recommended: NET Income Mode

The system defaults to **NET income mode**, which is simpler:
- Enter take-home pay from your payslips
- No tax calculations needed
- Fewer moving parts
- Tax refunds handled as income when received

See [NET_INCOME_MODE.md](NET_INCOME_MODE.md) for full details.

To use GROSS mode (calculate tax automatically), add `--use-gross` flag.

## Quick Start

### 1. Create Templates (First Time)
```bash
python main.py --create-templates Michael Jacqui
```
Creates simple Excel templates for each person with:
- Income Sheet (enter NET amounts - take-home pay from payslips)
- Expenses Sheet (shared costs you paid)

### 2. Fill In Your Data
**Michael_April_2024.xlsx:**
- Income Sheet: R68,633 (NET salary from payslip)
- Expenses Sheet: Groceries R5,000, etc.

**Jacqui_April_2024.xlsx:**
- Income Sheet: R38,520 (NET salary from payslip)
- Expenses Sheet: Utilities R3,000, etc.

### 3. Calculate Split
```bash
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx
```

Result: Shows who should transfer to whom!

### 4. Next Month (Auto!)
```bash
python main.py --next
```
Automatically finds and processes next month's files.

### Optional: See Demo
```bash
python main.py --demo
```
Runs a demo with sample data.

## Understanding the Output

### Financial Split Report
Shows:
- Gross income for each person
- Tax and UIF deductions
- Net income after tax
- Proportional split percentages
- What each person should pay for shared expenses
- **Transfer amount** - who should pay whom and how much

### Key Concept: The Settlement
The system calculates:
1. What each person **should pay** based on their income proportion
2. What each person **actually paid**
3. The **transfer needed** to balance it fairly

**Example:**
- Michael earns 70%, Jacqui earns 30%
- Shared expenses = R10,000
- Michael should pay R7,000, Jacqui should pay R3,000
- If Michael paid all R10,000:
  - Michael overpaid by R3,000
  - **Jacqui should transfer R3,000 to Michael**

## How to Use This Going Forward

### Option 1: Continue with Excel + Python Analysis
1. Keep entering data in Excel as you do now
2. Run the Python importer monthly to get:
   - Fair split calculations
   - Detailed reports
   - Category breakdowns
   - Tax calculations

```bash
python main.py --import "Finances 2024 05.xlsx"
```

### Option 2: Transition to Python Data Entry
1. Create CSV files for your expenses:
   ```csv
   Description,Amount,Category,PaidBy
   Groceries,8000,GROCERIES,Michael
   Internet,899,UTILITIES,Jacqui
   ```

2. Import and process in Python
3. Generate reports

### Option 3: Build a Dashboard (Future)
- Create a Streamlit web interface
- Enter data through forms
- See live calculations
- Export reports to PDF

## Customizing for Your Needs

### Update Income
Edit the values in your Excel file or in the Python code:
```python
period.add_income(Income(
    person=michael,
    amount=Decimal("95000"),  # New salary
    income_type=IncomeType.SALARY,
    description="Salary",
    period=date(2024, 5, 1)
))
```

### Add New Expense Categories
Edit `src/models.py`:
```python
class ExpenseCategory(Enum):
    # ... existing categories ...
    ENTERTAINMENT = "Entertainment"
    PETS = "Pet Care"
```

### Change Split Strategy
By default, the system uses net income (after tax) for proportional splits.

To use gross income instead:
```python
result = splitter.calculate_split(
    period,
    michael,
    jacqui,
    use_gross_income_for_split=True  # Use gross instead of net
)
```

### Update Tax Year
When the new tax year starts, update `src/tax_calculator.py`:
```python
# Add new brackets for 2025/2026
SA_TAX_BRACKETS_2025_2026 = [
    TaxBracket(...),  # New rates from SARS
]
```

## Important Notes About Your Data

### Current Excel Import Issues
The Excel importer is working but may need refinement because:
1. Your Excel has complex merged cells and formulas
2. Some expenses might be misclassified
3. "Who paid" information might not be fully captured

### Recommendations:
1. **Verify the imported data** - check that numbers match your Excel
2. **Improve the importer** - you can enhance `src/excel_importer.py` to better handle your specific sheet layout
3. **Consider simplifying your Excel** - or move to a cleaner data entry method

## Next Steps

### Immediate:
1. Run `python main.py --import "Finances 2024 04.xlsx"`
2. Review the output to verify accuracy
3. Compare with your current Excel calculations
4. Adjust the importer if needed

### Short-term:
1. Create a monthly workflow:
   - Update Excel with monthly data
   - Run Python import and generate reports
   - Use reports for splitting decisions

2. Add features you need:
   - Email reports
   - PDF export
   - Budget vs. actual tracking

### Long-term:
1. Build a web dashboard (Streamlit recommended)
2. Automate bank transaction imports
3. Add visualizations and trends
4. Historical year-over-year analysis

## Getting Help

### Run Tests
```bash
python -m unittest tests.test_calculations -v
```
All tests should pass. If they don't, something is broken.

### Check the Code
All source code is in `src/` with clear comments:
- `models.py` - Data structures
- `tax_calculator.py` - Tax logic
- `split_calculator.py` - Splitting algorithm
- `reports.py` - Report generation
- `excel_importer.py` - Excel import

### Common Issues

**"Transfer amount seems wrong"**
- Check if expenses are classified correctly (Shared vs Individual)
- Verify "paid_by" is set correctly
- Review the expense breakdown report

**"Tax calculation doesn't match my payslip"**
- The calculator uses standard PAYE rates
- Your employer might have different assumptions
- Check if age-based rebates are correct

**"Import fails or gives weird numbers"**
- Your Excel layout might be different
- Check the sheet name is "Expense balance sheet"
- Review `src/excel_importer.py` and adjust for your layout

## Code Structure Cheat Sheet

```
models.py
├── Person - Represents Michael/Jacqui
├── Income - Salary, rental, etc.
├── Expense - Any expense item
├── FinancialPeriod - A month's worth of data
└── SplitResult - The calculated split

tax_calculator.py
└── TaxCalculator - Calculates SA PAYE tax

split_calculator.py
└── FinancialSplitter - Does the fair split calculation

reports.py
└── ReportGenerator - Creates various reports

excel_importer.py
└── ExcelImporter - Loads data from Excel
```

## Example Workflows

### Monthly Reconciliation
```bash
# 1. Import current month
python main.py --import "Finances 2024 05.xlsx"

# 2. Review the settlement amount
# (shows who should transfer to whom)

# 3. Make the transfer

# 4. Update a tracking sheet with results
```

### What-If Scenarios
```python
# In Python:
from split_calculator import FinancialSplitter

splitter = FinancialSplitter(2024)

# Compare different salary scenarios
scenarios = [
    ("Current", Decimal("91350"), Decimal("38000")),
    ("Michael 10% raise", Decimal("100485"), Decimal("38000")),
    ("Both 10% raise", Decimal("100485"), Decimal("41800")),
]

results = splitter.compare_scenarios(period, michael, jacqui, scenarios)

# See how splits change
for name, result in results.items():
    print(f"{name}: {result.person1.name} pays R{result.person1_should_pay:,.2f}")
```

### Annual Summary
```python
# Import 12 months of data
monthly_results = []
for month in range(1, 13):
    period, m, j = quick_import(f"Finances 2024 {month:02d}.xlsx")
    result = splitter.calculate_split(period, m, j)
    monthly_results.append(result)

# Generate yearly report
reporter = ReportGenerator()
print(reporter.generate_yearly_summary(monthly_results))
```

## You're All Set!

The system is ready to use. Start with the demo, then import your Excel data, and take it from there.

The code is clean, documented, and tested - so you can modify it confidently to fit your exact needs.

**Have fun with it!**
