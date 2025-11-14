# FairShare GUI Troubleshooting Guide

This guide helps resolve common issues when using the FairShare GUI.

## Installation Issues

### Error: "ModuleNotFoundError: No module named 'PyQt5'"

**Solution:**
```cmd
uv sync
```

Or install manually:
```cmd
uv pip install PyQt5
```

### Error: "uv is not installed or not in PATH"

**Solution:**
Install uv first:

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your terminal/command prompt.

## Import Errors

### Error: "attempted relative import beyond top-level package"

This error was fixed in the latest version. Make sure you have the updated GUI files with absolute imports.

**Solution:**
Re-download or update your GUI files. All imports should be like:
- `from checkpoint_manager import CheckpointManager` (not `from ..checkpoint_manager`)
- `from gui.home_tab import HomeTab` (not `from .home_tab`)

### Error: "CheckpointManager object has no attribute 'checkpoint_data'"

This error was fixed. The GUI now uses `checkpoint_manager.data` instead of `checkpoint_manager.checkpoint_data`.

**Solution:**
Make sure you have the latest version of the GUI files.

## Runtime Errors

### Error: "No module named 'person_sheet_importer'"

**Cause:** Python can't find the src modules.

**Solution:**
The `gui_main.py` script should automatically add the `src` directory to the Python path. If this fails, try:

```cmd
# From the project root directory
set PYTHONPATH=c:\projects\home_finances\src
uv run gui_main.py
```

Or use absolute paths in imports.

### GUI Window Doesn't Appear

**Possible Causes:**
1. Display/graphics driver issues
2. Qt platform plugin issues
3. Running in headless environment

**Solutions:**

**Try different Qt platform:**
```cmd
set QT_QPA_PLATFORM=windows
uv run gui_main.py
```

**Check if running in remote/headless:**
The GUI requires a display. It won't work over SSH without X11 forwarding.

**Update graphics drivers:**
Ensure your graphics drivers are up to date.

### GUI Crashes on Startup

**Check Python version:**
```cmd
python --version
```
Requires Python 3.7 or higher.

**Check PyQt5 installation:**
```cmd
python -c "from PyQt5 import QtWidgets; print('PyQt5 OK')"
```

**Try running with verbose errors:**
```cmd
uv run python -v gui_main.py
```

## Functional Issues

### "Process Next Month" Button Disabled

**Cause:** No months processed yet, or next month's files not found.

**Solution:**
1. Process your first month manually via "Process Month" tab
2. Ensure next month's files follow naming convention: `PersonName_Month_Year.xlsx`
3. Files must exist in the same directory as previous month

### Calculation Errors

**Error: "File not found" or "Invalid file format"**

**Solution:**
- Ensure Excel files exist at the specified paths
- Check file names are spelled correctly
- Verify files have the correct structure (Income and Expenses sheets)
- Try opening files in Excel to ensure they're not corrupted

**Error: "No shared expenses found"**

**Cause:** All expenses marked as "Personal/Individual" instead of "Household/Shared"

**Solution:**
- Open Excel files
- In Expenses sheet, check the "Type" column
- Change relevant expenses to "Household" or "Shared"

### History Tab Shows No Data

**Cause:** No checkpoint file exists yet.

**Solution:**
Process at least one month first using the "Process Month" tab.

### Export to CSV Fails

**Possible Causes:**
1. No write permission in selected directory
2. File is open in another program
3. Invalid file path

**Solution:**
- Choose a different directory with write permissions
- Close the CSV file if it's open in Excel
- Use a simple filename without special characters

## Performance Issues

### GUI Slow to Open

**Cause:** Loading large checkpoint file or many months of data.

**Solution:**
This is normal for many months of data. The GUI should still be responsive once loaded.

### Calculation Takes Too Long

**Normal behavior:** Calculations run in background thread and should complete within seconds.

**If stuck:**
- Check Excel files aren't extremely large
- Look for circular references in Excel formulas
- Restart the GUI and try again

### GUI Freezes

**If frozen during calculation:**
- This shouldn't happen (calculations are threaded)
- Force close and restart
- Check Excel files for issues

**If frozen on startup:**
- Check checkpoint file isn't corrupted
- Try renaming `financial_checkpoint.json` to backup and restart
- The GUI will create a new empty checkpoint

## Data Issues

### Wrong Results / Unexpected Amounts

**Check:**
1. Income values are entered correctly
2. Expense types (Household vs Personal) are correct
3. NET vs GROSS mode matches your data
4. All amounts are positive numbers (no negatives)

**Verify:**
- Compare with CLI results: `uv run fairshare --person-sheets File1.xlsx File2.xlsx`
- Check the detailed breakdown for specific issues
- Review category summary for unexpected expenses

### Duplicate Month Error

**Cause:** Trying to process a month that's already in the checkpoint.

**Solution:**
1. View history to confirm the month is already processed
2. Either skip it or clear history and reprocess all months
3. Use different file names if testing

### Cumulative Balance Seems Wrong

