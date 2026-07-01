@echo off
title SOPS - Sales Order Processing System
echo ========================================
echo Starting SOPS Application...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

REM Start the Flask application
echo Launching application at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
venv\Scripts\python.exe app.py

pause
