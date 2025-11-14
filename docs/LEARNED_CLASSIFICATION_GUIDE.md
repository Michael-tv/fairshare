# Learned Classification Guide

## Overview

FairShare now includes an **intelligent learning system** that improves transaction classification based on your corrections. Instead of repeatedly fixing the same merchants, the system learns from your edits and automatically applies that knowledge to future transactions.

## How It Works

### 1. Storage Location

Learned rules are stored in:
```
data/processed/learned_rules.json
```

This file persists across runs and grows as you make more corrections.

### 2. Fuzzy Matching

The system uses **fuzzy string matching** (via `rapidfuzz`) to handle variations:

**Example:**
- You correct "Woolworths Rondebosch" → GROCERIES, SHARED
- System automatically applies to:
  - "Woolworths Rondebosch 123" ✓
  - "WOOLWORTHS RONDEBOSCH" ✓
  - "Woolworths Rondebosch Store" ✓
  - "Woolworths Sea Point" ✗ (different branch, too different)

**Similarity threshold:** 85% (configurable)

### 3. Classification Priority

When classifying transactions:
1. **Learned rules** (from your corrections) - **HIGHEST PRIORITY**
2. Keyword patterns (default system rules) - Fallback

This means your corrections always take precedence!

## Usage Workflow

### Step 1: Process Statements

```bash
uv run fairshare --process-statements
```

This creates transaction files with auto-classification.

### Step 2: Review & Correct

Open the transaction files in Excel:
```
data/processed/transactions/Michael/Michael_transactions.xlsx
data/processed/transactions/shared_credit_card/shared_credit_card_transactions.xlsx
```

**Columns:**
- `auto_category`: System's guess
- `user_category`: **Edit this** to override
- `final_category`: Formula (uses user_category if provided, else auto_category)
- `auto_type`: System's guess (SHARED/INDIVIDUAL)
- `user_type`: **Edit this** to override
- `final_type`: Formula (uses user_type if provided, else auto_type)

**Example corrections:**
| description | auto_category | user_category | auto_type | user_type |
|-------------|---------------|---------------|-----------|-----------|
| Woolworths Rondebosch | GROCERIES | *(leave empty)* | SHARED | *(leave empty)* |
| Takealot Purchase | OTHER | **HOUSEHOLD** | INDIVIDUAL | **SHARED** |
| Netflix Subscription | ENTERTAINMENT | *(leave empty)* | INDIVIDUAL | **SHARED** |

### Step 3: Learn from Corrections

```bash
uv run fairshare --learn-from-corrections
```

**Output:**
```
================================================================================
LEARN FROM USER CORRECTIONS
================================================================================

Processing: Michael_transactions.xlsx
  Learned from 5 corrections
    [+] 3 new rules
    [~] 2 updated rules
  Total rules: 15

Processing: shared_credit_card_transactions.xlsx
  Learned from 2 corrections
    [+] 2 new rules
  Total rules: 17

================================================================================
LEARNING COMPLETE
================================================================================

New rules learned: 5
Existing rules updated: 2

Learned rules saved to: data\processed\learned_rules.json

Next time you run --process-statements, these learned rules will be
automatically applied to classify similar transactions!
```

### Step 4: Apply to Existing Files (Optional)

To apply learned rules to existing transaction files **without** reparsing PDFs:

```bash
uv run fairshare --apply-learned-rules
```

This is much faster than `--process-statements --force` because it only updates classifications, not re-parse statements.

**When to use:**
- After learning new rules from corrections
- After adding custom categories
- To fix final_category/final_type values

**What it does:**
- Re-classifies transactions using learned rules
- Updates auto_category and auto_type
- Preserves user corrections
- Fixes final_category and final_type columns

**Example output:**
```
================================================================================
APPLY LEARNED RULES TO EXISTING TRANSACTIONS
================================================================================

Loaded 12 learned rules

Found 10 transaction files to process

Processing: 2025-05/michael_classified.xlsx
  michael_classified.xlsx: 2 reclassified, 36 unchanged

Processing: 2025-09/credit_card_classified.xlsx
  credit_card_classified.xlsx: 1 reclassified, 21 unchanged

================================================================================
APPLICATION COMPLETE
================================================================================

Files updated: 2
Transactions reclassified: 3
Transactions unchanged: 331

Auto-classifications have been updated in all transaction files.
User corrections were preserved and remain unchanged.
```

## Commands

### Learn from Corrections

```bash
uv run fairshare --learn-from-corrections
```

Scans all transaction files for user corrections and adds them to learned rules.

### Show Statistics

