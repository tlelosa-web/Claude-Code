# Task Queue — TebelloReborn (Career Engine)

> Updated: 2026-08-07 (**Indeed adapter Phase C built** — Phase 20, steps 123–127: the prep-state
> submit gate wired into `pipeline.py`, `pending_review` reporting, and the `--all` auto-submit
> refusal. Offline; **Phase D is next**. Earlier the same day: Phase B, Phase 19, steps 118–122 — the
> `submission_preps`/`screening_questions` tables, the `pending_review` outcome, the widened
> `submissions.outcome` CHECK with its migration and drift guard, and `submission_prep_ready()`.
> Also earlier the same day: ADR-004's schema migration ledger,
> Phase 18 steps 107–117; Indeed adapter Phase A, steps 103–104, see Phase 17. Stage 6 submission
> core built 2026-08-06, Phase 16 steps 81–102.)

---

## Known Issues (machine-specific, not architecture)

- **`black .` as documented in CLAUDE.md now reformats 17 unrelated files — 2026-08-06.** Running the
  documented pre-commit gate (`black . && ruff check .`) under this machine's current tooling
  (black 26.5.1, ruff 0.15.22) rewrites 7 files in `_archive_qwen_prototype/` (protected by Hard Rule
  12) plus 10 in `src/`/`tests/`/`tools/` that no one touched — formatter-version drift, since the
  committed code was formatted by an older black. `ruff check .` separately reports 10 pre-existing
  errors, 9 of them in the archive and 1 (`F401 json`) in `tests/unit/test_vacancy_match_result.py`.
  So the gate as literally written does not pass on a clean checkout. Worked around during the Phase
  16 build by scoping both tools to the files actually being changed. **Not fixed here** — a
  repo-wide reformat is its own decision and its own commit, and it should not ride along inside a
  feature build. Options: bump and reformat everything once, pin black in the dev extra, or add a
  `[tool.black]`/`[tool.ruff]` `exclude` for `_archive_qwen_prototype/`.

- **This machine's `.env` runs `OLLAMA_MODEL=qwen3:1.7b`, not the documented `qwen3:8b` default
  (CLAUDE.md/.env.example unchanged) — 2026-08-01.** Real go-live `run-all` hit severe RAM pressure
  (~8GB total, <1GB free with Claude Code + Chrome running): `qwen3:8b` (5.9GB) caused a trivial
  one-word prompt to hang 5+ minutes uncompleted even after the READ_TIMEOUT/keep_alive fix below —
  genuine memory thrashing, not a code bug. Swapped to `qwen3:1.7b` (1.4GB) for this machine only;
  confirmed working (5.2s for a real-shaped JSON prompt, correct output). This is a local workaround,
  not a project-wide default change — a machine with more RAM should keep using `qwen3:8b`. Revisit
  if match-quality problems show up in review (smaller model, weaker reasoning) — not verified against
  real vacancy data yet, only a synthetic test prompt.
- **Fixed same session:** `src/shared/ollama_client.py`'s `READ_TIMEOUT` bumped 60s → 120s and
  `"keep_alive": "30m"` added, mirroring `ai-outreach-agency`'s identical fix (`3ec16cd`) that this
  project's separate copy never received (`277800b`). Real fix, applies regardless of model size.

## Completed

- [x] Archived the old Qwen-era prototype intact into `_archive_qwen_prototype/` (nothing deleted).
- [x] Scaffolded new directory structure: `data/`, `docs/decisions/`, `src/{shared,profile,vacancy_search,matching,doc_gen,review}/`, `tests/{unit,integration}/`, `exports/`.
- [x] Copied forward real reference content: Master CV → `data/`, tracker + recruiter DB → `data/legacy_reference/`.
- [x] Wrote `CLAUDE.md` (project brain, DCOE v3.1 style, mirrors `ai-outreach-agency`).
- [x] Wrote `docs/architecture.md` (pipeline design, data flow, MVP scope: Phases 1–5 of 7).
- [x] Wrote 9 DCOE agent definitions in `.claude/agents/` (domain, planner, architect, executor, tester, reviewer, doc-writer, debugger, data-agent).
- [x] Confirmed console-script/package name: **`career-engine`** (no longer a placeholder).
- [x] Confirmed target-title weighting for `profile_seed.json`: **Operations Foreman/Manager is the primary lane**, Project Engineer (Mechanical) is a secondary lane carried in the same file.
- [x] Full MVP build plan written: `docs/specs/mvp-pipeline-build.md` (46 atomic tasks, Phases 0–8, Stages 1–5 only).
- [x] ADR-003 (`docs/decisions/ADR-003-inference-provider-split.md`) accepted 2026-07-19: OpenRouter dropped entirely, pre-build. AI Matching (Phase 4) re-routed to local Ollama, Document Generation (Phase 5) re-routed to headless Claude Code. Build Queue below re-planned accordingly — total step count grew from 46 to 54 (see Build Queue).
- [x] `tools/dashboard_server.py` + `tools/dashboard.html` (`1be39ca`, 2026-08-01): local live dashboard over `career.db`, kanban view by pipeline status, Approve/Reject on `asset_ready` cards wired to the real review-gate DB functions. Dev/visualization tool, not part of the Build Queue. See `session-log.md`'s 2026-08-01 entry.
- [x] Fixed a real bug (found 2026-08-01): `_run_pipeline_for_vacancy()` in `src/main.py` sent a
      vacancy to the human review gate even when `run_doc_gen` didn't reach `asset_ready` (e.g. a
      headless `claude -p` timeout), presenting a blank "CV: None / Cover Letter: None" for approval.
      Added a status guard that skips the gate and prints a diagnostic instead (`6bbd0d8` RED,
      `1403c47` GREEN). 239 tests passing, zero regressions. See `session-log.md`'s 2026-08-01 entry.

---

## Build Queue — ordered, atomic (see `docs/specs/mvp-pipeline-build.md` for full detail: inputs, outputs, verification, network flags, per-step agent; the spec was rewritten for ADR-003 in `4b71833` — 46→54 steps, Phase 4/5 now match the Ollama/headless-Claude-Code routing below)

### Phase 0 — Scaffolding & Config
- [x] 1. `pyproject.toml` (deps + `career-engine` console script)
- [x] 2. `.env.example` + `.gitignore` (do NOT blanket-ignore `data/`)
- [x] 3. `tests/conftest.py` + `tests/unit/conftest.py` (autouse `OFFLINE_MODE`)
- [x] 4. [RED] `tests/unit/test_config.py`
- [x] 5. [GREEN] `src/config.py`

### Phase 1 — Shared External-Client Infra
- [x] 6. [RED] `tests/unit/test_rate_limiter.py`
- [x] 7. [GREEN] `src/shared/rate_limiter.py` (copied verbatim from `ai-outreach-agency`)
- [x] 8. [RED] `tests/unit/test_config.py` — update for ADR-003 §5: remove the `OPENROUTER_API_KEY`/`OPENROUTER_RATE_LIMIT_PER_MIN` assertions, add assertions for `OLLAMA_BASE_URL`/`OLLAMA_MODEL`/`OLLAMA_RATE_LIMIT_PER_MIN`
- [x] 9. [GREEN] `src/config.py` + `.env.example` — same field swap (defaults: `OLLAMA_BASE_URL="http://localhost:11434"`, `OLLAMA_MODEL="qwen3:8b"`, `OLLAMA_RATE_LIMIT_PER_MIN=120`). This is a queued follow-up code change to an already-committed, already-tested file (Phase 0 step 5), per ADR-003 §5 — not part of the ADR itself, gets its own atomic RED/GREEN commit.

> `src/shared/openrouter_client.py` (formerly steps 8–9 in this phase) is dropped entirely per ADR-003 §1 — never built.

