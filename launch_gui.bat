@echo off
title LPES GUI Manager
echo 🚀 Starting LPES GUI Manager...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ and try again
    pause
    exit /b 1
)

REM Launch the GUI
python lpes_gui.py

if errorlevel 1 (
    echo.
    echo ❌ LPES GUI failed to start
    echo Check the error message above
    pause
)
