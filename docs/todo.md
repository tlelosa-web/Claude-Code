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

## Batch 19 — CSV Import Quantity-Overwrite Removal (2026-07-14)
- [x] Session opened with `/continue`. Committed Batch 18's stray untracked reviewer-agent memory (`ced588c`), then reviewed `data/ItemListingReport.csv` upload's effect on Stock Report at Tebello's request.
- [x] Review surfaced a risk: `/items/import`'s default (unchecked) "Preserve Stock Quantities" checkbox overwrote `Item.qty_on_hand` for existing items straight from the CSV, with no diff/preview — since SOPS now owns the full stock lifecycle via `stock_service` (WO/STO issue, PO receipt, adjust, reversals, all audited), this could silently revert live stock movements back to a stale Sage export on a missed click.
- [x] Tebello confirmed (after review): remove the toggle entirely, make quantity-preservation the only import behavior. Spec: `docs/specs/csv-import-quantity-safety.md`.
- [x] `services/item_importer.py`: deleted the overwriting `import_items_from_csv()`; renamed `import_items_from_csv_skip_quantities()` → `import_items_from_csv()` (new-item quantity seeding unchanged, existing-item `qty_on_hand` never touched again).
- [x] `routes/items.py`: dropped `preserve_quantities`/`import_func` branching, single call site, collapsed flash messages.
- [x] `templates/items/import.html`: removed both checkboxes + hidden input + sync script; replaced with a static note that quantities are managed inside SOPS, not by import.
- [x] `tests/test_item_importer.py`: rewrote the existing-item test to assert preservation (was asserting overwrite — would now be testing a false claim if left as-is), added an explicit regression test for a CSV row with a different quantity than the DB's current value.
- [x] Full suite: 148 tests green (was 147). `git grep` confirmed `preserve_quantities` and `import_items_from_csv_skip_quantities` both gone from all live code — one stale reference remains in `archive/2026-06-debug-scripts/quick_update_items.py` (already-documented dead script per `archive/README.md`, out of scope, left untouched).
- [x] Committed: `2965367`.
- Next task: none queued — awaiting Tebello's review/commit confirmation. `build_bom.html` shortfall-display gap (see Batch 18 note above) remains the next roadmap candidate; a scoped plan for it was presented and is ready to spec/build on request.
- Blockers: None.