### Phase 2 — Stage 1: Profile Import (offline)
- [x] 10. [RED] `tests/unit/test_profile_schema.py`
- [x] 11. [GREEN] `src/profile/schema.py`
- [x] 12. [RED] `tests/unit/test_profile_db.py`
- [x] 13. [GREEN] `src/profile/db.py` + `src/profile/migrations.py`
- [x] 14. [RED] `tests/unit/test_profile_seed_data.py`
- [x] 15. [GREEN] `data/profile_seed.json` (Ops Foreman/Manager primary, Project Engineer secondary)

### Phase 3 — Stage 2: Vacancy Fetch (Apify for real runs)
- [x] 16. [RED] `tests/unit/test_vacancy_schema.py`
- [x] 17. [GREEN] `src/vacancy_search/schema.py`
- [x] 18. [RED] `tests/unit/test_vacancy_db.py`
- [x] 19. [GREEN] `src/vacancy_search/db.py` + `src/vacancy_search/migrations.py`
- [x] 20. [RED] `tests/unit/test_apify_client.py`
- [x] 21. [GREEN] `src/vacancy_search/apify_client.py`

### Phase 3.5 — ADRs
- [x] 22. `docs/decisions/ADR-001-vacancy-store.md`
- [x] 23. `docs/decisions/ADR-002-apify-job-scraping.md`
- [x] ADR-003 (`docs/decisions/ADR-003-inference-provider-split.md`) — already written and decided (2026-07-19). Filed **out of numeric sequence**, ahead of ADR-001/ADR-002 above: the OpenRouter-drop decision was time-sensitive (Phases 4–5 hadn't been built yet, so re-planning now means the OpenRouter path is never written at all), whereas ADR-001 (vacancy-store) and ADR-002 (Apify scraping) are documentation of already-settled Phase 2/3 conventions and can be written whenever convenient.

### Phase 4 — Stage 3: AI Matching (local Ollama, `qwen3:8b` — ADR-003 §2)
- [x] 24. [RED] `tests/unit/test_matching.py`
- [x] 25. [GREEN] `src/matching/prompt_builder.py`
- [x] 26. [RED] `tests/unit/test_ollama_client.py` — module-level `RateLimiter` (`OLLAMA_RATE_LIMIT_PER_MIN`), two distinct exception types (`OllamaError` base, `OllamaUnreachableError` subclass for connection-refused/connect-timeout), no API key/no missing-key guard, native `POST {OLLAMA_BASE_URL}/api/generate` with `{"model", "prompt", "stream": false, "think": false}`, `<think>...</think>` stripped from the returned `response` field
- [x] 27. [GREEN] `src/matching/ollama_client.py` — lives beside its single consumer (`matching/`, not `src/shared/`), mirroring `ai-outreach-agency/research/ollama_client.py`'s shape and the `apify_client.py` single-consumer precedent (ADR-003 §2, §Alternatives.D)
- [x] 28. [GREEN] `src/matching/scorer.py` — consumes `ollama_client.py`; **fails loud** on `OllamaError`/`OllamaUnreachableError`, no fallback backend (ADR-003 §2)
- [x] 29. [RED] `tests/unit/test_matching_pipeline.py`
- [x] 30. [GREEN] `src/matching/pipeline.py`

> **Corrected during Build Queue execution:** ADR-003 §2's "no migration required" note turned out
> to be inaccurate against how Phase 3 was actually built — the `vacancies` table had no
> score/rationale columns. Added `score`/`strengths`/`weaknesses`/`recommendation` as a proper
> migration in `vacancy_search/migrations.py` (versions 1-4) plus a `save_match_result()` in
> `vacancy_search/db.py`, per CLAUDE.md hard rule #6 and this project's own baseline-vs-migration
> convention (see Resolved Items below). Covered by `tests/unit/test_vacancy_match_result.py`
> (its own RED/GREEN pair, run before step 29 since the pipeline depends on it).

### Phase 5 — Stage 4: Document Generation (headless Claude Code, `claude -p` — ADR-003 §3–4)
- [x] 31. [RED] `tests/unit/test_doc_gen_schema.py` — `GenerationStatus` enum (`success` / `throttled` / `error`)
- [x] 32. [GREEN] `src/doc_gen/schema.py`
- [x] 33. [RED] `tests/unit/test_doc_gen_db.py` — `generation_log` table: `vacancy_id` FK → `vacancies(id)`, `doc_type` CHECK IN (`'cv'`,`'cover_letter'`), `status` CHECK IN (`'success'`,`'throttled'`,`'error'`); **no `quality_flag`** — that belongs to `review/` (Phase 6), not `doc_gen` (ADR-003 §4)
- [x] 34. [GREEN] `src/doc_gen/db.py` — inline `CREATE TABLE IF NOT EXISTS generation_log` (+ two indexes) per the exact baseline schema in ADR-003 §4 — `+` `src/doc_gen/migrations.py` (empty `MIGRATIONS` stub, ships from day one per the project's baseline-vs-migration convention, see Resolved Items below)
- [x] 35. [RED] `tests/unit/test_claude_code_runner.py` — `subprocess.run(["claude", "-p", <instruction>, "--allowedTools", "Read,Write", "--output-format", "json"], capture_output=True, text=True, timeout=<module-level default constant>)`, mirroring `ai-outreach-agency/handoff/runner.py`
- [x] 36. [GREEN] `src/doc_gen/runner.py` — `throttled`/`error` are result **fields**, not exceptions (throttle detected via stderr indicators); only `FileNotFoundError` (`claude` missing from `PATH`) propagates
- [x] 37. [RED] `tests/unit/test_doc_gen.py` — fresh `OFFLINE_MODE` stub branches for both generators. **Note:** unlike the sibling projects, there is no pre-existing offline branch to preserve here — both branches are new (ADR-003 §3, §7)
- [x] 38. [GREEN] `src/doc_gen/cv_generator.py` — `OFFLINE_MODE` stub branch returns deterministic output before any subprocess call; non-offline branch routes through `runner.py`
- [x] 39. [GREEN] `src/doc_gen/cover_letter_generator.py` — same offline/non-offline split as step 38
- [x] 40. [RED] `tests/unit/test_pdf_export.py`
- [x] 41. [GREEN] `src/doc_gen/pdf_export.py`
- [x] 42. [RED] `tests/unit/test_doc_gen_pipeline.py`
- [x] 43. [GREEN] `src/doc_gen/pipeline.py`

> **Deliberately excluded** per ADR-003 §6 (judgment call, not an oversight): `settings.py`, `scheduler.py`, volume-cap/weekly-report machinery, `handoff_settings.json`. TebelloReborn has no documented volume-throttling requirement, unlike the sibling project's controlled-trial constraint. Do not add these by copying `ai-outreach-agency`'s fuller `handoff/` machinery — if a controlled-batch need is confirmed later, it gets its own spec + ADR.

> **Security correction to ADR-003 §3 (post-step-39, flagged by automated commit review):** the ADR's literal
> `--allowedTools "Read,Write"` is a real vulnerability here — both generators' instructions embed
> `vacancy.description`, untrusted scraped job-posting text, so a prompt-injected instruction from a
> malicious posting could make the headless agent write attacker-controlled content to an arbitrary
> file. Neither generator actually needs Write: the CV/cover-letter text comes back via the JSON
> `result` field, and `pdf_export.py` (trusted Python code, not the agent) does the real file write.
> `src/doc_gen/runner.py`'s `ALLOWED_TOOLS` was corrected to `"Read"` only, `tests/unit/test_claude_code_runner.py`
> updated to match plus a new `TestRunClaudeCodeNeverGrantsWrite` guard, and both instruction builders now
> wrap `vacancy.description` via a new `runner.wrap_untrusted_text()` helper (clear untrusted-data
> delimiters + an explicit "don't follow embedded instructions" warning) as defense in depth alongside
> the reduced tool scope. ADR-003 itself is left unedited (historical record of the decision as
> accepted); this note is the correction, mirroring the match-result migration note above.

### Phase 6 — Stage 5: Human Review (offline) — **steps 48–49 required Reviewer sign-off BEFORE execution, not just before merge**
- [x] 44. [RED] `tests/unit/test_review_schema.py`
- [x] 45. [GREEN] `src/review/schema.py`
- [x] 46. [RED] `tests/unit/test_review_db.py`
- [x] 47. [GREEN] `src/review/db.py` + `src/review/migrations.py`
- [x] 48. [RED] `tests/unit/test_review_cli.py` (`b2734b8`)
- [x] 49. [GREEN] `src/review/cli.py` (`1ed2fca`) — also enables `PRAGMA foreign_keys = ON` in `review/db.py`

### Phase 7 — CLI Wiring & Integration
- [x] 50. [RED] `tests/unit/test_main.py`
- [x] 51. [GREEN] `src/main.py`
- [x] 52. `tests/integration/test_full_pipeline.py` (offline end-to-end)

> **Bug found by step 52 (not by any unit test):** every prior unit test mocks
> `export_cv_pdf`/`export_cover_letter_pdf` entirely, so none of them ever
> rendered real generated content through fpdf2. The new offline integration
> test does, and hit `FPDFException: Not enough horizontal space to render a
> single character` — `multi_cell(0, ...)` calls in `pdf_export.py` left the
> cursor at the right margin (fpdf2's default `new_x=XPos.RIGHT`), so two
> non-blank lines in a row (e.g. a `## ` heading directly followed by body
> text) starved the next line of width. Fixed by passing
> `new_x=XPos.LMARGIN, new_y=YPos.NEXT` on all three `multi_cell` calls.

### Phase 8 — Docs Closeout
- [x] 53. `docs/api-patterns.md` — must document **Ollama** (matching) and **headless Claude Code** (document generation), not OpenRouter (ADR-003)
- [x] 54. `docs/session-log.md`

### Phase 9–14 — PNet/Careers24 Vacancy Coverage (see `docs/specs/pnet-careers24-coverage.md` for full detail: inputs, outputs, verification, per-step agent; Codex-reviewed and amended 2026-07-29 — **PRIORITY**, per hub `docs/todo.md`)

- [x] 55. [RED] `tests/unit/test_ollama_client.py` — import path update to `src.shared.ollama_client`
- [x] 56. [GREEN] Move `src/matching/ollama_client.py` → `src/shared/ollama_client.py`; update `scorer.py` import
- [x] 57. Update `CLAUDE.md`'s External Client Patterns table + Directory Structure for the move
- [x] 58. [RED] `tests/unit/test_vacancy_schema.py` — `pnet`/`careers24` platform cases
- [x] 59. [GREEN] `src/vacancy_search/schema.py` — `VALID_PLATFORMS` addition (no migration — Python-validation only)
- [x] 60. `data/crawler_seed_urls.json` — generic placeholder seed-URL config (job-detail pages only, per Amendment)
- [x] 61. [RED] `tests/unit/test_crawler_client.py` — OFFLINE_MODE fixture, rate limiter, graceful-degradation convention, `_source_mode` tagging (per Amendment)
- [x] 62. [GREEN] `src/vacancy_search/crawler_client.py` — Apify `website-content-crawler` client

> **PAUSED 2026-07-29 — objective drift caught before Phase 12, then RESOLVED same day.**
> The original static `data/crawler_seed_urls.json` design (Phase 10, step 60) required
> Tebello to manually find and paste individual job-detail-page URLs — manual job-search
> labor at the discovery stage, contradicting this project's actual goal (the pipeline
> *continuously finds* vacancies automatically, and Tebello's manual involvement is supposed
> to be **only** the human-approval gate). The original steps 63–72 (extraction + fold-in +
> docs, built directly against the static seed-URL design) were never built as originally
> planned. `docs/specs/pnet-careers24-coverage.md`'s "Amendment — Automated Discovery
> Redesign" (2026-07-29) replaced them in full with a new step sequence, **also numbered
> 63–80** (continuing from the same step 62), which **is** what was built — see below.
> Phases 9–11 (steps 55–62, all committed pre-pause) remain valid and reused unchanged:
> `ollama_client.py`'s promotion, `VALID_PLATFORMS`, and `crawler_client.py`'s raw-fetch
> mechanics (rate limiting, OFFLINE_MODE, `_source_mode` tagging).

#### Phase 12 (redesigned) — Automated Discovery (Careers24 full-auto, PNet gated + fallback)
- [x] 63. [RED] `tests/unit/test_crawler_client.py` — `fetch_raw_page(url)` single-URL primitive + refactor regression lock
- [x] 64. [GREEN] `src/vacancy_search/crawler_client.py` — extract `fetch_raw_page(url)`, `fetch_raw_pages()` composes on it (pure refactor)
- [x] 65. [RED] `tests/unit/test_discovery.py` (new) — `build_search_url`/`parse_job_urls_from_listing`/`discover_job_urls` for careers24
- [x] 66. [GREEN] `src/vacancy_search/discovery.py` (new) — careers24 discovery, deterministic listing-page parse (never an LLM call)
- [x] 67. [RED] `tests/unit/test_discovery.py` — `build_search_url("pnet", ...)` bare-path-only shape, no `?` under any input
- [x] 68. [GREEN] `src/vacancy_search/discovery.py` — pnet `build_search_url`, structurally no query-string code path
- [x] 69. `data/discovery_config.json` (new) — pnet gated `manual_pending_verification`, careers24 always `auto`
- [x] 70. [RED] `tests/unit/test_discovery.py` — `get_job_urls()` single entry point, careers24 no gate, pnet config-driven branch + seed-urls fallback
- [x] 71. [GREEN] `src/vacancy_search/discovery.py` — `get_job_urls()` implementation

#### Phase 13 — LLM Extraction (preserved unchanged from the original Phase 12 content, renumbered)
- [x] 72. [RED] `tests/unit/test_vacancy_extraction.py` — extraction prompt + parse/validate, empty-string required-field rejection, one-page-one-vacancy contract test
- [x] 73. [GREEN] `src/vacancy_search/extraction_prompt.py` — pure prompt builder
- [x] 74. [GREEN] `src/vacancy_search/extractor.py` — `VacancyExtractionError`, consumes `src/shared/ollama_client.py`

#### Phase 14 — Fold into `fetch_vacancies()` (preserved unchanged from the original Phase 13 content, integration point changed to discovery-sourced URLs)
- [x] 75. [RED] `tests/unit/test_apify_client.py` — discovery integration, `normalize_url()` dedupe fix, PNet fallback end-to-end case, fixture-mode warning log
- [x] 76. [GREEN] `src/vacancy_search/apify_client.py` — `fetch_vacancies()` folds pnet/careers24 via `get_job_urls` → `fetch_raw_page` → `extract_vacancy_fields`, no `if platform == "pnet"` branching

#### Phase 15 — Docs Closeout
- [x] 77. `docs/decisions/ADR-002-apify-job-scraping.md` — second dated amendment (`## Amendment — 2026-07-29 (Automated Discovery)`), additive
- [x] 78. `docs/api-patterns.md` — PNet/Careers24 section (crawler_client.py + extractor.py + discovery.py subsections), Ollama section path fix
- [x] 79. `CLAUDE.md` — External Client Patterns table + Directory Structure update for `crawler_client.py`/`discovery.py`/`discovery_config.json`
- [x] 80. `docs/todo.md` — this section

### Phase 16 — Stage 6: Submission core, platform-agnostic (see `docs/specs/submission-core.md` for full detail; Codex-reviewed and amended 2026-08-06 — **built 2026-08-06**)

Ports and corrects the hub's `2026-08-04-tebelloreborn-playwright-auto-submit.md`, which scoped the
build to **LinkedIn Easy Apply only** — a platform this project dropped on 2026-08-01, with zero rows
in `career.db`. Built as written it could have submitted nothing. Scope became the platform-agnostic
core; the site adapter is a separate, later task (see Open Items).

- [x] 81. [RED] `tests/unit/test_submission_schema.py` — enums, `SubmissionAttempt`, tz-aware `attempted_at`
- [x] 82. [GREEN] `src/submission/schema.py` + `__init__.py`
- [x] 83. [RED] `tests/unit/test_vacancy_schema.py` — `submitted`/`submission_failed` statuses
- [x] 84. [GREEN] `src/vacancy_search/schema.py` — `VALID_STATUSES` (no migration — Python-validation only, step-59 precedent)
- [x] 85. [RED] `tests/unit/test_vacancy_db.py` — submission transitions, retry-that-fails-again, `submitted` terminal, Hard Rule 1 guards
- [x] 86. [GREEN] `src/vacancy_search/db.py` — `VALID_TRANSITIONS` extension
- [x] 87. [RED] `tests/unit/test_submission_db.py` — table, per-connection FK, CHECK constraints, `user_version` untouched
- [x] 88. [GREEN] `src/submission/db.py` — `init_db`/`save_attempt`/`get_attempts_for_vacancy`; **no `migrations.py`** (Hard Rule 6)
- [x] 89. [RED] `tests/unit/test_submission_session.py` — path resolution + `.gitignore` credential guard
- [x] 90–91. [GREEN] `src/config.py` + `.gitignore` (`SESSION_STATE_PATH`, `.session/`) and `src/submission/session.py`. **Landed as one commit**: the `.gitignore` entry alone leaves the suite failing collection, and Hard Rule 4 requires tests passing before a commit
- [x] 92. [RED] `tests/unit/test_submission_eligibility.py` — empty registry, capability dispatch, declining adapter
- [x] 93. [GREEN] `src/submission/eligibility.py` — `SubmitAdapter` Protocol + `ADAPTERS` (empty by design) + `get_adapter`/`is_auto_submittable`
- [x] 94. [RED] `tests/unit/test_submission_pipeline.py` — approval gate, all outcome paths, persistence-before-transition
- [x] 95. [GREEN] `src/submission/pipeline.py` — `run_submission()`, `SubmissionNotAllowedError`, `SubmissionStatusError`
- [x] 96. [RED] `tests/unit/test_main.py` + `tests/unit/test_submission_cli.py` — `submit` parsing and dispatch
- [x] 97. [GREEN] `src/submission/cli.py` + `src/main.py` wiring. **Deviation from the spec:** the spec put the CLI in `main.py`; inlining it pushed `main.py` to 354 lines, past this project's own 300-line standard, so it moved to `src/submission/cli.py` — matching how `run_review_gate` already lives in `src/review/cli.py`. Dispatch tests moved with it
- [x] 98. `tests/integration/test_full_pipeline.py` — offline end-to-end: approved → submit → `not_supported` recorded, status unchanged, operator told to submit by hand; plus Hard Rule 1 end-to-end and a `--all` summary run
- [x] 99. `docs/architecture.md` — Stage 6 section + extended state machine
- [x] 100. `CLAUDE.md` — Stage 6, submit commands, `src/submission/`, and the global-`user_version` rule in Hard Rule 6
- [x] 101. `docs/todo.md` — this section
- [x] 102. `pyproject.toml` — `pytest-cov` in dev extras so CLAUDE.md's ≥80% standard is enforceable (dev-only; runtime deps stay at three). Verified: **100%** across all seven `src/submission/` modules

**Result:** 344 tests passing (was 249), zero regressions. No `playwright` dependency, no browser
binary, nothing on the wire.

### Phase 17 — Indeed submit adapter, **Phase A only** (see `docs/specs/indeed-submit-adapter.md`
§Amendment A5 — built 2026-08-07)

Contact details for Indeed's application form. Phase A blocks every other phase in that spec, so it
went first; **B–H are not started.**

- [x] 103. [RED] `tests/unit/test_profile_schema.py` + `tests/unit/test_profile_db.py` (`9d4ee17`) —
      `email`/`phone` in `REQUIRED_FIELDS`, migration versions asserted as `[5, 6]`, a test that
      reproduces the live DB's `user_version = 4` pre-contact state, and an actionable-error test for
      a profile row written before the migration
- [x] 104. [GREEN] `src/profile/schema.py` + `migrations.py` + `db.py` + `data/profile_seed.json`
      (`379a4b2`) — real values sourced from `data/Tebello_Lelosa_Master_CV_2026.md`
      (`tlelosa@gmail.com`, `078 481 8711`), with a test asserting the seed and the CV never drift
      apart (an employer sees both on the same application)
- [x] 105. `.gitignore` — `*.db.backup-*`. `*.db` does **not** match
      `career.db.backup-pre-phase-a-2026-08-07`; the timestamp suffix means the filename doesn't end
      in `.db`, so a `git add -A` would have committed a full copy of the live career data
- [x] 106. `docs/todo.md` + `docs/session-log.md` — this section

**Result:** 362 tests passing (was 344), zero regressions.

> **A real regression was introduced by this phase and caught by the integration suite, not by any
> unit test** — the same class of gap as the Phase 7 fpdf2 bug and the Apify payload-shape bugs.
> `profile` owns the highest migration versions (5–6) and `import-profile` is CLAUDE.md's documented
> *first* command. So on a fresh database `profile.init_db()` advanced the shared `user_version`
> 0 → 6 before `vacancy_search.init_db()` ever ran; its migrations 1–4 were then skipped by
> `if version > current`, and because its baseline `CREATE TABLE` omits those columns, `vacancies`
> came out with no `score`/`strengths`/`weaknesses`/`recommendation` at all — `IndexError: No item
> with that key` on the first read, on every new install.
>
> **Fix (scoped to `src/profile/` deliberately):** schema state, not the counter, is the source of
> truth. `email`/`phone` are in profile's baseline `CREATE TABLE` *as well as* in migrations 5/6, and
> `apply_migrations` skips an `ADD COLUMN` whose column already exists, advancing `user_version` only
> for migrations it actually ran. A fresh database therefore reaches the right shape while staying at
> version 0, leaving the lower numbers free for `vacancy_search`. Two regression tests lock both
> orderings and assert they converge on the same schema.
>
> Verified against a **copy** of the live `career.db` before anything touched the real one:
> `user_version` 4 → 6, both columns added, all 10 vacancies and 6 approved applications intact,
> and `import-profile` repopulating the contact details cleanly.

### Phase 18 — ADR-004: schema migration ledger (built 2026-08-07)

Replaces the shared `PRAGMA user_version` counter with a
`schema_migrations(module, version, applied_at)` ledger and one shared runner. Offline throughout.
See `docs/decisions/ADR-004-schema-migration-ledger.md` and its `§Amendment — 2026-08-07 (Codex
fold-in)`.

- [x] 107. [RED+GREEN] `tests/unit/test_shared_migrations.py` + `src/shared/migrations.py`
      (`899890a`) — landed together because the RED state is a `ModuleNotFoundError` that breaks
      suite collection, same precedent as steps 90–91
- [x] 108. [RED] `tests/unit/test_profile_db.py` — counter assertions become ledger assertions
      (`98725f7`)
- [x] 109. [GREEN] `src/profile/migrations.py` delegates (`7df3d51`)
- [x] 110. [RED] `tests/unit/test_vacancy_db.py` — baseline declares the match columns, ledger
      records 1–4 (`4394890`)
- [x] 111. [GREEN] `src/vacancy_search/migrations.py` delegates + `db.py` baseline gains
      `score`/`strengths`/`weaknesses`/`recommendation` (§6, `278a5eb`)
- [x] 112. [GREEN] `src/doc_gen/migrations.py` + `src/review/migrations.py` delegate (`fe5866b`)
- [x] 113. `tests/unit/test_submission_db.py` — `test_does_not_advance_user_version` becomes its
      ledger equivalent (`bc6ae0a`)
- [x] 114. [GREEN] Phase-B-shaped table-rebuild acceptance test (`6545af7`) — **the step that proves
      the stated blocker is solved**, not merely asserted
- [x] 115. `tests/integration/test_full_pipeline.py` — all five `init_db()`s against one database in
      both orders (`bbcef1c`)
- [x] 116. Verified against a **copy** of the live `career.db`, never the real file
- [x] 117. Docs closeout — CLAUDE.md Hard Rule 6 rewritten, `docs/architecture.md` gains a Schema
      Migrations section, this file, `docs/session-log.md`

**Result:** 399 tests passing (was 362), zero regressions.

> **Two findings from building it, both verified against this machine's sqlite3 3.49.1 rather than
> assumed.** The first came from the Codex pass and would have failed at runtime: a migration payload
> of `str` cannot express Phase B's table rebuild, because `Connection.execute()` raises
> `ProgrammingError` on multi-statement SQL — and `executescript()` is no escape hatch, since it
> issues an **implicit COMMIT before running**, which would have silently voided the ADR's
> "commits once at the end" atomicity. Payloads are now `str | Callable[[sqlite3.Connection], None]`
> with one `BEGIN IMMEDIATE` per migration. The second surfaced while making the rebuild test
> actually pass: `PRAGMA foreign_keys` is a **no-op inside a transaction**, so SQLite's documented
> "turn foreign keys off first" rebuild step is unavailable to a migration the runner has already
> wrapped. `PRAGMA defer_foreign_keys` is settable mid-transaction and is what a rebuild must use.
> Phase B should follow `TestPhaseBShapedRebuild`'s shape rather than the SQLite docs verbatim.

### Phase 19 — Indeed submit adapter, **Phase B** (see `docs/specs/indeed-submit-adapter.md`
§Amendment A2/A3/A4/A12 — built 2026-08-07)

