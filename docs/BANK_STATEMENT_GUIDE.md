# Bank Statement Processing Guide

## Overview

The system can automatically parse bank statement PDFs (FNB format) and extract transactions, making it much faster to create expense sheets for your monthly financial splitting.

## Features

- **PDF Parsing**: Extracts transactions from FNB credit card statement PDFs
- **Auto-Categorization**: Automatically categorizes expenses (Groceries, Fuel, Entertainment, etc.)
- **Excel Export**: Exports to expense sheet format compatible with person sheets
- **Summary Reports**: Shows spending by category

## Quick Start

### 1. Parse and View Bank Statement

```bash
python main.py --parse-bank-statement "path/to/statement.pdf"
```

This shows:
- Total expenses and payments
- Transactions grouped by category
- Summary by category

### 2. Export to Excel Expense Sheet

```bash
python main.py --export-bank-statement "path/to/statement.pdf" "Michael_September_2025.xlsx"
```

This creates an Excel file with:
- **Expenses Sheet**: All transactions with auto-categorized expenses
- **Income Sheet**: Empty template (fill in manually)

### 3. Review and Adjust

1. Open the exported Excel file
2. Review the automatically categorized expenses
3. Adjust categories if needed (some may be categorized as "OTHER")
4. Delete any personal (non-shared) expenses
5. Add your income to the Income sheet

### 4. Process Normally

```bash
python main.py --person-sheets Michael_September_2025.xlsx Jacqui_September_2025.xlsx
```

## Supported Banks

Currently supports:
- **FNB Credit Card Statements** (Private Clients format)

## Auto-Categorization

The system automatically categorizes transactions based on merchant names:

| Category | Merchants |
|----------|-----------|
| GROCERIES | Superspar, Checkers, Woolworths, Makro, Pick n Pay, Tops |
| FUEL | Engen, Shell, BP, Total |
| ENTERTAINMENT | Netflix, Spotify, DSTV, Restaurants, Cinema |
| MEDICAL | Hospitals, Clinics, Pharmacies, Doctors, Vets |
| UTILITIES | Electricity, Water, Municipal, Telkom, MTN, Internet |
| CLOTHING | Fashion stores, Baby City |
| HOUSEHOLD | Builders, Hardware, Mica, Chamberlain |
| TRANSPORT | Parking, Toll plazas |
| OTHER | Everything else |

## Example Workflow

### Scenario: Shared Credit Card Account

**Setup:**
- You and your partner share a credit card
- All purchases are made on this card
- You need to split expenses fairly

**Steps:**

1. **Download Statement**
   - Download PDF statement from online banking
   - Save to `data/bank statements/` folder

2. **Export to Excel**
   ```bash
   python main.py --export-bank-statement \
     "data/bank statements/CREDIT_CARD_033.pdf" \
     "Michael_September_2025.xlsx"
   ```

3. **Review Expenses**
   - Open `Michael_September_2025.xlsx`
   - Check categorization is correct
   - Delete non-shared expenses (if any)
   - Example: Delete "Personal gym membership"

4. **Add Income**
   - Fill in Income sheet with your NET salary
   - Add any other income (rental, bonuses, etc.)

5. **Partner Does Same**
   - Partner exports their own sheet (or uses same card statement)
   - If shared card, both use the same statement but split who "paid" what

6. **Process**
   ```bash
   python main.py --person-sheets \
     Michael_September_2025.xlsx \
     Jacqui_September_2025.xlsx
   ```

## Advanced: Splitting Shared Credit Card

If you have a **shared credit card** where both partners use it:

### Option 1: Split by Cardholder

If you can see which card number made each purchase:
1. Export statement once
2. Each person reviews and deletes the other person's transactions
3. Save as separate files
4. Process normally

### Option 2: All Expenses Shared

If everything on the card is shared:
1. Export to one person's sheet
2. That person shows they "paid" all shared costs
3. Partner has minimal expenses
4. System calculates proper transfer

