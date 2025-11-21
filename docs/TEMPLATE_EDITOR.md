# Template Editor Guide

The **Template Editor** is a user-friendly interface for creating and editing bank statement templates with real-time validation and visual feedback.

## Overview

The Template Editor provides a **3-panel side-by-side interface** that makes creating bank templates easy and error-free:

```
┌─────────────────────────────────────────────────────────────────────┐
│  📝 Bank Template Editor                                            │
│  Create and edit bank statement templates with real-time validation │
├─────────────────────────────────────────────────────────────────────┤
│ Template: [FNB Credit Card ▼] [➕ New] [💾 Save] [📄 Load PDF] [▶️] │
├──────────────┬───────────────────┬──────────────────────────────────┤
│ Template     │ Statement         │ Parsed Output &                  │
│ Rules (YAML) │ Preview           │ Validation                       │
├──────────────┼───────────────────┼──────────────────────────────────┤
│              │                   │ ┌─ Validation Results ─────────┐│
│ bank_name:   │ --- PAGE 1 ---    │ │ Score: 95/100                ││
│   "FNB"      │                   │ │ Status: ✅ VALID             ││
│              │ FNB CREDIT CARD   │ │                              ││
│ detection:   │ Statement Date    │ │ ℹ️  INFO (1):                ││
│   markers:   │ 01 Nov 2024       │ │  • Template is valid!        ││
│   - "FNB"    │                   │ └──────────────────────────────┘│
│   priority:  │ Opening Balance   │                                  │
│     10       │ R 1,234.56        │ ┌─ Statement Summary ──────────┐│
│              │                   │ │ Statement: 2024-11-01        ││
│ parsing:     │ Transaction Date  │ │ Opening: R 1,234.56          ││
│   pattern:   │ 05 Nov Groceries  │ │ Closing: R 987.65            ││
│   '(?P<day>  │ 06 Nov Fuel       │ │ Expenses: R 543.21           ││
│              │ ...               │ └──────────────────────────────┘│
│              │                   │                                  │
│ [Auto-save]  │ ✅ Matched 15/15  │ ┌─ Parsed Transactions ────────┐│
│ [Syntax OK]  │    transactions   │ │ Date     | Description |Amt  ││
│              │                   │ │ 2024-11-05 Groceries  R150  ││
│              │                   │ │ 2024-11-06 Fuel       R200  ││
│              │                   │ │          ...                 ││
│              │                   │ └──────────────────────────────┘│
│              │                   │ [📊 Export to Excel]             │
└──────────────┴───────────────────┴──────────────────────────────────┘
```

## Features

### ✨ **Real-Time Validation**
- As you type, the template is automatically validated
- Errors, warnings, and info messages appear instantly
- Validation score (0-100) shows template quality

### 🎨 **Syntax Highlighting**
- YAML syntax highlighting for easy reading
- Keys, strings, numbers, and comments are color-coded
- Clear visual structure

### 📄 **PDF Preview**
- Load a sample bank statement PDF
- See the extracted text from your statement
- Matched transaction lines are highlighted
- Multi-page support with page indicators

### ✅ **Live Parsing**
- See parsed transactions immediately as you edit
- Transaction table shows: Date, Description, Amount, Type, Card Number
- Color-coded amounts: 🟢 Credits (green) | 🔴 Debits (red)
- Summary section shows totals and counts

### 💾 **Easy Save/Load**
- Load existing templates from dropdown
- Create new templates with skeleton code
- Save directly to `bank_templates/` folder
- Auto-reload template registry after saving

### 📊 **Export Functionality**
- Export parsed transactions to Excel
- Test your template before using it in production
- Verify all data is captured correctly

## Quick Start Guide

### 1. **Open the Template Editor**
Launch FairShare GUI and click the **"Template Editor"** tab.

### 2. **Load an Existing Template** (to learn or modify)
1. Select a template from the dropdown (e.g., "FNB - Credit Card")
2. The YAML content loads in the left panel
3. Validation results appear in the right panel

### 3. **Load a Sample PDF**
1. Click **"📄 Load Sample PDF"**
2. Select a bank statement PDF from your computer
3. The PDF text appears in the middle panel
4. Transactions are automatically parsed and shown in the right panel

### 4. **Edit the Template**
1. Make changes to the YAML in the left panel
2. After 1 second of inactivity, the template is auto-validated
3. See results update in real-time:
   - ✅ Validation status
   - 📊 Parsed transaction count
   - 🟢/🔴 Transaction table
   - ⚠️ Errors/warnings

### 5. **Save Your Changes**
1. Click **"💾 Save Template"**
2. Confirm the save
3. Template is saved to `bank_templates/{name}.yaml`
4. Ready to use in statement processing!

