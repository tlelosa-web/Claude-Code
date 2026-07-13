# Spec: CSV Item Import — Remove Quantity-Overwrite Path

**Status:** Confirmed — Tebello approved 2026-07-14, proceed to build.
**Origin:** Raised during CSV-upload/Stock-Report impact review (docs/session-log.md, 2026-07-14). No prior research doc — small, self-contained decision.

## Problem

`services/item_importer.py` has two import functions, selected by a "Preserve Stock Quantities"
checkbox on `templates/items/import.html` that defaults to **unchecked**:

- `import_items_from_csv()` — overwrites `Item.qty_on_hand` for every existing item from the CSV's
  "Qty on Hand" column, no diff/preview.
- `import_items_from_csv_skip_quantities()` — updates description/category/cost/price/active only;
  never touches `qty_on_hand` for existing items (still sets initial qty for brand-new codes).

Now that SOPS owns the full stock lifecycle (WO/STO issue, PO receipt, manual adjust, reversals —
all through `stock_service` with an audit trail), the CSV must never be a second source of truth for
`qty_on_hand`. A checkbox that defaults to the wrong (overwriting) behavior is a standing risk: one
missed click silently reverts live stock movements back to a stale Sage export.

## Decision (confirmed with Tebello)

Remove the toggle. CSV import becomes catalogue-metadata-only, unconditionally — no code path in the
app may overwrite `qty_on_hand` for an existing item via CSV import ever again. New item codes still
get their initial quantity seeded from the CSV (unchanged — there's no existing quantity to protect).

Bulk stock recounts, if ever needed, are a separate future feature built on the already-audited
`stock_service.adjust()` path (Item Detail → Adjust) — explicitly out of scope here.

## Changes

1. **`services/item_importer.py`**: delete `import_items_from_csv` (the overwriting variant).
   Rename `import_items_from_csv_skip_quantities` → `import_items_from_csv` (only one behavior
   remains, so the qualifier is meaningless). Docstring should state plainly that this never
   modifies `qty_on_hand` for an existing item.
2. **`routes/items.py`** (`import_csv()`, ~line 88-114): drop the `preserve_quantities` /
   `import_func` selection — always call the single remaining `import_items_from_csv`. Update the
   two flash messages accordingly (drop the "(quantities preserved)" branch — it's now always true).
3. **`app.py`** (first-run bootstrap, ~line 93): update the import to the same function/name.
   No behavior change on a first run (every item is new), just collapses to one code path.
4. **`templates/items/import.html`**: remove both "Preserve Stock Quantities" checkboxes (upload
   form ~line 21-31, seed form ~line 44-54) and the JS that syncs the seed-form hidden input
   (~line 91-103, and the now-unused hidden input at line 57). Replace with a short static note:
   "This only updates item details — description, category, cost, price, active status. Stock
   quantities are managed inside SOPS and are never changed by import." Also drop the
   `preserve_quantities` hidden input from the seed form entirely (no longer a param the route reads).
5. **`tests/test_item_importer.py`**: currently only exercises the now-deleted overwriting function
   (4 tests, importing `import_items_from_csv` expecting overwrite behavior). Update all 4 to
   exercise the renamed function and assert the *preserved* semantics; add one explicit regression
   test — existing item's `qty_on_hand` is unchanged after import even when the CSV row shows a
   different quantity for that code.

## Non-goals

- No change to `stock_service.adjust()` or any other stock-mutation path.
- No new "bulk recount" feature — noted as a possible future ask only.
- No schema change.

## Test plan

- `tests/test_item_importer.py` full rewrite per above — existing-item update preserves
  `qty_on_hand`; new-item insert still seeds `qty_on_hand` from the CSV; inactive rows still skipped;
  category/cost/price/active still update on existing items.
- Full suite green, no regressions (currently 147 tests).
- Manual: load `/items/import`, confirm no checkbox is present, upload the sample CSV, confirm
  flash message and catalogue values look right, confirm `git grep -n "preserve_quantities"` /
  `git grep -n "import_items_from_csv_skip_quantities"` return nothing repo-wide.

## Sequencing

Single atomic commit — this is one cohesive rename + call-site update + template edit + test
rewrite, not a multi-stage feature.
