# Spec — Dashboard & BOM Builder UI Fixes (2026-07-15)

**Status:** Pending approval
**Requested by:** Tebello, via 3 screenshots (Build Works Pack page, WO0001 detail, Dashboard) + a 6-item punch list.
**Files touched:** `static/css/main.css`, `templates/dashboard.html`, `routes/dashboard.py`, `templates/sales_orders/build_bom.html`, `templates/works_orders/edit.html` — 5 files, plan-first rule applies.

Sales-value scope confirmed with Tebello via AskUserQuestion: the new card sums **Draft + Open Sales Orders only** (same `SO_ACTIVE` set already used by `services/order_filters.py` and the dashboard's "Open Sales Orders" table) — not all-time revenue.

-----

## Item 1 — BOM Builder as a popup with an easier dropdown

**Current state:** `templates/sales_orders/build_bom.html`'s "Add Component" panel is always-visible inline on the page: a free-text search input with a custom `<div>`-based results dropdown (absolute-positioned, manually filtered/rendered in JS), a plain `<select>` for "For Fan line...", a qty input, and an Add button.

**Fix:** Convert the Add Component panel into an Alpine.js modal (same pattern already shipped in Batch 25's Edit Item / Adjust Stock & Levels modals — Alpine is vendored and this repo already has the convention). Trigger: an "Add Component" button opens the modal; the modal contains the search input, results list, Fan-line select, qty input, and Add/Cancel buttons. Replace the hand-rolled filtered-`<div>` dropdown with **Tom Select** (vendored at `static/vendor/tom-select/`, currently unused anywhere in the app) bound to the catalogue JSON already available as `catalogueItems` — gives keyboard nav, clear-to-search, and no manual show/hide/z-index handling, which is also what caused the Batch 26 transparency bug on this exact dropdown.

**Out of scope:** Section 1/2 (SO header, Job/FM numbers, Classify Line Items) stay as-is — only the component-adding UI becomes a popup.

-----

## Item 2 — Overall app width feels cramped / unnecessary text wrapping

**Current state:** `static/css/main.css:158` — `.content-body { max-width: 1400px; ... }`, sidebar is a fixed 240px on top of that.

**Fix:** Raise `.content-body` `max-width` from `1400px` to `1800px`. Wide data tables (Stock Report, Items Catalogue, SO/WO/STO lists) get materially more breathing room on a normal desktop monitor without the page becoming unreadable on very wide screens (`max-width` still caps it, just higher). No other layout structure changes.

-----

## Item 3 — Replaced BOM item renders as a main item instead of nested

**Root cause (confirmed by reading the code, not guessed):** `templates/works_orders/edit.html`'s `addItemFromCatalogue()` (the "Add Items from Catalogue" panel on the WO **Edit** page) always creates a row with `className = 'flat-row'` and appends it to the end of `#selected-items-body` — there is no way, today, to add a new item as a `component-row` nested under an existing `assembly-row`. So removing a component and adding its replacement from the catalogue always produces a new bold top-level "main item" row instead of an indented `└─` sub-component of the assembly it was meant to replace.

**Fix:** Add an "Add as component of…" select next to the existing search/category filter on the Edit page, populated from the current `assembly-row`s in the table (mirrors `build_bom.html`'s existing `componentFanLine` pattern — same interaction the user already knows). When a value is selected, `addItemFromCatalogue()` inserts the new `<tr>` as a `component-row` (with the `└─` indent styling) directly after the chosen assembly's existing component rows, instead of appending a `flat-row` at the end. Leaving the selector on its default ("— standalone item —") preserves exactly today's behavior (flat row), so nothing breaks for the common case of adding a genuinely standalone stock item.

-----

## Item 4 — Status colour: "Draft" should be amber, not blue

**Current state:** `static/css/main.css:374` — `.badge-draft, .badge-open { background: var(--fm-blue); color: #fff; }` (both share one rule).

**Fix:** Split into two rules: `.badge-draft { background: var(--fm-amber); color: #fff; }` and `.badge-open { background: var(--fm-blue); color: #fff; }`. `--fm-amber` (`#F59E0B`) already exists as a design token, just unused for badges. Affects every `badge-draft` usage app-wide (Sales Orders and Purchase Orders both have a `Draft` status) — confirmed this is a shared, desired convention (both "not yet actioned" states), not a one-off.

-----

## Item 5 — FM numbers as the 1st column on the Dashboard

**Scope:** The "Open Sales Orders" table on `templates/dashboard.html` (the table visible in the attached dashboard screenshot) — add a "FM / Job Number" column before "SO Number", reading `so.job_numbers` (existing column, already populated via Build Works Pack). No route/query change needed — `open_sales_orders` already carries the full SO object.

-----

## Item 6 — Total Sales Value dashboard card (Total / Cash Sale / Account)

**Fix:** `routes/dashboard.py` — query `SalesOrder.query.filter(SalesOrder.status.in_(SO_ACTIVE))` (reuse the import already used for `open_sales_orders`, no new query), sum `total_incl` (existing computed property) three ways:
- **Total** — all Draft+Open SOs
- **Cash Sale** — `payment_status.startswith('Cash Sale')`
- **Account** — `payment_status.startswith('Account')`

New stat card on `templates/dashboard.html`, styled consistently with the existing 5-card stats grid (3 sub-values in one wider card, similar to how other cards show a stat + subtitle).

-----

## Test plan

- `tests/test_dashboard.py` (new or extended if it exists): asserts the sales-value card's 3 numbers against a fixture with a mix of Draft/Open/Closed SOs and Cash Sale/Account payment statuses — Closed SOs must be excluded, math must match `total_incl` sums.
- `tests/test_works_orders.py` or similar: regression test that adding a catalogue item with "Add as component of [assembly]" selected produces a `COMPONENT` line nested under that assembly in the saved BOM (not a new `ASSEMBLY_ITEM`/flat line).
- Manual/live verification (dev server, real `instance/sops.db`): Draft badges render amber app-wide; Open badges stay blue; dashboard FM column populated for SOs with job numbers and blank for those without; BOM builder popup opens/searches/adds correctly; wider content area confirmed at normal desktop resolution.
- Offline-first re-check: `grep -rn "cdn\."/"fonts.googleapis"` on touched templates — must stay empty (Tom Select is already vendored locally, this doesn't add a new CDN dependency).

## Acceptance criteria

- [ ] All 6 items above implemented as described.
- [ ] Full test suite green (191 baseline + new tests).
- [ ] `ruff check` clean on touched files.
- [ ] Offline-first constraint intact.
- [ ] Live-verified against real `instance/sops.db` via a freshly-started dev server (not a stale process — recurring risk flagged in Batch 12/20/Ops notes).
