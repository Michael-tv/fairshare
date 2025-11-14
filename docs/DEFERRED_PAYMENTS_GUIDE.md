# Deferred Payments Guide

## Overview

The deferred payments system tracks expenses that **should have been paid** but were **missed/delayed** and will be paid in a future month. This supports **accrual accounting** (when expense occurred) vs **cash accounting** (when actually paid).

## Use Cases

### 1. Missed Bills
```
September electricity bill (R500) was due but forgot to pay.
Will pay in October.

→ Belongs to September expenses, but cash leaves in October
```

### 2. Delayed Reimbursements
```
Michael paid shared groceries (R2000) in September.
Jacqui will reimburse in October.

→ Shared expense incurred in September, cash transfer in October
```

### 3. Upcoming Known Expenses
```
Insurance premium (R1500) due September 30th.
Can't pay until October salary arrives.

→ Should be counted in September, will be paid in October
```

## How It Works

### File Location
```
data/processed/deferred_payments.xlsx
```

### Excel Columns

| Column | Description | Editable? |
|--------|-------------|-----------|
| `payment_id` | Unique ID | No |
| `description` | What expense | Yes |
| `amount` | Amount (R) | Yes |
| `category` | Expense category | Yes |
| `expense_type` | SHARED or INDIVIDUAL | Yes |
| `accrual_month` | When incurred | Yes |
| `payment_month` | When paid/will pay | Yes |
| `responsible_person` | Who should pay | Yes |
| `paid_by` | Who actually paid | System |
| `status` | PENDING/PAID/CANCELLED | System |
| `reason` | Why deferred | Yes |
| `notes` | Additional info | Yes |

## Using Deferred Payments

### Method 1: Add Manually in Excel

1. **Open the file**:
   ```
   data/processed/deferred_payments.xlsx
   ```

2. **Add a new row**:
   ```
   payment_id: (leave blank - will auto-generate)
   description: September Electricity Bill
   amount: 500.00
   category: UTILITIES
   expense_type: SHARED
   accrual_month: 2025-09-01
   payment_month: 2025-10-01
   responsible_person: Michael
   paid_by: (leave blank)
   status: PENDING
   reason: Forgot to pay on time
   notes: Will pay early October
   ```

3. **Save the file**

### Method 2: Add via Python (Future Feature)

```python
from deferred_payment_manager import DeferredPaymentManager
from models import ExpenseCategory, ExpenseType
from datetime import date
from decimal import Decimal

manager = DeferredPaymentManager("data/processed/deferred_payments.xlsx")

# Add deferred payment
manager.add_deferred_payment(
    description="September Electricity Bill",
    amount=Decimal("500.00"),
    category=ExpenseCategory.UTILITIES,
    expense_type=ExpenseType.SHARED,
    accrual_month=date(2025, 9, 1),
    responsible_person="Michael",
    reason="Forgot to pay on time",
    payment_month=date(2025, 10, 1),
    notes="Will pay early October"
)
```

## Marking as Paid

When you actually pay a deferred expense:

### In Excel

1. Open `deferred_payments.xlsx`
2. Find the row
3. Update:
   - `status` → `PAID`
   - `paid_by` → Person who paid
   - `payment_month` → Actual payment month
4. Save

### Via Python (Future)

```python
manager.mark_as_paid(
    payment_id="DEF202509150001",
    paid_by="Michael",
    payment_month=date(2025, 10, 5)
)
```

## Accrual Adjustments

The system can adjust monthly totals for accrual accounting:

### Scenario

**September**:
- Electricity bill incurred: R500 (should count)
- Actually paid: R0

**October**:
- Electricity bill paid: R500 (already counted in Sept)
- Need to avoid double-counting

### Adjustment Calculation

```python
# For September
adjustments = manager.get_accrual_adjustments(date(2025, 9, 1))
# Returns:
{
  "add_incurred_not_paid": 500.00,  # Add to September
  "subtract_paid_not_incurred": 0,
  "net_adjustment": +500.00
}

# For October
adjustments = manager.get_accrual_adjustments(date(2025, 10, 1))
# Returns:
{
  "add_incurred_not_paid": 0,
  "subtract_paid_not_incurred": 500.00,  # Subtract from October
  "net_adjustment": -500.00
}
```

## Integration with Monthly Split

### Manual Method (Current)

1. **Calculate normal split** for September
2. **Note deferred expenses** from `deferred_payments.xlsx`
3. **Manually adjust** the split calculation:
   ```
   September expenses = R10,000 (actual) + R500 (deferred) = R10,500
   ```

### Automatic Method (Future Enhancement)

The system could automatically:
1. Read `deferred_payments.xlsx`
2. Apply accrual adjustments
3. Show both:
   - **Cash basis**: What actually changed hands
   - **Accrual basis**: What expenses were incurred

## Reports

