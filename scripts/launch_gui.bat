@echo off
title LPES GUI Manager
echo 🚀 Starting LPES GUI Manager...
echo.

REM Change to root directory (parent of scripts)
cd /d "%~dp0\.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ and try again
    pause
    exit /b 1
)

REM Check if GUI files exist
if not exist "gui\lpes_gui_enhanced.py" (
    if not exist "gui\lpes_gui.py" (
        echo ❌ GUI files not found in gui directory
        echo Please ensure you're running from the LPES root directory
        pause
        exit /b 1
    )
)

REM Launch the GUI launcher
python scripts\launch_gui.py

if errorlevel 1 (
    echo.
    echo ❌ LPES GUI failed to start
    echo Check the error message above
    echo.
    echo 📋 Troubleshooting:
    echo   1. Run: pip install -r requirements.txt
    echo   2. Ensure you're in the LPES root directory
    echo   3. Check Python version (3.9+ required)
    pause
)