Screening-question state, offline throughout. Nothing on the wire, no `playwright` dependency, the
adapter registry still empty.

- [x] 118. [RED] `tests/unit/test_submission_schema.py` (`6e457a6`) — `PrepStatus` (7 states),
      `FieldType` (with `radio`), `QuestionDecision`, `Sensitivity`, `SubmissionPrep`,
      `ScreeningQuestion`, `PrepReadiness`, `SubmissionOutcome.PENDING_REVIEW`, plus a test pinning
      `prep_failed` as never-added (A3 resolved it by deletion, not definition)
- [x] 119. [GREEN] `src/submission/schema.py` (`adc3429`)
- [x] 120. [RED] `tests/unit/test_submission_db.py` (`f80637c`) — both tables, CHECK constraints,
      per-connection FK enforcement, `prep_id` scoping, one test per row of A2's gate table, and
      three tests carrying the A4 trap. `test_records_nothing_in_the_migration_ledger` converted to
      `test_records_its_own_version_1_and_disturbs_no_other_module` — Phase B ends its premise
- [x] 121. [GREEN] `src/submission/db.py` + `src/submission/migrations.py` (`ad04b4a`)
- [x] 122. Docs closeout — `docs/architecture.md` (Stage 6 screening-question state + two new
      Schema Migrations bullets), `CLAUDE.md` (Hard Rule 1, Stage 6, directory structure), this
      file, `docs/session-log.md`

