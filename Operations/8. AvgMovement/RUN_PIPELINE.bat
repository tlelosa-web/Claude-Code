@echo off
REM ============================================
REM RUN_PIPELINE.bat - Master Executable
REM Run all scripts in sequence from Project Root
REM ============================================

echo ============================================
echo  Starting AvgMovement Pipeline
echo ============================================
echo.

cd /d "%~dp0"

REM Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.x and try again.
    pause
    exit /b 1
)

REM Check for required Python packages
python -c "import openpyxl" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install openpyxl
)

REM Archive previous-month reports (keep current month clean in 3_Live_Reports)
echo Archiving previous-month reports from 3_Live_Reports...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$curr=Get-Date; $live=Join-Path $PWD '3_Live_Reports'; $archiveRoot=Join-Path $PWD '5_Archive_and_Debug\Archived_Reports'; if(!(Test-Path $live)){exit 0}; Get-ChildItem -Path $live -Filter '*.xlsx' -File | ForEach-Object { $m=[regex]::Match($_.BaseName,'(\d{2}\.\d{2}\.\d{4})$'); if(-not $m.Success){ return }; $d=$m.Groups[1].Value; try{ $dt=[datetime]::ParseExact($d,'dd.MM.yyyy',$null) } catch { return }; if($dt.Year -ne $curr.Year -or $dt.Month -ne $curr.Month){ $folder=Join-Path $archiveRoot ($dt.ToString('yyyy-MM')); New-Item -ItemType Directory -Force -Path $folder | Out-Null; Move-Item -LiteralPath $_.FullName -Destination $folder -Force -ErrorAction SilentlyContinue } }" >nul
echo.

REM Run pipeline
echo Running Item Movement Report pipeline...
echo.

python 4_Scripts\item_movement_report.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Item Movement pipeline failed. Check 5_Archive_and_Debug\debug_output_utf8.txt
    pause
    exit /b 1
)

echo Running Item Movement By Category pipeline...
echo.

python 4_Scripts\item_movement_by_cat.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Category pipeline failed. Check 5_Archive_and_Debug\debug_output_utf8.txt
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Pipeline Complete
echo ============================================
pause
