# Spec: Shortfall/Availability Display on Build Works Pack (`build_bom.html`)

**Status:** Draft — awaiting Tebello's confirmation before build.
**Depends on:** Enhancement 3 / `services/demand.py` (shipped Batch 18) — no new logic, wiring only.
**Origin:** Known gap flagged at the end of Batch 18 (`docs/todo.md`), scoped in chat 2026-07-14.

## Problem

`build_bom()` in `routes/sales_orders.py` is the route behind the primary "Build Works Pack" page —
where most orders are actually created from a Sales Order. Its `catalogue_json` (GET branch,
~line 452, and the POST error-path re-render, ~line 438) is built as a bare
`{id, code, description}` dict. None of the Batch 18 demand-netting work reaches this page: a user
adding a component here gets no on-hand / on-order / committed / shortfall signal at all. The
netted `available_qty` only shows up later, on the WO/STO **edit** page (`bom_builder.js`), after
the order already exists.

## Scope

Wire the existing `item_to_bom_json()` / `services/demand.py` bulk functions into this page, the
same way commit `03109bf` (Batch 18) wired them into the edit-page `bom_builder.js`. No new demand
logic — this is data plumbing plus a template/JS display change.

## Changes

1. **`routes/sales_orders.py` `build_bom()`**:
   - GET branch (~line 448-461): replace the bare `catalogue_json` comprehension with bulk calls —
     `get_qty_on_order_bulk()`, `get_qty_committed_bulk()`, `get_next_po_due_bulk()` over the active
     catalogue's item ids (no `exclude_wo_id`/`exclude_sto_id` — the SO has no WO/STO yet at this
     point) — then map each item through the existing `item_to_bom_json()`.
   - POST error-path re-render (~line 433-445): rebuilds a second, even-thinner `catalogue_json` on
     exception. Must get the identical treatment, or it goes stale the moment this ships and
     silently drops shortfall info the one time a user actually needs to see the error state.
2. **`templates/sales_orders/build_bom.html`** (JS only, no new endpoints):
   - Search results (~line 235-241, `search-result-item` template string): append available qty and
     the "on order, due `<date>`" hint when `qty_on_order > 0` — same wording already used on the
     edit page.
   - Selected-item display panel (`selectedDisplay`/`selectedCode`/`selectedDesc`, ~line 261-270):
     surface `available_qty` before the user commits a quantity.
   - `addComponent()` (~line 275-347): compare the entered qty against `item.available_qty`
     (`shortfall = max(0, qty - available_qty)`, matching `bom_builder.js:293`'s formula) and apply
     the same amber-flag treatment to the new table row when a shortfall exists.
3. **Tests**: extend `tests/test_bom_builder.py` to assert `build_bom()`'s served `catalogue_json`
   carries `qty_on_hand`/`qty_on_order`/`qty_committed`/`available_qty`/`next_po_due` per item —
   payload-presence check, not visual (the amber-flag rendering itself isn't unit-testable without a
   browser, same accepted limitation as `test_resizable_columns.py`).

## Non-goals

- No change to the demand-netting formula or `services/demand.py` itself.
- No change to the WO/STO edit-page `bom_builder.js` (already wired, Batch 18).
- No schema change.

## Test plan

- `catalogue_json` payload test (per above) for both the GET and POST-error-path renders.
- Full suite green, no regressions (currently 148 tests).
- Manual: open Build Works Pack for a Sales Order, search a component with a known shortfall (or
  known on-order PO), confirm the hint/amber flag appears; add it to the table and confirm the row
  reflects it; confirm an item with sufficient `available_qty` shows no flag.

## Sequencing

Single atomic commit — same shape as Batch 18's commit `03109bf`, which did the identical wiring for
the edit-page equivalent.
