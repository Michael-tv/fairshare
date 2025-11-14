# Tax Refund & Year-End Claims Guide

## The Question

**"Should we split based on GROSS or NET income when tax refunds are involved?"**

## TL;DR - Quick Answer

**Use GROSS income (current default) and treat tax refunds as income.**

Add refund to your Income sheet in the month you receive it:
```
Description      | Amount  | Type
-----------------|---------|--------
Monthly Salary   | 100000  | Salary
Tax Refund       | 10000   | Other    <- Add this!
```

The system handles the rest automatically and fairly.

## Detailed Explanation

### Scenario

- Michael earns R100,000/month gross
- Jacqui earns R50,000/month gross
- At year-end, Michael gets R10,000 tax refund

**Question:** How should this refund be handled?

### Option 1: GROSS Income Basis (Recommended ✓)

#### Regular Month (April)
```
Michael gross: R100,000 → Net: R68,633 (after tax)
Jacqui gross:  R50,000  → Net: R38,520
Total gross:   R150,000

Split ratio: 66.7% (Michael) vs 33.3% (Jacqui)
Shared expenses: R30,000
  Michael pays: R20,000 (66.7%)
  Jacqui pays:  R10,000 (33.3%)
```

#### December (with refund)
```
Michael gross: R110,000 (R100k salary + R10k refund)
Jacqui gross:  R50,000
Total gross:   R160,000

Split ratio: 68.8% (Michael) vs 31.2% (Jacqui)
Shared expenses: R30,000
  Michael pays: R20,625 (68.8%)
  Jacqui pays:  R9,375 (31.2%)
```

**How to implement:**
```excel
Michael_December_2024.xlsx - Income Sheet:
  Salary          | 100000 | Salary
  Tax Refund      | 10000  | Other
```

### Option 2: NET Income Basis

#### Regular Month (April)
```
Michael net: R68,633
Jacqui net:  R38,520
Total net:   R107,153

Split ratio: 64.1% (Michael) vs 35.9% (Jacqui)
Shared expenses: R30,000
  Michael pays: R19,215 (64.1%)
  Jacqui pays:  R10,785 (35.9%)
```

#### December (with refund as income)
```
Michael net: R74,533 (R68,633 + R10,000 refund - tax on refund)
Jacqui net:  R38,520
Total net:   R113,053

Split ratio: 65.9% (Michael) vs 34.1% (Jacqui)
Shared expenses: R30,000
  Michael pays: R19,778 (65.9%)
  Jacqui pays:  R10,222 (34.1%)
```

## Key Insights

### 1. Both Approaches Work IF...
You **treat the tax refund as income** in both cases!

### 2. The Difference
- **GROSS basis:** Ratio is 66.7/33.3 normally, adjusts to 68.8/31.2 with refund
- **NET basis:** Ratio is 64.1/35.9 normally, adjusts to 65.9/34.1 with refund

### 3. Why GROSS is Better (System Default)

#### Advantages:
1. **Simpler conceptually** - Tax refund is just more income
2. **More stable ratios** - Based on earning capacity, not tax withholding
3. **Aligns with tax calc** - System already works with gross
4. **Easier to explain** - "You earn 66.7% of household income"

#### How it works:
- Michael over-withheld tax all year (paid too much)
- When refund comes, it's "delayed income"
- Both partners benefit proportionally
- Fair because both "lost access" to that money during the year

## What NOT To Do ❌

### Wrong Approach 1: Keep Refund 100%
```
"I got the refund, I keep it all"
```

**Problem:**
- Partner subsidized your over-withholding all year
- You benefited from lower proportional share (64% vs 67%)
- They paid higher share because your net was artificially low
- **Not fair unless agreed upfront**

### Wrong Approach 2: Split Refund 50/50
```
"We split everything 50/50"
```

**Problem:**
- Ignores proportional income
- Person who earned less pays too much
- Defeats purpose of proportional splitting

## Correct Approach ✓

### Current System (Default)
Uses GROSS income, so just add refund as income:

**Step 1:** Add to your Income sheet
```
Michael_December_2024.xlsx - Income Sheet:
Description      | Amount  | Type
-----------------|---------|--------
Salary           | 100000  | Salary
Tax Refund       | 10000   | Other
```

**Step 2:** Process normally
```bash
python main.py --next
```

**Step 3:** System calculates
- Tax on your R100k salary
- Adds R10k refund to gross income
- Calculates your new proportion (68.8%)
- Splits expenses fairly
- **Done!**

