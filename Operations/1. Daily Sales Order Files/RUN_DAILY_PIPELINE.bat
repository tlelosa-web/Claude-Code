@echo off
title Daily Sales Order Pipeline
color 0B

echo =======================================================
echo     DAILY SALES ORDER UPDATE PIPELINE
echo =======================================================
echo.

:: Ensure working directory is the folder where the bat file lives
cd /d "%~dp0"

:: Use the external contract register workbook and Contracts 2026 tab
set "CONTRACT_REGISTER_PATH=C:\Users\Fan Movement\OneDrive - Fan Movement (Pty) Ltd\Zinziso Xhallie's files - Sales\Sales Contracts & Register\Contract Register\Fan Movement Contract Register.xlsx"

echo [1/5] Extracting latest PDF Comments...
python "4_Scripts\extract_pdf_comments.py"
echo.

echo [2/5] Building Sales Report from SAGE...
python "4_Scripts\run_daily_update.py"
echo.

echo [3/5] Re-injecting PDF statuses...
python "4_Scripts\update_payment_status_col_j.py"
echo.

echo [4/5] Formatting reports (highlighting pending jobs, setting column widths, adding footnotes)...
python "4_Scripts\format_reports.py"
echo.

echo [5/5] Building Monthly Invoice tab (from CustomerInvoicesReport.csv)...
python "4_Scripts\update_invoice_tab.py"
echo.

echo =======================================================
echo          PIPELINE FINISHED SUCCESSFULLY!
echo =======================================================
pause
