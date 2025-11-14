# Invoice Slip Matching System

## Overview

The invoice slip matching system helps you match scanned invoice slips (receipts) to transactions on your bank statements. This is useful for:
- Verifying transactions
- Categorizing expenses based on actual purchases
- Tracking what was purchased for each transaction
- Reconciling credit card and bank statements with physical receipts

## How It Works

1. **OCR Parsing**: Scans invoice slip PDFs/images and extracts:
   - Merchant name
   - Transaction date
   - Total amount
   - VAT amount
   - Payment method
   - Line items

2. **Fuzzy Matching**: Matches slips to bank transactions using:
   - **Amount matching** (primary, 50% weight) - Must match within tolerance
   - **Date matching** (30% weight) - Within configurable days
   - **Merchant name matching** (20% weight) - Fuzzy string matching
   - **Card digits** (bonus) - If available

3. **Excel Export**: Creates a comprehensive Excel file with:
   - Matched transactions (with confidence scores)
   - Unmatched slips (for manual review)
   - Unmatched transactions
   - Summary statistics

## Usage

### Basic Command

```bash
python main.py --match-slips --statements <statement1.pdf> <statement2.pdf> ...
```

### Examples

```bash
# Match slips in data/slips to credit card and personal account
python main.py --match-slips \
  --statements \
    "data/bank statements/PRIVATE_CLIENTS_CREDIT_CARD_033.pdf" \
    "data/bank statements/Michael/FNB_FUSION_PRIVATE_CLIENTS_ACC_193.pdf"

# Specify custom slips directory
python main.py --match-slips \
  --slips-dir "my_receipts" \
  --statements "statement.pdf"

# Specify custom output file
python main.py --match-slips \
  --statements "statement.pdf" \
  --output "my_matches.xlsx"
```

## Matching Configuration

The matcher can be configured in [transaction_matcher.py](src/transaction_matcher.py):

```python
matcher = TransactionMatcher(
    amount_tolerance=Decimal("1.00"),  # ±R1 tolerance for amounts
    date_tolerance_days=3,              # ±3 days for dates
    merchant_threshold=0.6              # 60% similarity for merchant names
)
```

## Output Format

The Excel file contains 4 sheets:

### 1. Matched
- Slip File
- Merchant
- Slip Date / Amount
- Transaction Date / Description / Amount
- Amount Difference
- Date Difference (days)
- Confidence Score
- Match Reason

### 2. Unmatched Slips
- Slip File
- Merchant / Date / Amount
- Payment Method
- Confidence
- **Manual Match** (fill in transaction index)
- **Notes** (for your comments)

### 3. Unmatched Transactions
- Index
- Date / Description / Amount
- Account Type
- Notes

### 4. Summary
- Total slips/transactions
- Match rate
- Confidence breakdown

## Supported Statement Formats

### FNB Credit Card
- Private Clients Credit Card statements
- Extracts: Date, Merchant, Location, Amount, Card digits

### FNB Personal Account
- Fusion Private Clients Account statements (English/Afrikaans)
- Extracts: Date, Description, Amount, Card digits

## OCR Requirements

For image-based PDFs (scanned slips), you need:

1. **Python packages** (already in requirements.txt):
   ```bash
   pip install pytesseract pillow pdf2image
   ```

2. **Tesseract OCR** (system dependency):
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
   - Linux: `apt-get install tesseract-ocr`

3. **Poppler** (for PDF to image conversion):
   - Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases
   - macOS: `brew install poppler`
   - Linux: `apt-get install poppler-utils`

**Note**: Many PDFs have text layers and don't require OCR. The system will try text extraction first, then fall back to OCR if needed.

## How to Improve Matching

### Low Match Rates?

1. **Check slip quality**: Ensure slips are readable
2. **Adjust matching parameters**: Loosen tolerances in [transaction_matcher.py](src/transaction_matcher.py)
3. **Add merchant patterns**: Add common merchant names to `merchant_patterns` in [invoice_slip_parser.py](src/invoice_slip_parser.py)
4. **Manual matching**: Use the "Unmatched Slips" sheet to manually link slips to transactions

### Adding Merchant Recognition

Edit [invoice_slip_parser.py](src/invoice_slip_parser.py) and add patterns:

```python
self.merchant_patterns = [
    r'(?i)(your_store_name)',
    r'(?i)(another\s*store)',
    # ... add more
]
```

## Future Integration with Finance System

The slip matching system is designed to integrate with the main finance splitting tool:

### Potential Use Cases

1. **Automatic Categorization**
   - Match slip line items to expense categories
   - Learn categorization patterns from past slips

2. **Shared vs Personal Classification**
   - Use slip details to determine if expense is shared or personal
   - E.g., restaurant slip for 2 people = shared, pharmacy = personal

3. **Receipt Verification**
   - Verify that claimed shared expenses have matching receipts
   - Flag unusual spending patterns

4. **Detailed Expense Breakdown**
   - Show what was purchased for each transaction
   - Track specific items (groceries, fuel, etc.)

### How to Integrate

The system can be extended in several ways:

1. **Add to PersonSheetImporter**: Automatically match slips when processing monthly sheets
2. **Enhanced Reports**: Include slip details in expense reports
3. **Category Prediction**: Use slip merchant/items to suggest expense categories
4. **Audit Trail**: Link each expense to its physical receipt

## File Structure

```
src/
├── invoice_slip_parser.py      # OCR and text extraction
├── transaction_matcher.py      # Matching logic and bank statement parsing
└── slip_matcher_exporter.py    # Excel export functionality

data/
├── slips/                      # Place invoice slips here
└── bank statements/            # Place bank statements here

output/                         # Matching results saved here
```

## Troubleshooting

### "Unable to get page count. Is poppler installed?"
- Install poppler (see OCR Requirements above)
- Or ensure your PDFs have text layers (not pure images)

### "No matches found"
- Check that dates are within tolerance (default ±3 days)
- Verify amounts match within ±R1
- Check merchant name spelling

### "Low confidence matches"
- Review the match in Excel
- Check the "Match Reason" column
- Adjust parameters if needed

## Command Reference

```bash
# Match slips
python main.py --match-slips --statements <pdf> [<pdf> ...]

# Options:
--slips-dir DIR          Directory containing slips (default: data/slips)
--statements PDF [PDF]   Bank statement PDFs (required)
--output FILE           Output Excel file (auto-generated if not specified)
```

## Example Workflow

1. **Collect slips**: Scan receipts to `data/slips/`
2. **Get statements**: Download bank statements to `data/bank statements/`
3. **Run matcher**:
   ```bash
   python main.py --match-slips --statements \
     "data/bank statements/CREDIT_CARD.pdf" \
     "data/bank statements/ACCOUNT.pdf"
   ```
4. **Review Excel**: Open the output file in Excel
5. **Manual matching**: Fill in "Manual Match" column for unmatched slips
6. **Categorize**: Use slip details to categorize expenses in your person sheets

## Tips

- Name your slips descriptively (e.g., `Woolworths_2025-09-14.pdf`)
- Keep slips organized by month
- Process statements monthly for best results
- Use the confidence scores to prioritize manual review
- Save the Excel files for record-keeping
