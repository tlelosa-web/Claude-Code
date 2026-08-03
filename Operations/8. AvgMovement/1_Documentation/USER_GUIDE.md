# User Guide

## Overview

This project automates item movement reporting and analysis.

## How to Run (Full Pipeline)

1. Double-click `RUN_PIPELINE.bat` from the project root.
2. Check `3_Live_Reports/` for generated outputs.
3. Review `5_Archive_and_Debug/` for logs and debug info.

## Update Current Stock Values

Current Stock is loaded from:

- `2_Source_Data/ImportStockFinal.xlsx` → sheet `ImportStockCount_TOT`
- Columns used: `Item` and `Current Stock`

To update Current Stock in the generated reports:

1. Open `2_Source_Data/ImportStockFinal.xlsx`
2. Go to `ImportStockCount_TOT`
3. Update the `Current Stock` column values for the relevant `Item` codes
4. Save the Excel file
5. Re-run `RUN_PIPELINE.bat`

Notes:
- If an item code is not found in `ImportStockCount_TOT`, Current Stock will default to `0` in the reports.
- Always save/close the Excel file before running the pipeline to avoid file lock issues.

## Folder Structure

- `1_Documentation/` - Project directives and guides
- `2_Source_Data/` - Raw input files (CSV, Excel, etc.)
- `3_Live_Reports/` - Generated outputs and dashboards
- `4_Scripts/` - Python automation scripts
- `5_Archive_and_Debug/` - Logs, tests, and archived files

## Inputs (Source Data)

- `2_Source_Data/ItemMovementReport.csv`
  - Primary item movement transactions used to calculate Purchased/Sold totals and periods
- `2_Source_Data/ItemListingReport.csv`
  - Used to enrich items with Description, Category, and Avg. Cost
- `2_Source_Data/OutstandingPOByItemReport.csv`
  - Used to calculate Supplier, Lead Time, and On Order (pending quantities)
- `2_Source_Data/ImportStockFinal.xlsx`
  - Used to populate Current Stock (from `ImportStockCount_TOT`)

## Outputs (Reports)

Generated into `3_Live_Reports/`:

- `Item Movement [dd.mm.yyyy].xlsx`
  - Sheet: `Item Movement Summary`
  - Sheet: `Order Summary`
- `Item Movement By Cat [dd.mm.yyyy].xlsx`
  - Sheet: `Category Summary`
  - One sheet per Category

## Scripts (Functions)

These are the main scripts in `4_Scripts/` and what each one does:

- `item_movement_report.py`
  - Reads `ItemMovementReport.csv`, enriches from `ItemListingReport.csv`, `OutstandingPOByItemReport.csv`, and `ImportStockFinal.xlsx`
  - Produces `Item Movement [date].xlsx`
- `item_movement_by_cat.py`
  - Uses the same inputs as `item_movement_report.py`
  - Produces `Item Movement By Cat [date].xlsx` with a summary tab and category tabs
- `align_formatting.py`
  - Copies the formatting/column layout from the latest `Item Movement [date].xlsx` summary tab onto all tabs in `Item Movement By Cat [date].xlsx`
  - Use when you need formatting consistency (not required for normal pipeline runs)
- `diagnose_missing_item.py`
  - Helper script used to diagnose why an item may be missing from a report
- `patch_python.py`
  - Helper script used for one-off patching of scripts (not part of normal pipeline runs)


## Troubleshooting

- Check `5_Archive_and_Debug/debug_output_utf8.txt` for detailed logs.
- Ensure all source data files are placed in `2_Source_Data/`.
