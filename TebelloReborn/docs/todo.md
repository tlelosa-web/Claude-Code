# Task Queue — TebelloReborn (Career Engine)

> Updated: 2026-07-29 (PNet/Careers24 Automated Discovery build complete — steps 55-80, Phases 9-15)

---

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

---

## Known Issues

_(none active — the PNet/Careers24 gap below is now a scheduled, spec-backed build, not an open issue)_

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
- [x] 80. `docs/todo.md` — this section (you are here)

---

## Resolved Items

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

---

## Open Items (require Tebello — not something an agent should attempt)

- [ ] **Manual PNet bare-URL verification (Amendment, Open Item 4).** Open
      `https://www.pnet.co.za/jobs/operations-foreman/in-gauteng` (the bare path-only shape, no `?`
      query string) once in an ordinary browser and confirm whether it renders a working PNet
      results/listing page or an error/redirect/block page. Record the result by editing
      `data/discovery_config.json`'s `pnet.mode` directly: `"auto"` if it works, or leave it at
      `"manual_pending_verification"` (with a one-line dated note added to the file's `_comment`) if it
      doesn't. One-time check, not a recurring task — this gates whether `discovery.py::get_job_urls`
      ever calls `discover_job_urls("pnet", ...)` for real, or stays on the seed-urls fallback below.
- [ ] **Real PNet seed URLs — now PNet-only and conditional (Amendment, updated Open Item 1).**
      Careers24 no longer needs this at all (fully automated). If the manual bare-URL check above shows
      the bare-path shape does *not* render a usable page, `data/crawler_seed_urls.json`'s `"pnet"` list
      needs real job-detail-page URLs supplied by Tebello — this becomes PNet's **permanent** sourcing
      path in that case, not a temporary placeholder.
- [ ] Extraction reliability at scale (Amendment, unchanged Open Item 2) — `qwen3:8b`'s known
      reliability risk applies to messier, more variable job-posting page text than the dedicated-actor
      JSON payloads. A high real-world `VacancyExtractionError` rate is signal for prompt-tuning or a
      stronger local model, not evidence the design is wrong — flagged for a future evidence-based
      revisit, not resolved here.
- [ ] `CRAWLER_RATE_LIMIT_PER_MIN` default of 30 (Amendment, unchanged Open Item 3) — confirm this is
      conservative enough once real (non-fallback) crawls are in regular use; easy to override via env
      either way.

---

## Future (not yet scheduled)

- [ ] Phase 6 (post-MVP numbering — original 7-phase plan): Playwright-based auto-fill/submit, paused before final submission.
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
