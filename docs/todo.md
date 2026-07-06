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

## Batch 6 — Remaining Plan Items (2026-06-29)
- [x] Fix 1: Add GET guard to `build_bom` — redirects with flash if WO already exists (spec requirement, was POST-only)
- [x] Fix 2: Remove debug `print()` statements from `build_bom` POST handler
- [x] Fix 3: Replace all `Query.get()` legacy calls with `db.session.get()` in routes (items.py, sales_orders.py, works_orders.py)
- [x] Fix 4: Replace `datetime.utcnow()` with `datetime.now()` in routes (works_orders.py, sales_orders.py)
- [x] Fix 5: Add `POST /stock-orders/<id>/complete` route — StockOrder had `Complete` status with no way to set it
- [x] Fix 6: Add Mark Complete button to `templates/stock_orders/detail.html`
- [x] Fix 7: Add `tests/test_stock_orders.py` — 8 tests covering list, detail, cancel, complete (all passing)
- [x] Commit: `520f955` — all 25 tests green

## Batch 7 — Edit Fixes (2026-06-29, commit pending 2026-07-01)
- [x] Fix WO edit: existing BOM line qty fields now render as editable inputs (not static text); buildPayloadFromRow always reads from input
- [x] Add STO edit: GET/POST /stock-orders/<id>/edit route, templates/stock_orders/edit.html (inline editable table + add/remove lines), Edit button on detail page (Open status only)

## Batch 8 — Multi-page SO PDF Parser Fix (2026-07-01)
- [x] Bug: `services/pdf_parser.py` silently dropped all line items on page 2+ of multi-page Sales Order PDFs — footer text ("BANKING DETAILS"/"Total Discount:") repeats on every page of the template, and the old code treated hitting it on page 1 as end-of-document, breaking the outer page loop before page 2 was scanned.
- [x] Fix 1: Scoped the footer-detected `break` to the current page's line loop only, instead of stopping the whole document.
- [x] Fix 2: Reset `table_started` at the start of every page (header/title/FROM-TO block also repeats per page) so continuation pages re-detect the "Description/Quantity" column header instead of misparsing the repeated header block as line items.
- [x] Added `tests/fixtures/FM4167-4771 - Vortron - Sales Order - SO4684.pdf` (real 2-page SO) and `test_parse_multipage_captures_all_line_items` regression test — verifies 16 line items across both pages, sum matches Grand Total (R241,125.00).
- [x] Verified: all 26 tests green, no regressions.

## Batch 9 — Multi-Fan-Line Build Works Pack (2026-07-01)
- [x] Gap: SO4684 (once fully parsed by Batch 8) has 5 distinct Fan lines (MAXFLO 560/250/14, 560/250/14 1.10KW, 800/250/14 4.00KW, 800/250/14 5.50KW x2) — `build_bom` hard-stopped with "Only one line can be marked as Fan."
- [x] Decision (Tebello, spec `docs/specs/multi-fan-build-bom.md`): 5 fan lines → 5 separate Works Orders; keep single shared BOM Components list with a per-row "For Fan line..." dropdown instead of repeating the whole panel per fan.
- [x] `routes/sales_orders.py build_bom`: classify multiple `fan_line_ids`, generate one WorksOrder + ASSEMBLY_ITEM header per fan line, group submitted components by `component_fan_line_id[]` (defaults to the single fan line when only one is selected, for backward compatibility).
- [x] `templates/sales_orders/build_bom.html`: removed `enforceSingleFan` single-select restriction; added `componentFanLine` dropdown populated from currently-checked Fan radios via `refreshFanLineOptions()`.
- [x] Added `test_build_bom_creates_separate_wo_per_fan_line` — verifies 2 fan lines produce 2 WOs with correctly scoped components; existing single-fan test unmodified and still passing.
- [x] Verified against the real SO4684 scenario (lines 1,3,6,10,12 as Fan) end-to-end: 5 WOs created (WO0001–WO0005), each matched to the correct catalogue item; remaining 11 lines collapsed into 1 Stock Order.
- [x] Full suite: 27 tests green.

