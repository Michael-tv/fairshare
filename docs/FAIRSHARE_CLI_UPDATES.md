# FairShare CLI Updates

## Overview

The home finances system has been renamed to **FairShare** with simplified CLI commands focused on the core workflow: processing statements and calculating fair share splits.

## Changes Implemented

### 1. Renamed main.py → fairshare.py

**Before:**
```bash
python main.py --process-all
```

**After:**
```bash
python fairshare.py --process-statements
```

### 2. Replaced `--process-all` with `--process-statements`

**New Command:**
```bash
# Process all users from config
python fairshare.py --process-statements

# Process specific user only
python fairshare.py --process-statements --user-dir "Michael"

# Force reprocess everything
python fairshare.py --process-statements --force
```

**Functionality:**
- Processes bank statements for configured users
- Auto-classifies transactions (category + SHARED/INDIVIDUAL)
- Outputs one Excel file per person
- Supports incremental processing (only new months)
- Can filter to specific user with `--user-dir`

**Output Files:**
- `data/processed/transactions/Michael_transactions.xlsx`
- `data/processed/transactions/Jacqui_transactions.xlsx`

**Excel Columns:**
- `transaction_id`, `date`, `description`, `amount`
- `auto_category`, `user_category`, `final_category`
- `auto_type`, `user_type`, `final_type`
- `slip_matched`, `match_confidence`, `needs_review`, `user_notes`

### 3. New `--calculate-split` Command

**Usage:**
```bash
# Use classified files from data/processed/transactions/
python fairshare.py --calculate-split

# Or specify custom paths
python fairshare.py --calculate-split person1.xlsx person2.xlsx
```

**Functionality:**
- Reads classified transaction Excel files
- Groups by month
- Calculates income proportions
- Determines shared expense split
- Shows who owes whom
- Outputs monthly breakdown + cumulative summary
- Saves results to Excel and displays in console

**Output:**
- Console report (see example below)
- `data/processed/fair_share_calculation.xlsx`

### 4. New `--user-dir` Parameter

**Purpose:** Process statements for specific user only

**Usage:**
```bash
python fairshare.py --process-statements --user-dir "Michael"
```

**Effect:**
- Only processes Michael's statements
- Skips other users in config
- Useful for privacy (process each user separately)
- Faster when only one user has new data

## Complete Workflow

### Step 1: Initial Setup
```bash
python fairshare.py --create-config
# Edit config.json with your persons and folders

python fairshare.py --init-workspace
# Creates folder structure
```

### Step 2: Add Statements
```bash
# Add bank statement PDFs
cp statements/*.pdf data/raw/statements/Michael/
cp statements/*.pdf data/raw/statements/Jacqui/
cp credit_card.pdf data/raw/statements/shared/
```

### Step 3: Validate Data
```bash
python fairshare.py --validate-months
# Check that you have complete month data
```

**Example Output:**
```
Michael:
  Transactions: 145
  Date range: 2025-08-01 to 2025-09-30
  Complete months: 2025-08, 2025-09

Jacqui:
  Transactions: 98
  Date range: 2025-08-01 to 2025-09-30
  Complete months: 2025-08, 2025-09

COMMON COMPLETE MONTHS: 2025-08, 2025-09
```

### Step 4: Process Statements
```bash
python fairshare.py --process-statements
```

**Output:**
```
TRANSACTION PROCESSING PIPELINE
Working directory: data
Mode: INCREMENTAL

Validating transaction data completeness...
Found 2 complete months: 2025-08, 2025-09
Will process 2 new months: 2025-08, 2025-09

Processing: Michael
  Parsing 2 statement(s)...
  Total: 145 transactions
  Filtered to complete months: 145 transactions
  Classifying transactions...
  Saved: data/processed/transactions/Michael_transactions.xlsx

Processing: Jacqui
  Parsing 2 statement(s)...
  Total: 98 transactions
  Filtered to complete months: 98 transactions
  Classifying transactions...
  Saved: data/processed/transactions/Jacqui_transactions.xlsx

PROCESSING COMPLETE!
Marked as processed: 2025-08, 2025-09
```

### Step 5: Review & Edit Classifications

Open the Excel files:
- `data/processed/transactions/Michael_transactions.xlsx`
- `data/processed/transactions/Jacqui_transactions.xlsx`

**Edit:**
- Fill in `user_category` to override auto-classification
- Fill in `user_type` to override SHARED/INDIVIDUAL
- Add notes in `user_notes` column

**Example:**
```
Transaction: "Woolworths"
auto_category: GROCERIES
user_category: [leave blank if correct, or enter: ENTERTAINMENT]
auto_type: SHARED
user_type: [leave blank if shared, or enter: INDIVIDUAL]
final_category: =IF(user_category="", auto_category, user_category)
final_type: =IF(user_type="", auto_type, user_type)
```

### Step 6: Calculate Fair Share

```bash
python fairshare.py --calculate-split
```

**Example Output:**
```
================================================================================
FAIR SHARE CALCULATION
================================================================================

Using processed transaction files:
  Michael: data/processed/transactions/Michael_transactions.xlsx
  Jacqui: data/processed/transactions/Jacqui_transactions.xlsx

Loading transaction data...
Found 2 common months: 2025-08, 2025-09

================================================================================
MONTHLY BREAKDOWN
================================================================================

2025-08:
  Income: Michael R45,000.00 (64.3%) | Jacqui R25,000.00 (35.7%)
  Total Shared Expenses: R12,500.00
  Transfer: Jacqui → Michael: R2,343.75

2025-09:
  Income: Michael R45,000.00 (64.3%) | Jacqui R25,000.00 (35.7%)
  Total Shared Expenses: R13,200.00
  Transfer: Jacqui → Michael: R2,476.20

================================================================================
CUMULATIVE SUMMARY
================================================================================

Total paid by Michael: R16,250.00
Total paid by Jacqui: R9,450.00

** NET: Jacqui should transfer R6,800.00 to Michael **

Results saved to: data/processed/fair_share_calculation.xlsx
```

