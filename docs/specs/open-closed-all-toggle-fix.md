# Spec: Fix broken "All" toggle + add "Closed" view (SO/WO/STO)

**Status:** Confirmed — Tebello requested directly in chat 2026-07-14, proceed to build.
**Origin:** Tebello reported "when I select all, it reverts to open only" while looking for
closed SO4731. Root cause found in chat before this spec was written.

## Bug
`routes/{sales_orders,works_orders,stock_orders,purchase_orders}.py` `list_orders()`:
`view = request.args.get('view', 'open')` — default flipped from `'all'` to `'open'` in
Batch 16. The "All" link in all 4 list templates was never updated to pass an explicit
`view=all` query param — it links to the bare list URL
(`{{ url_for('sales_orders.list_orders') }}`), which now resolves to the same `'open'`
default. Result: the "All" button visually looks selectable but always re-renders the
Open-only list. Confirmed identical bug in all 4 modules (SO, WO, STO, PO).

## Fix scope (per Tebello's explicit request: SO/WO/STO only, PO gets the bug fix only)

1. **`services/order_filters.py`**: no change — existing `SO_ACTIVE`/`WO_ACTIVE`/`STO_ACTIVE`
   tuples are reused for the new "Closed" view via negation (`NOT IN`), not a new tuple —
   keeps the active-status definition single-sourced.

2. **`routes/sales_orders.py`, `works_orders.py`, `stock_orders.py`** `list_orders()`: extend
   the `view` branch to 3 states:
   ```python
   view = request.args.get('view', 'open')
   if view == 'open':
       query = query.filter(Model.status.in_(ACTIVE))
   elif view == 'closed':
       query = query.filter(~Model.status.in_(ACTIVE))
   # else 'all': no filter
   ```

3. **`templates/sales_orders/list.html`, `works_orders/list.html`, `stock_orders/list.html`**:
   - Toggle becomes 3 buttons: **All** / **Open** / **Closed** (was "All" / "Open only").
   - Every link gets an explicit `view=...` query param (`view='all'` no longer relies on the
     route default) — this is the actual bug fix; the rename/add-button work rides along.
   - Card title reflects all 3 states (`Open ... ` / `Closed ...` / `All ...`).

4. **`routes/purchase_orders.py`**: no route change (already handles any non-`'open'` value as
   unfiltered "all", once the link explicitly passes it).

5. **`templates/purchase_orders/list.html`**: bug-fix only — "All" link gets explicit
   `view='all'`. No "Closed" button added here (out of Tebello's requested scope).

## Out of scope
- No "Closed" button on Purchase Orders (not requested).
- No new status tuples — "Closed" is defined as the negation of the existing ACTIVE tuple per
  module, not a hand-maintained list.
- Dashboard is unaffected (doesn't use this toggle pattern).

## Acceptance criteria
- Clicking "All" on SO/WO/STO/PO lists actually shows every record regardless of status
  (was silently showing Open-only before this fix).
- SO/WO/STO lists have 3 working toggle states: All / Open / Closed.
- SO4731 (Closed) is visible via the new "Closed" toggle (or "All") on the Sales Orders list.
- Existing `?view=open` behavior and default landing view (Open) unchanged.
- Full test suite green; new tests cover `view=closed` excludes active statuses and `view=all`
  (explicit param) returns closed records.