### If You Want NET-Based Splitting

You can change the default, but must still add refund as income:

```python
# In your processing, use:
use_gross_income_for_split=False
```

Then add refund to Income sheet (same as above).

## Annual Reconciliation

### Scenario: Process all 12 months

```
Jan-Nov: Split at 66.7% / 33.3% (based on regular gross)
Dec:     Split at 68.8% / 31.2% (includes refund)

Cumulative over year: Averages out fairly
```

### What the Numbers Show

**Regular month (66.7/33.3):**
- Michael pays: R20,000
- Jacqui pays: R10,000

**Refund month (68.8/31.2):**
- Michael pays: R20,625 (pays R625 more)
- Jacqui pays: R9,375 (pays R625 less)

**Net effect over year:**
- Jacqui saved R625 in December
- This compensates for the months where she paid slightly more
  due to Michael's over-withholding reducing his net income
- **Result: Fair!**

## Practical Examples

### Example 1: Medical Aid Tax Credit
```
You paid R7,000/month for medical aid
At year-end, you get R5,000 back from SARS

Add to Income sheet:
  Medical aid refund | 5000 | Other
```

### Example 2: Retirement Annuity Deduction
```
You contributed R2,500/month to RA (reduces taxable income)
At year-end, this saved you R10,000 in tax

Add to Income sheet:
  RA tax benefit | 10000 | Other
```

### Example 3: Work-from-Home Tax Deduction
```
You claimed home office expenses
SARS refunded R3,000

Add to Income sheet:
  Tax refund - home office | 3000 | Other
```

## Edge Cases

### What if we DON'T process refund?

**Scenario:** Michael keeps R10,000 refund entirely

**Annual split:**
```
Jan-Nov combined: R330,000 shared expenses
  Michael paid: R220,000 (66.7%)
  Jacqui paid:  R110,000 (33.3%)

December: R30,000 shared expenses
  Michael paid: R20,000 (66.7%)
  Jacqui paid:  R10,000 (33.3%)

Total: R360,000 expenses
  Michael should pay: R240,000 (66.7%)
  Jacqui should pay:  R120,000 (33.3%)

But Michael's REAL income was:
  R100k × 12 months + R10k refund = R1,210,000

True ratio should be:
  Michael: R1,210,000 / R1,710,000 = 70.8%
  Jacqui:  R500,000 / R1,710,000 = 29.2%

Michael should have paid: R254,880 (70.8% of R360k)
But he paid: R240,000
Difference: R14,880 underpaid!

By keeping the refund, Michael got:
  - R10,000 refund
  - R14,880 less expenses to pay
  = R24,880 benefit!

Jacqui overpaid by R14,880!
```

**This is only fair if you both agreed upfront that refunds aren't shared.**

### What if refund is HUGE?

```
Example: Michael gets R50,000 refund due to big RA contribution

Add to Income:
  Tax refund | 50000 | Other

December split:
  Michael gross: R150,000 (R100k + R50k)
  Jacqui gross: R50,000
  Ratio: 75% / 25%

Fair because:
  - Michael earned that R50k during the year
  - It was just withheld/deferred
  - Both benefit proportionally from his higher earning
```

## Recommendation Summary

### For Your System (Current Setup)

1. **Use GROSS income** (current default) ✓
2. **Add tax refunds as income** when received
3. **Process normally** - system handles it fairly

### How To Do It

**Income Sheet:**
```
Description                  | Amount  | Type
-----------------------------|---------|--------
Monthly Salary               | 100000  | Salary
Tax Refund (year-end claim)  | 10000   | Other  <- Add this
RA Tax Benefit               | 5000    | Other  <- Or this
Medical Aid Credit           | 3000    | Other  <- Or this
```

**Process:**
```bash
python main.py --next
```

**Result:**
- Refund increases your gross income that month
- Split adjusts proportionally
- Partner benefits from your refund (fairly)
- Everyone happy!

## Why This Matters

**Fair splitting means:**
- Both partners benefit from household income proportionally
- Tax refunds are delayed income
- The person who got over-withheld shouldn't profit from it
- The partner shouldn't subsidize over-withholding

**By processing refunds as income:**
- ✓ Simple and transparent
- ✓ Mathematically fair
- ✓ Automatic with the system
- ✓ Consistent over time

## Bottom Line

**Just add tax refunds to your Income sheet and process normally.**

The system does the math and ensures fairness automatically!
