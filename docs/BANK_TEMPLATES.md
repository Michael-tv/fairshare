# Bank Statement Templates Guide

Complete guide to creating and customizing YAML templates for parsing bank statements from any bank.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Template Structure](#template-structure)
3. [Creating Your First Template](#creating-your-first-template)
4. [Pattern Writing Guide](#pattern-writing-guide)
5. [Testing Templates](#testing-templates)
6. [Troubleshooting](#troubleshooting)
7. [Example Templates](#example-templates)
8. [Advanced Features](#advanced-features)

---

## Quick Start

### Using Existing Templates

```bash
# List available templates
python main.py --list-templates

# Auto-detect bank and parse
python main.py --parse-bank-statement statement.pdf

# Use specific template
python main.py --parse-bank-statement statement.pdf --bank-template fnb_credit_card

# Export to Excel
python main.py --export-bank-statement statement.pdf output.xlsx --bank-template absa_cheque
```

### Creating a New Template

1. Copy an existing template from `bank_templates/` as a starting point
2. Open your PDF statement and examine the transaction format
3. Update the patterns in the YAML file to match your statement
4. Test with: `python main.py --parse-bank-statement your_statement.pdf --bank-template your_template`

---

## Template Structure

A bank template is a YAML file with the following main sections:

```yaml
bank_name: "BankName"        # Name of the bank
account_type: "AccountType"  # Type of account (Credit Card, Cheque, etc.)
country: "ZA"               # Country code (optional)

detection:          # How to auto-detect this template from PDF
parsing:            # How to extract transactions
sections:           # Where transactions appear in the statement
summary:            # How to extract statement metadata
output:             # How to label the extracted data
```

---

## Template Sections Explained

### 1. Detection

Auto-detection looks for markers in the first page of the PDF:

```yaml
detection:
  markers:
    - "FNB CREDIT CARD"
    - "CREDIT CARD"
  priority: 10  # Higher = checked first (default: 0)
```

**Tips:**
- Use unique text that appears on the first page
- Add multiple markers for reliability
- Higher priority templates are checked first during auto-detection

### 2. Parsing Configuration

The heart of the template - defines how to extract transaction data:

#### Transaction Pattern

Use named regex groups to extract fields:

```yaml
parsing:
  transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+(?P<description>.+?)\s+(?P<amount>[\d\s,.]+)(?P<credit>Cr)?$'
```

**Named Groups:**
- `day` - Transaction day
- `month` - Month abbreviation or number
- `year` - Year (optional, can use statement year)
- `description` - Transaction description
- `amount` - Amount value
- `credit` - Credit indicator (optional)

#### Date Configuration

```yaml
parsing:
  date:
    day_group: "day"          # Which regex group has the day
    month_group: "month"      # Which regex group has the month
    year_group: "year"        # Optional - omit to use statement year
    format: "%d %b"           # Date format string
    year_source: "statement"  # "statement" or "pattern"
    adjust_year: true         # Handle year boundary transactions

    # Optional: Translate non-English months
    month_translation:
      Mei: "May"     # Afrikaans
      Okt: "Oct"
      Des: "Dec"
```

**Format Codes:**
- `%d` - Day (01-31)
- `%m` - Month number (01-12)
- `%b` - Month abbreviation (Jan, Feb, etc.)
- `%B` - Full month name
- `%Y` - Four-digit year
- `%y` - Two-digit year

#### Amount Configuration

```yaml
parsing:
  amount:
    group: "amount"               # Regex group name
    decimal_separator: "."        # Usually "." or ","
    thousands_separator: ","      # Usually "," or " " or "."

    # How to identify credits vs debits
    credit_indicator:
      group: "credit"             # Regex group name
      value: "Cr"                 # Value indicating credit
      debit_value: "Dr"           # Optional debit indicator
      invert: false               # Set true if logic is reversed
```

#### Description Processing

```yaml
parsing:
  description:
    group: "description"          # Regex group name
    min_length: 3                 # Skip if shorter than this

    # Cleanup rules (applied in order)
    cleanup:
      - pattern: '\s+ZA$'         # Remove trailing country code
        replace: ''
      - pattern: '\s{2,}'         # Collapse multiple spaces
        replace: ' '
      - pattern: '^\s+|\s+$'      # Trim whitespace
        replace: ''
```

#### Optional Fields

```yaml
parsing:
  # Extract location/country code
  location:
    pattern: '\b(?P<country>[A-Z]{2})\s*$'
    group: "country"

  # Track card numbers
  card_number:
    context_pattern: 'Card No\.\s+(?P<card>[\d*\s]+)'
    inline_pattern: '\d{6}\*(?P<digits>\d{4})'
    extract_last_digits: 4
    scope: "until_next_card"  # How long this card applies

  # Track running balance (for verification)
  balance:
    group: "balance"
    decimal_separator: "."
    thousands_separator: ","
```

### 3. Section Boundaries

Define where transaction data appears:

```yaml
sections:
  # Transaction section starts after these markers
  start_markers:
    - "Transaction Date"
    - "Card No."

  # Transaction section ends before these markers
  end_markers:
    - "Closing Balance"
    - "Account Summary"

  # Lines containing these are always skipped
  skip_lines:
    - "Opening Balance"
    - "Page "
    - "Interest"
```

**Tips:**
- If no start_markers, all lines are checked
- Use specific markers to avoid false matches
- Skip lines for headers, footers, summary sections

### 4. Summary Extraction

Extract statement metadata:

```yaml
summary:
  statement_date:
    pattern: 'Statement Date\s+(?P<date>\d{2}\s+\w+\s+\d{4})'
    format: "%d %b %Y"
    # Can also use 'patterns' (list) instead of 'pattern'
    patterns:
      - 'Statement Date\s+(?P<date>...)'
      - 'Date:\s+(?P<date>...)'

  opening_balance:
    pattern: 'Opening Balance\s+(?P<amount>[\d\s,.]+)'

  closing_balance:
    pattern: 'Closing Balance\s+(?P<amount>[\d\s,.]+)'

  total_expenses:
    pattern: 'Total Debits\s+(?P<amount>[\d\s,.]+)'

  total_payments:
    pattern: 'Total Credits\s+(?P<amount>[\d\s,.]+)'

  interest_fees:
    pattern: 'Interest.*?\s+(?P<amount>[\d\s,.]+)'

  statement_number:
    pattern: 'Statement No\.:?\s*(?P<number>\d+)'

  account_number:
    pattern: 'Account\s+(?P<account>[\d\s]+)'
```

**Named Groups:**
- For amounts: use `(?P<amount>...)`
- For dates: use `(?P<date>...)`
- For numbers: use `(?P<number>...)`
- For accounts: use `(?P<account>...)`

### 5. Output Configuration

```yaml
output:
  account_type: "credit_card"  # Label for this account type
```

---

## Pattern Writing Guide

### Common Regex Patterns

#### Dates

```yaml
# DD Mon (e.g., "05 Sep")
'(?P<day>\d{2})\s+(?P<month>\w{3})'

# DD/MM/YYYY (e.g., "05/09/2024")
'(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{4})'

# YYYY-MM-DD (e.g., "2024-09-05")
'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'

# DD Month YYYY (e.g., "05 September 2024")
'(?P<day>\d{2})\s+(?P<month>\w+)\s+(?P<year>\d{4})'
```

#### Amounts

```yaml
# South African format: 1,234.56 or 1 234.56
'(?P<amount>\d{1,3}(?:[,\s]\d{3})*\.\d{2})'

# European format: 1.234,56
'(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})'

# With optional currency symbol: R 1,234.56
'R?\s*(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2})'

# With credit indicator: 1,234.56Cr or 1,234.56DR
'(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2})(?P<credit>Cr|DR)?'
```

#### Descriptions

```yaml
# Greedy match (captures everything)
'(?P<description>.+)'

# Non-greedy match (stops at first amount)
'(?P<description>.+?)\s+(?P<amount>...)'

# Match until country code
'(?P<description>.+?)\s+(?:ZA|US|GB)\s+(?P<amount>...)'
```

### Transaction Line Examples

Let's create patterns for different statement formats:

#### Example 1: FNB Credit Card
```
Transaction line: "05 Sep Superspar Willow Way ZA 314.99"
```

Pattern:
```yaml
transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+(?P<description>.+?)\s+(?P<amount>[\d\s,.]+)(?P<credit>Cr)?$'
```

#### Example 2: ABSA Cheque Account
```
Transaction line: "2024/09/05 POS Purchase Woolworths 500.00 DR 5,000.00"
```

Pattern:
```yaml
transaction_pattern: '(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})\s+(?P<description>.+?)\s+(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2})\s+(?P<indicator>DR|CR)\s+(?P<balance>[\d,.]+)'
```

#### Example 3: Standard Bank
```
Transaction line: "12 SEP WOOLWORTHS RONDEBOSCH 450.00"
```

Pattern:
```yaml
transaction_pattern: '(?P<day>\d{2})\s+(?P<month>[A-Z]{3})\s+(?P<description>.+?)\s+(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2})'
```

### Testing Your Regex

Use online tools to test patterns:
1. Visit https://regex101.com/
2. Select "Python" flavor
3. Paste a sample transaction line
4. Test your pattern
5. Verify named groups capture correctly

---

## Creating Your First Template

### Step-by-Step Walkthrough

Let's create a template for **Capitec Credit Card**:

**Step 1: Examine Your Statement**

Open your PDF and find a transaction line. Example:
```
15 AUG CHECKERS SOMERSET WEST 789.50
```

**Step 2: Create Template File**

Create `bank_templates/capitec_credit_card.yaml`:

```yaml
bank_name: "Capitec"
account_type: "Credit Card"
country: "ZA"

detection:
  markers:
    - "CAPITEC"
    - "CREDIT CARD"
  priority: 5

parsing:
  # Pattern for: DD MON DESCRIPTION AMOUNT
  transaction_pattern: '(?P<day>\d{2})\s+(?P<month>[A-Z]{3})\s+(?P<description>.+?)\s+(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2})'

  date:
    day_group: "day"
    month_group: "month"
    format: "%d %b"
    year_source: "statement"
    adjust_year: true

    # Uppercase months - translate to titlecase
    month_translation:
      JAN: "Jan"
      FEB: "Feb"
      MAR: "Mar"
      APR: "Apr"
      MAY: "May"
      JUN: "Jun"
      JUL: "Jul"
      AUG: "Aug"
      SEP: "Sep"
      OCT: "Oct"
      NOV: "Nov"
      DEC: "Dec"

  amount:
    group: "amount"
    decimal_separator: "."
    thousands_separator: ","

  description:
    group: "description"
    cleanup:
      - pattern: '\s{2,}'
        replace: ' '
    min_length: 3

sections:
  start_markers:
    - "Transaction Date"
    - "DATE"
  end_markers:
    - "Total"
    - "Closing Balance"
  skip_lines:
    - "Opening Balance"
    - "Page "

summary:
  statement_date:
    pattern: 'Statement Date\s+(?P<date>\d{2}\s+[A-Z]{3}\s+\d{4})'
    format: "%d %b %Y"
    month_translation:
      JAN: "Jan"
      # ... (same as above)

  opening_balance:
    pattern: 'Opening Balance\s+(?P<amount>[\d\s,.]+)'

  closing_balance:
    pattern: 'Closing Balance\s+(?P<amount>[\d\s,.]+)'

  total_expenses:
    pattern: 'Total Purchases\s+(?P<amount>[\d\s,.]+)'

  total_payments:
    pattern: 'Total Payments\s+(?P<amount>[\d\s,.]+)'

  statement_number:
    pattern: 'Statement\s+(?P<number>\d+)'

  account_number:
    pattern: 'Card Number\s+(?P<account>[\d\s*]+)'

output:
  account_type: "capitec_credit_card"
```

**Step 3: Test Template**

```bash
python main.py --parse-bank-statement capitec_statement.pdf --bank-template capitec_credit_card
```

**Step 4: Refine**

If transactions aren't extracted:
1. Check section markers (start_markers/end_markers)
2. Verify transaction_pattern matches your lines
3. Test pattern on regex101.com
4. Check for whitespace or special characters

---

## Testing Templates

### Quick Test

```bash
# Test parsing with specific template
python main.py --parse-bank-statement statement.pdf --bank-template my_template

# Check if auto-detection works
python main.py --parse-bank-statement statement.pdf
```

### Validation Checklist

✅ **Transactions extracted?**
- Check that transaction count matches statement
- Verify amounts are correct
- Check dates parse correctly

✅ **Summary extracted?**
- Statement date correct?
- Opening/closing balances match?
- Total expenses/payments correct?

✅ **Descriptions clean?**
- No extra spaces?
- No unwanted characters?
- Location codes removed if needed?

✅ **Auto-detection works?**
- Parser detects correct template?
- Warning if wrong template specified?

### Debugging Tips

```bash
# Run the bank_statement_parser directly
python src/bank_statement_parser.py statement.pdf my_template

# Check template loading
python -c "from bank_template import TemplateRegistry; from pathlib import Path; reg = TemplateRegistry(Path('bank_templates')); print(reg.list_all())"
```

---

## Troubleshooting

### Problem: No transactions extracted

**Causes:**
1. Section markers don't match
2. Transaction pattern doesn't match line format
3. Lines being skipped

**Solutions:**
```yaml
# Try removing start/end markers temporarily
sections:
  start_markers: []  # Empty = scan all lines
  end_markers: []

# Simplify transaction pattern
# Start with just: '(?P<description>.+)'
# Then add fields one by one

# Reduce skip_lines to minimum
skip_lines:
  - "Page "
```

### Problem: Dates parsing incorrectly

**Causes:**
1. Month format doesn't match
2. Year adjustment logic wrong
3. Date format string wrong

**Solutions:**
```yaml
date:
  # Add month translation
  month_translation:
    Okt: "Oct"
    Mei: "May"
    Des: "Dec"

  # Try different format
  format: "%d %b"      # 05 Sep
  # or
  format: "%d/%m/%Y"   # 05/09/2024
  # or
  format: "%Y-%m-%d"   # 2024-09-05

  # Disable year adjustment if problematic
  adjust_year: false
```

### Problem: Amounts parsing incorrectly

**Causes:**
1. Thousands/decimal separators wrong
2. Currency symbols not removed
3. Spaces in amount

**Solutions:**
```yaml
amount:
  decimal_separator: "."
  thousands_separators: [",", " "]  # List for multiple

cleanup:
  - pattern: '[R$£€]'  # Remove currency symbols
    replace: ''
```

### Problem: Template not auto-detected

**Causes:**
1. Detection markers don't appear on first page
2. Another template has higher priority

**Solutions:**
```yaml
detection:
  # Add more specific markers
  markers:
    - "BANK NAME ACCOUNT STATEMENT"  # More specific
    - "Unique text from first page"

  # Increase priority
  priority: 20  # Higher than competing templates
```

### Problem: Wrong transactions (noise)

**Causes:**
1. Pattern too greedy
2. Section markers too loose
3. Not enough skip_lines

**Solutions:**
```yaml
# Make pattern more specific
transaction_pattern: '^(?P<day>\d{2})\s+...'  # ^ = start of line

# Add more skip patterns
skip_lines:
  - "Subtotal"
  - "Balance Forward"
  - "Interest"
  - "Fees"

# Tighten section boundaries
sections:
  start_markers:
    - "TRANSACTIONS"  # More specific
```

---

## Example Templates

### Minimal Template

Simplest possible template:

```yaml
bank_name: "MyBank"
account_type: "Credit Card"

detection:
  markers:
    - "MYBANK"

parsing:
  transaction_pattern: '(?P<description>.+?)\s+(?P<amount>\d+\.\d{2})'
  amount:
    group: "amount"
  description:
    group: "description"

sections:
  skip_lines:
    - "Balance"
    - "Total"

summary:
  statement_date:
    pattern: 'Date\s+(?P<date>\d{2}/\d{2}/\d{4})'
    format: "%d/%m/%Y"

output:
  account_type: "mybank_card"
```

### Bilingual Template

Handles English/Afrikaans:

```yaml
bank_name: "FNB"
account_type: "Fusion Account"

detection:
  markers:
    - "FUSION PRIVATE CLIENTS"
    - "Datum Beskrywing Bedrag"  # Afrikaans header
  priority: 15

parsing:
  date:
    month_translation:
      Mei: "May"
      Okt: "Oct"
      Des: "Dec"

sections:
  start_markers:
    - "Datum Beskrywing"   # Afrikaans
    - "Date Description"   # English
  end_markers:
    - "Staatsaldo"         # Afrikaans
    - "Statement Balance"  # English

summary:
  opening_balance:
    patterns:
      - 'Opening Balance\s+(?P<amount>...)'
      - 'Openingsaldo\s+(?P<amount>...)'
```

### Multi-Format Amount Template

Handles different amount formats:

```yaml
parsing:
  amount:
    group: "amount"
    decimal_separator: "."
    thousands_separators: [",", " ", "."]  # Handle all variants

  # Pattern captures amount in multiple formats
  transaction_pattern: '... (?P<amount>(?:\d{1,3}[,.\s])*\d{1,3}\.\d{2}) ...'
```

---

## Advanced Features

### Context Tracking

Track card numbers across multiple transactions:

```yaml
parsing:
  card_number:
    # Appears before transaction block
    context_pattern: 'Card No\.\s+(?P<card>[\d*\s]+)'

    # Applies to all following transactions until next card marker
    scope: "until_next_card"

    # Extract last 4 digits
    extract_last_digits: 4
```

### Inline Field Extraction

Extract data from within the transaction line:

```yaml
parsing:
  card_number:
    # Extract from within transaction description
    inline_pattern: '\d{6}\*(?P<digits>\d{4})'
    extract_last_digits: 4
```

### Multiple Pattern Support

Try multiple patterns for robustness:

```yaml
summary:
  statement_date:
    patterns:
      - 'Statement Date:\s+(?P<date>\d{2}/\d{2}/\d{4})'
      - 'Date:\s+(?P<date>\d{4}-\d{2}-\d{2})'
      - 'Datum:\s+(?P<date>\d{2}\s+\w+\s+\d{4})'
    format: "%d/%m/%Y"
```

### Credit/Debit Logic

Handle different indicator systems:

```yaml
# Standard: Cr = credit, Dr = debit
amount:
  credit_indicator:
    group: "indicator"
    value: "Cr"
    debit_value: "Dr"

# Inverted: Kt = credit, Dt = debit (some banks)
amount:
  credit_indicator:
    group: "indicator"
    value: "Kt"
    invert: true  # Reverse the logic
```

### Balance Tracking

Extract and verify running balance:

```yaml
parsing:
  balance:
    group: "balance"
    decimal_separator: "."
    thousands_separator: ","

# Pattern includes balance
transaction_pattern: '... (?P<amount>\d+\.\d{2}) (?P<balance>\d+\.\d{2})'
```

---

## Best Practices

### Template Design

✅ **DO:**
- Start with a working template and modify
- Use specific detection markers
- Test with multiple statement months
- Add comments explaining patterns
- Use named regex groups
- Handle edge cases (year boundaries, etc.)

❌ **DON'T:**
- Make patterns too greedy
- Hard-code specific values
- Skip testing with real statements
- Forget to handle bilingual text
- Use overly complex regex

### Pattern Writing

✅ **DO:**
- Test patterns on regex101.com
- Use non-greedy matching (`.+?`)
- Anchor patterns where possible (`^`, `$`)
- Handle optional whitespace (`\s*`, `\s+`)
- Use character classes (`\w`, `\d`)

❌ **DON'T:**
- Use greedy matching unnecessarily (`.+`)
- Hardcode whitespace count
- Forget about special characters
- Make patterns too specific (dates, account numbers)

### Maintenance

✅ **DO:**
- Test templates after bank statement format changes
- Keep templates in version control
- Document customizations
- Share templates with community

❌ **DON'T:**
- Modify working templates unnecessarily
- Delete old templates (rename instead)
- Forget to update detection markers

---

## Getting Help

### Resources

- Example templates: `bank_templates/*.yaml`
- Regex tester: https://regex101.com (use Python flavor)
- Python datetime formats: https://strftime.org/

### Common Questions

**Q: Can I have multiple templates for one bank?**
A: Yes! Create separate files for each account type (e.g., `fnb_credit_card.yaml`, `fnb_cheque.yaml`).

**Q: How do I test a template without a PDF?**
A: You can't fully test without a PDF, but you can test regex patterns on regex101.com.

**Q: Can templates handle PDFs with multiple accounts?**
A: Not currently. Process each account's statement separately with its own template.

**Q: My bank changed their format. What do I do?**
A: Create a new template with a version suffix (e.g., `mybank_v2.yaml`) or update the existing one.

**Q: Can I share my templates?**
A: Yes! Templates are just YAML files. Share them however you like.

---

## Summary

Creating bank templates:

1. **Examine** your statement format
2. **Copy** an existing similar template
3. **Modify** patterns to match your format
4. **Test** with `--parse-bank-statement`
5. **Refine** until all transactions extract correctly
6. **Verify** with multiple statement months

The system is designed to be flexible and handle any bank's format. With the right template, you can parse any PDF bank statement automatically!

For more help, see the example templates in `bank_templates/` or refer to [CLAUDE.md](../CLAUDE.md) for system architecture.