### Option 3: Manual Split

1. Export to Excel
2. Manually assign who paid what in the "Type" column
3. Or use custom categories

## Tips

### 1. Check Auto-Categorization

Some merchants might be mis-categorized:
- Review the "OTHER" category - these need manual categorization
- Restaurants might be under ENTERTAINMENT or OTHER
- Adjust in Excel before processing

### 2. Handle Payments

Bank statement parser automatically ignores:
- ✅ Payments (marked "Cr" for credit)
- ✅ Interest/fees (captured separately)
- ✅ Transfers

You only see actual expenses.

### 3. Multiple Cards

If you have multiple cards:
1. Export each statement separately
2. Combine in Excel (copy/paste)
3. Or process each month with multiple statements

### 4. Verify Totals

After exporting, verify the total matches:
```
Statement total: R42,667.27
Exported total:  R42,360.81
```

Small differences are normal (due to fees, interest, etc.)

## Command Reference

### Parse Bank Statement
```bash
python main.py --parse-bank-statement PDF_FILE
```

**Output**: Expense report showing all transactions grouped by category

**Use when**: You want to quickly see what's on your statement

### Export Bank Statement
```bash
python main.py --export-bank-statement PDF_FILE OUTPUT_XLSX
```

**Output**: Excel file compatible with person sheets

**Use when**: You want to use the statement for financial splitting

## Troubleshooting

### "File not found"
Check the file path is correct. Use quotes if path has spaces:
```bash
python main.py --parse-bank-statement "data/bank statements/My Statement.pdf"
```

### "Error parsing PDF"
- Make sure it's a valid FNB credit card statement
- Check the PDF isn't password protected
- Try re-downloading the statement

### "Missing transactions"
Some transactions might not parse if:
- The format is unusual
- The transaction description is very long
- The line wraps in the PDF

Manually add these in Excel if needed.

### "Wrong categories"
Categories are best-effort based on merchant names. Review and adjust in Excel:
1. Open the exported file
2. Find mis-categorized items
3. Change the "Category" column value
4. Save and process

## Future Enhancements

Planned features:
- Support for more bank formats (Absa, Standard Bank, etc.)
- Machine learning for better categorization
- Direct import from online banking APIs
- Split detection for shared cards (by card number)

## Example Output

### Parse Command
```
================================================================================
BANK STATEMENT EXPENSE REPORT
================================================================================
Statement Date: 07 Oct 2025
Statement No: 033

Opening Balance: R   56,046.71
Total Expenses:  R   42,667.27
Total Payments:  R   50,468.00
Closing Balance: R   48,936.72

================================================================================
TRANSACTIONS
================================================================================

GROCERIES (R7,864.64 - 19 transactions)
--------------------------------------------------------------------------------
  05 Sep Superspar Willow Way              R    314.99
  06 Sep Superspar Willow Way              R    410.00
  ...

================================================================================
CATEGORY SUMMARY
================================================================================
GROCERIES            R    7,864.64 ( 19 transactions)
FUEL                 R    4,252.48 (  4 transactions)
ENTERTAINMENT        R    1,069.00 (  2 transactions)
...
================================================================================
TOTAL                R   42,360.81 ( 65 transactions)
================================================================================
```

### Export Command
```
[OK] Bank statement exported successfully!

Output: Michael_September_2025.xlsx

Summary:
  Total expenses:  R42,667.27
  Transactions:    65
  Statement date:  07 Oct 2025

Next steps:
1. Open Michael_September_2025.xlsx in Excel
2. Review the expenses and adjust categories as needed
3. Add income to the Income sheet
4. Use with --person-sheets to process
```

## See Also

- [NEW_WORKFLOW_GUIDE.md](NEW_WORKFLOW_GUIDE.md) - Person sheets workflow
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet
- [NET_INCOME_MODE.md](NET_INCOME_MODE.md) - NET income mode guide
