# Agent Prompt — Sales Order Processing System (SOPS)
# Fan Movement (Pty) Ltd — Production & Stores Pack Generator
# DOE Architecture | Offline-First | Version: 1.0

---

## DISPATCHER BRIEF

You are the **Dispatcher** for this project. Read this entire brief before producing
`docs/todo.md`. Use `ultrathink` to plan. Do not write a single line of application
code — decompose into atomic tasks and hand off to the Orchestrator.

---

## PROJECT OVERVIEW

```
Project:     SOPS — Sales Order Processing System
Type:        Local Desktop Web App (single-machine, no internet required)
Stack:       Python 3.11+ · Flask · SQLite (via SQLAlchemy) · Jinja2 · HTML/CSS/JS
Deployment:  localhost only — `python app.py` → opens in browser
Owner:       Fan Movement (Pty) Ltd
```

**What it does:**
A production & stores management tool for Fan Movement (Pty) Ltd that converts
inbound Sales Orders into Works Orders (for production) and Bills of Materials /
Picking Lists (for stores), while tracking all inventory movements.

**Hard constraint:** The application MUST run 100% offline. No CDN links, no external
API calls, no internet dependency of any kind. All assets (fonts, icons, JS libraries)
must be vendored into `static/vendor/`.

---

## BUSINESS WORKFLOW

```
1. Upload Sales Order PDF (e.g. SO4603 from Arctic Air)
       ↓  Extract: SO number, reference, date, delivery date, customer name,
          customer VAT, delivery address, line items (description + qty + price)
2. Select Required Items from Item Listing (ItemListingReport)
       ↓  Search / filter / multi-select components needed to fulfil the SO
          Each selected line = one BOM row (item code, description, qty required,
          unit cost, stock on hand, shortfall if any)
3. Classify the Order
       ↓  User selects: ASSEMBLY ORDER (needs Works Order for production)
                   OR   STOCK ORDER (items dispatched directly from stores)
4a. Assembly Order path → Generate Works Order (WO)
       · Header: WO number (auto), SO number, customer name, delivery address,
         delivery date, sales rep, date issued, status (Open/In Progress/Complete)
       · Body: list of components to be issued to production
       · Footer: sign-off block (Produced by / Checked by / Approved by)
4b. Stock Order path → Generate Picking List (PL)
       · Header: PL number (auto), SO number, customer, delivery date
       · Body: items to pick from finished-goods / stores
       · Footer: Picked by / Checked by
5. Confirm Dispatch / Issue
       ↓  User confirms document → system deducts quantities from inventory
          and records a stock movement entry (date, ref, type, qty, user)
6. Reports
       · Stock Report — current quantities, cost, value by category
       · Movement Report — full audit trail per item or per date range
```

---

## DATA MODEL (SQLite via SQLAlchemy)

Define these models in `models.py`. Never use raw SQL strings — use ORM only.

