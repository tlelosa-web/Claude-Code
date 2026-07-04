# Session Log — ai-outreach-agency

> Chronological record of durable context changes.

---

## 2026-06-28 — Project initialisation

- Created DCOE v3.0 scaffold: docs, src modules, tests, .claude config
- Wrote CLAUDE.md with project definition, inference routing, offline-first rule, human approval gate
- Wrote architecture.md documenting the 6-stage pipeline and data flow
- Wrote todo.md with initial task queue
- Pending decision: ADR-001 (lead store format)
- No application logic written yet — scaffold and docs only

- [2026-06-28 07:15 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:15 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:15 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)
- [2026-06-28 07:19 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:19 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:19 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)
- [2026-06-28 07:22 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:22 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:22 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)
- [2026-06-28 07:22 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:22 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:22 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)
- [2026-06-28 07:23 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:23 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:23 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)
- [2026-06-28 07:23 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:23 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:23 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)
- [2026-06-28 07:26 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:26 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:26 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)
- [2026-06-28 07:50 UTC] Imported 2 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:50 UTC] Imported 1 leads from leads.csv (0 duplicates skipped)
- [2026-06-28 07:50 UTC] Imported 0 leads from leads.csv (1 duplicates skipped)

## 2026-06-28 — Network integrations wired in

- `feat: scaffold email_draft module with Gmail stub` — composer, pipeline guard on approval decision, `GmailClient.create_draft` still a stub (fake draft id, no OAuth)
- `feat: config layer and main CLI runner` — `src/config.py` (Settings via python-dotenv), `src/main.py` CLI (import/list/run/run-all), `.env.example` + `.gitignore`
- `feat: wire OpenRouter API into research and asset_gen` — added `src/shared/openrouter_client.py`, real inference calls from `claude_summariser.py` and `asset_gen/generator.py`
- `feat: wire Apify scraper into research module` — `research/apify_client.py` now calls the real Apify website-content-crawler actor, with `OFFLINE_MODE` fixture and fallback on missing key or request failure
- `feat: lead status lifecycle tracking` — added `VALID_TRANSITIONS` state machine to `lead_import/db.py` (`new → researched → asset_ready → approved/rejected → drafted`), enforced across research/asset_gen/approval/email_draft pipelines

Remaining before end-to-end run: Gmail OAuth2 + real draft creation, `pyproject.toml`.

## 2026-07-04 — Closed remaining gaps

