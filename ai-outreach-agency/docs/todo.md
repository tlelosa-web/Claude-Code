# Task Queue — ai-outreach-agency

> Updated: 2026-07-04

---

## Completed

- [x] **ADR-001**: Lead store format — SQLite is source of truth, Sheets/Apollo are CSV input only. See `docs/decisions/ADR-001-lead-store.md`.
- [x] Scaffold `lead_import` module — schema dataclass, CSV reader, SQLite layer, 16 unit tests passing.
- [x] Scaffold `research` module — Apify stub, Claude summariser stub, pipeline with missing-website handling.
- [x] Scaffold `asset_gen` module — prompt builder, generator stub, AssetType enum, pipeline with logging.
- [x] Scaffold `approval` module — CLI approval gate (approve/reject/edit/quit), SQLite persistence.
- [x] Scaffold `email_draft` module — composer, Gmail stub, pipeline guard on approval decision.
- [x] Create `.env.example` + `.gitignore` + `src/config.py` (Settings from .env via python-dotenv).
- [x] Create `src/main.py` CLI runner — import, list, run, run-all commands. 53 tests passing.
- [x] Implement OpenRouter client wrapper with model routing — used by `research/claude_summariser.py` and `asset_gen/generator.py`.
- [x] Implement Apify actor integration for company research — real API call in `research/apify_client.py` (website-content-crawler), with `OFFLINE_MODE` fixture and graceful fallback on failure/missing key.
- [x] Add lead status lifecycle tracking — `VALID_TRANSITIONS` state machine in `lead_import/db.py`, enforced on every stage transition.
- [x] Set up `pyproject.toml` with dependencies (requests, python-dotenv, google-api-python-client, google-auth-httplib2, google-auth-oauthlib; pytest as dev extra).
- [x] Implement Gmail OAuth2 flow + draft creation — `email_draft/gmail_client.py` now runs a real `InstalledAppFlow` against `credentials.json`, caches the refresh token in `token.json` (gitignored), and calls `drafts().create()` (compose scope only, never send). `OFFLINE_MODE` still returns a stub id for tests, matching the Apify/OpenRouter convention.
- [x] Add rate limiting for external API calls — token-bucket `RateLimiter` (`src/shared/rate_limiter.py`) wired into OpenRouter, Apify, and Gmail clients, each with its own conservative default (60/30/20 per minute) overridable via env var.
- [x] Fix `src/main.py` not threading `db_path` through pipeline stages (would have crashed any real `run`/`run-all` on the first status update). Added CLI-level regression test. Ran a genuine live end-to-end pipeline test (real Apify + OpenRouter + Gmail draft) — all 6 stages confirmed working.
- [x] Add lead deduplication logic — `normalize_company_name`/`find_duplicate` in `lead_import/db.py` catch near-duplicate company names (case, whitespace, legal suffixes like "Pty Ltd"/"CC"/"Inc") sharing the same email, not just exact-string matches. Wired into `cmd_import` ahead of the existing `UNIQUE(company_name, email)` DB constraint, which stays as a backstop. 6 new tests, 91 passing.
- [x] **ADR-002**: Retire n8n from the stack — orchestration confirmed as in-process via the `ai-outreach` CLI (`run`/`run-all`), no external workflow engine. Resolves the "Confirm/retire this in an ADR" note that had been sitting in CLAUDE.md. `docs/architecture.md`'s n8n section replaced with a pointer to the ADR.
- [x] Google Sheets sync — closed, not built. Superseded by ADR-001 (SQLite is source of truth; CSV is the only import path; a live Sheets integration was explicitly rejected there).
- [x] Add schema migration convention — `src/lead_import/migrations.py` tracks numbered migrations applied via `PRAGMA user_version` in `init_db()`. First migration adds a `campaign` column (default `'default'`) to `leads`.
- [x] Add campaign management — `--campaign` on `import`/`list`/`run-all` (group/filter leads by campaign) and `--asset-type` on `run`/`run-all` (per-invocation override of the asset type used for that batch), instead of a persisted config file/table.
- [x] PDF export for generated assets — `src/asset_gen/pdf_export.py` (fpdf2), wired into `_run_single_lead` right after the approval gate (uses `edited_asset_text` when the human edited, else the original `asset_text` — neither is otherwise persisted). Output dir configurable via `Settings.EXPORTS_DIR` (default `exports/`, gitignored).
- [x] Fix `approvals` table never being written by the real pipeline — `run_approval_gate` (`src/approval/cli.py`) returned an `ApprovalResult` but never called `save_approval`/`init_approvals_table`, so the table only ever existed in tests. Added `_persist_approval()`, called from all three decision branches (approve/reject/edit). Found while building the dashboard's approval-history view, which would otherwise always render empty. New unit-conftest mock (`mock_persist_approval`) keeps existing isolated unit tests from writing to the real `data/leads.db` fallback path; two integration tests (`TestHappyPath`, `TestRejectionPath` in `test_full_pipeline.py`) now assert a real `approvals` row is written.
- [x] Visual dashboard for lead store — `src/dashboard/` (`data.py` query functions + `generator.py` self-contained HTML renderer, no new dependency) and a new `ai-outreach dashboard [--output PATH] [--open]` CLI command. Shows summary cards, the pipeline funnel, a campaign × status matrix, and approval/rejection history. `Settings.DASHBOARD_PATH` (default `dashboard.html`, gitignored) controls the default output location. 16 new tests (129 passing total).

---

## Known Issues

- [ ] OpenRouter account is out of credits for the default 4096-token request (HTTP 402, can only afford ~2659 tokens as of 2026-07-04). Top up at openrouter.ai/settings/credits before running a real batch — otherwise every research/asset-gen call will fail.

---

## Build Queue

_(empty)_

---

## Future (not yet scheduled)

_(empty)_

Everything codeable is done. What's left: top up OpenRouter credits and run the pipeline for real leads.
