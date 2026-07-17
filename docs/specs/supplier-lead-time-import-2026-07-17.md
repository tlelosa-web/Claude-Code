# Spec — Supplier + Lead Time import (from Sage OutstandingPOByItemReport.csv)

**Date:** 2026-07-17 | **Owner:** Tebello Lelosa | **Status:** Approved, ready to build

## Context

Cross-project review found `8. AvgMovement` (a standalone Excel pipeline) computes
per-item Supplier and Lead Time from a Sage export (`OutstandingPOByItemReport.csv`)
that SOPS doesn't ingest today. Tebello decided to fold this into SOPS rather than
keep two systems doing overlapping things, and to retire AvgMovement once this ships
(retirement tracked separately at the hub level, not part of this spec).

Confirmed scope (3 rounds of AskUserQuestion):
1. **Surface location:** Stock Report (new columns) + Item detail page.
2. **Import mechanism:** new, separate manual CSV import — not folded into the
   existing Items import — mirroring the existing `items.import_csv` pattern.
3. **On Order — explicitly OUT of scope.** SOPS already computes its own
   `qty_on_order` live from PurchaseOrders created inside SOPS
   (`services/demand.py::get_qty_on_order_bulk`). The Sage CSV's own on-order
   figure (`pending_qty` in AvgMovement's parser) must **not** be imported or
   surfaced anywhere — doing so would recreate the exact "two processes, two
   numbers" problem this consolidation is meant to remove. Only `Supplier` and
   `Lead Time` are new; parse the CSV for those two fields only.

## Data source

`OutstandingPOByItemReport.csv` — same Sage export format AvgMovement already
parses. Reference implementation to adapt (read-only reference, do not import
from this path — copy/adapt the parsing logic):
`8. AvgMovement/4_Scripts/item_movement_report.py::parse_po_by_item()`.

Format: title row + 3 metadata rows, then repeating blocks of:
- an "item name" row: `Code - Description` (or just `Code`)
- transaction rows: `Date, Reference, Order No., Supplier, Delivery Date, Status, Qty, ...`
- a `Total for Item:` row ending the block

Per item, compute:
- `supplier` — the most-frequent `Supplier` value across that item's PO rows
  (mode by transaction count, matching AvgMovement's `top_supplier` logic).
- `lead_time_weeks` — average of `(Delivery Date - Date)` in weeks across rows
  with a valid, non-negative delivery date (matching AvgMovement's
  `avg_lead_time_weeks`). Store in **weeks** (not months — simpler, one fewer
  conversion than AvgMovement's report used).
- Do **not** compute or store `pending_qty`/on-order — out of scope, see above.

Unmatched item codes (no matching `Item.code` in SOPS) are skipped, not created —
this importer only enriches existing catalogue items, it never creates new ones.

## Model changes (`models.py`)

Add to `Item`:
```python
supplier = db.Column(db.String(255))  # most-frequent supplier from PO history, CSV-sourced
lead_time_weeks = db.Column(db.Float, default=0.0)  # avg lead time in weeks, CSV-sourced
```

## Migration

New `scripts/migrate_add_item_supplier_lead_time.py`, following the existing
pattern (see `scripts/migrate_add_item_max_level.py` for the shape: add column
if not exists, idempotent). Add the matching self-heal entry to
`app.py::ensure_schema_columns()`, same convention as every prior Item column
addition (`max_level`, `is_stocked_finished_good`, etc.) — do **not** run this
migration against the real `instance/sops.db`; that's a live-data step held for
Tebello's go-ahead, same convention as every past schema change here.

## Service

New `services/po_by_item_importer.py`:
```python
def import_supplier_lead_time_from_csv(csv_path) -> tuple[int, int]:
    """Parse OutstandingPOByItemReport.csv, update Item.supplier /
    Item.lead_time_weeks for matching item codes. Returns (updated_count,
    unmatched_count). Never creates new items, never touches qty_on_hand,
    qty_on_order, or any other Item field."""
```
Reuse the shadow-copy-before-read protocol from AvgMovement's
`safe_copy_for_reading()` (avoids reading a potentially locked live file) —
copy that helper in rather than importing across projects (no shared package
between SOPS and AvgMovement today, and this consolidation is explicitly about
retiring AvgMovement, not creating a new cross-project dependency).

## Route (`routes/items.py`)

New route, mirroring `import_csv()`'s shape but upload-only (no "seed from
default file" option — there's no existing default path for this CSV in SOPS
today, don't invent one):

```python
@items_bp.route('/items/import-supplier-leadtime', methods=['GET', 'POST'])
def import_supplier_leadtime():
    ...
```
POST handling: save uploaded file to `UPLOAD_FOLDER` (same as existing import),
call `import_supplier_lead_time_from_csv()`, flash a result summary
(`"{updated} items updated, {unmatched} item codes not found in catalogue"`),
redirect to `items.catalogue`.

## Template

New `templates/items/import_supplier_leadtime.html`, modeled on
`templates/items/import.html` (single upload form, no default-seed option,
plus a "CSV Format Requirements" card documenting the expected columns:
Date, Reference, Order No., Supplier, Delivery Date, Status, Qty).

**Entry point:** add a second button next to the existing "Import CSV" button
on the Inventory page header (`templates/items/catalogue.html`) — e.g.
"Import Supplier/Lead Time" — linking to the new route.

## Stock Report changes

- `routes/reports.py::stock_data()` — add `'supplier': item.supplier or '-'`
  and `'lead_time_weeks': round(item.lead_time_weeks or 0.0, 1)` to the
  per-item dict.
- `routes/reports.py::stock_export_csv()` — add `Supplier` and
  `Lead Time (weeks)` columns to the CSV header and row output.
- `templates/reports/stock.html` — add two Tabulator columns after
  `Reorder Point` (or wherever reads best next to the existing columns):
  `{ title: 'Supplier', field: 'supplier' }` and
  `{ title: 'Lead Time (wks)', field: 'lead_time_weeks', formatter: 'number' }`.

## Item detail page (`templates/items/detail.html`)

Add two rows to the left-hand "identity" table (alongside Code/Description/
Category/Status, not the pricing/quantity table on the right):
```html
<tr><td class="detail-label">Supplier</td><td class="detail-value">{{ item.supplier or '-' }}</td></tr>
<tr><td class="detail-label">Lead Time</td><td class="detail-value">{{ "%.1f"|format(item.lead_time_weeks or 0) }} weeks</td></tr>
```
Read-only display — these fields are CSV-sourced only, not editable via the
Edit Item modal (consistent with how `avg_cost`/`last_cost` etc. are display-only
outside of CSV import — no new form fields needed).

## Tests

- `services/po_by_item_importer.py`: unit tests with a small fixture CSV
  (mirroring the real format) — most-frequent supplier wins on a tie-breakable
  case, lead-time averaging, unmatched codes skipped (not created), missing/
  malformed delivery dates excluded from the average, existing `qty_on_hand`
  and `qty_on_order`-related fields untouched by this importer.
- `routes/items.py`: request test for the new import route (GET renders form,
  POST with a valid file updates matching items and flashes a summary).
- `routes/reports.py`: extend existing stock report tests to assert the new
  `supplier`/`lead_time_weeks` fields appear in `stock_data()` JSON and in the
  CSV export.

## Explicitly out of scope (do not implement)

- On Order / pending PO quantity from the Sage CSV (see Context above).
- Any change to `services/demand.py` or the existing PO-based on-order calc.
- Retiring/archiving the `8. AvgMovement` project folder — tracked as a
  separate hub-level decision (ADR), not part of this SOPS-side spec.
- A "seed from default file" option for this import (no existing convention
  for where this CSV would live in SOPS's `data/` folder).
