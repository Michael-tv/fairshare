# Incremental Month Processing

## Overview

The system now tracks which complete months have been processed and automatically handles:
- **Incremental processing**: Only process new complete months
- **Historical months**: Automatically process older months when data becomes available
- **Future months**: Automatically process newer months when data is added
- **Force reprocessing**: Option to reprocess all months

## How It Works

### Checkpoint Tracking

**Location:** `data/processed/checkpoint/transaction_checkpoint.json`

The checkpoint stores:
```json
{
  "processed_months": ["2025-08", "2025-09", "2025-10"],
  ...
}
```

### Processing Logic

1. **Validation Phase:**
   - Identify all complete months with data from all persons/accounts
   - Check checkpoint for which months have been processed
   - Determine which months need processing

2. **Incremental Mode (Default):**
   - Skip already-processed months
   - Only process new complete months
   - Fast - no redundant work

3. **Force Mode:**
   - Clear processed month tracking
   - Reprocess ALL complete months
   - Use when you want to regenerate everything

## Usage Examples

### Example 1: Initial Processing

**Setup:**
```bash
# Add August statements for all persons
cp michael_aug.pdf data/raw/statements/Michael/
cp jacqui_aug.pdf data/raw/statements/Jacqui/
cp credit_card_aug.pdf data/raw/statements/shared/
```

**Process:**
```bash
python main.py --process-all
```

**Output:**
```
Found 1 complete months: 2025-08
[OK] Will process 1 new months: 2025-08

Processing...
Marked as processed: 2025-08
```

### Example 2: Add New Month (Future)

**Add September data:**
```bash
cp michael_sept.pdf data/raw/statements/Michael/
cp jacqui_sept.pdf data/raw/statements/Jacqui/
cp credit_card_sept.pdf data/raw/statements/shared/
```

**Process:**
```bash
python main.py --process-all
```

**Output:**
```
Found 2 complete months: 2025-08, 2025-09
Already processed: 2025-08
[OK] Will process 1 new months: 2025-09

Processing...
Marked as processed: 2025-09
```

**Result:** Only September is processed. August is skipped (already done).

### Example 3: Add Older Month (Historical)

**Add July data (older than existing):**
```bash
cp michael_july.pdf data/raw/statements/Michael/
cp jacqui_july.pdf data/raw/statements/Jacqui/
cp credit_card_july.pdf data/raw/statements/shared/
```

**Process:**
```bash
python main.py --process-all
```

**Output:**
```
Found 3 complete months: 2025-07, 2025-08, 2025-09
Already processed: 2025-08, 2025-09
[OK] Will process 1 new months: 2025-07

Processing...
Marked as processed: 2025-07
```

**Result:** Only July is processed. August and September are skipped.

### Example 4: Fill Gaps

**Initially had:** August, October (September missing)
**Add September:**
```bash
cp michael_sept.pdf data/raw/statements/Michael/
cp jacqui_sept.pdf data/raw/statements/Jacqui/
cp credit_card_sept.pdf data/raw/statements/shared/
```

**Process:**
```bash
python main.py --process-all
```

**Output:**
```
Found 3 complete months: 2025-08, 2025-09, 2025-10
Already processed: 2025-08, 2025-10
[OK] Will process 1 new months: 2025-09

Processing...
Marked as processed: 2025-09
```

**Result:** Gap is filled - only September processed.

### Example 5: Force Reprocess Everything

**Scenario:** Made changes to classification rules, want to regenerate all months.

```bash
python main.py --process-all --force
```

**Output:**
```
Found 3 complete months: 2025-08, 2025-09, 2025-10
[OK] FORCE mode: Will reprocess all 3 months

Processing...
Marked as processed: 2025-08, 2025-09, 2025-10
```

**Result:** All months reprocessed from scratch.

## Benefits

### 1. Fast Incremental Updates

**Before:**
```bash
# Every run reprocesses everything
python main.py --process-all
# Processes: Aug, Sept, Oct (even if already done)
# Time: 5 minutes
```