```
Item
  id            INTEGER PK
  code          TEXT UNIQUE NOT NULL          -- from ItemListingReport "Code"
  description   TEXT NOT NULL
  category      TEXT
  last_cost     REAL DEFAULT 0
  avg_cost      REAL DEFAULT 0
  excl_price    REAL DEFAULT 0
  incl_price    REAL DEFAULT 0
  qty_on_hand   REAL DEFAULT 0
  active        BOOLEAN DEFAULT TRUE
  updated_at    DATETIME

SalesOrder
  id            INTEGER PK
  so_number     TEXT UNIQUE NOT NULL          -- e.g. "SO4603"
  reference     TEXT                          -- e.g. "FM4087"
  so_date       DATE
  delivery_date DATE
  customer_name TEXT
  customer_vat  TEXT
  delivery_address TEXT
  sales_rep     TEXT
  raw_pdf_text  TEXT                          -- extracted text from PDF
  status        TEXT DEFAULT 'Draft'          -- Draft / Open / Closed
  created_at    DATETIME

SOLineItem
  id            INTEGER PK
  so_id         FK → SalesOrder
  description   TEXT
  qty           REAL
  excl_price    REAL
  vat_pct       REAL
  excl_total    REAL
  incl_total    REAL

WorksOrder
  id            INTEGER PK
  wo_number     TEXT UNIQUE NOT NULL          -- auto: WO-YYYYMMDD-NNN
  so_id         FK → SalesOrder
  order_type    TEXT                          -- 'ASSEMBLY' or 'STOCK'
  status        TEXT DEFAULT 'Open'           -- Open / In Progress / Complete / Cancelled
  issued_by     TEXT
  created_at    DATETIME
  completed_at  DATETIME

BOMLine
  id            INTEGER PK
  wo_id         FK → WorksOrder
  item_id       FK → Item
  qty_required  REAL
  qty_issued    REAL DEFAULT 0
  unit_cost     REAL
  notes         TEXT

StockMovement
  id            INTEGER PK
  item_id       FK → Item
  movement_type TEXT    -- 'ISSUE' / 'RECEIPT' / 'ADJUSTMENT' / 'OPENING'
  reference     TEXT    -- WO number or manual ref
  qty_change    REAL    -- positive = in, negative = out
  qty_after     REAL    -- snapshot of qty_on_hand after movement
  notes         TEXT
  created_by    TEXT
  created_at    DATETIME
```

---

## FEATURE SPECIFICATIONS

### F-01 · Item Import
- On first run (or via Settings), import items from `ItemListingReport.csv`
- CSV format: first row is `sep=,`, second row is header.
  Parse with `skiprows=1` in pandas.
- Last Cost column has format `"R 1,500.00"` — strip `R ` and commas, cast to float.
- On re-import: UPDATE existing items (match on `code`), INSERT new ones.
- Record an `OPENING` StockMovement for any item where qty_on_hand changed.
- Show import summary: X updated, Y inserted, Z skipped (inactive).

### F-02 · Sales Order Upload
- Accept PDF upload via `<input type="file" accept=".pdf">`.
- Extract text server-side using `pdfplumber` (preferred) or `pypdf`.
- Parse the following fields from the extracted text (regex + heuristics):
  - SO number (pattern: `SO\d+`)
  - Reference (pattern: `FM\d+` or similar)
  - Date and Delivery Date (`DD/MM/YYYY`)
  - Customer name (line after "TO")
  - Customer VAT number
  - Delivery address block
  - Sales rep name
  - Line items: Description | Qty | Excl. Price | Disc% | VAT% | Excl. Total | Incl. Total
- Store raw extracted text in `SalesOrder.raw_pdf_text` for audit.
- If parsing fails on any field, show it as editable in the UI so the user
  can correct it before saving.
- Duplicate SO numbers should warn the user and offer to overwrite or skip.

### F-03 · BOM Builder (Item Selection)
- After SO is saved, user clicks "Build BOM / Works Pack".
- Present a searchable, filterable item table from the `Item` catalogue:
  Columns: Code · Description · Category · Qty on Hand · Excl. Price
  Filters: text search (code or description), category dropdown, in-stock only toggle.
- User enters `qty_required` per selected item (defaults to 1).
- Running total panel on the right: line count, total excl. cost, items with shortfall.
- Shortfall = qty_required > qty_on_hand → highlight row in amber.
- User selects order type: **ASSEMBLY ORDER** or **STOCK ORDER**.
- "Generate Documents" button creates the WorksOrder record + BOMLines.

### F-04 · Works Order Document (Assembly Orders)
- Printable A4 HTML page styled to match Fan Movement's brand (dark navy + orange accent,
  monospace-style table, logo placeholder top-left).
- Header block:
  ```
  WORKS ORDER                          WO Number: WO-20260521-001
  Fan Movement (Pty) Ltd               SO Number: SO4603
  3 Sivewright Ave, Alrode South       Reference: FM4087
  VAT: 4080272422                      Customer:  Arctic Air (Pty) Ltd
                                       Delivery:  8441 Kiev Crescent, Cosmo City
  Date Issued: 21/05/2026              Delivery Date: 21/05/2026
  Status: Open
  ```