## Batch 10 — STO Print + Required FM Number on Build Works Pack (2026-07-02)
- [x] `routes/stock_orders.py`: added `GET /stock-orders/<id>/print` route (no status guard, mirrors `works_orders.print_order`).
- [x] `templates/stock_orders/print.html`: new standalone print document (modeled on `picking_list_print.html`) — STO/SO/customer/job-number info table, line items, signoff block, auto-print script.
- [x] `templates/stock_orders/detail.html`: added a Print button, always visible regardless of status.
- [x] `templates/sales_orders/build_bom.html`: added an editable `job_numbers` (FM number) input inside the existing `<form>`, pre-filled from `so.job_numbers`.
- [x] `routes/sales_orders.py build_bom()`: reads `job_numbers` early, requires it (flash + redirect) when at least one line is marked Fan, persists it onto `so.job_numbers` when non-blank; stock-only builds are unaffected.
- [x] Fixed an existing test-fixture collision: `tests/test_stock_orders.py` setup_data was minting `StockOrder` numbers in the same `STOxxxx` format the app auto-generates, which collided with the new build_bom-driven STO creation in the shared session-scoped in-memory test DB — renamed to `STO-TEST-xxx` (mirrors the existing `SO-STO-xxx` so_number convention in the same fixture).
- [x] Added `test_print_renders`/`test_print_404_for_missing` (test_stock_orders.py) and `test_build_bom_requires_job_number_for_assembly`/`test_build_bom_saves_job_number_on_assembly`/`test_build_bom_stock_only_does_not_require_job_number` (test_bom_builder.py); updated the two existing fan-line build_bom tests to supply `job_numbers` now that it's required.
- [x] Full suite: 32 tests green.
- Known pre-existing issue flagged (not fixed, out of scope): `templates/sales_orders/detail.html` line ~95 crashes with `TypeError` if any `SOLineItem.excl_price` is `None` (only reachable via lines created outside the normal PDF-parse path, e.g. directly via tests/DB).

## Batch 11 — Per-Line Job Numbers + Sales Order Close (2026-07-06)
- [x] Picked up in-progress uncommitted work from a prior unlogged session implementing `docs/specs/sales-order-job-numbers.md` (per-line FM/job numbers) plus a `can_close_sales_order()` helper and manual "Close Order" feature (scope expansion beyond the spec).
- [x] `models.py`: `SOLineItem.job_number` column (migrated via `scripts/migrate_add_so_line_job_number.py`, confirmed already applied to `instance/sops.db`).
- [x] `routes/sales_orders.py build_bom()`: per-line job number input/validation per Fan line; SO-level `job_numbers` summary rebuilt from collected per-line values. Removed dead `job_numbers_input` variable left over from the old single-field version.
- [x] `routes/works_orders.py` (`mark_complete`, `confirm_pick`) and `routes/stock_orders.py` (`complete_order`): now call shared `can_close_sales_order()` and set SO status to `'Closed'` (was `'Complete'`) once all WOs/STOs for the SO are Complete/Cancelled.
- [x] `routes/sales_orders.py`: added `POST /sales-orders/<id>/close` route + "Close Order" button on `templates/sales_orders/detail.html`.
- [x] Gap found + fixed: `templates/works_orders/picking_list_print.html` was missing the Job Number(s) row (WO print and STO print already had it) — acceptance criterion "BOM/WO/PL pages and print documents show the combined job/SO reference" was not fully met.
- [x] Gap found + fixed: no test coverage existed for `close_order`/`can_close_sales_order` or for the new auto-close-to-`'Closed'` behavior in `mark_complete`/`confirm_pick`/`complete_order`. Added `tests/test_sales_order_close.py` (7 tests: manual close blocked/succeeds/idempotent, auto-close from both WO and STO completion paths, non-close while the other order type is still open).
- [x] Full suite: 39 tests green (was 32).
- Note: the `'Complete'` → `'Closed'` SO status rename and the manual Close Order route were not in the original job-numbers spec — flagged to Tebello as a scope expansion; no other code references `SalesOrder.status == 'Complete'` so this is safe, but `scripts/fix_so_status.py` (pre-existing, uncommitted-work-unrelated) still writes the old `'Complete'` value if ever re-run — out of scope, not touched.
- Next task: none queued — awaiting Tebello's review/commit confirmation.
