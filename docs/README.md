# Home Finance Splitting System

A comprehensive Python-based system for processing bank statements, classifying transactions, and fairly splitting household financial obligations between partners based on proportional income.

## Features

### Transaction Processing
- **Automated Bank Statement Parsing**: Extract transactions from FNB PDF statements (Fusion, Credit Card, Personal accounts)
- **Smart Classification**: AI-powered transaction categorization with machine learning
- **Learned Rules**: System learns from your corrections to improve accuracy over time
- **Monthly Organization**: Transactions organized by month for easy management
- **Custom Categories**: Add your own expense categories without editing code
- **Slip Matching**: Match invoice slips to bank transactions automatically

### Financial Splitting
- **Fair Splitting**: Calculates proportional splits based on net or gross income
- **Tax Calculator**: Accurate South African PAYE tax calculations (2024/2025 tax year)
- **Multiple Reports**: Summary reports, expense breakdowns, category analysis
- **Scenario Planning**: Compare different income/expense scenarios
- **Transparent Logic**: Clear, documented calculations

## Installation

### Using uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# The project will auto-install dependencies when you run commands
uv run fairshare --help
```

### Using pip
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Initial Setup

```bash
# Create configuration file
uv run fairshare --create-config

# Initialize workspace structure
uv run fairshare --init-workspace
```

### 2. Add Bank Statements

Place your FNB bank statement PDFs in the appropriate folders:
```
data/raw/statements/
├── Michael/           # Person 1's statements
│   ├── statement_may_2024.pdf
│   └── statement_june_2024.pdf
├── Jacqui/           # Person 2's statements
│   └── statement_may_2024.pdf
└── shared/           # Shared account statements
    └── credit_card/
        └── statement_may_2024.pdf
```

### 3. Process Statements

```bash
# Process all bank statements
uv run fairshare --process-statements

# This will:
# - Parse all PDF statements
# - Extract transactions
# - Auto-classify by category and type
# - Organize by month into Excel files
```

### 4. Review and Correct Classifications

Open the generated Excel files in `data/processed/transactions/`:
- `Michael/2024-05/michael_classified.xlsx`
- `shared_credit_card/2024-05/credit_card_classified.xlsx`

Columns:
- `auto_category`: System's classification (e.g., GROCERIES, FUEL)
- `user_category`: **Edit this** to correct wrong classifications
- `auto_type`: HOUSEHOLD (shared) or INDIVIDUAL (personal)
- `user_type`: **Edit this** to override

### 5. Learn from Your Corrections

```bash
# System learns from your corrections
uv run fairshare --learn-from-corrections

# Apply learned rules to all existing files
uv run fairshare --apply-learned-rules
```

## Key Commands

### Transaction Processing
```bash
# Process new bank statements
uv run fairshare --process-statements

# Force reprocess everything
uv run fairshare --process-statements --force

# Learn from corrections
uv run fairshare --learn-from-corrections

# Apply learned rules to existing files
uv run fairshare --apply-learned-rules

# Show learned rules statistics
uv run fairshare --show-learned-stats

# Export learned rules to Excel
uv run fairshare --export-learned-rules learned_rules.xlsx
```

### Category Management
```bash
# List all categories
uv run fairshare --list-categories

# Add custom category
uv run fairshare --add-category DISCRETIONARY_DINING "Discretionary Dining"

# Remove category
uv run fairshare --remove-category OLD_CATEGORY

# Rename category
uv run fairshare --rename-category OLD_KEY NEW_KEY "New Display Name"
```

### Financial Splitting (Coming Soon)
```bash
# Calculate monthly split
uv run fairshare --calculate-split

