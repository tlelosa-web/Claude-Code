# Spec — AMU + suggested Min/Max reorder levels (from Sage ItemMovementReport.csv)

**Date:** 2026-07-17 | **Owner:** Tebello Lelosa | **Status:** Approved, ready to build

## Context

Continuation of the AvgMovement reuse work (see Batch 32,
`docs/specs/supplier-lead-time-import-2026-07-17.md`). AvgMovement also
computes AMU (average monthly usage) and automated Min/Max reorder-level
suggestions from Sage's `ItemMovementReport.csv` transaction history — a
capability SOPS doesn't have (`Item.reorder_point`/`max_level` are manually
set by Tebello, only 11 of 3,126 items have them set at all). Tebello wants
this ported into SOPS. Retiring AvgMovement stays on hold regardless (prior
decision, not reopened here).

`data/ItemMovementReport.csv` already sits in the SOPS project root (unused
by any code today) — same file AvgMovement's algorithm reads, no need to
source it from AvgMovement's folder.

Confirmed scope:
1. **Separate suggested fields — do NOT write into the existing
   `reorder_point`/`max_level`.** Those are manually-curated operational
   fields the Stock Report's "Below Reorder Point" filter already depends
   on; overwriting them from an automated import would clobber the 11
   items Tebello already set by hand, and silently change what "below
   reorder" means for them. New fields (`amu`, `suggested_min`,
   `suggested_max`) are purely informational — Tebello copies a suggestion
   into the real fields manually if they agree with it. No "apply
   suggestion" button — not asked for, don't build it.
2. **Reuse the already-stored `Item.lead_time_weeks` (Batch 32) for the
   Min/Max formula — do NOT re-parse `OutstandingPOByItemReport.csv` a
   second time in this importer.** AvgMovement's original script computed
   lead time itself as part of the same pipeline run; SOPS already has
   this value on `Item` from the Supplier/Lead Time import, so reuse it
   instead of recomputing the same number two different ways in two
   different importers — that would be the exact "two processes, same
   thing" problem this whole thread of work exists to avoid. If
   `lead_time_weeks` is 0 (not yet imported), fall back to a 0.5-month
   floor, matching AvgMovement's own floor behavior.
3. **Surface location:** Item detail page + Stock Report, same pattern as
   Batch 32.
4. **Import mechanism:** another new, separate manual CSV import (not
   folded into the existing Items or Supplier/Lead-Time imports) — same
   established pattern.

## Data source & algorithm

Reference implementation to adapt (read-only reference — copy/adapt the
logic, do not cross-project `import`):
`8. AvgMovement/4_Scripts/item_movement_report.py` — specifically
`parse_csv()`, `round_amu_half()`, and the AMU/Min/Max portion of
`aggregate_items()` (ignore the Supplier/Cost/Current-Stock/On-Order
enrichment in that function — already covered by Batch 32 or explicitly
out of scope, see below).

**Parsing `ItemMovementReport.csv`** (`services/movement_history_importer.py`,
new file):
- Format: title row, skip 3 metadata rows, then repeating blocks of an
  item-name row (`Code - Description` or just `Code`) followed by
  transaction rows `Date, Reference, Description, Customer/Supplier, Qty`,
  ending in a `Total for Item:` row (identical shell shape to the PO-by-item
  file from Batch 32, different columns).
- Per transaction row: `is_purchase = (Description == "Supplier Invoice")`,
  `is_sale = (Description == "Tax Invoice")`. Accumulate `total_purchased`
  (sum of `abs(qty)` where `is_purchase`) and `total_sold` (sum of
  `abs(qty)` where `is_sale`) per item code. Track each item's transaction
  date range (min/max date) for the period calculation.
- `period_months = max(1, (max_date.year - min_date.year) * 12 +
  (max_date.month - min_date.month))` per item (matches AvgMovement
  exactly — a single-transaction or same-month item gets `period_months = 1`).
- `amu_raw = max(total_purchased, total_sold) / period_months`.
- `amu = round_amu_half(amu_raw)`:
  ```python
  def round_amu_half(val):
      if val <= 0:
          return 1.0
      rounded = math.ceil(val * 2) / 2
      return max(round(rounded, 1), 1.0)
  ```
  (copy this helper in verbatim — it's a small, self-contained rounding
  rule, faithfully port it rather than re-deriving).
- `lead_time_months = round(item.lead_time_weeks / 4.33, 1) if
  item.lead_time_weeks > 0 else 0.0`, then floored to `max(lead_time_months,
  0.5)`.
- `min_qty = round(amu * lead_time_months)`; if `min_qty <= 0`, `min_qty = 1`.
- `max_qty = min_qty + round(amu * 2)`; if `max_qty <= min_qty`,
  `max_qty = min_qty * 2`.

