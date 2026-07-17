# Spec — Batch 31: List Sort/Filter, Sticky Headers, Dashboard Payment Status (2026-07-17)

**Status:** Approved (scope confirmed via 4 rounds of AskUserQuestion)
**Requested by:** Tebello, 3-item punch list.
**Files touched:** `static/js/table_sort_filter.js` (new), `static/js/resizable_columns.js`, `static/css/main.css`, `templates/sales_orders/list.html`, `templates/works_orders/list.html`, `templates/stock_orders/list.html`, `templates/purchase_orders/list.html`, `templates/dashboard.html` — 8 files, plan-first rule applies.

Scope confirmed with Tebello:
- Sort/filter and sticky headers apply to the **4 order-list pages only** (Sales/Works/Stock/Purchase Orders) — these are plain `<table class="data-table">` pages with no/partial column-level sort or filter today. Items Catalogue and the two Reports pages already use Tabulator (click-to-sort works there) — left untouched.
- Sort/filter is a **new vanilla JS utility** (matches the existing `resizable_columns.js` pattern), not a Tabulator migration — Batch 29 already rejected Tabulator for these pages because their Actions columns have live forms/dropdowns Tabulator would need custom cell formatters for.
- Dashboard "Open Sales Orders" alignment fix = consistent cell alignment (vertically centered, and right-align numeric/status-style columns so they don't ragged-edge against the Action button).

-----

## Item 1 — Sort + filter by any column, all 4 order-list pages

**Current state:** `templates/{sales_orders,works_orders,stock_orders,purchase_orders}/list.html` render plain `<table class="data-table">`s. Only the Sales Orders list has any filtering — a single free-text `#so-search` box (Batch 29) that hides rows via `row.style.display` based on a `data-search` attribute concatenating several fields. No page has column-header sort.

**Fix:** New `static/js/table_sort_filter.js`, exposing `window.makeTableSortableFilterable(tableId)` (called from each list template's `extra_scripts` block, same pattern as `makeColumnsResizable(tableId)`):

- **Sort:** clicking a `<th>` sorts `tbody` rows by that column, toggling ascending/descending on repeat clicks, with a small ▲/▼ indicator appended to the active header. Sort key per row: `td.dataset.sort` if present, else the cell's trimmed `textContent`. Skip any `<th>` marked `data-sortable="false"` (the Actions column on all 4 tables).
- **Filter:** each sortable `<th>` gets a small text `<input>` injected below its label (inside the same `<th>`, not a second `<tr>` — keeps sticky-header CSS to one row, see Item 2). Typing filters rows by substring match (case-insensitive) against that column's cell text. Multiple active column filters combine with AND. Columns marked `data-sortable="false"` get no filter input either.
- **Composing with the existing SO search box:** the SO list's `#so-search` script and the new per-column filters must not stomp each other by both writing `row.style.display` directly (last write wins = the two features fight). Fix: the new script tracks per-row filter state via `row.dataset.hiddenByColumnFilter` and exposes `window.updateTableRowVisibility(row)` (sets `display: none` if `hiddenByColumnFilter === '1'` OR `hiddenBySearch === '1'`, else `''`). Rewrite the existing inline search script in `sales_orders/list.html` to set `row.dataset.hiddenBySearch` instead of `row.style.display` directly, then call `window.updateTableRowVisibility(row)`. Verify live: search box narrows rows, a column filter narrows further, clearing one restores only what the other still allows.
- **Numeric/date sort correctness:** string-sorting `"10/07/2026"`-style dates or `"R 1234.56"` currency text gives wrong order. Add `data-sort="{{ ...isoformat... }}"` on every `col-date` `<td>` (Date/Created/Delivery Date/Due Date/PO Date columns, all 4 tables) and `data-sort="{{ so.total_incl }}"` on the SO list's Total column. Status/Payment Status/text columns sort correctly as plain strings, no `data-sort` needed.
- Mark each table's Actions `<th>` with `data-sortable="false"`.

-----

## Item 2 — Sticky headers on scroll, same 4 pages

**Current state:** `.topbar` (`static/css/main.css:131`) is already `position: sticky; top: 0` and works, because the whole document scrolls (body has no `overflow` constraint) — so the same technique applies directly to table headers. **Real conflict found while reading the code:** `resizable_columns.js:50` sets `th.style.position = 'relative'` via **inline style** on every header cell — an inline style always wins over an external stylesheet rule, so a `.data-table th { position: sticky; }` CSS rule alone would be silently overridden on every page that calls `makeColumnsResizable()` (all 4 of these).

**Fix:**
- `static/js/resizable_columns.js:50`: change `th.style.position = 'relative';` → `th.style.position = 'sticky';`. (`position: sticky` still establishes a positioning context for the absolutely-positioned resize handle child, so the resize feature is unaffected.)
- `static/css/main.css`, on the existing `.data-table th` rule (`:314`): add `top: var(--topbar-height); z-index: 40;` (below the topbar's `z-index: 50`, above table body content).
- Cosmetic-only nit, not a hard requirement: give the new filter `<input>` (Item 1) a little right padding/margin so it doesn't visually crowd the resize handle's 6px strip on the right edge of the `<th>` — eyeball it live, not worth a pixel-perfect spec.

-----

## Item 3 — Dashboard "Open Sales Orders" card: Payment Status column + alignment

**Current state:** `templates/dashboard.html:94-153`. Table columns: FM/Job Number, SO Number, Customer, Delivery Date, Status, Action (View button). All `<td>`/`<th>` are plain left-aligned inline styles (`padding: 16px` / `padding: 12px`), no explicit `text-align` beyond the header row's default. `open_sales_orders` (from `routes/dashboard.py`) is a list of `SalesOrder` ORM objects — `so.payment_status` is already a populated column, no route change needed.

**Fix:**
- Add a **Payment Status** `<th>`/`<td>` between **Status** and **Action** (both in the `<thead>` and the `{% for so in open_sales_orders %}` loop), reading `{{ so.payment_status or '-' }}` — same plain-text rendering the Sales Orders list already uses for this field (no badge styling exists for payment status app-wide, don't invent one here).
- Alignment tidy-up: add `text-align: right` to the Status, Payment Status, and Action header/cells (they currently ragged-edge at different widths against the right side of the card); keep FM/Job Number, SO Number, Customer, Delivery Date left-aligned as today. Confirm `vertical-align: middle` is effectively applied to every `<td>` (the badge `<span>` in the Status cell and the plain text in the new Payment Status cell should sit on the same baseline within the row).

-----

## Test plan

- No new automated tests planned — this repo's standing convention for pure client-side JS / template-only changes (Batch 27's Alpine modals, Batch 29's SO search box) is manual/live verification only, no server-side logic changes here either.
- Live verification (dev server, real `instance/sops.db`, freshly-started process — recurring stale-server risk per Batch 12/20/27/28/29/30):
  - Each of the 4 order-list pages: click every sortable column header, confirm ascending/descending toggle and correct order (numeric for dates/Total, alphabetical for text); type into each column filter, confirm rows narrow correctly and multiple filters AND together; confirm the Actions column has no sort/filter UI.
  - Sales Orders list specifically: confirm the existing `#so-search` box and the new column filters compose correctly (search narrows, then a column filter narrows further; clearing one restores only what the other still allows).
  - Scroll each of the 4 list pages with enough rows to exceed one screen — confirm the header (with filter inputs) stays visible/usable while scrolling, and doesn't overlap the topbar.
  - Confirm column resize (existing feature) still works after the `position: relative` → `sticky` change.
  - Dashboard: Payment Status column renders between Status and Action with real data; right-aligned columns line up cleanly; existing "View All" / View button links still work.
- Offline-first re-check: no new CDN/font references introduced (pure local JS/CSS/template edits).

## Acceptance criteria

- [ ] All 3 items above implemented as described.
- [ ] Full test suite still green (no regressions — no new tests expected, this is UI-only).
- [ ] `ruff check` clean on any touched `.py` files (none expected — this batch is JS/CSS/template only).
- [ ] Offline-first constraint intact.
- [ ] Live-verified against real `instance/sops.db` via a freshly-started dev server.
