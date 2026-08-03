# Spec: Open/Active Filter — Dashboard + SO/WO/STO/PO Lists

Owner: Tebello Lelosa | Written: 2026-07-07 | Status: Shipped — Batch 14 (2026-07-08), commit `bd25fcf`

## Goal
Dashboard surfaces open Sales Orders; List pages for SO/WO/STO/PO gain an
"All / Open only" toggle. Default view unchanged (All) — filter is opt-in,
per Tebello's decision.

## Active-status definition (per Tebello's decision)
| Type | Active/Open statuses | Excluded |
|---|---|---|
| SalesOrder | Draft, Open | Closed |
| WorksOrder | Open, In Progress | Complete, Cancelled |
| StockOrder | Open | Complete, Cancelled |
| PurchaseOrder | Draft, Open, Partially Received | Received, Cancelled |

## Changes

1. **New `services/order_filters.py`** — single source of truth for the
   table above (`SO_ACTIVE`, `WO_ACTIVE`, `STO_ACTIVE`, `PO_ACTIVE` tuples)
   so the 4 route files and dashboard don't duplicate magic strings.

2. **`routes/sales_orders.py`, `works_orders.py`, `stock_orders.py`,
   `purchase_orders.py` — `list_orders()`**: read `?view=open|all`
   (default `all`, unchanged behavior). When `open`, filter query by the
   matching active-status tuple. Pass `view` to template for toggle state.

3. **4 list templates**: add a small "All / Open only" link toggle near
   the page header (reuses existing `.btn`/`.badge` CSS, no new deps,
   stays offline-first). Toggle preserves state via URL query param —
   no JS/localStorage needed.

4. **`routes/dashboard.py`**:
   - Add `open_sos` query (Draft+Open SalesOrders) and a new **"Open
     Sales Orders"** table section (so_number, customer, delivery date,
     status, link to detail) — directly answers "dashboard should show
     open sales orders."
   - Existing "Recent Works Orders Activity" table: no change to query
     (stays recent-5-any-status) — it's an activity feed, not a queue;
     flagging this assumption for confirmation below.
   - Existing stat cards unchanged (pending_sos card already counts
     Draft only — leave as-is unless you want it to match the new
     Draft+Open definition too).

5. **`templates/dashboard.html`**: new "Open Sales Orders" card/table,
   styled like the existing Recent WO Activity table.

6. **Tests**: `tests/test_dashboard.py` (new) — open_sos excludes Closed
   SOs. Extend `test_sales_orders.py`/`test_works_orders.py`/
   `test_stock_orders.py`/`test_purchase_orders.py` with `?view=open`
   cases confirming excluded statuses are hidden and default `view=all`
   is unchanged (no regression).

7. **`docs/todo.md`**: log as Batch 14 on completion, per project
   convention.

## Open question flagged to Tebello
Should the Dashboard's "Recent Works Orders Activity" table also default
to Open/In-Progress only (dropping Complete/Cancelled from the feed), or
stay as a full recent-activity log regardless of status? Assumed **stay
as-is** above since it's a 5-row activity feed, not a work queue — but
this is a one-line change if you want it filtered too.

## Out of scope
- No schema/migration changes (all statuses already exist as columns).
- No change to default list-page behavior (All remains default per
  your choice) — this is additive, not a breaking change.
