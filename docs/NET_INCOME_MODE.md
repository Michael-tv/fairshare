# NET Income Mode Guide

## Overview

**Default Mode:** NET Income (Take-Home Pay)

The system now defaults to using NET income (take-home pay from payslips) instead of calculating tax automatically. This is simpler when you don't have all payslip details readily available.

## Why NET Income Mode?

### Advantages
- ✅ **Simpler** - Just enter what you actually received
- ✅ **Accurate** - Uses exact amounts from payslips
- ✅ **Less data** - Don't need to track gross, tax brackets, deductions
- ✅ **Faster** - No complex tax calculations needed

### When to Use NET Mode
- You have payslips with take-home amounts
- You don't want to track gross salary details
- You prefer simplicity over detailed tax analysis
- Tax is already deducted correctly by employer

## How It Works

### Step 1: Fill Income Sheet with NET Amounts

**Income Sheet (Michael_April_2024.xlsx):**
```
Description          | Amount  | Type
---------------------|---------|--------
Take-home Salary     | 68633   | Salary   <- NET amount from payslip
Bonus (after tax)    | 4500    | Salary   <- After-tax bonus
```

**NOT GROSS:**
```
Monthly Salary       | 100000  | Salary   <- DON'T do this in NET mode!
```

### Step 2: Process Normally

```bash
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx
```

The system:
- Uses NET amounts as-is
- Skips tax calculations
- Splits based on NET income proportions
- Calculates settlement

### Step 3: Year-End Tax Refund

When you get a tax refund, add it as income:

**Income Sheet (December):**
```
Description          | Amount  | Type
---------------------|---------|--------
Take-home Salary     | 68633   | Salary
Tax Refund           | 10000   | Other    <- Add refund here!
```

The system will:
- Add R10,000 to your NET income for December
- Adjust your proportion for that month
- Split expenses fairly
- Everything balances!

## Example Calculation

### Scenario
- Michael NET: R68,633/month (from payslip)
- Jacqui NET: R38,520/month (from payslip)
- Shared expenses: R30,000

### Calculation
```
Total NET income: R68,633 + R38,520 = R107,153

Michael proportion: R68,633 / R107,153 = 64.1%
Jacqui proportion:  R38,520 / R107,153 = 35.9%

Shared expenses split:
  Michael should pay: R30,000 × 64.1% = R19,215
  Jacqui should pay:  R30,000 × 35.9% = R10,785
```

If Michael paid all R30,000:
- Michael overpaid by R10,785
- **Jacqui transfers R10,785 to Michael**

## Year-End Tax Refunds

### Michael gets R10,000 refund in December

**December Income Sheet:**
```
Description          | Amount  | Type
---------------------|---------|--------
Take-home Salary     | 68633   | Salary
Tax Refund           | 10000   | Other
```

**December calculation:**
```
Michael NET: R68,633 + R10,000 = R78,633
Jacqui NET:  R38,520
Total NET:   R117,153

New proportions:
  Michael: 67.1%
  Jacqui:  32.9%

Shared expenses (R30,000):
  Michael pays: R20,136
  Jacqui pays:  R9,864
```

**Result:** Michael's higher income (including refund) means he pays slightly more that month. Fair!

## GROSS vs NET Comparison

### NET Mode (Default)
```bash
python main.py --person-sheets FILE1 FILE2
```
- Enter take-home pay from payslips
- No tax calculation
- Simpler, fewer moving parts

### GROSS Mode
```bash
python main.py --person-sheets FILE1 FILE2 --use-gross
```
- Enter gross salary (before tax)
- System calculates tax automatically
- More detailed analysis
- Useful if you want tax breakdowns

## Which Mode Should You Use?

### Use NET Mode (Default) If:
- ✅ You have payslips with NET amounts
- ✅ You want simplicity
- ✅ You don't care about tax details
- ✅ Tax is correctly deducted by employer

