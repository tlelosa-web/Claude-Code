# Spec: Demand-Netted Shortfall Calculation (Enhancement 3)

**Status:** Shipped — Batch 18 (2026-07-14), commits `3e4c0ed`, `03109bf`, `638b70d`, `ea3e032`, `46d0724`, `f4fce5d`. Follow-on gap (build_bom.html display) closed separately by Batch 20 (`docs/specs/build-bom-shortfall-display.md`).
**Depends on:** Enhancement 1 (Purchase Orders, shipped Batch 13) — no new tables needed.
**Origin:** `docs/research/erp-mrp-benchmark-2026-07-07.md` §4, Enhancement 3. Scope decisions below confirmed with Tebello via AskUserQuestion on 2026-07-13.

## Problem

BOM Builder's shortfall check (`static/js/bom_builder.js:293`) and the Stock Report are both driven by raw `Item.qty_on_hand` only. This produces two false signals:

1. **False shortfall** — a component already has a Purchase Order inbound, but shows as a hard shortage because `qty_on_order` isn't tracked anywhere in the calc.
2. **False confidence** — on-hand stock is already promised to a different open Works/Stock Order, but shows as fully available to a second order being built against the same item.

## Scope decisions (confirmed with Tebello)

- **Netting scope:** `qty_committed` counts outstanding demand from **all open Works/Stock Orders system-wide**, not just orders for the same customer/SO as the one currently being built. This matches standard MRP netting.
- **Surface area:** the netted number replaces the current on-hand-only view in **both** BOM Builder and the Stock Report — not BOM-Builder-only.

## Formula

```
available = qty_on_hand + qty_on_order - qty_committed
shortfall = max(0, qty_required - available)
```

Where, per item:

- **`qty_on_order`** = `sum(POLine.qty_ordered - POLine.qty_received)` across `POLine.item_id == item.id`, joined to `PurchaseOrder`, filtered to `PurchaseOrder.status not in ('Received', 'Cancelled')`.
- **`qty_committed`** = outstanding demand across two sources, summed:
  - `sum(BOMLine.qty_required - BOMLine.qty_issued)` where `BOMLine.item_id == item.id`, `BOMLine.line_type != 'ASSEMBLY_ITEM'`, joined to `WorksOrder`, filtered to `WorksOrder.status in ('Open', 'In Progress')`.
  - `sum(StockOrderLine.qty - StockOrderLine.qty_issued)` where `StockOrderLine.item_code == item.code` (STO lines key by code, not `item_id` — same resolution pattern already used in `stock_orders.complete_order()`), joined to `StockOrder`, filtered to `StockOrder.status == 'Open'`.

Both sums default to `0` when no rows match (unmatched-item POs, i.e. `POLine.item_id IS NULL`, are excluded from `qty_on_order` — they haven't been linked to a catalogue item yet, same as today's "Link Item" fixup flow).

## Changes

**`services/stock_service.py`** (or a new `services/demand.py` if the file is getting crowded — decide at build time): add `get_qty_on_order(item_id)` and `get_qty_committed(item_id)` as the two aggregate queries above, plus a convenience `get_available_qty(item_id)` returning `qty_on_hand + qty_on_order - qty_committed`.

**`routes/sales_orders.py` `item_to_bom_json()`**: add `qty_on_order` and `qty_committed` (or a single `available_qty`) to the JSON payload sent to BOM Builder. Also surface the earliest `PurchaseOrder.due_date` among that item's open/partial POs (if any) as `next_po_due` — this backs the "on order, due `<date>`" inline hint.

**`static/js/bom_builder.js`**: shortfall formula at line 293 changes from `qty_required - item.qty_on_hand` to `qty_required - item.available_qty`. Row display (currently just the flat amber flag) gains a small "on order, due `<next_po_due>`" hint when `qty_on_order > 0`, so a shortfall against an item with inbound stock reads differently from one with none.

**`routes/reports.py` / `templates/reports/stock.html`**: Stock Report's per-item row switches from `qty_on_hand` to the same netted `available_qty` for its "Below Reorder Point" comparison and general display — needs a column addition (or a tooltip/sub-value) so `qty_on_hand` itself isn't lost from view entirely, since it's still the ground-truth physical count.

**No schema change** — this is a query + display change only, no migration needed.

## Performance note

Both aggregates are per-item queries. The BOM Builder catalogue page and Stock Report render N items in one page load, so this needs to be one batched query per aggregate (grouped by `item_id`/`item_code`), not N+1 queries in a loop — worth flagging explicitly to whoever builds this, since the existing `item_to_bom_json()` loop pattern would tempt an N+1 if copied naively.

## Test plan

- Unit tests for `get_qty_on_order()` / `get_qty_committed()` against constructed Item/PO/WO/STO fixtures — covering: no open orders (0), one open PO not yet received (full qty), partially received PO (remainder only), Received/Cancelled POs excluded, one open WO line partially issued (remainder only), Complete/Cancelled WOs excluded, same for STO lines.
- BOM Builder integration test: item with on-hand shortfall but sufficient `qty_on_order` no longer flags a shortfall in the served JSON.
- BOM Builder integration test: item with sufficient on-hand but fully committed to another open WO/STO does flag a shortfall.
- Stock Report test: netted `available_qty` (not raw `qty_on_hand`) drives the "Below Reorder Point" filter.

## Effort estimate

Medium — one new service module/functions, one route payload change, one JS formula + display change, one report route/template change, no migration. Comparable in size to Batch 16.

## Sequencing suggestion

Single Planner pass → 2-3 atomic commits: (1) service-layer aggregate queries + tests, (2) BOM Builder wiring (route JSON + JS formula/display) + tests, (3) Stock Report wiring + tests. Reviewer pass recommended before merge since this touches the shortfall decision that drives real purchasing/stock behavior.
