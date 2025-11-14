# New Workflow Guide: Individual Person Sheets

## Overview

The new recommended workflow has each person maintain their own simple spreadsheet with:
1. **Income Sheet** - All income sources for the month (gross amounts)
2. **Expenses Sheet** - ONLY shared household costs that THEY paid

This is much simpler and more transparent than the old combined spreadsheet!

## Why This Is Better

### Old Way (Complex):
- ❌ One complex spreadsheet with hardcoded formulas
- ❌ Both people editing same file
- ❌ Hard to see who paid what
- ❌ Easy to make mistakes

### New Way (Simple):
- ✅ Each person maintains their own simple sheet
- ✅ Just list your income and what you paid
- ✅ System automatically categorizes and calculates
- ✅ Transparent and auditable

## Getting Started

### Step 1: Create Template Spreadsheets

```bash
python main.py --create-templates Michael Jacqui
```

This creates:
- `Michael_Template.xlsx`
- `Jacqui_Template.xlsx`

### Step 2: Each Person Fills Their Sheet

#### Income Sheet
List all income for the month (GROSS amounts before tax):

| Description | Amount | Type |
|-------------|--------|------|
| Monthly Salary | 70000 | Salary |
| Bonus | 5000 | Salary |
| Rental Income | 8500 | Rental |
| Tax Refund | 2000 | Other |

**Important:** Use GROSS salary (before tax). The system calculates tax automatically.

#### Expenses Sheet
List ONLY shared household costs that YOU paid:

| Description | Amount | Category |
|-------------|--------|----------|
| Woolworths Groceries | 4500 | Groceries |
| Electricity Bill | 2000 | Utilities |
| Bond Payment | 14187.74 | Loans |
| Medical Aid | 7241 | Medical Aid |
| School Fees | 4273 | School Fees |

**Important:**
- ✅ Include: Things you paid that should be shared (groceries, utilities, bond, insurance, etc.)
- ❌ Don't include: Personal expenses like your car payment or gym membership
- ❌ Don't include: Things the other person paid (they'll list those in their sheet)

### Step 3: Save Your Sheets

Save as: `PersonName_Month_Year.xlsx`

Examples:
- `Michael_April_2024.xlsx`
- `Jacqui_May_2024.xlsx`

### Step 4: Run the Calculation

```bash
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx
```

You'll get:
- Complete income summary
- Tax calculations for each person
- Fair split of shared expenses
- **Settlement amount** (who should transfer to whom)
- Detailed expense breakdown

## Example Output

```
INCOME SUMMARY
                                       Michael          Jacqui           Total
Gross Income                   R     75,000.00 R     30,000.00 R    105,000.00
Deductions (Tax + UIF)         R     21,117.45 R      4,960.20 R     26,077.66
Net Income                     R     53,882.55 R     25,039.80 R     78,922.34

INCOME PROPORTIONS
Michael: 68.3%
Jacqui: 31.7%

SETTLEMENT
** Jacqui should transfer R5,047.47 to Michael **
```

This means:
- Michael paid R31,079.74 for shared costs
- Jacqui paid R7,050.00 for shared costs
- Based on their 68.3% / 31.7% income split:
  - Michael should pay R26,032.27
  - Jacqui should pay R12,097.47
- So Jacqui transfers R5,047.47 to Michael to settle fairly

## Template Structure

### Income Sheet
```
Description          | Amount  | Type
---------------------|---------|--------
Monthly Salary       | 0.00    | Salary
Bonus/Commission     | 0.00    | Salary
Rental Income        | 0.00    | Rental
Other Income         | 0.00    | Other
```

### Expenses Sheet
```
Description          | Amount  | Category
---------------------|---------|---------------
Groceries           | 0.00    | Groceries
Electricity         | 0.00    | Utilities
Water               | 0.00    | Utilities
Internet            | 0.00    | Utilities
Bond/Rent           | 0.00    | Loans
Insurance           | 0.00    | Insurance
Medical Aid         | 0.00    | Medical Aid
School Fees         | 0.00    | School Fees
Domestic Help       | 0.00    | Domestic Help
Fuel                | 0.00    | Fuel
Other               | 0.00    | Other
```

## Categories (Auto-Detected)

The system automatically detects categories from descriptions:

### Income Types
- **Salary** - salary, wage, bonus, commission
- **Rental** - rent, rental income
- **Business** - business, consulting, freelance
- **Investment** - dividends, interest, investment
- **Other** - everything else

### Expense Categories
- **Groceries** - groceries, food, woolworths, pick n pay, spar
- **Utilities** - electricity, water, gas, internet, wifi
- **Fuel** - petrol, diesel, fuel
- **Loans** - bond, mortgage, loan
- **Insurance** - insurance, cover
- **Medical Aid** - medical, doctor, pharmacy
- **School Fees** - school, education, fees
- **Levies** - levies, levy, body corporate
- **Rates** - rates, municipal
- **Domestic Help** - cleaning, cleaner, garden, gardener
- **Subscriptions** - netflix, dstv, subscription
- **Maintenance** - maintenance, repair
- **Other** - everything else