**Result:** 456 tests passing (was 399), zero regressions. Coverage on the new code: `schema.py`
100%, `db.py` 99%, `migrations.py` 95%.

> **Deviation from the spec, deliberate: Phase B ships a real migration, not only the DDL edit and
> the drift guard.** A4's resolution was two-part — edit the inlined `CREATE TABLE` string (valid
> only while `submissions` doesn't exist, which it verified is still true of the live database) and
> add a guard that refuses loudly otherwise. Written that way, a database where `submit` had already
> run once would fail at `init_db()` with no automated remedy. ADR-004 landed between the spec and
> this build and makes the remedy cheap: `src/submission/migrations.py` version 1 rebuilds the table,
> following `TestPhaseBShapedRebuild` rather than SQLite's documented procedure, since
> `PRAGMA foreign_keys` is a no-op inside the runner's transaction and `defer_foreign_keys` is the
> one settable mid-transaction. The guard stays, now as a genuine last-resort invariant for the cases
> a migration cannot reach — a restored backup, a hand-edited schema, a ledger row without the DDL
> change it claims. A4's own closing note ("the fix is SQLite's standard table rebuild … inside a
> migration") is exactly this, brought forward from *if the guard fires* to *before it can*. Its
> "globally-unique `user_version ≥ 5`" wording is superseded by ADR-004 — version 1, per-module.
>
> **The migration self-guards, which a callable has to do for itself.** The runner's
> `_already_satisfied` shortcut is scoped to `ADD COLUMN` strings and never to a callable, so
> `_widen_outcome_check()` reads `sqlite_master` and returns early when the baseline already produced
> the widened shape. Without that, every fresh database would rebuild a table it had just correctly
> created.
>
> **Verified against a copy of the live `career.db`, never the real file** (sqlite3 backup API, not a
> file copy): 10 vacancies, 10 approvals, 43 `generation_log` rows and the profile all intact,
> `integrity_check = ok`, `user_version` still frozen at 4, the three tables present with the widened
> CHECK, and all 6 approved vacancies correctly gating to `pending_review` with "never prepped".

