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
- [ ] T-03: Routes & templates for Items (catalogue, detail, import) — partially done
- [ ] T-04: Routes & templates for Sales Orders (upload, list, detail)
- [ ] T-05: Vendor bundling — download Tabulator, Tom Select, Alpine.js, Inter font to `static/vendor/`

## Batch 3 (Core Logic — depends on Batch 2)
- [ ] T-06: BOM Builder — `bom_builder.js` + item selection UI
- [ ] T-07: Stock service — already complete (`services/stock_service.py`)

## Batch 4 (Documents + Reports — depends on Batch 3)
- [ ] T-08: Works Orders routes + templates (detail, print)
- [ ] T-09: Picking List template + confirm-pick flow
- [ ] T-10: Reports routes + templates (stock report, movement report, CSV export)

## Batch 5 (Integration + Testing)
- [ ] T-11: Dashboard — mostly complete, wire up remaining stats
- [ ] T-12: Test suite — all 4 test files, `pytest` green
  - Verified passing: `test_pdf_parser.py`, `test_item_importer.py`, `test_bom_builder.py`
  - Blocked: full suite / `test_stock_service.py` due local `flask_sqlalchemy` import hang; see `docs/bugs/pytest-flask-sqlalchemy-import-hang.md`
- [ ] T-13: Print CSS — `@media print` blocks for WO/PL
- [ ] T-14: Static assets — `main.css` full stylesheet, `bom_builder.js`, `adjustments.js`

## Acceptance Criteria
All items below must be green before delivery:
- [ ] `pip install -r requirements.txt && python app.py` starts with no errors
- [ ] All 2,967 items import from CSV on first run
- [ ] Upload SO4603 PDF → all fields parse correctly
- [ ] BOM Builder shows items with correct Qty on Hand; shortfalls highlighted in amber
- [ ] Assembly path: Works Order generated, printed to A4, "Mark Complete" deducts stock
- [ ] Stock path: Picking List generated, "Confirm Pick" deducts stock
- [ ] Stock adjustment updates qty_on_hand and records movement
- [ ] Stock Report shows all items grouped by category with correct value
- [ ] Movement Report filters by date range and item code
- [ ] `pytest` — all tests green
- [ ] `grep -r "cdn\." templates/` — returns empty (fully offline)
- [ ] `grep -r "fonts.googleapis" static/` — returns empty
