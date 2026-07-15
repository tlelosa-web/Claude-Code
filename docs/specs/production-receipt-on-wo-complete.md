# Spec — Production Receipt on Works Order Complete

Status: Pending approval
Author: Claude (Software/AI domain), confirmed scope with Tebello via AskUserQuestion (2026-07-15)

## Problem

`mark_complete()` (`routes/works_orders.py`) deducts every COMPONENT BOM line's stock but
explicitly skips `ASSEMBLY_ITEM` lines ("must never be issued from stores" — correct, that
line represents the finished fan being built, not a component consumed from stores). The
flip side was never built: completing a WO never adds the built unit back into
`Item.qty_on_hand` for the assembly item itself. SOPS currently has no finished-goods
receipt step at all.

Surfaced by Tebello reviewing WO0001 (SO4698), where the assembly item MFP3150752 showed
`qty_on_hand = -1.0` (traced to a 2026-05-28 CSV `OPENING` import row, not a SOPS bug) with
no path for that number to ever move in the direction of "we built one."

## Decision (confirmed via AskUserQuestion)

1. **Build a real production-receipt step** — WO Complete increments the assembly item's
   `qty_on_hand`; WO Reopen reverses it. Not just a display fix.
2. **Scoped to flagged items only**, not every assembly line. New
   `Item.is_stocked_finished_good` boolean (default `False`, opt-in per catalogue item).
   Rationale: many "assembly" lines in this catalogue are one-off, made-to-order
   configurations (e.g. `MFA5000754PTL - ... (Plate Mount) Extraction`) that are never
   resold as a standalone stocked unit — auto-incrementing those would leave phantom
   balances in the Items Catalogue / Stock Report that never move again. Only items
   Tebello explicitly flags as real stocked/sellable finished goods get the receipt.

## Scope

### 1. `models.py`
- `Item.is_stocked_finished_good = db.Column(db.Boolean, default=False)`

### 2. `scripts/migrate_add_item_is_stocked_finished_good.py`
- New migration script, same shape as `scripts/migrate_add_item_max_level.py`
  (`ALTER TABLE item ADD COLUMN is_stocked_finished_good BOOLEAN DEFAULT 0`, idempotent
  check via `db.inspect`).
