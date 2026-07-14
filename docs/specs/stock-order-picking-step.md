## Task: Add a Picking step to the Stock Order process (before Complete)

**Domain:** Software / AI
**Date:** 2026-07-14
**Requested by:** Tebello

**Goal:** Today a Stock Order (STO) goes `Open → Complete` in one click — `complete_order()` issues stock for every line at once, with no intermediate checkpoint. Add a required **Picking** step in between: warehouse staff confirm each line as picked (recording actual picked qty and deducting stock at that moment, per line), and `Complete` is only allowed once every line has been fully picked. This mirrors the *intent* of the existing Works Order picking-list flow (`WorksOrder.order_type == 'STOCK'` + `confirm_pick()`), but that code path is confirmed dead for STOs (per `docs/specs/payment-status-delivery-date-reopen-columns.md` C0 note — `build_bom()` creates `StockOrder`/`StockOrderLine` directly, never a `WorksOrder(order_type='STOCK')`), so this is new code on the real `StockOrder` model, not a revival of the old path.

**Decisions confirmed with Tebello (2026-07-14, via AskUserQuestion):**
1. **Stock timing** — picking a line deducts stock immediately (`stock_service.issue()` at pick time, not deferred to Complete).
2. **Granularity** — per-line. Each `StockOrderLine` records its own picked qty (reuses the existing `qty_issued` column added in Batch 17 — no schema change needed for this part).
3. **Status model** — new status value: `Open → Picking → Complete`. `Picking` sits between `Open` and `Complete` on `StockOrder.status` (still a free-text column, no schema change — just a new string value alongside `Open` / `Complete` / `Cancelled`).
4. **Complete gate** — Complete is **blocked** until every line is fully picked (`qty_issued >= qty` for all lines). This is a real checkpoint, not a one-click fallback like the WO path.
5. **Cancel mid-pick** — cancelling a `Picking` order (partial stock already issued on some lines) **reverses** the already-picked qty per line via `stock_service.reverse_issue()` before flipping to `Cancelled`, so no stock is left phantom-deducted. A `Cancelled` STO always has `qty_issued == 0` on every line by construction.

---

### Model changes — `models.py`

