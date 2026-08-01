# Bug: PNet/Careers24 automated discovery finds zero job URLs on real runs

> Found 2026-08-01 during the first real (non-offline) `fetch-vacancies` run
> against the Automated Discovery build (merged `9319b5a`, 2026-07-31). This
> was the evidence-gathering exercise for the two Open Items in
> `docs/todo.md` ("extraction reliability at scale", "confirm
> `CRAWLER_RATE_LIMIT_PER_MIN`'s default") — neither of those turned out to
> be reachable, because discovery itself never produces a URL for extraction
> to run on. This supersedes both Open Items until the discovery layer
> itself is fixed.

## Symptom

`career-engine fetch-vacancies --limit 10` returned 10 vacancies, all
`platform = "indeed"`. Querying `career.db` shows **zero** `pnet` or
`careers24` vacancies have ever been stored, across both this run and the
2026-07-31 run that first exercised the Automated Discovery build.

No warning was logged (`fetch_vacancies()`'s fixture-mode summary never
fired), which is itself informative: it means real, live (non-fixture)
listing-page fetches succeeded, but discovery still produced 0 job URLs
from them — silently, because `get_job_urls()` → `discover_job_urls()` →
`parse_job_urls_from_listing()` has no failure path for "found nothing," by
design (an empty listing is a legitimate outcome for a niche search).

## Root causes — two independent bugs, not one

### 1. PNet has no URL-extraction pattern at all

`discovery.py`'s `_JOB_URL_PATTERNS` dict only has a `"careers24"` entry:

```python
_JOB_URL_PATTERNS = {
    "careers24": re.compile(r'https://www\.careers24\.com/jobs/vacancy-[^"\'\s<>]+'),
}
```

`parse_job_urls_from_listing(text, "pnet")` hits `pattern is None` and
returns `[]` unconditionally — **every single time**, regardless of what
the real PNet listing page contains. `build_search_url("pnet", ...)` and
the `discovery_config.json` gate were both built and tested (Phase 12,
steps 67–71), but the actual PNet job-URL-parsing regex was never added.
Confirmed live: `https://www.pnet.co.za/jobs/operations-foremanmanager/in-gauteng-south-africa`
(the real constructed search URL — see bug #3 below on the slug itself)
returns a real listing page with real job snippets (10.7KB of readable
text), but `discover_job_urls("pnet", ...)` still returns `[]` because
there is no pattern to match against.

**Why the test suite never caught this:** `tests/unit/test_discovery.py`'s
PNet coverage (per `docs/todo.md` step 67) only tests `build_search_url`'s
URL shape and the config-driven fallback branch in `get_job_urls` — no test
ever calls `parse_job_urls_from_listing(real_pnet_html, "pnet")` and asserts
non-empty output, because no such fixture/test was ever written.

### 2. The regex approach is structurally incompatible with the crawler's default output shape

Even for careers24, where a pattern *does* exist, it can never match:
`crawler_client.fetch_raw_page()` requests Apify's `website-content-crawler`
actor **without `saveHtml: true`**, so the returned `text_content` field
(`first.get("text", first.get("text_content", ""))`) is plain, readable,
de-markup'd text — confirmed by direct real-API test: a real careers24
listing page's `text_content` contains **zero occurrences of `"https://"`
anywhere in 1,236 characters of text**. Anchor hrefs simply aren't present
in that field; the actor strips them as part of producing clean readable
text (the same design choice that makes `text_content` good input for LLM
extraction — see `extractor.py` — is exactly what breaks link-harvesting).

`parse_job_urls_from_listing()`'s docstring frames this as "deterministic
regex extraction... not an LLM call" — a reasonable design intent, but it
was never checked against what the actor's default output actually
contains. The unit tests pass because their fixtures are hand-authored
strings that happen to embed literal URL substrings — a shape real
extracted page text never has.

**Fix requires either:**
- **(a)** Request `"saveHtml": true` in `fetch_raw_page()`'s Apify payload
  and parse hrefs out of real HTML instead of `text_content` — closest to
  the original design intent, straightforward regex-on-HTML swap.
- **(b)** Switch discovery to Apify's own link-following (`maxCrawlPages` >
  1 with `maxCrawlDepth` ≥ 1) and let the actor discover linked pages
  itself, filtering the resulting dataset by URL shape — avoids
  hand-rolled HTML parsing entirely, but changes cost/shape of what
  `fetch_raw_page` returns (multiple dataset items per call, not one).

Option (a) is the smaller change and keeps `fetch_raw_page()`'s
single-URL-in/one-page-out contract intact (relied on elsewhere — see
`extractor.py`'s "one raw page = one Vacancy" contract).

### 3. Bonus finding: `build_search_url("pnet", ...)`'s title slug is wrong for multi-word titles with a slash

`SEARCH_TITLES[0]` is `"Operations Foreman/Manager"` (one combined string,
by design — see `apify_client.py`'s comment). `_pnet_slug()` strips any
non-alphanumeric-non-hyphen character *after* slugifying, so `"/"` is
silently deleted rather than treated as a separator:
`"operations foreman/manager"` → `"operations-foreman/manager"` (slugify) →
`"operations-foremanmanager"` (strip) — concatenating "Foreman" and
"Manager" into one word. PNet tolerates this (returns a best-effort keyword
search rather than a 404 — confirmed real: still returns real, relevant job
snippets), so this alone doesn't cause the zero-URL symptom, but it means
PNet auto-discovery is searching for a keyword that doesn't match the
verified-working shape from `docs/specs/pnet-careers24-coverage.md`'s
Amendment Open Item 4 (`https://www.pnet.co.za/jobs/operations-foreman/in-gauteng`,
singular "operations-foreman", no "manager"). Worth fixing alongside #1,
low severity on its own.

## Separate, unrelated finding: LinkedIn actor requires a paid rental

Not a code bug. Direct real-API test against
`bebity~linkedin-jobs-scraper`:

```json
{"error": {"type": "actor-is-not-rented", "message": "You must rent a paid Actor in order to run it after its free trial has expired. To rent this Actor, go to https://console.apify.com/actors/BHzefUZlZRKWxkTck"}}
```

`fetch_vacancies()`'s `except (requests.RequestException, ValueError): pass`
around the LinkedIn call swallows this as a normal per-call failure (by
design, so one platform's outage doesn't block the others) — which is why
it was invisible in `career-engine fetch-vacancies`'s output. This explains
why **all 20 vacancies ever stored are `platform = "indeed"`** — LinkedIn
has silently contributed zero results since this actor's free trial
expired, on every real run including the pre-PNet/Careers24 one from
2026-07-31. This needs Tebello's decision (rent the actor on Apify's
console, or accept LinkedIn coverage as permanently degraded/dropped) — not
something an agent should decide or pay for unprompted.

## Suggested next steps (not yet actioned — awaiting direction)

1. Decide fix approach for #2 (saveHtml vs. actor-level link-following).
2. Fix #1 (add a PNet `_JOB_URL_PATTERNS` entry, or fold into whatever #2
   becomes) and #3 (fix `_pnet_slug`'s slash-handling) alongside it — same
   files, same TDD pass.
3. Add a regression test that exercises `parse_job_urls_from_listing`
   against real-shaped fixture data (HTML with real anchor structure, not
   hand-authored URL strings) for **both** platforms, closing the gap that
   let this ship unnoticed.
4. Tebello: decide on the LinkedIn actor rental (separate, non-code
   decision).
5. Once fixed, re-run a small real `fetch-vacancies` to confirm PNet/
   Careers24 vacancies actually land in `career.db` before closing this
   out.
