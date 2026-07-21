# ADR-002: Job-Board Scraping via Apify

**Status:** Accepted — documents the convention already established and built in Phase 3 (Build Queue steps 16–21); filed retroactively per `docs/todo.md`'s Phase 3.5 note.
**Date:** 2026-07-21
**Decider:** Tebello Lelosa
**Related:** Mirrors the *pattern* — not the code — of `ai-outreach-agency`'s Apify-based `research/apify_client.py`. ADR-001 (this project) establishes `vacancies` as the destination table.

## Context

Vacancy Fetch (Stage 2) needs a source of real job postings matching the candidate's target title lanes (Operations Foreman/Manager primary, Project Engineer secondary — see `CLAUDE.md`'s Target Candidate Profile). Options considered:

- **A. Manual entry** — no automation, defeats the purpose of a semi-automated pipeline.
- **B. Direct scraping per job board** — brittle, breaks on every site redesign, high maintenance.
- **C. Apify** — hosted actors per job board, already proven working in the sibling `ai-outreach-agency` project for its own scraping needs, no scraper maintenance burden on this project.

## Decision

**Apify is the vacancy-fetch backend**, via `src/vacancy_search/apify_client.py::fetch_vacancies(limit)`.

- **Two dedicated job-board actors are used for the MVP: Indeed and LinkedIn Jobs.** Both are confirmed to exist as dedicated scrapers on the Apify Store. The client calls each actor's `run-sync-get-dataset-items` endpoint, normalizes each platform's item shape into a `Vacancy` (`_normalize_indeed` / `_normalize_linkedin`), and de-duplicates on `(company, title, url)` before returning.
- **PNet and Careers24 are explicitly out of scope for the MVP** — neither has a dedicated Apify actor as of this decision (see `docs/todo.md`'s "Known Issues"). If added later, the natural path is Apify's generic `website-content-crawler` actor (the same one `ai-outreach-agency` already uses) plus LLM-based extraction, not a dedicated actor — this is a deferred, not-yet-scheduled item (`docs/todo.md`'s "Future" section).
- **The exact actor slugs currently in `apify_client.py` (`misceres~indeed-scraper`, `bebity~linkedin-jobs-scraper`) are unconfirmed placeholders**, called out in-file and in `docs/todo.md`'s "Known Issues" — the test suite mocks `requests.post` so this doesn't block the build, but the real slugs must be confirmed against the Apify Store before the first non-`OFFLINE_MODE` `fetch-vacancies` run. This is a pre-deployment checklist item, not a design gap.
- **Graceful degradation, not hard failure, on a missing API key or a request error:** unlike the Ollama/Claude Code backends (which fail loud per ADR-003), a missing `APIFY_API_KEY` or a failed actor call results in a `warnings.warn(...)` and a fallback to the fixture vacancies, not an exception. This is a deliberate asymmetry — vacancy fetch is the *first* pipeline stage with nothing downstream depending on a specific real result yet, whereas Ollama/Claude Code failures happen mid-pipeline on a specific vacancy already committed to the DB. If this proves too permissive in practice (e.g. it silently masks a real credential problem for too long), tightening it to fail loud is a small, isolated change — flagged here as a judgment call, not locked in.
- **Rate-limited** via the same `RateLimiter` token-bucket pattern as the Ollama client (`src/shared/rate_limiter.py`), default `30/min`, override via `APIFY_RATE_LIMIT_PER_MIN`. Each actor call acquires the limiter independently.
- **`OFFLINE_MODE` fixture:** `_fixture_vacancies(limit)` returns three fake vacancies (one per platform-flavour: Indeed, LinkedIn, Indeed) matching the primary/secondary title lanes, de-duplicated the same way real results are. No test makes a real HTTP call to the Apify API.

## Consequences

- Vacancy Fetch has zero scraper-maintenance burden — Apify's hosted actors absorb job-board layout changes, the same trade this project's sibling already made.
- The pipeline depends on an `APIFY_API_KEY` with an active Apify balance for real (non-offline) runs — analogous to (but independent of) the earlier `OPENROUTER_API_KEY` credit exhaustion that motivated ADR-003; Apify is unaffected by that ADR since it was never routed through OpenRouter.
- Coverage is intentionally partial at MVP (Indeed + LinkedIn only) — this under-covers the local SA job market (PNet, Careers24 are both used regionally) but keeps the build scoped to actors that definitely exist rather than speculative crawler+LLM-extraction work.
- Before the first real `fetch-vacancies` run: confirm the two actor slugs against the Apify Store (they are currently unverified placeholders) and confirm `APIFY_API_KEY` is funded.