**Check:**
1. All months processed in correct order
2. No months skipped
3. Review history tab for each month's transfers
4. Verify cumulative calculation manually if needed

## Display Issues

### Text Overlapping or Truncated

**Cause:** High DPI display scaling issues.

**Solution:**
Windows:
- Right-click `run_gui.bat` → Properties → Compatibility
- Check "Override high DPI scaling behavior"
- Set to "Application"

Or adjust Windows display scaling settings.

### Tables Not Displaying Correctly

**Solution:**
- Resize window to trigger layout refresh
- Switch to another tab and back
- Click "Refresh" button if available

### Fonts Look Wrong

**Cause:** System font settings.

**Solution:**
The GUI uses "Segoe UI" on Windows. If unavailable, it falls back to system default. This is usually fine.

## File System Issues

### Can't Find Excel Files in File Picker

**Solution:**
- Ensure files have `.xlsx` or `.xls` extension
- Use "All Files (*.*)" filter option if needed
- Navigate to correct directory
- Files might be in OneDrive/cloud storage (check sync status)

### Template Creation Fails

**Possible Causes:**
1. No write permission in selected directory
2. Disk full
3. File name conflict

**Solution:**
- Choose a different directory
- Check disk space
- Delete or rename existing template files

### Checkpoint File Location

**Default location:** Same directory as `gui_main.py`

**To use different location:**
Currently not supported in GUI. Would need to modify `CheckpointManager` initialization.

## Platform-Specific Issues

### Windows

**Issue:** Double-clicking `run_gui.bat` flashes and closes immediately

**Solution:**
1. Right-click `run_gui.bat` → Edit
2. Check the batch file contents
3. Run from Command Prompt to see errors:
   ```cmd
   cd c:\projects\home_finances
   run_gui.bat
   ```

**Issue:** "Windows protected your PC" message

**Solution:**
Click "More info" → "Run anyway"
(The script is safe, Windows is just cautious about batch files)

### macOS

**Issue:** "Permission denied" when running `run_gui.sh`

**Solution:**
```bash
chmod +x run_gui.sh
./run_gui.sh
```

**Issue:** GUI doesn't respect dark mode

**Solution:**
This is a PyQt5 limitation. The GUI uses the Fusion style for consistency.

### Linux

**Issue:** Missing Qt platform plugin

**Solution:**
```bash
sudo apt-get install libxcb-xinerama0  # Ubuntu/Debian
```

**Issue:** Font rendering issues

**Solution:**
```bash
sudo apt-get install fonts-dejavu  # Ubuntu/Debian
```

## Getting More Help

### Enable Debug Output

Run with Python directly to see detailed errors:
```cmd
cd c:\projects\home_finances
set PYTHONPATH=src
python gui_main.py
```

### Check Log Files

The GUI doesn't create log files by default. Errors are shown in dialogs and terminal output.

### Verify Installation

**Test imports:**
```python
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
python -c "from person_sheet_importer import PersonSheetImporter; print('Imports OK')"
```

**Check file structure:**
Ensure this structure exists:
```
home_finances/
├── gui_main.py
├── src/
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── home_tab.py
│   │   ├── process_month_tab.py
│   │   ├── history_tab.py
│   │   ├── templates_tab.py
│   │   └── dialogs.py
│   ├── person_sheet_importer.py
│   ├── split_calculator.py
│   ├── checkpoint_manager.py
│   └── ...
```

### Still Having Issues?

1. Try the CLI version to verify your data is correct:
   ```cmd
   uv run fairshare --person-sheets File1.xlsx File2.xlsx
   ```

2. Check the main documentation:
   - [GUI Guide](GUI_GUIDE.md)
   - [README](../README.md)

3. Create a minimal test case:
   - Use the demo: `uv run fairshare --demo`
   - Create simple test templates
   - Process one test month

4. Reinstall dependencies:
   ```cmd
   uv sync --reinstall
   ```

5. Check for updates or report the issue

## Common Error Messages

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| "No module named 'PyQt5'" | PyQt5 not installed | `uv sync` |
| "attempted relative import" | Old version of GUI | Update GUI files |
| "checkpoint_data" attribute error | Old version | Update GUI files |
| "File not found" | Wrong file path | Check file exists |
| "Invalid Excel file" | Corrupted or wrong format | Recreate file |
| "No shared expenses" | All marked as Personal | Fix Type column |
| "Division by zero" | Zero income entered | Check income values |
| "Month already processed" | Duplicate | Check history or clear |

## Prevention Tips

1. **Always backup `financial_checkpoint.json`** before major operations
2. **Test new files** with demo data first
3. **Keep Excel files simple** - avoid complex formulas
4. **Use consistent naming** - `PersonName_Month_Year.xlsx`
5. **Process months in order** - don't skip months
6. **Verify results** - review detailed breakdown after each calculation
7. **Export history regularly** - use CSV export for backup

---

**Last Updated:** 2025-01-12
**GUI Version:** 1.0.0