**After:**
```bash
# First run
python main.py --process-all
# Processes: Aug, Sept, Oct
# Time: 5 minutes

# Add November data
# Second run
python main.py --process-all
# Processes: Only Nov
# Time: 1 minute
```

### 2. Flexible Data Addition

- **Add future months**: Just drop in new statements, run processing
- **Add historical months**: Fill in gaps in your data anytime
- **No order required**: Doesn't matter if you add July after September

### 3. Safe Reprocessing

- Checkpoint tracks what's done
- Won't lose progress if processing is interrupted
- Can always force reprocess if needed

### 4. Consistent Output

- Each month processed exactly once (unless forced)
- No risk of accidentally double-processing
- Output files remain consistent

## Technical Details

### Checkpoint Methods

**File:** `src/checkpoint_manager.py`

```python
# Mark a month as processed
checkpoint.mark_month_processed(2025, 8)  # August 2025

# Check if processed
is_done = checkpoint.is_month_processed(2025, 8)  # True/False

# Get all processed months
processed = checkpoint.get_processed_months()
# Returns: [(2025, 7), (2025, 8), (2025, 9)]

# Get unprocessed months
available = [(2025, 7), (2025, 8), (2025, 9), (2025, 10)]
to_process = checkpoint.get_unprocessed_months(available)
# Returns: [(2025, 10)] if 7-9 already processed

# Force mode - clear tracking
checkpoint.clear_processed_months()
```

### Integration with Transaction Processor

**File:** `src/transaction_processor.py`

```python
def _validate_data_completeness(self, force: bool = False):
    # Find all complete months
    common_months = self.validator.get_common_complete_months(...)

    # Filter to unprocessed only
    if force:
        self.checkpoint.clear_processed_months()
        months_to_process = common_months
    else:
        months_to_process = self.checkpoint.get_unprocessed_months(common_months)

    # Process only unprocessed months
    self.valid_months = months_to_process

def process_all(self, force: bool = False):
    # ... processing ...

    # Mark as processed
    for year, month in self.valid_months:
        self.checkpoint.mark_month_processed(year, month)
```

### Processing Flow

```
1. User adds statements for multiple months
   ├─ August: michael.pdf, jacqui.pdf, credit_card.pdf
   ├─ September: michael.pdf, jacqui.pdf, credit_card.pdf
   └─ October: michael.pdf, jacqui.pdf, credit_card.pdf

2. Run: python main.py --process-all

3. Validation Phase:
   ├─ Parse statements to get date ranges
   ├─ Identify complete months: [Aug, Sept, Oct]
   ├─ Check checkpoint: [] (nothing processed yet)
   └─ To process: [Aug, Sept, Oct]

4. Processing Phase:
   ├─ Process August → Mark as processed
   ├─ Process September → Mark as processed
   └─ Process October → Mark as processed

5. Add November data later

6. Run: python main.py --process-all

7. Validation Phase:
   ├─ Identify complete months: [Aug, Sept, Oct, Nov]
   ├─ Check checkpoint: [Aug, Sept, Oct]
   └─ To process: [Nov] only

8. Processing Phase:
   └─ Process November → Mark as processed
```

## Checkpoint File Location

```
data/
└── processed/
    └── checkpoint/
        └── transaction_checkpoint.json
```

**Contents:**
```json
{
  "processed_months": [
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10"
  ],
  "processed_files": {
    "data/raw/statements/Michael/aug.pdf": {
      "file_path": "data/raw/statements/Michael/aug.pdf",
      "last_modified": "2025-11-05T10:00:00",
      "file_size": 123456,
      "transaction_count": 45,
      "processed_at": "2025-11-05T11:00:00"
    }
  }
}
```

## Scenarios

### Scenario 1: Monthly Statement Workflow

**Month 1 (August):**
```bash
# Receive August statements
# Add to data folder
python main.py --process-all
# Result: August processed
```

