---
name: pattern-qty-on-hand-none-guard
description: Inline availability calcs omit the `or 0.0` NULL guard that the service layer uses — latent TypeError on NULL qty_on_hand.
metadata:
  type: project
---

`Item.qty_on_hand` is `db.Column(db.Float, default=0.0)` — the default applies at INSERT, but legacy/imported rows can still hold NULL. `services/demand.py::get_available_qty()` defensively uses `(item.qty_on_hand or 0.0)`, and `item_to_bom_json()` uses `item.qty_on_hand or 0.0`. But the inline calcs in `services/doc_generator.py` (line ~44/71) and `routes/reports.py` (stock_data / export_csv) use bare `item.qty_on_hand + ...`, which raises `TypeError: unsupported operand ... NoneType` if the value is NULL.

Same latent issue applies to summed line quantities (`qty_ordered`, `qty_required`, `qty`) — but those go through SQL `func.sum`, where NULL terms are ignored, so they degrade to 0 safely. The exposure is specifically the Python-side `item.qty_on_hand` arithmetic.

**Why:** Noted during Enhancement 3 review (2026-07). Low likelihood in practice (importer sets a value) but it is inconsistent guarding that will bite on any hand-edited or partially-migrated row.

**How to apply:** When reviewing any Python-side availability/stock-value arithmetic, check for the `or 0.0` guard on `item.qty_on_hand`. Recommend matching the service-layer defensive style rather than trusting the column default.
