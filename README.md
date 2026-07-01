# SOPS — Sales Order Processing System

**Fan Movement (Pty) Ltd — Production & Stores Pack Generator**

A local desktop web application for managing Sales Orders, generating Works Orders and Picking Lists, and tracking inventory movements.

## Features

| Feature | Description |
| --- | --- |
| **Item Import** | Import items from `data/ItemListingReport.csv` with currency parsing |
| **Sales Order Upload** | Upload PDF sales orders, auto-extract fields using `pdfplumber` |
| **BOM Builder** | Searchable, filterable item selection with shortfall detection |
| **Works Orders** | A4-printable Works Order documents (Assembly Orders) |
| **Picking Lists** | A4-printable Picking List documents (Stock Orders) |
| **Stock Adjustment** | Manual quantity adjustments with audit trail |
| **Stock Report** | Grouped by category with filters and CSV export |
| **Movement Report** | Full audit trail per item with date range filtering |
| **Dashboard** | Stat cards, recent activity, quick-action buttons |

## Tech Stack

```
Backend:   Python 3.11+ · Flask 3.x · SQLAlchemy 2.x · pdfplumber · pandas
Frontend:  Jinja2 · Vanilla JS · CSS Custom Properties
Database:  SQLite (instance/sops.db)
Vendor:    Tabulator.js 6.x · Tom Select 2.x · Alpine.js 3.x · Inter font
Offline:   100% — no CDN links, no internet required at runtime
```

## Quick Start

```bash
# 1. Clone and enter the project
cd sops

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate    # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download vendor libraries (one-time)
# Windows PowerShell:
Invoke-WebRequest -Uri "https://unpkg.com/tabulator-tables@6.3.0/dist/css/tabulator.min.css" -OutFile "static\vendor\tabulator\tabulator.min.css"
Invoke-WebRequest -Uri "https://unpkg.com/tabulator-tables@6.3.0/dist/js/tabulator.min.js" -OutFile "static\vendor\tabulator\tabulator.min.js"
Invoke-WebRequest -Uri "https://unpkg.com/tom-select@2.3.1/dist/css/tom-select.css" -OutFile "static\vendor\tom-select\tom-select.css"
Invoke-WebRequest -Uri "https://unpkg.com/tom-select@2.3.1/dist/js/tom-select.complete.min.js" -OutFile "static\vendor\tom-select\tom-select.complete.min.js"
Invoke-WebRequest -Uri "https://unpkg.com/alpinejs@3.14.8/dist/cdn.min.js" -OutFile "static\vendor\alpinejs\alpine.min.js"

# 5. Run the app (first run auto-creates DB and imports items)
python app.py

# 6. Open in browser
# http://127.0.0.1:5000
```

## Usage Flow

```
1. Upload Sales Order PDF → fields are parsed automatically
2. Review & correct parsed fields → Save
3. Click "Build BOM / Works Pack" → Select items from catalogue
4. Choose order type:
   → Assembly Order → Generates Works Order (A4 printable)
   → Stock Order   → Generates Picking List (A4 printable)
5. Confirm dispatch → Stock is deducted, movement recorded
6. View reports: Stock Report, Movement Report
```

## Project Structure

```
sops/
├── app.py                    ← Flask app factory
├── models.py                 ← SQLAlchemy ORM models (6 tables)
├── config.py                 ← Configuration
├── requirements.txt          ← Python dependencies
├── launch.bat                ← Windows launch batch script
├── launch.ps1                ← Windows launch PowerShell script
├── instance/sops.db          ← SQLite database (auto-created)
├── data/                     ← Data sheets and PDF samples
│   ├── ItemListingReport.csv
│   ├── ItemMovementReport.csv
│   └── FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf
├── logs/                     ← Application logs and run outputs
│   ├── startup.log
│   └── startup.err.log
├── scripts/                  ← Helper and utility scripts
│   ├── download_vendor.sh
│   ├── fast_import.py
│   ├── fix_so_status.py
│   ├── migrate_add_related_wo.py
│   ├── quick_update_items.py
│   └── test_import.py
├── routes/                   ← Route handlers
│   ├── dashboard.py
│   ├── sales_orders.py
│   ├── works_orders.py
│   ├── items.py
│   └── reports.py
├── services/                 ← Business logic
│   ├── pdf_parser.py
│   ├── item_importer.py
│   ├── bom_builder.py
│   ├── doc_generator.py
│   └── stock_service.py
├── templates/                ← Jinja2 templates
├── static/                   ← CSS, JS, vendored libraries
├── tests/                    ← pytest test suite
├── docs/                     ← DCOE specs, task queue, research, bugs, decisions
│   ├── todo.md
│   └── specs/
├── .Codex/                   ← Codex executor manifests, hooks, commands, worktrees
├── trading/                  ← Trading domain workspace
├── engineering/              ← Engineering domain workspace
└── tools/                    ← Software / AI tooling workspace
```

## Running Tests

```bash
pytest tests/ -v
```

## Hard Constraints

- **100% offline** — No CDN links, no external API calls
- **ORM only** — No raw SQL strings
- **Stock integrity** — Every deduction goes through `stock_service.issue()`
- **Fault-tolerant parsing** — PDF parser never crashes; returns partial results

## License

Internal tool — Fan Movement (Pty) Ltd
