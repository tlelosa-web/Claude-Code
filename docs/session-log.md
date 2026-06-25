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