# View checkpoint summary
uv run fairshare --checkpoint-summary
```

## Project Structure

```
home_finances/
├── src/
│   ├── models.py                    # Data models
│   ├── transaction_processor.py     # Main processing pipeline
│   ├── transaction_classifier.py    # Auto-classification logic
│   ├── learned_classifier.py        # ML-based learning system
│   ├── category_manager.py          # Dynamic category management
│   ├── bank_statement_parser.py     # PDF parsing
│   ├── month_validator.py           # Statement completeness checking
│   └── workspace_manager.py         # File organization
├── data/
│   ├── raw/
│   │   └── statements/              # Bank statement PDFs
│   └── processed/
│       ├── transactions/            # Organized by person/month
│       ├── learned_rules.json       # Learned classification rules
│       └── categories.json          # Custom categories
├── docs/                            # Documentation
├── fairshare.py                     # Main CLI interface
└── README.md                        # This file
```

## How Transaction Classification Works

### 1. Auto-Classification
The system uses two methods:
1. **Keyword Patterns**: Matches merchant names (e.g., "Woolworths" → GROCERIES)
2. **Learned Rules**: Uses your past corrections with fuzzy matching

Priority: Learned rules > Keyword patterns

### 2. Learning from Corrections
When you correct a classification:
```
1. Open classified Excel file
2. Edit user_category or user_type columns
3. Run: uv run fairshare --learn-from-corrections
4. System saves the rule and applies fuzzy matching
```

Example:
- You correct "Lucky Castle Erasmuskloof" → DISCRETIONARY_DINING
- System learns and will also match:
  - "Lucky Castle Waterkloof" (different location)
  - "lucky castle" (case insensitive)
  - "Lucky Castel" (typo tolerance)

### 3. Monthly File Organization

Transactions are organized by month:
```
data/processed/transactions/
├── Michael/
│   ├── 2024-05/
│   │   ├── michael_raw_extracted.xlsx    # Raw data
│   │   └── michael_classified.xlsx       # With classifications
│   └── 2024-06/
│       └── ...
└── shared_credit_card/
    └── 2024-05/
        └── credit_card_classified.xlsx
```

Benefits:
- Easy to review specific months
- Selective reprocessing
- Better organization

## Custom Categories

### Add New Category
```bash
uv run fairshare --add-category DISCRETIONARY_DINING "Discretionary Dining"
```

Categories are stored in `data/processed/categories.json` and can be:
- Added dynamically without code changes
- Used immediately in classifications
- Renamed or removed as needed

## Learned Classification System

The system learns from your corrections and gets smarter over time:

### Features
- **Fuzzy Matching**: Handles variations, typos, and case differences
- **Confidence Scoring**: Tracks how often each rule is used
- **Count Tracking**: Shows which rules are most common
- **Easy Export**: Export rules to Excel for review

### Workflow
```bash
# 1. Process statements (initial auto-classification)
uv run fairshare --process-statements

# 2. Review and correct in Excel files

# 3. Learn from corrections
uv run fairshare --learn-from-corrections

# 4. New statements will use learned rules automatically
uv run fairshare --process-statements

# 5. Apply rules to old files (optional)
uv run fairshare --apply-learned-rules
```

## Testing

Run unit tests:
```bash
python -m pytest tests/
```

Or with unittest:
```bash
python -m unittest tests.test_calculations
```

## Configuration

The `config.yaml` file contains:
- Person names
- Shared account names
- Working directory
- Processing options

Example:
```yaml
persons:
  - name: Michael
  - name: Jacqui

shared_accounts:
  - name: credit_card
    display_name: Shared Credit Card

working_dir: c:/projects/home_finances
```

## Documentation

- [BANK_STATEMENT_GUIDE.md](BANK_STATEMENT_GUIDE.md) - Bank statement processing guide
- [LEARNED_CLASSIFICATION_GUIDE.md](LEARNED_CLASSIFICATION_GUIDE.md) - Learning system details
- [CLAUDE.md](../CLAUDE.md) - Developer guide for AI assistance

## Tax Information

The system uses South African PAYE tax rates for the 2024/2025 tax year:

| Annual Income | Tax Rate |
|---------------|----------|
| R0 - R237,100 | 18% |
| R237,100 - R370,500 | 26% |
| R370,500 - R512,800 | 31% |
| R512,800 - R673,000 | 36% |
| R673,000 - R857,900 | 39% |
| R857,900 - R1,817,000 | 41% |
| R1,817,000+ | 45% |

Primary rebate: R17,235

UIF: 1% of income (capped at R177.12 per month)

## Future Enhancements

Completed:
- ✅ Bank statement parsing (FNB PDF support)
- ✅ Transaction classification
- ✅ Machine learning from corrections
- ✅ Monthly organization
- ✅ Custom categories

Planned:
- [ ] Financial split calculations (in progress)
- [ ] Streamlit web dashboard
- [ ] Additional bank support (Standard Bank, Capitec)
- [ ] Budget vs. actual analysis
- [ ] PDF report export

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - Use freely for personal or commercial purposes.

## Support

For issues or questions, please create an issue in the repository.