You can also manually specify categories in the "Type" or "Category" column.

## Monthly Workflow

### At the Beginning of the Month
Each person starts with a fresh copy of their template (or copy last month's file and update).

### During the Month
Each person adds their expenses to their sheet as they pay them.

### End of Month
1. Finalize both sheets
2. Run the import command
3. Review the settlement amount
4. Make the transfer
5. Archive the files for records

## Tips & Best Practices

### Do's ✅
- ✅ List ALL income sources (salary, bonuses, rental, etc.)
- ✅ Use GROSS salary amounts (before tax)
- ✅ List ONLY shared costs you paid in Expenses
- ✅ Be consistent with descriptions (helps with auto-categorization)
- ✅ Keep sheets simple and clear
- ✅ Archive monthly files for history

### Don'ts ❌
- ❌ Don't include your personal expenses (car payment, gym, etc.)
- ❌ Don't list expenses the other person paid
- ❌ Don't use NET salary (system calculates tax)
- ❌ Don't forget to save with proper filename format
- ❌ Don't edit old months (keep as historical record)

## Troubleshooting

### "My categories are wrong"
- Either add them manually in the "Category" column, OR
- Use standard keywords in descriptions (see list above)

### "Tax calculation doesn't match my payslip"
- The system uses standard SARS PAYE rates
- Your employer might apply different rules
- This gives you a good approximation

### "Settlement amount seems high/low"
- Check both sheets have all expenses listed
- Verify income amounts are correct (GROSS not NET)
- Review the detailed breakdown report

### "Import fails"
- Check filename format: `PersonName_Month_Year.xlsx`
- Ensure sheets are named "Income" and "Expenses"
- Check file isn't open in Excel

## Advanced Usage

### Compare Multiple Months
```python
from person_sheet_importer import import_household_month
from split_calculator import FinancialSplitter
from reports import ReportGenerator
from datetime import date

# Import multiple months
periods = []
for month in range(1, 13):
    period = import_household_month(
        f"Michael_{month:02d}_2024.xlsx",
        "Michael",
        f"Jacqui_{month:02d}_2024.xlsx",
        "Jacqui",
        date(2024, month, 1)
    )
    periods.append(period)

# Generate yearly summary
# ... (see Python examples in other docs)
```

### Export to CSV
After import, you can export the data:
```python
reporter = ReportGenerator()
csv_data = reporter.export_to_csv(period, result)
with open("april_2024.csv", "w") as f:
    f.write(csv_data)
```

## File Organization

Recommended folder structure:
```
home_finances/
├── 2024/
│   ├── 01_January/
│   │   ├── Michael_January_2024.xlsx
│   │   └── Jacqui_January_2024.xlsx
│   ├── 02_February/
│   │   ├── Michael_February_2024.xlsx
│   │   └── Jacqui_February_2024.xlsx
│   └── ...
├── 2025/
│   └── ...
└── Templates/
    ├── Michael_Template.xlsx
    └── Jacqui_Template.xlsx
```

## Quick Reference

```bash
# Create templates (first time only)
python main.py --create-templates Michael Jacqui

# Calculate monthly split
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx

# Get help
python main.py --help
```

## Real Example

### Michael_April_2024.xlsx

**Income Sheet:**
| Description | Amount | Type |
|-------------|--------|------|
| Monthly Salary | 91350 | Salary |
| Consulting | 5000 | Business |

**Expenses Sheet:**
| Description | Amount | Category |
|-------------|--------|----------|
| Woolworths | 4500 | Groceries |
| Pick n Pay | 2300 | Groceries |
| Electricity | 2000 | Utilities |
| Internet | 899 | Utilities |
| Bond Payment | 14187.74 | Loans |
| Levies | 1170 | Levies |
| School Fees | 4273 | School Fees |
| Petrus Gardener | 1750 | Domestic Help |

### Jacqui_April_2024.xlsx

**Income Sheet:**
| Description | Amount | Type |
|-------------|--------|------|
| Monthly Salary | 38000 | Salary |

**Expenses Sheet:**
| Description | Amount | Category |
|-------------|--------|----------|
| Spar | 1800 | Groceries |
| Water Bill | 450 | Utilities |
| Marta Cleaning | 1300 | Domestic Help |
| Medical Aid | 3500 | Medical Aid |

### Result:
```bash
$ python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx

Total Income: R134,350
Michael paid: R31,079.74 for shared costs
Jacqui paid: R7,050.00 for shared costs

Settlement: Jacqui should transfer R5,047.47 to Michael
```

## Summary

The new person-sheet workflow is:
- ✅ Simpler to use
- ✅ More transparent
- ✅ Less error-prone
- ✅ Each person owns their data
- ✅ Easy to audit and verify
- ✅ Scales well over time

**Start using it today!**

```bash
python main.py --create-templates [Your Name] [Partner Name]
```
