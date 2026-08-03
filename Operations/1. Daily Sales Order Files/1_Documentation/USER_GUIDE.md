
# Ops Daily Sales Order Automation

## Overview
- Updates the daily Sales Order report from SAGE CSV exports.
- Scans Released Jobs PDFs to extract text box notes and infer payment statuses.
- Rebuilds the daily tab and prints an executive summary.
- Re-injects validated payment statuses back into the report.

## Folder Layout
This workspace uses a strict 5-folder layout:
- `1_Documentation/` (this file)
- `2_Source_Data/` (CSV exports + contract register)
- `3_Live_Reports/` (Excel outputs)
- `4_Scripts/` (automation scripts)
- `5_Archive_and_Debug/` (old tools, logs, scratch)

## Requirements
### Software
- Python 3.x
- Python packages:
  - `pandas`
  - `openpyxl`
  - `pdfplumber`

### Expected Files
- Sales Order report (in `3_Live_Reports/`):
  - Preferred: `Ops Sales Order Report - MM.YYYY.xlsx`
  - Legacy (auto-renamed when possible): `Sales Order Report - MM.YYYY.xlsx`
- Contract register (external workbook):
  - `Fan Movement Contract Register.xlsx` from `C:\Users\Fan Movement\OneDrive - Fan Movement (Pty) Ltd\Zinziso Xhallie's files - Sales\Sales Contracts & Register\Contract Register`
  - uses the `Contracts 2026` tab
- CSV exports (in `2_Source_Data/`):
  - `CustomerSalesOrdersReport.csv`
  - `CustomerSalesOrdersByCustomer.csv`
  - `CustomerInvoicesReport.csv` (SAGE invoice export – used to populate the Monthly INV tab)

### Network/Folder Access
The pipeline scans Released Jobs PDFs from:
- `C:\Users\Fan Movement\OneDrive - Fan Movement (Pty) Ltd\Zinziso Xhallie's files - Sales\Sales Contracts & Register\Contract Register\Released Jobs`

## How To Run
### Option A (Recommended): One-click pipeline
Run:
- `RUN_DAILY_PIPELINE.bat`

### Option B: Run each step manually
From the project root:
```bash
python 4_Scripts\extract_pdf_comments.py
python 4_Scripts\run_daily_update.py
python 4_Scripts\update_payment_status_col_j.py
python 4_Scripts\format_reports.py
python 4_Scripts\update_invoice_tab.py
```

## Self-Correcting Behavior
- Report filename resolution:
  - Uses `Ops Sales Order Report - MM.YYYY.xlsx` for the current month.
  - If only the legacy filename exists, attempts to rename it automatically.
  - If neither current-month file exists, falls back to the most recently modified matching report in `3_Live_Reports/`.

## Troubleshooting
- Excel locked / PermissionError: close the report in Excel and rerun the pipeline.
- Missing packages:
  - `pip install pandas openpyxl pdfplumber`
- Released Jobs folder missing/unavailable: PDF extraction will skip and the pipeline will continue, but payment-status enrichment may be incomplete.
- Blank `Payment Status` cells in column J mean no validated payment status was found from the previous daily sheet or the Released Jobs PDF comments source. These cells are intentionally left blank instead of using stale formulas.

## Fix History / Known Behaviors
- 2026-06-08: Fixed Monthly INV tab cells F3, F4, F9, and F10 to use dynamic formulas linking to the BREAKDOWN section in the latest daily tab instead of static values. These cells now automatically recalculate when Excel opens the workbook or when the daily tab data changes, eliminating the need for manual linking.
- 2026-05-28: Fixed missing order details in column K when `CustomerSalesOrdersByCustomer.csv` does not contain item-description rows. The report now carries forward prior daily-sheet details where available and uses the contract register job description as a fallback for new FM jobs.
- 2026-05-28: Fixed the title date formatting by setting cell `K1` to the same bold 14 pt font size as `A1`.
- 2026-05-28: Fixed column J payment status handling. The report now writes carried-forward or PDF-derived payment statuses as real text values and no longer writes fallback `VLOOKUP` formulas into column J.
- 2026-05-28: Known behavior: column J can still be blank for orders that have no prior payment status and no validated payment-status text in the Released Jobs PDF comments. To populate those cells, update the source PDF comment/status and rerun `python 4_Scripts\update_payment_status_col_j.py`, or enter the validated status manually in the report.

