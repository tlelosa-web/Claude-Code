# Spec: PNet + Careers24 Vacancy Coverage (Generic Crawler + Local LLM Extraction)

> Status: planned, not implemented.
> Author: Planner agent · Date: 2026-07-29
> Extends Stage 2 (Vacancy Fetch) of the MVP pipeline (`docs/specs/mvp-pipeline-build.md`, Phase 3,
> steps 16–21 — already built and merged, all 54 original steps done per `docs/todo.md`).
> Step numbers below continue that Build Queue's numbering (55 onward) rather than restarting at 1 —
> `docs/todo.md` is the source of truth for numbering; this file is the source of truth for per-step
> detail, exactly the convention `mvp-pipeline-build.md` itself establishes.
> Amends **ADR-002** (`docs/decisions/ADR-002-apify-job-scraping.md`) — no new ADR is filed, per
> Tebello's explicit decision and this project's amend-rather-than-edit convention for historical ADRs
> (see the match-result and security-correction notes already appended to `docs/todo.md`'s Resolved
> Items / Phase 5 notes).

---

## Goal

Add PNet and Careers24 as vacancy sources to Stage 2 (Vacancy Fetch), closing the coverage gap
ADR-002 explicitly deferred ("neither has a dedicated Apify actor as of this decision"). Since no
dedicated Apify actor exists for either site, this uses Apify's **generic** `website-content-crawler`
actor (the same actor `ai-outreach-agency/src/research/apify_client.py` already calls) to fetch raw
page content, then a **local Ollama (`qwen3:8b`) extraction pass** to turn that raw content into
structured `Vacancy` fields — normalized into the existing schema alongside the two dedicated-actor
sources (Indeed, LinkedIn) already built in Phase 3.

Three decisions are fixed inputs, already confirmed by Tebello, not re-litigated here:

1. Documented as a **dated amendment to ADR-002**, not a new ADR (step 68).
2. Extraction LLM backend: **local Ollama, `qwen3:8b`** — reuses the existing backend from Phase 4
   (AI Matching), accepting the known reliability risk already noted in ADR-003, gated behind strict
   output validation and a dedicated typed exception on malformed output (`VacancyExtractionError`).
3. Seed-URL configuration is **generic and parameterized** — the crawler client takes seed URLs
   (or a config file mapping platform → seed URLs) as configuration, never literal PNet/Careers24
   URLs hardcoded into source. Tebello supplies real seed URLs later via `data/crawler_seed_urls.json`
   or an env override; no code change required at that point.