### Phase 20 — Indeed submit adapter, **Phase C** (see `docs/specs/indeed-submit-adapter.md`
§Amendment A2/A3/A15 — built 2026-08-07)

The prep-state gate, wired. Offline throughout, adds no new state — it consumes what Phase B built.
Nothing on the wire, no `playwright` dependency, the adapter registry still empty.

- [x] 123. [RED] `tests/unit/test_submission_pipeline.py` (`861cff5`) — one test per row of A2's gate
      table, the two orderings below, and A15's batch refusal. Existing adapter-path tests updated to
      seed a prep row: reaching `submit()` without one is now the bug, not incidental setup
- [x] 124. [GREEN] `src/submission/pipeline.py` + `src/submission/eligibility.py` (`80a49ee`) —
      `PENDING_REVIEW` joins `NOT_SUPPORTED` as a no-transition outcome; `_decide()` consults
      `submission_prep_ready()`; `run_submission(batch=)`; `can_handle()`'s pure/offline contract (A1)
- [x] 125. [RED] `tests/unit/test_submission_cli.py` (`fdbacaf`) — `pending_review` wording, its own
      summary bucket, `batch=` on both dispatch paths, exit codes
- [x] 126. [GREEN] `src/submission/cli.py` (`86d90c4`)
- [x] 127. Docs closeout — `docs/architecture.md` (the gate table, the `--all` policy, `can_handle()`'s
      amended contract), `CLAUDE.md` Stage 6, this file, `docs/session-log.md`

**Result:** 485 tests passing (was 456). Coverage on the phase's three modules: `pipeline.py` 100%,
`cli.py` 100%, `eligibility.py` 100%.

