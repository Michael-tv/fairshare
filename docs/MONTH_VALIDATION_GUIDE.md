# Month Validation Guide

## Overview

The month validation system ensures that transaction processing only includes **complete months** with data from **all persons/accounts**. This prevents partial month data from skewing financial calculations.

## Why Month Validation Matters

### Problem: Partial Month Data

Bank statements often don't align with calendar months:

**Example 1: Mid-Month Statement**
```
Credit Card Statement: Sept 7 to Oct 5
├─ September: Partial (missing Sept 1-6)
├─ October: Partial (missing Oct 6-31)
└─ Complete months: None
```

**Example 2: Misaligned Persons**
```
Michael:  Aug 1 - Aug 31, Sept 1 - Sept 30  ✓ Complete months: Aug, Sept
Jacqui:   Sept 15 - Oct 14                  ✗ Complete months: None
Common:   None (no overlap)
```

### Solution: Validation & Filtering

The system:
1. **Validates** that each person/account has complete month coverage
2. **Identifies** which months ALL persons have complete data for
3. **Filters** transactions to only include those complete months
4. **Reports** which months will be processed

## How It Works

### Complete Month Definition

A month is **complete** for a person/account if:
- Data starts on the 1st day of the month
- Data ends on the last day of the month (28/29/30/31 depending on month)

### Common Complete Months

A month is **common** across all persons if:
- ALL persons have complete data for that month
- ALL shared accounts have complete data for that month

Only common complete months are processed.

## Commands

### Validate Data Completeness

```bash
python main.py --validate-months
```

Shows:
- Transaction count per person/account
- Date range per person/account
- Complete months per person/account
- Common complete months (intersection of all)

**Example Output:**

```
================================================================================
TRANSACTION DATA VALIDATION
================================================================================

Michael:
  Transactions: 145
  Date range: 2025-08-01 to 2025-09-30
  Complete months: 2025-08, 2025-09

Jacqui:
  Transactions: 98
  Date range: 2025-08-01 to 2025-09-30
  Complete months: 2025-08, 2025-09

Shared: Credit Card:
  Transactions: 67
  Date range: 2025-08-05 to 2025-09-28
  Complete months: None (partial month data)

--------------------------------------------------------------------------------
COMMON COMPLETE MONTHS (all persons):
--------------------------------------------------------------------------------
  None - no complete months with data from all persons

================================================================================

[!] No complete months found
Ensure all persons/accounts have statement data covering full months
(from 1st to last day of the month)
```

### Automatic Validation During Processing

```bash
python main.py --process-all
```

Validation runs automatically:

```
================================================================================
TRANSACTION PROCESSING PIPELINE
================================================================================

Working directory: data
Mode: INCREMENTAL (new files only)

────────────────────────────────────────────────────────────────────────────────
Validating transaction data completeness
────────────────────────────────────────────────────────────────────────────────

[... validation report ...]

[OK] Will process 2 complete months: 2025-08, 2025-09
```

## Common Scenarios

### Scenario 1: Partial Months at Statement Boundaries

**Problem:**
```
Credit Card: Sept 7 to Oct 5
```

**Why Incomplete:**
- September is missing days 1-6 (incomplete)
- October is missing days 6-31 (incomplete)

**Solution:**
- Provide August statement (e.g., Aug 7 - Sept 6)
- Then September becomes complete: Sept 7 (from Sept stmt) + Sept 1-6 (from Aug stmt)
- OR manually enter missing transactions

### Scenario 2: One Person Missing Data

**Problem:**
```
Michael:  Complete months: Aug, Sept, Oct
Jacqui:   Complete months: Sept, Oct, Nov
Common:   Sept, Oct only
```

**Why Only Sept/Oct:**
- Michael missing November
- Jacqui missing August

**Solution:**
- Add Michael's November statement
- Add Jacqui's August statement
- Then all three months (Aug, Sept, Oct, Nov) become common

### Scenario 3: No Statements (Manual Entry)