- Components table:
  | # | Item Code | Description | Category | Qty Required | Qty Issued | Unit Cost | Total Cost |
- Totals row: Total Excl. Cost
- Sign-off block: Produced by ___ / Checked by ___ / Approved by ___ / Date ___
- "Print" button → `window.print()`. Print CSS hides all navigation/chrome.
- "Mark as Complete" button → sets status = Complete, records ISSUE movements for
  all BOMLines (deducts qty_issued from each item's qty_on_hand).

### F-05 · Picking List (Stock Orders)
- Same header layout as Works Order but titled "PICKING LIST".
- Table: | # | Item Code | Description | Qty to Pick | Bin/Location | Picked? |
- "Confirm Pick & Issue" button → deducts stock and records ISSUE movements.

### F-06 · Quantity Adjustment
- On the item detail page (click any item in catalogue): show current qty, movement
  history, and a form to do a manual ADJUSTMENT.
- Fields: New Qty on Hand (or Delta), Reason (text), Adjusted By (text).
- Records a StockMovement of type ADJUSTMENT.
- Also accessible inline on the BOM Builder: a small edit icon next to Qty on Hand.

### F-07 · Stock Report
- Route: `/reports/stock`
- Grouped by Category, sorted by description.
- Columns: Code · Description · Qty on Hand · Avg. Cost · Stock Value (Qty × Avg. Cost)
  · Last Movement Date
- Footer: Grand Total Value
- Filter: Category, Active only toggle, zero-stock toggle.
- Export to CSV button (server-side, streams a `.csv` response).

### F-08 · Movement Report
- Route: `/reports/movements`
- Filters: Item Code (autocomplete), Date From / Date To, Movement Type.
- Columns: Date · Item Code · Description · Type · Ref · Qty Change · Qty After · Notes · By
- Totals: net movement per item over filtered period.
- Export to CSV.

### F-09 · Dashboard (Home)
- Route: `/`
- Stat cards: Open Works Orders · Items Below Min Stock (qty ≤ 0) ·
  Movements Today · SO's This Month
- Recent Works Orders table (last 10, with status badge).
- Quick-action buttons: Upload SO · View Stock · New Adjustment.

---

## TECH STACK & CONSTRAINTS

```
Backend:    Python 3.11+, Flask 3.x, SQLAlchemy 2.x (ORM only — no raw SQL),
            pdfplumber (PDF parsing), pandas (CSV import), Werkzeug (file upload)

Frontend:   Jinja2 templates, vanilla JS (no React/Vue — keep it simple and offline),
            CSS custom properties for theming

Vendor (all bundled in static/vendor/ — NO CDN):
  - Tabulator.js 6.x  (interactive tables — download and bundle)
  - Tom Select 2.x    (searchable dropdowns)
  - Alpine.js 3.x     (reactive UI without build step)
  - Inter font        (woff2 self-hosted)

Database:   SQLite file at `instance/sops.db`
            On first run: `db.create_all()` and import items if CSV present.

Print:      All document pages must have a `@media print` CSS block that:
            - Hides: nav, sidebar, action buttons, browser chrome
            - Forces white background, black text
            - Page breaks at the right places
            - Shows full document including sign-off block

No internet: Verify by checking that NO template or Python file contains
             any URL pointing outside localhost. CI check: `grep -r "cdn\." templates/`
             must return empty.
```

---

## PROJECT STRUCTURE

```
sops/
├── app.py                    ← Flask app factory + route registration
├── models.py                 ← SQLAlchemy ORM models (all 6 tables)
├── config.py                 ← Config: DB URI, upload folder, secret key
├── requirements.txt          ← Pinned deps
├── instance/
│   └── sops.db               ← SQLite database (git-ignored)
├── uploads/                  ← Temporary PDF uploads (git-ignored)
├── routes/
│   ├── __init__.py
│   ├── dashboard.py          ← GET /
│   ├── sales_orders.py       ← SO upload, list, detail
│   ├── works_orders.py       ← WO create, detail, complete
│   ├── items.py              ← Item catalogue, adjustments, import
│   └── reports.py            ← Stock report, movement report, CSV export
├── services/
│   ├── pdf_parser.py         ← pdfplumber extraction + regex parsing
│   ├── item_importer.py      ← CSV import logic (pandas + ORM)
│   ├── bom_builder.py        ← BOM creation, shortfall calculation
│   ├── stock_service.py      ← Issue, receipt, adjustment, movement recording
│   └── doc_generator.py      ← WO / PL HTML context assembly
├── templates/
│   ├── base.html             ← Layout: nav sidebar + main content area
│   ├── dashboard.html
│   ├── sales_orders/
│   │   ├── list.html
│   │   ├── upload.html
│   │   └── detail.html
│   ├── works_orders/
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── works_order_print.html   ← Print-only template (extends nothing)
│   │   └── picking_list_print.html
│   ├── items/
│   │   ├── catalogue.html
│   │   ├── detail.html
│   │   └── import.html
│   └── reports/
│       ├── stock.html
│       └── movements.html
├── static/
│   ├── css/
│   │   ├── main.css          ← App styles + CSS variables
│   │   └── print.css         ← Print-specific overrides
│   ├── js/
│   │   ├── bom_builder.js    ← Item selection table + shortfall logic
│   │   └── adjustments.js    ← Inline qty adjustment modal
│   └── vendor/               ← ALL third-party assets bundled here
│       ├── tabulator/
│       ├── tom-select/
│       ├── alpinejs/
│       └── fonts/
├── tests/
│   ├── test_pdf_parser.py
│   ├── test_item_importer.py
│   ├── test_stock_service.py
│   └── test_bom_builder.py
└── docs/
    └── todo.md               ← Live task queue (agents update this)
```

---

## DESIGN LANGUAGE

The UI should feel like a **professional industrial operations tool** — not a generic
CRUD dashboard. Think: dark slate sidebar, cream/off-white main area, sharp orange
accent (Fan Movement brand colour), monospace font for document tables, generous
whitespace in forms.

```
CSS Variables:
  --fm-navy:       #1A2332   (sidebar background)
  --fm-orange:     #E8610A   (primary accent, buttons, badges)
  --fm-cream:      #F8F5EF   (main content background)
  --fm-text:       #1C1C1C
  --fm-muted:      #6B7280
  --fm-border:     #D1C9BC
  --fm-amber:      #F59E0B   (shortfall warning)
  --fm-green:      #16A34A   (in-stock / complete)
  --fm-red:        #DC2626   (out-of-stock / cancelled)

Typography:
  Headings:   'Inter' (self-hosted woff2), 600 weight
  Body:       'Inter', 400
  Documents:  'Courier New' or similar monospace (WO/PL print tables)
```

Status badges:
- Open         → blue pill
- In Progress  → orange pill
- Complete     → green pill
- Cancelled    → grey pill
- Shortfall    → amber row highlight

---

## SEED / BOOTSTRAP SEQUENCE

On `python app.py` (first run):

1. Create `instance/` directory if not exists.
2. Run `db.create_all()`.
3. Check if `Item` table is empty.
4. If empty AND `ItemListingReport.csv` exists in project root → auto-import items.
5. Print to console:
   ```
   ✓ Database initialised at instance/sops.db
   ✓ Imported 2,967 items from ItemListingReport.csv
   → Running at http://127.0.0.1:5000
   ```

---

## TESTING REQUIREMENTS (TDD)

Write tests BEFORE implementation for all service layer functions:

| Test file                   | Must cover                                                   |
|-----------------------------|--------------------------------------------------------------|
| `test_pdf_parser.py`        | Extracts all fields from SO4603 fixture PDF correctly        |
| `test_item_importer.py`     | Import inserts new, updates existing, skips inactive         |
| `test_stock_service.py`     | Issue deducts qty; adjustment records movement; qty_after ✓  |
| `test_bom_builder.py`       | Shortfall detected; total cost calculation; WO record created|

Use `pytest` + `pytest-flask`. SQLite in-memory DB for tests (`TESTING=True`).

---

## ATOMIC TASK BREAKDOWN FOR ORCHESTRATOR

The Orchestrator must create git worktrees for parallelisable tasks.
Suggested parallel batches:

**Batch 1 (sequential foundation):**
  T-01: Project scaffold — directory structure, `app.py`, `config.py`, `requirements.txt`
  T-02: Models — `models.py` with all 6 ORM models + `db.create_all()` bootstrap

**Batch 2 (parallel):**
  T-03: `services/item_importer.py` + `routes/items.py` + catalogue/import templates
  T-04: `services/pdf_parser.py` + `routes/sales_orders.py` + SO templates
  T-05: Vendor bundling — download Tabulator, Tom Select, Alpine.js, Inter font to `static/vendor/`

**Batch 3 (parallel, depends on T-02, T-03, T-04):**
  T-06: `services/bom_builder.py` + `bom_builder.js` (item selection UI + shortfall)
  T-07: `services/stock_service.py` (issue, receipt, adjustment, movement recording)

**Batch 4 (parallel, depends on T-06, T-07):**
  T-08: `routes/works_orders.py` + WO detail + print template (Assembly path)
  T-09: Picking List template + confirm-pick flow (Stock path)
  T-10: `routes/reports.py` + stock report + movement report + CSV export

**Batch 5 (sequential, depends on all above):**
  T-11: Dashboard — stat cards, recent WOs table, quick actions
  T-12: Test suite — all 4 test files, run `pytest`, all green
  T-13: Print CSS — `@media print` blocks on WO and PL templates, verify layout
  T-14: README.md — install instructions, `pip install -r requirements.txt`, run command

---

## ACCEPTANCE CRITERIA

The system is done when ALL of the following pass:

- [ ] `pip install -r requirements.txt && python app.py` starts with no errors
- [ ] All 2,967 items import from CSV on first run
- [ ] Upload SO4603 PDF → all fields parse correctly (SO number, customer, dates, line item)
- [ ] BOM Builder shows items with correct Qty on Hand; shortfalls highlighted in amber
- [ ] Assembly path: Works Order generated, printed to A4, "Mark Complete" deducts stock
- [ ] Stock path: Picking List generated, "Confirm Pick" deducts stock
- [ ] Stock adjustment updates qty_on_hand and records movement
- [ ] Stock Report shows all items grouped by category with correct value
- [ ] Movement Report filters by date range and item code
- [ ] `pytest` — all tests green
- [ ] `grep -r "cdn\." templates/` — returns empty (fully offline)
- [ ] `grep -r "fonts.googleapis" static/` — returns empty

---

## HARD RULES (inherit from CLAUDE.md)

1. One task = one atomic commit with a descriptive message.
2. No raw SQL — ORM only.
3. No internet dependencies — every external asset must be vendored.
4. No secrets or credentials in code.
5. `pytest` must pass before any merge.
6. Qty on Hand is the ground truth — every deduction MUST go through
   `stock_service.issue()`, never by directly writing `item.qty_on_hand`.
7. All monetary values stored as REAL (ZAR). No currency conversion logic needed.
8. PDF parser failures must NEVER crash the app — catch exceptions, return
   a partial result dict with `parse_errors: [...]` so the user can fix manually.

---

## FUTURE EXPANSION HOOKS (do not implement now — just leave extension points)

- Purchase Order receipts (GRN — Goods Received Note) → StockMovement type RECEIPT already modelled
- Multi-user login (Flask-Login ready — just add `User` model and `created_by` FK)
- Email dispatch of WO/PL as PDF attachment
- PurchasesByItemReport integration for historical movement import
- Minimum stock level alerts (add `min_qty` column to `Item`)

---

*Dispatcher: write `docs/todo.md` with these tasks, then hand to Orchestrator.*
*Orchestrator: read todo.md, spawn Executors per batch, integrate results.*
*Executors: one task, one worktree, one commit.*
