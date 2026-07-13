## Task: Payment Status at intake, editable Delivery Date, Reopen SO/WO/STO, resizable list columns

**Domain:** Software / AI
**Date:** 2026-07-13
**Requested by:** Tebello

**Goal:** Four related changes to the order-management screens:
1. Capture Payment Status at Sales Order upload/review time (currently only settable after save, via a separate detail-page dropdown), and add a "Partially Paid" option.
2. Make `SalesOrder.delivery_date` editable after save (currently fixed at parse time forever), and standardize its **display** format to `DD/MM/YYYY` everywhere (currently inconsistent — ISO on list/detail/dashboard pages, `DD/MM/YYYY` on print documents).
3. Add a "Reopen" action for Sales Orders, Works Orders, and Stock Orders, reversing any stock that was issued when the record was originally completed.
4. Add drag-to-resize column widths on the four plain-HTML list pages (SO/WO/STO/PO), and stop date cells from wrapping onto two lines.

**Decisions confirmed with Tebello (2026-07-13, via AskUserQuestion + code audit):**
- **STO stock-deduction gap** — code audit found `StockOrder`/`complete_order()` never calls `stock_service` at all (only `WorksOrder` completion does), contradicting the README's claim that "Confirm Pick deducts stock." Tebello confirmed: **fix this in this batch**, so Reopen-STO reversal has something real to reverse.
- **Reopen cascade** — reopening a Complete/Cancelled WO or a Complete/Cancelled STO whose parent SO was auto-closed **also flips the parent SO back to Open**. (Reopening the SO directly does *not* cascade back down to its WOs/STOs — see Part C for why.)
- **Column resize approach** — lightweight vanilla JS/CSS drag handles added to the existing plain `<table class="data-table">` markup, **not** a migration to Tabulator (smaller change, no regression risk to the existing view=open/all toggle, sorting, or row links).

---

### Part A — Payment Status at intake + "Partially Paid" option

**models.py:27** — `PAYMENT_STATUS_OPTIONS` currently:
`('Pending', 'Paid', 'Unpaid', 'Account - Up to Date', 'On Hold')`
→ insert `'Partially Paid'` between `'Paid'` and `'Unpaid'`:
`('Pending', 'Paid', 'Partially Paid', 'Unpaid', 'Account - Up to Date', 'On Hold')`
No schema change — `SalesOrder.payment_status` (models.py:44) already exists with `default='Pending'`.

**`templates/sales_orders/upload.html`** — add a Payment Status `<select>` field to the review/save form, next to the existing Delivery Date field (around line 72-75), populated from `payment_status_options` (already passed to other Sales Order templates — confirm it's passed into the upload/review render call in `routes/sales_orders.py`, add if not). Default-selected option: `Pending` (or `parsed.payment_status` if the field is ever pre-filled, though PDF parsing doesn't currently extract this).

**`routes/sales_orders.py save_order()` (lines 80-152)** — read `request.form.get('payment_status', 'Pending')`, pass into the `SalesOrder(...)` constructor at line 116.

**No change** to the existing `POST /sales-orders/<id>/payment-status` route or its detail-page dropdown — that remains the way to change it after the fact.

---

### Part B — Delivery Date: editable post-save + DD/MM/YYYY display everywhere

**Editable:** new `POST /sales-orders/<id>/delivery-date` route in `routes/sales_orders.py`, mirroring the existing `update_payment_status()` inline-form pattern. Parse `request.form['delivery_date']` (`%Y-%m-%d` — this is what an `<input type="date">` posts, regardless of display locale), set `so.delivery_date`, commit, flash, redirect to detail.

**`templates/sales_orders/detail.html`** (around line 67, next to the existing Payment Status inline dropdown) — add a small inline form: `<input type="date">` pre-filled with `so.delivery_date.strftime('%Y-%m-%d')` + a small "Update" submit button (a date input needs an explicit submit, unlike the payment-status `<select onchange=submit>` pattern — a raw `onchange` would fire mid-keyboard-entry).

