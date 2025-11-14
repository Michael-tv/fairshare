# FairShare Commands Reference

Quick reference for all available FairShare commands using UV.

## Command Format

```bash
uv run fairshare [command] [options]
```

## Main Workflow Commands

### Configuration & Setup

```bash
# Create config file (interactive)
uv run fairshare --create-config

# Initialize workspace directories
uv run fairshare --init-workspace

# Check workspace status
uv run fairshare --status
```

### Processing Pipeline

```bash
# 1. Validate month completeness
uv run fairshare --validate-months

# 2. Process bank statements (all users)
uv run fairshare --process-statements

# 2b. Process for specific user only
uv run fairshare --process-statements --user-dir Michael

# 2c. Force reprocess all months
uv run fairshare --process-statements --force

# 3. Calculate fair share
uv run fairshare --calculate-split

# 3b. Calculate from specific files
uv run fairshare --calculate-split person1.xlsx person2.xlsx
```

## Deferred Payments

```bash
# Add a deferred payment
uv run fairshare --add-deferred

# List all deferred payments
uv run fairshare --list-deferred

# Mark payment as paid
uv run fairshare --mark-paid <payment_id>
```

## Bank Statement Operations

```bash
# Parse and view bank statement
uv run fairshare --parse-bank-statement statement.pdf

# Export statement to Excel
uv run fairshare --export-bank-statement statement.pdf output.xlsx

# Match invoice slips to statements
uv run fairshare --match-slips

# Match slips with custom directory
uv run fairshare --match-slips --slips-dir path/to/slips
```

## Legacy Commands (Person Sheets)

```bash
# Create template spreadsheets
uv run fairshare --create-templates Person1 Person2

# Import from person sheets
uv run fairshare --person-sheets Person1_April.xlsx Person2_April.xlsx

# Auto-detect next month
uv run fairshare --next

# Checkpoint summary
uv run fairshare --checkpoint-summary
```

## Other Commands

```bash
# Run demo
uv run fairshare --demo

# Show tax calculation demo
uv run fairshare --tax

# Interactive mode
uv run fairshare --interactive

# Help
uv run fairshare --help
```

## UV Package Management

### Environment Management

```bash
# Install/update all dependencies
uv sync

# Install dependencies including dev
uv sync --dev

# Update all dependencies
uv sync --upgrade
```

### Package Operations

```bash
# Add a package
uv add package-name

# Add a dev package
uv add --dev package-name

# Remove a package
uv remove package-name

# List installed packages
uv pip list

# Show dependency tree
uv tree
```

### UV Maintenance

```bash
# Update UV itself
uv self update

# Clean cache
uv cache clean

# Lock dependencies
uv lock

# Lock with upgrade
uv lock --upgrade
```

## Traditional Python Commands (Still Work)

If you activate the virtual environment first:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Then use directly
fairshare --status
fairshare --process-statements
```

```bash
# macOS/Linux
source .venv/bin/activate

# Then use directly
fairshare --status
fairshare --process-statements
```

## Common Workflows

### First Time Setup

```bash
# 1. Install UV (one-time)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Setup project
uv sync

# 3. Configure FairShare
uv run fairshare --create-config
uv run fairshare --init-workspace

# 4. Check status
uv run fairshare --status
```

### Monthly Processing

```bash
# 1. Validate data
uv run fairshare --validate-months

# 2. Process statements
uv run fairshare --process-statements

# 3. Review/edit classifications in Excel
# (Open data/processed/transactions/*.xlsx)

# 4. Calculate split
uv run fairshare --calculate-split

# 5. Review output
# (Check data/processed/fair_share_calculation.xlsx)
```

### Privacy-Conscious Processing

```bash
# Process Michael's data only
uv run fairshare --process-statements --user-dir Michael

# (Michael reviews/edits data/processed/transactions/Michael.xlsx)

# Process Jacqui's data separately
uv run fairshare --process-statements --user-dir Jacqui

# (Jacqui reviews/edits data/processed/transactions/Jacqui.xlsx)

# Calculate combined split
uv run fairshare --calculate-split
```

### Reprocessing Everything

```bash
# Force reprocess all months
uv run fairshare --process-statements --force

# Recalculate split
uv run fairshare --calculate-split
```

## Environment Variables

Currently none used. Configuration is via `config.json`.

## Exit Codes

- `0`: Success
- `1`: Error (check error message)

## Tips

### Speed Up Repeated Commands

Instead of typing `uv run fairshare` every time:

**Option 1: Create alias (PowerShell)**
```powershell
function fs { uv run fairshare $args }
# Usage: fs --status
```

**Option 2: Activate environment**
```powershell
.venv\Scripts\Activate.ps1
fairshare --status  # No 'uv run' needed
```

**Option 3: Add to PATH (advanced)**
After activation, fairshare is on PATH.

### Combine Commands

```bash
# Validate and process in one go
uv run fairshare --validate-months && uv run fairshare --process-statements
```

### Redirect Output

```bash
# Save output to file
uv run fairshare --validate-months > validation.txt

# Save errors too
uv run fairshare --process-statements 2>&1 | tee process.log
```

## Troubleshooting Commands

```bash
# Check Python version
uv run python --version

# Verify imports work
uv run fairshare --status

# Check installed packages
uv pip list

# Reinstall dependencies
uv sync --reinstall

# Clean and reinstall
uv cache clean && uv sync
```

## Getting Help

```bash
# General help
uv run fairshare --help

# UV help
uv --help

# Specific command help
uv sync --help
uv add --help
```

## Documentation

- **UV Setup**: [UV_SETUP.md](UV_SETUP.md)
- **CLI Updates**: [FAIRSHARE_CLI_UPDATES.md](FAIRSHARE_CLI_UPDATES.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Month Validation**: [MONTH_VALIDATION_GUIDE.md](MONTH_VALIDATION_GUIDE.md)
- **Deferred Payments**: [DEFERRED_PAYMENTS_GUIDE.md](DEFERRED_PAYMENTS_GUIDE.md)

## Quick Reference Card

| Task | Command |
|------|---------|
| **Setup** | |
| Install deps | `uv sync` |
| Create config | `uv run fairshare --create-config` |
| Init workspace | `uv run fairshare --init-workspace` |
| **Processing** | |
| Validate months | `uv run fairshare --validate-months` |
| Process statements | `uv run fairshare --process-statements` |
| Process one user | `uv run fairshare --process-statements --user-dir NAME` |
| Calculate split | `uv run fairshare --calculate-split` |
| **Utilities** | |
| Status | `uv run fairshare --status` |
| Parse statement | `uv run fairshare --parse-bank-statement file.pdf` |
| Match slips | `uv run fairshare --match-slips` |
| **Package Management** | |
| Update deps | `uv sync --upgrade` |
| Add package | `uv add package-name` |
| Update UV | `uv self update` |

---

*For detailed information, see [UV_SETUP.md](UV_SETUP.md)*
