# Quick Start Guide - New Config-Driven Workflow

## Installation

### 1. Install UV Package Manager

```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Dependencies

```bash
cd home_finances
uv sync
```

This will install all dependencies from `pyproject.toml`.

## Initial Setup

### 1. Create Configuration

```bash
python main.py --create-config
```

This creates `config.json` from the template. Edit it with your details:

```json
{
  "working_dir": "data",
  "persons": [
    {
      "name": "Michael",
      "statements_folder": "raw/statements/Michael"
    },
    {
      "name": "Jacqui",
      "statements_folder": "raw/statements/Jacqui"
    }
  ],
  "shared_accounts": [
    {
      "name": "Joint Credit Card",
      "statements_folder": "raw/statements/shared"
    }
  ],
  "matching": {
    "amount_tolerance": 1.00,
    "date_tolerance_days": 3,
    "merchant_similarity_threshold": 0.6
  },
  "classification": {
    "enabled": true,
    "default_shared_type": "SHARED"
  }
}
```

### 2. Initialize Workspace

```bash
python main.py --init-workspace
```

This creates the folder structure:

```
data/
├── raw/
│   ├── slips/                      # Put invoice receipts here
│   ├── statements/
│   │   ├── Michael/                # Put Michael's statements here
│   │   ├── Jacqui/                 # Put Jacqui's statements here
│   │   └── shared/                 # Put joint credit card statements here
│   └── person_sheets/              # Optional: manual transaction files
└── processed/                       # Auto-generated outputs
    ├── transactions/
    ├── slips/
    ├── matching/
    ├── monthly_splits/
    └── checkpoint/
```

### 3. Add Your Data

```bash
# Copy your bank statement PDFs
cp ~/Downloads/bank_statement.pdf data/raw/statements/Michael/
cp ~/Downloads/credit_card.pdf data/raw/statements/shared/

