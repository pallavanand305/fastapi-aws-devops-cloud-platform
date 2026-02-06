@echo off
echo 🚀 ML Workflow Platform - Local Development Setup
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Run the Python startup script
python scripts/local_start.py

pause