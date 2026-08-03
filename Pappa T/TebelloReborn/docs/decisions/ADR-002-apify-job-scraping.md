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

## Amendment — 2026-07-29 (Automated Discovery)

PNet/Careers24 discovery is now automated — the `docs/todo.md` "Known Issues"/"Future" deferral this ADR's original Decision section flagged is closed, not merely scheduled. Full detail: `docs/specs/pnet-careers24-coverage.md`'s "Amendment — Automated Discovery Redesign" section (build steps 63–80). This amendment documents what shipped without editing the Decision/Consequences sections above, which remain the historical record of the original MVP-scope decision.

- **Generic crawler + local LLM extraction, as originally flagged as the natural path.** `src/vacancy_search/crawler_client.py` (Apify's generic `website-content-crawler` actor, same one `ai-outreach-agency` already uses) fetches raw page content; `src/vacancy_search/extractor.py` turns it into `Vacancy`-shaped fields via `src/shared/ollama_client.py::call_ollama()` (`qwen3:8b`), strictly validated — `VacancyExtractionError` on any parse failure or a missing/empty required field (`company`/`title`/`url`).
- **Discovery is now a distinct sub-stage, not a hand-maintained seed-URL list.** `src/vacancy_search/discovery.py` constructs each platform's search-results URL from `apify_client.py`'s existing `SEARCH_TITLES`/`SEARCH_LOCATION` constants (`build_search_url`), fetches it via `crawler_client.fetch_raw_page()`, and parses individual job-detail-page URLs out of the listing page with a deterministic regex/anchor parse (`parse_job_urls_from_listing` — never an LLM call; listing-page anchor structure is a structural extraction task, unlike unstructured job-description field extraction). This closes the "one raw page = one vacancy" gap the original static seed-URL design had for search-results/listing pages.
- **PNet is gated behind a one-time manual verification, Careers24 is not.** PNet's live `robots.txt` (`User-agent: *`) disallows the query-string search shape (`Disallow: /jobs/*?*`, confirmed 2026-07-29); `build_search_url("pnet", ...)` only ever constructs the bare path-only shape, with no code path capable of appending a query string. Whether that bare-path shape renders a usable results page was unconfirmed as of this amendment, so PNet discovery is gated behind `data/discovery_config.json`'s `pnet.mode` (`"manual_pending_verification"` by default) — Tebello opens the URL once in an ordinary browser and flips the mode to `"auto"` only if it renders usably. Careers24's `robots.txt` has no blanket disallow for a generic crawler UA, so it has no gate — `discovery.py::get_job_urls("careers24", ...)` always calls `discover_job_urls`, regardless of config content.
- **A documented, permanent fallback, not a stopgap.** If PNet's bare-path shape never renders usably, `pnet.mode` stays `"manual_pending_verification"` indefinitely and PNet continues sourcing from the pre-existing `data/crawler_seed_urls.json` (Phase 10, step 60) — a supported end state, not a temporary workaround. `discovery.py::get_job_urls(platform, limit)` is the single entry point `apify_client.py::fetch_vacancies()` calls for both platforms; the config-driven branch lives entirely inside `discovery.py`, so `apify_client.py` never special-cases either platform (`CRAWLER_PLATFORMS = ("pnet", "careers24")`, looped generically).
- **`VALID_PLATFORMS` addition (`"pnet"`, `"careers24"`) is confirmed non-schema** — a Python-level dataclass validation set in `src/vacancy_search/schema.py`, not a DB constraint (`vacancies.platform` is plain `TEXT NOT NULL`, no `CHECK`). No migration file required; see `docs/specs/pnet-careers24-coverage.md`'s Migration Note.
- **`ollama_client.py` promoted `src/matching/` → `src/shared/`** per ADR-003 §Alternatives.D's own stated trigger ("promote later if a second consumer appears") — the extraction step above is that second consumer, alongside `matching/scorer.py`.
- **New exception type**: `VacancyExtractionError(ValueError)`, defined in `extractor.py`, distinct from `matching/scorer.py`'s `MatchParseError` (different domain — malformed LLM extraction of a scraped page, not a malformed match score).
- **Seed URLs remain parameterized config, never hardcoded** — `data/crawler_seed_urls.json` (unchanged from Phase 10) is now PNet's fallback source only, not the primary discovery path for either platform.

## Amendment — 2026-08-01 (Zero-Results Root Cause + Fix)

The Automated Discovery Redesign above shipped and passed its full offline
test suite, but the first real (non-offline) run returned **zero** PNet or
Careers24 vacancies — full root-cause writeup:
`docs/bugs/pnet-careers24-discovery-zero-results.md`. Two compounding causes,
both fixed:

- **`parse_job_urls_from_listing()` was reading the wrong field.**
  `discover_job_urls()` parsed `listing_page["text_content"]` — but
  `crawler_client.fetch_raw_page()` never requested `saveHtml`, so
  `text_content` is the actor's plain, de-markup'd readability text, which
  contains zero URLs of any kind (confirmed live: a real careers24 page's
  `text_content` had 0 occurrences of `"https://"`). Even careers24's
  correct-looking regex could never match.
- **`saveHtml: true` alone does not fix this.** A direct real-API test
  against a live PNet listing page (2026-08-01) found the actor's *default*
  `htmlTransformer` (`readableText`, Mozilla Readability) strips every
  `<a href>` from its HTML output too — not just `text_content`. Getting real
  anchors back required also setting `htmlTransformer: "none"`. This is a
  correction to this ADR's own original Amendment text above, which assumed
  (untested) that `saveHtml` alone would suffice.
- **Fix**: `crawler_client.fetch_raw_page()` now sends both
  `saveHtml: true` and `htmlTransformer: "none"`, and surfaces the result as
  a new `"html"` field on its return dict — `"text_content"` is unchanged
  (still clean readability text, still what `extractor.py`'s LLM extraction
  prompt consumes; no reason to feed raw markup to the LLM).
  `discover_job_urls()` now parses `listing_page["html"]` instead.
- **`_JOB_URL_PATTERNS` had no `"pnet"` entry at all** — `parse_job_urls_from_listing(text, "pnet")` returned `[]`
  unconditionally, regardless of page content. Fixed with a pattern derived
  from a real capture (see below), not guessed.
- **PNet's real job-detail links are domain-relative, and a completely
  different shape from careers24's.** Confirmed via a direct real-API call
  against `https://www.pnet.co.za/jobs/operations-foreman/in-gauteng` with
  `htmlTransformer: "none"`: individual postings are
  `<a data-testid="job-item-title" href="/jobs--<slug>--<numeric-id>-inline.html">`
  — e.g. `/jobs--Panelshop-Foreman-Johannesburg-Scania-S-A-Pty-Ltd--4243343-inline.html`.
  `_JOB_URL_PATTERNS["pnet"]` matches this shape and resolves it to an
  absolute URL against `https://www.pnet.co.za` (careers24's pattern already
  matches absolute URLs, so no resolution step was needed there). The same
  listing page also has `/jobs/<category>/in-<location>` "related search"
  links in a *different* path shape (no `--`) — the pattern is specific
  enough not to pick these up as if they were postings.
- **Bonus fix, same root-cause investigation**: `_pnet_slug()` silently
  dropped `"/"` instead of treating it as a word separator, so
  `SEARCH_TITLES`'s `"Operations Foreman/Manager"` slugified to
  `"operations-foremanmanager"` (two words concatenated) instead of a
  properly hyphen-separated slug. Low severity on its own — PNet tolerated
  the malformed slug and still returned relevant results — but fixed
  alongside the rest since it was found in the same pass.
- **Also fixed**: `crawler_client.TIMEOUT` bumped `60s → 180s`. The real PNet
  call took ~150s to complete (bot-detection/JS-rendering delay, confirmed
  via direct real-API test) — the previous 60s timeout would have silently
  returned `None` on every real PNet fetch via the existing broad `except`
  clause, which would have masked this entire fix as a continued failure.
- **Test-suite gap closed**: the original tests' fixtures were hand-authored
  HTML strings that happened to embed literal URL substrings — a shape real
  extracted content never has, which is exactly why this shipped unnoticed.
  New tests parse against a listing fixture with a `text_content` field that
  contains zero URLs (matching real readability output) and assert URLs are
  still found — proving the parser reads `"html"`, not `"text_content"`.

Careers24's regex and gating logic (Careers24 has no manual-verification
gate, unlike PNet) are otherwise unchanged by this amendment — only the
field it reads changed.
