# Session Log

## 2026-05-21 - Project Reorganisation

- Domain classified as Software/AI.
- Checked project tree, git status, README, AGENTS.md, and docs/todo.md.
- Added DCOE support structure required by AGENTS.md.
- Preserved the current Flask app layout at the repository root to avoid breaking imports and runtime paths.
- Moved the SOPS product brief into `docs/specs/sops-product-spec.md`.
- Verified no CDN references in templates and no Google Fonts references in static assets.
- Fixed Windows console encoding risk in `app.py` by replacing Unicode status glyphs with ASCII output.
- Logged remaining pytest/import hang under `docs/bugs/pytest-flask-sqlalchemy-import-hang.md`.

## 2026-06-24 — Full Health Screen

- Domain classified as Software/AI.
- Ran full health screen per Debugger Brief (7 checks), assigned manually.
- **Check 1 (App Startup):** PASS — Flask starts cleanly on localhost:5000.
- **Check 2 (Route Registration):** PASS — 31 routes, all blueprints registered.
- **Check 3 (Test Suite):** WARNING — 15 passed, 1 failed (stale assertion: `"BOM Builder"` → `"Build Works Pack"`), 2 root scripts blocked by missing `requests` module, 75 deprecation warnings.
- **Check 4 (Database Integrity):** PASS — 8 tables present, 2,999 items vs 2,967 expected. DB in `instance/sops.db`. Root `sops.db` is 0-byte stub.
- **Check 5 (Offline Assets):** PASS — No CDN, Google Fonts, or unpkg references. All vendors self-hosted in `static/vendor/`.
- **Check 6 (Known Risk Areas):** PASS — All 4 inspected files clean (imports, kwargs, form wrappers, model definitions).
- **Check 7 (June 17 Fix Verification):** PASS — All 5 fixes confirmed present in current code.
- Written findings to `docs/bugs/health-screen-2026-06-24.md`.
- **Outcome:** Codebase is STABLE. No production-impacting defects. Three action items identified: fix stale test assertion, install/remove `requests`, plan deprecation cleanup.
- **Next task:** Human review of health-screen report, then assign Executor to fix Check 3 issues.
- **Blockers:** None — report ready for human review.

## 2026-06-24 — Task 1: Fix stale test assertion

- Date: 2026-06-24
- Task: Fix stale test assertion — test_build_bom_page_renders_item_catalogue
- Files changed: tests/test_bom_builder.py
- Commit hash: bae4d6d
- Next task: Task 2 — install requests or remove root-level test scripts

## 2026-06-24 — Task 2: Remove root-level ad-hoc test scripts

- Date: 2026-06-24
- Task: Remove root-level ad-hoc test scripts that blocked pytest collection
- Files changed: test_build_bom_post.py, test_build_bom_with_correct_ids.py
- Commit hash: f54d4e9
- Next task: Task 3 — migrate Query.get() and utcnow() deprecations

## 2026-06-25 — Task 3: Deprecation cleanup — Query.get() and utcnow()

- Date: 2026-06-25
- Task: Deprecation cleanup — Query.get() and utcnow()
- Files changed: services/bom_builder.py, services/doc_generator.py, services/stock_service.py, services/item_importer.py, tests/test_bom_builder.py, tests/test_stock_service.py
- Commit hash: 32a1405
- Next task: None — all 3 tasks complete, SOPS baseline clean

## 2026-06-25 — Add /continue command and executor session-log rule

- Date: 2026-06-25
- Task: Add /continue command and executor session-log rule
- Files changed: .claude/commands/continue.md, .claude/agents/executor.md
- Commit hash: 97369be
- Next task: None — baseline complete
- Blockers: None

## 2026-06-29 — Remaining Plan Items

- Domain: Software/AI.
- Audited codebase against AGENT_build_bom_works_pack.md spec and found 4 gaps.
- **Fix 1 (Spec gap):** `build_bom` GET handler now checks for existing WorksOrder and
  redirects with flash — spec required this but only POST had the guard.
- **Fix 2 (Code quality):** Removed debug `print()` statements from `build_bom` POST.
- **Fix 3 (Deprecations):** Replaced remaining `Query.get()` calls in routes with
  `db.session.get()` — previous cleanup (2026-06-25) covered services/tests only.
- **Fix 4 (Deprecations):** Replaced `datetime.utcnow()` with `datetime.now()` in routes.
- **Fix 5 (Functional gap):** Added `POST /stock-orders/<id>/complete` route — `StockOrder`
  model had `Complete` as a valid status but there was no route or UI to set it.
- **Fix 6:** Added Mark Complete button to `templates/stock_orders/detail.html`.
- **Fix 7 (Test coverage):** Added `tests/test_stock_orders.py` with 8 tests covering
  list, detail, 404, cancel (open), cancel (complete blocked), complete (open),
  complete (cancelled blocked), complete (idempotent).
- Commit: `520f955` — 25 tests passing, 2 residual LegacyAPIWarnings from `get_or_404()`
  inside Flask-SQLAlchemy (not controllable from app code).
- Next task: None — plan complete.
- Blockers: None. Note: git lock files on OneDrive mount required direct ref write.

## 2026-07-01 — Batch 7 commit + line-ending normalization (backfill)

- Domain: Software/AI.
- Commit `21bafc2`: Stock Order edit route/template + WO edit BOM qty fix (work done 2026-06-29, committed 2026-07-01).
- Commit `2cb58b3`: normalize line endings across repo (OneDrive sync artifact).

## 2026-07-01 — Multi-page Sales Order PDF parser bug fix

- Domain: Software/AI.
- Task: Verify a user-supplied 2-page Sales Order PDF (SO4684) would upload correctly.
- Ran the actual PDF (found in `uploads/`) through `parse_sales_order_pdf` directly and found only
  12 of 16 line items were captured — subtotal R214,574 vs Grand Total R241,125. No parse error was
  raised because `line_items` wasn't empty, so this would have silently produced an incomplete BOM
  on upload.