```bash
uv run fairshare --show-learned-stats
```

**Output:**
```
================================================================================
LEARNED CLASSIFICATION RULES STATISTICS
================================================================================

Total learned rules: 17

Rules file: data\processed\learned_rules.json

By Category:
  GROCERIES: 5
  ENTERTAINMENT: 3
  HOUSEHOLD: 2
  FUEL: 2
  CLOTHING: 2
  SUBSCRIPTIONS: 2
  UTILITIES: 1

By Type:
  SHARED: 12
  INDIVIDUAL: 5

To export rules to Excel for review:
  uv run fairshare --export-learned-rules learned_rules.xlsx
```

### Export Rules

```bash
uv run fairshare --export-learned-rules learned_rules.xlsx
```

Exports learned rules to an Excel file for review:

| description | category | type | count | confidence |
|-------------|----------|------|-------|------------|
| woolworths rondebosch | GROCERIES | SHARED | 3 | 100 |
| netflix subscription | ENTERTAINMENT | SHARED | 1 | 100 |
| takealot purchase | HOUSEHOLD | SHARED | 2 | 100 |

**Fields:**
- `description`: Transaction description (normalized to lowercase)
- `category`: Learned category
- `type`: Learned type (SHARED/INDIVIDUAL)
- `count`: Number of times this correction was made
- `confidence`: Confidence level (always 100 for user corrections)

## JSON Format

The `learned_rules.json` file structure:

```json
{
  "woolworths rondebosch": {
    "category": "GROCERIES",
    "type": "SHARED",
    "count": 3,
    "confidence": 100
  },
  "netflix subscription": {
    "category": "ENTERTAINMENT",
    "type": "SHARED",
    "count": 1,
    "confidence": 100
  }
}
```

## Custom Categories

### Dynamic Category Management

You can add custom expense categories without editing code!

```bash
# List all available categories
uv run fairshare --list-categories

# Add a custom category
uv run fairshare --add-category DISCRETIONARY_DINING "Discretionary Dining"

# Remove a category
uv run fairshare --remove-category OLD_CATEGORY

# Rename a category
uv run fairshare --rename-category OLD_KEY NEW_KEY "New Display Name"
```

### Using Custom Categories

Once added, custom categories work just like built-in ones:

1. **In Excel files**: Use either the key or display name
   - `user_category`: "DISCRETIONARY_DINING" ✓
   - `user_category`: "Discretionary Dining" ✓ (auto-normalized)

2. **In learned rules**: Automatically supported
   ```bash
   # Edit transaction with custom category
   # Run learning
   uv run fairshare --learn-from-corrections
   # Custom category is now in learned rules!
   ```

3. **Apply to existing files**:
   ```bash
   # After adding a custom category, update old files
   uv run fairshare --apply-learned-rules
   ```

### Category Storage

Categories are stored in `data/processed/categories.json`:
```json
{
  "GROCERIES": "Groceries",
  "FUEL": "Fuel",
  "DISCRETIONARY_DINING": "Discretionary Dining"
}
```

### Example Workflow with Custom Categories

```bash
# 1. Add custom category
uv run fairshare --add-category COFFEE_SHOPS "Coffee Shops"

# 2. Edit transaction files
#    Change "Starbucks" from OTHER to "Coffee Shops"

# 3. Learn the correction
uv run fairshare --learn-from-corrections
#    Now all coffee shops will be classified as COFFEE_SHOPS

# 4. Apply to existing files
uv run fairshare --apply-learned-rules
```

## Advanced Configuration

### Adjusting Similarity Threshold

Edit `src/learned_classifier.py`:

```python
# Default: 85% similarity required
classifier = LearnedClassifier(rules_path, category_manager, similarity_threshold=85)

# Stricter (fewer fuzzy matches):
classifier = LearnedClassifier(rules_path, category_manager, similarity_threshold=90)

# More lenient (more fuzzy matches):
classifier = LearnedClassifier(rules_path, category_manager, similarity_threshold=80)
```

### Disabling Learned Classification

Edit `src/transaction_processor.py`:

```python
# Disable learned classifier
self.classifier = TransactionClassifier(
    category_manager=category_manager,
    learned_rules_path=learned_rules_path,
    use_learned=False  # Set to False
)
```

## Best Practices

### 1. Review Before Learning

Always review your corrections before running `--learn-from-corrections`:
- Make sure corrections are accurate
- Use consistent category/type choices
- Don't leave partial corrections (both category AND type should match)

### 2. Incremental Learning

You don't have to correct everything at once:
1. Process statements
2. Correct a few obvious ones
3. Run `--learn-from-corrections`
4. Repeat as you use the system

