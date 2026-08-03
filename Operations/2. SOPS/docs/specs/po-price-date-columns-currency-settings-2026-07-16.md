## Task: PO price columns, Order Date as 1st list column, Settings module + system currency

**Domain:** Software / AI
**Date:** 2026-07-16
**Requested by:** Tebello

**Goal:** Three unrelated small-to-medium changes, requested together from a live PO4066 screenshot plus two standing asks:
1. Show unit price and line total on the Purchase Order detail page's Line Items table (currently shows qty only, no price — the data already exists on `POLine`).
2. Move each list page's own order/created date to be the 1st column on the Sales Orders, Works Orders, Stock Orders, and Purchase Orders list pages (no time-of-day component).
3. Add a Settings module with a system currency setting, and replace the "R " hardcoded in every money display with it.

**Decisions confirmed with Tebello (2026-07-16, via AskUserQuestion + code audit):**
- **PO price columns** — add both Unit Price (`excl_price`) and Line Total (`excl_total`), not incl. VAT.
- **Date column** — "the order/created date, no timestamp." Code audit found `SalesOrder.so_date` and `PurchaseOrder.po_date` are real order-date fields (so_date already shown on the SO list, po_date exists on the model but isn't shown on the PO list at all yet); `WorksOrder`/`StockOrder` have no order-date field of their own, only `created_at` (currently shown at 4th-from-last column, with a timestamp). Applying "each tab's own order/created date" literally:
  - SO list: move the existing `so_date` ("Date") column to 1st position (already date-only via the `dmy` filter — no format change needed).
  - PO list: **add** `po_date` as a new 1st column (not currently on this list at all — `due_date` and `created_at` are, neither is the order date).
  - WO/STO lists: move the existing `created_at` ("Created") column to 1st position, and switch its format from `strftime('%Y-%m-%d %H:%M')` to the existing `dmy` filter (date-only, matches every other date column app-wide) — the "no timestamp" instruction applies here since these are the columns actually being moved.
  - Existing `Delivery Date` / `Due Date` / `Created` columns elsewhere on each table are **not removed**, only reordered — this is an add/reorder, not a replace.
- **Currency scope** — full Settings module, not a one-off label fix. New `Setting` key-value table (extensible for future settings, not a single-purpose currency column) seeded with `currency_symbol = 'R'` so display is unchanged until Tebello edits it. A Jinja context processor injects `currency_symbol` into every template so the ~30 hardcoded `"R "` call sites don't need per-route wiring.

---

### Part A — Purchase Order Line Items: Unit Price + Line Total columns

**`templates/purchase_orders/detail.html`** (Line Items table, currently `#`, Item Code, Description, Qty Ordered, Qty Received, Remaining, [Receive Now]):
- Add `<th>Unit Price</th>` and `<th>Line Total</th>` after Description, before Qty Ordered (so price context sits next to the item, matching the pattern already used on `sales_orders/detail.html`'s line-items table).
- Add matching `<td>{{ currency_symbol }} {{ "%.2f"|format(line.excl_price or 0) }}</td>` / `<td>{{ currency_symbol }} {{ "%.2f"|format(line.excl_total or 0) }}</td>`.
- No route change — `po.lines` (a list of `POLine`) is already passed to this template in full; `excl_price`/`excl_total` are already-populated columns (parsed at PO upload time, per `services/po_parser.py`).

---

### Part B — Order/Created Date as 1st column (SO / WO / STO / PO lists)

**`templates/sales_orders/list.html`** — move the existing `<th class="col-date">Date</th>` / `<td class="col-date">{{ so.so_date | dmy or '-' }}</td>` from position 5 to position 1 (before `SO Number`). `data-search` attribute on the `<tr>` is unaffected (doesn't reference column position).

**`templates/purchase_orders/list.html`** — add a new 1st column:
- `<th class="col-date">PO Date</th>` before `PO Number`.
- `<td class="col-date">{{ order.po_date | dmy or '-' }}</td>` (use the existing `dmy` filter, not the raw `due_date.strftime(...)` pattern already on this page — keeps format consistent with the SO list rather than copying this page's own pre-existing inconsistency).
- No route change — `purchase_orders.list_orders()` already passes full `PurchaseOrder` objects; `po_date` is an existing column.

**`templates/works_orders/list.html`** — move `<th class="col-date">Created</th>` / `<td class="col-date">{{ wo.created_at.strftime('%Y-%m-%d %H:%M') }}</td>` from its current position (after Issued By) to 1st (before Job Number), and change the cell to `{{ wo.created_at | dmy or '-' }}` (date-only, drops the timestamp, matches every other date column).

**`templates/stock_orders/list.html`** — same treatment: move `<th class="col-date">Created</th>` / `<td class="col-date">{{ order.created_at... }}</td>` to 1st position (before Job Number), switch to `{{ order.created_at | dmy or '-' }}`.

No test currently asserts column *order* or the raw HTML structure of these list tables (existing `tests/test_order_list_filters.py` asserts filtering behavior, not markup) — no test changes required for Part B; a quick visual/browser check is the acceptance gate.

---

### Part C — Settings module + system currency

**`models.py`** — new model:
```python
class Setting(db.Model):
    __tablename__ = 'setting'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255))
```
This is a **new table**, not a new column on an existing table — `db.create_all()` (already called on every app startup in `app.py:94`) creates it automatically, no `ALTER TABLE` needed. Still add a migration script per this repo's "no schema change without a migration file, ever" rule, documenting the addition and seeding the default row (mirrors the convention already used for every prior schema change, e.g. `scripts/migrate_add_item_max_level.py`):

**`scripts/migrate_add_settings_table.py`** — creates the `setting` table if missing (idempotent, same `db.create_all()`-then-check pattern as other migration scripts here) and inserts `('currency_symbol', 'R')` if that key doesn't already exist.

**`services/settings_service.py`** (new) — small service, mirrors this repo's existing `services/*.py` layering (no DB logic in routes):
```python
DEFAULT_SETTINGS = {'currency_symbol': 'R'}

def get_setting(key, default=None):
    row = Setting.query.filter_by(key=key).first()
    return row.value if row else DEFAULT_SETTINGS.get(key, default)

def set_setting(key, value):
    row = Setting.query.filter_by(key=key).first()
    if row:
        row.value = value
    else:
        row = Setting(key=key, value=value)
        db.session.add(row)
    db.session.commit()

def get_currency_symbol():
    return get_setting('currency_symbol', 'R')
```

**`routes/settings.py`** (new blueprint) — `GET/POST /settings`:
- GET renders the current `currency_symbol`.
- POST validates non-blank, calls `set_setting('currency_symbol', request.form['currency_symbol'].strip())`, flashes, redirects back to `GET /settings`.

**`templates/settings/index.html`** (new) — single form, one text input for Currency Symbol + Save button, styled like the existing `.card`/`.detail-table` pattern (e.g. `items/detail.html`'s Reorder Settings form) rather than inventing new CSS.

**`app.py`**:
- Register `settings_bp` alongside the other blueprints.
- Add `app.context_processor` injecting `currency_symbol` (calls `get_currency_symbol()` inside a request/app context — cheap single-row lookup, table will have at most a handful of rows).
- `ensure_schema_columns()` is for *column* additions to existing tables — the new `Setting` table doesn't need an entry there (`db.create_all()` already covers new tables), but seed the default row here too (belt-and-suspenders alongside the standalone migration script, same as how other batches leave both the self-heal path and the standalone script in place).

**`templates/base.html`** — add a Settings sidebar link after Reports (line 74), same `<li>`/`sidebar-link` markup pattern, simple gear-style inline SVG icon.

**Replace hardcoded `"R "` with `{{ currency_symbol }}`** (context processor makes this available with no per-route wiring) at every site found by `grep -rn "R {{" templates/` plus the JS-based Tabulator config in `reports/stock.html`:
- `templates/items/detail.html` — Last Cost, Avg. Cost, Excl. Price, Incl. Price, Stock Value (5 sites).
- `templates/purchase_orders/upload.html` — 3 sites (preview table).
- `templates/purchase_orders/print.html` — 5 sites (line price/total, incl. total, grand totals x2).
- `templates/purchase_orders/detail.html` — the 2 new sites added in Part A (write these directly as `{{ currency_symbol }}`, not `"R "`, since Part C lands in the same batch).
- `templates/dashboard.html` — Total / Cash Sale / Account Sales Value cards (3 sites).
- `templates/sales_orders/upload.html` — 3 sites (preview table).
- `templates/sales_orders/list.html` — 1 site (Total column).
- `templates/sales_orders/detail.html` — Total, Balance Due, + 2 line-item sites (5 sites).
- `templates/reports/stock.html` — **JS, not Jinja text** — the Tabulator `formatterParams: { symbol: 'R ' }` (2 sites) and the plain-JS grand-total string `'R ' + data.grand_total...` (1 site) need `{{ currency_symbol }}` interpolated into the `<script>` block at render time (e.g. `symbol: '{{ currency_symbol }} '`), not a runtime JS lookup — this page has no other server-rendered JS values today, confirm the interpolation doesn't break if `currency_symbol` ever contained a `'` (out of scope to sanitize further; single-character symbols like `R`/`$`/`€` are the expected input, not free text).

**Deliberately left untouched:** `templates/sales_orders/bom_builder.html` — confirmed orphaned in Batch 18/29 (no route renders it) — not worth touching a dead template in this batch.

---

### Sequencing (atomic commits)

1. `Setting` model + `scripts/migrate_add_settings_table.py` + `services/settings_service.py`.
2. `routes/settings.py` + `templates/settings/index.html` + blueprint registration + context processor + `base.html` nav link.
3. Replace all `"R "` sites with `{{ currency_symbol }}` (Jinja sites) across the 8 templates listed above.
4. `reports/stock.html` JS-interpolation sites.
5. Part A — PO detail Unit Price / Line Total columns (uses `{{ currency_symbol }}` directly, lands after Part C's context processor exists).
6. Part B — date column reorder on all 4 list pages.
7. Tests (see below) + full suite green + offline-first re-verify.

**New/updated tests:**
- `services/settings_service.py`: `get_setting` returns the seeded default when unset, `set_setting` persists and is read back, updates an existing key without creating a duplicate row.
- `routes/settings.py`: GET renders current value; POST updates it and the change is reflected on next GET; POST with a blank value is rejected (flash, no change).
- Context processor: a spot-check that a rendered page (e.g. dashboard) contains the currency symbol from `Setting`, not the literal old default, after changing it — proves the wiring, not just the service function.
- No test needed for Part B (no existing test asserts column order/markup) or Part A (no existing test asserts PO detail page markup) — both are visual changes, verified live in-browser per this repo's standing convention for pure-template changes.

**Acceptance criteria:**
- [ ] PO detail page shows Unit Price and Line Total per line, matching the parsed PO PDF values.
- [ ] SO/WO/STO/PO list pages each show their own order/created date (no time-of-day) as the 1st column; existing Delivery Date/Due Date/Created columns elsewhere on the same tables are unchanged.
- [ ] `/settings` page exists, reachable from the sidebar, lets Tebello view and change the currency symbol.
- [ ] Every money value across the app (dashboard cards, SO/PO lists and details, Items detail, Stock Report, PO upload/print) reflects the current `currency_symbol` setting, not a hardcoded `"R"`.
- [ ] Changing the currency symbol via `/settings` and reloading any of the above pages shows the new symbol everywhere, with no app restart required.
- [ ] `pytest` full suite green.
- [ ] `grep -rn "R {{"` (or equivalent hardcoded-currency search) across `templates/` returns empty except the deliberately-untouched orphaned `sales_orders/bom_builder.html`.
- [ ] Offline-first re-verified (no `cdn.`/`fonts.googleapis` introduced).

**Out of scope:**
- Any real multi-currency conversion/exchange-rate logic — this is a display-symbol setting only, no math changes.
- Adding more settings beyond currency symbol (the `Setting` table is generic/extensible for future use, but no other setting is being added now).
- Fixing `sales_orders/bom_builder.html`'s hardcoded `"R "` (dead/orphaned template, confirmed in Batch 18/29).
- Migrating any list page to Tabulator, or changing sort order (Part B is a column-position/format change only — the underlying `ORDER BY` in each route is untouched).