## Batch 20 — Build Works Pack Shortfall Display (2026-07-14)
- [x] Closed the last remaining gap from Batch 18: `build_bom()` / `templates/sales_orders/build_bom.html` — the primary "Build Works Pack" page — now carries the same demand-netted availability data the WO/STO edit page got in Batch 18 (commit `03109bf`).
- [x] Spec: `docs/specs/build-bom-shortfall-display.md`, written before dispatch (5 files >2 → plan-first rule).
- [x] `routes/sales_orders.py` `build_bom()`: both the GET render and the POST error-path re-render now bulk-fetch `get_qty_on_order_bulk()`/`get_qty_committed_bulk()`/`get_next_po_due_bulk()` (no `exclude_wo_id`/`exclude_sto_id` — no WO/STO exists yet at this point) and map through the existing `item_to_bom_json()`, replacing two bare `{id, code, description}` dicts.
- [x] `templates/sales_orders/build_bom.html`: search results show `(available: N)` and an `(on order, due <date>)` hint; selected-item panel surfaces `available_qty`; `addComponent()` computes shortfall against `available_qty` and applies the same `row-amber` class / `(short N)` styling `bom_builder.js` already uses (verified `.row-amber` is a real defined class in `static/css/main.css:383`, not invented).
- [x] `tests/test_bom_builder.py`: new test asserts the GET-served `catalogue_json` carries all 5 demand-netting fields. POST error-path payload test explicitly skipped (would need artificial-failure fixture machinery beyond scope) — noted rather than silently dropped.
- [x] Full suite: 149 tests green (was 148).
- [x] Orchestrator-side live verification (dev server against real `instance/sops.db`, SO25's build-bom page): first attempt hit a **stale dev-server process left running from before this session** (started 00:38, before the 01:00 commit) serving the old 3-field payload — same class of issue documented in Batch 12. Killed it, confirmed a fresh process serves the new 5-field payload (`available_qty`, `qty_on_order`, `qty_committed`, `next_po_due`, `qty_on_hand`) and all new JS hint/shortfall code renders. Stopped the server afterward.
- [x] Committed: `782514a` (implementation), `ca30d89` (spec, committed after since it was outside the executor's file scope).
- Next task: none queued — awaiting Tebello's review/commit confirmation. This closes the last known gap from the Enhancement 3 demand-netting effort; no further roadmap item currently queued.
- Blockers: None.
- Ops note: recurring risk — a stale Werkzeug dev-server process from an earlier session can keep serving old code on port 5000 indefinitely (2nd occurrence, see Batch 12). Worth checking `Get-NetTCPConnection -LocalPort 5000` before trusting a "live" verification if a dev server wasn't freshly started this session.

## Ops — Repo Health Check + Stale Spec Status Cleanup (2026-07-14)
- [x] Tebello requested a general repo health check after noticing `docs/specs/dashboard-open-filter.md` was stuck showing "Pending approval" despite being shipped.
- [x] Checked for stale dev-server process on port 5000 — none found (prior session's had already exited cleanly).
- [x] Found and fixed real git corruption: `.git/refs/heads/` had two leftover files (`master.lock.bak.1`, `master.lock.bak.30564`) from the OneDrive lock-corruption incident documented in Batch 14 — these were breaking `git branch -a`/`git log --all` (`fatal: bad object`). Verified `master.lock.bak.1` pointed to an already-merged ancestor commit (`520f955`, no data loss) before deleting both; `git fsck` clean afterward (only harmless dangling objects).
- [x] Verified: 149/149 tests green, Flask app factory imports cleanly, offline-first constraint intact (no `cdn.`/`fonts.googleapis` in served templates/static).
- [x] Found the "Pending approval" status wasn't isolated — 5 specs had stale pre-build status lines despite being shipped weeks earlier. Updated all 5 to `Shipped` with batch/commit refs: `dashboard-open-filter.md`, `purchase-order-module-plan.md`, `demand-netted-shortfall.md`, `csv-import-quantity-safety.md`, `build-bom-shortfall-display.md`. Committed `3aae9fb`.
- Blockers: None.

## Batch 21 — Fix broken "All" toggle + add "Closed" view (SO/WO/STO) (2026-07-14)
- [x] Tebello reported SO4731 (a Closed SO) wasn't visible even after clicking "All" on the Sales Orders list — investigated live via DB lookup (`SalesOrder.query.filter_by(so_number='SO4731')`), confirmed it exists (id 38, status Closed).
- [x] Root cause found: `routes/{sales_orders,works_orders,stock_orders,purchase_orders}.py` `list_orders()` default to `view='open'` (since Batch 16's default flip), but the "All" link in all 4 list templates linked to the bare list URL with no `view` param — silently falling through to the same `'open'` default. The "All" button had been non-functional since Batch 16.
- [x] Tebello's fix request: rename "Open only" → "Open", add a "Closed" button (negates the existing ACTIVE-status tuple, no new status list), apply to SO/WO/STO only. Purchase Orders confirmed to have the identical link bug — fixed the link only there (no Closed button, out of requested scope).
- [x] Spec written first (7 files >2 → plan-first rule): `docs/specs/open-closed-all-toggle-fix.md`.
- [x] Dispatched a single `executor` agent — commit `5c6e8ae`: `routes/sales_orders.py`/`works_orders.py`/`stock_orders.py` gain a `elif view == 'closed'` branch negating `SO_ACTIVE`/`WO_ACTIVE`/`STO_ACTIVE`; SO/WO/STO list templates get a 3-button All/Open/Closed toggle with every link passing an explicit `view=` param; `purchase_orders/list.html` gets the same explicit `view='all'` link fix only. 3 new tests in `tests/test_order_list_filters.py` covering the `closed` view per module.
- [x] Orchestrator-side verification: read the full diff line-by-line (not just the executor's summary), re-ran the full suite independently (152 passed, was 149). Live-verified against the real `instance/sops.db` via the already-running dev server (Flask's reloader picked up the change automatically) — confirmed SO4731 now appears under Closed/All and correctly stays hidden under Open.
- [x] Full suite: 152 tests green (was 149).
- Next task: none queued — awaiting Tebello's review/commit confirmation for the spec file.
- Blockers: None.
- Commits: `5c6e8ae` (implementation). Spec (`open-closed-all-toggle-fix.md`) to be committed separately per convention.

## Batch 22 — Bug Sweep (2026-07-14)
- [x] Tebello asked to "check for other bugs" after Batch 21. Dispatched a `reviewer` agent (permanent Opus per standing policy) for a broad correctness sweep of routes/services/models.py; independently re-verified every finding by reading the live code myself before accepting any of them — one finding needed correcting in the process (see below).
- [x] 5 confirmed findings, all approved by Tebello for immediate fix:
  1. **BLOCKER-severity as reported, corrected on verification**: `routes/sales_orders.py` `reupload_order()` POST branch omitted `payment_status_options` (its sibling `upload_order()` always passes it) — the shared template unconditionally loops over it once `parsed` is set. Initially reported as a 500 crash; empirically tested Jinja's default `Undefined.__iter__` (`python -c` repro) and found it does NOT raise — the real symptom is a silently empty Payment Status dropdown on the reupload review page, not a hard crash. Corrected severity before reporting to Tebello.
  2. `routes/purchase_orders.py` `create_from_shortfall()` filtered on raw `qty_on_hand` while the Stock Report button that launches it flags items on demand-netted `available_qty` — could add unnecessary PO lines or skip genuinely short items.
  3. `routes/works_orders.py` `confirm_pick()` was missing the `Cancelled` status guard its sibling `mark_complete()` already has — not reachable via current UI, but a direct POST could un-cancel a WO and re-issue stock.
  4. Unguarded `qty_on_hand * avg_cost` / cost-field formatting in `routes/reports.py` (`stock_data`, `stock_export_csv`) and `routes/items.py` (catalogue AJAX JSON) — a single legacy item row with a NULL cost/qty field could 500 the Stock Report or Items catalogue.
  5. Unguarded `BOMLine.qty_required` arithmetic in `services/doc_generator.py` and `routes/works_orders.py` — latent, no current creation path leaves it NULL, defensive hardening only.
- [x] Spec written first (7 files touched >2 → plan-first rule): `docs/specs/bug-sweep-2026-07-14.md`.
- [x] Dispatched a single `executor` agent for 4 atomic commits (Fix 4+5 share a commit — same guard-pattern, same review pass):
  - `22f6daa` — Fix 1: added missing `payment_status_options` kwarg + regression test.
  - `1ed8d6e` — Fix 2: `create_from_shortfall()` now bulk-fetches `get_qty_on_order_bulk()`/`get_qty_committed_bulk()` once for the candidate set and filters on netted `available_qty`, matching `reports.py:55` exactly (no N+1). 2 new tests (covered-by-on-order excluded; pushed-below-by-committed included).
  - `cba8171` — Fix 3: added the same `Cancelled` guard to `confirm_pick()`. 1 new regression test.
  - `1bd56c4` — Fix 4+5: `or 0.0`/`or 0` guards added at all cited sites; executor found 2 additional unguarded `round(item.avg_cost, 2)` call sites in `reports.py` the spec's suggested diff had missed and fixed those too (needed to actually satisfy the 200-response acceptance criterion). 3 new tests using Core-level `Item.__table__.insert()` to force a real NULL past the ORM's `default=0.0`, which otherwise silently overrides an explicit `avg_cost=None` in the constructor.
- [x] Orchestrator-side verification: read all 4 diffs in full, independently re-ran the full suite (159 passed, was 152) rather than trusting the executor's reported count.
- [x] Full suite: 159 tests green (was 152).
- Next task: none queued — awaiting Tebello's review/commit confirmation for the spec file.
- Blockers: None.
- Commits: `22f6daa`, `1ed8d6e`, `cba8171`, `1bd56c4`. Spec (`bug-sweep-2026-07-14.md`) to be committed separately per convention.

## Batch 23 — Stock Order Picking Step (2026-07-14)
- [x] Spec written first (6 files touched >2 → plan-first rule), confirmed with Tebello via 3 rounds of AskUserQuestion: `docs/specs/stock-order-picking-step.md`. New `StockOrder.status` value `Picking` sits between `Open` and `Complete`; picking deducts stock immediately per line (not deferred); Complete is blocked until every line is fully picked; Cancel reverses any partially-picked stock; scoped to Stock Orders only (not Works Orders).
- [x] Dispatched a single `executor` agent for the full 7-step sequence, working directly on `master` in the existing OneDrive checkout (no git worktree, per this repo's documented corruption history with concurrent/unusual git ops):
  - `6c70850` — `STO_ACTIVE` gains `'Picking'`.
  - `c7491d8` — new `POST /stock-orders/<id>/pick` route: per-line pick qty, clamped to remaining outstanding, calls `stock_service.issue()` immediately, flips `Open → Picking` on first pick.
  - `4ccfb13` — `complete_order()` gate: blocked with a flash error until every line's `qty_issued >= qty`.
  - `1350b31` — `cancel_order()`: reverses any partially-issued lines via `stock_service.reverse_issue()` before setting `Cancelled`.
  - `62c4ab7` — `templates/stock_orders/detail.html`: per-line Pick Qty inputs + Picked column, gated Mark Complete action, updated Cancel confirm text.
  - `9b6b079` — `.badge-picking` CSS.
  - `8ca3603` — `view=open`/`view=closed` list-filter tests for the new status.
  - `10bad4b` — updated `StockOrder.status` inline model comment.
- [x] Orchestrator-side verification: independently re-ran the full suite (168 passed, was 159), read every diff against the spec line-by-line (route logic, template conditionals, CSS) — all matched exactly.
- [x] Real finding surfaced by the executor, confirmed on review: a `StockOrderLine` whose `item_code` never resolves to a catalogue `Item` can now never satisfy the Complete gate (`qty_issued` can never reach `qty` for that line via `/pick`, since unmatched lines are skipped there too) — so an STO with even one bad/unrecognized item code can become permanently stuck at `Picking`, unable to Complete or auto-close its parent SO. Previously, `complete_order()` tolerated unmatched lines (skip + warn, still completed). **Flagged to Tebello, not yet fixed — pending decision** on whether unmatched lines should count as "resolved" for the Complete gate, or whether this stricter behavior is actually desired now that picking is a real checkpoint.
- [x] Full suite: 168 tests green (was 159). Offline-first re-verified. `ruff` clean on all touched files (pre-existing unrelated findings untouched).
- Next task: Batch 24 (Payment Status restructure, same session) — see below. STO picking's flagged unmatched-item edge case remains open.
- Blockers: None (one open decision flagged above, not blocking).
- Commits: `6c70850`, `c7491d8`, `4ccfb13`, `1350b31`, `62c4ab7`, `9b6b079`, `8ca3603`, `10bad4b`. Spec (`stock-order-picking-step.md`) to be committed separately per convention.

## Batch 24 — Payment Status: Cash Sale/Account restructure + Amount Paid (2026-07-14)
- [x] Spec written first (5 files touched >2 → plan-first rule), confirmed with Tebello via 3 rounds of AskUserQuestion: `docs/specs/payment-status-cash-account-amount-paid.md`. New 7-value `PAYMENT_STATUS_OPTIONS` (`Cash Sale - Unpaid/Paid/Partial`, `Account - Pending/Up to Date/On Hold/Overdue`, exact list dictated by Tebello); new `SalesOrder.amount_paid` column + computed `balance_due` property, scoped to `Cash Sale - Partial` only; existing-data migration via a documented best-guess mapping table, ambiguous rows flagged for manual review, not auto-trusted.
- [x] Dispatched a single `executor` agent for the full 6-step sequence, working directly on `master` (same session as Batch 23, sequential not parallel — non-overlapping files but this repo's OneDrive git-lock history made sequential the safer call):
  - `24c583b` — `models.py`: new option list, default → `'Account - Pending'`, `amount_paid` column, `balance_due` property.
  - `0e1b0c7` — `scripts/migrate_add_payment_status_amount_paid.py` (schema) + `ensure_schema_columns()` self-heal entry.
  - `76a5021` — `scripts/migrate_payment_status_values.py` (one-off data migration, written + unit-tested but **deliberately not run** against `instance/sops.db` — that's a live-data operation held for Tebello's deliberate go-ahead).
  - `b5a0d03` — `update_payment_status()` reads/validates `amount_paid` for `Cash Sale - Partial`.
  - `80bd14d` — `templates/sales_orders/detail.html`: Balance Due row + Amount Paid input + Update button.
  - `515f840` — 10 new tests (`tests/test_so_report_fields.py`).
- [x] Executor found and fixed two hardcoded `'Pending'` literals the spec didn't call out (`save_order()`'s fallback default, `upload.html`'s default-selected option) — both would have silently pointed at a now-invalid legacy value. Corrected to `'Account - Pending'`. Flagged for review, judged correct on inspection — not a scope change, just closing a gap the spec's "no change" note didn't anticipate.
- [x] Orchestrator-side verification: independently re-ran the full suite (178 passed, was 168), read every diff against the spec (models, route, both templates, both migration scripts) — all matched. Confirmed `instance/sops.db` untouched (still 4 old-style values, no `amount_paid` column) — data migration intentionally not yet run.
- [x] Full suite: 178 tests green (was 168). Offline-first re-verified. `ruff` clean on all new files; pre-existing unrelated findings on touched-but-not-rewritten files left alone.
- Next task: Tebello to run `python scripts/migrate_add_payment_status_amount_paid.py` then `python scripts/migrate_payment_status_values.py` against the real `instance/sops.db` when ready, and review the printed list of "GUESS" SO mappings (old `Pending`/`Paid`/`Unpaid` → new value) for correctness.
- Blockers: None. Two specs (`stock-order-picking-step.md`, `payment-status-cash-account-amount-paid.md`) to be committed separately per convention.
- Commits: `24c583b`, `0e1b0c7`, `76a5021`, `b5a0d03`, `80bd14d`, `515f840`.

## Fix — STO unmatched-item-code Complete-gate regression (2026-07-14)
- [x] Resolved the open decision flagged at the end of Batch 23: an `StockOrderLine` whose `item_code` never resolves to a catalogue `Item` could never reach `qty_issued >= qty` via `/pick` (skipped there with a warning), which meant the Batch 23 picking-step full-pick gate permanently blocked `/complete` for that order — a regression from the pre-picking-step behavior, which tolerated unmatched lines.
- [x] `routes/stock_orders.py`: added shared `can_complete_stock_order()`/`_line_needs_pick()` helpers — a line only "needs pick" if it has outstanding qty AND its `item_code` resolves to a real catalogue `Item`. Used by both `complete_order()` (the gate) and `view_order()` (passed to the template as `can_complete`), so the server-side gate and the detail page's Mark Complete button state can never drift out of sync.
- [x] `templates/stock_orders/detail.html`: removed the template's own namespace-based `all_picked` loop (had no unmatched-line tolerance) in favor of the server-computed `can_complete`.
- [x] `tests/test_stock_orders.py`: renamed/reworked `test_complete_blocked_when_a_line_item_code_has_no_catalogue_match` → `test_complete_tolerates_a_line_item_code_with_no_catalogue_match` (asserts Complete now succeeds); added `test_complete_succeeds_once_matched_line_fully_picked_despite_unmatched_line` regression test; updated the two still-blocked tests to seed catalogue matches for both lines so they continue to test genuine outstanding-pick blocking, not the unmatched-line case.
- [x] Full suite: 179 tests green (was 178).
- Blockers: None.
- Committed: `2fe75f2`.

## Ops — Payment Status Data Migration Run (2026-07-14)
- [x] Ran both payment-status migration scripts against the real `instance/sops.db` per Tebello's go-ahead (the two scripts named in Batch 24's "Next task" above). Backed up the DB first: `instance/sops.db.pre-payment-status-migration-backup-20260714_121209` (and a second identical-content safety copy `...-20260714_124613` from re-confirming state this session).
- [x] `migrate_add_payment_status_amount_paid.py`: `amount_paid` column already present (this had evidently already been run earlier in this session before a context summarization — idempotent, no-op confirmed).
- [x] `migrate_payment_status_values.py`: all 23 Sales Orders already on a new-list `PAYMENT_STATUS_OPTIONS` value (also already run) — 0 rows changed on this re-run, 0 guessed mappings printed (nothing left to guess once already migrated).
- [x] Since the original run's printed GUESS list wasn't captured anywhere durable (terminal output, not logged) before context was summarized, reconstructed the review list by querying which SOs currently sit on a value the mapping table could have guessed at (old `Pending`→`Account - Pending`, `Paid`→`Cash Sale - Paid`, `Unpaid`→`Cash Sale - Unpaid`): **22 of 23 SOs** — only SO4725 (`Account - Up to Date`) came from a direct, non-guessed mapping (old `On Hold`/`Account - Up to Date`/`Partially Paid` values). Full list: SO4517, SO4556, SO4624, SO4661, SO4685, SO4698, SO4699, SO4702, SO4710, SO4714, SO4717, SO4718, SO4719, SO4722, SO4724, SO4726, SO4727, SO4728, SO4729, SO4730, SO4731, SO4732.
- Next task: **Tebello to manually review and correct, per SO on the SO detail page, any of the 22 listed above whose guessed Payment Status is wrong** (this is real production data — the migration script itself can't know which `Pending`/`Paid`/`Unpaid` orders were actually cash sales vs. accounts). Not yet reviewed as of this entry.
- Blockers: None (review is not code-blocking, but is a live-data-correctness item for Tebello).

## Ops — Stale Dev Server Fix (STO0004 stuck at Picking) (2026-07-14)
- [x] Tebello reported STO0004 stuck at Picking with no way to Complete. Root cause: not a code bug — the Complete-gate fix from commit `2fe75f2` (the "STO unmatched-item-code Complete-gate regression" fix, landed 12:11:45) had already resolved this exact case, but the Flask dev server process on port 5000 had been running since 11:53:00, before the fix landed, so it was still serving pre-fix code. 3rd occurrence of this recurring class of issue (see Batch 12, Batch 20).
- [x] Verified directly against the DB: `can_complete_stock_order()` for STO0004 correctly returns `True` (fully picked, item code resolves). Killed the stale process, restarted the dev server, confirmed 200 + fix live.
- Blockers: None.

## Batch 25 — Edit Item + Adjust Stock/Levels Popups, Max Level, Auto Reorder Qty (2026-07-14)
- [x] Spec written first (7 files touched >2 — plan-first rule), confirmed with Tebello via 3 rounds of AskUserQuestion: `docs/specs/item-edit-and-levels-popup.md`. Edit Item = identity/pricing only (not Qty on Hand, which stays on the audited `adjust_stock` path); Reorder Qty = auto-calculated (`Max Level - Reorder Point`), stored, override allowed; two separate modals (Edit Item / Adjust Stock & Levels), not one combined form.
- [x] Dispatched a single `executor` agent, commit `2eed031`:
  - `models.py`: new `Item.max_level` column.
  - `scripts/migrate_add_item_max_level.py` + `app.py::ensure_schema_columns()` self-heal entry.
  - `routes/items.py`: new `POST /items/<id>/edit` (`update_item`) — code/description/category/active/4 cost-price fields, duplicate-code + non-numeric validation, `qty_on_hand` untouched; `update_reorder_settings` extended to save `max_level` alongside the existing fields (no server-side recompute — auto-calc is client-side only).
  - `templates/items/detail.html`: replaced the two always-visible cards with two Alpine.js modals (Alpine was already vendored, unused elsewhere until now); Reorder Qty auto-fills client-side to `max(0, max_level - reorder_point)` unless the user has directly edited it within that modal session (dirty-flag tracked, reset on reopen).
  - Tests: new `tests/test_items.py` (5 tests — success update, checkbox handling, duplicate code, invalid numeric, blank code); extended `tests/test_reorder.py` for `max_level` persistence.
- [x] Orchestrator-side verification: read the full diff line-by-line, independently re-ran the suite (184 passed, was 179). Live-verified in the browser against the real `instance/sops.db` (dev server restarted fresh so the new code was actually being served — same stale-server class of risk as above, checked proactively this time): Edit Item modal opens/saves; Adjust Stock & Levels modal opens, Reorder Qty correctly auto-calculates on Max Level/Reorder Point input, and correctly stops auto-filling once manually overridden; explicit Save persists exactly the entered values.
- [x] Found and corrected a live-data side effect from my own manual browser testing: an earlier, less controlled round of clicking left `Item` id 1326 (CE 250) with a stray `max_level` value in the real DB that didn't match anything deliberately entered. A follow-up controlled test (type into Max Level only, check DB before any Save click, then click Save and check again) proved the shipped code has no auto-save bug — the anomaly was an artifact of the test tooling, not the app. Reverted CE 250 back to its pre-test values (`reorder_point=10.0`, `reorder_qty=10.0`, `max_level=0.0`) regardless, since it's live production data.
- [x] Full suite: 184 tests green (was 179).
- Next task: none queued — awaiting Tebello's review/commit confirmation. `docs/specs/item-edit-and-levels-popup.md` was committed together with the implementation (single commit, per this batch's scope).
- Blockers: None.
- Committed: `2eed031`.

## Batch 26 — Build Works Pack dropdown fix + Production Receipt on WO Complete (2026-07-15)
- [x] Tebello reported two issues from live screenshots: (1) the component search dropdown on `build_bom.html` visually overlapping/garbling the BOM Components table underneath it, (2) asked whether an assembly item's `qty_on_hand` becomes +1 when its Works Order closes.
- [x] Fix 1 (root cause traced, not guessed): `templates/sales_orders/build_bom.html`'s `#search-results` dropdown used `background: var(--bg-card)` — a CSS variable that doesn't exist anywhere in `static/css/main.css`, making the dropdown fully transparent and letting the table underneath bleed through. Changed to `background: #fff` (matches `.card` everywhere else) + `box-shadow: var(--shadow-lg)`. Verified live via computed styles against the real dev server. Same undefined-var pattern (`--bg-card`/`--text-muted`/`--brand-accent`) also exists as `color:` (not `background:`) in 16 other templates — cosmetic only there (degrades to inherited text color, not transparency), flagged but not touched. Committed `8a19ad3`.
- [x] Finding 2: confirmed via code read (`routes/works_orders.py mark_complete()`) — completing a WO only ever deducts COMPONENT stock; `ASSEMBLY_ITEM` lines are explicitly skipped everywhere (`mark_complete`, `reopen_order`, `demand.py`). SOPS has no finished-goods production-receipt step at all. The `-1.0` Tebello saw on MFP3150752 traced to a 2026-05-28 CSV `OPENING` import row, not a SOPS bug.
- [x] Tebello confirmed via 2 rounds of AskUserQuestion: build a real production-receipt step, scoped to a new opt-in `Item.is_stocked_finished_good` flag (not every assembly line — many are one-off made-to-order configs that would otherwise accumulate phantom stock balances). Spec written first (8 files touched — plan-first rule): `docs/specs/production-receipt-on-wo-complete.md`.
- [x] Dispatched a single `executor` agent, working directly on `master` (no worktree, per this repo's documented OneDrive git-corruption history) — 6 commits (`ce1086f`..`84494b2`):
  - `models.py`: new `Item.is_stocked_finished_good` boolean (default `False`).
  - `scripts/migrate_add_item_is_stocked_finished_good.py` + `app.py::ensure_schema_columns()` self-heal entry — **not run** against `instance/sops.db` (deferred to Tebello's go-ahead, same convention as Batch 24).
  - `services/stock_service.py`: new `produce()` (new `PRODUCTION` movement type, distinct from `RECEIPT` so "built in-house" is never confused with "bought from a supplier") and `reverse_production()` (reuses the existing `REVERSAL` type, negative direction).
  - `routes/works_orders.py`: `mark_complete()` calls `produce()` for flagged assembly lines and records `qty_issued` on that line (reusing the existing column to mean "qty produced," mirroring how component lines already use it); `reopen_order()` calls `reverse_production()` to undo it.
  - `routes/items.py` + `templates/items/detail.html`: Edit Item modal gained a "Stocked Finished Good" checkbox; Movement Report filter + Item detail badge recognize `PRODUCTION`.
  - Tests: `tests/test_stock_service.py` (+2), new `tests/test_production_receipt.py` (+3), `tests/test_items.py` (+1). Suite: 184 → 190.
- [x] Orchestrator-side review caught a real bug in my own spec (not the executor's fault — it built exactly what was specified): `reopen_order()`'s new branch re-checked `bom_line.item.is_stocked_finished_good` *at reopen time* before reversing. Since that flag is mutable catalogue metadata (toggleable via the Edit Item modal), an item unflagged between Complete and Reopen would permanently leak its produced stock — `qty_on_hand` never reverts, `qty_issued` stuck non-zero forever. Fix: key the reopen branch off `qty_issued > 0` alone (sufficient on its own, since that column is only ever set via `produce()` in the first place) — matches how the component-line branch already works. Added a regression test that reproduces the exact scenario via the real Edit Item route (not a raw ORM write, after an earlier version of the test gave a false pass due to a session-fixture quirk — verified the rewritten test fails against the pre-fix code and passes post-fix before trusting it). Commit `2d36254`.
- [x] Full suite: 191 tests green (was 184 at the start of this batch). Offline-first re-verified on both touched templates.
- Next task: none queued — awaiting Tebello's review/commit confirmation. Batch 24 payment-status data migration review (22 SOs with guessed values, flagged in the "Ops — Payment Status Data Migration Run" entry above) remains the only outstanding live-data item.
- Blockers: None.
- Commits: `8a19ad3`, `ce1086f`, `c0369eb`, `d4b2cfb`, `65d14f6`, `eb62cc4`, `84494b2`, `2d36254`.

## Ops — is_stocked_finished_good Migration Check (2026-07-15)
- [x] Resolved the Batch 26 open item on whether `scripts/migrate_add_item_is_stocked_finished_good.py` still needed to be run standalone. Confirmed directly against `instance/sops.db`: the `is_stocked_finished_good` column already exists (self-healed via `ensure_schema_columns()` during the Batch 26 dev-server restart) — the standalone script would now just print its no-op message.
- [x] Left the script in place (not archived) — matches this repo's standing convention: every migration script (`migrate_add_item_max_level.py`, `migrate_add_purchase_order_tables.py`, `migrate_add_fm_number_and_payment_status.py`, etc. — 10 total) stays in `scripts/` permanently as an idempotent historical record, whether or not it was ever run standalone.
- Tebello asked to ignore the Batch 24 payment-status review item for now — carried forward, not actioned this entry.
- Blockers: None.

## Batch 27 — Dashboard & BOM Builder UI Fixes (2026-07-15)
- [x] Tebello requested 6 UI/UX fixes from 3 live screenshots (Build Works Pack page, WO0001 detail, Dashboard). Spec written first (5 files touched — plan-first rule), confirmed with Tebello via AskUserQuestion on the one genuine business-judgment call (sales-value card scope: Draft+Open SOs only, not all-time revenue): `docs/specs/dashboard-bom-ui-fixes-2026-07-15.md`.
- [x] Dispatched a single `executor` agent, working directly on `master` (no worktree, per this repo's documented OneDrive git-corruption history) — 6 commits:
  - `0336953` — BOM Builder "Add Component" panel converted to an Alpine.js modal (matches Batch 25's Edit Item/Adjust Stock modal convention), hand-rolled filtered-`<div>` dropdown replaced with Tom Select (vendored, previously unused anywhere) bound to `catalogueItems`.
  - `2f632a3` — `.content-body` `max-width` 1400px → 1800px.
  - `9f0833f` — `.badge-draft`/`.badge-open` split into separate rules; Draft now `--fm-amber`, Open stays `--fm-blue` (affects SO and PO Draft badges app-wide).
  - `3123892` — FM / Job Number added as the first column of the Dashboard's Open Sales Orders table (`so.job_numbers`, existing field, no route change).
  - `3823ef9` — Total Sales Value dashboard card (Total / Cash Sale / Account), `routes/dashboard.py` sums `total_incl` over `SO_ACTIVE` (Draft+Open) SOs, split by `payment_status` prefix.
  - `2b2b3e4` — WO Edit page root-cause fix: `addItemFromCatalogue()` always appended a flat top-level row, so replacing a component always produced a new "main item" instead of a nested one. Added an "Add as component of…" select (mirrors `build_bom.html`'s `componentFanLine` pattern) that inserts the new row as a `component-row` under the chosen assembly; default (unselected) preserves today's flat-row behavior.
- [x] Tests: `tests/test_dashboard.py` (new, 6 tests — FM column + sales value card math, delta-based against the shared cumulative test DB), `tests/test_works_orders_edit.py` (new, 3 tests — nesting regression, standalone-still-flat regression, GET smoke test for the new select). Full suite: 191 → 200 passed.
- [x] Orchestrator-side verification: read every diff line-by-line, independently re-ran the full suite (200 passed, matches executor's report), `ruff check` clean on all touched files (2 pre-existing unrelated `E712` warnings on untouched lines in `routes/dashboard.py` left alone). Offline-first re-verified (`grep -rn "cdn\."/"fonts.googleapis"` on templates/static — only hit is the pre-existing `static/vendor/download_assets.py` build script, not runtime code).
- [x] Killed a stale dev-server process (started 20:24, before this batch's 21:2x–21:36 commits — 4th occurrence of this recurring class of issue, see Batch 12/20/Ops notes) before live verification. Restarted fresh and drove all 6 items through the real browser against `instance/sops.db`:
  - Dashboard: FM/Job Number column renders first with real data; Total Sales Value card shows R767,473.83 / R269,341.11 / R498,132.72 (Cash Sale + Account = Total, confirmed by arithmetic) for the live Draft+Open SO set.
  - Badges: computed `background-color` confirmed `rgb(245,158,11)` (amber) for Draft, `rgb(37,99,235)` (blue) for Open.
  - `.content-body` computed `max-width: 1800px` confirmed.
  - BOM Builder modal (SO4717/build-bom): opened via Alpine (`componentOpen` toggle confirmed), Tom Select initialized and search-matched correctly, full add-component flow completed (row added, modal auto-closed) — never submitted, so no data was written.
  - WO Edit nesting fix (WO0006/edit): selected the assembly target, added a catalogue item, confirmed it inserted as a `component-row` nested under the assembly (not a new top-level row) and that `syncEditJSON()` correctly nests it into the assembly's `components` array in the POST payload — never submitted, so no data was written.
- Known gap, flagged not fixed (pre-existing, not introduced by this batch): running the new `test_works_orders_edit.py` tests with SQLAlchemy warnings promoted to errors (`-W error::sqlalchemy.exc.SAWarning`) surfaces `Identity map already had an identity for (<class 'models.BOMLine'>, ...), replacing it with newly flushed object` inside `update_order()`'s existing delete-then-recreate-in-one-transaction pattern (`routes/works_orders.py` ~line 303-330, untouched by this batch). Under normal (non-strict) test/production execution this is a warning only — the full suite passes and the persisted result is correct (verified by the passing regression test) — but it signals a latent identity-map hygiene issue in that pre-existing bulk-delete pattern, newly surfaced because this batch's test is the first to exercise "edit a WO that already has an ASSEMBLY_ITEM line, in one POST." Not investigated further — out of scope for a UI-fix batch, worth a dedicated look if it ever manifests as a real failure.
- Next task: none queued — awaiting Tebello's review/commit confirmation.
- Blockers: None.
- Commits: `0336953`, `2f632a3`, `9f0833f`, `3123892`, `3823ef9`, `2b2b3e4`. Spec (`dashboard-bom-ui-fixes-2026-07-15.md`) to be committed separately per convention.

## Batch 28 — Stock Order Detail: Notes → Comments (availability/on-order) (2026-07-15)
- [x] Tebello requested (from a live STO0014 screenshot) that the Stock Order detail page's "Notes" column become a "Comments" column stating availability, or referencing the closest-due open PO when short. Small, precedented, 2-file change (no separate spec — `routes/stock_orders.py edit_order()`'s existing GET handler already does the exact same bulk-fetch pattern this reuses).
- [x] `routes/stock_orders.py`: new `_line_comments(stock_order)` helper. Resolves each line's `item_code` to a catalogue `Item`, bulk-fetches `qty_on_order`/`qty_committed` (with `exclude_sto_id` so the order's own demand isn't counted against itself, matching every other single-order shortfall site) and `next_po_due` via `services/demand.py`, and reuses `item_to_bom_json()` (imported from `routes.sales_orders`, already used by `edit_order()`) for the `available_qty` arithmetic rather than re-deriving it inline — this calc is already duplicated at 5 other sites per `.claude/agent-memory/reviewer/pattern_shortfall_duplication.md`, which explicitly asks to reuse the canonical calc rather than add a 6th copy when touching this area. Wired into `view_order()`.
- [x] `templates/stock_orders/detail.html`: `Notes` header → `Comments`; cell now reads `line_comments.get(line.id, '-')` instead of `line.notes`.
- [x] Tests: 4 new cases in `tests/test_stock_orders.py` — unmatched item code, fully-available, short-with-a-PO-due-date (verified the PO's qty doesn't have to fully cover the gap to still be referenced), short-with-no-PO. Full suite: 200 → 204 passed.
- [x] `ruff check` clean on both touched Python files (the pre-existing `E712`/`E711` findings in `edit_order()` are untouched lines, out of scope).
- [x] Live-verified against the real `instance/sops.db` — navigated to the exact STO0014 from Tebello's screenshot: `Available (5.0)`, `Available (6.0)`, and 3 genuine `Short N.0 — not on order` lines (real live shortfalls, not test data). Caught and killed a second stale dev-server process bound to the same port mid-verification (Windows allowed two processes to hold `LISTENING` on :5000 simultaneously — same recurring class of issue as Batch 12/20/27, but this is the first time it manifested as two concurrent listeners rather than one leftover from a prior session) before trusting the render.
- Next task: none queued — awaiting Tebello's review/commit confirmation.
- Blockers: None.
- Commits: not yet committed — pending Tebello's review of this entry.