- **Security fix**: `.env.example` had a real OpenRouter API key pasted into it (working tree only, not committed — the committed version already had the `sk-or-replace-me` placeholder). Restored the placeholder; the real key remains only in gitignored `.env`.
- Added `pyproject.toml` — core deps (`requests`, `python-dotenv`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`), `pytest` as a dev extra, `ai-outreach` console script entry point.
- Implemented Gmail OAuth2 in `email_draft/gmail_client.py`: `InstalledAppFlow` against `credentials.json`, token cached/refreshed via `token.json` (gitignored), real `drafts().create()` call using the `gmail.compose` scope only. `OFFLINE_MODE` path unchanged (returns `draft_{timestamp}` stub) so existing tests keep passing offline.
- Added `TestGmailClient` cases to `tests/unit/test_email_draft.py` (offline stub id, and `FileNotFoundError` when credentials are missing in online mode). Full suite: 81 passed.
- Installed the new Google API packages into the local environment.

Pipeline is now code-complete for all 6 stages; only remaining setup step for a real end-to-end run is dropping a real `credentials.json` (Google Cloud OAuth client) in place and completing the one-time browser consent flow.

## 2026-07-04 — Gmail OAuth2 verified live

- Created a dedicated `ai-outreach-agency` GCP project (separate from `MIMS-ERP`), enabled the Gmail API, configured the OAuth consent screen (External audience), added `tlelosa@gmail.com` as a test user, and created a Desktop app OAuth client.
- Placed the downloaded `credentials.json` in the project root and ran the real (non-`OFFLINE_MODE`) `GmailClient.create_draft()` path for the first time.
- First attempt hit `Error 403: access_denied` — the signing-in account wasn't yet on the consent screen's test user list (required while the app is in "Testing" publish status). Fixed by adding `tlelosa@gmail.com` under Audience > Test users.
- Second attempt succeeded: completed the browser consent flow, `token.json` cached in the project root (gitignored), and a real Gmail draft was created (id `r6796278908385378625`) with the `gmail.compose` scope only. Confirms the OAuth2 integration works end-to-end, not just in `OFFLINE_MODE`.

## 2026-07-04 — Rate limiting added

- New `src/shared/rate_limiter.py` — token-bucket `RateLimiter` (configurable rate/period/capacity), thread-safe, sleeps only when the bucket is exhausted.
- Wired into all three external clients ahead of each real network call: `shared/openrouter_client.py` (60/min default), `research/apify_client.py` (30/min), `email_draft/gmail_client.py` (20/min). Each is overridable via `OPENROUTER_RATE_LIMIT_PER_MIN` / `APIFY_RATE_LIMIT_PER_MIN` / `GMAIL_RATE_LIMIT_PER_MIN`.
- Added `tests/unit/test_rate_limiter.py` (3 tests, fake monotonic clock — no real sleeping). Full suite: 84 passed, including the existing 429-retry test that mocks the shared `time.sleep`.
- Documented in `docs/api-patterns.md` under Common Patterns.

## 2026-07-04 — Live end-to-end pipeline test + bug fix

- **Bug found and fixed**: `src/main.py`'s `_run_single_lead` never passed `db_path` to `research_lead`/`run_asset_gen`/`run_approval_gate`/`run_email_draft`, so each fell back to `lead_import/db.py`'s `DEFAULT_DB_PATH` (`data/leads.db`) instead of `settings.DB_PATH` (`outreach.db`) — the DB the CLI actually reads leads from. That path has no `leads` table, so the first real `update_lead_status()` call would raise `sqlite3.OperationalError: no such table: leads`. Unit tests never caught this because `conftest.py`'s autouse fixture mocks `update_lead_status` out entirely. Fixed by threading `db_path=str(Path(settings.DB_PATH))` through all four calls.
- Added a regression test, `TestMainCLIRunCommand` in `tests/integration/test_full_pipeline.py`, that runs `main(["run", "--lead-id", ...])` through the real CLI entry point (not calling pipeline stages directly like the existing integration tests do) and asserts the real DB file ends with status `drafted`. This is the only test that would have caught the bug above.
- Ran a genuine live (non-`OFFLINE_MODE`) pipeline test: imported one lead (`Apify (Live Pipeline Smoke Test)`, a real crawl-friendly public site, contact email set to `tlelosa@gmail.com` so no real prospect was involved) → real Apify scrape → real OpenRouter summary + asset generation → human approval (genuinely reviewed by Tebello, not auto-approved) → real Gmail draft (`r2903087794821991922`) via the OAuth2 integration. Lead status progressed `new → researched → asset_ready → approved → drafted` correctly.
- **Found along the way**: the OpenRouter account is out of credits for the default 4096-token request (only ~2659 tokens affordable) — returns HTTP 402. Worked around for this one test by lowering `max_tokens` to 500; not a code bug, but blocks any real batch run until credits are topped up at openrouter.ai/settings/credits.
- Full suite: 85 passed.

## 2026-07-04 — Lead deduplication logic

- The existing dedup (SQLite `UNIQUE(company_name, email)` + `IntegrityError` catch in `cmd_import`) only caught byte-for-byte identical company names. Added `normalize_company_name()` in `lead_import/db.py` — lowercases, collapses whitespace, and strips a trailing legal suffix (Pty Ltd, (Pty) Ltd, CC, Inc, LLC, Corp) — so "Acme Engineering" and "ACME ENGINEERING (PTY) LTD" are recognized as the same company. `find_duplicate()` matches on email + normalized company name (both required, per the architecture doc's "company name + contact email" dedup spec) and is checked in `cmd_import` before every insert; the raw `UNIQUE` constraint stays as a backstop.
- TDD: added 6 failing tests first (`TestDeduplication` in `test_lead_import.py`, one CLI-level case in `test_main.py`), confirmed RED, then implemented GREEN. Full suite: 91 passed.
- **Bug found and fixed along the way**: `_log_session()` in `main.py` writes to the real `docs/session-log.md` unconditionally and was never mocked in tests, so every test run touching `cmd_import`/`_run_single_lead` appended "Imported N leads..." noise to this file (visible above as repeated entries with fake-looking timestamps — removed as cleanup). Added `tests/conftest.py` with an autouse fixture that mocks `src.main._log_session` for the whole suite.