**Display format — `DD/MM/YYYY` everywhere delivery_date (and so_date) is shown as text** (not the editable `<input type="date">`, which must keep its ISO `value` attribute — that's an HTML5 requirement, unrelated to display format):
- `templates/sales_orders/list.html:47`, `sales_orders/detail.html:67`, `dashboard.html:101`, `sales_orders/build_bom.html:13`, `sales_orders/bom_builder.html:77`, `works_orders/list.html:50`, `stock_orders/list.html:37`, `stock_orders/detail.html:53`.
- Since the same `strftime('%d/%m/%Y') if x else ''` guard would otherwise be repeated at 8+ call sites, add one small Jinja filter in `app.py` (e.g. `app.jinja_env.filters['dmy'] = lambda d: d.strftime('%d/%m/%Y') if d else ''`) and use `{{ so.delivery_date | dmy }}` at each site instead of inlining the guard 8 times.
- Print templates (`works_order_print.html:71`, `picking_list_print.html:71`, `stock_orders/print.html:64`) already use `%d/%m/%Y` — leave as-is, optionally switch to the new filter for consistency (not required).

---

### Part C — Reopen Sales Order / Works Order / Stock Order (with stock reversal)

**C0 — Fix the STO stock-deduction gap first** (prerequisite for STO reversal to mean anything):
- `models.py` — add `StockOrderLine.qty_issued = db.Column(db.Float, default=0.0)` (mirrors `BOMLine.qty_issued` exactly — needed so Reopen knows precisely how much to reverse per line, same pattern already proven for WO).
- New `scripts/migrate_add_stock_order_line_qty_issued.py` + `ensure_schema_columns()` self-heal entry in `app.py` (hard rule: no schema change without a migration file).
- `routes/stock_orders.py complete_order()` — before setting status to Complete, loop `stock_order.lines`, resolve `Item.query.filter_by(code=line.item_code).first()`. If found and `qty > line.qty_issued`, call `stock_service.issue(item_id=item.id, qty=line.qty - line.qty_issued, reference=stock_order.stock_order_number, notes=f"Issued for {stock_order.stock_order_number}", created_by=request.form.get('completed_by','System'))`, then `line.qty_issued = line.qty`. If no matching `Item` (manual/free-text line with no catalogue match), skip stock deduction for that line only and flash a warning — don't block completion of the rest of the order.
- Note in code/spec: `services/bom_builder.py`'s `create_works_order_or_picking_list()` and `routes/works_orders.py`'s `confirm_pick()` (for `WorksOrder.order_type == 'STOCK'`) are **dead code** in the live app — `build_bom()` constructs `StockOrder`/`StockOrderLine` directly and never produces a `WorksOrder(order_type='STOCK')` row (confirmed: `create_works_order_or_picking_list` is only referenced from `tests/test_bom_builder.py`, never from any route). Not touched in this batch — flagged as a separate future cleanup, out of scope here.

**C1 — `services/stock_service.py`** — add `reverse_issue(item_id, qty, reference, notes="", created_by="System")`: adds `qty` back to `item.qty_on_hand` and logs a `movement_type='REVERSAL'` `StockMovement` (same shape as `receipt()`, but tagged distinctly so movement history can tell a real supplier receipt apart from a reopened-order stock return).

**C2 — WO Reopen** — new `POST /works-orders/<id>/reopen` in `routes/works_orders.py`:
- Allowed when `wo.status in ('Complete', 'Cancelled')`.
- If `wo.status == 'Complete'`: for each `bom_line` where `line_type != 'ASSEMBLY_ITEM'` and `qty_issued > 0`, call `reverse_issue(item_id=bom_line.item_id, qty=bom_line.qty_issued, reference=wo.wo_number, notes=f"Reversed on reopen of {wo.wo_number}")`, then `bom_line.qty_issued = 0.0`.
- Set `wo.status = 'Open'`, `wo.completed_at = None`.
- Cascade: if `wo.sales_order.status == 'Closed'`, set it back to `'Open'`.
- `templates/works_orders/detail.html` — add a "Reopen" button, visible when status is Complete or Cancelled.

**C3 — STO Reopen** — new `POST /stock-orders/<id>/reopen` in `routes/stock_orders.py`:
- Allowed when `stock_order.status in ('Complete', 'Cancelled')`.
- If `stock_order.status == 'Complete'`: for each line where `qty_issued > 0`, resolve the `Item` by `item_code` and call `reverse_issue(...)` for `qty_issued`, then reset `line.qty_issued = 0.0`. (Same "no matching Item" tolerance as C0 — skip + flash, don't block.)
- Set `stock_order.status = 'Open'`.
- Cascade to parent SO, same as C2.
- `templates/stock_orders/detail.html` — add a "Reopen" button, visible when status is Complete or Cancelled.

**C4 — SO Reopen** — new `POST /sales-orders/<id>/reopen` in `routes/sales_orders.py`:
- Allowed when `so.status == 'Closed'` → sets `so.status = 'Open'`.
- **Does not cascade down** — reopening the SO itself doesn't force its WOs/STOs back open (they may be Complete for good reason, e.g. the user just wants to add a note or a new line to the SO). Cascading only flows upward (child reopen → parent reopen), never downward. Flagging this as the one asymmetric design call in this batch — reviewable if Tebello wants it to also force-reopen children.
- `templates/sales_orders/detail.html` — add a "Reopen" button next to the existing "Close Order" button, visible when status is Closed.

**Movement Report / Item detail display** — `templates/reports/movements.html:25-28` (the type filter `<select>`) and `templates/items/detail.html:119-124` (the badge color logic) both enumerate `ISSUE`/`RECEIPT`/`ADJUSTMENT` explicitly — add `REVERSAL` to both (a filter option, and its own badge color rather than falling through to the generic grey "else" brange) so reversed stock is visible and filterable in the audit trail, not just lumped in as "other."

---

### Part D — Resizable list columns + no-wrap date cells

**Resizable columns:** new small vanilla-JS module (e.g. `static/js/resizable_columns.js`) attached to `.data-table` elements on the four list pages (`sales_orders/list.html`, `works_orders/list.html`, `stock_orders/list.html`, `purchase_orders/list.html`). Standard drag-handle pattern: absolutely-positioned 4px grab strip on the right edge of each `<th>`, `mousedown`/`mousemove`/`mouseup` adjusts that column's `width` (switch the table to `table-layout: fixed` while resizing so widths stick). No new dependency, no CDN, consistent with the "offline-first" constraint. **Confirmed with Tebello: widths persist** — saved to `localStorage` keyed by a per-table id (e.g. `colwidths:sales_orders_list`) on `mouseup`, and re-applied on page load before first paint (inline `<script>` right after the `<table>`, not waiting for `DOMContentLoaded`, to avoid a visible layout jump). Resettable later by clearing the browser's local storage — no in-app "reset columns" control in this batch.

**Date column no-wrap:** `static/css/main.css` — `.data-table td` (line 324-328) currently has no `white-space` rule at all. Add a `.data-table td.col-date { white-space: nowrap; }` (or similar) and apply the class to the Date/Delivery Date/Job Number-date columns in the 4 list templates (don't blanket-apply `nowrap` to *all* cells — Customer/Description columns should still be allowed to wrap).

---

### Sequencing (atomic commits)

1. `PAYMENT_STATUS_OPTIONS` + upload/review Payment Status field + `save_order()` change.
2. `dmy` Jinja filter + apply at all 8+ delivery_date/so_date display sites.
3. Delivery Date inline-edit route + detail-page form.
4. `StockOrderLine.qty_issued` column + migration + `ensure_schema_columns()`.
5. `stock_service.reverse_issue()`.
6. STO `complete_order()` stock-deduction fix.
7. WO Reopen route + button + SO-cascade.
8. STO Reopen route + button + SO-cascade.
9. SO Reopen route + button.
10. `REVERSAL` movement type in Movement Report filter + Item detail badge color.
11. Resizable-column JS + date no-wrap CSS on the 4 list pages.
12. Tests (see below) + full suite green + offline-first re-verify.

**New/updated tests:**
- Payment Status settable at upload/review save; `Partially Paid` is a valid value.
- `SalesOrder.delivery_date` updatable via the new route; rejects an empty/invalid date.
- `stock_service.reverse_issue()` adds qty back and logs a `REVERSAL` movement.
- STO `complete_order()` now deducts stock per line and records `ISSUE` movements (extends/updates existing `test_stock_orders.py` coverage that previously assumed no deduction).
- WO Reopen: reverses exactly the issued qty per non-assembly-header line, resets `qty_issued`, flips SO back to Open if it was auto-closed by this WO.
- STO Reopen: same, for `StockOrderLine.qty_issued`.
- SO Reopen: Closed → Open; does not touch child WO/STO statuses.
- Reopen guarded against wrong starting status (e.g. reopening an already-Open WO is a no-op/error, not a double-reversal).

**Acceptance criteria:**
- [ ] Payment Status is selectable during Sales Order upload/review, before the first save; `Partially Paid` appears as an option everywhere Payment Status is shown.
- [ ] Delivery Date can be changed after save from the Sales Order detail page; the change is visible on the SO/WO/STO list pages.
- [ ] Delivery Date and SO Date render as `DD/MM/YYYY` on every list/detail/dashboard page (print pages already did).
- [ ] A completed Stock Order now shows real `ISSUE` stock movements against its items (previously none).
- [ ] Reopen is available on Complete/Cancelled Works Orders, Complete/Cancelled Stock Orders, and Closed Sales Orders; reopening a Complete WO/STO adds the issued quantity back to stock and logs a `REVERSAL` movement per line; reopening cascades the parent SO back to Open if it had been auto-closed.
- [ ] SO/WO/STO/PO list page columns can be drag-resized; date columns never wrap onto two lines.
- [ ] `pytest` full suite green.
- [ ] `grep -r "cdn\."` / `fonts.googleapis` across touched templates/static returns empty.

**Out of scope:**
- Cleaning up the dead `WorksOrder(order_type='STOCK')` / `confirm_pick()` / `services/bom_builder.py` code path (flagged, not removed).
- Reopening a Sales Order cascading down to force-reopen its WOs/STOs.
- Any automated/Sage-synced Payment Status.
- Migrating the 4 list pages to Tabulator.
