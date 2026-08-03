@echo off
echo =========================================
echo INVENTORY MANAGEMENT SYSTEM PIPELINE
echo =========================================
echo.

echo [1/4] Extracting and Cleaning Data...
python 4_Scripts\01_extract_data.py
if %errorlevel% neq 0 (
    echo Extraction failed. Check 1_Documentation\GEMINI.md for details.
    pause
    exit /b %errorlevel%
)
echo.

echo [2/4] Calculating Average Monthly Usage (AMU)...
python 4_Scripts\04_calculate_amu.py
if %errorlevel% neq 0 (
    echo AMU calculation failed.
    pause
    exit /b %errorlevel%
)
echo.

echo [3/4] Building Inventory Master...
python 4_Scripts\02_build_inventory.py
if %errorlevel% neq 0 (
    echo Building failed.
    pause
    exit /b %errorlevel%
)
echo.

echo [4/4] Generating Live Report...
python 4_Scripts\03_generate_report.py
if %errorlevel% neq 0 (
    echo Report Generation failed.
    pause
    exit /b %errorlevel%
)
echo.

echo =========================================
echo PIPELINE COMPLETED SUCCESSFULLY!
echo =========================================
pause