**Problem:**
```
Michael: Has statements
Jacqui:  No statements (privacy, no bank statements available)
```

**Solution:**
Use manual transaction file:

1. Create `data/raw/person_sheets/Jacqui_transactions.xlsx`:
   ```
   | date       | description      | amount  | category  | type       |
   |------------|------------------|---------|-----------|------------|
   | 2025-08-01 | Salary           | 30000   | SALARY    | INCOME     |
   | 2025-08-15 | Groceries        | 2500    | GROCERIES | SHARED     |
   | 2025-08-31 | Final transaction| 100     | OTHER     | INDIVIDUAL |
   ```

2. Ensure data covers full months (1st to last day)

3. Leave `data/raw/statements/Jacqui/` empty

4. System will use manual file and validate completeness

## Fixing Incomplete Data

### Option 1: Add More Statements

If you have partial months, add adjacent statements:

```bash
# Before
data/raw/statements/Michael/
└── sept_statement.pdf  (Sept 7 - Oct 5)

# After (add previous statement)
data/raw/statements/Michael/
├── aug_statement.pdf   (Aug 7 - Sept 6)
└── sept_statement.pdf  (Sept 7 - Oct 5)

Result: September is now complete!
```

### Option 2: Manual Transaction Entry

For missing days at month boundaries:

1. Identify missing date ranges from validation output
2. Manually enter transactions for those dates
3. Add to person's manual file or create supplemental Excel

### Option 3: Accept Partial Coverage

If you can't get complete months:

**Understand the impact:**
- Partial months will be excluded from processing
- Financial calculations will only cover complete months
- You may need to manually calculate partial months separately

## Technical Details

### Validation Logic

**File:** `src/month_validator.py`

**Key Methods:**

```python
validator = MonthValidator()

# Check date range
min_date, max_date = validator.get_transaction_date_range(transactions)

# Determine complete months
complete_months = validator.get_complete_months(min_date, max_date)
# Returns: [(2025, 8), (2025, 9)] for Aug and Sept

# Validate all statements
validation_results = validator.validate_statements_coverage(statement_files)

# Find intersection
common_months = validator.get_common_complete_months(validation_results)

# Filter transactions
filtered_txns = validator.filter_transactions_by_months(
    transactions,
    common_months
)
```

### Complete Month Algorithm

**For minimum date:**
- If min_date is 1st of month: include that month
- Otherwise: start from next month

**For maximum date:**
- If max_date is last day of month: include that month
- Otherwise: end at previous month

**Example:**
```python
min_date = 2025-08-05  # Not the 1st
max_date = 2025-10-28  # Not the last day (Oct has 31 days)

# August: Excluded (starts on 5th, not 1st)
# September: Included (fully covered from Sept 1-30)
# October: Excluded (ends on 28th, not 31st)

complete_months = [(2025, 9)]  # Only September
```

### Filtering in Processing Pipeline

**File:** `src/transaction_processor.py`

When processing statements:

```python
# 1. Parse all transactions
all_transactions = parse_statements(pdf_files)
print(f"Total: {len(all_transactions)} transactions (before filtering)")

# 2. Filter to complete months only
if self.valid_months:
    all_transactions = self.validator.filter_transactions_by_months(
        all_transactions,
        self.valid_months
    )
    print(f"Filtered to complete months: {len(all_transactions)} transactions")

# 3. Continue with classification, matching, etc.
```

## Integration with Transaction Processing

### Automatic Validation

Every `--process-all` run:

1. **Step 0:** Validate data completeness
   - Parse all statements to extract date ranges
   - Determine complete months per person
   - Find common complete months
   - Display validation report

2. **Step 1-4:** Process transactions
   - Only include transactions from common complete months
   - Filtered before classification
   - Ensures consistent date ranges across all persons

### Manual Override (Not Implemented)

Future enhancement:
```bash
# Force processing specific months (even if incomplete)
python main.py --process-all --force-months 2025-08,2025-09

# Skip validation entirely (not recommended)
python main.py --process-all --skip-validation
```