- Matching `ensure_schema_columns()` self-heal entry in `app.py`.
- **Not run against `instance/sops.db` by this batch** — same convention as Batch 24's
  schema migrations (run against the real DB only on Tebello's deliberate go-ahead).

### 3. `services/stock_service.py`
Two new functions, mirroring the existing `receipt()` / `reverse_issue()` pattern exactly:
- `produce(item_id, qty, reference, notes="", created_by="System")` — adds `qty` to
  `item.qty_on_hand`, logs a **new** `movement_type='PRODUCTION'` (positive `qty_change`).
  Kept distinct from `RECEIPT` so the audit trail can tell "built in-house from a WO" apart
  from "bought in from a supplier PO" — same rationale Batch 17 used to keep `REVERSAL`
  distinct from `RECEIPT`.
- `reverse_production(item_id, qty, reference, notes="", created_by="System")` — subtracts
  `qty` from `item.qty_on_hand`, logs `movement_type='REVERSAL'` (**reuses** the existing
  REVERSAL type, negative `qty_change` this time — REVERSAL already means "undoing a
  stock-affecting effect of an order that's being reopened," direction-agnostic; the
  `qty_change` sign already carries the direction in the UI). Avoids adding a second new
  movement-type string just for the reverse case.

### 4. `routes/works_orders.py`
- `mark_complete()`: inside the existing per-`bom_line` loop, where `ASSEMBLY_ITEM` lines
  are currently `continue`d — before continuing, check `bom_line.item.is_stocked_finished_good`.
  If `True`, call `produce(item_id=bom_line.item_id, qty=bom_line.qty_required, reference=wo.wo_number, notes=f"Produced by {wo.wo_number} (...)", created_by=...)` and set
  `bom_line.qty_issued = bom_line.qty_required` (reusing the existing `qty_issued` column on
  the assembly line itself to record "qty produced," mirroring exactly how component lines
  already use it to record "qty issued" — keeps `reopen_order()`'s logic symmetric instead
  of needing a new column). Then `continue` as before (still never calls `issue()` for this
  line).
- `reopen_order()`: in the existing `if wo.status == 'Complete': ...` block, add an
  `ASSEMBLY_ITEM` branch (currently unconditionally skipped) — if
  `bom_line.item.is_stocked_finished_good` and `bom_line.qty_issued > 0`, call
  `reverse_production(item_id=bom_line.item_id, qty=bom_line.qty_issued, reference=wo.wo_number, notes=f"Production reversed on reopen of {wo.wo_number}", created_by=...)` and reset
  `bom_line.qty_issued = 0.0`.
- Both changes are additive inside existing loops — no new route, no template routing change.

### 5. `routes/items.py` / `templates/items/detail.html` (Edit Item modal)
- `update_item()`: read `is_stocked_finished_good = request.form.get('is_stocked_finished_good') == 'on'`, persist alongside the existing `active` boolean (same pattern).
- Edit Item modal: new checkbox next to the existing "Active" one:
  `<input type="checkbox" name="is_stocked_finished_good" {% if item.is_stocked_finished_good %}checked{% endif %}> Stocked Finished Good`.

### 6. `templates/reports/movements.html` + `templates/items/detail.html`
- Add `<option value="PRODUCTION">PRODUCTION</option>` to the Movement Report type filter
  (mirrors the existing `REVERSAL` option added in Batch 17).
- Add a badge color for `PRODUCTION` in the Item detail movement-history table
  (`{% elif m.movement_type == 'PRODUCTION' %}var(--brand-primary);` — orange, distinct from
  RECEIPT's green, signalling "built here" vs "bought in"). REVERSAL's existing badge/filter
  entries need no change — already covers the reverse-production case.

### 7. `templates/works_orders/detail.html`
- No required change — the assembly row already renders `qty_on_hand`; once flagged items
  start receiving production credit, that number will simply reflect reality instead of
  standing still. Optionally could show "(produced: N)" next to the assembly row once
  `qty_issued > 0` there, mirroring the "(short N)" convention used elsewhere — flagged as a
  nice-to-have, not required for the core fix.

### 8. Tests
- `tests/test_stock_service.py`: `produce()` / `reverse_production()` unit tests (movement
  type, direction, `qty_after` correctness) — same shape as existing `issue`/`receipt`/
  `reverse_issue` tests in that file.
- `tests/test_works_orders.py` (or wherever `mark_complete`/`reopen_order` are already
  tested): WO Complete on a flagged assembly item increments `qty_on_hand` by
  `qty_required` and logs a `PRODUCTION` movement; WO Complete on an **unflagged** assembly
  item leaves `qty_on_hand` untouched (regression guard — this is the default/current
  behavior and must not change); Reopen after a flagged-item Complete reverses exactly what
  was produced and logs a `REVERSAL` movement.
- `tests/test_items.py`: Edit Item modal round-trips `is_stocked_finished_good` (extend the
  existing `update_item` test, same shape as the `active` checkbox test).

## Explicitly out of scope
- Not retroactively flagging any existing catalogue items — `is_stocked_finished_good`
  ships `False` for everything; Tebello flags items manually as needed.
- Not touching Stock Order (`StockOrder`/`StockOrderLine`) completion — STOs don't build
  anything, this is a Works Order (assembly) concept only.
- Not changing the demand-netting (`services/demand.py`) shortfall calc — flagged items'
  `qty_on_hand` will simply be more accurate going forward; no netting-formula change needed.
- Not backfilling `MFP3150752`'s `-1.0` opening balance — that's pre-existing Sage import
  data, unrelated to this feature; a separate manual data decision for Tebello if wanted.

## Acceptance criteria
- [ ] Completing a WO with an assembly item flagged `is_stocked_finished_good=True`
      increments that item's `qty_on_hand` by the assembly line's `qty_required` and logs a
      `PRODUCTION` movement.
- [ ] Completing a WO with an **unflagged** (default) assembly item leaves `qty_on_hand`
      untouched — identical to today's behavior.
- [ ] Reopening a Complete WO that produced flagged-item stock reverses exactly that amount
      via a `REVERSAL` movement, resetting the line back to un-produced.
- [ ] Edit Item modal can toggle `is_stocked_finished_good` per catalogue item.
- [ ] Movement Report type filter and Item detail movement-history badges both recognize
      `PRODUCTION`.
- [ ] Full test suite green, no regressions.
- [ ] Offline-first re-verified (no new CDN/font references — none expected, this is
      backend + existing-template-pattern only).