### 3. Periodic Review

Occasionally export and review learned rules:

```bash
uv run fairshare --export-learned-rules review.xlsx
```

Check for:
- Duplicate rules (different wordings of same merchant)
- Outdated rules (merchants you no longer use)
- Conflicting rules

### 4. Backup Learned Rules

The `learned_rules.json` file is valuable! Back it up:

```bash
cp data/processed/learned_rules.json learned_rules_backup.json
```

Or commit to version control (if not dealing with sensitive merchant names).

## Troubleshooting

### "Skipping invalid classification"

**Problem:**
```
[!] Skipping invalid category: HEALTH
```

**Solution:** You used a category name that doesn't exist.

**Check available categories:**
```bash
uv run fairshare --list-categories
```

**Add the category if it's legitimate:**
```bash
uv run fairshare --add-category HEALTH "Health"
```

Then re-run:
```bash
uv run fairshare --learn-from-corrections
```

### No Rules Learned

**Problem:** `--learn-from-corrections` found 0 corrections.

**Solution:**
1. Make sure you edited the `user_category` or `user_type` columns
2. Save the Excel file
3. Run `--learn-from-corrections` again

### Fuzzy Matching Not Working

**Problem:** Similar transactions not being classified.

**Solutions:**
1. Lower similarity threshold (see Advanced Configuration)
2. Transaction might be too different (< 85% similarity)
3. Check if rule exists: `--show-learned-stats`

### Wrong Classification Applied

**Problem:** Learned rule is incorrect.

**Solution:**
1. Edit the transaction file with correct classification
2. Run `--learn-from-corrections` again (updates existing rule)
3. Or manually edit `data/processed/learned_rules.json`

## Example Workflow

### Month 1: September 2025

```bash
# Process statements
uv run fairshare --process-statements

# Review Michael's transactions in Excel
# Correct 10 transactions:
#   - Woolworths → GROCERIES, SHARED
#   - Netflix → ENTERTAINMENT, SHARED
#   - Gym → SUBSCRIPTIONS, INDIVIDUAL

# Learn from corrections
uv run fairshare --learn-from-corrections
# Output: Learned 10 new rules

# Calculate split
uv run fairshare --calculate-split
```

### Month 2: October 2025

```bash
# Process new statements
uv run fairshare --process-statements

# Open transactions - many already correctly classified!
# - Woolworths automatically classified as GROCERIES, SHARED ✓
# - Netflix automatically classified as ENTERTAINMENT, SHARED ✓
# - Gym automatically classified as SUBSCRIPTIONS, INDIVIDUAL ✓

# Only need to correct new/unfamiliar merchants
# Correct 3 new transactions

# Learn from new corrections
uv run fairshare --learn-from-corrections
# Output: Learned 3 new rules (total: 13)

# Calculate split
uv run fairshare --calculate-split
```

### Month 3+: System Gets Smarter

As months go by:
- Fewer corrections needed
- System recognizes more merchants
- Classification accuracy improves
- Less manual work!

## Future Enhancements

Potential future improvements:

1. **Machine Learning Integration**
   - Train on historical corrections
   - Generalize patterns (e.g., "all gyms are SUBSCRIPTIONS, INDIVIDUAL")

2. **Active Learning**
   - System asks about low-confidence predictions
   - Prioritizes learning from uncertain cases

3. **Rule Suggestions**
   - "You corrected Woolworths 5 times. Create a permanent rule?"

4. **Shared Rule Database**
   - Community-contributed rules for common South African merchants

## Summary

The learned classification system:

✅ **Stores** your corrections in `learned_rules.json`
✅ **Applies** learned rules automatically to future transactions
✅ **Handles** merchant variations with fuzzy matching
✅ **Improves** over time as you make more corrections
✅ **Reduces** manual classification work month-over-month
✅ **Supports** custom categories added on-the-fly
✅ **Preserves** user corrections when applying rules

**Key Commands:**
```bash
# Learning
uv run fairshare --learn-from-corrections          # Learn from your edits
uv run fairshare --apply-learned-rules             # Apply to existing files
uv run fairshare --show-learned-stats              # View statistics
uv run fairshare --export-learned-rules file.xlsx  # Export to Excel

# Custom Categories
uv run fairshare --list-categories                 # List all categories
uv run fairshare --add-category KEY "Display Name" # Add category
uv run fairshare --remove-category KEY             # Remove category
```

Start correcting transactions today, and watch the system learn!

---

*Last updated: November 2025*
*Features: Learned Classification, Custom Categories, Apply Rules*
