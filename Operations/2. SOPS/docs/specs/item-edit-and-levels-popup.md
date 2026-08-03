# Spec — Edit Item + Adjust Stock/Levels as Popups, Max Level, Auto Reorder Qty

Status: Ready to build
Confirmed with Tebello via 3 rounds of AskUserQuestion (2026-07-14).

## Problem

`templates/items/detail.html` currently has two always-visible inline forms
("Manual Stock Adjustment", "Reorder Settings") and no way to edit an item's
own identity/pricing fields (code, description, category, active, costs,
prices) at all — those only ever get set via CSV import.

Reorder Qty (`Item.reorder_qty`) is a free-typed number today, with no
relationship to a maximum stock level.

## Scope decisions (confirmed)

1. **Edit Item** covers identity + pricing only: Code, Description, Category,
   Active, Last Cost, Avg Cost, Excl. Price, Incl. Price. **Qty on Hand is
   excluded** — it must keep going through `stock_service.adjust()` (the
   audited path with a required reason), never a free-text field.
2. **Reorder Qty** becomes auto-calculated (`Max Level - Reorder Point`),
   stored on `Item.reorder_qty` as today, auto-filled/refreshed whenever
   either input changes, but still a plain editable number the user can type
   over for a one-off exception. No enforcement that it must equal the
   calculation server-side — it's a convenience auto-fill, not a constraint.
3. **Two modals** on the Item detail page, replacing the two existing
   always-visible cards:
   - "Edit Item" — identity/pricing fields, posts to a new route.
   - "Adjust Stock & Levels" — Qty on Hand adjustment (+ reason, existing
     `adjust_stock` route, unchanged), Reorder Point, **Max Level (new)**,
     Reorder Qty (auto-calc default) — posts to the existing
     `update_reorder_settings` route, extended to accept `max_level`.
   Both triggered by buttons in the Item Details card header; Movement
   History table stays as-is (not modal, no change).

## Changes

### 1. `models.py`
- `Item.max_level = db.Column(db.Float, default=0.0)` — 0 means "not set",
  same convention as `reorder_point`.

### 2. `scripts/migrate_add_item_max_level.py` (new)
- Mirrors `scripts/migrate_add_stock_order_line_qty_issued.py` pattern:
  `ALTER TABLE item ADD COLUMN max_level FLOAT DEFAULT 0.0` if not present.
- Add matching self-heal entry in `app.py::ensure_schema_columns()` under the
  existing `if 'item' in inspector.get_table_names():` block.

### 3. `routes/items.py`
- New `POST /items/<id>/edit` route (`update_item`): reads code, description,
  category, active (checkbox), last_cost, avg_cost, excl_price, incl_price.
  Validates the 4 numeric fields parse as floats (flash + no-op on failure,
  same pattern as `update_reorder_settings`). Code must stay non-blank and
  unique (excluding itself) — flash + reject if a duplicate code is entered
  (mirrors the existing `unique=True` DB constraint; catch it explicitly
  rather than let it 500).
- `update_reorder_settings`: add `item.max_level = float(request.form.get('max_level', 0) or 0)`
  alongside the existing `reorder_point`/`reorder_qty` reads. No server-side
  recomputation of reorder_qty from max_level — the auto-calc is a
  client-side (JS) convenience only, per decision #2; the server just saves
  whatever three numbers it's given.

### 4. `templates/items/detail.html`
- Replace the "Manual Stock Adjustment" and "Reorder Settings" cards with:
  - An "Edit Item" button in the Item Details card header, opening an
    Edit Item modal (identity/pricing form, action = new `items.update_item`
    route).
  - An "Adjust Stock & Levels" button (near Qty on Hand in the second
    column), opening a modal containing: the existing Qty-on-Hand adjustment
    form fields (new_qty, adjusted_by, reason → `items.adjust_stock`) and the
    existing Reorder Point / Reorder Qty fields + new Max Level field
    (→ `items.update_reorder_settings`). Keep these as two separate `<form>`
    elements inside one modal (two independent submits, matching today's two
    separate routes) — do not merge into a single form/route.
- Modal mechanics: use Alpine.js (already vendored via `base.html`, unused
  elsewhere so far) — `x-data="{ open: false }"` on a wrapping element,
  `x-show`/`@click` for open/close, backdrop click and Escape key close it.
  No new vendor dependency.
- Reorder Qty auto-calc: small inline script (or Alpine `x-effect`) — on
  input to either Reorder Point or Max Level, set Reorder Qty's value to
  `max(0, max_level - reorder_point)`, only while the field hasn't been
  manually edited since the modal opened (track a `dirty` flag so a manual
  override isn't silently clobbered by continuing to type in the other two
  fields). Simplest correct approach: recompute on Reorder Point / Max Level
  input unless the user has directly focused/edited the Reorder Qty field
  first in this modal session.
- No changes to Movement History table.

### 5. Tests
- `tests/test_items.py` (existing or new file — check for one first): new
  tests for `update_item` — success updates all fields, duplicate code
  rejected with flash + no changes persisted, invalid numeric input rejected.
- Extend the existing reorder-settings test(s) to cover `max_level` being
  saved.
- No test needed for the client-side auto-calc JS (no JS test harness in
  this project — out of scope, matches existing precedent e.g.
  `resizable_columns.js`).

## Out of scope (explicitly declined this round)
- Editing Qty on Hand outside the audited adjust path.
- Server-side enforcement/validation that Reorder Qty == Max - Min.
- Catalogue-page (list view) inline editing — this is Item detail page only.
- Any change to `create_from_shortfall()`, Stock Report, or Dashboard — they
  already read `reorder_qty`/`reorder_point` and need no change since the
  storage shape doesn't change.

## Acceptance criteria
- [ ] `Item.max_level` column exists, migrates cleanly on a real DB via
      self-heal (`ensure_schema_columns()`) with no manual migration run
      required (consistent with every other Item column added so far).
- [ ] Item detail page: "Edit Item" modal opens, saves identity/pricing
      fields, validates duplicate code.
- [ ] Item detail page: "Adjust Stock & Levels" modal opens, contains both
      the stock-adjust form and the reorder-settings form (incl. new Max
      Level field), both submit independently to their existing routes.
- [ ] Reorder Qty auto-fills as Max Level / Reorder Point are typed, but a
      manual edit to Reorder Qty itself is not overwritten within the same
      modal session.
- [ ] Full test suite green, no regressions.
- [ ] Offline-first re-verified (no new `cdn.`/`fonts.googleapis` refs).