## Execution Log
- 2026-07-30 15:19:22: SUCCESS - Daily update completed successfully.
- 2026-07-28 07:45:15: SUCCESS - Daily update completed successfully.
- 2026-07-27 08:04:02: SUCCESS - Daily update completed successfully.
- 2026-07-24 08:22:13: SUCCESS - Daily update completed successfully.
- 2026-07-23 13:52:39: SUCCESS - Daily update completed successfully.
- 2026-07-22 10:27:29: SUCCESS - Daily update completed successfully.
- 2026-07-21 07:22:28: SUCCESS - Daily update completed successfully.
- 2026-07-17 08:09:00: SUCCESS - Daily update completed successfully.
- 2026-07-16 07:39:10: SUCCESS - Daily update completed successfully.
- 2026-07-15 12:37:09: SUCCESS - Daily update completed successfully.
- 2026-07-14 10:53:06: SUCCESS - Daily update completed successfully.
- 2026-07-13 11:30:57: SUCCESS - Daily update completed successfully.
- 2026-07-10 08:05:00: SUCCESS - Daily update completed successfully.
- 2026-07-09 09:16:16: SUCCESS - Daily update completed successfully.
- 2026-07-08 08:16:05: SUCCESS - Daily update completed successfully.
- 2026-07-07 07:37:19: SUCCESS - Daily update completed successfully.
- 2026-07-06 12:20:13: SUCCESS - Daily update completed successfully.
- 2026-07-03 08:45:13: SUCCESS - Daily update completed successfully.
- 2026-07-02 07:57:52: SUCCESS - Daily update completed successfully.
- 2026-07-01 08:00:28: SUCCESS - Daily update completed successfully.
- 2026-06-29 07:56:24: SUCCESS - Daily update completed successfully.
- 2026-06-26 09:35:08: SUCCESS - Daily update completed successfully.
- 2026-06-25 07:20:05: SUCCESS - Daily update completed successfully.
- 2026-06-24 08:56:01: SUCCESS - Daily update completed successfully.
- 2026-06-23 10:40:47: SUCCESS - Daily update completed successfully.
- 2026-06-22 16:02:19: SUCCESS - Daily update completed successfully.
- 2026-06-19 08:24:44: SUCCESS - Daily update completed successfully.
- 2026-06-18 14:14:26: SUCCESS - Daily update completed successfully.
- 2026-06-17 07:31:21: SUCCESS - Daily update completed successfully.
- 2026-06-12 07:59:48: SUCCESS - Daily update completed successfully.
- 2026-06-11 09:42:37: SUCCESS - Daily update completed successfully.
- 2026-06-10 09:08:14: SUCCESS - Daily update completed successfully.
- 2026-06-09 08:47:52: SUCCESS - Daily update completed successfully.
- 2026-06-09 08:43:01: SUCCESS - Daily update completed successfully.
- 2026-06-08 08:43:20: SUCCESS - Daily update completed successfully.
- 2026-06-08 [FIX]: Monthly INV tab cells F3/F4/F9/F10 now use formulas linking to BREAKDOWN section instead of static values.
- 2026-06-05 07:34:57: SUCCESS - Daily update completed successfully.
- 2026-06-04 15:41:19: SUCCESS - Daily update completed successfully.
- 2026-06-04 07:50:07: SUCCESS - Daily update completed successfully.
- 2026-06-03 07:51:12: SUCCESS - Daily update completed successfully.
- 2026-06-02 07:49:39: SUCCESS - Daily update completed successfully.
- 2026-06-01 08:52:08: SUCCESS - Daily update completed successfully.
- 2026-05-29 10:08:19: SUCCESS - Daily update completed successfully.
- 2026-05-28 12:59:11: SUCCESS - Daily update completed successfully.
- 2026-05-28 10:35:02: SUCCESS - Daily update completed successfully.
- 2026-05-28 07:41:47: SUCCESS - Daily update completed successfully.
- 2026-05-25 13:54:11: SUCCESS - Daily update completed successfully.
- 2026-05-25 13:28:36: SUCCESS - Daily update completed successfully.
- 2026-05-25 09:25:11: SUCCESS - Daily update completed successfully.
- 2026-05-21 08:22:29: SUCCESS - Daily update completed successfully.
- 2026-05-20 07:47:38: SUCCESS - Daily update completed successfully.
- 2026-05-19 09:32:06: SUCCESS - Daily update completed successfully.
- 2026-05-18 09:17:55: SUCCESS - Daily update completed successfully.
- 2026-05-18 09:08:32: SUCCESS - Daily update completed successfully.
- 2026-05-18 08:55:26: SUCCESS - Daily update completed successfully.
- 2026-05-15 08:15:39: SUCCESS - Daily update completed successfully.
- 2026-05-14 07:51:02: SUCCESS - Daily update completed successfully.
- 2026-05-13 08:42:04: SUCCESS - Daily update completed successfully.
- 2026-05-12 08:22:22: SUCCESS - Daily update completed successfully.
- 2026-05-12 08:02:41: SUCCESS - Daily update completed successfully.
- 2026-05-11 07:32:51: SUCCESS - Daily update completed successfully.
- 2026-05-08 07:41:09: SUCCESS - Daily update completed successfully.
- 2026-05-07 12:31:09: SUCCESS - Daily update completed successfully.
- 2026-05-07 12:27:23: SUCCESS - Daily update completed successfully.
- 2026-05-07 12:18:57: SUCCESS - Daily update completed successfully.
- 2026-05-07 11:58:26: SUCCESS - Daily update completed successfully.
- 2026-05-07 11:50:24: SUCCESS - Daily update completed successfully.
- 2026-05-07 08:02:12: SUCCESS - Daily update completed successfully.
- 2026-05-06 09:35:59: SUCCESS - Daily update completed successfully.
- 2026-05-05 09:38:32: SUCCESS - Daily update completed successfully.
- 2026-05-04 07:52:45: SUCCESS - Daily update completed successfully.
- 2026-04-29 10:17:19: SUCCESS - Daily update completed successfully.
- 2026-04-29 10:04:19: SUCCESS - Daily update completed successfully.
- 2026-04-28 08:38:57: SUCCESS - Daily update completed successfully.
- 2026-04-23 09:33:56: SUCCESS - Daily update completed successfully.
- 2026-04-22 11:33:35: SUCCESS - Daily update completed successfully.
- 2026-04-21 15:37:00: SUCCESS - Daily update completed successfully.
- 2026-04-21 15:23:57: SUCCESS - Daily update completed successfully.
- 2026-04-21 15:18:26: SUCCESS - Daily update completed successfully.
- 2026-04-21 15:09:41: SUCCESS - Daily update completed successfully.
- 2026-04-21 14:58:20: SUCCESS - Daily update completed successfully.
- 2026-04-21 14:53:17: SUCCESS - Daily update completed successfully.
- 2026-04-21 14:48:43: SUCCESS - Daily update completed successfully.
- 2026-04-21 12:26:02: SUCCESS - Daily update completed successfully.
- 2026-04-21 09:22:40: SUCCESS - Daily update completed successfully.
