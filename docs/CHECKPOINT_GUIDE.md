# Checkpoint System Guide

## Overview

The checkpoint system automatically tracks your monthly financial calculations and maintains a running total of cumulative transfers. This makes it easy to:

- Track month-over-month data
- See cumulative transfer amounts
- Auto-detect next month's files
- Keep a complete financial history

## How It Works

When you process monthly data with `--person-sheets`, the system:

1. **Saves the results** to a checkpoint file (`financial_checkpoint.json`)
2. **Tracks monthly transfers** - who should pay whom each month
3. **Calculates cumulative totals** - running total across all months
4. **Remembers file patterns** - auto-detects next month's files

## Quick Start

### First Month
```bash
# Process April 2024
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx
```

This creates `financial_checkpoint.json` with April's data.

### Next Month (Auto-Detect)
```bash
# Just run --next and it figures out the files!
python main.py --next
```

The system:
- Looks at your last processed month (April 2024)
- Determines next month is May 2024
- Looks for `Michael_May_2024.xlsx` and `Jacqui_May_2024.xlsx`
- Processes them automatically

### View Cumulative Summary
```bash
python main.py --checkpoint-summary
```

Shows:
- All months processed
- Monthly transfers
- **CUMULATIVE NET** - who owes whom overall

## Example Workflow

### Month 1: April 2024
```bash
$ python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx

# Results:
- Jacqui should transfer R5,047.47 to Michael
- [OK] Checkpoint saved
```

### Month 2: May 2024 (Auto)
```bash
$ python main.py --next

# System auto-detects:
- Expected files: Michael_May_2024.xlsx, Jacqui_May_2024.xlsx
- [OK] Files found!

# Results:
- Michael should transfer R2,500.00 to Jacqui (this month)
- Shows cumulative summary
```

### View Cumulative
```bash
$ python main.py --checkpoint-summary

====================================================================================================
MONTHLY CHECKPOINT SUMMARY
====================================================================================================

Month                          Gross Income      Shared Exp                  Transfer
                   Michael         Jacqui                       Amount   From -> To
----------------------------------------------------------------------------------------------------
2024-04      R   75,000.00  R   30,000.00 R    38,129.74 R   5,047.47 Jac->Mic
2024-05      R   80,000.00  R   32,000.00 R    40,000.00 R   2,500.00 Mic->Jac
----------------------------------------------------------------------------------------------------
TOTAL        R  155,000.00  R   62,000.00 R    78,129.74

====================================================================================================
CUMULATIVE TRANSFERS
====================================================================================================
Total Michael -> Jacqui: R2,500.00
Total Jacqui -> Michael: R5,047.47

** NET: Jacqui should transfer R2,547.47 to Michael **

Months processed: 2
====================================================================================================
```

## Commands

### Process Month (Manual Files)
```bash
python main.py --person-sheets FILE1.xlsx FILE2.xlsx
```

Saves to checkpoint automatically.

### Process Next Month (Auto-Detect)
```bash
python main.py --next
```

OR (equivalent):
```bash
python main.py --person-sheets
```

Auto-detects next month's files based on checkpoint.

### View Checkpoint Summary
```bash
python main.py --checkpoint-summary
```

Shows all months and cumulative transfers.

### Reset Checkpoint
```bash
python main.py --reset-checkpoint
```

**WARNING:** Deletes all historical data. Use with caution!

### Process Without Saving to Checkpoint
```bash
python main.py --person-sheets FILE1.xlsx FILE2.xlsx --no-checkpoint
```

Useful for one-off calculations or testing.

### Custom Checkpoint File
```bash
python main.py --person-sheets FILE1.xlsx FILE2.xlsx --checkpoint-file my_checkpoint.json
```

Use a different checkpoint file (e.g., for different households).

## Checkpoint File Format

The checkpoint is stored as JSON in `financial_checkpoint.json`:

```json
{
  "person1_name": "Michael",
  "person2_name": "Jacqui",
  "monthly_data": {
    "2024-04": {
      "period": "2024-04",
      "person1_file": "Michael_April_2024.xlsx",
      "person2_file": "Jacqui_April_2024.xlsx",
      "person1_gross": "75000.00",
      "person2_gross": "30000.00",
      "transfer_amount": "5047.47",
      "transfer_from": "Jacqui",
      "transfer_to": "Michael",
      ...
    }
  },
  "cumulative": {
    "total_transfers_person1_to_person2": "0.00",
    "total_transfers_person2_to_person1": "5047.47",
    "net_transfer_amount": "5047.47",
    "net_transfer_from": "Jacqui",
    "net_transfer_to": "Michael",
    "months_processed": 1
  }
}
```

