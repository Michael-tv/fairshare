# Transaction Splits Guide

## Overview

FairShare now supports **partial transaction splits**, allowing you to classify a single transaction as both HOUSEHOLD and INDIVIDUAL (personal) in varying proportions.

This is useful when:
- A grocery shop includes both household items and personal items
- A shared credit card purchase includes items for one person
- A personal account transaction includes household expenses

## Key Concepts

### Terminology Change: SHARED → HOUSEHOLD

**Important:** The system now uses "HOUSEHOLD" instead of "SHARED" throughout:
- **HOUSEHOLD** = Expenses split proportionally between partners
- **INDIVIDUAL** = Personal expenses belonging to one person only

### Default Classification

**Personal Accounts** (Michael/Jacqui):
- **Default:** Transactions are INDIVIDUAL (belong to account owner)
- **Split to HOUSEHOLD:** Use `split_amount` and `split_to` columns to remap portion to household

**Shared Credit Card**:
- **Default:** Transactions are HOUSEHOLD (split between both)
- **Split to Person:** Use `split_amount` and `split_to` columns to remap portion to a specific person

## Column Structure

Every transaction file now includes:

| Column | Description | Example Values |
|--------|-------------|----------------|
| `amount` | Total transaction amount | 1000.00 |
| `auto_type` | System classification | "Household", "Individual" |
| `user_type` | User override | "Household", "Individual" |
| `final_type` | Effective type (formula) | "Household" |
| `split_amount` | Amount to remap | 300.00 |
| `split_to` | Where to remap | "HOUSEHOLD", "Michael", "Jacqui" |

## Usage Examples

### Example 1: Personal Account - Groceries with Personal Items

**Scenario:** Michael's account - Woolworths R1000
- R700 is household groceries
- R300 is Michael's personal snacks/items

**Excel Entry:**
| description | amount | auto_type | user_type | final_type | split_amount | split_to |
|-------------|--------|-----------|-----------|------------|--------------|----------|
| Woolworths | 1000 | Individual | | Individual | 700 | HOUSEHOLD |

**Result:**
- R700 goes to HOUSEHOLD pool (split proportionally)
- R300 stays with Michael (INDIVIDUAL)

### Example 2: Personal Account - Fully Household

**Scenario:** Michael paid for household internet R899

**Excel Entry:**
| description | amount | auto_type | user_type | final_type | split_amount | split_to |
|-------------|--------|-----------|-----------|------------|--------------|----------|
| Afrihost | 899 | Individual | | Individual | 899 | HOUSEHOLD |

**Result:**
- R899 goes to HOUSEHOLD pool (split proportionally)
- R0 stays with Michael

**Alternative:** Simply change `user_type` to "Household" (no split needed)

### Example 3: Shared Credit Card - Personal Purchase

