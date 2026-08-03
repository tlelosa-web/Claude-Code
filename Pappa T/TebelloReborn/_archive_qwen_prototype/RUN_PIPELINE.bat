@echo off
title TebelloReborn Pipeline
echo ========================================
echo   TebelloReborn - Pipeline Runner
echo ========================================
echo.

REM Ensure execution from Project Root
cd /d "%~dp0"

echo [INFO] Starting pipeline execution...
echo [INFO] Timestamp: %date% %time%
echo.

REM Check for Python availability
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo [ERROR] Please install Python 3.x and add it to your system PATH.
    pause
    exit /b 1
)

echo [INFO] Python detected. Proceeding with pipeline...
echo.

REM ========================================
REM PIPELINE STAGES
REM Add script calls below as needed:
REM python 4_Scripts\your_script.py
REM ========================================

echo [INFO] No scripts configured yet in pipeline.
echo [INFO] Add your Python scripts to 4_Scripts\ and update RUN_PIPELINE.bat
echo.

echo ========================================
echo   Pipeline Complete
echo ========================================
echo.
pause
