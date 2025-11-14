@echo off
REM FairShare GUI Launcher for Windows
REM Double-click this file to launch the FairShare GUI

echo Starting FairShare GUI...
echo.

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo Error: uv is not installed or not in PATH
    echo Please install uv from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

REM Launch the GUI using uv
uv run gui_main.py

REM If there was an error, pause so user can see it
if errorlevel 1 (
    echo.
    echo An error occurred. Please check the error message above.
    pause
)
