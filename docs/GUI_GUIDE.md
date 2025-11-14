# FairShare GUI Guide

A user-friendly PyQt5 graphical interface for the FairShare household finance splitting system.

## Installation

This project uses `uv` for dependency management. Make sure you have uv installed.

### Quick Start

**Windows:**
- Double-click `run_gui.bat`
- OR open Command Prompt and run: `uv run gui_main.py`

**macOS/Linux:**
- Run: `./run_gui.sh` (make executable first: `chmod +x run_gui.sh`)
- OR run directly: `uv run gui_main.py`

### Manual Installation

If you need to install dependencies manually:
```
uv pip install -r requirements.txt
```

## Interface Overview

The FairShare GUI consists of 4 main tabs:

### 1. Home Tab

**Purpose:** Dashboard with quick actions and current status

**Features:**
- View current cumulative balance
- See latest month summary
- Quick access buttons to all features
- "Process Next Month" button for automatic file detection
- Getting started guide

**Typical Use:**
- Check current balance status
- Quick navigation to other features
- Process the next month automatically after setting up the first month

---

### 2. Process Month Tab

**Purpose:** Import Excel files and calculate fair share splits

**Features:**
- File pickers for Person 1 and Person 2 Excel sheets
- NET/GROSS income mode selector
- Calculate button to perform the split
- Results display with summary report
- View detailed breakdown and category summary buttons

**Typical Use:**
1. Click "Browse..." to select each person's Excel file
2. Choose income mode:
   - **NET Mode (Default):** Income values are take-home pay
   - **GROSS Mode:** System calculates tax from gross salary
3. Click "Calculate Fair Share Split"
4. Review results showing:
   - Income proportions
   - Total shared expenses
   - Who owes whom
5. Use "View Detailed Breakdown" for expense-by-expense details
6. Use "View Category Summary" for spending by category

**Income Modes Explained:**
- **NET Mode:** Use this if you enter your actual take-home pay (after tax). No tax calculation needed.
- **GROSS Mode:** Use this if you enter your gross salary. The system will calculate South African PAYE tax and UIF.

---

### 3. History Tab

**Purpose:** View all processed months and cumulative totals

**Features:**
- Cumulative summary showing total transfers
- Table of all processed months with details
- Export to CSV functionality
- View raw checkpoint file
- Clear history option (with confirmation)

**Typical Use:**
- Review past months
- Check cumulative balance
- Export data for analysis
- Clear history to start fresh

**Table Columns:**
- **Month:** Period processed (YYYY-MM)
- **Person 1/2 Net:** Net income for each person
- **Total Shared:** Total shared expenses for the month
- **Person 1/2 Paid:** Amount each person paid
- **Transfer Amount:** How much needs to be transferred
- **Transfer Direction:** Who pays whom

---

### 4. Create Templates Tab

**Purpose:** Generate Excel templates for new people or months

**Features:**
- Input fields for both person names
- Output directory selector
- Template creation with automatic naming
- Instructions and next steps
- Option to open the folder after creation

**Typical Use:**
1. Enter names for both people (e.g., "Michael" and "Jacqui")
2. Choose where to save the templates
3. Click "Create Templates"
4. Rename templates to include month/year (e.g., `Michael_January_2024.xlsx`)
5. Fill in income and expenses
6. Return to "Process Month" tab to calculate

**Template Structure:**
Each template has two sheets:

**Income Sheet:**
| Description | Amount | Type |
|-------------|--------|------|
| Monthly Salary | 70000.00 | Salary |
| Rental Income | 8500.00 | Rental |

**Expenses Sheet:**
| Description | Amount | Category | Type |
|-------------|--------|----------|------|
| Groceries | 3500.00 | Groceries | Household |
| My Car Payment | 5000.00 | Loans | Personal |

**Important:** The **Type** column in the Expenses sheet determines if an expense is split:
- **Household/Shared:** Split proportionally between partners
- **Personal/Individual:** Not split (belongs to one person only)

---

## Common Workflows

### First Time Setup

1. **Create Templates:**
   - Go to "Create Templates" tab
   - Enter both person names
   - Generate templates
   - Save them with month/year in filename