No new columns. `StockOrderLine.qty_issued` (Batch 17) is reused as the per-line picked-qty tracker, exactly as it already is for `complete_order()`/`reopen_order()`. `StockOrder.status` stays a plain string column — `'Picking'` is simply a new value it can hold, alongside the existing `'Open' / 'Complete' / 'Cancelled'` (update the model's inline status comment to list all four).

---

### `services/order_filters.py`

`STO_ACTIVE = ('Open',)` → `STO_ACTIVE = ('Open', 'Picking')`. A Picking order is still in-progress/active — it must keep showing under the default "Open" list/dashboard filter, not fall through to "Closed".

---

### `routes/stock_orders.py`

**New route — `POST /stock-orders/<id>/pick`:**
- Guard: reject (flash + redirect) unless `stock_order.status in ('Open', 'Picking')`.
- For each `line in stock_order.lines`: read `request.form.get(f'pick_qty_{line.id}', '0')`, parse as float (fall back to `0.0` on bad input, don't crash the whole submission over one bad field). Clamp to `max(0, min(entered_qty, (line.qty or 0.0) - (line.qty_issued or 0.0)))` — never allow picking more than what's outstanding on that line, even if the form is tampered with.
- Skip lines where the clamped qty is `0`.
- For each remaining line: resolve `Item.query.filter_by(code=line.item_code).first()`. If no match, skip + collect into an `unmatched` list (same tolerance pattern as `complete_order()` — flash a warning, don't block the rest of the submission). If matched, call `stock_service.issue(item_id=item.id, qty=clamped_qty, reference=stock_order.stock_order_number, notes=f"Picked for {stock_order.stock_order_number}", created_by=picked_by)`, then `line.qty_issued = (line.qty_issued or 0.0) + clamped_qty`.
- `picked_by = request.form.get('picked_by', 'System').strip() or 'System'` (same free-text-name pattern as `issued_by`/`completed_by`/`reopened_by` — no login system, matches project convention).
- If at least one line was actually picked in this submission and `stock_order.status == 'Open'`, set `stock_order.status = 'Picking'`.
- If nothing was picked (all requested qtys were `0`/blank), flash a warning and redirect without touching status — don't manufacture a no-op Picking transition.
- Wrap in try/except → rollback + flash on error, same shape as every other STO route.
- Redirect to `stock_orders.view_order`.

**`complete_order()` — add the full-pick gate:**
- Existing guards stay (`Cancelled` → error, already-`Complete` → warning).
- New guard, checked before the existing issue-loop: if `any((line.qty or 0.0) - (line.qty_issued or 0.0) > 0 for line in stock_order.lines)`, flash `"All lines must be picked before this Stock Order can be completed."` and redirect without changing anything.
- The existing per-line issue loop stays in place as a defensive no-op (every line's `qty_to_issue` will be `0` once the gate above passes) rather than being deleted — cheap insurance against a future edge case, and avoids a second code path just for "finalize."
- Rest of the function (status → `Complete`, SO auto-close cascade check) is unchanged.

**`cancel_order()` — reverse partial picks before cancelling:**
- Existing guard (`if stock_order.status == 'Complete': block`) already permits both `Open` and `Picking` through unchanged — no guard rewrite needed.
- Before setting `status = 'Cancelled'`: loop `stock_order.lines`, for any `line.qty_issued > 0`, resolve `Item` by `item_code`. If matched, call `stock_service.reverse_issue(item_id=item.id, qty=line.qty_issued, reference=stock_order.stock_order_number, notes=f"Reversed on cancel of {stock_order.stock_order_number}", created_by=request.form.get('cancelled_by', 'System').strip() or 'System')`, then `line.qty_issued = 0.0`. If unmatched, skip + flash warning (same tolerance pattern, don't block the cancel itself).
- Then `status = 'Cancelled'`, commit, flash, redirect — unchanged shape otherwise.

**`reopen_order()` — no logic change needed.** Because `cancel_order()` now fully reverses at cancel-time, every `Cancelled` STO already has `qty_issued == 0` on all lines by the time Reopen runs — the existing `if stock_order.status == 'Complete':` reversal branch is still exactly correct (Cancelled → Open stays a no-op for stock, Complete → Open still reverses everything). Reopening always lands back on `'Open'` (not `'Picking'`) regardless of how far picking had gotten before — simplest, and picking naturally restarts from a clean `Open` state.

**`edit_order()` — no change needed.** It already only allows editing when `status == 'Open'`; once any line has been picked (status flips to `'Picking'`), editing is automatically blocked by the existing guard — correct, since editing lines out from under partially-issued stock would corrupt the `qty_issued`/`qty` relationship.

---

### `templates/stock_orders/detail.html`

- **Status badge:** unchanged markup (`badge-{{ status.lower() }}`) — just needs a CSS color for `picking` (see below).
- **Line items table:** when `stock_order.status in ('Open', 'Picking')`, add a "Picked" column showing `line.qty_issued or 0` alongside the existing Qty column, and wrap the whole table in a `<form method="POST" action=".../pick">` with a `pick_qty_<line.id>` number input per row (defaulting to the remaining qty = `line.qty - (line.qty_issued or 0)`, `min="0"`, `step="0.1"`, disabled/hidden once that line is already fully picked), a `picked_by` text input, and a single "Confirm Picks" submit button below the table — one POST records picks for as many lines as the user filled in, consistent with the app's existing "one form, many rows" pattern (`build_bom.html`, `stock_orders/edit.html`) rather than a separate request per line.
- When `stock_order.status == 'Complete'` (or `'Cancelled'`), render the line table read-only as it does today (no pick inputs).
- **Actions dropdown:**
  - "Mark Complete" — only rendered (or rendered but disabled with a tooltip) when every line's `qty_issued >= qty`; otherwise show a disabled item: `title="All lines must be picked first."`.
  - "Cancel Order" — visible whenever status is `Open` or `Picking` (unchanged availability), confirm dialog text updated to mention stock reversal when applicable: `"Cancel this Stock Order? Any already-picked stock will be reversed."`.
  - "Edit" — stays gated to `status == 'Open'` only (unchanged).
  - "Reopen" — stays gated to `status in ('Complete', 'Cancelled')` (unchanged).

### `templates/stock_orders/list.html`

No structural change — the existing `badge badge-{{ order.status.lower() }}` and `view=open/closed/all` toggle both work automatically once `STO_ACTIVE` includes `'Picking'` and the CSS class exists.

### `static/css/main.css`

Add `.badge-picking { background: var(--fm-orange); color: #fff; }` near the existing `.badge-inprogress` rule (line ~375) — reuses the same orange already used for WO's "In Progress", keeping the color language consistent (blue = not started, orange = in progress, green = done, grey = cancelled/closed).

### `templates/stock_orders/print.html`

No change — printing an in-progress Picking order should still show the full line list as today (a picking document is exactly the kind of thing someone would print *during* picking).

---

### Sequencing (atomic commits)

1. `services/order_filters.py` — add `'Picking'` to `STO_ACTIVE`.
2. `routes/stock_orders.py` — new `pick_lines()` route (`POST /stock-orders/<id>/pick`).
3. `routes/stock_orders.py` — `complete_order()` full-pick gate.
4. `routes/stock_orders.py` — `cancel_order()` partial-pick reversal.
5. `templates/stock_orders/detail.html` — pick form, Picked column, Complete-button gating, updated Cancel confirm text.
6. `static/css/main.css` — `.badge-picking`.
7. Tests (see below) + full suite green + offline-first re-verify.

**New/updated tests (`tests/test_stock_orders.py`):**
- `POST /pick` on an `Open` STO: picking one line issues stock for exactly that line, sets its `qty_issued`, flips status to `Picking`, leaves other lines untouched.
- `POST /pick` again on a `Picking` STO: picking the remaining line(s) issues correctly, does not double-issue an already-fully-picked line, status stays `Picking` (not auto-advanced to `Complete`).
- `POST /pick` clamps an over-large submitted qty to the remaining outstanding amount rather than over-issuing.
- `POST /complete` on a `Picking` STO with lines still outstanding → blocked, flash error, no status change, no stock movement.
- `POST /complete` on a `Picking` STO with all lines fully picked → succeeds, status → `Complete`, SO auto-close cascade check still runs (existing behavior, now reached via the new path too).
- `POST /cancel` on a `Picking` STO with partial stock issued → reverses exactly the issued qty per line (logs `REVERSAL` movements), resets `qty_issued` to `0`, status → `Cancelled`.
- `POST /cancel` on a plain `Open` STO (nothing picked yet) → unchanged behavior, no reversal calls made (nothing to reverse).
- `list_orders(view='open')` includes a `Picking` STO; `view='closed'` excludes it.
- `POST /pick` with an unmatched `item_code` on one line → that line skipped + warning flashed, other lines in the same submission still process.
- Reopen of a `Complete` STO (full pick history) still reverses everything as before (regression check — Complete-path reopen behavior unchanged by this batch).

**Acceptance criteria:**
- [ ] A Stock Order's line items can be picked individually, with stock deducted at the moment each line is picked (not deferred to Complete).
- [ ] `StockOrder.status` shows `Picking` once at least one line has been picked, and is filterable/visible under the "Open" list view alongside `Open` orders.
- [ ] "Mark Complete" is unavailable (or explicitly blocked server-side) until every line on the order has been fully picked.
- [ ] Cancelling a Stock Order that has partially-picked lines reverses the already-deducted stock before the order is marked Cancelled — no stock is left phantom-deducted.
- [ ] Reopening a `Complete` Stock Order still reverses all issued stock, unchanged from existing behavior.
- [ ] `pytest` full suite green.
- [ ] `grep -r "cdn\."` / `fonts.googleapis` across touched templates/static returns empty (offline-first).

**Out of scope:**
- Cleaning up the dead `WorksOrder(order_type='STOCK')` / `confirm_pick()` code path (still flagged, not touched — separate future cleanup per the C0 note it was first raised in).
- Applying the same Picking step to Works Orders (explicitly scoped to Stock Orders only per Tebello's answer).
- A picking-specific print document (the existing STO print page is reused as-is for now).
- Per-line `picked_by`/`picked_at` audit columns on `StockOrderLine` itself — the picker's name is captured on the `StockMovement.created_by` for each issued line (already sufficient audit trail via the existing movement log), not duplicated onto the line row.
