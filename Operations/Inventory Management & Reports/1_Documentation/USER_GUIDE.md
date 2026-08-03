# 📋 Inventory Management System — User Guide
**Fan Movement (Pty) Ltd** | Last Updated: 2026-03-24

---

## 1. Overview

This system automatically processes SAGE data exports and generates a 3-tab Excel inventory dashboard at:

```
3_Live_Reports/Live_Inventory_Status.xlsx
```

To run it, **double-click** `RUN_PIPELINE.bat` from the project root folder.

---

## 2. Required Source Data

Place the following files in the `2_Source_Data/` folder before running the pipeline.

| # | File | Source | Required? | What It Provides |
|---|------|--------|-----------|------------------|
| 1 | `ItemListingReport.csv` | SAGE Export → Item Listing Report | **Yes** | Item Code, Description, Category, Qty on Hand |
| 2 | `Workshop Stock 19.03.26.xlsx` | Workshop reference workbook | **Yes** | ROP/MAX baseline values, embedded reference sheet with Category & Cost Price |
| 3 | `ImportStockFinal.xlsx` | Import stock workbook | Optional | Additional Category, Cost Price, and Supplier data |
| 4 | `CustomerSalesOrdersByCustomer.csv` | SAGE Export → Customer Sales Orders by Customer | Optional | Sales quantities for AMU calculation (demand signal) |
| 5 | `OutstandingPOByItemReport.csv` | SAGE Export → Purchase Orders by Item | Optional | PO quantities for AMU fallback, Supplier, and Lead Time |

> **Tip:** Optional files improve data coverage. The system gracefully skips any missing optional file.

---

## 3. How to Export from SAGE

### ItemListingReport.csv
1. SAGE → Reports → Item Listing Report
2. Export as **CSV**
3. Save to `2_Source_Data/`

### CustomerSalesOrdersByCustomer.csv
1. SAGE → Reports → Customer Sales Orders by Customer
2. Select **All Dates** or a wide date range
3. Export as **CSV**
4. Save to `2_Source_Data/`

### OutstandingPOByItemReport.csv
1. SAGE → Reports → Purchase Orders by Item Report
2. Set Start Date to the **earliest available** and End Date to **today**
3. Export as **CSV**
4. Save to `2_Source_Data/`

---

## 4. Output Reports

The generated `Live_Inventory_Status.xlsx` contains 3 tabs:

### Tab 1: Master Live Inventory Status
Full dataset with all calculated fields — the source of truth.

| Column | Description |
|--------|-------------|
| Code | SAGE item code |
| Description | Product description |
| Category | Product category |
| Supplier | Last known supplier (from PO data) |
| Cost Price | Unit cost (ZAR) |
| Avg Monthly Usage (AMU) | Average units sold/bought per month |
| Lead Time (months) | Average delivery lead time from PO history |
| Safety Factor (months) | Buffer multiplier (default: 1 month) |
| Review Period (months) | Replenishment review cycle (default: 1 month) |
| Safety Stock | AMU × Safety Factor |
| Lead Time Demand | AMU × Lead Time |
| Reorder Point (ROP) | Safety Stock + Lead Time Demand |
| Maximum Stock (MAX) | ROP + (AMU × Review Period) |
| Current Stock | Live Qty on Hand from SAGE |
| On Order | Outstanding purchase order qty |
| Order Quantity | Qty to order when stock ≤ ROP |
| Replenishment | MAX − Current Stock − On Order (floored at 0) |
| Order Cost | Replenishment × Cost Price |

### Tab 2: Live Inventory Report
Streamlined operational view with key columns only:
- Code, Description, Category, Supplier
- Safety Stock, ROP, MAX, Current Stock, On Order, Replenishment

### Tab 3: Suggested Orders
Filtered to items **that need ordering** (Replenishment > 0), with Cost Price and Order Cost columns added.

---

## 5. Stock Level Formulas

```
Safety Stock     = AMU × Safety Factor
Lead Time Demand = AMU × Lead Time (months)
Reorder Point    = Safety Stock + Lead Time Demand
Maximum Stock    = ROP + (AMU × Review Period)
Replenishment    = MAX − Current Stock − On Order
Order Cost       = Replenishment × Cost Price
```

AMU is calculated from the **earliest transaction date to today**:
- **Primary source**: Sales orders (units sold ÷ months)
- **Fallback source**: Purchase orders (units bought ÷ months)
- Items with no transaction history show `N/A`

---

## 6. Folder Structure

```
📁 Inventory Management & Reports/
├── 📁 1_Documentation/       ← This guide + GEMINI.md
├── 📁 2_Source_Data/          ← Place SAGE exports here
├── 📁 3_Live_Reports/         ← Generated output appears here
├── 📁 4_Scripts/              ← Python automation scripts
├── 📁 5_Archive_and_Debug/    ← Temp files, logs, debug output
└── ⚡ RUN_PIPELINE.bat        ← Double-click to run
```

---

## 7. Troubleshooting

| Problem | Solution |
|---------|----------|
| Pipeline fails at extraction | Ensure CSV/XLSX files are in `2_Source_Data/` with exact filenames |
| PermissionError on report | Close `Live_Inventory_Status.xlsx` before running the pipeline |
| Encoding errors | Re-export CSVs from SAGE (the system handles UTF-8-sig and Latin1) |
| Many items show `N/A` for AMU | Provide sales or PO CSV files with a wider date range |
| Error details | Check `1_Documentation/GEMINI.md` (execution log at the bottom) |
| Debug data | Check `5_Archive_and_Debug/debug_output_utf8.txt` |