### Pending Payments Report

Shows all unpaid deferred payments:

```python
manager = DeferredPaymentManager("data/processed/deferred_payments.xlsx")
print(manager.generate_report())
```

Output:
```
================================================================================
DEFERRED PAYMENTS REPORT
================================================================================

Pending Payments: 3
Total Amount: R2,500.00

Details:
  [DEF202509150001] September Electricity Bill
    Amount: R500.00
    Incurred: September 2025
    Responsible: Michael
    Reason: Forgot to pay on time
    Expected Payment: October 2025

  [DEF202509160002] Shared Groceries Reimbursement
    Amount: R2,000.00
    Incurred: September 2025
    Responsible: Jacqui
    Reason: Will reimburse from next salary
    Expected Payment: October 2025

By Person:
  Michael: 1 pending (R500.00)
  Jacqui: 1 pending (R2,000.00)
```

### By Month Report

```python
# Get what was incurred in September
sept_incurred = manager.get_payments_for_month(date(2025, 9, 1), by="accrual")

# Get what will be paid in October
oct_payments = manager.get_payments_for_month(date(2025, 10, 1), by="payment")
```

## Workflow Example

### Scenario: Forgot to Pay Electricity

**September 30th**: Realize you forgot to pay R500 electricity bill

**Step 1**: Add to deferred payments
```
Description: September Electricity Bill
Amount: 500.00
Category: UTILITIES
Expense_type: SHARED
Accrual_month: 2025-09-01
Payment_month: 2025-10-01
Responsible_person: Michael
Status: PENDING
Reason: Forgot to pay, will pay in Oct
```

**Step 2**: Calculate September split
- Include R500 in September shared expenses
- Note: Michael owes this to the household

**October 5th**: Pay the bill

**Step 3**: Mark as paid
```
Status: PAID
Paid_by: Michael
Payment_month: 2025-10-01
```

**Step 4**: Calculate October split
- **Don't** include the R500 again (already counted in Sept)
- Or use accrual adjustment to subtract it

## Best Practices

### 1. Record Immediately
When you realize a payment is deferred, add it immediately.

### 2. Set Expected Payment Date
Always fill `payment_month` so you remember when to pay.

### 3. Update Status
When paid, update to PAID status to track completion.

### 4. Monthly Review
Check pending payments at month end to see what needs to be paid next month.

### 5. Distinguish Types
- **Missed bills**: Forgot to pay
- **Delayed reimbursements**: Agreed to pay later
- **Timing mismatches**: Bill due end-of-month, paid early next month

## Common Questions

### Q: Should I always use accrual accounting?

**A**: Depends on your preference:
- **Cash basis** (simpler): Count expenses when money actually moves
- **Accrual basis** (more accurate): Count expenses when incurred

For household finances, **cash basis is simpler**. Use deferrals only for significant timing differences.

### Q: What if someone paid for the other person?

**A**: Example:
```
Michael paid Jacqui's R500 phone bill in September.
Jacqui will reimburse in October.

→ Add to deferred payments:
  Description: Jacqui's Phone Bill (paid by Michael)
  Expense_type: INDIVIDUAL (Jacqui's expense)
  Responsible_person: Jacqui
  Paid_by: Michael
  Payment_month: 2025-10-01 (when Jacqui reimburses)
  Reason: Paid on behalf, will reimburse
```

### Q: Do I need this for small amounts?

**A**: No. Reserve for:
- Amounts > R100
- Regular bills (utilities, insurance)
- Significant reimbursements

### Q: How do I clear old deferrals?

Mark as CANCELLED:
```
Status: CANCELLED
Notes: No longer applicable
```

## Future Enhancements

Planned features:
- [ ] CLI commands: `--add-deferred`, `--mark-paid`, `--list-pending`
- [ ] Automatic integration with monthly split
- [ ] Recurring deferrals (e.g., rent always paid 5 days into month)
- [ ] Reminders for upcoming payments
- [ ] Automatic matching when payment found in statements

## Example File

See `data/processed/deferred_payments.xlsx` (created automatically on first use)

Initial structure:
```
| payment_id | description | amount | category | expense_type | accrual_month | payment_month | responsible_person | paid_by | status | reason | notes |
|------------|-------------|--------|----------|--------------|---------------|---------------|-------------------|---------|--------|--------|-------|
| (empty initially)
```

## Getting Started

1. **Manual setup**: Create `data/processed/deferred_payments.xlsx` with columns above
2. **Or use Python**:
   ```python
   from deferred_payment_manager import DeferredPaymentManager
   from pathlib import Path

   manager = DeferredPaymentManager(Path("data/processed/deferred_payments.xlsx"))
   manager.save()  # Creates empty file with correct structure
   ```

3. **Add your first deferred payment** (in Excel or Python)
4. **Review monthly** and mark as paid when complete
