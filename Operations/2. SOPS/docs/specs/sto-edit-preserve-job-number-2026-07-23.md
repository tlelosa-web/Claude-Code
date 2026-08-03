# Spec — Stock Order edit must preserve (and allow editing) per-line FM/Job numbers

**Date:** 2026-07-23
**Type:** Bug fix (Pattern 2) + small UI addition
**Owner:** Tebello Lelosa
**Status:** Approved — design confirmed (editable column)

## Problem

STO0027 (built from SO4756) showed no Job Numbers even though all 14 of its
source sales-order lines carry `FM4247`. Root cause is two-layered:

1. **Data-loss bug (primary / recurrence vector).** The Stock Order edit flow
   silently discards every line's `job_number`:
   - `templates/stock_orders/edit.html` has no FM/Job column. Its `syncJSON()`
     builds `lines_json` from only `item_code`, `description`, `qty`, `notes`
     (edit.html:147-152).
   - `routes/stock_orders.py::edit_order` (POST) deletes all lines
     (stock_orders.py:443) and recreates them **without** `job_number`
     (stock_orders.py:452-458).
   So *any* edit of an STO — even changing one quantity — wipes all line job
   numbers to `NULL`. STO0027 went Open→Released (edited in between), which is
   how its job numbers were lost.

2. **No post-build way to assign a stock-line FM number.** `job_number` is only
   ever written at build time in `routes/sales_orders.py::build_bom`
   (sales_orders.py:282 → copied to the StockOrderLine at :457). For fan lines
   it is required; for stock lines it is optional and often blank at build. The
   STO's displayed `job_numbers` is derived live from its own lines
   (`models.py:180-187`), so blank lines → empty display, with no UI to fix it.

The build-time snapshot itself is correct and is **not** changed by this spec.

## Scope of the fix

Confined to the STO edit flow. Add an **editable** FM/Job column so an edit
both preserves existing job numbers and lets the user assign/correct them.

### Files

1. `routes/stock_orders.py` — `edit_order` POST loop: set
   `job_number=str(ld.get('job_number', '')).strip() or None` on each recreated
   `StockOrderLine`.
2. `templates/stock_orders/edit.html`:
   - Add a `<th>FM / Job No.</th>` header.
   - Existing rows: add a `.job-input` text input pre-filled with
     `{{ line.job_number or '' }}`.
   - `addItem()` row template: add the same (empty) `.job-input` cell.
   - `syncJSON()`: include `job_number: row.querySelector('.job-input').value.trim()`.
3. `tests/test_stock_orders.py` — regression test.

Column order (thead + both row templates must match):
`Code | Description | FM / Job No. | Qty | Notes | (remove)`.

### Out of scope
- `build_bom` snapshot logic (already correct).
- STO `job_numbers` derived property (already correct once lines carry values).
- Print/consolidation templates (already read `line.job_number`; only benefit).
- Any schema change (none needed — `stock_order_line.job_number` already exists).

## Acceptance criteria

- Editing an STO and saving preserves the `job_number` on every unchanged line.
- A blank stock line's FM number can be typed in the edit screen and persists.
- Clearing an FM number in the edit screen persists as `NULL`.
- New regression test fails against the pre-fix code and passes after.
- Full `pytest` suite stays green; `black`/`ruff` clean.

## Data remediation (already done, 2026-07-23)

STO0027's 14 lines were backfilled to `FM4247` from their source SO lines
(DB backed up first to `instance/sops.db.pre-fm4247-backfill-20260723-072539`).
This spec prevents recurrence.
