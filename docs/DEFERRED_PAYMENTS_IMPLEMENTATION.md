# Deferred Payments Implementation Summary

## Overview

Deferred payment tracking has been successfully integrated into the home finances system. This feature allows tracking expenses that should have been paid but were missed/delayed and will be paid in a future month.

## What Was Implemented

### 1. Core Manager (`src/deferred_payment_manager.py`)

**Key Features:**
- Add deferred payments with accrual and payment months
- Mark payments as paid (updates status, paid_by, payment_month)
- List pending/paid payments
- Generate detailed reports
- Calculate accrual adjustments for accounting
- Excel-based storage at `data/processed/deferred_payments.xlsx`

**Data Model:**
```python
@dataclass
class DeferredPayment:
    payment_id: str              # Auto-generated (DEF202509150001)
    description: str
    amount: Decimal
    category: ExpenseCategory
    expense_type: ExpenseType    # SHARED or INDIVIDUAL
    accrual_month: date          # When expense occurred
    payment_month: Optional[date]  # When paid/will pay
    responsible_person: str
    paid_by: Optional[str]
    status: str                  # PENDING, PAID, CANCELLED
    reason: str                  # Why deferred
    notes: str
```

### 2. CLI Commands (`main.py`)

**New Commands:**

```bash
# Add a deferred payment interactively
python main.py --add-deferred

# List all deferred payments (with pending summary)
python main.py --list-deferred

# Mark a payment as paid
python main.py --mark-paid DEF202509150001
```

**Interactive Add Workflow:**
1. Prompts for description, amount
2. Shows category options (numbered menu)
3. Asks for expense type (SHARED/INDIVIDUAL)
4. Requests accrual month (YYYY-MM format)
5. Requests expected payment month
6. Shows list of persons from config
7. Asks for reason and optional notes
8. Auto-generates payment ID
9. Saves to Excel

**Mark as Paid Workflow:**
1. Finds payment by ID
2. Shows payment details
3. Asks who paid (from config persons)
4. Asks for payment month (or uses current)
5. Updates status to PAID
6. Saves to Excel

### 3. Integration with Transaction Processor

**Auto-Display in `--process-all`:**

When processing transactions, if deferred payments exist, shows:
```
────────────────────────────────────────────────────────────────────────────────
DEFERRED PAYMENTS SUMMARY
────────────────────────────────────────────────────────────────────────────────

Pending payments: 2
Total amount: R2,500.00

By person:
  Michael: 1 pending (R500.00)
  Jacqui: 1 pending (R2,000.00)

Use --list-deferred to see details
```

**Implementation:**
- Added `_show_deferred_summary()` method to `TransactionProcessor`
- Called automatically after slip matching
- Silently skips if no deferred payments file exists
- Groups by responsible person

### 4. Documentation

**Created:**
- [DEFERRED_PAYMENTS_GUIDE.md](DEFERRED_PAYMENTS_GUIDE.md) (300+ lines)
  - Use cases and examples
  - Excel column structure
  - Manual and Python workflows
  - Accrual accounting explanations
  - Best practices

**Updated:**
- [QUICK_START.md](QUICK_START.md) - Added deferred payments section
- [main.py](main.py) help text - Added example commands

## Usage Example

### Scenario: Forgot to Pay Electricity Bill

**Step 1: Add Deferred Payment (September 30th)**
```bash
python main.py --add-deferred
```

Enter when prompted:
```
Description: September Electricity Bill
Amount (R): 500.00
Category: 3 (UTILITIES)
Type: 1 (SHARED)
Accrual month: 2025-09
Expected payment month: 2025-10
Responsible person: 1 (Michael)
Reason: Forgot to pay, will pay in October
Notes: Due on 25th
```

**Step 2: List Pending Payments**
```bash
python main.py --list-deferred
```

Output shows payment ID (e.g., `DEF202509300001`)

**Step 3: Pay the Bill (October 5th)**

After paying, mark as paid:
```bash
python main.py --mark-paid DEF202509300001
```

**Step 4: Automatic Integration**

When running `--process-all`, summary is shown automatically:
```bash
python main.py --process-all
```

## File Structure

```
data/
└── processed/
    └── deferred_payments.xlsx  # Excel file with all deferred payments
```