## Troubleshooting

### "No complete months found"

**Cause:** No month has data from 1st to last day for ALL persons.

**Solutions:**
1. Check date ranges with `--validate-months`
2. Add missing statements to cover month boundaries
3. Use manual transaction files for missing data
4. Verify statement parsing is working (use `--parse-bank-statement`)

### "Transactions: 0" for a person

**Cause:** Statement parser couldn't extract transactions from PDF.

**Solutions:**
1. Check if PDF is encrypted (requires password)
2. Verify statement format matches parser expectations (FNB format)
3. Try `--parse-bank-statement file.pdf` to debug parsing
4. Use manual transaction file as workaround

### Only 1-2 months processed when expecting more

**Cause:** Persons have different statement periods.

**Solutions:**
1. Run `--validate-months` to see each person's complete months
2. Add statements to align date ranges
3. Check that all persons have overlapping coverage

## Best Practices

### 1. Validate Before Processing

Always run validation first:

```bash
python main.py --validate-months
# Review output
# Add missing data if needed
python main.py --process-all
```

### 2. Align Statement Dates

Request monthly statements for the same period:
- All statements should cover Aug 1 - Aug 31
- Avoid misaligned periods (e.g., Aug 5 - Sept 4)

### 3. Keep Adjacent Statements

Don't delete old statements:
- September's statement (Sept 7 - Oct 5) needs August's statement
- Keep at least 2 adjacent statements to cover month boundaries

### 4. Use Manual Files for Gaps

If statements have gaps:
- Create manual transaction file for missing periods
- Ensure manual file covers 1st to last day of month

### 5. Monitor Validation Output

During `--process-all`, check:
```
[OK] Will process 3 complete months: 2025-08, 2025-09, 2025-10
```

If fewer months than expected, investigate.

## Example Workflow

### Complete Example: From No Data to Processed

**Step 1: Initial Setup**
```bash
python main.py --create-config
python main.py --init-workspace
```

**Step 2: Add Statements**
```bash
cp ~/Downloads/michael_aug.pdf data/raw/statements/Michael/
cp ~/Downloads/michael_sept.pdf data/raw/statements/Michael/
cp ~/Downloads/jacqui_aug.pdf data/raw/statements/Jacqui/
cp ~/Downloads/jacqui_sept.pdf data/raw/statements/Jacqui/
cp ~/Downloads/credit_card_aug.pdf data/raw/statements/shared/
```

**Step 3: Validate**
```bash
python main.py --validate-months
```

Output shows:
```
Michael: Complete months: 2025-08, 2025-09
Jacqui: Complete months: 2025-08, 2025-09
Shared Credit Card: Complete months: 2025-08

COMMON COMPLETE MONTHS: 2025-08
```

**Analysis:** Only August is common (September missing from credit card).

**Step 4: Fix (Add Missing Statement)**
```bash
cp ~/Downloads/credit_card_sept.pdf data/raw/statements/shared/
```

**Step 5: Re-validate**
```bash
python main.py --validate-months
```

Output now shows:
```
COMMON COMPLETE MONTHS: 2025-08, 2025-09
```

**Step 6: Process**
```bash
python main.py --process-all
```

Processes both August and September!

## Related Files

**Implementation:**
- [src/month_validator.py](src/month_validator.py) - Core validation logic
- [src/transaction_processor.py](src/transaction_processor.py) - Integration with processing pipeline
- [main.py](main.py) - CLI command (`--validate-months`)

**Documentation:**
- [QUICK_START.md](QUICK_START.md) - Updated with validation steps
- This file - Complete validation guide

## Summary

Month validation ensures:
- ✅ Only complete months (1st to last day) are processed
- ✅ All persons have data for the same months
- ✅ Financial calculations are accurate
- ✅ Partial month data doesn't skew results
- ✅ Clear visibility into what will be processed

Always run `--validate-months` before `--process-all` to ensure data quality!
