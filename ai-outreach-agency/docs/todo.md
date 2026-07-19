# Task Queue — ai-outreach-agency

> Updated: 2026-07-19

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
- [x] **Planning**: Adapted `docs/specs/drafts/handoff-tracking.md` (OpenRouter-out-of-credits workaround: headless `claude -p` under Tebello's subscription, replacing `asset_gen`'s OpenRouter call) to this project's real migration/config conventions. Full build plan written to `docs/specs/handoff-tracking-build.md`. Key finding: `email_draft` has no existing OpenRouter call site to replace (only `asset_gen` and `research` do) — build scoped to `asset_gen` only pending Tebello's decision on the combined-call option (see Build Queue Step 22).
- [x] **Planning (ADR-004)**: Designed the second cost-elimination track — local Ollama (`qwen3:8b`) for the `research` summariser, replacing its OpenRouter call. `docs/decisions/ADR-004-local-ollama-research-inference.md` + `docs/specs/ollama-research-build.md`. Key findings: `nomic-embed-text`/embeddings scoped **out** (no consumer exists in the codebase — `ResearchResult` has no vector field, dedup is string-based); fail-loud on unreachable Ollama (no silent fallback to the also-broken OpenRouter); no schema change so no migration file; client placed in `research/` not `shared/` (single consumer, per `apify_client.py` precedent).
- [x] **Build Queue B (ADR-004) — local Ollama inference for `research`, shipped**: `src/research/ollama_client.py` (`call_ollama`, `OllamaError`/`OllamaUnreachableError`, module-level `RateLimiter` at `OLLAMA_RATE_LIMIT_PER_MIN`, default 120/min, no API key — local daemon), `OLLAMA_BASE_URL`/`OLLAMA_MODEL` added to `Settings`/`load_settings`/`.env.example`, and `research/claude_summariser.py`'s non-offline branch swapped from `call_openrouter` to `call_ollama` (the `OFFLINE_MODE` stub short-circuit is untouched, byte-for-byte). Fails loudly on an unreachable Ollama daemon — no silent fallback to OpenRouter, which is itself out of credits (see Known Issues). Connect-timeout/connection-refused and read-timeout are distinct exception types with distinct messages (`OllamaUnreachableError` "is it running?" vs. `OllamaError` "model may be slow/cold-loading") — a conflation between the two was caught and fixed in commit `338002f`. All 14 steps of the build queue done, Reviewer (Opus) approved, full suite **153 tests passing**. Commit range: ADR-004 planning through `338002f` on `feature/handoff-tracking` (branch shared with, but file-disjoint from, Build Queue A). `asset_gen` is untouched by this track and still calls OpenRouter — its own migration (headless Claude Code, ADR-003) is Build Queue A, separately scoped and not yet built.

---

## Known Issues

- [ ] OpenRouter account is out of credits for the default 4096-token request (HTTP 402, can only afford ~2659 tokens as of 2026-07-04). Top up at openrouter.ai/settings/credits before running a real batch — **but only still matters for `asset_gen`**. `research`'s half of this issue is **resolved**: Build Queue B landed (2026-07-19, ADR-004) and `research/claude_summariser.py` now runs on local Ollama (`qwen3:8b`), $0 marginal cost, independent of OpenRouter credit status — real (non-offline) research runs still need the Ollama daemon running + `qwen3:8b` pulled locally (see `docs/specs/ollama-research-build.md` §Prerequisites), which is a one-time local setup step, not a recurring cost. The remaining half — `asset_gen` — still calls OpenRouter and is blocked on this same HTTP 402 until either credits are topped up or Build Queue A (headless Claude Code, `docs/specs/handoff-tracking-build.md`, not yet built) lands.

---

## Build Queue A — Claude Code Headless Handoff (asset_gen)

Full detail, dependency ordering, and Reviewer-sign-off flags in
`docs/specs/handoff-tracking-build.md`. Branch: `feature/handoff-tracking`.
Steps flagged **[sign-off]** require Reviewer approval *before* the executor
starts, not just before merge. Touches `src/handoff/*`, `src/asset_gen/*`,
`src/approval/*`, `src/main.py` — no overlap with Build Queue B.