- **Root cause 1:** The "BANKING DETAILS"/"Total Discount:" footer repeats on every page of the SO
  template, not just the last page. The old code set a document-level `table_ended` flag on hitting
  it, which broke the outer per-page loop — so page 2 was never scanned at all.
- **Root cause 2 (uncovered by fixing #1):** Continuation pages (2+) also repeat the full page header
  (title, FROM/TO blocks, "Description/Quantity" column header) before their real line items resume.
  The old code assumed page 2+ dropped straight into table rows and forced `table_started = True`
  immediately, so the repeated header block was misparsed as ~17 garbage/blank line items.
- **Fix:** `services/pdf_parser.py` — scoped the footer-triggered `break` to the current page's line
  loop only (not the whole document), and reset `table_started = False` at the top of every page so
  each page re-detects its own "Description/Quantity" header before parsing rows.
- Added `tests/fixtures/FM4167-4771 - Vortron - Sales Order - SO4684.pdf` (real 2-page fixture) and
  `test_parse_multipage_captures_all_line_items` in `tests/test_pdf_parser.py`.
- Verified: all 26 tests green (was 25), including the new regression test.
- Next task: None — awaiting commit confirmation from Tebello.
- Blockers: None.

## 2026-07-01 — Multi-Fan-Line Works Pack (5 WOs per Sales Order)

- Domain: Software/AI.
- Tebello reviewed the now-fully-parsed SO4684 in the live Build Works Pack UI and flagged that
  lines 1, 3, 6, 10 & 12 (5 distinct MAXFLO fan models) each require their own individual BOM — the
  `build_bom` route only supported a single Fan line per Sales Order and hard-stopped with
  "Only one line can be marked as Fan" otherwise.
- Wrote spec `docs/specs/multi-fan-build-bom.md`. Clarified design via AskUserQuestion before
  building: (1) 5 fan lines → 5 separate Works Orders, not one WO with 5 nested assemblies; (2) keep
  the single shared BOM Components list, add a per-row "For Fan line..." dropdown rather than
  repeating the whole components panel per fan.
- `routes/sales_orders.py build_bom`: classifies multiple `fan_line_ids` instead of one; loops to
  create a WorksOrder + ASSEMBLY_ITEM header per fan line; groups submitted components via new
  `component_fan_line_id[]` field (defaults to the single selected fan line when only one is chosen,
  keeping old single-fan form payloads working unmodified).
- `templates/sales_orders/build_bom.html`: removed `enforceSingleFan`; added `componentFanLine`
  dropdown + `refreshFanLineOptions()` rebuilt from currently-checked Fan radios.
- Added `test_build_bom_creates_separate_wo_per_fan_line` to `tests/test_bom_builder.py`.
- Verified against the real SO4684 scenario end-to-end (not just unit tests): posted the exact
  line classification from Tebello's screenshot (lines 1,3,6,10,12 = Fan) through the live route —
  produced WO0001–WO0005, each correctly matched to its catalogue item (MFAZ5600554, MFAZ5601104,
  MFAZ8004004, MFAZ8005504 x2), remaining 11 lines collapsed into STO0001.
- Full suite: 27 tests green.
- Next task: None — awaiting commit confirmation from Tebello.
- Blockers: None.

## 2026-07-02 — Batch 10: STO Print + Required FM Number on Build Works Pack

- Domain: Software/AI.
- Added `GET /stock-orders/<id>/print` route (`routes/stock_orders.py`, no status guard,
  mirrors `works_orders.print_order`) and a new standalone `templates/stock_orders/print.html`
  (modeled on `picking_list_print.html`) — STO/SO/customer/job-number table, line items,
  signoff block, auto-print script.
- Added a Print button to `templates/stock_orders/detail.html`, always visible regardless of
  status.
- Added an editable `job_numbers` (FM number) input to `templates/sales_orders/build_bom.html`,
  pre-filled from `so.job_numbers`.
- `routes/sales_orders.py build_bom()`: reads `job_numbers` early, requires it (flash + redirect)
  when at least one line is marked Fan, persists it onto `so.job_numbers` when non-blank;
  stock-only builds unaffected.
- Fixed a test-fixture collision in `tests/test_stock_orders.py`: `setup_data` was minting
  `StockOrder` numbers in the same `STOxxxx` format the app auto-generates, colliding with
  build_bom-driven STO creation in the shared session-scoped in-memory test DB — renamed to
  `STO-TEST-xxx`.
- Added `test_print_renders` / `test_print_404_for_missing` (test_stock_orders.py) and
  `test_build_bom_requires_job_number_for_assembly` / `test_build_bom_saves_job_number_on_assembly`
  / `test_build_bom_stock_only_does_not_require_job_number` (test_bom_builder.py); updated the two
  existing fan-line build_bom tests to supply `job_numbers` now that it's required.
- Verified full suite green (32 passed) immediately before commit.
- Commit: `f2438fa`.
- Known pre-existing issue flagged, not fixed (out of scope): `templates/sales_orders/detail.html`
  ~line 95 raises `TypeError` if any `SOLineItem.excl_price` is `None` (only reachable via lines
  created outside the normal PDF-parse path, e.g. directly via tests/DB).
- Next task: None queued — awaiting Tebello's next task.
- Blockers: None.

## 2026-07-06 — Batch 11: Finish/verify in-flight Job Numbers + SO Close work

- Domain: Software/AI.
- `/continue` surfaced 7 modified files + 1 untracked script left uncommitted from a prior
  unlogged session: per-line job numbers (spec `docs/specs/sales-order-job-numbers.md`) plus
  an unplanned `can_close_sales_order()` helper and manual Sales Order "Close Order" feature.
- Verified against the spec's acceptance criteria one by one:
  - Per-line Job/FM number input + validation on Build Works Pack: present (`build_bom.html`,
    `build_bom()`).
  - Saved Sales Orders retain the combined job numbers: present (`so.job_numbers`,
    `so.job_reference` property, pre-existing).
  - BOM/WO/PL pages and print documents show the job/SO reference: **gap found** — Works Order
    print and Stock Order print already showed Job Number(s), but
    `templates/works_orders/picking_list_print.html` did not. Fixed by adding a Job Number(s)
    row to the picking list print info table.
  - Tests pass: were passing (32/32) but with zero coverage of the new
    `close_order`/`can_close_sales_order` route or the `'Complete'` → `'Closed'` SO auto-close
    rename in `mark_complete`/`confirm_pick`/`complete_order`. Added
    `tests/test_sales_order_close.py` (7 tests) covering manual close (blocked while WO/STO
    open, succeeds once both Complete, idempotent when already Closed) and auto-close from
    both the Works Order and Stock Order completion paths (closes only once the other order
    type is also done).
- Cleanup: removed a dead `job_numbers_input` variable in `build_bom()` left over from the old
  single SO-level job number field, now superseded by per-line collection.
- Ran `scripts/migrate_add_so_line_job_number.py` — confirmed `job_number` column already
  present on `instance/sops.db` (migration had already been applied in the prior session).
- Flagged to Tebello: the SO status rename (`'Complete'` → `'Closed'`) and the whole Close
  Order feature are a scope expansion beyond the job-numbers spec. Confirmed no other code
  path reads `SalesOrder.status == 'Complete'`, so the rename is safe as shipped.
  `scripts/fix_so_status.py` (pre-existing, unrelated to this batch) still writes the old
  `'Complete'` value if it were ever re-run — left untouched, out of scope.
- Full suite: 39 tests green (was 32).
- Next task: none queued — awaiting Tebello's review/commit confirmation.
- Blockers: None.
- Committed: `d59f99c`.

## 2026-07-06 — Batch 12: Sort Sales/WO/STO lists by Delivery Date

- Domain: Software/AI.
- Tebello asked for Sales Orders, Works Orders, and Stock Orders lists to be sorted by
  delivery date.
- `routes/sales_orders.py`: changed `list_orders()` from `created_at.desc()` to
  `nullslast(SalesOrder.delivery_date.asc())` — soonest delivery first, orders with no
  delivery date sink to the bottom instead of floating to the top.
- `WorksOrder` and `StockOrder` have no `delivery_date` column of their own (it lives on the
  parent `SalesOrder`), so `routes/works_orders.py` and `routes/stock_orders.py`
  `list_orders()` now outer-join to `SalesOrder` and sort on `SalesOrder.delivery_date` the
  same way.
- Added a "Delivery Date" column to `templates/works_orders/list.html` and
  `templates/stock_orders/list.html` (Sales Orders list already displayed it) so the sort
  key is visible on screen, not just implicit in row order.
- Verification caught a real gotcha: the first live check against `instance/sops.db` via the
  dev server still showed the old `created_at`-descending order. Root cause was a stale
  Werkzeug debug-reloader child process (Flask's Windows reloader runs the actual server in
  a child process separate from the one bound in `Get-NetTCPConnection`) that hadn't picked
  up the route change. Killed both the parent and child process on port 5000, started a
  clean instance, and confirmed all three list pages now render in ascending delivery-date
  order against real production data.
- Full suite: 39 tests green — no existing test asserted list ordering, so none needed
  updating.
- Next task: none queued — awaiting Tebello's review/commit confirmation.
- Blockers: None.

## 2026-07-07 — Batch 13: Purchase Order Module + Reorder Point Signals (Enhancements 1 & 2)

- Domain: Software/AI.
- Tebello attached two real Sage-exported Supplier Purchase Order PDFs (PO4088 - LUFT,
  PO4106 - ATTENU-TEC) and asked for the Purchase Order module (Enhancement 1) and reorder
  point signals (Enhancement 2) to be built, per `docs/specs/purchase-order-module-plan.md`.
- Confirmed both POs are the same Sage template family as Sales Orders — identical
  line-item table column geometry, different header fields. Extracted the shared
  geometry-dependent parsing (`clean_numerical_str`, `build_merged_lines`,
  `parse_line_item_row`, multi-page line-item walking) out of `services/pdf_parser.py` into
  new `services/pdf_common.py`, refactored the SO parser to use it — no behavior change,
  verified against the existing 39-test baseline before building anything new on top.
- New `services/po_parser.py`: `parse_purchase_order_pdf()` (header regex for
  NUMBER/REFERENCE/DATE/DUE DATE/OVERALL DISCOUNT %/SUPPLIER VAT NO/supplier name, reuses
  `pdf_common` for line items) + `split_item_code()` (splits `"<code> - <description>"` on
  the *first* ` - ` only, since descriptions often contain further ` - ` segments like
  degree suffixes). Verified against both real sample PDFs — all extracted item codes
  matched existing `Item.code` rows in `data/ItemListingReport.csv` exactly.
- New `PurchaseOrder`/`POLine` models (`models.py`) + migration script
  (`scripts/migrate_add_purchase_order_tables.py`) — denormalized supplier fields on
  `PurchaseOrder`, no separate `Supplier` master table yet (not needed until spend-by-
  supplier reporting matters). `POLine.item_id` is nullable — unmatched lines stay
  unlinked (`item_code_raw` preserved) until manually linked, never blocking a save.
- New `routes/purchase_orders.py` + `templates/purchase_orders/` (upload/review two-step
  form, list, detail with inline "Link Item" fixup, A4 print, receive with full/partial
  quantity entry per line, cancel blocked once any receipt exists). Registered blueprint in
  `app.py`, added sidebar nav entry. Receiving calls the *existing*
  `services.stock_service.receipt()` (already present, unused until now) per line and
  updates `Item.last_cost` from the PO line price.
- Enhancement 2: `Item.reorder_point`/`reorder_qty` columns (both default 0.0 = "not set",
  self-heals via `ensure_schema_columns()` in `app.py` same pattern as
  `sales_order.job_numbers`, plus an explicit migration script per the hard rule). Stock
  Report gained a "Below Reorder Point" filter + amber row highlight + Reorder Point column;
  Dashboard gained a stat card; new `purchase_orders.create_from_shortfall()` route builds a
  Draft PO (`PO-DRAFT-####` numbering, kept separate from real supplier PO#s) with one line
  per shortfall item at `reorder_qty`/`last_cost`.
- Gap caught during implementation: reorder_point/reorder_qty had no UI to actually set them
  per item (only reachable via direct DB access) — added a small "Reorder Settings" form +
  `items.update_reorder_settings()` route on the Item detail page so the feature is usable
  end-to-end, not just plumbed.
- Checked `black`/`ruff` against the new files only — clean. Did *not* run project-wide
  `black .`/`ruff check .` fixes: the existing codebase already fails `black --check` at
  baseline (pre-existing, confirmed before touching anything), so a full reformat would
  create a large unrelated diff. Flagging this to Tebello as a separate future decision
  rather than folding it into this batch.
- Verification: in addition to per-route unit tests, added one true end-to-end test
  (`test_upload_save_receive_attenutec_po`) that uploads the real PO4106 fixture, scrapes
  the `lines_json` hidden field out of the rendered review HTML exactly as a browser would
  submit it, saves, and receives — confirmed stock movement + `last_cost` update against
  real data (4x 800S1.5DP @ R4,423).
- Offline-first constraint re-verified: `grep -r "cdn\."` / `fonts.googleapis` across all new
  templates returns empty.
- Full suite: 62 tests green (was 39). 8 atomic commits, one per logical unit (pdf_common
  refactor, po_parser, models+migration, PO routes, reorder columns, reorder UI/reports,
  reorder-settings form, e2e test).
- Next task: none queued — awaiting Tebello's review/commit confirmation. Enhancement 3
  (demand-netted shortfall calc, per `docs/research/erp-mrp-benchmark-2026-07-07.md`) is the
  next item on the roadmap once 1 & 2 are reviewed.
- Blockers: None.
- Commits: `65f8443`, `15a265e`, `6f0dc53`, `b4bfdc4`, `c06a9f5`, `0b08b7c`, `fc63598`,
  `c0a5ceb`.

## 2026-07-09 — Batch 15: CLAUDE.md v3.2 + Repo Folder Cleanup

- Domain: Software/AI.
- `/continue` surfaced uncommitted, unlogged CLAUDE.md v3.1 → v3.2 work already sitting in the
  working tree (user-level `~/.claude/agents/` roster, project-level `.claude/agents/` reserved
  for overrides only). Deleted the leftover `CLAUDE.md.v3.1.bak`, staged the CLAUDE.md diff plus
  the now-redundant `.claude/agents/executor.md` deletion, committed as `804738a`.
- Tebello opened `AGENT_build_bom_works_pack.md` (the v1.0 Build BOM/Works Pack spec from
  2026-06-12) and asked if it was still relevant. It wasn't: its core assumption ("only one line
  can be marked as Fan") was overturned by the multi-fan-line work in Batch 9, it has no concept
  of the per-line job numbers added in Batch 11, and it documents a `sops/routes/`/`sops/models.py`
  package layout that was never the real repo structure.
- Confirmed the doc's real learnings are already captured elsewhere before deleting it: multi-fan
  behavior in `docs/specs/multi-fan-build-bom.md` + the 2026-07-01 session-log entry; job numbers
  in `docs/specs/sales-order-job-numbers.md` + the 2026-07-06 (Batch 11) entry. No new spec content
  needed writing — just removal.
- Asked to remove the file and do a broader folder cleanup. Surveyed all git-tracked files outside
  the main app dirs (`git ls-files`) and found more orphaned material than just the one doc:
  - A full **duplicate `sops/` package** (`sops/app.py`, `sops/config.py`, `sops/models.py`,
    `sops/__init__.py`) — dated 2026-06-12, the same day as the stale spec doc. Traced it to
    predate `docs/decisions/0001-keep-flask-app-at-root.md`, which explicitly decided to keep the
    Flask app flat at the repo root and treat any future `sops/` package move as a separate,
    never-taken task. Confirmed via `git grep` that nothing in the live app imports from `sops.*`
    (only the dead debug scripts and the doc being removed did). The package also had untracked
    runtime artifacts next to it — `sops/instance/sops.db` (53KB, a real but orphaned test-run DB,
    disconnected from the actual `instance/sops.db`) and empty `sops/uploads/`, `sops/__pycache__/`.
  - **Six 2026-06-17 ad-hoc debug scripts** at the repo root and in `scripts/`
    (`check_db_state.py`, `check_so_lines.py`, `find_item.py`, `fix_bom_line.py`, `test_render.py`,
    `scripts/quick_update_items.py`) — the same "Works Pack Debug Session" that commit `f54d4e9`
    (2026-06-24) already partially cleaned up (`test_build_bom_post.py`,
    `test_build_bom_with_correct_ids.py`); these six siblings were missed at the time.
    `quick_update_items.py` also imported from the dead `sops` package above, so it was silently
    broken as well as stale.
  - **Eight tracked `logs/*.log`/`*.txt` files** (2026-05 through 2026-07) — historical
    `python app.py` stdout/stderr captures that had been committed instead of gitignored. One
    (`startup.err.log`) contained a traceback referencing the project's pre-rename folder name
    (`3. Works Order & B.O.M`) — harmless (just log text) but confirmed via `git grep` to be the
    *only* stale-path reference anywhere in tracked files; all real source/config paths were
    already clean.
  - Three pure-junk files not worth archiving: root `sops.db` (0-byte stub, already flagged twice
    in `docs/bugs/health-screen-2026-06-24.md` and `docs/session-log.md` but never removed), root
    `startup_test.log` (0 bytes), and a root-level `FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf`
    confirmed byte-identical to the canonical `data/` copy via `diff`.
- Decision: archive (don't delete) anything non-trivial, since "archive" was the explicit
  instruction and git-tracked moves are cheap to reconsider. New `archive/` at repo root with
  `archive/README.md` explaining what's in each subfolder and why, plus pointers back to the ADR
  and specs that made each piece obsolete. Preserved the orphaned `sops/instance/sops.db` inside
  `archive/pre-adr-sops-package/instance/` rather than deleting it outright, even though it was
  untracked, since it's real (non-empty) data of unclear origin.
- Added `logs/*` + `!logs/.gitkeep` to `.gitignore` so run-output logs stop accumulating in git —
  addresses the root cause of the stale-path log rather than just moving today's copies aside.
- Updated `README.md` project structure tree to drop references to now-archived/deleted files and
  note the `logs/` gitignore change and new `archive/` folder.
- Verification: `git grep` confirmed nothing references `quick_update_items.py` outside the README
  tree diagram (fixed) before archiving it; full suite re-run after removing the dead `sops/`
  package — 69 tests green, no regressions.
- Next task: none queued — awaiting Tebello's review/commit confirmation. Enhancement 3
  (demand-netted shortfall calc) remains the next roadmap item once picked up.
- Blockers: None.

## 2026-07-10 — Batch 16: FM Numbers on WO/STO + Default-Open Lists + SO Report Parity

- Domain: Software/AI.
- Spec: `docs/specs/fm-numbers-default-open-so-report.md` (commit `7af3283`) — two scope
  decisions confirmed with Tebello via AskUserQuestion before building: track FM number
  properly on both WO and STO (schema columns, not a display-only approximation), and make
  Payment Status a fixed dropdown rather than free text.
- `models.py`: added `WorksOrder.job_number`, `StockOrderLine.job_number`, and
  `SalesOrder.payment_status` (+ `PAYMENT_STATUS_OPTIONS` constant) columns; `StockOrder.job_numbers`
  and `SalesOrder.total_incl` added as computed `@property`s rather than stored columns — both
  derive from existing line data using the same pattern as the pre-existing `job_reference`
  property, so no extra column (and no drift risk) was needed for either. Migration script +
  matching `ensure_schema_columns()` self-heal entries added per the hard rule. Committed as
  `dfbb763`.
- `routes/sales_orders.py build_bom()`: each per-fan-line `WorksOrder` now gets `job_number` set
  from its originating Fan line; `StockOrderLine.job_number` captured from the already-existing
  (previously Fan-only-enforced) per-line job number input — no template change was needed there,
  since the input already rendered for every line regardless of role. Job Number column/row added
  to the WO/STO list and detail templates. SO report parity: added Sales Rep, Total, and Payment
  Status columns to the Sales Orders list, relabeled "Reference" to "Customer Ref.", and added a
  Total row + inline Payment Status dropdown (new `POST /sales-orders/<id>/payment-status` route)
  to the SO detail page. Committed as `cace063`.
- Default `?view=open|all` flipped so bare `/sales-orders`, `/works-orders`, `/stock-orders`,
  `/purchase-orders` now default to Open (was `all` — Batch 14's original opt-in decision,
  explicitly reversed this time per Tebello). `?view=all` still works as opt-in. Four one-line
  route changes, no template changes needed since the All/Open toggle already read the `view`
  variable. Committed as `3c8e873`.
- Tests: updated `tests/test_order_list_filters.py` (renamed the "default shows all" tests to
  "default hides inactive statuses", added new "all view still shows everything" tests for all 4
  modules); extended `tests/test_bom_builder.py` with 2 new tests (per-fan-line `WorksOrder.job_number`,
  optional stock-line job number rolling up into `StockOrder.job_numbers`); added
  `tests/test_so_report_fields.py` covering `total_incl`, the `payment_status` route (including
  rejecting an invalid value), and the `StockOrder.job_numbers` rollup with duplicate/blank inputs.
  Committed as `04b8045`.
- Full suite: 86 tests green (was 69). Offline-first re-verified (`grep -rn "cdn\."`/`fonts.googleapis`
  on templates/static — empty). Manually verified via live dev server: SO/WO/STO list pages 200
  with the new columns present, SO detail payment-status dropdown renders all 5 options correctly.
- Known gap, accepted rather than fixed: pre-existing WOs/STOs created before this migration have
  no Job Number and no reliable backfill source — multi-fan Sales Orders have no stored per-WO
  mapping in the old data, so guessing would be worse than a blank field.
- Next task: none queued at the time — Enhancement 3 (demand-netted shortfall calc) remained the
  next roadmap item.
- Blockers: None.
- Commits: `7af3283`, `dfbb763`, `cace063`, `3c8e873`, `04b8045`, `f470500` (docs: log Batch 16
  in `docs/todo.md` — this session-log entry itself was missed at the time and is being backfilled
  on 2026-07-13).

## 2026-07-10 — Ops: Pre-08:00 Test Data Purge

- Domain: Software/AI.
- Tebello requested deleting all Sales Orders (and their linked Works/Stock Orders) created before
  2026-07-10 08:00, to get a clean slate for exercising the new Job Number field — treating the
  pre-cutoff records as reloadable test data rather than anything worth preserving.
- Before deleting anything, checked whether a non-destructive backfill was actually possible instead
  (per the hard rule to ask before deleting in production data paths) — found that all 12 pre-cutoff
  Sales Orders could in fact have been backfilled (each had at most 1 WO and `so.job_numbers` was
  already populated; Batch 16's "can't backfill" caveat only applies to multi-fan Sales Orders with
  several WOs and no stored per-WO mapping). Surfaced this to Tebello via AskUserQuestion before
  proceeding; confirmed: delete anyway, the records are being used as test data and can be reloaded.
- Backed up `instance/sops.db` to `instance/sops.db.pre-cleanup-backup-20260710_150329` before
  deleting anything (not committed — DB files are gitignored, this was purely a local safety copy).
- Deleted 12 Sales Orders (SO4641, SO4653, SO4659, SO4652, SO4678, SO4683, SO4684, SO4693, SO4704,
  SO4676, SO4706, SO4708), 8 Works Orders (all already `Complete`), and 7 Stock Orders (3 `Complete`,
  4 `Cancelled`) via a one-off ORM script — explicit `session.delete()` per WO/STO then per SO, since
  the model relationships don't cascade SO→WO/STO automatically (only WO→BOMLine and
  STO→StockOrderLine do). Left `StockMovement` audit-trail rows untouched — out of the requested
  scope, they're independent ledger rows with no FK back to WO/STO.
- Gap found and fixed, unrelated to the purge itself but surfaced by it: an archived ad-hoc debug
  script (`archive/2026-06-debug-scripts/test_render.py`) matched pytest's `test_*.py` discovery
  pattern and ran top-level code against the *live* DB at import time (a hardcoded
  `get_works_order_print_context(9)`), so it started failing collection the moment WO id 9 was
  deleted. Added `pytest.ini` (`testpaths = tests`) so pytest only ever collects the real suite —
  this closes off the whole class of landmine (an archived script accidentally shaped like a test)
  rather than just patching this one instance. Committed as `3ff1aa0`.
- Full suite re-verified: 86 tests green. Live dev server spot-check confirmed SO/WO/STO list pages
  and Dashboard all render 200 with the reduced dataset (WO/STO lists correctly empty).
- Result: 15 Sales Orders remain (all created 2026-07-10 after 08:00); 0 Works Orders and 0 Stock
  Orders remain — every prior WO/STO record belonged to one of the purged pre-cutoff Sales Orders.
- Blockers: None.
- Commits: `3ff1aa0`, `f4b6eb5` (docs: log the purge in `docs/todo.md` — this session-log entry
  itself was missed at the time and is being backfilled on 2026-07-13).

## 2026-07-13 — Batch 17: Payment Status at Intake, Editable Delivery Date, Reopen SO/WO/STO, Resizable Columns

- Domain: Software/AI.
- Session opened with `/continue`; found `docs/session-log.md` was two batches behind
  `docs/todo.md` (Batch 16 and the Ops test-data purge, both 2026-07-10, had never been written
  up here) and backfilled both entries first, per Tebello's instruction — commit `868f56f`.
- Tebello asked to prepare five items for implementation: Payment Status settable at PDF
  review/save (plus a Partially Paid option), an editable Delivery Date in DD/MM/YYYY, a Reopen
  option for SO/WO/STO that reverses any issued stock, a check on whether the system already did
  any of this, and column-resize + no-wrap dates on the order list pages. Ran a factual audit
  (via a read-only Explore pass) before proposing anything, rather than assuming — found Payment
  Status and Delivery Date were both write-once-at-parse only; Reopen didn't exist anywhere
  (confirmed via `grep -rn "reopen"` across routes/templates/services — zero matches); and, more
  seriously, that `StockOrder.complete_order()` never called `stock_service` at all — Stock Order
  completion had been silently not deducting stock since the feature was built, despite the
  README claiming otherwise. Wrote the audit + a full spec to
  `docs/specs/payment-status-delivery-date-reopen-columns.md` before touching any code, then
  confirmed with Tebello via AskUserQuestion that resized column widths should persist (via
  `localStorage`) rather than reset on reload.
- Part A: added `Partially Paid` to `PAYMENT_STATUS_OPTIONS` (models.py), added the field to the
  upload/review form, and read it in `save_order()` (defaults to Pending when omitted so existing
  callers/tests are unaffected). Commit `ddd91b2`.
- Part B: new `POST /sales-orders/<id>/delivery-date` route + inline edit form on the SO detail
  page (Delivery Date was previously fixed at initial PDF parse with no way to change it after).
  Added a `dmy` Jinja filter in `app.py` and swept every place delivery_date/so_date rendered as
  text (list/detail/dashboard/bom templates) to use it, replacing a previously inconsistent mix of
  raw ISO and DD/MM/YYYY formatting — print templates already used DD/MM/YYYY and were left as-is.
  The editable `<input type="date">` keeps its ISO value attribute, which HTML5 requires
  regardless of display format. Commit `0a8070f`.
- Part C0 (the real gap found during the audit): `StockOrderLine.qty_issued` column + migration
  (`scripts/migrate_add_stock_order_line_qty_issued.py`) + `ensure_schema_columns()` self-heal
  entry, mirroring the existing `BOMLine.qty_issued`. Fixed `stock_orders.complete_order()` to
  actually resolve each line's `item_code` against the Item catalogue and call
  `stock_service.issue()` for the outstanding qty — lines with no catalogue match are flagged via
  flash and skipped rather than blocking the rest of the order. Commits `b03185f`, `ac61985`.
- Part C1: `services/stock_service.reverse_issue()` — adds stock back and logs a movement with a
  new `REVERSAL` type, deliberately kept distinct from `RECEIPT` so a reopened order's stock
  return can never be mistaken for a real supplier receipt in the audit trail. Commit `b03185f`.
- Part C2–C4 (the actual Reopen feature): `POST /works-orders/<id>/reopen`,
  `/stock-orders/<id>/reopen`, `/sales-orders/<id>/reopen`. Reopening a Complete WO/STO reverses
  its issued stock per line via `reverse_issue()` and resets `qty_issued` to 0 so a later
  re-completion issues correctly again; reopening a Cancelled WO/STO just flips status back since
  nothing was ever issued. Either path cascades the parent Sales Order back to Open if it had been
  auto-closed by that WO/STO completing. SO Reopen (Closed → Open) deliberately does **not**
  cascade down to its WOs/STOs — they may be Complete for a legitimate reason, and reopening the SO
  itself is meant to just allow editing it again (e.g. a note or a line), not undo child work.
  Commit `c7ce7f9`.
- Surfaced the new `REVERSAL` movement type in the Movement Report type filter and gave it its own
  badge color on the Item detail movement history (it was previously falling through to the
  generic grey "other" styling since it didn't exist as a type before this batch). Commit `c9b48e0`.
- Part D: new `static/js/resizable_columns.js` — no dependency, no CDN, drag handle on the right
  edge of each `<th>` on the four order list pages, `table-layout: fixed` while resizing, widths
  persisted per-table in `localStorage` (confirmed with Tebello, see above) and re-applied on next
  load. Added a `col-date` CSS class (`white-space: nowrap`) to every date column on those same
  four pages so dates stop wrapping onto two lines. Commit `c224459`.
- Tests added/extended per part: `test_sales_order_upload.py` (+3 for Payment Status capture),
  `test_delivery_date.py` (new, 5), `test_stock_service.py` (+1 for `reverse_issue`),
  `test_stock_orders.py` (+2 for the STO stock-deduction fix), `test_reopen.py` (new, 10 covering
  WO/STO/SO reopen, stock reversal, and the upward-only cascade), `test_resizable_columns.py` (new,
  4 wiring checks — table id + script tag present per page, since drag interaction itself isn't
  exercisable without a browser in this suite). Full suite: 111 tests green (was 86).
- Verification: ran the real dev server against `instance/sops.db` (not just the in-memory test
  DB) and curl-checked all 4 list pages (200, dates render DD/MM/YYYY, `col-date` class present,
  resizable-columns script served and wired), the SO detail page (Delivery Date/Payment Status
  inline forms present), and the Movement Report (REVERSAL filter option present). Offline-first
  re-verified (`grep -rn "cdn\."/"fonts.googleapis"` on templates/static — empty). Stopped the dev
  server afterward.
- Next task: none queued — awaiting Tebello's review/commit confirmation. Separately prepared a
  recommendation for Enhancement 3 (demand-netted shortfall calc, the long-standing next roadmap
  item per Batches 13/15/16) since Tebello asked for that alongside this batch — not started, spec
  not yet written.
- Blockers: None.
- Commits: `868f56f`, `3dc14f2`, `ddd91b2`, `0a8070f`, `b03185f`, `ac61985`, `c7ce7f9`, `c9b48e0`,
  `c224459`.

## 2026-07-14 — Batch 18: Enhancement 3 (Demand-Netted Shortfall Calc)

- Domain: Software/AI.
- Session opened with `/continue`. `docs/todo.md` and `df71f17` (2026-07-13, spec commit) showed
  Enhancement 3's spec (`docs/specs/demand-netted-shortfall.md`) written and awaiting review —
  Tebello reviewed it via a 3-example walkthrough, then confirmed to proceed with implementation.
- Routed through the DCOE Executor pattern: 6 sequential atomic commits, each dispatched as a
  fresh-context `executor` agent with the relevant model fields/file locations pre-verified by the
  orchestrator, followed by a `reviewer` (Opus) pass per the project's standing policy for changes
  driving purchasing/stock decisions.
- Commit `3e4c0ed`: new `services/demand.py` — `get_qty_on_order_bulk()`, `get_qty_committed_bulk()`,
  `get_next_po_due_bulk()` plus single-item wrappers, all batched (`{item_id: qty}` dicts) to avoid
  N+1 on catalogue-page callers. 17 new unit tests covering the spec's full PO/WO/STO status matrix.
- Commit `03109bf`: wired `item_to_bom_json()` (`routes/sales_orders.py`) and `static/js/bom_builder.js`
  to the netted `available_qty`, added the "(on order, due `<date>`)" hint. Mid-task discovery,
  confirmed by reading the actual templates rather than trusting the spec's description:
  `bom_builder.js` is only reachable from the WO/STO **edit** pages, not from `build_bom.html` (the
  page most order creation actually goes through), which shows no shortfall/qty info at all;
  `templates/sales_orders/bom_builder.html` is orphaned (no route renders it). Surfaced to Tebello
  rather than silently patching the wrong file — decision: fix exactly what the spec named now,
  leave `build_bom.html`'s missing shortfall display as a separate, declined-for-now feature gap.
- Commit `638b70d`: `/reports/stock/data` + `/export-csv` switched their "Below Reorder Point" filter
  and display to netted `available_qty`, `qty_on_hand` kept visible as ground truth, new
  `available_qty` Tabulator column.
- Commit `ea3e032`: found a 3rd, separate un-netted shortfall calc the spec never mentioned —
  `services/doc_generator.py::get_works_order_print_context()`, feeding both the WO detail screen
  and the print document. Tebello confirmed (AskUserQuestion) to fix it in the same batch rather
  than defer it. Netted it identically; left `works_order_print.html` untouched since it doesn't
  actually render `qty_on_hand`/shortfall (only defines an unused CSS class).
- Commit `46d0724`: bug fix, found by the commit-4 executor and escalated rather than worked around
  — `get_qty_committed_bulk()` had no way to exclude an order's own lines from its own demand count,
  so checking a WO's own BOM against itself falsely counted that WO's outstanding requirement as
  "committed elsewhere," producing a false shortfall equal to the order's own full requirement in
  the worst case (e.g. exactly-sufficient on-hand stock with zero real competing demand). Tebello
  confirmed fixing immediately rather than deferring. Added `exclude_wo_id`/`exclude_sto_id` params,
  wired into the WO/STO edit pages and WO print context; Stock Report deliberately excludes nothing
  (no single "current order" context there).
- Reviewer (Opus) pass on all 5 commits: **Approved with nits**, no blockers. Confirmed the
  exclusion fix correct/complete, N+1 avoided everywhere, STO `item_code` join degrades safely on
  unmatched codes, full spec test-plan covered. Flagged: Dashboard reorder stat card still un-netted
  (disagreeing with the Stock Report on the same signal), possible negative `qty_committed` from an
  over-issued line, 4 sites missing `qty_on_hand or 0.0` null-guards, `get_available_qty()` missing
  exclusion-param parity, and a >50-line duplication in `doc_generator.py` (deferred, non-blocking).
- Commit `f4fce5d`: Tebello confirmed (AskUserQuestion) netting the Dashboard card too, so it stops
  disagreeing with the Stock Report on the same purchasing signal (`low_stock_count` deliberately
  left as a raw physical-stock measure, unchanged). Also floored negative per-line committed demand
  at 0 (summed in Python rather than risk a SQLite `func.max` aggregate-vs-scalar ambiguity in SQL),
  added the 4 missing null-guards, added exclusion-param parity to `get_available_qty()`.
- Full suite: 111 → 147 tests green across the 6 commits, verified after every commit, no
  regressions. Each feature commit was also spot-checked against the real dev server
  (`/reports/stock`, `/reports/stock/export-csv`, `/` dashboard) before landing.
- Known gap, explicitly declined for this batch (Tebello's call): `build_bom.html`, the actual
  "Build Works Pack" page, still shows no stock-availability/shortfall info of any kind when first
  creating a Works Pack — the netting fix only reaches the *edit* path for an already-created
  WO/STO. Logged in `docs/todo.md` as the next candidate item if picked up later.
- Blockers: None.
- Commits: `3e4c0ed`, `03109bf`, `638b70d`, `ea3e032`, `46d0724`, `f4fce5d`.

## 2026-07-14 — Batch 19: CSV Import Quantity-Overwrite Removal

- Domain: Software/AI.
- Session opened with `/continue`. `git status` showed one untracked item left over from Batch 18:
  the Opus reviewer agent's persistent memory (3 pattern notes + index) from its review pass, never
  committed. Committed it as-is (`ced588c`) since it's legitimate cross-session project memory and
  nothing else was outstanding.
- Tebello asked for a plan to close the known `build_bom.html` shortfall-display gap (flagged at the
  end of Batch 18) and a review of how re-uploading `data/ItemListingReport.csv` affects the Stock
  Report. Read `routes/sales_orders.py`, `templates/sales_orders/build_bom.html`, and
  `services/demand.py` to scope the first; read `services/item_importer.py` and `routes/items.py`
  for the second. Presented both as findings/plan in chat (no code touched) — the `build_bom.html`
  plan remains queued, not yet built.
- The CSV review surfaced a standing risk: `/items/import`'s "Preserve Stock Quantities" checkbox
  defaulted to **unchecked**, meaning the default action overwrote `Item.qty_on_hand` for every
  existing item straight from the CSV with no diff/preview. Now that SOPS owns the full stock
  lifecycle (WO/STO issue, PO receipt, manual adjust, reversals — all through `stock_service` with
  an audit trail), this could silently revert live stock movements back to a stale Sage snapshot on
  one missed click.
- Tebello reviewed the finding and confirmed via chat: remove the toggle entirely rather than flip
  the default — quantity-preservation becomes the only import behavior, permanently, not an
  opt-in/opt-out choice. Wrote `docs/specs/csv-import-quantity-safety.md` capturing the decision and
  exact file/line scope before dispatching build work, per the plan-first rule (5 files touched).
- Routed the implementation through a single `executor` agent (one cohesive rename + call-site
  update + template edit + test rewrite, not a multi-stage feature — one atomic commit was the right
  shape, not several). Commit `2965367`:
  - `services/item_importer.py`: deleted the overwriting `import_items_from_csv()`; renamed
    `import_items_from_csv_skip_quantities()` → `import_items_from_csv()` (new-item quantity
    seeding on first-time import is unchanged; an existing item's `qty_on_hand` is never modified
    by import again).
  - `routes/items.py`: removed the `preserve_quantities`/`import_func` branch, single call site.
  - `templates/items/import.html`: removed both checkboxes, the hidden sync input, and the sync
    `<script>`; replaced with a static note that quantities are managed inside SOPS.
  - `tests/test_item_importer.py`: the existing-item test previously asserted *overwrite* behavior
    — left as-is it would now assert something false, so it was rewritten to assert preservation;
    added an explicit regression test for a CSV row carrying a different quantity than the DB's
    current value for that code.
- Orchestrator-side verification after the executor's commit: re-ran `tests/test_item_importer.py`
  (5 passed) and the full suite (148 passed, was 147, no regressions). Confirmed via `git grep` that
  `preserve_quantities` and `import_items_from_csv_skip_quantities` are gone from all live code —
  one stale reference remains in `archive/2026-06-debug-scripts/quick_update_items.py`, an
  already-documented dead script (imports from the defunct `sops.*` package, not run by the live
  app per `archive/README.md`); correctly left untouched by the executor as out of scope rather than
  silently expanding into the archive.
- `app.py`'s first-run bootstrap needed no code change — its local `from services.item_importer
  import import_items_from_csv` already resolves to the renamed function, and first-run behavior is
  identical (every item is new, so quantity-seeding still happens).
- Blockers: None.
- Commit: `2965367`. (Plus `ced588c` for the carried-over reviewer memory, committed at session
  start before this batch's work began.)
