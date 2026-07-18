# Spec: TebelloReborn (Career Engine) MVP Pipeline Build

> Status: planned, not implemented. No pipeline code exists yet — `src/` and `tests/` are empty.
> Author: Planner agent · Date: 2026-07-18
> Supersedes the unordered items in `docs/todo.md`'s old "Build Queue" section.

---

## Goal

Build Stages 1–5 of the Career Engine pipeline (Profile Import → Vacancy Fetch → AI Matching →
Document Generation → Human Review) as a working, offline-testable Python CLI (`career-engine`),
following the architecture in `docs/architecture.md` and the patterns already proven in the sibling
project `ai-outreach-agency`. Stage 6 (Auto-Submit) and Stage 7 (Dashboard) are explicitly **out of
scope** for this build.

Two decisions previously blocking this plan are now resolved and are treated as fixed inputs below:

1. Console-script/package name: **`career-engine`** (no longer a placeholder — used throughout).
2. `profile_seed.json` title-lane weighting: **Operations Foreman/Operations Manager is the primary
   lane**; Project Engineer (Mechanical) is carried as a secondary, lower-weighted lane in the same
   file (per `CLAUDE.md`'s instruction not to collapse to a single lane by assumption).

---

## Acceptance Criteria

- `career-engine import-profile`, `fetch-vacancies`, `list`, `run`, `run-all` all work end-to-end
  against SQLite, with `run`/`run-all` walking a vacancy through matching → doc gen → review.
- Full test suite (`python -m pytest`) passes fully offline (`OFFLINE_MODE=true`, no network calls),
  mirroring `ai-outreach-agency`'s `conftest.py` convention.
- `data/profile_seed.json` exists, validates against `profile/schema.py`, and encodes Operations
  Foreman/Manager as the primary title lane and Project Engineer (Mechanical) as secondary.
- The vacancy status state machine (`new → scored → asset_ready → approved|rejected`) is enforced in
  code (`VALID_TRANSITIONS`), not just by convention — no stage can be skipped.
- No code path can move a vacancy to `approved` or `rejected` except through `src/review/cli.py`.
  Approval/rejection/edit decisions are persisted to SQLite (this project must not repeat
  `ai-outreach-agency`'s earlier bug where approval decisions were computed but never saved).
- `black . && ruff check .` clean; coverage ≥ 80% on all new `src/` code.
- ADRs exist for the vacancy-store schema and the Apify job-scraping integration.
- `docs/api-patterns.md` exists and documents the real OpenRouter + Apify usage as implemented.

---

## Out of Scope (do not build)

- Stage 6: Playwright-based auto-fill/submit.
- Stage 7: tracking dashboard.
- PNet/Careers24 coverage (no dedicated Apify actor exists yet — deferred per ADR-002).
- Reviving recruiter cold-outreach from `data/legacy_reference/`.
- Any change inside `ai-outreach-agency/` (read-only reference for patterns only).
- Topping up `OPENROUTER_API_KEY` credits (cross-project account issue, not a code task).

---

## Dependency Ordering (phase-level)

```
Phase 0 (scaffolding/config)
   └─▶ Phase 1 (shared clients: rate_limiter, openrouter_client)
          ├─▶ Phase 2 (profile import)  ──┐
          └─▶ Phase 3 (vacancy fetch)  ───┼─▶ Phase 4 (AI matching) ─▶ Phase 5 (doc gen) ─▶ Phase 6 (human review)
                     └─▶ Phase 3.5 (ADRs, can run any time after Phase 3)   │
                                                                             ▼
                                                                     Phase 7 (CLI wiring + integration test)
                                                                             ▼
                                                                     Phase 8 (docs closeout)
```

Within each phase, RED (failing test) steps must land before their paired GREEN (implementation)
step — this is a hard TDD ordering, not just a style preference. GREEN steps that create or touch a
DB table always include the module's `migrations.py` in the same commit, even when it starts as an
empty `MIGRATIONS` list — this is the mechanism that satisfies "no schema change without a migration
file" for *future* ALTERs. **Flag to Architect:** confirm this empty-stub-from-day-one pattern
(identical to `ai-outreach-agency/src/lead_import/migrations.py`) is sufficient for the *initial*
`CREATE TABLE IF NOT EXISTS` statements in Phases 2/3/6, since those are net-new tables, not schema
changes to an existing one — the hard rule's intent (protect against silent, untracked ALTERs) is
preserved either way, but this should be confirmed rather than assumed.

---

## Files to Change (by module, final state)

```
pyproject.toml, .env.example, .gitignore
src/config.py
src/shared/{rate_limiter.py, openrouter_client.py}
src/profile/{schema.py, db.py, migrations.py}
src/vacancy_search/{schema.py, db.py, migrations.py, apify_client.py}
src/matching/{prompt_builder.py, scorer.py, pipeline.py}
src/doc_gen/{cv_generator.py, cover_letter_generator.py, pdf_export.py, pipeline.py}
src/review/{schema.py, db.py, migrations.py, cli.py}
src/main.py
data/profile_seed.json
docs/decisions/{ADR-001-vacancy-store.md, ADR-002-apify-job-scraping.md}
docs/api-patterns.md, docs/session-log.md
tests/conftest.py, tests/unit/conftest.py, tests/unit/test_*.py, tests/integration/test_full_pipeline.py
```

No file above is touched by more than one atomic task, and no single task below touches more than 2
files (test-file-only RED steps count as 1; GREEN steps that pair a module file with its
`migrations.py` count as 2 — the maximum allowed).

---

## Task Plan

Legend: **[RED]** = write failing test(s) first. **[GREEN]** = minimal implementation to pass.
**Network** = `none` (fully offline, always) or `Apify`/`OpenRouter` (required for real runs; tests
still run offline via the `OFFLINE_MODE` fixture).

### Phase 0 — Scaffolding & Config

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 1 | Create `pyproject.toml`: deps (`requests`, `python-dotenv`, `fpdf2`), `dev` extra (`pytest`), `[project.scripts] career-engine = "src.main:main"`, setuptools packages config. Mirror `ai-outreach-agency/pyproject.toml` structure. | executor | `ai-outreach-agency/pyproject.toml` (reference only) | `pyproject.toml` | `python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"` parses cleanly; `pip install -e .` succeeds | none (PyPI fetch is a one-time dev-env step, not a pipeline stage) |
| 2 | Create `.env.example` (placeholders: `OPENROUTER_API_KEY`, `APIFY_API_KEY`, `DB_PATH=career.db`, `OFFLINE_MODE`, `OPENROUTER_RATE_LIMIT_PER_MIN=60`, `APIFY_RATE_LIMIT_PER_MIN=30`) and `.gitignore` (`.env`, `career.db`/`*.db`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `exports/`). **Do not blanket-ignore `data/`** — unlike `ai-outreach-agency`'s `.gitignore`, this project's `data/` holds tracked source data (`Tebello_Lelosa_Master_CV_2026.md`, `profile_seed.json`) that must stay committed. | executor | `ai-outreach-agency/.env.example`, `ai-outreach-agency/.gitignore` (reference only) | `.env.example`, `.gitignore` | Manual read-check: no real secrets in `.env.example`; `data/` absent from `.gitignore` | none |
| 3 | Create `tests/conftest.py` (mock `_log_session` if/when `main.py` writes to `docs/session-log.md`) and `tests/unit/conftest.py` (autouse fixture forcing `OFFLINE_MODE=true` for every unit test). Mirror `ai-outreach-agency/tests/conftest.py` + `tests/unit/conftest.py` exactly, minus the lead-specific mocks (those get added per-module later as needed). | tester | `ai-outreach-agency/tests/conftest.py`, `ai-outreach-agency/tests/unit/conftest.py` | `tests/conftest.py`, `tests/unit/conftest.py` | `python -m pytest --collect-only` runs clean (no tests yet, but fixtures load without error) | none |
| 4 | **[RED]** `tests/unit/test_config.py` — assert `Settings` dataclass has `OPENROUTER_API_KEY`, `APIFY_API_KEY`, `DB_PATH` (default `career.db`), `OFFLINE_MODE`, rate-limit override fields, `EXPORTS_DIR`; assert `load_settings()` reads from env vars with correct defaults when unset. | tester | none (new module) | `tests/unit/test_config.py` | `python -m pytest tests/unit/test_config.py` fails with `ModuleNotFoundError`/`ImportError` (RED confirmed) | none |
| 5 | **[GREEN]** `src/config.py` — `Settings` dataclass + `load_settings()` via `python-dotenv`, adapted from `ai-outreach-agency/src/config.py` (drop Gmail/sender fields, keep `DB_PATH`, `EXPORTS_DIR`, add `OFFLINE_MODE` field). | executor | `tests/unit/test_config.py`, `ai-outreach-agency/src/config.py` (reference) | `src/config.py` | `python -m pytest tests/unit/test_config.py` passes (GREEN) | none |

### Phase 1 — Shared External-Client Infrastructure

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 6 | **[RED]** `tests/unit/test_rate_limiter.py` — copy/adapt from `ai-outreach-agency/tests/unit/test_rate_limiter.py` (token-bucket behavior: capacity, refill rate, blocking). | tester | `ai-outreach-agency/tests/unit/test_rate_limiter.py` | `tests/unit/test_rate_limiter.py` | Fails with `ImportError` (RED confirmed) | none |
| 7 | **[GREEN]** `src/shared/rate_limiter.py` — copy verbatim from `ai-outreach-agency/src/shared/rate_limiter.py` per `CLAUDE.md`'s explicit "copied in, not re-invented" instruction. Also create `src/shared/__init__.py`. | executor | `ai-outreach-agency/src/shared/rate_limiter.py` | `src/shared/rate_limiter.py`, `src/shared/__init__.py` | `python -m pytest tests/unit/test_rate_limiter.py` passes | none |
| 8 | **[RED]** `tests/unit/test_openrouter_client.py` — request/response shape for a chat-completion call, model selection (haiku vs sonnet), 429 retry via mocked `time.sleep`, `OFFLINE_MODE` short-circuit returning a fixture response, HTTP 402 (out-of-credits) surfaced as a clear error not a silent failure. | tester | `ai-outreach-agency/tests/unit/test_openrouter_client.py` | `tests/unit/test_openrouter_client.py` | Fails with `ImportError` (RED confirmed) | none |
| 9 | **[GREEN]** `src/shared/openrouter_client.py` — adapted from `ai-outreach-agency/src/shared/openrouter_client.py`; must accept a model-id parameter so callers can pass `anthropic/claude-haiku-4.5` (scoring) or `anthropic/claude-sonnet-5` (doc gen) per the inference-routing table in `CLAUDE.md`. Uses `shared/rate_limiter.py`, honors `OPENROUTER_RATE_LIMIT_PER_MIN`. | executor | `tests/unit/test_openrouter_client.py`, `ai-outreach-agency/src/shared/openrouter_client.py` (reference) | `src/shared/openrouter_client.py` | `python -m pytest tests/unit/test_openrouter_client.py` passes | OpenRouter (real calls only; tests offline) |

### Phase 2 — Stage 1: Profile Import (fully offline)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 10 | **[RED]** `tests/unit/test_profile_schema.py` — `CandidateProfile` dataclass validation: required fields (name, skills, experience timeline, region), `target_titles` as an ordered/weighted list supporting multiple lanes with a primary flag or weight, salary floor, industries. Include a case asserting a profile with two title lanes (one flagged primary) validates correctly. | tester | `docs/architecture.md` Stage 1 section, `ai-outreach-agency/src/lead_import/schema.py` (reference pattern only — different domain) | `tests/unit/test_profile_schema.py` | Fails with `ImportError` (RED confirmed) | none |
| 11 | **[GREEN]** `src/profile/schema.py` — `CandidateProfile` dataclass + `TitleLane` (or equivalent) supporting weighted/primary title lanes, matching the test contract from step 10. Create `src/profile/__init__.py`. | executor | `tests/unit/test_profile_schema.py` | `src/profile/schema.py`, `src/profile/__init__.py` | `python -m pytest tests/unit/test_profile_schema.py` passes | none |
| 12 | **[RED]** `tests/unit/test_profile_db.py` — `init_db` creates `candidate_profile` table; `upsert_profile`/`get_profile` round-trip (single-candidate table, upsert not insert-many); malformed data raises. | tester | `src/profile/schema.py` | `tests/unit/test_profile_db.py` | Fails with `ImportError` (RED confirmed) | none |
| 13 | **[GREEN]** `src/profile/db.py` (init/upsert/get, uses `sqlite3`, `PRAGMA journal_mode=WAL`) + `src/profile/migrations.py` (empty `MIGRATIONS` list, `apply_migrations()` — same shape as `ai-outreach-agency/src/lead_import/migrations.py`, ready for future ALTERs). | executor | `tests/unit/test_profile_db.py`, `ai-outreach-agency/src/lead_import/db.py` + `migrations.py` (reference) | `src/profile/db.py`, `src/profile/migrations.py` | `python -m pytest tests/unit/test_profile_db.py` passes | none |
| 14 | **[RED]** `tests/unit/test_profile_seed_data.py` — loads `data/profile_seed.json`, validates it via `profile/schema.py`'s `CandidateProfile`, and asserts the Operations Foreman/Operations Manager lane is present and flagged/weighted as primary, with Project Engineer (Mechanical) present as a secondary lane. | tester | `src/profile/schema.py` | `tests/unit/test_profile_seed_data.py` | Fails (`FileNotFoundError` — `data/profile_seed.json` doesn't exist yet) (RED confirmed) | none |
| 15 | **[GREEN]** Author `data/profile_seed.json` from `data/Tebello_Lelosa_Master_CV_2026.md`: skills, 19-year experience timeline, region (Gauteng), salary floor, industries (manufacturing/heavy industry/power generation/mining-adjacent), and the two title lanes — **Operations Foreman/Manager as primary**, **Project Engineer (Mechanical) as secondary** — per the now-confirmed weighting decision. | data-agent | `data/Tebello_Lelosa_Master_CV_2026.md`, `tests/unit/test_profile_seed_data.py` | `data/profile_seed.json` | `python -m pytest tests/unit/test_profile_seed_data.py` passes | none |

### Phase 3 — Stage 2: Vacancy Fetch (Apify required for real runs; tests offline)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 16 | **[RED]** `tests/unit/test_vacancy_schema.py` — `Vacancy` dataclass: company, title, description, url, platform (indeed/linkedin), salary, deadline, scraped_at, status (default `new`); required-field validation. | tester | `docs/architecture.md` Stage 2 section | `tests/unit/test_vacancy_schema.py` | Fails with `ImportError` (RED confirmed) | none |
| 17 | **[GREEN]** `src/vacancy_search/schema.py` — `Vacancy` dataclass matching step 16's contract. Create `src/vacancy_search/__init__.py`. | executor | `tests/unit/test_vacancy_schema.py` | `src/vacancy_search/schema.py`, `src/vacancy_search/__init__.py` | `python -m pytest tests/unit/test_vacancy_schema.py` passes | none |
| 18 | **[RED]** `tests/unit/test_vacancy_db.py` — `init_db` creates `vacancy` table with `UNIQUE(company, title, url)`; insert + dedup-on-conflict; `get_by_status`, `get_by_id`; `VALID_TRANSITIONS = {"new": {"scored"}, "scored": {"asset_ready"}, "asset_ready": {"approved", "rejected"}, "approved": set(), "rejected": set()}`; `update_vacancy_status` raises on invalid transition. | tester | `src/vacancy_search/schema.py`, `ai-outreach-agency/src/lead_import/db.py` (state-machine pattern reference) | `tests/unit/test_vacancy_db.py` | Fails with `ImportError` (RED confirmed) | none |
| 19 | **[GREEN]** `src/vacancy_search/db.py` (init/insert/dedup/get/`update_vacancy_status`) + `src/vacancy_search/migrations.py` (empty stub, same pattern as step 13). | executor | `tests/unit/test_vacancy_db.py` | `src/vacancy_search/db.py`, `src/vacancy_search/migrations.py` | `python -m pytest tests/unit/test_vacancy_db.py` passes | none |
| 20 | **[RED]** `tests/unit/test_apify_client.py` — `OFFLINE_MODE` fixture returns 2–3 fake vacancies (Indeed + LinkedIn shape); real-call path mocked (`requests.post`/`get`); rate limiter `.acquire()` called before every real request; missing `APIFY_API_KEY` falls back to fixture with a warning, not a crash. | tester | `ai-outreach-agency/tests/unit/test_apify_client.py`, `ai-outreach-agency/src/research/apify_client.py` (pattern reference) | `tests/unit/test_apify_client.py` | Fails with `ImportError` (RED confirmed) | none |
| 21 | **[GREEN]** `src/vacancy_search/apify_client.py` — calls the Apify Indeed scraper actor and LinkedIn Jobs scraper actor, normalizes results into `Vacancy` objects, dedupes by `(company, title, url)`, uses `shared/rate_limiter.py` (`APIFY_RATE_LIMIT_PER_MIN`), `OFFLINE_MODE` fixture per step 20. | executor | `tests/unit/test_apify_client.py`, `src/shared/rate_limiter.py`, `src/vacancy_search/schema.py` | `src/vacancy_search/apify_client.py` | `python -m pytest tests/unit/test_apify_client.py` passes | Apify (real calls only; tests offline) |

### Phase 3.5 — ADRs (can run any time after Phase 3 lands)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 22 | Write `docs/decisions/ADR-001-vacancy-store.md` — documents SQLite as source of truth for `Vacancy` records, the status state machine, and the migration-stub pattern (mirrors `ai-outreach-agency` ADR-001). Includes the flagged open question from the Dependency Ordering section above (initial-CREATE vs. migration-file scope). | architect | `src/vacancy_search/db.py`, `src/vacancy_search/migrations.py` | `docs/decisions/ADR-001-vacancy-store.md` | Read-check: decision, context, consequences sections present | none |
| 23 | Write `docs/decisions/ADR-002-apify-job-scraping.md` — documents the Indeed + LinkedIn actor choice, PNet/Careers24 deferral rationale (no dedicated actor as of this decision), and the future generic-crawler + LLM-extraction option. | architect | `src/vacancy_search/apify_client.py`, `docs/architecture.md` | `docs/decisions/ADR-002-apify-job-scraping.md` | Read-check: decision, context, consequences sections present | none |

### Phase 4 — Stage 3: AI Matching (OpenRouter required for real runs; tests offline)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 24 | **[RED]** `tests/unit/test_matching.py` — `build_match_prompt(profile, vacancy)` produces a prompt referencing both title lanes with correct weighting language; `score_vacancy(profile, vacancy, db_path=...)` parses a mocked Claude response into `(score: int, strengths: list[str], weaknesses: list[str], recommendation: str)`; `OFFLINE_MODE` returns a deterministic fixture score. | tester | `data/profile_seed.json` (shape), `src/vacancy_search/schema.py` | `tests/unit/test_matching.py` | Fails with `ImportError` (RED confirmed) | none |
| 25 | **[GREEN]** `src/matching/prompt_builder.py` — pure function, no network, builds the comparison prompt from `CandidateProfile` + `Vacancy`. Create `src/matching/__init__.py`. | executor | `tests/unit/test_matching.py` | `src/matching/prompt_builder.py`, `src/matching/__init__.py` | `python -m pytest tests/unit/test_matching.py::TestPromptBuilder` (or equivalent subset) passes | none |
| 26 | **[GREEN]** `src/matching/scorer.py` — calls `shared/openrouter_client.py` with `anthropic/claude-haiku-4.5` (per inference-routing table), parses the score/rationale response. Does **not** touch the DB directly (pure scoring function). | executor | `tests/unit/test_matching.py`, `src/matching/prompt_builder.py`, `src/shared/openrouter_client.py` | `src/matching/scorer.py` | `python -m pytest tests/unit/test_matching.py` passes fully | OpenRouter (real calls only; tests offline) |
| 27 | **[RED]** `tests/unit/test_matching_pipeline.py` — `run_matching(vacancy, profile, db_path)` calls scorer, persists score/rationale, and transitions `Vacancy.status` `new → scored` via `vacancy_search.db.update_vacancy_status`; invalid current status raises. | tester | `src/matching/scorer.py`, `src/vacancy_search/db.py` | `tests/unit/test_matching_pipeline.py` | Fails with `ImportError` (RED confirmed) | none |
| 28 | **[GREEN]** `src/matching/pipeline.py` — `run_matching()` orchestration per step 27 (mirrors `ai-outreach-agency/src/research/pipeline.py`'s shape). | executor | `tests/unit/test_matching_pipeline.py` | `src/matching/pipeline.py` | `python -m pytest tests/unit/test_matching_pipeline.py` passes | OpenRouter (via scorer; tests offline) |

### Phase 5 — Stage 4: Document Generation (OpenRouter required for CV/cover-letter text; pdf_export fully offline)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 29 | **[RED]** `tests/unit/test_doc_gen.py` — `generate_cv(profile, vacancy)` and `generate_cover_letter(profile, vacancy)` both call the mocked OpenRouter client at `anthropic/claude-sonnet-5`, return tailored text emphasizing the vacancy-relevant title lane; `OFFLINE_MODE` returns deterministic fixture text. | tester | `src/matching/scorer.py` (pattern), `data/profile_seed.json` (shape) | `tests/unit/test_doc_gen.py` | Fails with `ImportError` (RED confirmed) | none |
| 30 | **[GREEN]** `src/doc_gen/cv_generator.py` — tailors CV emphasis per vacancy via `shared/openrouter_client.py` (sonnet-tier). Create `src/doc_gen/__init__.py`. | executor | `tests/unit/test_doc_gen.py` | `src/doc_gen/cv_generator.py`, `src/doc_gen/__init__.py` | `python -m pytest tests/unit/test_doc_gen.py -k cv_generator` passes | OpenRouter (real calls only; tests offline) |
| 31 | **[GREEN]** `src/doc_gen/cover_letter_generator.py` — generates a personalized cover letter per vacancy via `shared/openrouter_client.py` (sonnet-tier). | executor | `tests/unit/test_doc_gen.py` | `src/doc_gen/cover_letter_generator.py` | `python -m pytest tests/unit/test_doc_gen.py` passes fully | OpenRouter (real calls only; tests offline) |
| 32 | **[RED]** `tests/unit/test_pdf_export.py` — `export_cv_pdf`/`export_cover_letter_pdf` write a valid PDF file to `EXPORTS_DIR`, filename includes vacancy id/company, reuses the working `fpdf2` pattern from `_archive_qwen_prototype/4_Scripts/generate_cv_pdf.py` and `ai-outreach-agency/src/asset_gen/pdf_export.py`. | tester | `_archive_qwen_prototype/4_Scripts/generate_cv_pdf.py`, `ai-outreach-agency/src/asset_gen/pdf_export.py` (references) | `tests/unit/test_pdf_export.py` | Fails with `ImportError` (RED confirmed) | none |
| 33 | **[GREEN]** `src/doc_gen/pdf_export.py` — implements the two export functions, fully offline (`fpdf2` is local rendering, no network). | executor | `tests/unit/test_pdf_export.py` | `src/doc_gen/pdf_export.py` | `python -m pytest tests/unit/test_pdf_export.py` passes | none |
| 34 | **[RED]** `tests/unit/test_doc_gen_pipeline.py` — `run_doc_gen(profile, vacancy, db_path)` calls both generators + both PDF exports, then transitions `Vacancy.status` `scored → asset_ready`. | tester | `src/doc_gen/cv_generator.py`, `src/doc_gen/cover_letter_generator.py`, `src/doc_gen/pdf_export.py`, `src/vacancy_search/db.py` | `tests/unit/test_doc_gen_pipeline.py` | Fails with `ImportError` (RED confirmed) | none |
| 35 | **[GREEN]** `src/doc_gen/pipeline.py` — `run_doc_gen()` orchestration per step 34 (mirrors `ai-outreach-agency/src/asset_gen/pipeline.py`). | executor | `tests/unit/test_doc_gen_pipeline.py` | `src/doc_gen/pipeline.py` | `python -m pytest tests/unit/test_doc_gen_pipeline.py` passes | OpenRouter (via generators; tests offline) |

### Phase 6 — Stage 5: Human Review (fully offline) — **MANDATORY REVIEWER SIGN-OFF**

> Every step in this phase touches `src/review/` (the human approval gate). Per `CLAUDE.md`'s hard
> rule #1 and this project's own `planner.md` rule, **the Reviewer agent must sign off on steps 40–41
> before an Executor is allowed to run them** — not just before the resulting commit is merged. This
> is the one place in the whole plan where a code path could silently let a document leave the system
> without a human decision if implemented wrong (repeating `ai-outreach-agency`'s earlier
> unsaved-approval bug), so treat sign-off as a hard gate, not a formality.

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 36 | **[RED]** `tests/unit/test_review_schema.py` — `Decision` enum (`APPROVED`, `REJECTED`, `EDITED`); `ReviewResult` dataclass (vacancy_id, decision, edited_cv_text/edited_cover_letter_text optional). | tester | `ai-outreach-agency/src/approval/schema.py` (reference) | `tests/unit/test_review_schema.py` | Fails with `ImportError` (RED confirmed) | none |
| 37 | **[GREEN]** `src/review/schema.py`. Create `src/review/__init__.py`. | executor | `tests/unit/test_review_schema.py` | `src/review/schema.py`, `src/review/__init__.py` | `python -m pytest tests/unit/test_review_schema.py` passes | none |
| 38 | **[RED]** `tests/unit/test_review_db.py` — `init_approvals_table`, `save_approval` actually persists a row (this is the exact bug class to guard against — assert a fresh `get_approval_by_vacancy_id` call after `save_approval` returns the saved decision, not `None`). | tester | `src/review/schema.py`, `ai-outreach-agency/src/approval/db.py` (reference) | `tests/unit/test_review_db.py` | Fails with `ImportError` (RED confirmed) | none |
| 39 | **[GREEN]** `src/review/db.py` + `src/review/migrations.py` (empty stub, same pattern as steps 13/19). | executor | `tests/unit/test_review_db.py` | `src/review/db.py`, `src/review/migrations.py` | `python -m pytest tests/unit/test_review_db.py` passes | none |
| 40 | **[RED — REQUIRES REVIEWER SIGN-OFF BEFORE EXECUTION]** `tests/unit/test_review_cli.py` — approve/reject/edit/quit flows; approve/edit both call `update_vacancy_status(..., "approved")` **and** `save_approval(...)` (assert both happen — this is the regression test for the known bug class); reject calls `update_vacancy_status(..., "rejected")`; quit raises `SystemExit(0)` without touching the DB. | tester | `src/review/schema.py`, `src/review/db.py`, `ai-outreach-agency/src/approval/cli.py` (reference) | `tests/unit/test_review_cli.py` | Reviewer sign-off obtained; then fails with `ImportError` (RED confirmed) | none |
| 41 | **[GREEN — REQUIRES REVIEWER SIGN-OFF BEFORE EXECUTION]** `src/review/cli.py` — CLI approval gate mirroring `ai-outreach-agency/src/approval/cli.py`'s structure exactly (print vacancy + generated CV/cover-letter text, take A/R/E/Q decision, persist via `save_approval`, update vacancy status). No code path may skip persistence. | executor | `tests/unit/test_review_cli.py`, `src/vacancy_search/db.py`, `src/review/db.py` | `src/review/cli.py` | Reviewer sign-off obtained; `python -m pytest tests/unit/test_review_cli.py` passes; reviewer re-confirms no path bypasses `save_approval` | none |

### Phase 7 — CLI Wiring & Integration

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 42 | **[RED]** `tests/unit/test_main.py` — argparse subcommands (`import-profile`, `fetch-vacancies`, `list`, `run`, `run-all`) parse correctly and dispatch to the right stage function (all stage functions mocked). | tester | `src/config.py`, all Phase 2–6 module signatures | `tests/unit/test_main.py` | Fails with `ImportError` (RED confirmed) | none |
| 43 | **[GREEN]** `src/main.py` — CLI runner wiring `import-profile` (Stage 1), `fetch-vacancies` (Stage 2), `list` (query vacancies by status), `run --vacancy-id` (Stages 3→4→5 for one vacancy), `run-all --status` (loop, stopping cleanly on `SystemExit` from the review CLI's Quit option — same pattern as `ai-outreach-agency/src/main.py::cmd_run_all`). | executor | `tests/unit/test_main.py`, all Phase 2–6 modules | `src/main.py` | `python -m pytest tests/unit/test_main.py` passes | none (dispatch only; underlying stages carry their own network flags) |
| 44 | `tests/integration/test_full_pipeline.py` — end-to-end offline run through the real `career-engine` CLI: `import-profile` → `fetch-vacancies` (OFFLINE_MODE fixture vacancies) → `run --vacancy-id <id>` (OFFLINE_MODE scoring + doc gen fixtures) → simulated Approve via a scripted `input_fn` → assert final `Vacancy.status == "approved"` and an approval row exists. Mirrors `ai-outreach-agency/tests/integration/test_full_pipeline.py`. | tester | `src/main.py`, all prior modules | `tests/integration/test_full_pipeline.py` | `python -m pytest tests/integration/test_full_pipeline.py` passes; then `python -m pytest` (full suite) passes with `black . && ruff check .` clean | none (fully offline integration run) |

### Phase 8 — Docs Closeout

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 45 | Write `docs/api-patterns.md` documenting the real OpenRouter (chat-completions, model routing table, 402 handling) and Apify (Indeed + LinkedIn actor calls, polling, `OFFLINE_MODE` fixture shape) usage as implemented in Phases 1/3/4/5 — this file is referenced by `CLAUDE.md` but doesn't exist yet. | doc-writer | `src/shared/openrouter_client.py`, `src/vacancy_search/apify_client.py` | `docs/api-patterns.md` | Read-check: matches the actual implemented function signatures, no invented endpoints | none |
| 46 | Create `docs/session-log.md` (empty chronological log with a header, ready for the `post-task` hook once wired) and append a final entry summarizing the MVP build completion once Phases 0–7 are merged. | doc-writer | none | `docs/session-log.md` | Read-check: file exists, header present | none |

---

## Verification Summary (run before considering the build "done")

```bash
cd TebelloReborn
pip install -e ".[dev]"
black . && ruff check .
python -m pytest                 # full suite, offline, must be 100% green
python -m pytest --cov=src --cov-report=term-missing   # ≥80% on new code
career-engine import-profile --file data/profile_seed.json
career-engine fetch-vacancies --limit 5   # OFFLINE_MODE=true for a dry run without Apify credits
career-engine list
```

---

## Open Items Flagged for Architect / User (not blocking start, but need an answer before the
## affected step is merged)

1. **Migration-file scope for net-new tables** (see Dependency Ordering section) — confirm the
   empty-stub `migrations.py` pattern satisfies "no schema change without a migration file" for
   initial `CREATE TABLE` statements in Phases 2/3/6, or whether Architect wants a first real
   migration entry recorded even for the initial create.
2. **Phase 6 reviewer sign-off** (steps 40–41) — Reviewer must explicitly approve before an Executor
   touches `src/review/`, per the hard rule. This is not a rubber-stamp step; budget real review time
   for it, likely with Opus per the permanent-Opus-for-reviewer routing rule.
