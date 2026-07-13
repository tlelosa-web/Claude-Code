---
name: pattern-shortfall-duplication
description: Availability/shortfall math is duplicated across many call sites in SOPS — check every copy when reviewing changes to the calc.
metadata:
  type: project
---

The `available = qty_on_hand + qty_on_order - qty_committed` / `shortfall = max(0, required - available)` calc is NOT centralized in one render path. It is re-implemented inline at multiple sites:

- `services/demand.py` (the canonical service — `get_available_qty`, `get_qty_*_bulk`)
- `services/doc_generator.py::get_works_order_print_context()` (WO detail + print) — inline, twice (top-level line + nested component loop)
- `routes/reports.py` Stock Report `/data` and `/export-csv` — inline, separately
- `routes/sales_orders.py::item_to_bom_json()` (BOM builder payload) — inline
- `static/js/bom_builder.js` — inline in JS
- `routes/dashboard.py` reorder_count stat card — still RAW `qty_on_hand` (NOT netted as of Enhancement 3)

**Why:** During Enhancement 3 (demand-netted shortfall, 2026-07) the author found and fixed THREE separate un-netted copies mid-session (BOM edit pages, Stock Report, then doc_generator). The dashboard reorder card was left un-netted, creating a divergence with the Stock Report's "Below Reorder Point" filter.

**How to apply:** When any shortfall/availability change lands, grep `available_qty|qty_on_hand|shortfall|reorder` across routes/, services/, static/js/, templates/ and confirm every decision-driving site uses the same definition. Flag any new un-netted copy. Recommend consolidation toward `services/demand.py` when touched.