### Step 7: Review Results

Open `data/processed/fair_share_calculation.xlsx` for detailed breakdown.

## User-Specific Processing

### Scenario: Privacy - Process Each User Separately

**Michael processes his own statements:**
```bash
python fairshare.py --process-statements --user-dir "Michael"
```

**Jacqui processes her own statements:**
```bash
python fairshare.py --process-statements --user-dir "Jacqui"
```

**Then calculate split together:**
```bash
python fairshare.py --calculate-split
```

**Result:** Each person only needs to process their own data. The calculate-split command uses the resulting files from both.

## Incremental Processing

### Month 1 (August):
```bash
python fairshare.py --process-statements
# Processes: August
# Output: Michael_transactions.xlsx, Jacqui_transactions.xlsx (August data)

python fairshare.py --calculate-split
# Calculates: August split
```

### Month 2 (September - Add New Data):
```bash
# Add September statements
cp sept_*.pdf data/raw/statements/Michael/
cp sept_*.pdf data/raw/statements/Jacqui/

python fairshare.py --process-statements
# Processes: Only September (August already done)
# Output: Updated Excel files with September data added

python fairshare.py --calculate-split
# Calculates: August + September (cumulative)
```

## Output Excel Format

### Transaction Files (per person)

**File:** `data/processed/transactions/Michael_transactions.xlsx`

| Column | Description | Editable |
|--------|-------------|----------|
| transaction_id | Unique ID | No |
| date | Transaction date | No |
| description | Transaction description | No |
| amount | Amount (R) | No |
| account | Account type | No |
| card_last_digits | Card number (last 4) | No |
| **auto_category** | System classification | No |
| **user_category** | User override | Yes |
| **final_category** | =IF(user="", auto, user) | Formula |
| **auto_type** | SHARED/INDIVIDUAL | No |
| **user_type** | User override | Yes |
| **final_type** | =IF(user="", auto, user) | Formula |
| slip_matched | Matched to receipt | No |
| match_confidence | Match score | No |
| needs_review | Low confidence flag | No |
| user_notes | Your notes | Yes |

### Fair Share Calculation File

**File:** `data/processed/fair_share_calculation.xlsx`

| Column | Description |
|--------|-------------|
| month | YYYY-MM |
| person1_income | Income earned |
| person2_income | Income earned |
| person1_proportion | % of household income |
| person2_proportion | % of household income |
| total_shared | Total shared expenses |
| person1_paid | What person 1 actually paid |
| person2_paid | What person 2 actually paid |
| person1_should_pay | Fair share based on income |
| person2_should_pay | Fair share based on income |
| transfer_from | Who owes money |
| transfer_to | Who should receive |
| transfer_amount | How much to transfer |

## Commands Kept Unchanged

The following commands still work as before:

**Month Validation:**
```bash
python fairshare.py --validate-months
```

**Deferred Payments:**
```bash
python fairshare.py --add-deferred
python fairshare.py --list-deferred
python fairshare.py --mark-paid DEF202509150001
```

**Slip Matching:**
```bash
python fairshare.py --match-slips --statements file.pdf
```

**Workspace:**
```bash
python fairshare.py --init-workspace
python fairshare.py --status
```

## Key Benefits

### 1. Clear Workflow
- `--process-statements`: Input (bank statements) → Output (classified transactions)
- `--calculate-split`: Input (classified transactions) → Output (fair share calculation)

### 2. User Privacy
- `--user-dir` allows processing one user at a time
- Users don't need to share raw bank statements
- Can exchange only classified Excel files

### 3. Incremental Updates
- Only processes new complete months
- Fast subsequent runs
- Maintains history across months

### 4. Transparency
- All auto-classifications visible in Excel
- User can override any classification
- Clear separation: auto vs user vs final

### 5. Comprehensive Output
- Monthly breakdown of splits
- Cumulative totals across all months
- Both console and Excel reports

## Migration from Old Commands

**Old:**
```bash
python main.py --process-all
```

**New:**
```bash
python fairshare.py --process-statements
```

**Old:**
```bash
python main.py --person-sheets Michael_Aug.xlsx Jacqui_Aug.xlsx
```

**New:**
```bash
# Now handles statements automatically:
python fairshare.py --process-statements
python fairshare.py --calculate-split
```

## Troubleshooting

### "Transaction files not found"
**Problem:** Running `--calculate-split` before `--process-statements`

**Solution:**
```bash
python fairshare.py --process-statements
python fairshare.py --calculate-split
```

### "No common months found"
**Problem:** Transaction files have different month coverage

**Solution:**
```bash
python fairshare.py --validate-months
# Add missing statements for common months
python fairshare.py --process-statements --force
```

### User-dir not found
**Problem:** Typo in user name

**Solution:**
```bash
# Check config for exact names
cat config.json | grep name
# Use exact match
python fairshare.py --process-statements --user-dir "Michael"
```

## Summary

The FairShare CLI now provides a streamlined workflow:

1. **Process statements** → Get classified transactions (one Excel per person)
2. **Edit classifications** → Review and override in Excel
3. **Calculate split** → Get fair share breakdown (monthly + cumulative)

All while maintaining:
- ✅ Month validation
- ✅ Incremental processing
- ✅ User privacy options
- ✅ Deferred payments
- ✅ Complete audit trail
