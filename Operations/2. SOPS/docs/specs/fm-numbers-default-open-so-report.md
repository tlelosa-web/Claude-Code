## Task: FM Number visibility on WO/STO + Default-Open lists + Sales Order report parity

**Domain:** Software / AI
**Date:** 2026-07-09
**Requested by:** Tebello (screenshots: Works Orders list, Stock Orders list, Sage "Sales Order Report" export)

**Goal:** Three related UI/data changes to the order-management screens:
1. Works Orders and Stock Orders lists show internal WO/STO numbers only — Tebello needs the FM/Job number, which is what he actually references day to day.
2. The Sales Orders, Works Orders, Stock Orders, and Purchase Orders list pages currently default to showing **all** records (`?view=all`); Tebello wants **Open** to be the default landing view everywhere, with "All" as the explicit opt-in (reverses the Batch 14 decision recorded in `docs/specs/dashboard-open-filter.md`).
3. The Sales Order list/detail pages should carry the same fields as the attached Sage Sales Order Report export: Date, Delivery Date, Job Number, SO Number, Customer Ref., Customer, Total, Sales Rep, Status, Payment Status.

**Decisions confirmed with Tebello (2026-07-09, via AskUserQuestion):**
- FM number on WO/STO: **track it properly on both.** Add `WorksOrder.job_number` (set from its originating Fan line at Build time). Also capture an FM number on Stock lines at Build time (currently optional/uncaptured) so Stock Orders get an accurate number too — not just an SO-level approximation.
- Payment Status: **fixed dropdown**, not free text. Proposed value set (confirm exact wording in review): `Pending`, `Paid`, `Unpaid`, `Account - Up to Date`, `On Hold`. Manually maintained in SOPS — there is no automated sync from Sage/accounting, so this field will only be as current as someone keeps it.

---

### Part A — FM Number on Works Orders & Stock Orders

**Schema (models.py + migration script, per hard rule "no schema changes without a migration file"):**
- `WorksOrder.job_number = db.Column(db.String(50))` — nullable.
- `StockOrderLine.job_number = db.Column(db.String(50))` — nullable, per-line (mirrors `SOLineItem.job_number`).
- New `scripts/migrate_add_wo_sto_job_numbers.py` + `ensure_schema_columns()` self-heal entries in `app.py` (same pattern already used for `job_numbers`, `reorder_point`).
- `StockOrder.job_numbers` — **computed `@property`**, not a stored column: joins the distinct non-null `job_number` values across `self.lines`, comma-separated (mirrors `SalesOrder.job_reference`). Keeps `StockOrderLine.job_number` as the single source of truth instead of a second copy that can drift.

