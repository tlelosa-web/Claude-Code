# SOPS — ERP/MRP Benchmark & Roadmap
**Date:** 2026-07-07 · **Author:** Claude (Research pattern, DCOE) · **Owner review:** Tebello Lelosa

---

## 1. Current State Summary

SOPS (Sales Order Processing System) is a Flask/SQLite desktop app covering one full loop:

```
Sales Order (PDF) → BOM Builder → Works Order (assembly) / Stock Order (pick)
                  → Dispatch confirmation → Stock deduction → Reports
```

Schema (6 core tables): `Item`, `SalesOrder`/`SOLineItem`, `WorksOrder`/`BOMLine` (self-referential for nested assemblies), `StockOrder`/`StockOrderLine`, `StockMovement`. 39 tests green as of Batch 12 (2026-07-06). Recent work (Batches 9–12) added multi-fan-line builds, per-line job numbers, a Close Order workflow, and delivery-date sorting.

This is a solid **Sales & Distribution + basic Inventory** module. It does not yet cover **Purchasing**, **MRP planning/netting**, or **Production routing/capacity** — the three legs that turn a stock-and-dispatch tool into an MRP system.

## 2. Gap Analysis vs. World-Class ERP/MRP (SAP B1, NetSuite, Odoo MRP, Fishbowl)

| ERP/MRP Standard Capability | SOPS Today | Gap |
|---|---|---|
| Demand netting (on-hand vs. on-order vs. required) | Shows on-hand only; shortfall is a point-in-time subtraction with no view of incoming supply | No visibility into what's already on order |
| Purchase Order / supplier management | None — no supplier entity, no PO, no goods receipt | Stock replenishment is entirely manual/off-system |
| Reorder point / min-max / safety stock | None — `Item` has no reorder fields | No proactive buy signal; shortfalls are discovered at build time |
| Routing / operations / labor & machine capacity | None — WO is a flat component list, no operation sequence or standard time | No production scheduling or capacity check |
| Lot/batch/serial traceability | None — `StockMovement` has no lot/serial field | No recall or warranty traceability |
| Standard vs. actual costing / variance | `last_cost`/`avg_cost` on `Item` only, no cost roll-up or variance report | Works Order doesn't report cost variance vs. BOM standard |
| Multi-warehouse / bin location | Single implicit location (`qty_on_hand` per item) | Not needed yet at current scale, but blocks future growth |
| Approval workflow / audit trail beyond stock | `StockMovement` logs qty changes; no approval gate on POs/WOs | Fine for current single-operator use; would matter if team grows |

SOPS is deliberately scoped and offline-first, which is the right call for a single-site production shop — most of the above (multi-warehouse, serial tracking) genuinely isn't needed yet. The three gaps that *do* matter at current scale are **purchasing visibility, reorder signals, and demand netting** — without them, every shortfall is discovered manually at BOM-build time rather than anticipated.

## 3. Proposed Next Steps (Roadmap)

Following DCOE — each of these should go through Domain (scope confirm) → Context (spec in `docs/specs/`) → Orchestrate → Execute, not straight to code.

1. **Purchase Order module** (new `PurchaseOrder`/`POLine` tables, supplier field on `Item` or new `Supplier` table, goods-receipt route that posts a `StockMovement` of type `RECEIPT` and updates `last_cost`). This is the prerequisite for #2 below.
2. **Reorder point + shortfall-to-PO workflow**: add `reorder_point`/`reorder_qty` to `Item`; a "Items Below Reorder Point" view; one-click "Create PO from shortfall" from the BOM Builder shortfall list.
3. **Demand netting on the shortfall calculation**: BOM Builder and Stock Report should show `qty_on_hand + qty_on_order − qty_committed` instead of raw on-hand, so a shortfall against a component that already has a PO in flight isn't flagged as urgent.
4. Longer-horizon, only once volume justifies it: routing/capacity (operation sequence + standard time per WO) and lot traceability.

Items 1–3 form one coherent spec (`docs/specs/purchasing-and-mrp-netting.md`) and should be planned as a single Context Agent pass, then executed in worktrees per component (models/migration, PO routes+templates, BOM Builder shortfall integration) since they touch >2 files each.

## 4. Three Concrete Enhancements

### Enhancement 1 — Purchase Order & Goods Receipt Module
**What:** Minimal `Supplier`, `PurchaseOrder`, `POLine` tables; PO create/list/detail/print (mirrors the existing SO/WO/STO pattern already in the codebase); a "Receive" action that posts a `StockMovement(movement_type='RECEIPT')` and updates `Item.last_cost`.
**Why (ERP standard):** Every MRP system closes the loop between "we need it" and "it arrived." Without this, SOPS tracks *outflow* (issues, picks) but has no system-of-record for *inflow* — replenishment currently happens entirely outside the tool.
**Effort:** Medium (1 new model group, 1 migration, ~4 routes, 3–4 templates, mirrors existing StockOrder pattern closely — low design risk).

### Enhancement 2 — Reorder Point / Min-Max Replenishment Signals
**What:** Add `reorder_point` and `reorder_qty` columns to `Item`; a Dashboard widget / Stock Report filter for "Below Reorder Point"; optional one-click PO draft generation from that list (depends on Enhancement 1).
**Why (ERP standard):** Min-max/reorder-point planning is the baseline replenishment method in every MRP system (it's MRP's simplest form, "Order Point System"). Right now shortfalls in SOPS are only discovered reactively when someone builds a BOM against a live Sales Order — by then it's often too late to reorder in time.
**Effort:** Small (2 columns + 1 migration, 1 report view, 1 dashboard card).

### Enhancement 3 — Demand-Netted Shortfall Calculation (MRP-lite netting)
**What:** Replace the current `qty_on_hand − qty_required` shortfall check in `bom_builder.py` with `(qty_on_hand + qty_on_order) − (qty_required + qty_committed_to_other_open_orders)`. Surface "on order, due <date>" inline in the BOM Builder shortfall row instead of just a flat amber flag.
**Why (ERP standard):** This is the core arithmetic of MRP (Material Requirements Planning) — netting gross requirements against all known supply, not just point-in-time stock. It prevents two failure modes SOPS is currently exposed to: false shortfalls (component is already inbound) and false confidence (on-hand stock is already promised to a different open Works Order).
**Effort:** Medium — requires Enhancement 1 (for `qty_on_order`) and a `qty_committed` aggregate query across open `BOMLine`/`StockOrderLine` rows; logic-only change to `services/bom_builder.py` and `services/stock_service.py`, no new tables beyond #1.

## 5. Suggested Sequencing

Enhancement 1 → 2 → 3, in that order — each depends on the previous. All three fit comfortably as one Pattern 1 (New Feature) cycle: single spec, single Planner pass, 3 Executor worktrees (PO model+routes, reorder UI, netting logic), one Reviewer pass (flag as `data-export`/`file-write` code touching stock integrity — reviewer on Opus per your model-routing rule).

---
*Filed under `docs/research/` per DCOE Pattern 5 (Research). Recommend Architect review before writing `docs/specs/purchasing-and-mrp-netting.md`.*