**Excel Columns:**
| Column | Description | User Editable |
|--------|-------------|---------------|
| payment_id | Auto-generated ID | No |
| description | Expense description | Yes |
| amount | Amount in Rands | Yes |
| category | ExpenseCategory | Yes |
| expense_type | SHARED/INDIVIDUAL | Yes |
| accrual_month | When incurred | Yes |
| payment_month | When paid | System (CLI) |
| responsible_person | Who should pay | Yes |
| paid_by | Who actually paid | System (CLI) |
| status | PENDING/PAID/CANCELLED | System (CLI) |
| reason | Why deferred | Yes |
| notes | Additional info | Yes |

## Accrual Accounting Support

The system supports both:

**Cash Accounting (Default):**
- Count expenses when money actually moves
- Simpler for household finances

**Accrual Accounting:**
- Count expenses when incurred (even if not yet paid)
- Use `get_accrual_adjustments(month)` method
- Returns adjustments: add_incurred_not_paid, subtract_paid_not_incurred

**Example:**
```python
# September adjustment (add R500 for incurred but unpaid)
adjustments = manager.get_accrual_adjustments(date(2025, 9, 1))
# Returns: {"add_incurred_not_paid": 500, "subtract_paid_not_incurred": 0, "net_adjustment": +500}

# October adjustment (subtract R500 to avoid double-counting)
adjustments = manager.get_accrual_adjustments(date(2025, 10, 1))
# Returns: {"add_incurred_not_paid": 0, "subtract_paid_not_incurred": 500, "net_adjustment": -500}
```

## Benefits

1. **Track Timing Mismatches**: Expense incurred in one month, paid in another
2. **Remember Missed Payments**: Don't lose track of what should have been paid
3. **Support Reimbursements**: One person pays, other reimburses later
4. **Accrual Accounting**: Accurate monthly expense allocation
5. **Auto-Visibility**: Shows in `--process-all` output automatically

## Technical Details

**Dependencies:**
- Existing: pandas, openpyxl, Decimal, date
- New imports in `main.py`: `DeferredPaymentManager`
- New imports in `transaction_processor.py`: `DeferredPaymentManager`

**Error Handling:**
- Graceful failure if deferred file doesn't exist
- Validation in CLI commands
- Input validation for dates and amounts

**Payment ID Format:**
- `DEF` + `YYYYMMDD` + 4-digit counter
- Example: `DEF202509300001` (first payment on Sept 30, 2025)

## Future Enhancements

Potential additions (not implemented):
- [ ] Recurring deferrals (e.g., rent always paid 5 days late)
- [ ] Automatic matching to transactions in statements
- [ ] Reminders for upcoming payment dates
- [ ] Integration with monthly split calculations
- [ ] CSV export of deferred payments
- [ ] Filter by status, person, or month

## Testing

**Manual Testing:**
- `--list-deferred` on empty system (shows helpful message)
- Integration with `--process-all` (silently skips if no file)
- CLI help text includes new commands

**Recommended Tests:**
1. Add a deferred payment via CLI
2. List deferred payments
3. Mark one as paid
4. List again (verify status changed)
5. Run `--process-all` (verify summary shows)
6. Manually edit Excel file (verify preserves edits)

## Migration Notes

**Existing Users:**
- No changes required to existing workflow
- Deferred payments are optional feature
- File only created when first payment added
- Safe to ignore if not needed

**New Users:**
- Feature available out-of-box
- Use `--add-deferred` to start tracking
- See [DEFERRED_PAYMENTS_GUIDE.md](DEFERRED_PAYMENTS_GUIDE.md) for details

## Related Files

**Core Implementation:**
- [src/deferred_payment_manager.py](src/deferred_payment_manager.py) (260 lines)
- [main.py](main.py) - CLI commands added (lines 619-765)
- [src/transaction_processor.py](src/transaction_processor.py) - Summary display (lines 460-498)

**Documentation:**
- [DEFERRED_PAYMENTS_GUIDE.md](DEFERRED_PAYMENTS_GUIDE.md) - Complete guide
- [QUICK_START.md](QUICK_START.md) - Updated with deferred payments section
- This file - Implementation summary

## Summary

The deferred payment system is fully implemented and integrated with the existing home finances workflow. It provides both CLI commands for interactive management and automatic visibility in the transaction processing pipeline. The system supports both cash and accrual accounting approaches while maintaining Excel as the primary data format for user accessibility.
