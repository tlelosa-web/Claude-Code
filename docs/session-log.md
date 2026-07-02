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
