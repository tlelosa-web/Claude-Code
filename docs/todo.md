# SOPS — Task Queue

## Batch 1 (Foundation)
- [x] Project scaffold: directory structure analysis
- [x] Models: `models.py` with all 6 ORM models
- [x] T-01: `app.py` Flask app factory + route registration + bootstrap sequence
- [x] T-02: Write `docs/todo.md` (this file)
- [x] DCOE-01: Align repository support structure with `AGENTS.md`
  - Created `docs/specs/`, `docs/research/`, `docs/bugs/`, `docs/decisions/`
  - Created `.Codex/agents/`, `.Codex/hooks/`, `.Codex/commands/`, `.Codex/worktrees/`
  - Added required specialist executor manifests
  - Moved the SOPS product brief to `docs/specs/sops-product-spec.md`

## Batch 2 (Parallel — Services + Vendor)
- [x] T-03: Routes & templates for Items (catalogue, detail, import)
- [x] T-04: Routes & templates for Sales Orders (upload, list, detail)
- [x] T-05: Vendor bundling — download Tabulator, Tom Select, Alpine.js, Inter font to `static/vendor/`

## Batch 3 (Core Logic — depends on Batch 2)
- [x] T-06: BOM Builder — `bom_builder.js` + item selection UI
- [x] T-07: Stock service — already complete (`services/stock_service.py`)

## Batch 4 (Documents + Reports — depends on Batch 3)
- [x] T-08: Works Orders routes + templates (detail, print)
- [x] T-09: Picking List template + confirm-pick flow
- [x] T-10: Reports routes + templates (stock report, movement report, CSV export)

## Batch 5 (Integration + Testing)
- [x] T-11: Dashboard — mostly complete, wire up remaining stats
- [x] T-12: Test suite — all 4 test files, `pytest` green
- [x] T-13: Print CSS — `@media print` blocks for WO/PL
- [x] T-14: Static assets — `main.css` full stylesheet, `bom_builder.js`, `adjustments.js`

## Maintenance
- [x] Fix upload review JSON serialization for parsed Sales Order line items
- [x] Fix BOM Builder item catalogue JSON serialization
- [x] Fix BOM Builder script initialization order so item selection works

## Works Pack Debug Session (2026-06-17)
- [x] Fix 1: Component search input wired up in build_bom.html (live search autocomplete)
- [x] Fix 2: Save Works Pack POST debug logging added (terminal confirms form keys)
- [x] Fix 3: `<form>` tag moved to wrap Sections 2+3+4 — line_role_* and component hidden inputs now POST correctly
- [x] Fix 4: StockOrder/StockOrderLine imports added to routes/sales_orders.py; catalogue_json serialisation hardened
- [x] E2E Verified: SO4652 (Setati Sol) — WO0001 created (2 BOM lines), STO0001 created (8 stock lines), SO status = Open

## Acceptance Criteria
All items below must be green before delivery:
- [x] `pip install -r requirements.txt && python app.py` starts with no errors
- [x] All 2,967 items import from CSV on first run
- [x] Upload SO4603 PDF → all fields parse correctly
- [x] BOM Builder shows items with correct Qty on Hand; shortfalls highlighted in amber
- [x] Assembly path: Works Order generated, printed to A4, "Mark Complete" deducts stock
- [x] Stock path: Picking List generated, "Confirm Pick" deducts stock
- [x] Stock adjustment updates qty_on_hand and records movement
- [x] Stock Report shows all items grouped by category with correct value
- [x] Movement Report filters by date range and item code
- [x] `pytest` — all tests green
- [x] `grep -r "cdn\." templates/` — returns empty (fully offline)
- [x] `grep -r "fonts.googleapis" static/` — returns empty
