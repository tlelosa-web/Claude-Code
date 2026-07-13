---
name: pattern-sto-item-code-join
description: StockOrderLine resolves to Item by item_code (string), not item_id FK — recurring join/lookup pattern to check for safe degradation.
metadata:
  type: project
---

`StockOrderLine` has NO `item_id` FK. It carries `item_code` (String) and resolves to a catalogue `Item` via `Item.code == StockOrderLine.item_code`. `Item.code` is `unique=True, nullable=False`, so the join is 1:1 and duplicate-safe. Unmatched/blank/NULL `item_code` drops the row from an inner join (degrades to 0, no crash).

Contrast: `BOMLine` and `POLine` use a real `item_id` FK (`POLine.item_id` is nullable — null until a PDF-extracted line is linked, and is excluded from qty_on_order).

**Why:** This asymmetry recurs across `stock_orders.complete_order()`, `stock_orders.reopen_order()`, and `services/demand.py::get_qty_committed_bulk()` (STO sub-query). Reviewers repeatedly need to confirm the code-based join handles unmatched codes gracefully.

**How to apply:** When reviewing STO-touching code, confirm item resolution goes through `item_code` and that unmatched codes are surfaced to the user (the routes flash a "no catalogue match" warning) or silently dropped (the aggregate queries) — never crash. Watch for anyone assuming a `StockOrderLine.item_id` that doesn't exist.