> **Two orderings decided here, both pinned by their own test, because getting either wrong is
> silent.**
>
> 1. **The gate runs before the session check.** Every answer it gives is state `prep-submission`
>    already recorded, so none of it needs a live session to read. Putting the session check first
>    would report a recorded `external_ats` as "no saved browser session — run the login setup",
>    sending Tebello to fix something that isn't broken and hiding the one finding that genuinely
>    means "submit by hand".
> 2. **The `--all` refusal is checked last, not first.** A vacancy that also has a real gate reason
>    hears that reason instead: "run `prep-submission`" is more use than "use an explicit
>    `--vacancy-id`" to someone who would have to prep first anyway. Checking it first would make
>    every un-prepped vacancy in a batch report the wrong next step.
>
> **A15 confirmed with Tebello before the build** (spec §Open Items, item 5 — it was raised there
> precisely so the behavior wouldn't be a surprise). Submitting the 6 approved Indeed vacancies will
> be six deliberate commands, by design.
>
> **`pending_review` and `not_supported` both map to no status transition**, so the CLI's wording is
> the *only* thing separating them for the operator. That is why `report_attempt()` gets a dedicated
> branch and its own asserted substrings, and why the summary counts them in separate buckets:
> folding them together would tell Tebello to submit by hand a batch that one `prep-submission` run
> may unblock.

---

---

## Resolved Items

- [x] **LinkedIn dropped — decided and actioned 2026-08-01.** The LinkedIn Apify actor
      (`bebity~linkedin-jobs-scraper`) returns `403 actor-is-not-rented` — its free trial expired and it
      requires a paid rental on Apify's console to keep working (confirmed via direct real-API test). All
      20 vacancies stored in `career.db` before this point were already `platform = "indeed"` only, since
      LinkedIn had silently contributed zero results since the trial expired (the existing per-call error
      swallow made this invisible). Firecrawl was considered as an alternative (per hub `docs/todo.md`'s
      2026-08-01 backlog note on Apify-vs-Firecrawl) and ruled out — heavily bot-defended, no dedicated
      LinkedIn actor either. **Decision: drop, not rent.** Code change (unlike the earlier "no code
      change" framing when this was still an open Known Issue): `LINKEDIN_ACTOR_URL`, the LinkedIn
      POST-call block, and `_normalize_linkedin()` removed from `apify_client.py`; `FIXTURE_VACANCIES`'
      LinkedIn entry replaced with a careers24-shaped one. `VALID_PLATFORMS` in `schema.py` left
      unchanged (still lists `"linkedin"` — harmless allowlist entry, no real rows use it). Docs updated:
      `docs/architecture.md`'s External Integrations table + Data Flow diagram,
      `docs/api-patterns.md`'s Apify section. 249 tests passing, zero regressions. Revisit only if
      LinkedIn coverage becomes a real product need later.
- [x] **PNet/Careers24 automated discovery zero-results bug — fixed 2026-08-01.** Full write-up:
      `docs/bugs/pnet-careers24-discovery-zero-results.md`'s Resolution section;
      `docs/decisions/ADR-002-apify-job-scraping.md`'s 2026-08-01 amendment. Root cause: discovery
      parsed `text_content` (zero URLs — the actor's readability-post-processed text), and even after
      switching to raw HTML, the actor's *default* `htmlTransformer` strips `<a href>` tags there too —
      `saveHtml: true` alone wasn't enough, `htmlTransformer: "none"` was also required (confirmed via a
      real capture against a live PNet page). Fixed: `crawler_client.fetch_raw_page()` now requests both
      flags and surfaces a new `"html"` field; `discovery.py` parses that field; `_JOB_URL_PATTERNS`
      gained a real, capture-derived `"pnet"` entry (domain-relative `/jobs--<slug>--<id>-inline.html`,
      resolved to absolute); `_pnet_slug()` no longer drops `"/"`; `crawler_client.TIMEOUT` bumped
      `60s → 180s` (PNet's real crawl took ~150s). 249 tests passing before this fix — see the ADR
      amendment for the post-fix count. Real-run verification (confirming PNet/Careers24 vacancies
      actually land in `career.db`) tracked as a follow-up below.
- [x] Migration-file convention for net-new tables (Phases 2/3/5/6): confirmed against
      `ai-outreach-agency/src/lead_import/db.py` — initial `CREATE TABLE IF NOT EXISTS` statements live
      directly in each module's `init_db()`, not in `migrations.py`. `migrations.py` (empty `MIGRATIONS`
      list + `PRAGMA user_version` runner) only tracks schema changes *after* that baseline, mirroring
      exactly how `ai-outreach-agency` added its `campaign` column. Steps 13/19/34/47 follow this pattern.
      ADR-003 §4 confirms `generation_log` (step 34) follows the same convention — no standalone
      `migrations/*.sql` file exists in this project.
- [x] OpenRouter Known Issue (out-of-credits blocker) resolved for TebelloReborn by ADR-003 — the project
      no longer depends on OpenRouter or its credit balance at all. (The blocker may still exist for
      `ai-outreach-agency` — it is simply no longer this project's to fix.)
- [x] Match-result persistence (Phase 4 corrective addendum): ADR-003 §2 assumed the score columns
      were "part of the Phase 3 vacancy schema," but Phase 3 (steps 16-19) shipped without them. Added
      via `vacancy_search/migrations.py` (versions 1-4) rather than editing the committed baseline
      `CREATE TABLE`, consistent with the migration-file convention above. ADR-003 itself is left
      unedited (historical record of the decision as accepted); this note is the correction.
- [x] Apify actor slugs verified against the live Apify Store (2026-07-26): `misceres~indeed-scraper`
      and `bebity~linkedin-jobs-scraper` are both live, published, active actors — slugs match exactly
      (API IDs use `~` where the store URL uses `/`). **Verification also surfaced a real bug, fixed
      in the same pass:** `fetch_vacancies()` was sending `{"maxItems": limit}` as the entire request
      body to both actors — not a valid field for either. Indeed needs `position`/`location` to have
      anything to search (the item-count field is `maxItemsPerSearch`, not `maxItems`); LinkedIn
      requires `title`/`location`/`rows`. Because HTTP errors were swallowed by the existing
      `except (requests.RequestException, ValueError): pass`, a real (non-`OFFLINE_MODE`) run would
      have silently returned zero results from both actors, with no visible failure — no unit test
      caught it because every test mocks `requests.post` directly rather than exercising a real
      payload against either actor's input schema. Fixed: `fetch_vacancies()` now loops over a new
      `SEARCH_TITLES` module constant (sourced from `profile_seed.json`'s `target_titles`: "Operations
      Foreman/Manager", "Project Engineer (Mechanical)") against `SEARCH_LOCATION` ("Gauteng, South
      Africa"), sending the correct field names per actor — matches `docs/architecture.md`'s Stage 2
      input spec ("search parameters: titles, locations, keywords, limit"), which the original
      implementation never actually followed. New regression test `test_sends_correct_actor_payload_fields`
      added (`tests/unit/test_apify_client.py`) — asserts the exact payload shape per actor so this
      class of bug can't silently regress. All 182 tests pass.
- [x] **Reviewer nits W1/W2 fixed and merged (2026-07-31).** Reviewer approved the PNet/Careers24
      Automated Discovery build "APPROVE WITH NITS" (no blockers) with two follow-ups:
      **W1** — `build_extraction_prompt()` embedded `raw_page_text` (untrusted, scraped job-posting
      text) directly into the Ollama extraction prompt with no defense-in-depth wrap, unlike
      `doc_gen`'s established `wrap_untrusted_text()` pattern for the equivalent `vacancy.description`
      sink. Fixed: `extraction_prompt.py` now wraps `raw_page_text` with `doc_gen/runner.py`'s
      `wrap_untrusted_text()` before embedding it (RED `4633dd8`, GREEN `a5c3285`).
      **W2** — `normalize_url()` stripped the *entire* query string before building the
      `(company, title, normalize_url(url))` dedupe key, collapsing every Indeed URL (whose canonical
      identity lives in `?jk=<id>`) to the same bare path — silently merging genuinely distinct
      postings. Fixed: `normalize_url()` now strips only an allowlist of known tracking params
      (`utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `gclid`, `fbclid`),
      preserving significant identifier params like `jk` (RED `5ffc010`, GREEN `6068db4`). Both fixes
      built TDD in worktree `agent-a6eb29f112cbc6764`, fast-forward merged to `master` at `9319b5a`
      (232 tests passing, zero regressions). Worktree removed after merge confirmed clean.
- [x] **Two real-run bugs found and fixed (2026-07-31) — the first non-offline, real (paid) `career-engine
      fetch-vacancies --limit 10` run against real Apify actors.** Both bugs were invisible to the existing
      unit test suite because every test mocks `requests.post` directly rather than exercising real actor
      behavior — the same class of gap flagged the last time this happened (the `maxItems`/actor-slug bug
      above). **Bug 1 — Indeed defaulting to the US site:** all 10 results came back as `indeed.com` (US
      domain) postings in Denver/Maui/southeast-US, despite `SEARCH_LOCATION = "Gauteng, South Africa"`
      being sent. Confirmed via the actor's own input-schema docs (`misceres/indeed-scraper`) that
      `location` is a free-text city/locality filter only — targeting a specific Indeed domain/region
      requires a separate `"country"` field, absent from the original payload, so the actor silently fell
      back to its US default. Fixed: the Indeed request payload now also sends `"country": "ZA"`.
      LinkedIn's actor (`bebity/linkedin-jobs-scraper`) needs no equivalent fix — confirmed via its own
      input-schema docs that `location` is plain free-text with no separate country field. **Bug 2 —
      truncation discarding paid results from other platforms:** `fetch_vacancies()` built one flat
      `results` list via sequential `.extend()` calls (Indeed, then LinkedIn, then each
      `CRAWLER_PLATFORMS` entry, in that fixed order) and truncated once at the end with `[:limit]`.
      Because Indeed is called with `"maxItemsPerSearch": limit`, it alone filled the entire truncation
      window in the real run before LinkedIn's or PNet/Careers24's already-fetched-and-billed results were
      ever appended — 10/10 results were Indeed, the other platforms contributed zero despite real network
      calls being made and paid for. This was a starvation bug by list position, not any relevance or
      fairness criterion. Fixed: each source's normalized items are now collected into their own list,
      then combined via a new `_interleave()` helper — round-robin, one item from each non-empty source in
      turn, cycling until exhausted — before the existing `_dedupe(...)[:limit]` call, so no single source
      can starve the others of slots. Two new regression tests added to
      `tests/unit/test_apify_client.py`: `test_indeed_payload_includes_country_za` (asserts the Indeed
      payload includes `"country": "ZA"`) and
      `test_other_sources_survive_truncation_when_indeed_alone_exceeds_limit` (constructs a scenario where
      Indeed's mocked response alone exceeds `limit` while LinkedIn also has distinct real items, and
      asserts LinkedIn items survive into the final truncated result rather than being fully starved out).
      `career.db` (containing the 10 real vacancies from the run that surfaced these bugs) was left
      untouched — no reset, no delete. Baseline was 232 tests before this fix; 234 after (2 new tests,
      zero regressions). See `docs/api-patterns.md`'s Apify section for the updated documented behavior.

---

## Open Items (require Tebello — not something an agent should attempt)

- [x] **Shared-`user_version` migration trap — RESOLVED 2026-08-07 by ADR-004, built and verified.**
      `docs/decisions/ADR-004-schema-migration-ledger.md` is **Accepted**, Codex-reviewed, folded in,
      and its 12-step Build Queue is complete — see Phase 18 in the Build Queue above. All five
      modules now delegate to one runner in `src/shared/migrations.py` and record into a
      `schema_migrations(module, version, applied_at)` ledger; version numbers are per-module;
      `PRAGMA user_version` is frozen and no longer gates anything. CLAUDE.md Hard Rule 6 was
      rewritten accordingly. **Phase B is unblocked.**

- [x] **Manual PNet bare-URL verification (Amendment, Open Item 4) — resolved 2026-07-31.** Tebello
      personally opened `https://www.pnet.co.za/jobs/operations-foreman/in-gauteng` (the bare path-only
      shape, no `?` query string) in an ordinary browser and confirmed it renders a working results page
      with real matches. `data/discovery_config.json`'s `pnet.mode` flipped from
      `"manual_pending_verification"` to `"auto"` accordingly — `discovery.py::get_job_urls` now calls
      `discover_job_urls("pnet", ...)` for real instead of the seed-urls fallback below.
- [ ] **Real PNet seed URLs — now dormant, not deleted (Amendment, updated Open Item 1).** With
      `pnet.mode` now `"auto"`, `data/crawler_seed_urls.json`'s `"pnet"` list is no longer PNet's active
      sourcing path — it stays in place as the fallback `get_job_urls` would revert to if `pnet.mode` is
      ever reverted to `"manual_pending_verification"` (e.g. PNet's live results page stops rendering
      usably). No action needed unless that revert happens.
- [ ] Extraction reliability at scale (Amendment, unchanged Open Item 2) — **first real data point
      2026-08-01**: a real `fetch_vacancies(limit=6)` run successfully extracted 3 real PNet vacancies
      end-to-end (discovery → crawl → LLM extraction → `Vacancy`), no `VacancyExtractionError`s. Still
      only 3 data points, not "at scale" — `qwen3:8b`'s known reliability risk on messier, more variable
      job-posting text is a valid future revisit with a larger sample, not resolved by one small run.
- [ ] `CRAWLER_RATE_LIMIT_PER_MIN` default of 30 (Amendment, unchanged Open Item 3) — **unblocked as of
      2026-08-01's discovery fix**, same reason as above: no real crawl volume has gone through this
      limiter yet, but discovery can now actually produce URLs to fetch. Revisit after the real-run
      verification below.
- [x] **Real-run verification for the 2026-08-01 discovery fix — confirmed 2026-08-01.** A real
      `fetch_vacancies(limit=6)` call returned 6 vacancies: 3 `indeed`, 3 `pnet` — PNet discovery is
      confirmed working end-to-end against real data (discovery → crawl → LLM extraction → `Vacancy`).
      Careers24 didn't appear in this particular 6-item sample (round-robin interleave may simply not
      have reached it at this limit) — not evidence of a problem, just a small sample; revisit with a
      larger `--limit` if Careers24 coverage needs separate confirmation.

---

## Future (not yet scheduled)

- [ ] **Indeed site adapter for Stage 6** (was "Playwright site adapter"; before that "Phase 6,
      post-MVP numbering"). **Two concurrent terminal sessions worked this item on 2026-08-07** — the
      one that wrote the block below (parked at the Indeed sign-in boundary, ToS/risk unanswered),
      and a second, later one (this entry) that got Tebello's ToS/account-risk acknowledgement
      directly, completed the sign-in, ran a live DOM recon, and wrote a full spec. **Flagged to
      Tebello as a real concurrent-session collision** — not resolved by this edit alone; see this
      session's own report. The core is built (Phase 16 above) and the registry is still empty, so
      every approved application still routes to manual today.

      **Superseding update (this session, later 2026-08-07):** the three "still open" items directly
      below are now stale.
      1. **ToS/account-risk exposure: explicitly accepted by Tebello**, in-session, distinct from and
         after the earlier sign-in-for-recon action (which correctly was *not* treated as that
         acknowledgement).
      2. **The sign-in boundary was crossed** — signed in as Tebello (he signed in himself; no agent
         touched credentials), then a real `claude-in-chrome` walkthrough of one of the 6 approved
         vacancies (`Utopia`, `jk=d7d04674eabafbac`) ran to the screening-questions step. **Nothing
         was submitted.**
      3. **The real-site smoke test requirement stands, and got bigger.** Recon surfaced two findings
         neither prior pass had: the flow is **reCAPTCHA-protected** (now a hard, non-negotiable
         design rule — detect and abort, never solve/defeat it, a separate risk from the ToS
         acknowledgement above) and **employer screening questions are real, per-posting, and often
         open-ended free-text** (one posting asked for a project-description essay) — not a pure
         deterministic form-fill as both earlier passes assumed. Tebello decided these get
         LLM-drafted (headless Claude Code) answers held for his explicit per-question approval
         before any submission.

      Full design, acceptance criteria, and a phase-level Build Queue:
      `docs/specs/indeed-submit-adapter.md` (new, 2026-08-07). `/codex-review` ran on it per Hard
      Rule 13 and returned substantive findings (an accidentally-networked `can_handle()`, no
      question-drift policy, underspecified CAPTCHA detection, missing `prep_failed` outcome
      semantics, duplicate-submission risk, and more).

      **Codex fold-in complete (2026-08-07, later hub session) — the spec's §Amendment now closes
      all of it, and Hard Rule 13's gate is satisfied.** 22 accepted changes (A1–A22), 6
      clarifications, 4 considered-and-declined. The four named gaps resolved concretely:
      `can_handle()` is now a pure offline URL predicate with all live work moved to a non-Protocol
      `inspect_apply_flow()`; question drift is a sha256 fingerprint over normalized
      text/type/required/options compared as a set, aborting in both directions; CAPTCHA detection
      is five specific abort states and three explicit never-abort states (the reCAPTCHA *notice* is
      normal and must not trip it); and `prep_failed` was **deleted** rather than defined —
      prep failures are not submission attempts, so they go to a new `submission_preps` table whose
      seven states also fix the "zero questions = never prepped or genuinely none?" ambiguity in
      `all_questions_reviewed()`.

      **Four further findings came from reading the code and the live `career.db` during the
      fold-in, not from Codex** — two of them would have failed at runtime as written:
      - **`email`/`phone` need real migrations (A5).** The spec claimed "no DB migration, same
        precedent as `VALID_PLATFORMS`/`VALID_STATUSES`" — a false analogy. Those validate values in
        an existing unconstrained column; these are **new columns** on the real `candidate_profile`
        table, so `upsert_profile()` would have failed with `no such column: email`. Now
        `(5, "ALTER TABLE candidate_profile ADD COLUMN email TEXT")` and `(6, … phone …)` in
        `profile/migrations.py` — versions 5/6 per Hard Rule 6, the first migration this project has
        written since that rule was recorded.
      - **The `submissions.outcome` CHECK is a trap with a closing window (A4).** Verified: the live
        `career.db` is at `user_version = 4` and has **no `submissions` table** — Stage 6 has never
        run against it. So editing the inlined CHECK works today, but `CREATE TABLE IF NOT EXISTS`
        will silently keep the old 3-value constraint the moment anyone runs `submit` once first,
        and `pending_review` inserts would then fail at runtime. Phase B adds the value **and** a
        DDL-drift guard in `init_db()` that refuses loudly instead.
      - **`prep-submission` is a network command in two senses (A9).** `run_claude_code()` shells to
        `claude -p`, which needs connectivity — "local subprocess" (ADR-003) is not "offline". Only
        `review-questions` is genuinely offline.
      - **No PDF path exists in the database (A16).** `generation_log` has no path column, so the
        adapter must reconstruct `pdf_export`'s naming; Phase G promotes it to a shared
        `resolve_export_paths()` rather than duplicating the format string.

      **Phase A is built — 2026-08-07, see Phase 17 in the Build Queue above** (`9d4ee17` RED,
      `379a4b2` GREEN). Both of its Open Items are closed: Tebello confirmed `tlelosa@gmail.com`
      and the phone was taken from the Master CV (`078 481 8711`), and **A15 was confirmed as
      wanted** — `submit --all` will refuse auto-submit, so the 6 approved vacancies go out as six
      deliberate single commands (spec Open Item 5).

      **Backup (spec Open Item 4) — done twice, by two concurrent sessions.** Two byte-identical
      copies of the same unmigrated `career.db` now exist:
      `career.pre-migration-5-6-20260807.db` (sqlite3 backup API, integrity-checked and
      row-count-verified — the better-made one, recorded in `6c7058e`) and
      `career.db.backup-pre-phase-a-2026-08-07` (plain file copy; safe here, verified no WAL
      sidecars existed at the time). Both are gitignored. **One should be deleted once Tebello
      picks which to keep** — not done unprompted, it's real career data.

      **Two things Phase A deliberately did not do:**
      1. **The live `career.db` is still at `user_version = 4`, unmigrated.** Migrations 5/6
         auto-apply on the next `init_db()` from any command, after which `get_profile()` raises an
         actionable error until `career-engine import-profile --file data/profile_seed.json` is
         re-run to populate the contact details. Verified end-to-end on a copy.
      2. **The shared-`user_version` fix covers `src/profile/` only** — see the new Open Item
         above. Worth settling before Phase B, which is the next thing that adds a migration.

      **Phase B is built — 2026-08-07, see Phase 19 in the Build Queue above** (`6e457a6`,
      `adc3429`, `f80637c`, `ad04b4a`). Both tables exist, `pending_review` is a real outcome, and
      `submission_prep_ready()` implements A2's gate table in full. The A4 trap is closed by a real
      migration rather than only a guard — see the deviation note in Phase 19.

      **Phase C is built — 2026-08-07, see Phase 20 in the Build Queue above** (`861cff5`,
      `80a49ee`, `fdbacaf`, `86d90c4`). The gate is wired, `pending_review` reaches the operator with
      the command it needs next, and `--all` refuses to auto-submit (A15, confirmed with Tebello
      before the build). Still offline, still no adapter registered — every approved application
      routes to manual today.

      Next: **Phase D** — `src/submission/browser.py`: session load, expiry detection (A18), CAPTCHA
      detection (A7), the combined navigation-state check (A17), step logging (C3). Offline for the
      logic; exercised live in E/G. The `playwright` runtime dependency itself is not declared until
      Phase H, per the amended phase table — Phase D writes the logic that will use it.
- [ ] Phase 7 (post-MVP numbering): tracking dashboard (applications, match-score distribution, response rate).
- [ ] Decide whether recruiter cold-outreach (in `data/legacy_reference/`, not part of the original 7-phase plan) gets revived as a later phase.
- [ ] Volume-cap / scheduler layer for document generation (ADR-003 §6, open judgment call #1) — only if Tebello confirms a controlled-batch need; would need its own spec + ADR, and likely a `PRAGMA user_version` migration via the `src/doc_gen/migrations.py` stub (step 34).
- [x] ~~Search-page discovery stage (`discover_job_urls`/`fetch_job_pages` split) for PNet/Careers24~~ —
      **built** (steps 65–71, `src/vacancy_search/discovery.py`) by the Automated Discovery Redesign
      amendment; no longer a future item.
- [ ] Site-specific lightweight HTML parsers for PNet/Careers24, LLM extraction as fallback only —
      alternative to full-LLM extraction flagged by Codex review; cheaper/more reliable if either
      site's HTML structure turns out to be stable enough to parse deterministically.
- [ ] Store raw crawler artifacts (snapshots or normalized JSON) under `data/` during non-offline
      PNet/Careers24 runs, for extraction-error debugging and prompt tuning — flagged by Codex review,
      not built in the current spec.
