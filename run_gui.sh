#!/bin/bash
# FairShare GUI Launcher for macOS/Linux
# Run this script to launch the FairShare GUI: ./run_gui.sh

echo "Starting FairShare GUI..."
echo

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Please install uv from https://docs.astral.sh/uv/"
    exit 1
fi

# Launch the GUI using uv
uv run gui_main.py

# Check exit status
if [ $? -ne 0 ]; then
    echo
    echo "An error occurred. Please check the error message above."
    read -p "Press Enter to continue..."
fi
