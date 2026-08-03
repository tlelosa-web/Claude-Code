## Task: Support multiple Fan/assembly lines per Sales Order in Build Works Pack

**Domain:** Software / AI

**Goal:** Allow a Sales Order with several distinct Fan/assembly line items (e.g. SO4684 —
5 MAXFLO fan lines) to produce one separate Works Order per Fan line, instead of the current
hard stop at "Only one line can be marked as Fan."

**Inputs:**
- `SalesOrder` with N `SOLineItem` rows, several classified as role=`fan` on `/sales-orders/<id>/build-bom` POST
- Shared "BOM Components" panel, each added component row tagged with which Fan line it belongs to (dropdown)

**Outputs:**
- One `WorksOrder` (order_type=`ASSEMBLY`) per selected Fan line, each with a sequential `wo_number`
  (`WO0001`, `WO0002`, ...), each containing exactly one `ASSEMBLY_ITEM` `BOMLine` (the fan item) with
  its assigned components nested as `COMPONENT` children (`parent_line_id`)
- Stock-classified lines still collapse into a single shared `StockOrder`, unchanged from current behaviour
- `sales_orders/detail.html` already lists `wos` as a collection — no template change needed there

**Constraints:**
- Decision (confirmed by Tebello 2026-07-01): 5 fan lines → 5 separate Works Orders, not one WO with
  5 nested assemblies.
- Decision: keep the single shared "BOM Components" list UI; add a per-row dropdown to assign each
  component to one of the currently-checked Fan lines, rather than repeating the whole panel per fan.
- Backward compatible: existing single-fan POSTs that omit `component_fan_line_id[]` must keep working
  (all components default to the one selected fan line) — covered by
  `test_build_bom_persists_fan_as_assembly_parent`.
- No schema changes — `WorksOrder.so_id` already has no uniqueness constraint; only `wo_number` is unique.
- Component rows with no fan assigned when 2+ fan lines are selected are dropped with a warning flash,
  not silently attached to the wrong assembly.

**Acceptance Criteria:**
- Selecting 2+ lines as `fan` no longer flashes "Only one line can be marked as Fan" / blocks the POST.
- POSTing SO4684-shaped data (5 fan lines, per-component fan assignment) creates 5 `WorksOrder` rows,
  each with 1 `ASSEMBLY_ITEM` line and only its own assigned `COMPONENT` children.
- Existing single-fan test (`test_build_bom_persists_fan_as_assembly_parent`) still passes unmodified.
- Full test suite green.

**Out of Scope:** Changing Stock Order grouping behaviour; changing the WO print/detail templates
(they already iterate `wos` as a list); combining fan lines into one WO (rejected option).
