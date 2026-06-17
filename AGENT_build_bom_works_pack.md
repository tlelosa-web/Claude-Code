# AGENT PROMPT — Build BOM / Works Pack Feature
# SOPS · Flask / SQLite / Jinja2
# Version: 1.0 | Date: 2026-06-12

---

## CONTEXT

You are implementing the **Build BOM / Works Pack** feature for SOPS (Sales Order Processing
System), a Flask/SQLite/Jinja2 offline desktop web app for Fan Movement (Pty) Ltd.

### Stack
- Backend: Flask, SQLAlchemy, SQLite (`instance/sops.db`)
- Frontend: Jinja2 templates, plain HTML/CSS — no JS frameworks
- Blueprints live in: `sops/routes/`
- Models live in: `sops/models.py`
- Templates live in: `templates/`
- App factory in: `sops/app.py`

### Existing models relevant to this feature
```python
SalesOrder       # so_number, customer_name, delivery_date, status, etc.
SOLineItem       # so_id (FK), description, qty, excl_price, vat_pct, excl_total
WorksOrder       # wo_number, so_id (FK), order_type, status, bom_lines relationship
BOMLine          # wo_id (FK), item_id (FK), qty_required, qty_issued, unit_cost, notes
Item             # code, description, category, excl_price, qty_on_hand, active
```

### Existing blueprint files (do not break these)
```
sops/routes/dashboard.py
sops/routes/items.py
sops/routes/sales_orders.py
sops/routes/works_orders.py
sops/routes/reports.py
```

---

## OBJECTIVE

Build the full **Build BOM / Works Pack** flow, triggered from the SO detail page.
This flow allows the user to:
1. Classify each SO line item as: Fan (WO subject) | Stock Order | Ignore
2. Build a BOM for the fan (select components from item catalogue)
3. Save — creating a WorksOrder + BOMLines and/or a StockOrder + StockOrderLines
4. See both linked on the SO detail page under "Related Works Orders / Picking Lists"

---

## TASK 1 — Add New Models to `sops/models.py`

Add the following two models. Do NOT modify any existing model.

```python
class StockOrder(db.Model):
    __tablename__ = 'stock_order'

    id = db.Column(db.Integer, primary_key=True)
    stock_order_number = db.Column(db.String(100), unique=True, nullable=False)
    so_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'), nullable=False)
    status = db.Column(db.String(50), default='Open')  # Open / Complete / Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lines = db.relationship('StockOrderLine', backref='stock_order', lazy=True,
                            cascade='all, delete-orphan')
    sales_order = db.relationship('SalesOrder', backref='stock_orders')


class StockOrderLine(db.Model):
    __tablename__ = 'stock_order_line'

    id = db.Column(db.Integer, primary_key=True)
    stock_order_id = db.Column(db.Integer, db.ForeignKey('stock_order.id'), nullable=False)
    item_code = db.Column(db.String(100))
    description = db.Column(db.Text)
    qty = db.Column(db.Float)
    notes = db.Column(db.Text)
```

Also add a helper method to `SalesOrder` for generating the next SO-linked WO number:
```python
# No model change needed — WO number generation is handled in the route (see Task 2)
```

---

## TASK 2 — Create `sops/routes/stock_orders.py` Blueprint

```python
from flask import Blueprint
stock_orders_bp = Blueprint('stock_orders', __name__)
```

Add these routes:

### `GET /stock-orders/`
List all StockOrders. Template: `templates/stock_orders/list.html`
Columns: Stock Order Number | SO Reference | Customer | Status | Created

### `GET /stock-orders/<id>`
Detail view. Template: `templates/stock_orders/detail.html`
Show header fields + line items table.

### `POST /stock-orders/<id>/cancel`
Set status → 'Cancelled'. Guard: cannot cancel if status is 'Complete'.
Redirect to detail page.

---

## TASK 3 — Register New Blueprint in `sops/app.py`

Add to the blueprint registration block:
```python
from sops.routes.stock_orders import stock_orders_bp
app.register_blueprint(stock_orders_bp)
```

---

## TASK 4 — Build BOM Route in `sops/routes/sales_orders.py`

