# Spec — PO Edit + Upload-screen Item Picker

- **Date:** 2026-07-23
- **Owner:** Tebello Lelosa
- **Status:** Approved (scope confirmed via AskUserQuestion)
- **Module:** Purchase Orders (`routes/purchase_orders.py`, `templates/purchase_orders/*`)

## 1. Problem

Two gaps in the PO module:

1. **No edit function.** Once a PO is saved (upload → save → detail), the only
   ways to change it are re-uploading the PDF (overwrite) or the per-line
   "Link" box on the detail page. There is no way to correct the supplier,
   dates, discount, a wrong quantity/price, or to add/remove a line. Every
   other order type (SO, WO, STO) has an edit screen; PO is the odd one out.

2. **Unparseable / mis-parsed lines can only be fixed after saving.** On the
   upload review screen an unmatched line is saved unlinked (amber row +
   "Unmatched" badge) and can only be linked later on the detail page by
   typing an exact item code. There is no catalogue search at review time,
   and a *wrong* auto-match cannot be corrected before saving at all.

## 2. Confirmed scope

| Decision | Choice |
|---|---|
| **PO editable when** | `status in ('Draft', 'Open')` **and** no receipts recorded (`all qty_received == 0`). Mirrors the existing overwrite/cancel guards. |
| **PO edit covers** | Header fields (supplier name, supplier VAT, reference, PO date, due date, overall discount) **and** line items (item link via picker, description, qty, price, discount) — including **add** and **remove** lines. |
| **Blocked once** | Any stock received against the PO (`Partially Received` / `Received` are never editable; a receipt on an otherwise-Open PO also blocks). |
| **Upload picker** | **Every** review line gets a searchable catalogue picker; unmatched lines stay highlighted. Lets the user fill in an unparsed item **and** correct a wrong auto-match before saving. |

## 3. Design

### 3.1 Shared inline item picker — `static/js/item_picker.js`

A small vanilla-JS inline autocomplete (no new vendor libs, offline-first).
Both the upload review screen and the PO edit screen use it, each passing the
catalogue as `window.SOPS_ITEMS` (array of `item_to_bom_json(...)` payloads).

Behaviour per picker cell:
- A text `<input>` (search box) plus three hidden values held as row
  `data-*` attributes: `item_id`, `item_code`, `description`.
- Typing filters the catalogue (case-insensitive substring on code **or**
  description), rendering an absolutely-positioned dropdown of up to 20 hits.
- Clicking a hit sets the row's `item_id` / `item_code` / `description`,
  fills the input with `CODE — description`, removes the `row-amber` /
  "Unmatched" styling, and fires a `change`-style callback so the owning
  page can re-sync its `lines_json`.
- Clearing the input (or never matching) leaves the line unlinked
  (`item_id` null) — still savable, exactly as today.

The module exposes one entry point, e.g.
`ItemPicker.attach(inputEl, { items, onSelect })`, and is defensively coded
(escapes HTML, guards missing nodes) in the same style as
`templates/stock_orders/edit.html`.

### 3.2 Route helper — `_build_lines_from_json(po_id, lines_json)`

Extract the POLine-building block currently inline in `save_order()` into a
module-level helper in `routes/purchase_orders.py`:

```
def _build_lines_from_json(po_id, lines_json):
    """Yield POLine objects from the review/edit form's lines_json.
    Shared by save_order() and edit_order()."""
```

Reads per item: `matched_item_id` → `item_id`, `item_code` → `item_code_raw`,
`description`, `qty` → `qty_ordered`, `excl_price`, `disc_pct`, `vat_pct`,
`excl_total`, `incl_total`. Same tolerant float-coercion as today. This is a
pure refactor of existing behaviour (regression-covered by the existing
save/receive tests) that removes duplication between save and edit.

### 3.3 New route — `edit_order`

```
@purchase_orders_bp.route('/purchase-orders/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
```

- **Editability guard** (`_po_is_editable(po)`): `po.status in ('Draft','Open')
  and not any((l.qty_received or 0) > 0 for l in po.lines)`. On failure →
  flash + redirect to `view_order`. Enforced on **both** GET and POST.
- **GET:** build the catalogue payload exactly as `stock_orders.edit_order`
  does (`Item.query.filter_by(active=True)…` + `item_to_bom_json` with bulk
  demand maps + distinct categories), render `purchase_orders/edit.html`
  with `po`, `items`, `categories`.
