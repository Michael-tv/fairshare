# What's New: Individual Person Sheets Workflow

## Summary

I've added a **much simpler workflow** where each person maintains their own spreadsheet instead of one complex combined sheet!

## The New Approach

### Before (Complex):
```
One big Excel file
├── Complex formulas
├── Both people editing same file
├── Hardcoded values
└── Hard to audit
```

### After (Simple):
```
Michael_April_2024.xlsx        Jacqui_April_2024.xlsx
├── Income sheet               ├── Income sheet
│   └── Simple list            │   └── Simple list
└── Expenses sheet             └── Expenses sheet
    └── What I paid                └── What I paid
```

## How It Works

### 1. Create Templates (Once)
```bash
python main.py --create-templates Michael Jacqui
```

Creates two template files ready to fill in.

### 2. Each Person Maintains Their Sheet

**Michael's Income Sheet:**
| Description | Amount | Type |
|-------------|--------|------|
| Salary | 70000 | Salary |
| Bonus | 5000 | Salary |

**Michael's Expenses Sheet** (only shared costs HE paid):
| Description | Amount | Category |
|-------------|--------|----------|
| Groceries | 4500 | Groceries |
| Bond | 14000 | Loans |
| Electricity | 2000 | Utilities |

**Jacqui does the same** with her income and the shared costs SHE paid.

### 3. Run Monthly Calculation
```bash
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx
```

Get instant results:
- Who earned what
- Tax calculations
- Who paid what
- **Settlement amount** (who transfers to whom)

## Key Benefits

### Simplicity ✅
- No complex formulas
- Just list your income and expenses
- Categories auto-detected
- Tax calculated automatically

### Transparency ✅
- Each person sees exactly what they entered
- Clear audit trail
- Easy to verify

### Independence ✅
- Each person owns their data
- No conflicts editing same file
- Update your sheet anytime

### Accuracy ✅
- Less room for errors
- System validates and calculates
- Automatic categorization

## What You Need to Know

### Income Sheet
- List ALL income (salary, bonuses, rental, etc.)
- Use GROSS amounts (before tax)
- System calculates tax automatically

### Expenses Sheet
- **ONLY shared household costs YOU paid**
- ✅ Include: Groceries, utilities, bond, insurance, school fees
- ❌ Exclude: Personal expenses (your car payment, gym, etc.)
- ❌ Exclude: Things the other person paid

### Categories
The system auto-detects categories from descriptions:
- "Woolworths" → Groceries
- "Electricity bill" → Utilities
- "Bond payment" → Loans
- "Medical aid" → Medical Aid

You can also specify manually in the Category column.

## Example Output

```
================================================================================
FINANCIAL SPLIT REPORT - April 2024
================================================================================

INCOME SUMMARY
                                       Michael          Jacqui           Total
Gross Income                   R     75,000.00 R     30,000.00 R    105,000.00
Deductions (Tax + UIF)         R     21,117.45 R      4,960.20 R     26,077.66
Net Income                     R     53,882.55 R     25,039.80 R     78,922.34

INCOME PROPORTIONS
Michael: 68.3%
Jacqui: 31.7%

EXPENSE SUMMARY
Shared Expenses                          R     38,129.74
  Michael should pay (68.3%):                 R     26,032.27
  Jacqui should pay (31.7%):                 R     12,097.47

Michael actually paid: R31,079.74
Jacqui actually paid: R7,050.00

** Jacqui should transfer R5,047.47 to Michael **
```

## Why This Settlement Amount?

Michael paid R31,079.74, but should only pay R26,032.27 (68.3% of shared costs).
So he overpaid by R5,047.47.

Jacqui paid R7,050.00, but should pay R12,097.47 (31.7% of shared costs).
So she underpaid by R5,047.47.

**Jacqui transfers R5,047.47 to Michael** = Fair and square! ⚖️

## Getting Started

### Option 1: Try the Examples

```bash
# Create example data
python create_example_data.py

# Run the calculation
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx
```

### Option 2: Create Your Own

```bash
# Create templates
python main.py --create-templates YourName PartnerName

# Fill in the templates
# Save as: YourName_Month_Year.xlsx

# Calculate
python main.py --person-sheets YourName_April_2024.xlsx PartnerName_April_2024.xlsx
```

## Files Added

- `src/person_sheet_importer.py` - Import logic for person sheets
- `NEW_WORKFLOW_GUIDE.md` - Complete guide
- `WHATS_NEW.md` - This file
- `create_example_data.py` - Creates example files
- Updated `main.py` with new commands

## Commands Reference

```bash
# Create templates (do this first)
python main.py --create-templates Person1 Person2

# Calculate monthly split
python main.py --person-sheets File1.xlsx File2.xlsx

# Still works: Demo and old import
python main.py --demo
python main.py --import OldFile.xlsx
```

## Monthly Workflow

1. **Start of month:** Copy your template or last month's file
2. **During month:** Add expenses as you pay them
3. **End of month:**
   - Finalize your sheet
   - Run the calculation
   - Review settlement
   - Make the transfer
4. **Archive:** Keep files for historical records

## Migration from Old Spreadsheet

You can use both approaches:
1. Keep using your old Excel for historical reference
2. Start using person sheets for new months
3. Gradually transition fully to person sheets

The old import still works:
```bash
python main.py --import "Finances 2024 04.xlsx"
```

## Next Steps

1. **Read:** [NEW_WORKFLOW_GUIDE.md](NEW_WORKFLOW_GUIDE.md)
2. **Try:** Run the example data
3. **Create:** Your templates
4. **Start:** Using it for this month!

## Support

All the existing features still work:
- Tax calculator
- Reports
- Scenario planning
- CSV export
- Everything!

The new workflow is just a simpler way to input data.

---

**Bottom Line:** Same powerful calculations, much simpler data entry! 🎉
