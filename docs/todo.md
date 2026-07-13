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
- Committed: `d59f99c`.

## Batch 12 — Sort Sales/WO/STO lists by Delivery Date (2026-07-06)
- [x] `routes/sales_orders.py list_orders()`: sort by `SalesOrder.delivery_date` ascending (soonest due first), nulls last via `sqlalchemy.nullslast()`.
- [x] `routes/works_orders.py list_orders()`: `WorksOrder` has no `delivery_date` of its own — outer-joined to `SalesOrder` and sorted by `SalesOrder.delivery_date` ascending, nulls last.
- [x] `routes/stock_orders.py list_orders()`: same pattern — outer-joined to `SalesOrder`, sorted by delivery date ascending, nulls last.
- [x] Added a "Delivery Date" column to `templates/works_orders/list.html` and `templates/stock_orders/list.html` (Sales Orders list already had one) so the new sort key is visible, not just implicit.
- [x] Verified against the live `instance/sops.db` data by running the dev server and diffing rendered rows — first pass showed a stale Werkzeug reloader child process still serving the old `created_at.desc()` order; killed both server processes, restarted clean, and confirmed all three list pages now render in ascending delivery-date order.
- [x] Full suite: 39 tests green (no test changes needed — no existing test asserted list ordering).
- Next task: none queued — awaiting Tebello's review/commit confirmation.

## Research — ERP/MRP Benchmark (2026-07-07)
- [x] Research pattern: benchmarked SOPS against world-class ERP/MRP standards (SAP B1, NetSuite, Odoo MRP) — see `docs/research/erp-mrp-benchmark-2026-07-07.md`.
- Gaps identified: no Purchase Order/supplier module, no reorder-point signals, shortfall calc is point-in-time (no demand netting against on-order/committed stock).
- Spec written: `docs/specs/purchase-order-module-plan.md` — revised after Tebello attached 2 real Sage PO PDFs, covering Enhancement 1 (PO upload/parse/receive) and Enhancement 2 (reorder points) in detail.

## Batch 13 — Purchase Order Module + Reorder Point Signals (2026-07-07)
- [x] `services/pdf_common.py`: extracted shared Sage-PDF table geometry parsing out of `services/pdf_parser.py` (no behavior change, verified against the 39-test baseline first).
- [x] `services/po_parser.py`: `parse_purchase_order_pdf()` + `split_item_code()`. Verified against both attached sample POs (PO4088 - LUFT, 5 lines; PO4106 - ATTENU-TEC, 1 line) — all item codes matched existing `Item.code` catalogue rows exactly.
- [x] `PurchaseOrder`/`POLine` models + `scripts/migrate_add_purchase_order_tables.py`. `POLine.item_id` nullable — unmatched lines never block a save.
- [x] `routes/purchase_orders.py` + `templates/purchase_orders/`: upload/review, list, detail (inline item-link fixup), print, receive (full/partial, calls existing `stock_service.receipt()`), cancel (blocked once received). Registered blueprint, added nav entry.
- [x] Enhancement 2: `Item.reorder_point`/`reorder_qty` columns + migration (self-heals via `ensure_schema_columns()`). Stock Report "Below Reorder Point" filter, Dashboard stat card, `create_from_shortfall()` Draft-PO generator.
- [x] Gap caught + fixed: reorder_point/reorder_qty had no UI — added Reorder Settings form on Item detail page (`items.update_reorder_settings()`).
- [x] End-to-end test added: real PDF upload -> scrape rendered `lines_json` -> save -> receive -> verified stock movement + `last_cost` against real PO4106 data.
- [x] Offline-first re-verified (no cdn./fonts.googleapis in new templates).
- [x] Full suite: 62 tests green (was 39). 8 atomic commits.
- Flagged to Tebello: existing codebase already fails `black --check` at baseline (pre-existing, not introduced by this batch) — did not run a project-wide reformat, since that would create unrelated diff noise. Separate decision for later if wanted.
- Next task: Enhancement 3 (demand-netted shortfall calc, `docs/research/erp-mrp-benchmark-2026-07-07.md`) once Tebello reviews 1 & 2.
- Blockers: None.
- Committed: `65f8443`, `15a265e`, `6f0dc53`, `b4bfdc4`, `c06a9f5`, `0b08b7c`, `fc63598`, `c0a5ceb`.