## Creating a New Template

### Step 1: Create from Skeleton
1. Click **"➕ New Template"**
2. Enter a name (e.g., `mybank_credit_card`)
3. A skeleton template is loaded with all required fields

### Step 2: Load a Sample Statement
1. Click **"📄 Load Sample PDF"**
2. Select a real bank statement for your bank
3. Study the format in the middle panel

### Step 3: Customize Detection
Update these fields to match your bank:

```yaml
bank_name: "MyBank"
account_type: "Credit Card"

detection:
  markers:  # Unique text on first page
    - "MYBANK"
    - "CREDIT CARD"
  priority: 5  # Higher = checked first (1-10)
```

### Step 4: Define Transaction Pattern
Look at transaction lines in the PDF preview and create a regex pattern:

**Example transaction line:**
```
05 Nov Groceries Store          150.00
```

**Regex pattern with named groups:**
```yaml
parsing:
  transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+(?P<description>.+?)\s+(?P<amount>[\d,.]+)'
```

**Named groups you can use:**
- `day` - Day of month (e.g., "05")
- `month` - Month name (e.g., "Nov")
- `year` - Year (optional)
- `description` - Transaction description
- `amount` - Transaction amount
- `credit` - Credit indicator (e.g., "Cr")
- `card_digits` - Last 4 digits of card

### Step 5: Configure Date Parsing
```yaml
date:
  day_group: "day"      # Which regex group has the day
  month_group: "month"  # Which regex group has the month
  format: "%d %b"       # Python strftime format
  year_source: "statement"  # Get year from statement date
```

For bilingual statements (Afrikaans/English):
```yaml
date:
  month_translation:
    Jan: "Jan"
    Feb: "Feb"
    Mrt: "Mar"  # Afrikaans → English
    Okt: "Oct"
    # ...
```

### Step 6: Configure Amount Parsing
```yaml
amount:
  group: "amount"           # Which regex group has amount
  decimal_separator: "."    # Usually "." or ","
  thousands_separator: ","  # Usually "," or " "

  # Optional: credit indicator
  credit_indicator:
    group: "credit"    # Regex group name
    value: "Cr"        # Text that means credit
```

### Step 7: Configure Description Cleanup
Remove unwanted text from descriptions:

```yaml
description:
  group: "description"
  cleanup:  # List of regex replacements
    - pattern: '\s+ZA\s*$'     # Remove " ZA" at end
      replace: ''
    - pattern: '\s{2,}'        # Replace multiple spaces
      replace: ' '
  min_length: 3  # Minimum description length
```

### Step 8: Define Sections
Tell the parser where transactions start and end:

```yaml
sections:
  start_markers:  # Text before first transaction
    - "Transaction Date"
    - "Date Description"

  end_markers:  # Text after last transaction
    - "Closing Balance"
    - "Total"

  skip_lines:  # Lines to ignore
    - "Page "
    - "Opening Balance"
    - "Statement continues"
```

### Step 9: Extract Summary Information
```yaml
summary:
  statement_date:
    pattern: 'Statement Date\s+(?P<date>\d{2}\s+\w+\s+\d{4})'
    format: "%d %b %Y"

  opening_balance:
    pattern: 'Opening Balance\s+(?P<amount>[\d\s,.]+)'

  closing_balance:
    pattern: 'Closing Balance\s+(?P<amount>[\d\s,.]+)'
```

### Step 10: Test and Refine
1. Click **"▶️ Parse"** to test
2. Check validation results:
   - ✅ All errors resolved?
   - 🟢 All transactions captured?
   - 📊 Correct amounts?
3. Adjust patterns as needed
4. Re-test until perfect!

### Step 11: Save
1. Click **"💾 Save Template"**
2. Template is ready to use!

## Validation Scoring

The validator checks your template and assigns a score:

| Score | Status | Meaning |
|-------|--------|---------|
| 100 | ✅ Perfect | All required fields, no warnings |
| 90-99 | ✅ Excellent | Minor warnings, fully functional |
| 70-89 | ⚠️ Good | Some warnings, may need adjustment |
| 50-69 | ⚠️ Fair | Multiple issues, testing needed |
| <50 | ❌ Poor | Critical errors, won't work |

### Common Validation Messages

**🔴 ERRORS (must fix):**
- Missing required field (e.g., `bank_name`)
- Invalid regex pattern
- Invalid date format
- Missing named groups in pattern

