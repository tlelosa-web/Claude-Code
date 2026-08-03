# Spec — Clickable Item Codes + Sales Orders List Search (2026-07-15)

**Status:** Pending approval
**Requested by:** Tebello — two asks: (1) click an item code to open its detail/edit page, scope confirmed via AskUserQuestion as app-wide (WO/STO/PO detail, not just the STO page it was raised from); (2) add search to the Sales Orders list.
**Files touched:** `services/doc_generator.py`, `routes/stock_orders.py`, `templates/works_orders/detail.html`, `templates/stock_orders/detail.html`, `templates/purchase_orders/detail.html`, `templates/sales_orders/list.html` — 6 files, plan-first rule applies.

-----

## Feature A — Clickable item codes → `/items/<id>` (detail + edit)

`/items/<id>` already exists (`routes/items.py::detail()`) and already has the Edit Item modal (Batch 25) — no new page needed, just links to it wherever an item code renders as plain text today.

**Scope decision, investigated before writing this spec:** `SalesOrder`'s own Line Items table (`SOLineItem` model) has no `item_id`/`item_code` at all — SO lines are raw PDF-parsed rows (description/qty/price only) with no catalogue link until Build Works Pack matches them. So Sales Order detail is **excluded** — there's nothing to link there. Scope is WO detail, STO detail, PO detail.

1. **Works Order detail** (`templates/works_orders/detail.html`) — item codes come from `services/doc_generator.py::get_works_order_print_context()`'s `line_dict`/`components` dicts, which carry `item_code` but not `item_id` today. Add `'item_id': item.id` (top-level) and `'item_id': child_item.id` (nested components) to those dicts. Template: wrap `assembly.item_code`, `comp.item_code`, and `line.item_code` (3 sites: assembly row, nested component row, flat line row) in `<a href="{{ url_for('items.detail', item_id=X.item_id) }}" class="link-primary">`.

2. **Stock Order detail** (`routes/stock_orders.py`, `templates/stock_orders/detail.html`) — `_line_comments()` (added in Batch 28) already resolves `item_code → Item` per line internally but only returns a comment string. Extend it to return `{line.id: {'comment': str, 'item_id': int|None}}` instead (rename to `_line_extras()`), update `view_order()`'s render call and the template's two accessors (`.comment` for the Comments cell, `.item_id` to wrap the Item Code cell in a link when not None — unmatched item codes stay plain text, matching the "Item not in catalogue" comment already shown for that line).

3. **Purchase Order detail** (`templates/purchase_orders/detail.html`) — `line.item` is already the real `Item` object when matched (line 78-79: `{% if line.item %}{{ line.item.code }}{% endif %}`). Simply wrap `{{ line.item.code }}` in a link using `line.item.id` when the `if line.item` branch is taken. The `{% else %}` unmatched/Link-item branch is untouched.

-----

## Feature B — Sales Orders list search

`templates/sales_orders/list.html` currently has an All/Open/Closed status toggle but no text search — the SO list can run to dozens of rows with no way to jump to one. `templates/works_orders/edit.html`'s catalogue-search pattern (plain `<input>` + JS `input` listener filtering rendered rows, no server round-trip, no dependency) is the existing in-house convention for this — reused here rather than migrating the list to Tabulator (bigger change, and the Actions column has live `<form>`s/dropdowns Tabulator would need custom formatters for).

- New `<input id="so-search" placeholder="Search SO #, customer, job number...">` next to the existing All/Open/Closed toggle.
- JS: on `input`, lowercase-match the query against each `<tr>`'s SO Number, Job Number(s), Customer Ref., Customer, and Sales Rep cells (the fields a user would realistically search by); hide non-matching rows, show matching ones. Pure client-side — the existing `view=` server-side filter and the search box compose naturally (search narrows whatever the current view already rendered).
- No behavior change to All/Open/Closed or the existing `resizable_columns.js` wiring.

-----

## Test plan

- `tests/test_works_orders.py` (or wherever WO detail is covered): assert `item_id` present in `get_works_order_print_context()`'s returned dicts for both a top-level and nested-component line.
- `tests/test_stock_orders.py`: extend the existing Comments tests (or add new ones) to also assert the item-code link renders for a matched line and does NOT render for the "Item not in catalogue" case.
- Purchase Orders: light regression check that a matched line's code renders inside an `<a href="/items/<id>">`.
- Sales Orders list: no new automated test planned (pure client-side filter, no server logic) — manual live verification only, per this repo's convention for JS-only UI (e.g. Batch 27's BOM Builder modal).
- Offline-first / `ruff check` / full suite green — standard acceptance bar for this repo.