**Scenario:** Shared card - Gym membership R500 (Jacqui's only)

**Excel Entry:**
| description | amount | auto_type | user_type | final_type | split_amount | split_to |
|-------------|--------|-----------|-----------|------------|--------------|----------|
| Virgin Active | 500 | Household | | Household | 500 | Jacqui |

**Result:**
- R0 goes to HOUSEHOLD pool
- R500 goes 100% to Jacqui (INDIVIDUAL)

**Alternative:** Change `user_type` to "Individual" (auto-maps to card owner if known)

### Example 4: Shared Credit Card - Partial Split

**Scenario:** Shared card - Takealot R1000
- R600 is household items
- R400 is Michael's personal order

**Excel Entry:**
| description | amount | auto_type | user_type | final_type | split_amount | split_to |
|-------------|--------|-----------|-----------|------------|--------------|----------|
| Takealot | 1000 | Household | | Household | 400 | Michael |

**Result:**
- R600 goes to HOUSEHOLD pool (split proportionally)
- R400 goes 100% to Michael

## Fair Share Calculation Logic

### Personal Account Transaction

**Original:**
- `amount = 1000`
- `split_amount = 700`
- `split_to = "HOUSEHOLD"`

**Calculation:**
```
household_portion = split_amount = 700 (split proportionally)
personal_portion = amount - split_amount = 300 (100% to account owner)
```

### Shared Card Transaction

**Original:**
- `amount = 1000`
- `split_amount = 400`
- `split_to = "Michael"`

**Calculation:**
```
household_portion = amount - split_amount = 600 (split proportionally)
personal_portion = split_amount = 400 (100% to Michael)
```

## Validation Rules

The system validates:

1. **`split_amount` must be ≤ `amount`**
   - You can't split more than the total transaction

2. **If `split_amount` > 0, then `split_to` must be filled**
   - System needs to know where to map the split

3. **For personal accounts: `split_to` must be "HOUSEHOLD"**
   - Personal accounts can only split TO household, not to other people

4. **For shared card: `split_to` must be a valid person name**
   - E.g., "Michael" or "Jacqui" (from config.json)

## Workflow

### Step 1: Process Statements

```bash
uv run fairshare --process-statements
```

This generates transaction files with all columns including `split_amount` and `split_to`.

### Step 2: Review & Add Splits

Open the transaction files in Excel:

**Michael's transactions:**
```
data/processed/transactions/Michael/Michael_transactions.xlsx
```

**Shared credit card:**
```
data/processed/transactions/shared_credit_card/shared_credit_card_transactions.xlsx
```

**Edit the columns:**
1. Review `auto_type` classification
2. Add `split_amount` for partial splits
3. Specify `split_to` destination
4. Or override `user_type` for simple reclassification

### Step 3: Calculate Fair Share

```bash
uv run fairshare --calculate-split
```

The system now:
1. Reads `split_amount` and `split_to` columns
2. Calculates household vs personal portions
3. Splits household expenses proportionally
4. Assigns personal portions 100% to the specified person

## Common Scenarios

### Scenario A: Monthly Groceries Split

Many grocery trips include both household and personal items.

**Approach 1 - Estimate Percentage:**
- If groceries are typically 80% household, 20% personal
- For R2000 Woolworths: `split_amount = 1600`, `split_to = HOUSEHOLD`

**Approach 2 - Use Receipts (Future):**
- Scan receipt slip
- System can auto-suggest split based on items

### Scenario B: Shared Card Misclassified Items

Some items on the shared card are actually personal.

**Example:** Clothing purchase R800 on shared card
- Was classified as "Household" (default for shared card)
- Actually belongs to Jacqui only
- Solution: `split_amount = 800`, `split_to = Jacqui`

### Scenario C: Personal Account Household Bills

Some household bills come from personal accounts.

**Example:** Michael pays internet R899 from his account
- Classified as "Individual" (default for personal account)
- Actually household expense
- Solution: `split_amount = 899`, `split_to = HOUSEHOLD`

## Tips & Best Practices

### 1. Start Simple

Don't split everything immediately:
- First pass: Just fix obvious misclassifications using `user_type`
- Second pass: Add splits for mixed transactions

### 2. Use Patterns

If you see patterns:
- "Woolworths is always 70% household"
- Add `split_amount` consistently
- System will learn from this (future enhancement)

### 3. Round Numbers

For estimates, use round numbers:
- R1347.63 groceries → split R1000 to household (easier to track)
- Precision isn't critical for fair splitting

### 4. Document Splits

Use the `user_notes` column to explain splits:
```
"Groceries: R700 household food, R300 Michael's snacks"
```

## Future Enhancements

### Slip-Based Auto-Splits

Once slip matching is active:
- Scan grocery receipt
- System identifies items as household vs personal
- Auto-fills `split_amount` and `split_to`

### Smart Split Suggestions

Based on learned patterns:
- "Woolworths transactions are usually 75% household"
- System pre-fills `split_amount` with suggested value
- User confirms or adjusts

### Split Templates

Create templates for recurring splits:
- "Virgin Active gym → always 100% to Jacqui"
- System auto-applies when detected

## Troubleshooting

### Problem: Split not applied in calculation

**Check:**
1. Is `split_amount > 0`?
2. Is `split_to` filled in?
3. Did you run `--calculate-split` after editing?

### Problem: Validation error

**Error:** "split_amount exceeds transaction amount"

**Solution:** Ensure `split_amount ≤ amount`

---

**Error:** "split_to must be filled when split_amount > 0"

**Solution:** Add destination in `split_to` column

---

**Error:** "Invalid split_to value for personal account"

**Solution:** For personal accounts, use `split_to = "HOUSEHOLD"` only

### Problem: Wrong person receiving split

**Check:**
- For shared card: Is `split_to` the correct person name?
- For personal account: Should always be "HOUSEHOLD"

## Summary

✅ **Split any transaction** between HOUSEHOLD and INDIVIDUAL
✅ **Personal accounts** default to INDIVIDUAL, split TO household
✅ **Shared card** defaults to HOUSEHOLD, split TO specific person
✅ **Flexible** - split full amount or partial amounts
✅ **Validated** - system checks split logic
✅ **Fair** - household portions split proportionally, personal portions go 100% to owner

**Key Columns:**
- `split_amount` - How much to remap
- `split_to` - Where to remap ("HOUSEHOLD", "Michael", "Jacqui")

Start using splits today for more accurate expense tracking!

---

*Feature Added: November 2025*
*Version: 2.0.0 - Transaction Splits*