**🟡 WARNINGS (should fix):**
- No detection markers (auto-detect won't work)
- Low priority value
- Missing summary patterns
- No description cleanup rules

**ℹ️ INFO (optional):**
- Template is valid
- Optional fields are missing but OK

## Tips for Success

### 1. **Start with a Similar Template**
Load an existing template that's closest to your bank format and modify it.

### 2. **Use Real Statements**
Always test with actual PDF statements from your bank.

### 3. **Test Edge Cases**
Try statements with:
- Different months
- Both credits and debits
- Special characters in descriptions
- Multiple pages

### 4. **Regex Testing**
Use regex tools like [regex101.com](https://regex101.com) to test patterns before adding them.

### 5. **Check the PDF Preview**
Look at the actual PDF text in the middle panel - formats can be different from what you see in a PDF viewer.

### 6. **Iterate Quickly**
The real-time validation lets you make small changes and see results instantly.

## Common Patterns

### Credit Cards
```yaml
# Pattern for: 05 Nov Groceries Store 150.00
transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+(?P<description>.+?)\s+(?P<amount>[\d,.]+)'
```

### Cheque Accounts
```yaml
# Pattern for: 2024-11-05 Debit Order Insurance -150.00
transaction_pattern: '(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\s+(?P<description>.+?)\s+(?P<amount>-?[\d,.]+)'
```

### With Card Numbers
```yaml
# Pattern for: 05 Nov Card *1234 Store 150.00
transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+Card\s+\*(?P<card>\d{4})\s+(?P<description>.+?)\s+(?P<amount>[\d,.]+)'
```

### Credit/Debit Indicators
```yaml
# Pattern for: 05 Nov Groceries 150.00 Dr
transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+(?P<description>.+?)\s+(?P<amount>[\d,.]+)\s*(?P<credit>Cr|Dr)?'

amount:
  credit_indicator:
    group: "credit"
    value: "Cr"  # "Cr" means credit, anything else is debit
```

## Troubleshooting

### ❌ "No transactions parsed"
**Solution:** Check your transaction pattern matches the actual lines in the PDF preview. Copy a line from the middle panel and test your regex.

### ❌ "Invalid regex pattern"
**Solution:** Escape special characters like `.`, `(`, `)`, `[`, `]` with backslash. Use raw strings in regex: `'pattern'` not `"pattern"`.

### ❌ "Date parsing failed"
**Solution:** Ensure `day_group` and `month_group` match your regex named groups. Check the date format string.

### ⚠️ "Wrong transaction count"
**Solution:** Adjust `start_markers` and `end_markers` to correctly identify the transaction section. Check `skip_lines` isn't skipping transactions.

### ⚠️ "Amounts are wrong"
**Solution:** Check `decimal_separator` and `thousands_separator`. Verify `credit_indicator` is correct if used.

### ⚠️ "Descriptions are messy"
**Solution:** Add cleanup rules to remove unwanted text. Test each rule individually.

## Examples

See the existing templates for complete examples:
- `bank_templates/fnb_credit_card.yaml` - Credit card with date translation
- `bank_templates/fnb_personal.yaml` - Cheque account, bilingual
- `bank_templates/fnb_fusion.yaml` - Private banking, complex patterns
- `bank_templates/absa_cheque.yaml` - Alternative bank format
- `bank_templates/absa_credit_card.yaml` - Credit card alternative

## Integration with FairShare

Once you've created and tested your template:

1. **Auto-Detection**: Templates with `detection.markers` are automatically detected when processing statements

2. **Manual Selection**: Use `--bank-template {name}` flag:
   ```bash
   python main.py --parse-bank-statement statement.pdf --bank-template mybank_credit
   ```

3. **GUI Processing**: Your template appears in the "Process Statements" tab dropdown

4. **Batch Processing**: Process multiple statements with the same template

## Advanced Features

### Multiple Date Formats
Handle statements with different date formats:
```yaml
date:
  format: "%d %b %Y"  # Try this first
  fallback_formats:   # If first fails, try these
    - "%d/%m/%Y"
    - "%Y-%m-%d"
```

### Conditional Patterns
Use multiple patterns for different transaction types:
```yaml
parsing:
  patterns:
    - name: "standard"
      pattern: '(?P<day>\d{2})...'
      priority: 10
    - name: "fee"
      pattern: 'Fee\s+(?P<description>.+?)...'
      priority: 5
```

### Custom Validators
Add custom validation rules:
```yaml
validation:
  require_card_numbers: false
  min_description_length: 3
  allow_negative_amounts: true
```

## Need Help?

- Check existing templates for examples
- Look at the PDF preview to understand the format
- Use the validation messages to guide you
- Test with multiple statements from different months
- Refer to the regex pattern examples above

Happy templating! 🎉
