# Spec — Purchase Order Module (Enhancement 1) + Reorder Signals (Enhancement 2)
**Revision:** 2 (adapted for Sage PO PDF upload) · **Date:** 2026-07-07 · **Status:** Shipped — Batch 13 (2026-07-07), commits `65f8443`, `15a265e`, `6f0dc53`, `b4bfdc4`, `c06a9f5`, `0b08b7c`, `fc63598`, `c0a5ceb`

## Why this revision

The two attached PDFs (`PO4088` — LUFT, `PO4106` — ATTENU-TEC) confirm Sage exports Supplier Purchase Orders in the **same template family** as the Sales Order PDFs SOPS already parses: same header block layout, same `Description / Quantity / Excl. Price / Disc % / VAT % / Excl. Total / Incl. Total` column geometry, same footer totals block. I verified this by extracting both PDFs with `pdfplumber` and diffing word coordinates against `services/pdf_parser.py`'s existing column thresholds — they line up exactly (see §3). That means Enhancement 1 is no longer just "build a PO module the user fills in by hand" — it should be **upload-first, mirroring the Sales Order flow**, with manual entry as a fallback.

One more finding worth flagging: the line-item description on POs is formatted `"<item_code> - <description>"` (e.g. `"IMP0560B150A10AR19080 - Impeller 0560mm 'B' 150A10AR 19mm 080Frame Deg00 - 15 DEG"`), and both sample item codes matched exactly against existing rows in `data/ItemListingReport.csv`. So PO lines can be **auto-linked to `Item` records** on upload, not just captured as free text.

---

## 1. PDF Field Mapping (from the two sample POs)

| Field | Source | Example |
|---|---|---|
| `po_number` | `NUMBER:\s*(PO\d+)` | `PO4088` |
| `reference` | `REFERENCE:\s*(\S+)` (reuses existing job-number filename regex too — `FM4167-4171` is a range, same pattern as SO reference) | `FM4167-4171` |
| `po_date` | `DATE:\s*(\d{2}/\d{2}/\d{4})` (label-anchored, not "first date found" — POs have 2 dates before line items, need explicit labels since order differs slightly from SO) | `26/06/2026` |
| `due_date` | `DUE DATE:\s*(\d{2}/\d{2}/\d{4})` | `30/06/2026` |
| `overall_discount_pct` | `OVERALL DISCOUNT %:\s*([\d.]+)%` | `0.00%` |
| `supplier_name` | Coordinate extraction, "TO" column (x0 ≥ 300, y-band ~190–208) — mirrors existing `customer_name` logic, just reading the right-hand block instead of left | `LUFT INDUSTRIES NATAL (PTY) LTD` |
| `supplier_vat` | `SUPPLIER VAT NO:\s*(\d+)` | `4050151630` |
| line items | Same column x-thresholds as `parse_line_item_row()` in `pdf_parser.py` — confirmed identical geometry | see below |

Line item table confirmed identical to SO parsing thresholds (desc <200, qty <240, price <300, disc <350, vat <410, excl-total <500, incl-total ≥500) — no new column-detection logic needed, only the header regexes above differ.

## 2. Item Code Auto-Match

For each parsed line, split `description` on the **first** `" - "` only (descriptions can contain further ` - ` inside, e.g. `"...Deg00 - 15 DEG"`):
- Candidate = text before first `" - "`.
- Look up `Item.query.filter_by(code=candidate).first()`.
- If matched → `POLine.item_id` set, `POLine.description` = remainder text.
- If not matched → `POLine.item_id` stays `None`, `POLine.item_code_raw` stores the candidate, full original description kept, and the upload-review screen flags it (amber, same visual language as BOM Builder shortfalls) for **manual item linking** — consistent with the "fault-tolerant parsing never crashes, returns partial results" hard constraint already in `README.md`.

## 3. Code Reuse / Refactor

`clean_numerical_str`, `build_merged_lines`, and `parse_line_item_row` in `services/pdf_parser.py` are template-geometry logic, not SO-specific. Extract them into a new `services/pdf_common.py` so both parsers use one implementation:

```
services/pdf_common.py        ← clean_numerical_str, build_merged_lines, parse_line_item_row, table-start/footer detection
services/pdf_parser.py        ← parse_sales_order_pdf() (SO-specific header regex/coords), imports from pdf_common
services/po_parser.py         ← parse_purchase_order_pdf() (PO-specific header regex/coords), imports from pdf_common
```

This avoids duplicating ~150 lines of coordinate-parsing logic (keeps files <300 lines per code standards) and means a future template-geometry bugfix (like the Batch 8 multi-page footer fix) only needs to happen once.

## 4. Data Model (Enhancement 1)

Denormalized supplier fields on `PurchaseOrder` for MVP — **no separate `Supplier` master table yet**. Rationale: reorder signals (Enhancement 2) don't need one, and every sample PO already carries supplier name/VAT inline, same pattern `SalesOrder.customer_name` already uses for customers. Revisit only if/when supplier-side reporting (e.g. spend-by-supplier) becomes a real need.