A fourth judgment call this spec resolves (not previously decided, Planner's call, justified inline):
**promote `ollama_client.py` from `src/matching/` to `src/shared/`.** ADR-003 §Alternatives.D rejected
`shared/` placement *only* because matching was Ollama's sole consumer at the time, and explicitly
said: *"Promote later if a second consumer appears."* The extraction step in this spec (§Phase 12)
is exactly that second consumer. Per ADR-003's own stated rule, the promotion is in scope for this
spec (steps 55–56) and is not itself a new architectural decision — it's ADR-003 executing on its own
already-stated condition. This is called out explicitly in the ADR-002 amendment (step 68) so a future
reviewer sees why `shared/ollama_client.py` exists without re-reading ADR-003 in full.

---

## Acceptance Criteria

- `career-engine fetch-vacancies` returns `Vacancy` records sourced from Indeed, LinkedIn, PNet, and
  Careers24, deduplicated on `(company, title, url)` across all four sources combined, truncated to
  `--limit`, exactly the same combined-flow contract Phase 3 already established for the first two
  sources.
- `Vacancy.schema.py`'s `VALID_PLATFORMS` accepts `"pnet"` and `"careers24"` in addition to the
  existing `"indeed"`/`"linkedin"` — confirmed as a **Python dataclass validation set only**, not a DB
  schema change (see Migration Note below).
- A new `src/vacancy_search/crawler_client.py` fetches raw page content via Apify's generic
  `website-content-crawler` actor, following the `OFFLINE_MODE` fixture / rate-limiter / config
  conventions already proven in `apify_client.py`.
- A new extraction step (`src/vacancy_search/extractor.py` + `extraction_prompt.py`) turns raw crawler
  output into `Vacancy`-shaped fields via `src/shared/ollama_client.py::call_ollama()` (its second
  consumer, post-promotion), with strict JSON-schema-shaped prompting and parse-and-validate logic
  that raises `VacancyExtractionError` on any malformed/incomplete output — no vacancy with missing
  required fields (`company`, `title`, `url`) is ever silently accepted.
- Seed URLs live in `data/crawler_seed_urls.json` (generic placeholders committed; Tebello swaps in
  real URLs later, no code change needed) — never hardcoded literal PNet/Careers24 URLs in
  `crawler_client.py` itself.
- `src/shared/ollama_client.py` exists (moved from `src/matching/`); `src/matching/scorer.py` imports
  from the new location; no remaining `src.matching.ollama_client` import anywhere in `src/` or
  `tests/`.
- Full test suite (`python -m pytest`) still passes fully offline — no real HTTP to the Apify crawler
  endpoint, no real HTTP to `localhost:11434`, matching the existing `OFFLINE_MODE` convention.
- `black . && ruff check .` clean; coverage ≥ 80% on all new `src/` code (project-wide standard,
  `CLAUDE.md` Testing Standards).
- `docs/decisions/ADR-002-apify-job-scraping.md` carries a dated amendment section (not a rewrite of
  its original Decision/Consequences) documenting this coverage.
- `docs/api-patterns.md` and `CLAUDE.md` reflect the new crawler client, the extraction step, and the
  `ollama_client.py` relocation.

---

## Out of Scope (do not build)

- Real seed URLs for PNet/Careers24 — `data/crawler_seed_urls.json` ships with generic placeholder
  URLs only; Tebello supplies real ones later via config, not a code change.
- Any change to the Indeed/LinkedIn dedicated-actor code paths in `apify_client.py` beyond folding the
  two new sources into the existing combined dedupe/truncate flow.
- Any change to `src/matching/scorer.py`'s scoring logic or prompt — only its `ollama_client` import
  path changes (step 56).
- A DB migration for `VALID_PLATFORMS` — confirmed unnecessary; see Migration Note below.
- Volume-cap / scheduler machinery for the crawler or extraction calls — no documented throttling
  requirement beyond the standard per-client rate limiter, mirroring the same judgment call ADR-003 §6
  already made for doc-gen.
- Any change to `ai-outreach-agency/` (read-only pattern reference for the crawler actor call shape).
- Re-verifying or re-confirming the Indeed/LinkedIn actor slugs (already confirmed 2026-07-26,
  unaffected by this spec).

---

## Migration Note (flagged per Hard Rule #6 — "No schema changes without a migration file")

`src/vacancy_search/schema.py`'s `VALID_PLATFORMS = {"indeed", "linkedin"}` is a **Python-level
dataclass validation set**, checked in `Vacancy.__post_init__()` — it is not a database constraint.
`src/vacancy_search/db.py`'s `vacancies.platform` column is plain `TEXT NOT NULL` with **no `CHECK`
constraint** (confirmed by reading the committed `db.py`). Adding `"pnet"` and `"careers24"` to this
set (step 59) changes what Python accepts before a row is ever written; it does not alter the table
definition, add a column, or require `src/vacancy_search/migrations.py` to gain an entry. Hard Rule #6
does not apply here. This is stated explicitly, in-file (a code comment on `VALID_PLATFORMS`) and in
the ADR-002 amendment (step 68), so a future reviewer doesn't need to re-derive this and doesn't
second-guess it as a missed migration.

---

## Dependency Ordering (phase-level)

```
Phase 9 (shared ollama_client promotion — prerequisite)
   └─▶ Phase 10 (schema + seed-URL config)
          └─▶ Phase 11 (crawler_client.py — raw page fetch)
                 └─▶ Phase 12 (extraction — consumes src/shared/ollama_client.py from Phase 9)
                        └─▶ Phase 13 (fold into apify_client.py::fetch_vacancies())
                               └─▶ Phase 14 (docs closeout: ADR-002 amendment, api-patterns.md,
                                             CLAUDE.md, .env.example, docs/todo.md Build Queue)
```

Phase 9 must land first: Phase 12's extraction step imports `src.shared.ollama_client`, not
`src.matching.ollama_client` — building extraction against the old path and moving the client later
would mean touching `extractor.py`'s import twice for no reason. Within each phase, RED steps land
before their paired GREEN step (hard TDD ordering, same as `mvp-pipeline-build.md`).

---

## Files to Change (by module, final state)

```
src/shared/ollama_client.py        (moved from src/matching/ollama_client.py)
src/matching/scorer.py             (import path only)
src/vacancy_search/schema.py       (VALID_PLATFORMS addition)
src/vacancy_search/crawler_client.py   (new)
src/vacancy_search/extraction_prompt.py (new)
src/vacancy_search/extractor.py    (new — VacancyExtractionError lives here)
src/vacancy_search/apify_client.py (fetch_vacancies() integration)
data/crawler_seed_urls.json        (new — placeholder seed-URL config)
.env.example                       (CRAWLER_RATE_LIMIT_PER_MIN)
docs/decisions/ADR-002-apify-job-scraping.md  (amendment section appended)
docs/api-patterns.md               (new section + Ollama section path update)
CLAUDE.md                          (External Client Patterns table, Directory Structure)
docs/todo.md                       (new Build Queue phase, steps 55–72; remove stale Future/Known-Issues lines)
tests/unit/test_ollama_client.py   (import path update)
tests/unit/test_vacancy_schema.py  (pnet/careers24 cases)
tests/unit/test_crawler_client.py  (new)
tests/unit/test_vacancy_extraction.py (new)
tests/unit/test_apify_client.py    (extended)
```

No task below touches more than 2 files (test-file-only RED steps count as 1; the ollama_client move
pairs the moved file with `scorer.py`'s import update, the maximum allowed 2).

---

## Task Plan

Legend: **[RED]** = write failing test(s) first. **[GREEN]** = minimal implementation to pass.
**Network** = `none` (fully offline, always) or `Apify`/`Ollama` (required for real runs; tests still
run offline via the `OFFLINE_MODE` fixture).

### Phase 9 — Promote `ollama_client.py` to `src/shared/` (ADR-003 §Alternatives.D's own trigger)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 55 | **[RED]** `tests/unit/test_ollama_client.py` — update the import from `src.matching.ollama_client` to `src.shared.ollama_client`; no behavioral test changes. | tester | `src/matching/ollama_client.py` (current), ADR-003 §Alternatives.D | `tests/unit/test_ollama_client.py` (updated) | `python -m pytest tests/unit/test_ollama_client.py` fails with `ModuleNotFoundError: src.shared.ollama_client` (RED confirmed) | none |
| 56 | **[GREEN]** Move `src/matching/ollama_client.py` → `src/shared/ollama_client.py` (`git mv`, preserves history); update `src/matching/scorer.py`'s import to `from src.shared.ollama_client import call_ollama`. No other logic changes — same `RateLimiter`, `OllamaError`/`OllamaUnreachableError`, `CONNECT_TIMEOUT`/`READ_TIMEOUT` constants, unchanged. | executor | `tests/unit/test_ollama_client.py` (step 55), `src/matching/scorer.py` | `src/shared/ollama_client.py`, `src/matching/scorer.py` (import updated) | `python -m pytest tests/unit/test_ollama_client.py tests/unit/test_matching.py` passes; `grep -r "src.matching.ollama_client" src/ tests/` returns no matches | none |
| 57 | Update `CLAUDE.md`'s "🌐 External Client Patterns" table row (`matching/ollama_client.py` → `shared/ollama_client.py`, note it now has two consumers: `matching/scorer.py` and the new `vacancy_search/extractor.py` from Phase 12) and the Directory Structure tree (`src/shared/` gains `ollama_client.py`, `src/matching/` loses it). | doc-writer | `src/shared/ollama_client.py` (step 56) | `CLAUDE.md` (updated) | Read-check: table and directory tree match the actual post-move file layout | none |

### Phase 10 — Schema Addition + Seed-URL Config

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 58 | **[RED]** `tests/unit/test_vacancy_schema.py` — add cases: `Vacancy(..., platform="pnet")` and `Vacancy(..., platform="careers24")` both construct without raising; an unrelated invalid platform (e.g. `"glassdoor"`) still raises `ValueError`; existing `"indeed"`/`"linkedin"` cases untouched. | tester | `src/vacancy_search/schema.py` (current `VALID_PLATFORMS`) | `tests/unit/test_vacancy_schema.py` (updated) | `python -m pytest tests/unit/test_vacancy_schema.py` fails on the new `pnet`/`careers24` cases (RED confirmed) | none |
| 59 | **[GREEN]** `src/vacancy_search/schema.py` — `VALID_PLATFORMS = {"indeed", "linkedin", "pnet", "careers24"}`, with an inline comment stating this is a Python-level validation set, not a DB constraint (`db.py`'s `platform` column is plain `TEXT NOT NULL`, no `CHECK` — no migration required, per this spec's Migration Note). | executor | `tests/unit/test_vacancy_schema.py` (step 58) | `src/vacancy_search/schema.py` (updated) | `python -m pytest tests/unit/test_vacancy_schema.py` passes fully | none |
| 60 | `data/crawler_seed_urls.json` — generic placeholder config: `{"pnet": ["https://example.co.za/pnet-placeholder"], "careers24": ["https://example.co.za/careers24-placeholder"]}`, with a top-level `"_comment"` field stating these are placeholders and must be replaced with real seed URLs before a non-`OFFLINE_MODE` crawl of that platform (per Tebello's decision — no real URLs baked into source or this file yet). | data-agent | none (new config file) | `data/crawler_seed_urls.json` | `python -c "import json; json.load(open('data/crawler_seed_urls.json'))"` parses cleanly; keys `"pnet"`/`"careers24"` present | none |

### Phase 11 — Crawler Client (Apify `website-content-crawler`)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 61 | **[RED]** `tests/unit/test_crawler_client.py` — `OFFLINE_MODE` fixture returns 2–3 fake raw-page dicts (`{"url", "title", "text_content"}` shape, mirroring `ai-outreach-agency/research/apify_client.py`'s `FIXTURE`); real-call path mocks `requests.post` against the `apify~website-content-crawler` actor URL; module-level `RateLimiter.acquire()` called before every real request (`CRAWLER_RATE_LIMIT_PER_MIN`); missing `APIFY_API_KEY` triggers `warnings.warn` + fallback to fixture, **not** a raised exception — this deliberately mirrors `apify_client.py`'s graceful-degradation convention (ADR-002), not `ollama_client.py`'s fail-loud convention, because `crawler_client.py` lives in the same Stage-2 vacancy-fetch module that already established graceful degradation as its failure philosophy; seed URLs are read from `data/crawler_seed_urls.json` (loadable via an injectable path param for testing), never hardcoded literal URLs in the module. | tester | `ai-outreach-agency/src/research/apify_client.py` (pattern reference), `src/vacancy_search/apify_client.py` (sibling convention reference), `data/crawler_seed_urls.json` (step 60) | `tests/unit/test_crawler_client.py` | Fails with `ModuleNotFoundError` (RED confirmed) | none |
| 62 | **[GREEN]** `src/vacancy_search/crawler_client.py` — `fetch_raw_pages(platform, limit, seed_urls_path="data/crawler_seed_urls.json")` loads seed URLs for `platform` from the config file, calls Apify's `apify~website-content-crawler` actor (`run-sync-get-dataset-items`) once per seed URL, uses `src/shared/rate_limiter.py`'s `RateLimiter` (`CRAWLER_RATE_LIMIT_PER_MIN`, default `30`), `OFFLINE_MODE` fixture per step 61, graceful fallback-to-fixture on missing key or `(requests.RequestException, ValueError)` (swallowed per-call, mirroring `apify_client.py`'s existing `except ...: pass` convention exactly — same module, same philosophy). Returns raw page dicts, not `Vacancy` objects — extraction (Phase 12) is a separate concern. | executor | `tests/unit/test_crawler_client.py` (step 61), `src/shared/rate_limiter.py`, `data/crawler_seed_urls.json` | `src/vacancy_search/crawler_client.py` | `python -m pytest tests/unit/test_crawler_client.py` passes | Apify (real calls only; tests offline, mock `requests.post`) |

### Phase 12 — LLM Extraction (local Ollama, strict validation)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 63 | **[RED]** `tests/unit/test_vacancy_extraction.py` — `build_extraction_prompt(raw_page_text, platform)` produces a JSON-schema-shaped instruction (explicitly lists the required output keys: `company`, `title`, `description`, `url`, `salary`, `deadline`); `extract_vacancy_fields(raw_page, platform)` calls a mocked `call_ollama`, parses a well-formed JSON response into a dict with those keys; a response missing `company`/`title`/`url` (the `Vacancy` `REQUIRED_FIELDS`), or non-JSON text, raises `VacancyExtractionError`; `OFFLINE_MODE` returns a deterministic fixture extraction without calling `call_ollama` at all. | tester | `src/vacancy_search/schema.py`'s `REQUIRED_FIELDS` (step 59's file, unchanged tuple), `src/matching/scorer.py`'s `MatchParseError` (pattern reference only — different domain, not reused) | `tests/unit/test_vacancy_extraction.py` | Fails with `ModuleNotFoundError` (RED confirmed) | none |
| 64 | **[GREEN]** `src/vacancy_search/extraction_prompt.py` — pure function `build_extraction_prompt(raw_page_text, platform)`, no network, no DB. | executor | `tests/unit/test_vacancy_extraction.py` (step 63) | `src/vacancy_search/extraction_prompt.py` | `python -m pytest tests/unit/test_vacancy_extraction.py -k prompt` (or equivalent subset) passes | none |
| 65 | **[GREEN]** `src/vacancy_search/extractor.py` — `extract_vacancy_fields(raw_page, platform)` consumes `src.shared.ollama_client.call_ollama` (its **second** consumer, post Phase 9 promotion); strict `json.loads` + required-field check against `Vacancy.REQUIRED_FIELDS`; raises `VacancyExtractionError(ValueError)` (defined in this file — distinct from `matching/scorer.py`'s `MatchParseError`, a different domain: malformed *LLM extraction of a scraped page*, not a malformed *match score*) on any parse or missing-field failure; `OFFLINE_MODE` checked before any `call_ollama` invocation. | executor | `tests/unit/test_vacancy_extraction.py` (step 63), `src/vacancy_search/extraction_prompt.py` (step 64), `src/shared/ollama_client.py` (step 56) | `src/vacancy_search/extractor.py` | `python -m pytest tests/unit/test_vacancy_extraction.py` passes fully | Ollama (via `call_ollama`; real calls only; tests offline, mock `call_ollama`) |

### Phase 13 — Fold into `fetch_vacancies()`

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 66 | **[RED]** `tests/unit/test_apify_client.py` — extend: `fetch_vacancies(limit)` now also calls `crawler_client.fetch_raw_pages` + `extractor.extract_vacancy_fields` for `"pnet"` and `"careers24"`, folding resulting `Vacancy` objects into the **existing** dedupe-by-`(company, title, url)`-and-truncate-to-`limit` flow alongside Indeed/LinkedIn results (all four sources combined before dedupe, not deduped separately then merged); a `VacancyExtractionError` raised while processing one raw page is caught and that page is skipped (logged), it must **not** abort the rest of the batch — mirrors the per-call swallow convention already used for Indeed/LinkedIn HTTP errors in the same function. | tester | `src/vacancy_search/apify_client.py` (current), `src/vacancy_search/crawler_client.py` (step 62), `src/vacancy_search/extractor.py` (step 65) | `tests/unit/test_apify_client.py` (updated) | Fails — new pnet/careers24 assertions don't yet pass (RED confirmed) | none |
| 67 | **[GREEN]** `src/vacancy_search/apify_client.py` — `fetch_vacancies()` folds in `crawler_client.fetch_raw_pages("pnet", limit)` + `crawler_client.fetch_raw_pages("careers24", limit)`, runs each raw page through `extractor.extract_vacancy_fields`, catches `VacancyExtractionError` per-page (skip + continue, does not abort the batch), constructs `Vacancy` objects from the extracted fields, and combines them with the existing Indeed/LinkedIn results before the single shared `_dedupe(...)[:limit]` call already in this function. | executor | `tests/unit/test_apify_client.py` (step 66) | `src/vacancy_search/apify_client.py` (updated) | `python -m pytest tests/unit/test_apify_client.py` passes fully | Apify + Ollama (via `crawler_client`/`extractor`; real calls only; tests offline) |

### Phase 14 — Docs Closeout

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 68 | Append a **dated amendment section** (`## Amendment — 2026-07-29`) to `docs/decisions/ADR-002-apify-job-scraping.md` — does **not** rewrite the original Decision/Consequences sections (historical record preserved, same convention as the match-result and security-correction notes already in `docs/todo.md`). Documents: PNet/Careers24 now covered via the generic `website-content-crawler` actor + local Ollama (`qwen3:8b`) extraction; `ollama_client.py` promoted `matching/` → `shared/` per ADR-003 §Alternatives.D's own stated trigger (second consumer appeared); seed URLs are parameterized config (`data/crawler_seed_urls.json`), never hardcoded; `VALID_PLATFORMS` addition is confirmed non-schema (no migration — see this spec's Migration Note); new `VacancyExtractionError` exception type. | architect | This spec, ADR-002 (original), ADR-003 §Alternatives.D | `docs/decisions/ADR-002-apify-job-scraping.md` (amended) | Read-check: original sections byte-identical above the amendment marker; amendment section present, dated, self-contained | none |
| 69 | Update `docs/api-patterns.md` — add a new "PNet/Careers24 (Generic Crawler + Local LLM Extraction)" section documenting `crawler_client.py` (actor URL, `CRAWLER_RATE_LIMIT_PER_MIN` default `30`, `OFFLINE_MODE` fixture, graceful-degradation-not-fail-loud convention) and `extractor.py` (`VacancyExtractionError`, strict JSON validation, `OFFLINE_MODE` fixture); update the existing "Local Ollama Inference" section to reference `src/shared/ollama_client.py` (not `src/matching/`) and note it now has two consumers (`matching/scorer.py`, `vacancy_search/extractor.py`). | doc-writer | `src/vacancy_search/crawler_client.py`, `src/vacancy_search/extractor.py`, `src/shared/ollama_client.py` | `docs/api-patterns.md` (updated) | Read-check: matches actual implemented function signatures and constants, no invented endpoints | none |
| 70 | `.env.example` — add `CRAWLER_RATE_LIMIT_PER_MIN=30` (non-secret integer default, same reasoning as the existing rate-limit placeholders). | executor | `.env.example` (current) | `.env.example` (updated) | Manual read-check: no real secrets added, new var present with a sane default | none |
| 71 | Update `CLAUDE.md`'s "🌐 External Client Patterns" table — add `vacancy_search/crawler_client.py` row (`Mirrors research/apify_client.py's generic-crawler pattern | 30 / min | CRAWLER_RATE_LIMIT_PER_MIN`) and update the Apify bullet in the same section to note PNet/Careers24 are now covered via the generic crawler + extraction, not deferred. Also update the Directory Structure tree: `src/vacancy_search/` gains `crawler_client.py`, `extraction_prompt.py`, `extractor.py`; `data/` gains `crawler_seed_urls.json`. | doc-writer | `src/vacancy_search/crawler_client.py`, `src/vacancy_search/extractor.py`, `data/crawler_seed_urls.json` | `CLAUDE.md` (updated) | Read-check: table, bullet, and directory tree match actual post-build file layout | none |
| 72 | `docs/todo.md` — add "Phase 9–14: PNet/Careers24 Coverage" as a new, active Build Queue section (steps 55–72) cross-referencing this spec, per the project's established "spec before build" convention (the MVP spec itself states it "supersedes the unordered items in `docs/todo.md`'s old Build Queue section" once written). Remove the now-superseded `- [ ] No dedicated Apify actor exists for PNet or Careers24 ...` line from "Known Issues" and the `- [ ] PNet/Careers24 coverage via generic Apify crawler + LLM extraction.` line from "Future" — both are now scheduled, atomic, spec-backed tasks, not open-ended future items. | doc-writer | This spec (all steps 55–72) | `docs/todo.md` (updated) | Read-check: new Build Queue phase present with correct step numbers/descriptions; stale Known-Issues/Future lines removed, no duplicate tracking of the same work in two places | none |

---

## Verification Summary (run before considering this coverage "done")

```bash
cd TebelloReborn
black . && ruff check .
python -m pytest                 # full suite, offline, must be 100% green
python -m pytest --cov=src --cov-report=term-missing   # ≥80% on new code
grep -r "src.matching.ollama_client" src/ tests/   # must return nothing
career-engine fetch-vacancies --limit 10   # OFFLINE_MODE=true for a dry run without Apify/Ollama
```

---

## Open Items Flagged for Architect / User (not blocking start, but need an answer before the
## affected step is merged)

1. **Real seed URLs for PNet/Careers24** (step 60) — this spec ships only generic placeholders.
   Tebello must supply real seed URLs in `data/crawler_seed_urls.json` (or an env-based override, if
   preferred at that point) before the first non-`OFFLINE_MODE` crawl of either platform actually
   returns anything useful. Not a blocker for the build itself — every test in this spec runs offline.
2. **Extraction reliability at scale** — `qwen3:8b`'s known reliability risk (already noted in
   ADR-003 for AI Matching) applies here too, and a job-posting page's raw text is messier and more
   variable than the two dedicated-actor JSON payloads. Strict validation (`VacancyExtractionError`)
   catches malformed output but does not improve extraction *accuracy* — if real-world runs show a
   high `VacancyExtractionError` rate, that is signal for prompt-tuning or a stronger local model, not
   evidence this spec's design is wrong. Flagged for a future evidence-based revisit, not resolved here.
3. **`CRAWLER_RATE_LIMIT_PER_MIN` default of 30** mirrors `APIFY_RATE_LIMIT_PER_MIN` (same underlying
   Apify platform, generic-actor calls are typically heavier than dedicated-actor calls). Confirm this
   default is conservative enough once real seed URLs are in use — easy to override via env either way.

---

## Codex second opinion (advisory) — 2026-07-29

**Second-Opinion Review**

The spec is directionally sound, especially on preserving ADR history, keeping seed URLs configurable, and isolating crawler fetch from LLM extraction. I would not rubber-stamp it as-is, though. The main weaknesses are not in the file list or TDD sequencing; they are in assumptions about what the generic crawler returns, what "coverage" means, and how failures are surfaced.

**Buried Assumptions**

1. The biggest hidden assumption is that Apify's generic `website-content-crawler` output can reliably produce vacancy-level records. The spec says it will "fetch raw page content" and then "turn that raw content into structured `Vacancy` fields," but does not distinguish search-result pages, listing pages, paginated pages, and individual job-detail pages. If the seed URL points at a search page containing 20 jobs, the extractor contract appears to produce one vacancy per raw page, which may silently lose most listings.

2. "Add PNet and Careers24 as vacancy sources" overstates what placeholder seed URLs deliver. The implementation can add source plumbing, but not actual source coverage until real seed URLs exist and are tested. The acceptance criterion that `career-engine fetch-vacancies` returns PNet/Careers24 records is not truly satisfiable with the planned placeholder config except via fixtures.

3. The spec assumes generic crawler usage is legally and operationally acceptable for PNet/Careers24. It does not mention robots.txt, terms of service, login walls, anti-bot handling, location filtering, or whether Apify can fetch these pages consistently.

4. It assumes `qwen3:8b` is available locally wherever the pipeline runs. The spec references "local Ollama, `qwen3:8b`" as fixed, but acceptance criteria only require offline tests. There is no real-run readiness check for model presence, Ollama health, timeout behavior, or model mismatch.

5. It assumes graceful fallback to fixtures is acceptable in production-like runs. Step 62 says missing `APIFY_API_KEY` or request failures fall back to fixture. That can make real commands look successful while returning fake vacancies. This is dangerous for a vacancy pipeline unless the returned records are visibly marked as fixtures or the CLI reports degraded mode.

**Missing Or Untestable Acceptance Criteria**

1. "PNet and Careers24 coverage" needs a concrete meaning. Add criteria like: given a configured seed URL that points to a search results page with multiple jobs, the pipeline extracts N vacancies, preserves the source URL, and does not collapse unrelated listings into one record.

2. The spec says "strict JSON-schema-shaped prompting," but tests only check required keys and JSON parsing. There is no criterion for schema types, URL validity, empty-string required fields, platform correctness, or extra hallucinated fields.

3. Deduplication on `(company, title, url)` is clear, but normalization is underspecified. Are company/title case folded? Are URLs canonicalized by stripping UTM params, fragments, trailing slashes, or redirect wrappers? Without this, the dedupe criterion is technically testable but weak.

4. "No vacancy with missing required fields is ever silently accepted" misses blank or garbage fields. `{ "company": "N/A", "title": "", "url": "unknown" }` could pass unless explicitly rejected.

5. "Full test suite still passes fully offline" is good, but there is no acceptance test for a non-offline dry run with mocked Apify plus mocked Ollama through the CLI. The top-level command behavior is the actual product surface.

6. Coverage "≥ 80% on all new `src/` code" is vague unless the tooling enforces per-file or diff coverage. `pytest --cov=src` only reports project/module totals unless configured otherwise.

**Failure Modes Not Considered**

1. A crawler page may contain multiple vacancies. The current extractor shape appears one raw page to one vacancy.

2. A crawler page may contain no vacancy, expired jobs, promoted jobs, navigation text, cookie banners, or unrelated content. The spec does not define "no vacancy found" separately from malformed extraction.

3. The LLM may return valid JSON with wrong facts. Strict validation catches shape, not factual extraction errors. The open item acknowledges accuracy risk, but the implementation has no sampling/audit path, confidence field, or raw-source trace.

4. Apify actor output shape may differ from `{"url", "title", "text_content"}`. Generic crawlers often vary fields by actor version or configuration. The spec should define a normalization layer and fixture based on actual actor output.

5. Long raw pages can exceed Ollama context limits or cause slow extraction. There is no truncation strategy, chunking rule, max input length, timeout, or retry behavior.

6. Graceful degradation can hide systemic outage. If both new sources fail and fixtures are returned, the pipeline may report fake success.

7. Rate limiting "once per seed URL" ignores the actor's internal crawl depth. One actor invocation may fan out into many page fetches, so `CRAWLER_RATE_LIMIT_PER_MIN=30` may not correspond to site pressure or Apify cost.

8. The spec does not mention source attribution or observability. When `VacancyExtractionError` is caught and skipped, "logged" is mentioned in step 66, but no acceptance criterion checks log content, counts, or summary reporting.

**Architectural Alternatives I Would Seriously Weigh**

1. Use site-specific lightweight parsers after generic crawling, with LLM fallback only for ambiguous pages.
   Reason: PNet and Careers24 likely have repeated HTML structures. A deterministic parser is cheaper, faster, easier to test, and less likely to hallucinate. The LLM can remain a fallback for description cleanup.

2. Split discovery from extraction.
   Instead of `fetch_raw_pages(platform, limit)` returning arbitrary raw pages, create two explicit stages: `discover_job_urls(platform, seed_urls)` and `fetch_job_pages(job_urls)`. This addresses the search-page versus detail-page ambiguity and gives better dedupe before expensive extraction.

3. Add a `source_mode` or `is_fixture` marker.
   If the design keeps graceful fallback, returned vacancies should carry metadata or the CLI should warn loudly. Otherwise placeholder or fixture data can pollute downstream matching.

4. Keep `ollama_client.py` promotion, but introduce an extraction-specific wrapper.
   Moving the shared client is reasonable. However, `extractor.py` should probably own timeout/model/default prompt behavior rather than calling a generic `call_ollama()` directly everywhere. That keeps shared code thin and domain behavior local.

5. Consider storing raw crawler artifacts for audit.
   Even if not in the main DB, saving raw page snapshots or normalized raw-page JSON under `data/` during non-offline runs would make extraction errors debuggable and support prompt tuning.

**Bottom Line**

The spec is implementable, but the term "coverage" is premature. As written, it builds plumbing and offline-fixture behavior more than verified PNet/Careers24 vacancy coverage. I would approve the structure after tightening acceptance criteria around multi-listing pages, no-vacancy pages, fixture/degraded-mode visibility, URL normalization, real actor output shape, and end-to-end CLI behavior with mocked crawler plus mocked Ollama.

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._

---

## Amendment — Codex Review Follow-up (2026-07-29)

Per this project's amend-rather-than-rewrite convention (same as the ADR-002 amendment this spec
itself will produce at step 68), the three strongest points from the Codex second opinion above are
folded in here as **additions/modifications to the Task Plan and Acceptance Criteria**, not as edits
to the original sections — the original Goal/Acceptance Criteria/Task Plan above remain the historical
record of what was first planned.

**1. Multi-listing vs. job-detail-page ambiguity (Codex's strongest point).**
The original spec never stated whether a seed URL points at a search-results page (many jobs) or a
single job-detail page — `fetch_raw_pages` → `extract_vacancy_fields` implicitly assumed one raw page
= one vacancy, which would silently under-count real PNet/Careers24 listings.

- **Resolved by scoping, not by adding a discovery stage** (Codex's Alternative #2 — splitting
  `discover_job_urls`/`fetch_job_pages` — is a reasonable future direction but is out of scope for this
  MVP-extension spec; flagged below as a Future item instead of expanding this build).
- **New Acceptance Criterion**: `data/crawler_seed_urls.json`'s seed URLs MUST be individual job-detail
  page URLs (one vacancy per page), never search-results/listing pages. This is enforced as a doc
  comment in the config file (step 60) and stated explicitly in `docs/api-patterns.md` (step 69).
- **Modifies step 61's test**: add a case asserting `extract_vacancy_fields` on a fixture page
  containing what looks like multiple job listings still returns exactly one `Vacancy` (documenting
  the one-page-one-vacancy contract as intentional, not an oversight) — this is a **contract test**,
  not a multi-listing parser.
- **New Future item** (added to `docs/todo.md`'s Future section by step 72, not built here): "Search
  page discovery stage (`discover_job_urls`) for PNet/Careers24 — needed if seed URLs must be
  search-result pages rather than direct job-detail links once Tebello supplies real URLs."

**2. Fixture/degraded-mode visibility (Codex's second point).**
Original step 62 fell back to fixture data on missing `APIFY_API_KEY` or request failure with only a
`warnings.warn` — a real run could look successful while silently returning fake vacancies.

- **New field, transient only (no schema/DB footprint)**: `crawler_client.fetch_raw_pages()` tags each
  returned raw-page dict with `"_source_mode": "live" | "fixture"` — an internal pipeline field, never
  written to the `vacancies` table or the `Vacancy` dataclass (no migration implication, consistent
  with this spec's existing Migration Note stance).
- **Modifies step 67's `fetch_vacancies()`**: counts how many raw pages (across all sources, not just
  the new two) came back tagged `"fixture"` during a **non-`OFFLINE_MODE`** run, and logs a single
  `logger.warning(...)` summary line (e.g. `"3 of 8 vacancy-source pages returned fixture data — check
  APIFY_API_KEY / network"`) if that count is non-zero. `OFFLINE_MODE=true` runs never trigger this
  (all data is expected to be fixture there).
- **New Acceptance Criterion**: a real (non-`OFFLINE_MODE`) `fetch_vacancies()` call that degrades to
  fixture data for any source logs a visible warning; this is unit-tested by asserting the log call,
  not by capturing real degraded output.

**3. URL normalization before dedupe (Codex's third point, narrower fix than proposed).**
The existing `(company, title, url)` dedupe key has no normalization — UTM params, trailing slashes,
or fragments on an otherwise-identical URL would defeat dedup.

- **New function**: `normalize_url(url)` in `src/vacancy_search/apify_client.py` (or a small shared
  helper if `crawler_client.py` needs it too) — strips query string, fragment, and trailing slash
  before building the dedupe key.
- **Scope note**: this changes the shared `_dedupe()` helper that **all four sources** (Indeed,
  LinkedIn, PNet, Careers24) already pass through, not just the two new ones. This is judged in-scope
  under the Out-of-Scope section's existing carve-out ("folding the two new sources into the existing
  combined dedupe/truncate flow") because the two new sources cannot dedupe correctly *without* this
  fix — it is a prerequisite for the new sources working, not an unrelated Indeed/LinkedIn change.
  Existing Indeed/LinkedIn behavior is unaffected in practice (their URLs already come pre-normalized
  from each dedicated actor), so no regression is expected, but the shared function itself changes.
- **New test**: `tests/unit/test_apify_client.py` gains a case asserting two vacancies whose URLs
  differ only by a UTM query string or trailing slash are treated as duplicates.

**Also folded in (validation tightening, Codex's "missing acceptance criteria" #4):**
`VacancyExtractionError` (step 65) now also raises on **empty-string** required fields (`company`,
`title`, `url` present but `""`), not just missing keys — closes the `{"company": "N/A", "title": "",
"url": "unknown"}`-shaped gap Codex flagged. `"N/A"`-style garbage-but-present values are explicitly
**not** caught by this (a factual-accuracy problem, not a shape problem) — Codex's own point #3 under
Failure Modes ("valid JSON with wrong facts") is correctly identified as out of scope for strict
validation and is left as the existing "Extraction reliability at scale" open item, not resolved here.

**Not folded in (judgment call, left as-is):** Codex's Alternative #1 (site-specific lightweight
parsers instead of LLM extraction) and Alternative #5 (storing raw crawler artifacts for audit) are
reasonable but represent a larger scope change than "fold the strongest points" — both are added to
`docs/todo.md`'s Future section (step 72) as flagged follow-ups, not built in this spec.

---

## Amendment — Automated Discovery Redesign (2026-07-29)

### Why this amendment exists

The build paused before Phase 12 (step 63) because the original design (Phases 9–11 above, plus the
now-superseded Phases 12–14 at steps 63–72) requires Tebello to manually find and paste individual
real job-detail-page URLs into `data/crawler_seed_urls.json` before a crawl of PNet or Careers24
returns anything. That is manual job-search labor performed at the discovery stage — it contradicts
this project's actual goal (`CLAUDE.md`'s Pipeline Stages section: the pipeline "continuously finds
job vacancies," and the Hard Rule that the **only** mandatory human-involvement point is the Stage 5
approval gate, not vacancy discovery). Indeed/LinkedIn already achieve fully automated discovery via
`apify_client.py`'s `SEARCH_TITLES`/`SEARCH_LOCATION` module constants driving a dedicated Apify actor
with zero manual URL input per search. This amendment redesigns PNet/Careers24 discovery to mirror
that pattern instead of relying on hand-pasted seed URLs.

**What is preserved, unchanged, from history:** Phases 9–11 (steps 55–62) are already built and
committed and are **not** re-planned here — `src/shared/ollama_client.py`'s promotion, the
`VALID_PLATFORMS` addition, and `crawler_client.py`'s raw-fetch mechanics (rate limiting,
`OFFLINE_MODE` fixture, `_source_mode` tagging from the Codex Review Follow-up amendment above) are
all still needed by the redesigned flow and are reused, not rewritten.

**What is superseded:** the original Phases 12–14 task sequence at **steps 63–72** (LLM extraction,
fold-into-`fetch_vacancies()`, and docs closeout, as originally specced against a static
`data/crawler_seed_urls.json` populated by hand) is **replaced in full** by the new step sequence
below, continuing numbering from **63 onward** again (the old 63–72 rows above are historical record
of the first plan and are never built as written — `docs/todo.md`'s own "BLOCKED on discovery
redesign" annotations against steps 63–72 reflect this). The extraction and fold-in *logic* from the
original Phases 12–13 is not thrown away — it is carried forward essentially unchanged in Phase 13/14
below, fed by a different, automated URL *source* instead of a hand-maintained config file. This is
called out per-step below.

### Research this amendment is built on (confirmed live, 2026-07-29 — not guesswork)

- **PNet**: search-results URLs are predictable and parameterizable from `SEARCH_TITLES`/
  `SEARCH_LOCATION` — confirmed live shape `https://www.pnet.co.za/jobs/<title-slug>/in-<location-slug>`
  (e.g. `pnet.co.za/jobs/operations-foreman/in-gauteng`), which the site itself redirects a query-based
  search onto with `?radius=30&searchOrigin=Homepage_top-search` appended. PNet's live `robots.txt`
  `User-agent: *` block includes `Disallow: /jobs/*?*` — the exact query-string shape is explicitly
  disallowed for generic crawlers. The **bare path-only** shape (no `?`) is not covered by that rule,
  but this session could not confirm live whether it actually renders a working results page —
  repeated automated navigation to pnet.co.za began being denied partway through testing (an
  operational-fragility signal independent of robots.txt compliance).
- **Careers24**: confirmed live shape `https://www.careers24.com/jobs/lc-<location-slug>/kw-<keyword-slug>/rmt-incl/`
  (e.g. `careers24.com/jobs/lc-gauteng/kw-operations-foreman/rmt-incl/`). Careers24's `robots.txt` has
  no blanket `User-agent: *` rule — it names specific known scraper user-agents (Scrapy, assorted
  SEO/SEM bots, Baiduspider, etc.) and disallows `/` only for those. A generic crawler UA (Apify's
  `website-content-crawler` presents a standard browser UA) is not named, so it is not technically
  blocked, though the site's evident intent is anti-scraping.
- **Both URLs are search-results/listing pages** (potentially many jobs), not job-detail pages — this
  confirms the existing "one raw page = one `Vacancy`" hard contract (the `HARD CONTRACT` comment
  already in `data/crawler_seed_urls.json`, and the Codex Review Follow-up amendment's point 1 above)
  is architecturally incompatible with automated discovery as currently built. A genuine **discovery**
  sub-stage — parse the listing page, extract individual job-detail-page URLs, then crawl+extract each
  one — is required. This is Codex's own "Architectural Alternative #2" ("split discovery from
  extraction") from the second-opinion review above, which the prior amendment explicitly deferred to
  a Future item rather than building. That deferral is now reversed: this amendment builds it.

**Tebello's explicit decision this session (fixed input, not re-litigated):** "Respect Disallow, scope
down" —

- Careers24 gets full automated discovery (no robots.txt blocker).
- PNet's query-string shape (`?radius=...`) must **never** be constructed or crawled — explicitly
  robots.txt-disallowed.
- PNet's bare-path shape is unverified and gated behind a one-time **manual browser check** by Tebello
  (opening the URL once in an ordinary browser — not the per-vacancy manual URL-pasting labor this
  redesign exists to eliminate) before any build step relies on it working.
- **If the bare-path shape doesn't return a usable results page, PNet falls back to the original
  Phase 10 seed-URL design** (`data/crawler_seed_urls.json`, already built) for PNet only, while
  Careers24 stays fully automated. This is a legitimate per-platform fallback, wired in now via a
  config-driven branch rather than requiring a second redesign pass later.

### New judgment calls this amendment resolves (Planner's call, justified inline, same convention as the ollama_client.py promotion above)

1. **Listing-page URL-extraction is a deterministic parse, not an LLM call.** `parse_job_urls_from_listing()`
   (step 66) uses a plain regex/anchor-tag extraction over the raw listing page's `text_content`/HTML,
   not `src/shared/ollama_client.py::call_ollama()`. Reasoning: listing pages have a repeated,
   predictable anchor structure per platform (harvesting URLs is a structural task), whereas the
   existing Phase 13 extraction step (job-detail *field* extraction — company/title/description/salary
   from unstructured body text) is exactly the kind of unstructured-text task Ollama is already
   justified for in this spec. Using the LLM for URL harvesting would add `qwen3:8b`'s latency and
   reliability risk (ADR-003) to a job better solved deterministically, and was never asked for by
   Tebello.
2. **`crawler_client.py` gains a small refactor, not a duplicate fetch path.** The existing
   `fetch_raw_pages(platform, limit, seed_urls_path)` only knows how to crawl seed URLs pre-configured
   per platform in a JSON file — it has no way to crawl an arbitrary, freshly-constructed listing URL
   or a freshly-discovered job-detail URL. Rather than writing a second, parallel Apify-call block in
   `discovery.py` (copy-pasting the POST/timeout/`_source_mode`/exception-handling logic a second
   time), this amendment extracts the existing per-seed-URL fetch logic already inside
   `fetch_raw_pages`'s loop into a new `fetch_raw_page(url) -> dict` primitive (steps 63–64), which
   `fetch_raw_pages()` itself now calls internally (pure refactor, byte-identical outward behavior —
   regression-locked by the existing step-61/62 tests still passing unmodified). `discovery.py` then
   composes on top of that same primitive for both the listing-page fetch and each discovered
   job-detail-page fetch — "reuse the existing crawler_client.py raw-fetch mechanics," per this
   session's instruction, achieved via composition rather than duplication.
3. **The PNet manual-verification gate and fallback are config, not a code fork.** A new
   `data/discovery_config.json` (step 69) holds a `mode` per platform (`"auto"` or
   `"manual_pending_verification"`). `discovery.py::get_job_urls(platform, limit)` is the **single**
   entry point `apify_client.py::fetch_vacancies()` calls for both PNet and Careers24 — it branches
   internally on the config value, so no `if platform == "pnet"` special-casing exists in
   `apify_client.py`'s control flow (satisfies this session's explicit "config-driven branch, not a
   code fork" instruction). Careers24 has no gate (`mode` is irrelevant/always treated as `"auto"` for
   that platform — Careers24's `_comment` in the config documents this).

### New/changed step sequence — supersedes original steps 63–72 in full

Legend unchanged: **[RED]**/**[GREEN]** as above. **Network**: `none` / `Apify` / `Ollama`.

#### Phase 12 (redesigned) — Automated Discovery (Careers24 full-auto, PNet gated + fallback)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 63 | **[RED]** `tests/unit/test_crawler_client.py` — add `fetch_raw_page(url)` case: given a single URL, returns one raw-page dict (`{"url", "title", "text_content", "_source_mode"}`, same shape as one item of `fetch_raw_pages()`'s existing return), `OFFLINE_MODE` fixture branch, real-call path mocks `requests.post`; add a regression case asserting `fetch_raw_pages(platform, limit, seed_urls_path)`'s existing outward behavior (from step 61/62) is unchanged once refactored to call `fetch_raw_page()` internally. | tester | `src/vacancy_search/crawler_client.py` (current, step 62) | `tests/unit/test_crawler_client.py` (updated) | `python -m pytest tests/unit/test_crawler_client.py` fails on the new `fetch_raw_page` assertions only — existing step 61/62 assertions still pass unmodified against current code (RED confirmed for the new function only) | none |
| 64 | **[GREEN]** `src/vacancy_search/crawler_client.py` — extract the existing per-seed-URL POST/timeout/`_source_mode`/exception-handling block out of `fetch_raw_pages()`'s loop into `fetch_raw_page(url) -> dict`; `fetch_raw_pages()` now calls it once per seed URL — pure refactor, no behavior change (judgment call #2 above). | executor | `tests/unit/test_crawler_client.py` (step 63) | `src/vacancy_search/crawler_client.py` (updated) | `python -m pytest tests/unit/test_crawler_client.py` passes fully, including the pre-existing step 61/62 tests unmodified | Apify (real calls only; tests offline) |
| 65 | **[RED]** `tests/unit/test_discovery.py` (new file) — `build_search_url("careers24", title, location)` returns the confirmed live shape `https://www.careers24.com/jobs/lc-<location-slug>/kw-<keyword-slug>/rmt-incl/` for a given `SEARCH_TITLES`/`SEARCH_LOCATION` pair (slugification: lowercase, spaces→hyphens); `parse_job_urls_from_listing(raw_text, platform="careers24")` extracts a list of individual job-detail-page URLs from a fixture listing-page text/HTML blob (fixture authored as test input, mirroring this project's existing fixture conventions — not live-scraped content); `discover_job_urls("careers24", limit)` calls `crawler_client.fetch_raw_page()` on the constructed listing URL (mocked), then `parse_job_urls_from_listing()` on its `text_content`, returning up to `limit` job-detail URLs tagged with the listing fetch's own `_source_mode`; `OFFLINE_MODE` returns a deterministic fixture list without any fetch call. | tester | `src/vacancy_search/crawler_client.py::fetch_raw_page` (step 64), `src/vacancy_search/apify_client.py`'s `SEARCH_TITLES`/`SEARCH_LOCATION` (pattern reference) | `tests/unit/test_discovery.py` | Fails with `ModuleNotFoundError` (RED confirmed) | none |
| 66 | **[GREEN]** `src/vacancy_search/discovery.py` (new) — `build_search_url(platform, title, location)`, `parse_job_urls_from_listing(raw_text, platform)` (deterministic regex/anchor parse — judgment call #1 above, no `call_ollama` import), `discover_job_urls(platform, limit)` for `"careers24"`; no PNet logic yet (added step 68). | executor | `tests/unit/test_discovery.py` (step 65) | `src/vacancy_search/discovery.py` | `python -m pytest tests/unit/test_discovery.py -k careers24` (or equivalent subset) passes | Apify (via `fetch_raw_page`; real calls only; tests offline) |
| 67 | **[RED]** `tests/unit/test_discovery.py` — extend: `build_search_url("pnet", title, location)` returns **only** the bare path-only shape `https://www.pnet.co.za/jobs/<title-slug>/in-<location-slug>` — assert the returned string contains no `"?"` character under any input; a docstring/comment on the function names the specific rule being avoided (`PNet robots.txt: "Disallow: /jobs/*?*"`, confirmed live 2026-07-29) so a future editor can't reintroduce the disallowed query-string shape without seeing why it's forbidden. | tester | Live-read PNet `robots.txt` (this session's research, cited above) | `tests/unit/test_discovery.py` (updated) | Fails — `build_search_url("pnet", ...)` doesn't exist yet (RED confirmed) | none |
| 68 | **[GREEN]** `src/vacancy_search/discovery.py` (same file, extended) — `build_search_url("pnet", ...)` added (bare-path shape only; the function has no parameter or code path capable of appending a query string — the disallowed shape is structurally unreachable, not just avoided by convention). | executor | `tests/unit/test_discovery.py` (step 67) | `src/vacancy_search/discovery.py` (updated) | `python -m pytest tests/unit/test_discovery.py` passes fully; `grep -n "?" src/vacancy_search/discovery.py` shows no query-string construction for the `pnet` branch | none |
| 69 | `data/discovery_config.json` (new) — `{"pnet": {"mode": "manual_pending_verification"}, "careers24": {"mode": "auto"}}` with a top-level `"_comment"` explaining: `careers24` is always automated (no robots.txt blocker, confirmed 2026-07-29); `pnet` stays `"manual_pending_verification"` until Tebello manually opens the bare-path URL (see the new Open Item below) in an ordinary browser once and confirms it renders a usable results page — flip to `"auto"` only then; if it never renders usably, leave this value as `"manual_pending_verification"` permanently and `pnet` continues sourcing from `data/crawler_seed_urls.json` (already built, step 60) indefinitely — a supported, intentional end state, not a stopgap. | data-agent | This amendment's decision record (above) | `data/discovery_config.json` | `python -c "import json; json.load(open('data/discovery_config.json'))"` parses cleanly; keys `"pnet"`/`"careers24"` present, each with a `"mode"` field | none |
| 70 | **[RED]** `tests/unit/test_discovery.py` — extend: `get_job_urls("careers24", limit)` always calls `discover_job_urls("careers24", limit)` regardless of `discovery_config.json`'s content (no gate for this platform); `get_job_urls("pnet", limit)` with `discovery_config.json`'s `pnet.mode` set to `"manual_pending_verification"` returns the URLs already present in `data/crawler_seed_urls.json`'s `"pnet"` list **unchanged**, without calling `build_search_url`/`discover_job_urls` at all (the fallback path); `get_job_urls("pnet", limit)` with `pnet.mode` set to `"auto"` (test overrides the config file path to a fixture config) calls `discover_job_urls("pnet", limit)` instead. One function, branching on config — not two call sites in a future consumer. | tester | `data/discovery_config.json` (step 69), `data/crawler_seed_urls.json` (step 60, already built) | `tests/unit/test_discovery.py` (updated) | Fails — `get_job_urls` doesn't exist yet (RED confirmed) | none |
| 71 | **[GREEN]** `src/vacancy_search/discovery.py` (same file, extended) — `get_job_urls(platform, limit, discovery_config_path="data/discovery_config.json", seed_urls_path="data/crawler_seed_urls.json")`: the single entry point `apify_client.py::fetch_vacancies()` (Phase 14 below) will call for **both** `"pnet"` and `"careers24"`; reads `discovery_config.json`, branches per the step 70 contract. This is the "config-driven branch, not a code fork" mechanism (judgment call #3 above) — `apify_client.py` never special-cases PNet. | executor | `tests/unit/test_discovery.py` (step 70) | `src/vacancy_search/discovery.py` (updated) | `python -m pytest tests/unit/test_discovery.py` passes fully | none |

#### Phase 13 — LLM Extraction (**preserved from the original Phase 12, steps 63–65 — content unchanged, only renumbered; input source changes from a static seed-URL config entry to a discovered/gated job-detail URL from Phase 12 above**)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 72 | **[RED]** `tests/unit/test_vacancy_extraction.py` — identical scope to the original spec's step 63 (`build_extraction_prompt`, `extract_vacancy_fields`, `VacancyExtractionError` on missing/empty required fields per the Codex Review Follow-up amendment's validation tightening, `OFFLINE_MODE` fixture) — **no new assertions from this redesign**; the only conceptual change is that the raw page handed to `extract_vacancy_fields` now originates from a discovered/gated URL (Phase 12), not a hand-maintained seed URL, which is invisible to this function's own contract. | tester | `src/vacancy_search/schema.py`'s `REQUIRED_FIELDS`, `src/matching/scorer.py`'s `MatchParseError` (pattern reference only) | `tests/unit/test_vacancy_extraction.py` | Fails with `ModuleNotFoundError` (RED confirmed) | none |
| 73 | **[GREEN]** `src/vacancy_search/extraction_prompt.py` — identical to the original spec's step 64, unchanged. | executor | `tests/unit/test_vacancy_extraction.py` (step 72) | `src/vacancy_search/extraction_prompt.py` | `python -m pytest tests/unit/test_vacancy_extraction.py -k prompt` passes | none |
| 74 | **[GREEN]** `src/vacancy_search/extractor.py` — identical to the original spec's step 65, unchanged (`VacancyExtractionError`, consumes `src.shared.ollama_client.call_ollama`). | executor | `tests/unit/test_vacancy_extraction.py` (step 72), `src/vacancy_search/extraction_prompt.py` (step 73), `src/shared/ollama_client.py` (step 56) | `src/vacancy_search/extractor.py` | `python -m pytest tests/unit/test_vacancy_extraction.py` passes fully | Ollama (via `call_ollama`; real calls only; tests offline) |

#### Phase 14 — Fold into `fetch_vacancies()` (**preserved from the original Phase 13, steps 66–67, renumbered — the integration point changes from `crawler_client.fetch_raw_pages(platform, limit)` reading a static config directly, to `discovery.get_job_urls(platform, limit)` supplying URLs, each fetched via `crawler_client.fetch_raw_page(url)`**)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 75 | **[RED]** `tests/unit/test_apify_client.py` — extend: `fetch_vacancies(limit)` now, for `"pnet"` and `"careers24"`, calls `discovery.get_job_urls(platform, limit)` to obtain job-detail URLs, then `crawler_client.fetch_raw_page(url)` per URL, then `extractor.extract_vacancy_fields` per raw page, folding resulting `Vacancy` objects into the existing combined dedupe-and-truncate flow (all four sources deduped together, same as the original contract) — this replaces the original step 66 assertion that called `crawler_client.fetch_raw_pages(platform, limit)` directly; add a case asserting the PNet fallback path is exercised: with `discovery_config.json`'s `pnet.mode` set to `"manual_pending_verification"`, `fetch_vacancies()` still returns PNet vacancies sourced from `data/crawler_seed_urls.json`'s existing entries (via `get_job_urls`'s fallback), proving the fallback path works end-to-end through the real integration point, not just in isolation (step 70 already unit-tests `get_job_urls` alone). A `VacancyExtractionError` per page is still caught and skipped (logged), same as originally specced. | tester | `src/vacancy_search/apify_client.py` (current), `src/vacancy_search/discovery.py` (step 71), `src/vacancy_search/crawler_client.py` (step 64), `src/vacancy_search/extractor.py` (step 74) | `tests/unit/test_apify_client.py` (updated) | Fails — new discovery-integration and PNet-fallback assertions don't yet pass (RED confirmed) | none |
| 76 | **[GREEN]** `src/vacancy_search/apify_client.py` — `fetch_vacancies()` calls `discovery.get_job_urls("pnet", limit)` / `discovery.get_job_urls("careers24", limit)`, fetches each returned URL via `crawler_client.fetch_raw_page(url)`, runs each raw page through `extractor.extract_vacancy_fields`, catches `VacancyExtractionError` per-page (skip + continue), and combines resulting `Vacancy` objects with Indeed/LinkedIn results before the existing shared `_dedupe(...)[:limit]` call — **no `if platform == "pnet"` branching in this file**; both platforms go through the identical `get_job_urls` → `fetch_raw_page` → `extract_vacancy_fields` pipeline, satisfying this amendment's config-driven-branch requirement (judgment call #3). | executor | `tests/unit/test_apify_client.py` (step 75) | `src/vacancy_search/apify_client.py` (updated) | `python -m pytest tests/unit/test_apify_client.py` passes fully, including the new PNet-fallback case | Apify + Ollama (real calls only; tests offline) |

#### Phase 15 — Docs Closeout (**supersedes the original Phase 14, steps 68–72 — same topics, updated content to reflect discovery instead of static seed-URL-only sourcing**)

| # | Description | Agent | Input | Output | Verification | Network |
|---|---|---|---|---|---|---|
| 77 | Append a **second dated amendment section** (`## Amendment — 2026-07-29 (Automated Discovery)`) to `docs/decisions/ADR-002-apify-job-scraping.md` — additive to, not a replacement of, the amendment step 68 already specced above (that one documents crawler+extraction existing at all; this one documents that PNet/Careers24 discovery is now automated via constructed search URLs + listing-page parsing, with PNet gated behind a manual one-time verification and a documented static-seed-URL fallback). Original Decision/Consequences sections remain untouched. | architect | This amendment, ADR-002 (original + step-68 amendment) | `docs/decisions/ADR-002-apify-job-scraping.md` (amended again) | Read-check: both prior sections byte-identical above this new amendment marker; new amendment present, dated, self-contained | none |
| 78 | Update `docs/api-patterns.md`'s "PNet/Careers24 (Generic Crawler + Local LLM Extraction)" section (already added at the original step 69) — add a new "Automated Discovery" subsection documenting `discovery.py` (`build_search_url`, `parse_job_urls_from_listing`, `discover_job_urls`, `get_job_urls`), the `data/discovery_config.json` gate, and the PNet fallback behavior; note `crawler_client.py` gained `fetch_raw_page(url)` as a reusable single-URL primitive. | doc-writer | `src/vacancy_search/discovery.py`, `src/vacancy_search/crawler_client.py`, `data/discovery_config.json` | `docs/api-patterns.md` (updated) | Read-check: matches actual implemented function signatures, no invented endpoints | none |
| 79 | Update `CLAUDE.md`'s "🌐 External Client Patterns" table and Directory Structure tree — add `vacancy_search/discovery.py` (new module, no independent rate limit — reuses `crawler_client.py`'s `CRAWLER_RATE_LIMIT_PER_MIN` via `fetch_raw_page`); `data/` gains `discovery_config.json` alongside `crawler_seed_urls.json`. | doc-writer | `src/vacancy_search/discovery.py`, `data/discovery_config.json` | `CLAUDE.md` (updated) | Read-check: table and directory tree match actual post-build file layout | none |
| 80 | `docs/todo.md` — replace the existing `[ ]`/"BLOCKED on discovery redesign" steps 63–72 block with this amendment's new Build Queue section, steps 63–80, cross-referencing this amendment; move the "Real seed URLs for PNet/Careers24" line in this spec's own Open Items (below) to reflect it is now PNet-only-and-conditional; add the new manual bare-URL verification item (below) as an explicit open task for Tebello, not folded silently into an existing line. | doc-writer | This amendment (all steps 63–80) | `docs/todo.md` (updated) | Read-check: new Build Queue phase present with correct step numbers/descriptions; no duplicate tracking of the superseded original steps 63–72 in two places | none |

No task above touches more than 2 files (Output column governs the count, same convention as the
rest of this spec — e.g. step 64 and step 66/68/71 each touch only `discovery.py` or
`crawler_client.py`, one file; test-only RED steps count as 1).

### New Acceptance Criteria (additive to the original Acceptance Criteria section above)

- **No request is ever sent to a robots.txt-disallowed URL shape.** Specifically: no code path may
  construct or crawl a PNet URL containing a `?` query string (violates PNet's live `robots.txt`
  `User-agent: *` → `Disallow: /jobs/*?*` rule, confirmed 2026-07-29) — enforced structurally in
  `build_search_url("pnet", ...)` (step 68: the function has no code path capable of appending a query
  string) and tested explicitly (step 67).
- **The PNet fallback-to-manual-seed-URL path is exercised by at least one test** — `test_discovery.py`
  (step 70, isolated) and `test_apify_client.py` (step 75, end-to-end through `fetch_vacancies()`) both
  assert that `pnet.mode = "manual_pending_verification"` in `data/discovery_config.json` causes PNet
  vacancies to be sourced from `data/crawler_seed_urls.json`'s existing entries, not from
  `discover_job_urls`/`build_search_url` at all.
- Careers24 discovery is exercised by at least one test asserting a listing-page fixture containing
  multiple job-detail anchors yields multiple discovered URLs (not the one-page-one-vacancy contract
  from the Codex Review Follow-up amendment — that contract still applies one level down, to
  `extract_vacancy_fields` on a single job-detail page, not to `parse_job_urls_from_listing` on a
  listing page, which is expected and required to return multiple URLs).

### Open Items Flagged for Architect / User (additive — updates item 1 from the original Open Items section, adds a new item 4)

1. **(Updated, was: "Real seed URLs for PNet/Careers24")** — Careers24 no longer needs this: discovery
   is fully automated from `SEARCH_TITLES`/`SEARCH_LOCATION`, no manual seed URL required. This item
   now applies **to PNet only, and only if the manual bare-URL check below fails** — if it fails,
   Tebello must supply real PNet job-detail seed URLs in `data/crawler_seed_urls.json` the same way the
   original spec described, as the permanent (not temporary) PNet sourcing path.
2. Extraction reliability at scale — unchanged from the original Open Items item 2.
3. `CRAWLER_RATE_LIMIT_PER_MIN` default of 30 — unchanged from the original Open Items item 3; this
   amendment adds no new rate-limit constant (`discovery.py` reuses `crawler_client.py`'s limiter via
   `fetch_raw_page`).
4. **New — manual bare-URL verification (blocks flipping `pnet.mode` to `"auto"`).** Tebello: open
   `https://www.pnet.co.za/jobs/operations-foreman/in-gauteng` (the bare path-only shape, no `?`
   query string) once in an ordinary browser, and confirm whether it renders a working PNet
   results/listing page or an error/redirect/block page. Record the result by editing
   `data/discovery_config.json`'s `pnet.mode` directly: set it to `"auto"` if the page works, or leave
   it at `"manual_pending_verification"` (with a one-line note added to the file's `_comment`, e.g.
   "checked 2026-0X-XX, bare URL does not render a usable results page — permanent fallback") if it
   doesn't. This is a one-time check, not a recurring task, and is not the same as the per-vacancy
   manual URL-pasting labor this redesign was written to eliminate.
