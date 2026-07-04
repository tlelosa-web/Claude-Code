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

---

## Known Issues

- [ ] OpenRouter account is out of credits for the default 4096-token request (HTTP 402, can only afford ~2659 tokens as of 2026-07-04). Top up at openrouter.ai/settings/credits before running a real batch — otherwise every research/asset-gen call will fail.

---

## Build Queue

_(empty)_

---

## Future (not yet scheduled)

- [ ] Implement Google Sheets sync (optional — not in current architecture)
- [ ] Build n8n workflow definitions
- [ ] Add lead deduplication logic
- [ ] Add campaign management (group leads by campaign, configure asset type per campaign)
- [ ] PDF export for generated assets
- [ ] Visual dashboard for lead store (deferred per ADR-001 — DB Browser for SQLite works as a stopgap; consider a lightweight web UI once pipeline runs end-to-end)