- **POST:** update header fields from the form (same parsing as
  `save_order`: dates via `%Y-%m-%d`, `overall_discount_pct` float);
  delete existing lines (`POLine.query.filter_by(po_id=po.id).delete()` +
  flush) and recreate via `_build_lines_from_json`; commit; redirect to
  `view_order`. Wrapped in try/except with rollback + flash, mirroring
  `save_order`.
- **Status transition:** a `Draft` PO (e.g. one auto-created from a reorder
  shortfall) is promoted to `Open` on successful save — consistent with how
  `save_order` always produces an `Open` PO from a reviewed upload. An
  already-`Open` PO stays `Open`. No other transitions.

### 3.4 `edit_order` template — `templates/purchase_orders/edit.html`

Modelled on `templates/stock_orders/edit.html`, adapted for PO fields:
- Header form group: PO Number (read-only — it is the unique key; changing it
  is a re-import, out of scope), Reference, Supplier Name, Supplier VAT, PO
  Date, Due Date, Overall Discount %.
- Editable lines table: **Item** (picker cell), **Description**, **Qty**,
  **Excl. Price**, **Disc %**, computed **Excl. Total** / **Incl. Total**
  (JS recompute: `excl_total = qty * price * (1 - disc/100)`,
  `incl_total = excl_total * (1 + vat/100)`, `vat` carried per line, default
  15), remove-line button, and an "Add line" affordance (blank line whose
  Item is set via the picker).
- Hidden `lines_json` re-synced on every input/select and on submit, same
  `syncJSON()` pattern as STO edit.
- Warning banner: "Editing replaces all line items. Only editable while no
  stock has been received."

### 3.5 Detail page — `templates/purchase_orders/detail.html`

Add an **Edit** link to the Actions dropdown, shown only when the PO is
editable. Compute editability in the route (`view_order` passes
`editable=_po_is_editable(po)`) so the template stays logic-light:

```
{% if editable %}
<li><a href="{{ url_for('purchase_orders.edit_order', order_id=po.id) }}">Edit</a></li>
{% endif %}
```

### 3.6 Upload review screen — `templates/purchase_orders/upload.html`

- Replace the static line-items table with an editable one: each row keeps
  its parsed Qty / prices (read-only display + carried in `lines_json`) and
  gains an **Item** picker cell pre-filled with the auto-matched item (or
  empty + amber when unmatched).
- Pass the catalogue to the template: in `upload_order`'s POST branch, build
  the same `item_to_bom_json` payload and hand it to `render_template`.
- JS builds `lines_json` from row state (parsed fields + picker-set
  `matched_item_id` / `item_code` / `description`) on every change and on
  submit — so `save_order` is **unchanged** and still reads `matched_item_id`.
- Keep the existing "Unmatched lines are saved without a linked item" note,
  reworded to mention the picker.

## 4. Files touched

| File | Change |
|---|---|
| `routes/purchase_orders.py` | Add `edit_order`, `_build_lines_from_json`, `_po_is_editable`; pass `items` to upload render + `editable` to detail render |
| `templates/purchase_orders/edit.html` | **New** — PO edit screen |
| `templates/purchase_orders/detail.html` | Add conditional Edit action |
| `templates/purchase_orders/upload.html` | Per-line item picker + catalogue payload |
| `static/js/item_picker.js` | **New** — shared inline autocomplete |
| `tests/test_purchase_orders.py` | New `TestPurchaseOrderEdit` class |

No schema change (no migration needed) — reuses existing `PurchaseOrder` /
`POLine` columns.

## 5. Acceptance criteria

1. Editable Open/Draft PO shows an **Edit** action; a `Partially Received` /
   `Received` / `Cancelled` PO (or an Open PO with any receipt) does **not**,
   and hitting `/edit` on such a PO redirects with a flash.
2. Editing header fields persists them; editing/adding/removing lines
   replaces the line set correctly; a `Draft` PO becomes `Open` on save.
3. Existing save → receive → cancel behaviour is unchanged (the
   `_build_lines_from_json` refactor is transparent).
4. Upload review screen: an unmatched line can be linked via the picker
   before saving and persists with the chosen `item_id`; a wrong auto-match
   can be re-pointed before saving.
5. Offline-first preserved — no CDN/font references added.
6. Full suite green (339 currently) plus the new edit tests.

## 6. Out of scope

- Editing `PO Number` (unique key; that's a re-import).
- Editing quantities/prices after any receipt (blocked by design).
- A supplier master table / supplier autocomplete (still free-text).
- Per-line VAT override UI (VAT carried per line, defaults 15; not surfaced
  as an editable field in this pass).