# Copy invoice slips
cp ~/Downloads/receipts/*.pdf data/raw/slips/
```

## Processing Transactions

### Validate Data Completeness (Recommended First Step)

```bash
python main.py --validate-months
```

This checks that you have complete transaction data for full months. A complete month has:
- Data from the 1st to the last day of the month
- All persons/accounts covered for the same months

**Example Output:**
```
Michael:
  Transactions: 0
  Date range: No data

Shared: Credit Card:
  Transactions: 26
  Date range: 2025-09-07 to 2025-10-05
  Complete months: None (partial month data)

COMMON COMPLETE MONTHS (all persons):
  None - no complete months with data from all persons
```

**What This Means:**
- If you have partial months (e.g., Sept 7-30 instead of Sept 1-30), those months will be excluded
- Only complete months that ALL persons have data for will be processed
- Add more statements or manual data to cover full months

### First Time (Full Process)

```bash
python main.py --process-all --force
```

This will:
1. ✅ Validate data completeness (shows complete months)
2. ✅ Parse all bank statements
3. ✅ Filter to complete months only
4. ✅ Auto-classify transactions (category + SHARED/INDIVIDUAL)
5. ✅ Parse invoice slips
6. ✅ Match slips to transactions
7. ✅ Export to Excel with classification columns

### Subsequent Runs (Incremental)

```bash
python main.py --process-all
```

Only processes new/modified files. Much faster!

## Review and Edit

### 1. Open Transactions File

```bash
# Open in Excel/LibreOffice
data/processed/transactions/all_transactions_combined.xlsx
```

### 2. Review Auto-Classification

The file has these columns:

| Column | Description | Editable? |
|--------|-------------|-----------|
| `auto_category` | System assigned | ❌ No (preserved) |
| `user_category` | Your override | ✅ Yes |
| `final_category` | = user if set, else auto | 📊 Formula |
| `auto_type` | SHARED or INDIVIDUAL | ❌ No (preserved) |
| `user_type` | Your override | ✅ Yes |
| `final_type` | = user if set, else auto | 📊 Formula |
| `needs_review` | Low confidence flag | ℹ️ Info |
| `user_notes` | Your comments | ✅ Yes |

### 3. Make Changes

- Fill in `user_category` to override auto-classification
- Fill in `user_type` to override SHARED/INDIVIDUAL
- Add notes in `user_notes` column

### 4. Re-Process

```bash
python main.py --process-all
```

Your edits are preserved! Only new transactions are added.

## Common Commands

### Check Status

```bash
python main.py --status
```

Shows:
- Number of slips found
- Statements per person
- Processing status

### Force Reprocess Everything

```bash
python main.py --process-all --force
```

**Warning**: This will reprocess all files. Use when:
- You want to apply updated classification rules
- Something went wrong
- You changed config significantly

### Manual Transactions (No Statements)

If someone doesn't want to share bank PDFs:

1. Create `data/raw/person_sheets/Person_transactions.xlsx` with:
   - Columns: `date`, `description`, `amount`, `category`, `type`

2. Leave their statements folder empty

3. Run `--process-all`

System will use the manual file instead.

## Example Workflow

```bash
# 1. Initial setup
python main.py --create-config
# Edit config.json
python main.py --init-workspace

# 2. Add data
cp statements/*.pdf data/raw/statements/Michael/
cp receipts/*.pdf data/raw/slips/

# 3. Process
python main.py --process-all --force

# 4. Review in Excel
# Edit: data/processed/transactions/Michael_transactions.xlsx

# 5. Reprocess with edits
python main.py --process-all

# 6. Check results
python main.py --status
```

## Migration from Old Workflow

If you have existing data:

```bash
# 1. Backup
cp financial_checkpoint.json financial_checkpoint.json.backup

# 2. Create config
python main.py --create-config

# 3. Reorganize files
python main.py --init-workspace

# Move your PDFs
mv "old_location/statements/"*.pdf data/raw/statements/Michael/
mv "old_location/slips/"*.pdf data/raw/slips/

# 4. Process
python main.py --process-all --force
```

## Troubleshooting

### "Config file not found"

```bash
python main.py --create-config
# Then edit config.json
```

### "No statements found"

Check folder paths in config.json match where you put PDFs:

```bash
python main.py --status
```

### "Want to redo everything"

```bash
python main.py --process-all --force
```

### "Classification is wrong"

1. Override in Excel (`user_category` column)
2. Or add custom rules to `src/transaction_classifier.py`

## Old Commands Still Work!

All existing commands work unchanged:

```bash
python main.py --demo
python main.py --match-slips --statements file.pdf
python main.py --person-sheets Person1.xlsx Person2.xlsx
```

## Deferred Payments

Track expenses that should have been paid but were missed and will be paid later.

### Add a Deferred Payment

```bash
python main.py --add-deferred
```

Interactive prompts will ask for:
- Description (e.g., "September Electricity Bill")
- Amount
- Category (Utilities, Groceries, etc.)
- Expense type (SHARED or INDIVIDUAL)
- Accrual month (when expense occurred)
- Expected payment month (when you'll pay)
- Responsible person
- Reason for deferral

### List Pending Payments

```bash
python main.py --list-deferred
```

Shows all unpaid deferred payments grouped by person.

### Mark a Payment as Paid

```bash
python main.py --mark-paid DEF202509150001
```

Replace `DEF202509150001` with the actual payment ID from `--list-deferred`.

### Manual Excel Editing

You can also directly edit `data/processed/deferred_payments.xlsx`:
- Add rows for new deferred payments
- Update `status` column to `PAID` when paid
- Update `paid_by` and `payment_month` when marking as paid

See [DEFERRED_PAYMENTS_GUIDE.md](DEFERRED_PAYMENTS_GUIDE.md) for detailed documentation.

## Next Steps

- See [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for architecture details
- See [CLAUDE.md](CLAUDE.md) for original system documentation
- See [SLIP_MATCHING_README.md](SLIP_MATCHING_README.md) for matching details
- See [DEFERRED_PAYMENTS_GUIDE.md](DEFERRED_PAYMENTS_GUIDE.md) for deferred payments

## Getting Help

```bash
python main.py --help
python main.py --status
python main.py --list-deferred
```

Check the output directories:
- `data/processed/transactions/` - Your classified transactions
- `data/processed/matching/` - Slip matching results
- `data/processed/deferred_payments.xlsx` - Deferred/pending payments