**`routes/sales_orders.py build_bom()`:**
- Fan lines already require + capture a per-line job number (Batch 11). No change to that validation.
- Stock lines: add an **optional** (not required — don't break existing stock-only flows) job number input, read the same way (`line_job_number_{line.id}`), saved onto `line.job_number` as today.
- In the per-fan-line `WorksOrder` creation loop: set `works_order.job_number = fan_line.job_number` (the line object is already fetched in that loop — one extra field on an existing `WorksOrder(...)` construction).
- When creating each `StockOrderLine`: set `job_number=line.job_number` (from the source `SOLineItem`, now optionally populated).

**`templates/sales_orders/build_bom.html`:** add the optional FM-number input to stock-line rows (currently only rendered for Fan rows).

**Templates:**
- `templates/works_orders/list.html`: add a **Job Number** column. Keep the WO/PL Number column too (Actions/Print/Delete links and internal traceability still need it) — Job Number becomes the prominent lookup column, WO number stays as the secondary reference.
- `templates/stock_orders/list.html`: add a **Job Number** column (from the new `StockOrder.job_numbers` property), same treatment.
- `templates/works_orders/detail.html` and `templates/stock_orders/detail.html`: add a Job Number row if not already surfaced.
- Print templates (`works_order_print.html`, `picking_list_print.html`, `stock_orders/print.html`) already show the SO-level Job Number(s) row (fixed in Batch 11) — leaving as-is; switching them to the more precise per-WO/STO number is a nice-to-have, not required for this batch.

**Known gap, explicitly not fixed here:** existing WOs/STOs created before this migration will show a blank Job Number — there's no reliable backfill source (multi-fan Sales Orders have several comma-separated job numbers with no stored mapping back to which WO each belonged to). Flagging as accepted, not silently backfilling with guesses.

---

### Part B — Default view = Open, across all 4 modules

- `routes/sales_orders.py`, `routes/works_orders.py`, `routes/stock_orders.py`, `routes/purchase_orders.py` — `list_orders()`: change `request.args.get('view', 'all')` → `request.args.get('view', 'open')`. Four one-line changes; `?view=all` remains available and unaffected as an explicit override.
- Templates need no change — the All/Open-only toggle already renders active state from the `view` variable, so it will correctly show "Open only" highlighted by default.
- Dashboard's existing "Open Sales Orders" table and "Recent Works Orders Activity" feed are unaffected by this — Batch 14 already confirmed the activity feed stays an unfiltered feed by design; not revisiting that here unless Tebello says otherwise.

---

### Part C — Sales Order report field parity

Current `templates/sales_orders/list.html` columns: SO Number, Job Number(s), Reference, Customer, Date, Delivery Date, Status, Actions.
Report columns: Date, Delivery Date, Job Number, SO Number, Customer Ref., Customer, Total, Sales Rep, Status, Payment Status.

Gap: **Total**, **Sales Rep**, **Payment Status** are missing from the list view (Sales Rep already exists on the model/detail page, just not listed; Total and Payment Status don't exist anywhere yet). "Reference" already maps to Customer Ref conceptually — relabel the column header to "Customer Ref." to match the report's terminology exactly.

**Schema:**
- `SalesOrder.payment_status = db.Column(db.String(50), default='Pending')`.
- `scripts/migrate_add_so_payment_status.py` + `ensure_schema_columns()` self-heal entry.

**Model:**
- `SalesOrder.total_incl` — computed `@property`, `sum(li.incl_total or 0 for li in self.line_items)`. No schema change; consistent with the existing `job_reference` computed-property pattern. (Using `incl_total` since the sample report's Total column reads VAT-inclusive against known SO totals — confirm against one real order before finalizing.)

**Routes:**
- New `POST /sales-orders/<id>/payment-status` in `routes/sales_orders.py` — updates `so.payment_status` from a dropdown on the detail page (mirrors the existing `close_order`/`cancel_order` inline-form pattern).

**Templates:**
- `templates/sales_orders/list.html`: add Sales Rep, Total (currency-formatted), Payment Status (badge) columns; relabel "Reference" → "Customer Ref."
- `templates/sales_orders/detail.html`: add a Payment Status row with an inline dropdown + submit form to set it (otherwise the field is only editable via direct DB access, which isn't usable).

---

### Sequencing (atomic commits)

1. Migrations + model columns/properties: `WorksOrder.job_number`, `StockOrderLine.job_number`, `StockOrder.job_numbers` property, `SalesOrder.payment_status`, `SalesOrder.total_incl` property.
2. `build_bom()`: populate `WorksOrder.job_number` + optional `StockOrderLine.job_number`; `build_bom.html` optional stock-line FM input.
3. WO/STO list + detail templates: Job Number column/row.
4. Default `view=open`: 4 route one-liners.
5. `test_order_list_filters.py`: update the 4 `test_default_view_shows_all_statuses` tests — bare URL now must hide inactive statuses (same assertions as the existing `test_open_view_hides_*` tests); rename accordingly.
6. SO list/detail: Sales Rep + Total + Customer Ref label + Payment Status column/row/route.
7. New/updated tests: `WorksOrder.job_number` set correctly per fan line (multi-fan case), `StockOrder.job_numbers` rollup, `SalesOrder.total_incl`, `payment_status` route.
8. Full suite green; re-verify offline-first (no new CDN/font references in touched templates).

**Acceptance criteria:**
- [ ] Works Orders list shows a Job Number column populated for all newly-created WOs.
- [ ] Stock Orders list shows a Job Number column populated when at least one line on the order had an FM number entered.
- [ ] Hitting `/sales-orders`, `/works-orders`, `/stock-orders`, `/purchase-orders` with no query param shows Open-only records; `?view=all` still shows everything.
- [ ] Sales Orders list shows Sales Rep, Total, and Payment Status columns matching the Sage report's field set; "Reference" column relabeled "Customer Ref."
- [ ] Payment Status is settable from the Sales Order detail page via a fixed dropdown.
- [ ] `pytest` full suite green, including updated `test_order_list_filters.py`.
- [ ] `grep -r "cdn\."` / `fonts.googleapis` across touched templates returns empty.

**Out of scope:**
- Backfilling Job Number onto pre-existing WOs/STOs.
- Any automated sync of Payment Status from Sage/accounting.
- Changing what the Dashboard's unfiltered "Recent Works Orders Activity" feed shows.
