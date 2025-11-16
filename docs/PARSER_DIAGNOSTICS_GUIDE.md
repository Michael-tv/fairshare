# Parser Diagnostics & Template Validation Guide

## Overview

Two new tabs have been added to the FairShare GUI to help troubleshoot and improve the reliability of bank statement parsing:

1. **Template Validation** - Validates bank statement templates before use
2. **Parser Diagnostics** - Monitors parsing operations and provides detailed logs

These tools address the common issues with transaction parsing:
- Missing transactions
- Incorrect Credit/Debit classification
- Silent parsing failures
- Difficult-to-debug template configurations

---

## Template Validation Tab

### Purpose
Validates YAML bank statement templates to catch configuration errors **before** they cause parsing failures.

### Features

#### ✅ Comprehensive Validation Checks

**Critical Errors (must fix):**
- Missing required fields (`bank_name`, `account_type`)
- Missing or invalid `transaction_pattern`
- Invalid regex syntax
- Missing required regex groups (`day`, `month`, `description`, `amount`)

**Warnings (should fix):**
- No auto-detection configuration
- No credit indicator (can't determine Credit vs Debit)
- Missing section markers (may parse entire document)
- Missing date or amount configuration

**Informational (optional improvements):**
- Missing country code
- Only one detection marker (add more for reliability)
- Missing summary extraction patterns
- Missing recommended fields for balance validation

#### 📊 Scoring System

Each template gets a confidence score (0-100):
- **Errors**: -20 points each
- **Warnings**: -5 points each
- **Info issues**: -1 point each

**Score Interpretation:**
- **90-100**: Excellent - template is well-configured
- **70-89**: Good - minor issues to address
- **50-69**: Fair - important issues that should be fixed
- **Below 50**: Poor - critical issues, likely to cause parsing failures

### How to Use

#### Validate a Single Template

1. Open the **Template Validation** tab
2. Select a template from the list (e.g., `fnb_credit_card`)
3. Click **"Validate Selected"** or double-click the template
4. Review the results:
   - Summary shows status, score, and issue counts
   - Detailed report shows all issues with suggestions

#### Validate All Templates

1. Click **"Validate All"** button
2. Wait for batch validation to complete
3. Review combined report showing:
   - List of valid templates
   - List of invalid templates
   - Detailed reports for each

#### Export Validation Report

1. After validating, click **"Export Report"**
2. Choose a location to save the `.txt` file
3. Use the report to:
   - Share with team members
   - Document template improvements
   - Track template quality over time

### Example Validation Output

```
================================================================================
TEMPLATE VALIDATION REPORT: fnb_credit_card
================================================================================

Overall Status: ✓ VALID
Confidence Score: 95.0/100
Total Issues: 1 (0 errors, 0 warnings, 1 info)

INFORMATION (optional improvements):
--------------------------------------------------------------------------------
ℹ️  [INFO] detection.markers: Only one detection marker - consider adding more for reliability
   💡 Suggestion: Add 2-3 unique markers from the PDF for better detection

================================================================================
```

### Common Issues and Solutions

#### Issue: "Missing required regex groups"

**Problem:**
```yaml
transaction_pattern: '(\d{2})\s+(\w{3})\s+(.+?)\s+([\d,.]+)'
```
Uses numbered groups instead of named groups.

**Solution:**
```yaml
transaction_pattern: '(?P<day>\d{2})\s+(?P<month>\w{3})\s+(?P<description>.+?)\s+(?P<amount>[\d,.]+)'
```
Use named groups: `(?P<day>...)`, `(?P<month>...)`, etc.

#### Issue: "No credit_indicator configuration"

**Problem:** Can't determine if transaction is Credit or Debit.

**Solution:**
```yaml
parsing:
  amount:
    credit_indicator:
      group: "credit"
      value: "Cr"
      debit_value: "Dr"
```

---

## Parser Diagnostics Tab

### Purpose
Monitors bank statement parsing in real-time and provides detailed diagnostics to troubleshoot parsing issues.

### Features

#### 📈 Real-Time Statistics

**Line Processing:**
- Total lines in PDF
- Lines in transaction section
- Lines matching pattern (with match rate %)
- Lines skipped (with reasons)

**Transaction Results:**
- Transactions created
- Transactions failed
- Success rate
- Credit vs Debit breakdown
- Total amounts

**Balance Validation:**
- Opening balance vs calculated
- Closing balance comparison
- Difference detection
- Warnings for mismatches

#### 📝 Detailed Logging

**Log Levels:**
- **DEBUG**: Low-level parsing details
- **INFO**: General parsing progress
- **WARNING**: Potential issues
- **ERROR**: Parsing failures

**Color-Coded Display:**
- 🔴 Red: Errors
- 🟡 Yellow: Warnings
- 🔵 Blue: Info
- ⚪ Gray: Debug

#### 🔍 Failed Lines Analysis

Table view of all lines that:
- Matched the regex pattern
- But failed to create transactions

Includes:
- Line number
- Line text
- Skip reason
- Error message

#### 📄 Unmatched Lines View

Shows lines that didn't match the transaction pattern.

**Use Cases:**
- Verify section markers are working
- Check if pattern is too strict
- Identify transaction format variations
- Detect lines that should be transactions but aren't

### How to Use

#### Monitor Active Parsing

1. Open the **Parser Diagnostics** tab
2. Check **"Auto-refresh"** (enabled by default)
3. Process a statement from the **Process Statements** tab
4. Switch back to **Parser Diagnostics** to see:
   - Real-time statistics
   - Log messages as they occur
   - Failed lines
   - Unmatched lines

#### Investigate Parsing Issues

**Scenario: Missing Transactions**

1. Check **Statistics** tab:
   - How many lines were in the section?
   - What's the match rate?
   - What's the success rate?

2. Check **Unmatched Lines** tab:
   - Are transaction lines being skipped?
   - Do they look different from expected pattern?

3. Check **Failed Lines** tab:
   - Which lines matched but failed?
   - What are the skip reasons?

4. Check **Logs** tab:
   - Filter to show WARNING and ERROR
   - Look for parsing errors

**Scenario: Wrong Credit/Debit Classification**

1. Check **Logs** tab for:
   - "No credit_indicator configured"
   - "Unknown indicator"
   - Warnings about indicator values

2. Review template's `credit_indicator` configuration

3. Check **Statistics** tab:
   - Do Credit/Debit counts match statement summary?
   - Are amounts correct?

#### Export Diagnostic Report

1. After parsing, click **"Export Report"**
2. Save the complete diagnostic report including:
   - Full statistics
   - All failed lines
   - Sample of unmatched lines
   - Complete log history

3. Use report to:
   - Debug template issues
   - Report bugs
   - Document parsing behavior

### Settings

#### Log Level
- **DEBUG**: Verbose - every parsing operation
- **INFO**: Normal - important events only
- **WARNING**: Minimal - warnings and errors only
- **ERROR**: Critical - errors only

**Recommendation:** Use INFO for normal operation, DEBUG for troubleshooting.

#### Auto-Refresh
- **Enabled**: Updates display every 2 seconds
- **Disabled**: Manual refresh only

**Recommendation:** Keep enabled when actively monitoring, disable for performance.

#### Max Sessions to Keep
Control how many parsing sessions are stored in memory.

**Recommendation:** Keep at 10 unless investigating specific issues.

---

## Workflow for Troubleshooting Parsing Issues

### Step 1: Validate Template

1. Go to **Template Validation** tab
2. Validate the template being used
3. Fix any errors or warnings found
4. Re-validate to confirm fixes

### Step 2: Test Parsing with Diagnostics

1. Enable **Parser Diagnostics** tab
2. Clear previous sessions (optional)
3. Parse a test statement
4. Review diagnostics immediately

### Step 3: Analyze Results

#### If transactions are missing:

**Check Unmatched Lines:**
- Are transaction lines showing up here?
- Do they match the expected format?

**Action:** Update `transaction_pattern` in template

**Check Section Markers:**
- Did parser find the transaction section?
- Check logs for "In section" messages

**Action:** Update `sections.start_markers` in template

#### If Credit/Debit is wrong:

**Check Logs:**
- Look for credit indicator warnings
- Check what indicator values are found

**Action:** Update `amount.credit_indicator` in template

**Check Statistics:**
- Compare Credit/Debit totals with statement
- Look for mismatches

**Action:** Verify indicator configuration and test

#### If amounts are wrong:

**Check Failed Lines:**
- Look at skip reasons
- Check for amount parsing errors

**Action:** Update amount parsing configuration

### Step 4: Iterate and Test

1. Make template changes
2. Re-validate template
3. Re-parse statement
4. Compare diagnostics
5. Repeat until issues resolved

### Step 5: Document and Share

1. Export validation report
2. Export diagnostics report
3. Document changes made
4. Share successful template configuration

---

## Best Practices

### For Template Developers

1. **Always validate before using** - Run Template Validation first
2. **Start with high-quality examples** - Use existing working templates as reference
3. **Test incrementally** - Make one change at a time
4. **Use diagnostics actively** - Monitor first few parses closely
5. **Document your patterns** - Add comments to template explaining decisions

### For Template Users

1. **Check validation regularly** - Re-validate after template updates
2. **Monitor first use** - Watch diagnostics for new bank statements
3. **Report issues** - Export diagnostics when reporting problems
4. **Keep templates updated** - Bank formats change over time

### For Debugging

1. **Enable DEBUG logging** - When investigating specific issues
2. **Compare multiple statements** - Test template with 2-3 different statements
3. **Check balance validation** - Ensure totals match statement
4. **Review failed lines** - Understand why parsing failed
5. **Export full reports** - Document issues for later analysis

---

## Technical Details

### Template Validation Architecture

**Validation Checks:**
1. YAML syntax and structure
2. Required fields presence
3. Regex pattern compilation
4. Named groups validation
5. Configuration consistency
6. Best practices compliance

**Validation Engine:**
- `src/template_validator.py` - Validation logic
- `src/gui/template_validation_tab.py` - GUI interface

### Parser Diagnostics Architecture

**Components:**
1. **Logging Handler** - Captures log messages
2. **Statistics Collector** - Tracks parsing metrics
3. **Line Attempt Recorder** - Records each parse attempt
4. **Session Manager** - Organizes diagnostic data

**Data Flow:**
```
BankStatementParser
  ↓ (logs)
DiagnosticsCollector
  ↓ (captures)
ParsingSession
  ↓ (displays)
ParserDiagnosticsTab
```

**Implementation:**
- `src/parser_diagnostics.py` - Diagnostics infrastructure
- `src/gui/parser_diagnostics_tab.py` - GUI interface

---

## Future Enhancements

### Planned Features

1. **Template Testing Tool**
   - Test templates against sample PDFs
   - Visual pattern builder
   - Interactive regex tester

2. **Automatic Issue Detection**
   - AI-powered template recommendations
   - Pattern anomaly detection
   - Automatic template updates

3. **Performance Metrics**
   - Parsing speed tracking
   - Template efficiency comparison
   - Optimization suggestions

4. **Enhanced Reporting**
   - PDF reports with charts
   - Email notifications for failures
   - Dashboard summaries

---

## Troubleshooting the Tools Themselves

### Template Validation Tab Not Loading

**Error:** Import error for `template_validator`

**Solution:**
```bash
# Verify file exists
ls src/template_validator.py

# Check for syntax errors
python -m py_compile src/template_validator.py
```

### Parser Diagnostics Not Showing Data

**Problem:** Auto-refresh not working

**Solution:**
1. Check "Auto-refresh" checkbox is enabled
2. Click "Refresh Now" manually
3. Verify parsing is actually happening

**Problem:** No sessions shown

**Solution:**
- Parse a statement first
- Sessions are created during parsing
- Check logs for any errors

### Export Functions Failing

**Problem:** Permission errors

**Solution:**
- Choose a writable directory
- Check disk space
- Verify file isn't open elsewhere

---

## Support

For issues or questions:
1. Check validation/diagnostic reports
2. Review template documentation in `docs/BANK_TEMPLATES.md`
3. Export and save diagnostic data
4. Create issue with exported reports attached

---

**Last Updated:** 2025-11-16
**Version:** 1.0