**Month 2 (September):**
```bash
# Receive September statements
# Add to data folder
python main.py --process-all
# Result: Only September processed (August skipped)
```

**Month 3 (October):**
```bash
# Receive October statements
# Add to data folder
python main.py --process-all
# Result: Only October processed (Aug, Sept skipped)
```

### Scenario 2: Historical Data Migration

**Start:** You have old statements from past year

```bash
# Add January through December 2024 statements all at once
cp 2024_*.pdf data/raw/statements/Michael/

python main.py --process-all
# Result: All 12 months processed
# Time: Takes a while (first time)

# Next month (January 2025)
cp jan_2025.pdf data/raw/statements/Michael/

python main.py --process-all
# Result: Only January 2025 processed
# Time: Fast (incremental)
```

### Scenario 3: Discovered Missing Month

**Current:** August, September, October processed
**Realize:** Forgot to add September for one person

```bash
# Add missing September statement
cp jacqui_sept.pdf data/raw/statements/Jacqui/

python main.py --validate-months
# Shows: September now complete (was partial before)

python main.py --process-all
# Result: September reprocessed (now with complete data)
```

## Validation Report

### Before First Processing

```bash
python main.py --validate-months
```

```
Found 3 complete months: 2025-08, 2025-09, 2025-10
[OK] Will process 3 new months: 2025-08, 2025-09, 2025-10
```

### After First Processing

```bash
python main.py --validate-months
```

```
Found 3 complete months: 2025-08, 2025-09, 2025-10
Already processed: 2025-08, 2025-09, 2025-10
[OK] All months already processed - no new data to process
```

### After Adding New Month

```bash
python main.py --validate-months
```

```
Found 4 complete months: 2025-08, 2025-09, 2025-10, 2025-11
Already processed: 2025-08, 2025-09, 2025-10
[OK] Will process 1 new months: 2025-11
```

## Force Mode

### When to Use Force Mode

1. **Classification rules changed**: Updated transaction categories
2. **Bug fix**: Fixed parsing bug, want to reprocess
3. **Data correction**: Corrected source statements
4. **Testing**: Want to regenerate everything

### How to Use

```bash
python main.py --process-all --force
```

**Effect:**
- Clears processed month tracking
- Reprocesses ALL complete months
- Creates fresh output files

**Warning:** Takes longer (processes everything)

## Best Practices

### 1. Regular Processing

```bash
# Monthly workflow
# 1. Add new month's statements
# 2. Run processing
python main.py --process-all
# 3. Review output
# 4. Done - only new month processed
```

### 2. Check Status First

```bash
# Before processing, check what's done
python main.py --validate-months
# Shows: Already processed vs. new months
```

### 3. Force Only When Needed

```bash
# Normal (incremental)
python main.py --process-all

# Only force when you need to regenerate
python main.py --process-all --force
```

### 4. Historical Data

```bash
# Add multiple old months at once - no problem
cp historical/*.pdf data/raw/statements/Michael/
python main.py --process-all
# System processes all new complete months
```

## Troubleshooting

### "All months already processed" but output looks wrong

**Solution:** Use force mode to regenerate
```bash
python main.py --process-all --force
```

### Added new month but not processing

**Check:** Is the month actually complete?
```bash
python main.py --validate-months
# Look for "Complete months: ..." for each person
```

**Common issue:** One person missing that month's data

### Want to reprocess specific month only

**Current:** System processes all unprocessed months
**Workaround:**
1. Manually edit `data/processed/checkpoint/transaction_checkpoint.json`
2. Remove specific month from `processed_months` array
3. Run `--process-all`

## Summary

The incremental month processing system:

✅ **Tracks** which complete months have been processed
✅ **Skips** already-processed months (fast incremental updates)
✅ **Processes** new months automatically (past, present, or future)
✅ **Handles** gaps and out-of-order additions
✅ **Supports** force reprocessing when needed

**Result:** Efficient, flexible transaction processing that scales with your data!