### `GET /sales-orders/<id>/build-bom`

Logic:
1. Load the SalesOrder by id. If not found → 404.
2. Check if a WorksOrder already exists for this SO (`WorksOrder.query.filter_by(so_id=id).first()`).
   If yes → flash "A Works Order already exists for this Sales Order." and redirect to
   `/sales-orders/<id>`.
3. Load all SOLineItems for this SO.
4. Load all active Items from the catalogue for the component search panel.
5. Render `templates/sales_orders/build_bom.html` with:
   - `so` — the SalesOrder object
   - `line_items` — list of SOLineItems
   - `catalogue_items` — all active Items (for BOM component selection)

### `POST /sales-orders/<id>/build-bom`

Receives form data:

```
# Line classification (one per SO line item)
line_role_<solineitem_id>  = "fan" | "stock" | "ignore"

# BOM components (repeating, for fan WO)
component_item_id[]   = item.id (from catalogue)
component_qty[]       = float

# Fan line identity
fan_line_id           = solineitem_id of the line marked as "fan"
```

Logic:
```
1. Parse form data.

2. Identify fan_line_id and stock_line_ids from line_role_* fields.

3. IF fan line selected:
   a. Auto-generate WO number:
      Last WO number in DB → increment. Format: "WO{NNNN}" e.g. "WO0042".
      If no WOs exist yet → start at "WO0001".
   b. Create WorksOrder:
      - wo_number = generated
      - so_id = so.id
      - order_type = 'ASSEMBLY'
      - status = 'Open'
   c. For each component_item_id[i] / component_qty[i] pair:
      - Skip if item_id is empty or qty <= 0
      - Load Item by id → get unit_cost from item.last_cost
      - Create BOMLine(wo_id, item_id, qty_required, unit_cost)
   d. db.session.add(works_order) — flush to get wo.id before adding BOMLines

4. Identify stock lines (role == "stock"):
   IF any stock lines exist:
   a. Auto-generate Stock Order number:
      Format: "STO{NNNN}" — same increment logic as WO numbers.
   b. Create StockOrder(stock_order_number, so_id, status='Open')
   c. For each stock SOLineItem:
      - Parse item_code from description (text before first " - " separator)
      - Create StockOrderLine(item_code, description, qty)

5. Update SalesOrder status → 'Open' (from 'Draft')

6. db.session.commit()

7. flash("Works Pack created successfully.")
8. Redirect to /sales-orders/<id>
```

**Error handling:**
- Wrap the entire save block in try/except. On exception: db.session.rollback(),
  flash the error message, re-render the build_bom page.
- If neither fan nor stock lines are selected → flash warning, do not save.

---

## TASK 5 — Templates

### `templates/sales_orders/build_bom.html`

Extend `base.html`. Page title: "Build Works Pack — {{ so.so_number }}"

**Section 1: SO Header (read-only)**
Display in a card: SO Number, Customer, Delivery Date, Sales Rep.

**Section 2: Classify Line Items**
Table with columns: # | Description | Qty | Role
For each SOLineItem, render a radio group in the Role column:
```html
<input type="radio" name="line_role_{{ line.id }}" value="fan"> Fan / WO Subject
<input type="radio" name="line_role_{{ line.id }}" value="stock" checked> Stock Order
<input type="radio" name="line_role_{{ line.id }}" value="ignore"> Ignore
```
Default selection: "Stock Order" for all lines.
Add a small note: "Only one line can be marked as Fan."
Use inline JS to enforce single-fan selection (uncheck other fan radios when one is selected).

**Section 3: BOM Components (shown always, user adds if fan selected)**
Heading: "BOM Components (for Fan / Assembly WO)"
Sub-note: "If no Fan line is selected above, this section is ignored."

Component add panel:
- Searchable dropdown (plain `<select>` with all catalogue_items, format: "CODE — Description")
- Qty input (number, min 0.1, step 0.1)
- "Add Component" button → JS appends a row to the components table below

Components table (dynamic, starts empty):
Columns: Item Code | Description | Qty | Remove

