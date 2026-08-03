# Inventory Management & Reports
# MASTER DIRECTIVE: AGENTIC WORKFLOW 2.0

## 1. DIRECTIVE (The Brain)
**Role:** Senior Autonomous Systems Architect.
**Objective:** Build an automated basic inventory management spreadsheet system that ingests source data, calculates inventory metrics (including AMU from dual sources), and generates live reports.
**Operational Principle:** Think-Before-Execution. Analyze the workspace context, directory structure, and existing data before generating any output.
**Quality Standards:** 
- Modular, self-documenting architecture.
- Atomic execution: Small, verifiable changes over massive code dumps.

## 2. SYSTEM ARCHITECTURE

📁 Inventory Management & Reports/
├── 📁 1_Documentation/
│   ├── GEMINI.md
│   └── USER_GUIDE.md
├── 📁 2_Source_Data/
│   ├── ItemListingReport.csv              <-- SAGE item master (Code, Desc, Category, Qty on Hand)
│   ├── Workshop Stock 19.03.26.xlsx       <-- Workshop ROP/MAX calc sheets + embedded reference
│   ├── ImportStockFinal.xlsx              <-- Import stock with Category, Cost Price, Supplier
│   ├── CustomerSalesOrdersByCustomer.csv  <-- SAGE sales orders (AMU Source 1: qty sold)
│   ├── OutstandingPOByItemReport.csv      <-- SAGE purchase orders (AMU Source 2: qty bought)
│   └── Cost Prices.xlsx                   <-- Fallback cost prices, supplier, category (514 rows)
├── 📁 3_Live_Reports/
│   └── Live_Inventory_Status.xlsx         <-- Final automated output
├── 📁 4_Scripts/
│   ├── 01_extract_data.py                 <-- Shadow-copy extractor for all sources
│   ├── 02_build_inventory.py              <-- Master builder: merge, map, inject AMU
│   ├── 03_generate_report.py              <-- Report writer with formatting
│   └── 04_calculate_amu.py                <-- Dual-source AMU calculator
├── 📁 5_Archive_and_Debug/
└── ⚡ RUN_PIPELINE.bat                     <-- 4-step master executable

## 3. CODING STANDARDS & VALIDATION
**1. Data Safety Protocol (Shadow Copying):** `tempfile` + `shutil.copy2` for all `.xlsx` reads.
**2. UTF-8 File Logging:** Debug outputs to `5_Archive_and_Debug/debug_output_utf8.txt`.
**3. Modular File Architecture:** Isolated modules chained via `RUN_PIPELINE.bat`.
**4. Error Handling (Self-Annealing):** Global `try/except` with human-readable log to `GEMINI.md`.

## 4. ORCHESTRATION (The Architect)
1. **Discovery:** Index workspace and identify all data sources.
2. **Strategy:** Present plan for user approval before modifying data.
3. **Execution:** Write logic in small, testable chunks.
4. **Validation:** Run integrity checks after every change.
5. **Logging:** Update Execution Log below.

## 5. EXECUTION CHECKLIST (The Worker)
- [x] **Task 1: Scaffold the Workspace**
- [x] **Task 2: Initialize the Brain**
- [x] **Task 3: Assess Source Data**
- [x] **Task 4: Develop Core Modular Scripts** (Extract, Build, Report)
- [x] **Task 5: Master Executable** (RUN_PIPELINE.bat)
- [x] **Task 6: Integrate ImportStockFinal** (Category, Cost Price, Supplier mapping)
- [x] **Task 7: Advanced Formatting** (Top Alignment, Frozen Panes, Accounting fmt)
- [x] **Task 8: AMU Calculator v1** (Sales Orders: `CustomerSalesOrdersByCustomer.csv`)
- [x] **Task 9: AMU Calculator v2 — Dual Source**
    - [x] Parse `OutstandingPOByItemReport.csv` (hierarchical SAGE PO export).
    - [x] Calculate AMU from PO data: Total Qty Bought ÷ Months (earliest PO to today).
    - [x] Merge both AMU sources: Sales-based AMU and PO-based AMU.
    - [x] Inject the best available AMU into the inventory (Sales-first, PO as fallback, N/A placeholder).
    - [x] Verify pipeline end-to-end.
- [x] **Task 10: Supplier-Grouped PO File** (`OutstandingPurchaseOrdersBySupplierReport.csv` integrated)
- [x] **Task 11: Cost File Integration** (`Cost Prices.xlsx` → fallback Cost Price, Supplier, Category)
- [x] **Task 12: Stock Adjustments & Overrides** (Reserved column, Re-Order calculation, and bi-directional Stock Take tab integration)
- [x] **Task 13: Executive Dashboard**
    - [x] Create a new "Executive Dashboard" tab in the final report.
    - [x] Add KPIs: Total Inventory Value, Total Value of Suggested Orders, Number of Items to Re-Order.
    - [x] Add Charts: Inventory Value by Category, Top 10 Items to Re-Order, Stock Status Breakdown.

## 6. PROJECT STATE & LOG
**Current Status:** In Development
**Memory Buffer:**
- `ItemListingReport.csv`: SAGE item master with `sep=,` header bug, skip 1 row.
- `Workshop Stock 19.03.26.xlsx`: Multi-sheet workbook. `W-shop Calc` = main calc sheet. Contains embedded `ItemListingReport` reference sheet.
- `ImportStockFinal.xlsx`: `ImportStockCount_TOT` sheet has items with Code, Category, Cost Price, Supplier. Header on row 1 (skiprows=1).
- `CustomerSalesOrdersByCustomer.csv`: Hierarchical SAGE export. Customer → Date/SO → Item lines. 16,445 rows. Uses Description as item ID.
- `OutstandingPOByItemReport.csv`: Hierarchical SAGE PO export. 6,702 rows. Item headers combine Code + Description (e.g. `0.2543PM - 0.25kW...`). PO lines have Date, Ref, Supplier, Qty, Price. Date range: 01/03/2020 to 28/02/2027.

**Execution Log:**
- 2026-03-25 16:00: Task 12 complete — Replaced 'Replenishment' with 'Re-Order', bolded sheet headers, added 'Reserved' column, and implemented a bidirectional manual override system via the new 'Stock Take' tab.
- 2026-03-25 14:45: Task 10 complete — Outstanding PO Suppliers layer integrated (2,143 items mapped). Supplier waterfall and category inference added. "Stock Health" summary tab created. Pipeline item count verified at 2,884.
- 2026-03-24 13:38: Task 11 complete — Cost Prices.xlsx (481 rows) integrated. 2,356/2,884 items now have Cost Price.
- 2026-03-24 13:03: Task 9 re-verified — Pipeline end-to-end: 2,527 Sales + 1,174 PO AMU, 1,440/2,884 items with AMU. Live_Inventory_Status.xlsx regenerated.
- 2026-03-24 02:34: Tasks 10-12 complete — PO supplier (1,174), lead time mapped, stock levels recalculated (1,040 items), 3-tab report generated.
- 2026-03-24 02:17: Task 9 complete — Dual-source AMU: 2,527 Sales + 1,174 PO items parsed and merged.
- 2026-03-24 02:15: Proposed dual-source AMU plan (Task 9). Awaiting user approval.
- 2026-03-24 01:55: AMU Calculator v1 completed — 680 items mapped from sales data.
- 2026-03-24 01:14: ImportStockFinal integrated + top alignment + frozen panes.
- 2026-03-24 01:04: Workshop Stock reference sheet mapped for Category and Cost Price.
- 2026-03-24 00:49: All SAGE items loaded via outer join.
- 2026-03-24 00:34: Project initialized. 5-folder scaffold complete.