### Use GROSS Mode If:
- You want detailed tax analysis
- You like seeing tax breakdowns
- You're verifying employer tax calculations
- You have complete payslip details

**For most people: NET mode is simpler and recommended!**

## Practical Examples

### Example 1: Regular Month

**Michael's Income Sheet:**
```
Description              | Amount  | Type
-------------------------|---------|--------
Salary (NET from slip)   | 68633   | Salary
```

**Jacqui's Income Sheet:**
```
Description              | Amount  | Type
-------------------------|---------|--------
Salary (NET from slip)   | 38520   | Salary
```

Process:
```bash
python main.py --next
```

Result:
- Split 64.1% / 35.9%
- Settlement calculated
- Done!

### Example 2: Bonus Month

**Michael's Income Sheet:**
```
Description              | Amount  | Type
-------------------------|---------|--------
Salary (NET)             | 68633   | Salary
Bonus (after tax)        | 8500    | Salary
```

Total NET for Michael: R77,133
Split adjusts to ~66.7% / 33.3%

### Example 3: Tax Refund

**Michael's Income Sheet (December):**
```
Description              | Amount  | Type
-------------------------|---------|--------
Salary (NET)             | 68633   | Salary
Tax Refund from SARS     | 15000   | Other
```

Total NET for Michael: R83,633
Split adjusts to ~68.5% / 31.5%

Jacqui benefits proportionally from Michael's refund!

### Example 4: Rental Income

**Jacqui's Income Sheet:**
```
Description              | Amount  | Type
-------------------------|---------|--------
Salary (NET)             | 38520   | Salary
Rental (after costs)     | 6500    | Rental
```

Total NET for Jacqui: R45,020
Split adjusts to benefit both partners

## Common Questions

### "Do I enter gross or net salary?"
**NET** - The amount that hits your bank account (take-home pay).

### "What about tax refunds?"
Add them as income in the month you receive them (Type: Other).

### "Can I switch modes?"
Yes! Use `--use-gross` flag for GROSS mode. But be consistent within a year.

### "What if I paid too much tax all year?"
When you get the refund, add it to your Income sheet. The system adjusts your proportion for that month.

### "Is this fair?"
Yes! The refund represents income that was withheld. Both partners should benefit proportionally.

## Template Instructions

When you create templates:
```bash
python main.py --create-templates Michael Jacqui
```

The templates now say:
```
** DEFAULT MODE: NET INCOME (Take-Home Pay) **

Income Sheet:
- Use NET amounts (take-home pay from payslip)
- Tax refunds: Add as 'Other' income type
```

## Command Reference

### Default (NET Mode)
```bash
# Process with NET income
python main.py --person-sheets FILE1 FILE2

# Auto-detect next month (NET mode)
python main.py --next
```

### GROSS Mode
```bash
# Process with GROSS income (calculates tax)
python main.py --person-sheets FILE1 FILE2 --use-gross

# Auto-detect with GROSS mode
python main.py --next --use-gross
```

### Checkpoint Summary
```bash
# View all months
python main.py --checkpoint-summary
```

## Migration from Old System

If you were using GROSS mode before:

### Option 1: Continue with GROSS
```bash
python main.py --next --use-gross
```

### Option 2: Switch to NET
1. Update your templates with NET amounts
2. Process new months without `--use-gross` flag
3. Add tax refunds as income when received

**Note:** You can mix modes in checkpoint (GROSS for old months, NET for new), but it's cleaner to be consistent.

## Summary

**Default: NET Income Mode**
- ✅ Enter take-home pay from payslips
- ✅ Add tax refunds as income when received
- ✅ System splits based on NET income
- ✅ Simple, accurate, fair

**Example workflow:**
```bash
# 1. Create templates
python main.py --create-templates Michael Jacqui

# 2. Fill with NET amounts from payslips

# 3. Process
python main.py --next

# 4. Make transfer
# Done!
```

**For GROSS mode:** Add `--use-gross` flag to any command.