2. **Fill Templates:**
   - Open Excel files
   - Add income sources to Income sheet
   - Add expenses to Expenses sheet
   - Mark expenses as "Household" or "Personal"

3. **Process First Month:**
   - Go to "Process Month" tab
   - Select both Excel files
   - Choose NET or GROSS mode
   - Calculate split
   - Review results

4. **Check Results:**
   - View summary in results area
   - Check detailed breakdown
   - Review category spending
   - Note who owes whom

### Monthly Processing (After First Month)

1. **Automatic Method:**
   - Fill in next month's Excel files
   - Name them with next month (e.g., `Name_February_2024.xlsx`)
   - Go to "Home" tab
   - Click "Process Next Month (Auto-detect)"
   - Confirm file selection
   - Calculate split

2. **Manual Method:**
   - Go to "Process Month" tab
   - Select files manually
   - Calculate split

### Reviewing History

1. Go to "History" tab
2. View cumulative summary at top
3. Browse monthly table for details
4. Export to CSV for analysis in Excel
5. Use "View Raw Checkpoint File" to see JSON data

---

## Tips & Best Practices

### File Naming
- Use consistent naming: `PersonName_Month_Year.xlsx`
- Examples: `Michael_January_2024.xlsx`, `Jacqui_Feb_2024.xlsx`
- Consistent naming enables auto-detection feature

### Expense Classification
- **Household expenses:** Rent/bond, utilities, groceries, joint activities
- **Personal expenses:** Individual car payments, personal shopping, hobbies
- When in doubt, mark as Household for fair splitting

### Income Entry
- **NET mode:** Enter your take-home pay (easier, recommended for most)
- **GROSS mode:** Enter pre-tax salary (system calculates tax)
- Be consistent within a month (both people use same mode)

### Regular Processing
- Process each month shortly after it ends
- Don't skip months (creates gaps in history)
- Keep Excel files organized in a dedicated folder

### Backups
- The `financial_checkpoint.json` file contains all history
- Back it up regularly
- Export history to CSV periodically

### Troubleshooting
- **File not found:** Check file paths and spelling
- **Calculation errors:** Verify Excel sheet structure matches template
- **Month already processed:** History prevents duplicates (clear if reprocessing needed)

---

## Keyboard Shortcuts

- **Tab:** Navigate between fields
- **Enter:** Activate focused button
- **Ctrl+Tab:** Switch between tabs
- **Alt+F4:** Close application (Windows)
- **Cmd+Q:** Close application (macOS)

---

## Technical Details

### Data Storage
- **Location:** `financial_checkpoint.json` in working directory
- **Format:** JSON with monthly data and cumulative totals
- **Persistence:** All history preserved across sessions

### Calculation Method
1. Calculate net income for each person
2. Determine proportion: `person1_ratio = person1_net / (person1_net + person2_net)`
3. Calculate fair share: `person1_should_pay = total_shared * person1_ratio`
4. Compare to actual: `person1_balance = person1_paid - person1_should_pay`
5. Settlement: If balance is negative, person owes money; if positive, they should receive money

### Thread Safety
- Calculations run in background thread
- UI remains responsive during processing
- Progress updates shown in real-time

---

## Frequently Asked Questions

**Q: Can I edit a previously processed month?**
A: Currently, you need to clear history and reprocess. Future versions may support editing.

**Q: What happens if I process the same month twice?**
A: The checkpoint system prevents duplicates by default. Clear history first if you need to reprocess.

**Q: Can I use this for more than 2 people?**
A: The current version supports exactly 2 people. Contact the developers for multi-person support.

**Q: What if we have shared and individual accounts?**
A: All shared expenses go in the Household type, individual expenses in Personal type. The system handles the rest.

**Q: How accurate is the tax calculation?**
A: Uses official South African PAYE brackets for 2024/2025. Update [tax_calculator.py](../src/tax_calculator.py) for new tax years.

**Q: Can I export to PDF?**
A: Not built-in yet. Export to text file and convert externally, or use CSV for data analysis.

**Q: Does this work on macOS/Linux?**
A: Yes! PyQt5 is cross-platform. The interface works on Windows, macOS, and Linux.

---

## Support & Feedback

For issues, feature requests, or contributions, please see the main project README or contact the development team.

Enjoy fair and stress-free expense splitting with FairShare!