```python
class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_order'
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(100), unique=True, nullable=False)
    reference = db.Column(db.String(100))              # FM job number(s), from filename/REFERENCE
    supplier_name = db.Column(db.String(255))
    supplier_vat = db.Column(db.String(100))
    po_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    overall_discount_pct = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Draft')  # Draft / Open / Partially Received / Received / Cancelled
    raw_pdf_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    lines = db.relationship('POLine', backref='purchase_order', lazy=True, cascade='all, delete-orphan')

class POLine(db.Model):
    __tablename__ = 'po_line'
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)   # null until matched/linked
    item_code_raw = db.Column(db.String(100))           # as extracted, even if unmatched
    description = db.Column(db.Text)
    qty_ordered = db.Column(db.Float)
    qty_received = db.Column(db.Float, default=0.0)
    excl_price = db.Column(db.Float)
    disc_pct = db.Column(db.Float)
    vat_pct = db.Column(db.Float)
    excl_total = db.Column(db.Float)
    incl_total = db.Column(db.Float)
```

Migration: `scripts/migrate_add_purchase_order_tables.py`, following the existing migration script pattern (e.g. `migrate_add_so_line_job_number.py`).

## 5. Routes / Templates (Enhancement 1) — mirrors existing SO/STO pattern

```
GET  /purchase-orders                     list (sortable by due_date, mirrors Batch 12 pattern)
GET  /purchase-orders/upload              upload form
POST /purchase-orders/upload              parse PDF via po_parser, render review screen
POST /purchase-orders                     save reviewed/edited PO + lines (post-match confirmation)
GET  /purchase-orders/<id>                detail (lines, item-link status, receive action)
GET  /purchase-orders/<id>/print          A4 print document (mirrors stock_orders print.html)
POST /purchase-orders/<id>/link-item      manually link an unmatched POLine to an Item (inline on detail page)
POST /purchase-orders/<id>/receive        full or partial receipt
```

**Receive logic** (`services/stock_service.py`, extend the existing `issue()` counterpart with a `receive()`):
- For each line being received: `StockMovement(movement_type='RECEIPT', reference=po.po_number, qty_change=+qty)`, `Item.qty_on_hand += qty`, `Item.last_cost = line.excl_price`.
- `POLine.qty_received` accumulates; PO status becomes `Received` once every line's `qty_received >= qty_ordered`, else `Partially Received`.
- Blocked if `item_id` is null on a line (must be manually linked first) — surfaced as a flash error, not a crash.

## 6. Reorder Signals (Enhancement 2) — unchanged in essence, refined

```python
# Item model additions
reorder_point = db.Column(db.Float, default=0.0)
reorder_qty = db.Column(db.Float, default=0.0)
```

- New view/filter: "Items Below Reorder Point" (Stock Report filter + Dashboard card), condition `Item.qty_on_hand <= Item.reorder_point`.
- "Create PO from shortfall" action, now meaningful because Enhancement 1 exists: pre-fills a new `PurchaseOrder` (status `Draft`) with one `POLine` per flagged item at `reorder_qty`, `supplier_name` left blank for manual fill-in (no supplier master yet, so no auto-fill source — acceptable for MVP).
- This is also what unlocks `qty_on_order` for the later Enhancement 3 (demand-netted shortfall calc) — `qty_on_order` = `SUM(POLine.qty_ordered - POLine.qty_received)` across open POs for that item, which now has real data to sum once Enhancement 1 ships.

## 7. Test Plan

- `tests/fixtures/` — add the two sample PDFs (`PO4088`, `PO4106`) as regression fixtures, same convention as the SO multi-page fixture from Batch 8.
- `test_parse_purchase_order_pdf_luft` — verifies 5 line items, all auto-matched to existing `Item` codes, Grand Total = R 40,338.10.
- `test_parse_purchase_order_pdf_attenutec` — verifies 1 line item, auto-matched, Grand Total = R 20,345.80.
- `test_parse_purchase_order_unmatched_item_code` — synthetic case, code not in catalog → `item_id` None, `item_code_raw` populated, no crash.
- `test_receive_purchase_order_full` / `_partial` — stock movement posted, `qty_on_hand` and `last_cost` updated correctly, status transitions.
- `test_reorder_below_threshold_view` — items below `reorder_point` surfaced correctly.

## 8. Sequencing (unchanged from prior plan)

Enhancement 1 → 2, in that order — 2 depends on 1 only for the "Create PO from shortfall" action; the reorder-point flagging itself has no dependency and could ship first if you want a quick win, but the PO upload work is now well-scoped enough that doing 1 first is no longer a bottleneck.

---
*Supersedes the Enhancement 1 & 2 sections of `docs/research/erp-mrp-benchmark-2026-07-07.md`. Enhancement 3 (demand-netted shortfall calc) is unaffected by this revision.*