## Auto-Detection Logic

The system auto-detects next month's files by:

1. **Reading last month** from checkpoint
2. **Finding file pattern** from last month's filenames
3. **Incrementing month**:
   - `Michael_April_2024.xlsx` → `Michael_May_2024.xlsx`
   - `Michael_2024_04.xlsx` → `Michael_2024_05.xlsx`
4. **Checking if files exist**
5. **Processing if found**

### Supported Filename Patterns

- `Name_MonthName_Year.xlsx` (e.g., `Michael_April_2024.xlsx`)
- `Name_Year_MonthNum.xlsx` (e.g., `Michael_2024_04.xlsx`)
- Mixed formats work too

## Cumulative Transfers Explained

The system tracks:

### Monthly Transfers
Each month shows who should transfer to whom:
- April: Jacqui transfers R5,047.47 to Michael
- May: Michael transfers R2,500.00 to Jacqui

### Cumulative Running Total
Across all months:
- Total Jacqui → Michael: R5,047.47
- Total Michael → Jacqui: R2,500.00
- **NET: Jacqui owes Michael R2,547.47**

### Practical Use

Instead of making monthly transfers, you can:
1. Process each month
2. Look at cumulative net at year end
3. Make ONE annual settlement

OR make monthly transfers and see them accumulate.

## Duplicate Month Detection

If you try to process a month that already exists:

```bash
$ python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx

WARNING: April 2024 already exists in checkpoint!
Overwrite existing data? (y/n):
```

This prevents accidentally processing the same month twice.

## Best Practices

### 1. Consistent Filename Format
Use the same pattern each month:
```
Michael_April_2024.xlsx
Michael_May_2024.xlsx
Michael_June_2024.xlsx
...
```

### 2. Monthly Workflow
```bash
# 1. Each person updates their sheet for the month
# 2. Run auto-detect
python main.py --next

# 3. Review results
python main.py --checkpoint-summary

# 4. Make transfer or note it for later
```

### 3. Backup Checkpoint
The checkpoint file contains your entire history:
```bash
cp financial_checkpoint.json financial_checkpoint_backup.json
```

### 4. Annual Review
```bash
# At year end, view cumulative
python main.py --checkpoint-summary

# Make one settlement
# Then optionally reset for new year
python main.py --reset-checkpoint
```

## Troubleshooting

### "No checkpoint data found"
You haven't processed any months yet. Run:
```bash
python main.py --person-sheets Person1_Month_Year.xlsx Person2_Month_Year.xlsx
```

### "Files not found" with --next
The auto-detected filenames don't exist. Either:
1. Create files with the expected names, OR
2. Specify files manually:
   ```bash
   python main.py --person-sheets ActualFile1.xlsx ActualFile2.xlsx
   ```

### Wrong Month Detected
If filenames don't follow standard patterns, auto-detection might fail. Use manual filenames:
```bash
python main.py --person-sheets FILE1.xlsx FILE2.xlsx
```

### Need to Recalculate a Month
```bash
# Process again (will ask to overwrite)
python main.py --person-sheets Month_File1.xlsx Month_File2.xlsx

# Or reset and start over
python main.py --reset-checkpoint
```

## Advanced Usage

### Multiple Households
Use different checkpoint files:
```bash
# Household 1
python main.py --person-sheets ... --checkpoint-file household1.json

# Household 2
python main.py --person-sheets ... --checkpoint-file household2.json
```

### View Specific Checkpoint
```bash
python main.py --checkpoint-summary --checkpoint-file household1.json
```

### Batch Processing
Process multiple months at once:
```bash
for month in April May June; do
    python main.py --person-sheets Michael_${month}_2024.xlsx Jacqui_${month}_2024.xlsx
done

# View cumulative
python main.py --checkpoint-summary
```

### Export Checkpoint Data
The checkpoint is JSON, so you can process it with other tools:
```python
import json

with open('financial_checkpoint.json') as f:
    data = json.load(f)

# Analyze, export to CSV, create charts, etc.
```

## Summary

**Key Benefits:**
- ✅ Auto-detects next month's files
- ✅ Tracks cumulative transfers
- ✅ Complete financial history
- ✅ Prevents duplicate processing
- ✅ Simple monthly workflow

**Monthly Process:**
1. Create your sheets
2. Run `python main.py --next`
3. Review cumulative with `--checkpoint-summary`
4. Make transfers (or accumulate for annual settlement)

**That's it!** The checkpoint system makes month-to-month tracking effortless.