**Only process item codes that actually appear in the CSV's parsed item
blocks** (whether or not they had a purchase/sale transaction — an item
block with zero purchase/sale rows still gets the `amu_raw <= 0 → amu = 1.0`
floor, faithfully matching AvgMovement's behavior). Item codes in the CSV
that don't match any `Item.code` in the catalogue are skipped, not created
(same convention as Batch 32). Items **not present in the CSV at all are
left completely untouched** — their `amu`/`suggested_min`/`suggested_max`
stay at whatever they already were (0.0 by default, meaning "not
computed"), not force-set to the AMU-floor values. This is a deliberate
difference from AvgMovement's own report (which included every catalogue
item, computing a floor AMU=1.0 for items with zero history) — SOPS should
only surface a suggestion for items the CSV actually has data for, not
manufacture one for items with no presence in the report at all.

**Explicitly out of scope (do not implement):** Supplier, Cost, Current
Stock, On Order — all either already covered (Batch 32) or explicitly
excluded (On Order, same reasoning as Batch 32: SOPS's own live PO-based
`qty_on_order` stays the only source).

## Model changes (`models.py`)

Add to `Item`:
```python
amu = db.Column(db.Float, default=0.0)  # average monthly usage, CSV-sourced; 0.0 = not computed
suggested_min = db.Column(db.Float, default=0.0)  # AMU-based suggested reorder point, CSV-sourced, informational only
suggested_max = db.Column(db.Float, default=0.0)  # AMU-based suggested max level, CSV-sourced, informational only
```

## Migration

New `scripts/migrate_add_item_amu_minmax.py`, same idempotent
add-column-if-not-exists pattern as
`scripts/migrate_add_item_supplier_lead_time.py`. Matching self-heal
entries in `app.py::ensure_schema_columns()`. **Do not run against
`instance/sops.db`** — held for Tebello's go-ahead, same standing
convention as every prior schema change in this repo.

## Service

New `services/movement_history_importer.py`:
```python
def import_amu_minmax_from_csv(csv_path) -> tuple[int, int]:
    """Parse ItemMovementReport.csv, update Item.amu / Item.suggested_min /
    Item.suggested_max for matching item codes present in the CSV. Returns
    (updated_count, unmatched_count). Never creates items, never touches
    qty_on_hand, qty_on_order, reorder_point, or max_level. Items not
    present in the CSV are left untouched (not force-defaulted)."""
```
Copy in the shadow-copy-before-read protocol, same as
`services/po_by_item_importer.py::_safe_copy_for_reading()` (don't import
across the two service files either — small enough to duplicate, matching
how Batch 32 already duplicated it from AvgMovement rather than sharing a
module).

## Route (`routes/items.py`)

New route, same upload-only shape as Batch 32's
`import_supplier_leadtime`:
```python
@items_bp.route('/items/import-movement-history', methods=['GET', 'POST'])
def import_movement_history():
    ...
```
Flash summary: `"{updated} items updated, {unmatched} item codes not found
in catalogue."`

## Template

New `templates/items/import_movement_history.html`, modeled on
`templates/items/import_supplier_leadtime.html` (upload-only form + CSV
Format Requirements card documenting: Date, Reference, Description,
Customer/Supplier, Qty columns; explain that Description of "Supplier
Invoice"/"Tax Invoice" drives the purchased/sold split; note that Min/Max
reuses the item's already-imported Lead Time, and this import does not
touch Supplier or Lead Time itself).

**Entry point:** third button on the Inventory page header
(`templates/items/catalogue.html`), alongside "Import CSV" and "Import
Supplier/Lead Time" — e.g. "Import Movement History".

## Stock Report changes

- `routes/reports.py::stock_data()` — add `'amu': round(item.amu or 0.0, 1)`,
  `'suggested_min': item.suggested_min or 0`,
  `'suggested_max': item.suggested_max or 0` to the per-item dict.
- `routes/reports.py::stock_export_csv()` — add `AMU`, `Suggested Min`,
  `Suggested Max` columns to the CSV header and row output.
- `templates/reports/stock.html` — add three Tabulator columns after the
  existing `Lead Time (wks)` column: `{ title: 'AMU', field: 'amu',
  formatter: 'number' }`, `{ title: 'Suggested Min', field:
  'suggested_min', formatter: 'number' }`, `{ title: 'Suggested Max',
  field: 'suggested_max', formatter: 'number' }`.

## Item detail page (`templates/items/detail.html`)

Add to the left-hand identity table, after the Supplier/Lead Time rows
added in Batch 32:
```html
<tr><td class="detail-label">AMU (avg. monthly usage)</td><td class="detail-value">{{ "%.1f"|format(item.amu or 0) }}</td></tr>
<tr><td class="detail-label">Suggested Min / Max</td><td class="detail-value">{{ item.suggested_min or 0 }} / {{ item.suggested_max or 0 }}</td></tr>
```
Read-only display, CSV-sourced only — same treatment as Supplier/Lead Time.
Do not add these to the Edit Item modal or the Adjust Stock & Levels modal
(those remain scoped to the real, manually-set `reorder_point`/`max_level`/
`reorder_qty`, per Batch 25 — unchanged by this spec).

## Tests

- `services/movement_history_importer.py`: unit tests with a small fixture
  CSV mirroring the real format — purchased/sold split by Description,
  period_months calculation (single-month and multi-month cases),
  `round_amu_half()` rounding behavior (including the `<=0 → 1.0` floor
  case), Min/Max formula using a stubbed `Item.lead_time_weeks` (both a
  set value and the 0/unset floor-to-0.5-months case), unmatched codes
  skipped not created, items absent from the CSV left untouched (still
  0.0 after import, not force-defaulted), `qty_on_hand`/`qty_on_order`/
  `reorder_point`/`max_level` all untouched.
- `routes/items.py`: request test for the new import route (GET renders
  form, POST with a valid file updates matching items and flashes a
  summary).
- `routes/reports.py`: extend existing stock report tests to assert
  `amu`/`suggested_min`/`suggested_max` appear in `stock_data()` JSON and
  in the CSV export.

## Explicitly out of scope (do not implement)

- Writing into `reorder_point`/`max_level`/`reorder_qty` (see Context #1).
- Re-parsing `OutstandingPOByItemReport.csv` for lead time (see Context #2)
  — reuse `Item.lead_time_weeks`.
- Supplier, Cost, Current Stock, On Order (already covered or excluded,
  see Data source & algorithm).
- An "apply suggestion to reorder_point/max_level" button or any other UI
  beyond read-only display — not asked for.
- Retiring/archiving `8. AvgMovement` — separate hub-level decision, not
  reopened by this spec.