Hidden inputs added dynamically per row:
```html
<input type="hidden" name="component_item_id[]" value="{{ item.id }}">
<input type="hidden" name="component_qty[]" value="{{ qty }}">
```

**Section 4: Actions**
```html
<button type="submit">Save Works Pack</button>
<a href="/sales-orders/{{ so.id }}">Cancel</a>
```

---

### `templates/stock_orders/list.html`

Extend `base.html`. Title: "Stock Orders"
Table: Stock Order No | SO Reference | Customer | Status | Created | Actions (View)
Empty state: "No stock orders found."

### `templates/stock_orders/detail.html`

Extend `base.html`. Title: "Stock Order: {{ stock_order.stock_order_number }}"

Header card: Stock Order No, SO Reference, Customer, Delivery Date, Status, Created.

Line items table: # | Item Code | Description | Qty | Notes

Actions: Cancel Order button (POST to `/stock-orders/<id>/cancel`) — only shown if
status is 'Open'. Back to SO link.

---

## TASK 6 — Update SO Detail Page

File: `templates/sales_orders/detail.html`

Find the "Related Works Orders / Picking Lists" section. Update it to show:

**Works Orders sub-table** (if any exist):
Columns: WO Number | Type | Status | Created | Actions (View)
Link View → `/works-orders/<wo.id>`

**Stock Orders sub-table** (if any exist):
Columns: Stock Order No | Status | Created | Actions (View)
Link View → `/stock-orders/<so.id>`

Both tables under the same section heading with a divider between them.
"Create New" button → `/sales-orders/<so.id>/build-bom`
Disable (grey out) "Create New" if a WorksOrder already exists for this SO.

---

## TASK 7 — Add Stock Orders to Navigation

File: `templates/base.html` (or wherever the sidebar nav is defined)

Add a nav link: **Stock Orders** → `/stock-orders/`
Place it below "Works Orders" in the sidebar.

---

## ACCEPTANCE CRITERIA

- [ ] User can open SO detail page and click "Build BOM / Works Pack" or "Create New"
- [ ] Build BOM page shows all SO line items with radio classification
- [ ] User can mark one line as Fan, rest as Stock Order or Ignore
- [ ] User can add BOM components from item catalogue with qty
- [ ] Saving creates WorksOrder + BOMLines (if fan selected)
- [ ] Saving creates StockOrder + StockOrderLines (if stock lines selected)
- [ ] SO status updates to 'Open' after save
- [ ] Both WO and Stock Order appear in "Related" section on SO detail page
- [ ] "Create New" button is disabled/greyed if WO already exists for the SO
- [ ] Stock Orders list and detail pages render correctly
- [ ] Stock Orders link appears in sidebar navigation
- [ ] SO with no fan line (stock only) creates StockOrder only — no WorksOrder
- [ ] Attempting to create a second WO for the same SO is blocked with a flash message
- [ ] All DB errors are caught, rolled back, and flashed to the user

---

## DO NOT

- Do not modify existing models (SalesOrder, SOLineItem, WorksOrder, BOMLine, Item,
  StockMovement)
- Do not change existing route paths for sales_orders or works_orders
- Do not use any JS framework — plain vanilla JS only for dynamic BOM rows
- Do not add pricing/cost fields to StockOrderLine — description and qty only for now
- Do not delete or alter existing templates outside of the specific sections noted above

---

## FILE SUMMARY — What to create / modify

| Action | File |
|--------|------|
| MODIFY | `sops/models.py` — add StockOrder, StockOrderLine |
| CREATE | `sops/routes/stock_orders.py` |
| MODIFY | `sops/app.py` — register stock_orders_bp |
| MODIFY | `sops/routes/sales_orders.py` — add GET+POST build-bom routes |
| CREATE | `templates/sales_orders/build_bom.html` |
| CREATE | `templates/stock_orders/list.html` |
| CREATE | `templates/stock_orders/detail.html` |
| MODIFY | `templates/sales_orders/detail.html` — Related section |
| MODIFY | `templates/base.html` — add Stock Orders nav link |

---

*One task. One commit. Test each acceptance criterion before committing.*