## Batch 14 — Open/Active Filter (Dashboard + SO/WO/STO/PO Lists) (2026-07-08)
- [x] Spec: `docs/specs/dashboard-open-filter.md` — active-status definitions confirmed with Tebello (SO: Draft+Open; WO: Open+In Progress; STO: Open; PO: Draft+Open+Partially Received).
- [x] New `services/order_filters.py` — single source of truth for the 4 active-status tuples (avoids duplicating status strings across route files).
- [x] `routes/{sales_orders,works_orders,stock_orders,purchase_orders}.py` `list_orders()`: added `?view=open|all` query param (default `all`, unchanged behavior — opt-in filter per Tebello's decision), filters by the matching active-status tuple.
- [x] 4 list templates: added an "All / Open only" toggle in the card header, driven by the URL param (no JS/localStorage, offline-first).
- [x] `routes/dashboard.py` + `templates/dashboard.html`: new "Open Sales Orders" table (Draft+Open SOs, top 10 by soonest delivery date) — directly answers the ask that the dashboard surface open Sales Orders.
- [x] Confirmed with Tebello: existing "Recent Works Orders Activity" table on the dashboard stays an unfiltered activity feed (not a queue) — no change.
- [x] Tests: new `tests/test_order_list_filters.py` (7 tests) — `view=open` excludes the correct terminal statuses per type, default `view=all` unchanged; dashboard shows open/draft SOs and hides Closed ones.
- [x] Full suite: 69 tests green (was 62). `ruff check` clean on all new/changed files (pre-existing baseline lint/black issues in untouched code, flagged in Batch 13, left alone — no unrelated diff noise).
- Ops note: mid-task, `.git/index` got corrupted and `.git/index.lock` got stuck — root cause was OneDrive's Desktop-backup feature silently syncing this repo's `.git` internals (lock/index files) even though the folder looks like a normal local Desktop path. Tebello cleared the stuck lock from Windows directly (`Remove-Item .git\index.lock`); index rebuilt clean via a plain `git status`/`git reset`, no data lost — working tree was never touched. Flagged as a standing risk: recommend excluding this repo from OneDrive Desktop backup (or relocating off Desktop) to prevent recurrence.
- Blockers: None (resolved).

## Batch 15 — CLAUDE.md v3.2 + Repo Folder Cleanup (2026-07-09)
- [x] Landed CLAUDE.md v3.1 → v3.2 (user-level `~/.claude/agents/` roster, project-level reserved for overrides only) — commit `804738a`.
- [x] Removed `AGENT_build_bom_works_pack.md` (superseded v1.0 spec) — confirmed its learnings are fully captured in `docs/specs/multi-fan-build-bom.md` and `docs/specs/sales-order-job-numbers.md` before deleting.
- [x] Repo folder cleanup — archived (not deleted) genuinely orphaned material into new `archive/` (see `archive/README.md`):
  - `sops/` package (`app.py`/`config.py`/`models.py`/`__init__.py`) — pre-`docs/decisions/0001-keep-flask-app-at-root.md` scaffold, unreferenced by the live app, plus its orphaned `sops/instance/sops.db` (53KB test-run artifact, not the real DB).
  - Six 2026-06-17 ad-hoc debug scripts (`check_db_state.py`, `check_so_lines.py`, `find_item.py`, `fix_bom_line.py`, `test_render.py`, `scripts/quick_update_items.py`) — siblings of scripts already cleaned in commit `f54d4e9` but missed at the time.
  - Eight tracked `logs/*.log`/`*.txt` run-output captures (2026-05 to 2026-07) — `logs/` is now gitignored (`logs/*` + `!logs/.gitkeep`) so run output stops landing in git going forward.
- [x] Deleted (confirmed pure junk, not archived): root `sops.db` (0-byte stub, already flagged stale in `docs/bugs/health-screen-2026-06-24.md`), root `startup_test.log` (0 bytes), root `FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf` (byte-identical duplicate of the `data/` copy).
- [x] Updated `README.md` project structure tree (removed refs to archived/deleted files, noted `logs/` is now gitignored, added `archive/` entry).
- [x] Full suite re-verified after cleanup: 69 tests green, no regressions from removing the dead `sops/` package.
- Next task: none queued — awaiting Tebello's review/commit confirmation. Enhancement 3 (demand-netted shortfall calc) remains the next roadmap item once picked up.
- Blockers: None.

## Batch 16 — FM Numbers on WO/STO + Default-Open Lists + SO Report Parity (2026-07-10)
- [x] Spec: `docs/specs/fm-numbers-default-open-so-report.md` — 2 scope decisions confirmed with Tebello via AskUserQuestion (track FM number properly on WO+STO with schema changes; Payment Status as a fixed dropdown, not free text).
- [x] `models.py`: `WorksOrder.job_number`, `StockOrderLine.job_number`, `SalesOrder.payment_status` (+ `PAYMENT_STATUS_OPTIONS` constant) columns; `StockOrder.job_numbers` and `SalesOrder.total_incl` computed `@property`s (no new columns for these — derived from existing line data, same pattern as `job_reference`).
- [x] `scripts/migrate_add_fm_number_and_payment_status.py` + matching `ensure_schema_columns()` entries in `app.py`.
- [x] `routes/sales_orders.py build_bom()`: each `WorksOrder` now gets `job_number` from its originating Fan line; `StockOrderLine.job_number` captured from the already-existing (previously Fan-only-enforced) per-line job number input — no template change needed, the input already renders for every line regardless of role.
- [x] `templates/works_orders/list.html`, `templates/stock_orders/list.html` (+ both detail templates): added a Job Number column/row alongside (not replacing) the internal WO/STO number.
- [x] Default `?view=open|all` flipped: bare `/sales-orders`, `/works-orders`, `/stock-orders`, `/purchase-orders` now default to Open (was `all`, Batch 14's original opt-in decision — explicit reversal per Tebello). `?view=all` still works as opt-in.
- [x] SO report parity: `templates/sales_orders/list.html` — added Sales Rep, Total, Payment Status columns, relabeled "Reference" → "Customer Ref."; `templates/sales_orders/detail.html` — added Total row + Payment Status row with an inline dropdown (`POST /sales-orders/<id>/payment-status`, new route in `routes/sales_orders.py`).
- [x] Tests: updated `tests/test_order_list_filters.py` (renamed `test_default_view_shows_all_statuses` → `test_default_view_hides_*`, added `test_all_view_shows_all_statuses` for all 4 modules); extended `tests/test_bom_builder.py` (2 new tests: per-fan-line `WorksOrder.job_number`, optional stock-line job number → `StockOrderLine.job_number` + `StockOrder.job_numbers` rollup); new `tests/test_so_report_fields.py` (`total_incl`, `payment_status` route incl. invalid-value rejection, `StockOrder.job_numbers` rollup with duplicates/blank).
- [x] Full suite: 86 tests green (was 69). Offline-first re-verified (`grep -rn "cdn\."/"fonts.googleapis"` on templates/static — empty). Manually verified via live dev server: SO/WO/STO list pages 200 + new columns present, SO detail payment-status dropdown renders all 5 options.
- Known gap, not fixed (documented in spec as accepted): pre-existing WOs/STOs created before this migration have no Job Number — no reliable backfill source (multi-fan SOs have no stored per-WO mapping in old data).
- Blockers: None.

## Ops — Pre-08:00 Test Data Purge (2026-07-10)
- [x] Tebello requested deleting all Sales Orders (+ linked Works/Stock Orders) created before 2026-07-10 08:00 to get a clean slate for the new Job Number field, treating the pre-cutoff records as reloadable test data.
- [x] Before deleting, surfaced that a non-destructive backfill was actually possible for every one of the 12 pre-cutoff SOs (each had ≤ 1 WO and `so.job_numbers` already populated — the "can't backfill" caveat from Batch 16 only applies to multi-fan SOs). Tebello confirmed via AskUserQuestion: delete anyway, records are being used as test data and can be reloaded.
- [x] Backed up `instance/sops.db` → `instance/sops.db.pre-cleanup-backup-20260710_150329` before deleting (not committed — DB files are gitignored).
- [x] Deleted 12 Sales Orders (SO4641, SO4653, SO4659, SO4652, SO4678, SO4683, SO4684, SO4693, SO4704, SO4676, SO4706, SO4708), 8 Works Orders (all were `Complete`), 7 Stock Orders (3 `Complete`, 4 `Cancelled`) via a one-off ORM script (explicit `session.delete()` per WO/STO then per SO — the model relationships don't cascade SO→WO/STO automatically, only WO→BOMLine and STO→StockOrderLine do). Left `StockMovement` audit-trail rows untouched (out of the requested scope; they're independent ledger rows, no FK to WO/STO).
- [x] Gap found + fixed (unrelated to the purge, surfaced by it): `archive/2026-06-debug-scripts/test_render.py` — an archived ad-hoc debug script matching pytest's `test_*.py` discovery pattern — ran top-level code against the *live* DB at import time (hardcoded `get_works_order_print_context(9)`), and started failing collection once WO id 9 was deleted. Added `pytest.ini` (`testpaths = tests`) so pytest only ever collects the real suite; this class of landmine (archived scripts accidentally shaped like tests) can't recur.
- [x] Full suite re-verified: 86 tests green. Live dev server spot-check: SO/WO/STO list pages and Dashboard all 200 with the reduced dataset (WO/STO lists correctly empty).
- 15 Sales Orders remain (all created 2026-07-10 after 08:00); 0 Works Orders, 0 Stock Orders remain — all prior WO/STO records belonged to the purged pre-cutoff SOs.
- Blockers: None.

## Batch 17 — Payment Status at intake, editable Delivery Date, Reopen SO/WO/STO, resizable columns (2026-07-13)
- [x] Spec written: `docs/specs/payment-status-delivery-date-reopen-columns.md`. Scope confirmed with Tebello via AskUserQuestion: fix the STO stock-deduction gap found during audit (Stock Orders currently never call `stock_service` at all — `WorksOrder(order_type='STOCK')`/`confirm_pick()` is dead code, `build_bom()` builds `StockOrder`/`StockOrderLine` directly); Reopen cascades upward (child → parent SO) but not downward; column resize via lightweight vanilla JS, not a Tabulator migration; column widths persist via `localStorage` (confirmed with Tebello).
- [x] Part A: `PAYMENT_STATUS_OPTIONS` gains `Partially Paid`; Payment Status field added to the upload/review form; `save_order()` reads it (defaults to Pending when omitted). Commit `ddd91b2`.
- [x] Part B: `POST /sales-orders/<id>/delivery-date` + inline edit form on SO detail; new `dmy` Jinja filter (`app.py`) applied to every delivery_date/so_date display site (list/detail/dashboard/bom templates — print templates already used DD/MM/YYYY). Commit `0a8070f`.
- [x] Part C0: `StockOrderLine.qty_issued` column + migration (`scripts/migrate_add_stock_order_line_qty_issued.py`) + self-heal entry; `stock_orders.complete_order()` now resolves each line's `item_code` against the catalogue and calls `stock_service.issue()` — this closes the gap where STO completion never deducted stock at all. Commits `b03185f`, `ac61985`.
- [x] Part C1: `stock_service.reverse_issue()` — adds stock back and logs a `REVERSAL` movement (kept distinct from `RECEIPT`). Commit `b03185f`.
- [x] Part C2–C4: `POST /works-orders/<id>/reopen`, `POST /stock-orders/<id>/reopen`, `POST /sales-orders/<id>/reopen`. WO/STO reopen reverses issued stock per line via `reverse_issue()` and resets `qty_issued`; either cascades the parent SO back to Open if it had been auto-closed. SO reopen (Closed → Open) does not cascade down to its WOs/STOs. Commit `c7ce7f9`.
- [x] `REVERSAL` surfaced in the Movement Report type filter + given its own badge color on Item detail (was falling through to generic grey). Commit `c9b48e0`.
- [x] Part D: `static/js/resizable_columns.js` (vanilla, no dependency) — drag handle per `<th>`, widths persisted per-table in `localStorage`. `col-date` CSS class (`white-space: nowrap`) applied to all date columns on the 4 list pages. Commit `c224459`.
- [x] Tests: `test_sales_order_upload.py` (+3), `test_delivery_date.py` (new, 5), `test_stock_service.py` (+1), `test_stock_orders.py` (+2), `test_reopen.py` (new, 10), `test_resizable_columns.py` (new, 4). Full suite: 111 tests green (was 86).
- [x] Verified live against the real `instance/sops.db` via dev server: SO/WO/STO/PO lists all 200, dates render DD/MM/YYYY with `col-date`/no-wrap applied, resizable-columns script served and wired, Delivery Date/Payment Status inline forms present on SO detail, Movement Report REVERSAL filter option present. Offline-first re-verified (`grep -rn "cdn\."/"fonts.googleapis"` on templates/static — empty).
- [x] Session-log backfilled for Batch 16 + the Ops test-data purge (both landed 2026-07-10 but were missed at the time) — commit `868f56f`.
- Next task: none queued — awaiting Tebello's review/commit confirmation. Enhancement 3 (demand-netted shortfall calc) recommendation prepared separately, not yet started.
- Blockers: None.

## Enhancement 3 — Demand-Netted Shortfall Calc (2026-07-13)
- [x] Recommendation prepared and scope confirmed with Tebello via AskUserQuestion: `qty_committed` nets against all open WOs/STOs system-wide (not just the current SO); the netted `available_qty` replaces raw `qty_on_hand` in both BOM Builder and the Stock Report (not BOM-Builder-only).
- [x] Spec written: `docs/specs/demand-netted-shortfall.md`. No schema change — logic + display only, depends on Enhancement 1 (shipped Batch 13).

## Batch 18 — Enhancement 3 Implementation + 2 In-Flight Scope Corrections (2026-07-14)
- [x] `services/demand.py` (new module): `get_qty_on_order_bulk()`, `get_qty_committed_bulk()`, `get_next_po_due_bulk()` + single-item wrappers — batched `{item_id: qty}` aggregate queries so catalogue-page callers avoid N+1. Commit `3e4c0ed`.
- [x] BOM Builder wiring: `item_to_bom_json()` gains `qty_on_order`/`qty_committed`/`available_qty`/`next_po_due`; `static/js/bom_builder.js` shortfall formula switched to `available_qty`, "(on order, due `<date>`)" hint added. Commit `03109bf`.
  - Scope finding: `static/js/bom_builder.js` is only reachable from the WO/STO **edit** pages (`works_orders/edit.html`, `stock_orders` edit) — not from `build_bom.html`, the actual "Build Works Pack" page most order creation goes through, which has **no shortfall/qty display of any kind** today. `templates/sales_orders/bom_builder.html` is orphaned (no route renders it). Left as a known gap — see below.
- [x] Stock Report wiring: `/reports/stock/data` and `/export-csv` — "Below Reorder Point" filter and display switched from raw `qty_on_hand` to netted `available_qty`; `qty_on_hand` kept visible as ground truth; `available_qty` column added to the Tabulator table. Commit `638b70d`.
- [x] Scope correction #1 (Tebello confirmed via AskUserQuestion): discovered mid-build that `services/doc_generator.py::get_works_order_print_context()` had a 3rd, separate un-netted shortfall calc (feeds the WO detail screen `templates/works_orders/detail.html` and the print document) that the original spec never mentioned. Netted it the same way, added "(on order N)" hint to `detail.html` (left `works_order_print.html` untouched — it doesn't render `qty_on_hand`/shortfall at all, only defines an unused CSS class). Commit `ea3e032`.
- [x] Bug found + fixed (own discovery, not spec'd): `get_qty_committed_bulk()` summed demand from *all* open WOs/STOs system-wide with no way to exclude the current order's own lines — caused a false shortfall equal to an order's own full requirement whenever nothing else competed for that item (e.g. WO needs 10, has exactly 10 on hand, zero other demand → was showing shortfall of 10, should be 0). Added `exclude_wo_id`/`exclude_sto_id` params, wired into the WO/STO edit pages and WO print context; Stock Report intentionally excludes nothing (no "current order" frame there). Commit `46d0724`.
- [x] Reviewer pass (Opus, per standing policy for changes driving purchasing/stock decisions): **Approved with nits**. Confirmed the self-counting fix correct/complete, N+1 avoided at every caller, STO `item_code` join degrades safely, spec test-plan fully covered. Flagged: Dashboard reorder stat card still un-netted (diverges from Stock Report), possible negative `qty_committed` from an over-issued line, missing `qty_on_hand or 0.0` guards at 4 sites, `get_available_qty()` missing exclusion-param parity, and `get_works_order_print_context()` duplication (>50 lines, deferred — not blocking).
- [x] Scope correction #2 (Tebello confirmed via AskUserQuestion): netted the Dashboard "Below Reorder Point" stat card too (`routes/dashboard.py`) so it no longer disagrees with the Stock Report on the same purchasing signal; `low_stock_count` left as a deliberate raw-physical-stock measure. Plus: floored negative per-line committed demand at 0 (Python-side sum, avoided a SQLite `func.max` aggregate-vs-scalar ambiguity), added the 4 missing `qty_on_hand or 0.0` guards, added exclusion-param parity to `get_available_qty()`. Commit `f4fce5d`.
- [x] Full suite: 111 → 147 tests green across the 6 commits (`3e4c0ed` +17, `03109bf` +3, `638b70d` +4, `ea3e032` +4, `46d0724` +5, `f4fce5d` +3).
- Known gap, confirmed out of scope for now (Tebello's call during the session): `build_bom.html`, the primary "Build Works Pack" page, still shows **no** stock-availability/shortfall information at all when first creating a Works Pack from a Sales Order — the netting fix only reaches the *edit* path for an already-created WO/STO. Adding shortfall display there would be a new feature (new UI + data wiring), not a netting fix, and was declined for this batch. Next candidate item if picked up later.
- Blockers: None.