- [ ] 1. ADR-003 (`docs/decisions/ADR-003-headless-claude-handoff.md`) — architect
- [ ] 2. `src/handoff/__init__.py` package marker — executor
- [ ] 3. RED `tests/unit/test_handoff_schema.py` — tester
- [ ] 4. GREEN `src/handoff/schema.py` (`HandoffStatus`, `QualityFlag`, `HandoffLogEntry`) — executor
- [ ] 5. RED `tests/unit/test_handoff_db.py` — tester
- [ ] 6. GREEN `src/handoff/db.py` + `src/handoff/migrations.py` — executor
- [ ] 7. RED `tests/unit/test_config.py` (`HANDOFF_SETTINGS_PATH`) — tester
- [ ] 8. GREEN `src/config.py` edit — executor
- [ ] 9. RED `tests/unit/test_handoff_settings.py` — tester
- [ ] 10. GREEN `src/handoff/settings.py` — executor
- [ ] 11. `config/handoff_settings.json` + `.env.example` entry — executor
- [ ] 12. RED `tests/unit/test_handoff_scheduler.py` — tester
- [ ] 13. GREEN `src/handoff/scheduler.py` — executor
- [ ] 14. Port `src/handoff/templates/handoff_template.md` (real field names) — doc-writer
- [ ] 15. **[sign-off]** RED `tests/unit/test_handoff_runner.py` (mocked `subprocess.run`) — tester
- [ ] 16. **[sign-off]** GREEN `src/handoff/runner.py` — executor
- [ ] 17. `scripts/run_handoff.bat` (manual convenience only) + `.gitignore` (`handoff/`) — executor
- [ ] 18. **[sign-off]** RED `tests/unit/test_asset_gen.py` extended (call-site swap + block propagation) — tester
- [ ] 19. **[sign-off]** GREEN `src/asset_gen/generator.py` + `src/asset_gen/pipeline.py` — executor
- [ ] 20. RED `tests/unit/test_main.py` extended (`run-all` skip-on-block) — tester
- [ ] 21. GREEN `src/main.py` edit — executor
- [ ] 22. **Decision checkpoint (no code)** — confirm Option A (asset_gen only, email_draft untouched) with Tebello before Step 25 — planner/architect
- [ ] 23. RED `tests/unit/test_weekly_report.py` — tester
- [ ] 24. GREEN `scripts/weekly_report.py` — executor
- [ ] 25. **[sign-off]** RED `tests/unit/test_approval.py` extended (`quality_flag` capture) — tester
- [ ] 26. **[sign-off]** GREEN `src/approval/cli.py` edit — executor
- [ ] 27. RED `tests/integration/test_full_pipeline.py` extended — tester
- [ ] 28. GREEN — close any gaps Step 27 surfaces — executor
- [ ] 29. Acceptance-criteria verification pass (spec §11 checklist) — tester + reviewer
- [ ] 30. `docs/architecture.md` + `CLAUDE.md` pipeline/stack description update — doc-writer
- [ ] 31. `docs/api-patterns.md` — new "Claude Code Headless Invocation" section — doc-writer
- [ ] 32. Final `docs/todo.md` cleanup — doc-writer

---

## Build Queue B — Local Ollama Inference (research)

Second cost-elimination track. Full detail + prerequisites in
`docs/specs/ollama-research-build.md` / ADR-004. Branch: `feature/handoff-tracking`
(shared, independently orderable). Touches `src/research/*`, `src/config.py`,
`.env.example`, docs — **no overlap with Build Queue A**. No **[sign-off]** steps
(research sits upstream of the approval gate — see spec §6); Reviewer still
approves the new network client before merge as normal.

> **Prerequisites (Tebello only — manual, not executor steps):** install Ollama
> (`OllamaSetup.exe` from ollama.com/download, or `winget install Ollama.Ollama`
> after verifying the ID via `winget search ollama`), then `ollama pull qwen3:8b`
> (~5 GB). Do **not** pull `nomic-embed-text` (scoped out). Tests pass offline
> without any of this; prerequisites are only needed to run a real (non-offline)
> batch. See spec §Prerequisites.

- [x] 1. ADR-004 (`docs/decisions/ADR-004-local-ollama-research-inference.md`) — architect **[done]**
- [x] 2. RED `tests/unit/test_config.py` (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`) — tester
- [x] 3. GREEN `src/config.py` edit (Settings + load_settings) — executor
- [x] 4. RED `tests/unit/test_ollama_client.py` (mocked `requests.post`: success/parse, connection-refused → `OllamaUnreachableError`, timeout, non-200 → `OllamaError`, bad shape, rate-limiter called, no API key, clean-prose/`think:false`) — tester
- [x] 5. GREEN `src/research/ollama_client.py` (`call_ollama`, `OllamaError`, `OllamaUnreachableError`, `RateLimiter`, `OLLAMA_RATE_LIMIT_PER_MIN`) — executor
- [x] 6. RED `tests/unit/test_claude_summariser.py` (OFFLINE stub preserved; non-offline calls `call_ollama`; unreachable propagates, no OpenRouter fallback) — tester
- [x] 7. GREEN `src/research/claude_summariser.py` (swap `call_openrouter` → `call_ollama` in non-offline branch only) — executor
- [x] 8. `.env.example` entry (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`) — executor
- [x] 9. RED `tests/integration/test_full_pipeline.py` extended (research produces summary offline, zero real HTTP to 11434) — tester
- [x] 10. GREEN — close any gaps Step 9 surfaces — executor
- [x] 11. Acceptance-criteria verification pass (spec §8 checklist) — tester + reviewer. Also caught and fixed the read-timeout/connection-refused conflation (commit `338002f`) — read-timeout now raises `OllamaError`, not `OllamaUnreachableError`, so the two failure messages stay distinct.
- [x] 12. `docs/api-patterns.md` — new "Local Ollama Inference (research)" section — doc-writer
- [x] 13. `docs/architecture.md` + `CLAUDE.md` research-stage/stack update — doc-writer
- [x] 14. Final `docs/todo.md` update — doc-writer

**Build Queue B: complete.** All 14 steps done, Reviewer-approved, 153 tests passing. `research` now runs on local Ollama (`qwen3:8b`) at $0 marginal cost, independent of OpenRouter credit status.

---

## Future (not yet scheduled)

- [ ] **Option B** (deferred, needs its own spec if wanted): combine `asset_gen` + `email_draft` into a single per-lead headless handoff call (per the original draft's `handoff_template.md` ASSET+EMAIL design), adding fields to `AssetResult`/`DraftResult` and redesigning the approval-gate display to show the drafted email alongside the asset before human review. Not started — see `docs/specs/handoff-tracking-build.md` §5.
- [ ] **Embeddings / semantic features** (deferred, needs its own spec + ADR if wanted): `nomic-embed-text` and a vector store were in Tebello's draft pipeline diagram but have **no consumer** in the codebase today (no semantic search, RAG, or vector dedup — dedup is string-based). Scoped out of ADR-004. Revisit only when a real retrieval/similarity feature is specified.
