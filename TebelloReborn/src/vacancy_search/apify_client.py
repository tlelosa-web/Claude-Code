import logging
import os
import warnings
from itertools import zip_longest
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

from src.shared.rate_limiter import RateLimiter

from .crawler_client import fetch_raw_page
from .discovery import get_job_urls
from .extractor import VacancyExtractionError, extract_vacancy_fields
from .schema import Vacancy

logger = logging.getLogger(__name__)

# Platforms sourced via the generic crawler + local LLM extraction pipeline
# (discovery.get_job_urls -> crawler_client.fetch_raw_page ->
# extractor.extract_vacancy_fields), as opposed to Indeed/LinkedIn's
# dedicated Apify actors below. Looping over this tuple (rather than
# `if platform == "pnet"` special-casing) is what keeps the PNet
# manual-verification gate a config-driven branch inside discovery.py,
# never a code fork here (Amendment, judgment call #3).
CRAWLER_PLATFORMS = ("pnet", "careers24")

DISCOVERY_CONFIG_PATH = "data/discovery_config.json"
SEED_URLS_PATH = "data/crawler_seed_urls.json"

# Actor slugs confirmed live on the Apify Store 2026-07-26 (misceres/indeed-scraper,
# bebity/linkedin-jobs-scraper — API IDs use "~" where the store URL uses "/").
INDEED_ACTOR_URL = (
    "https://api.apify.com/v2/acts/misceres~indeed-scraper/run-sync-get-dataset-items"
)
LINKEDIN_ACTOR_URL = "https://api.apify.com/v2/acts/bebity~linkedin-jobs-scraper/run-sync-get-dataset-items"
TIMEOUT = 60

# One search per target title from profile_seed.json's target_titles, run
# against both actors. Indeed requires "position"/"location" to have anything
# to search; LinkedIn requires "title"/"location"/"rows" — neither accepts a
# bare item-count field on its own (see the maxItems bug note below).
SEARCH_TITLES = ["Operations Foreman/Manager", "Project Engineer (Mechanical)"]
SEARCH_LOCATION = "Gauteng, South Africa"

RATE_LIMIT_PER_MIN = int(os.environ.get("APIFY_RATE_LIMIT_PER_MIN", "30"))
_limiter = RateLimiter(rate=RATE_LIMIT_PER_MIN, period=60.0)

FIXTURE_VACANCIES = [
    {
        "company": "Example Engineering (Pty) Ltd",
        "title": "Operations Foreman",
        "url": "https://za.indeed.com/viewjob?jk=example1",
        "description": "Oversee workshop production for a heavy engineering manufacturer.",
        "platform": "indeed",
        "salary": "R45,000 - R60,000 CTC",
        "deadline": None,
    },
    {
        "company": "Example Power Generation Ltd",
        "title": "Project Engineer (Mechanical)",
        "url": "https://www.linkedin.com/jobs/view/example2",
        "description": "Manage mechanical engineering projects across the power generation sector.",
        "platform": "linkedin",
        "salary": None,
        "deadline": "2026-08-31",
    },
    {
        "company": "Example Manufacturing Group",
        "title": "Operations Manager",
        "url": "https://za.indeed.com/viewjob?jk=example3",
        "description": "Lead multi-site manufacturing operations in Gauteng.",
        "platform": "indeed",
        "salary": "R55,000 CTC",
        "deadline": None,
    },
]


# Known tracking params to strip when building the dedupe key — never a
# platform's own significant identifier (e.g. Indeed's ?jk=<id>, which must
# survive normalization or every Indeed URL collapses to the same bare path
# key, silently merging genuinely distinct postings). Codex Review
# Follow-up (W2): the original implementation stripped the entire query
# string, which fixed UTM-differing duplicates but broke Indeed dedupe.
_TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}


def normalize_url(url: str) -> str:
    """Strips known tracking query params, fragment, and trailing slash
    before building the dedupe key — two vacancies whose URLs differ only
    by a UTM query string or trailing slash are otherwise treated as
    distinct (Codex Review Follow-up amendment). Significant identifier
    params (e.g. Indeed's ?jk=<id>) are preserved, not stripped — only
    _TRACKING_QUERY_PARAMS is removed. Used by all four sources (Indeed,
    LinkedIn, PNet, Careers24) via the shared _dedupe() below."""
    parts = urlsplit(url)
    path = parts.path.rstrip("/") if len(parts.path) > 1 else parts.path
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in _TRACKING_QUERY_PARAMS
    ]
    query = urlencode(query_pairs)
    return urlunsplit((parts.scheme, parts.netloc, path, query, ""))


def _dedupe(vacancies: list[Vacancy]) -> list[Vacancy]:
    seen = set()
    deduped = []
    for v in vacancies:
        key = (v.company, v.title, normalize_url(v.url))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(v)
    return deduped


def _fixture_vacancies(limit: int) -> list[Vacancy]:
    return _dedupe([Vacancy(**v) for v in FIXTURE_VACANCIES])[:limit]


def _normalize_indeed(item: dict) -> Vacancy:
    return Vacancy(
        company=item.get("company", ""),
        title=item.get("positionName", item.get("title", "")),
        url=item.get("url", ""),
        description=item.get("description", ""),
        platform="indeed",
        salary=item.get("salary"),
        deadline=item.get("deadline"),
    )


def _normalize_linkedin(item: dict) -> Vacancy:
    return Vacancy(
        company=item.get("companyName", item.get("company", "")),
        title=item.get("title", ""),
        url=item.get("link", item.get("url", "")),
        description=item.get("description", ""),
        platform="linkedin",
        salary=item.get("salary"),
        deadline=item.get("expireAt"),
    )


def _fetch_crawler_platform_vacancies(
    platform: str, limit: int
) -> tuple[list[Vacancy], int, int]:
    """One pass of the PNet/Careers24 pipeline for a single platform:
    discovery.get_job_urls() -> crawler_client.fetch_raw_page() ->
    extractor.extract_vacancy_fields(). A VacancyExtractionError on one page
    is caught and that page is skipped (logged), never aborting the batch —
    mirrors the per-call swallow convention already used for Indeed/LinkedIn
    HTTP errors below. Returns (vacancies, live_page_count, fixture_page_count)
    so fetch_vacancies() can log a single combined degraded-mode summary.
    """
    urls = get_job_urls(
        platform,
        limit,
        discovery_config_path=DISCOVERY_CONFIG_PATH,
        seed_urls_path=SEED_URLS_PATH,
    )

    vacancies: list[Vacancy] = []
    live_count = 0
    fixture_count = 0

    for url in urls:
        raw_page = fetch_raw_page(url)
        if raw_page is None:
            continue

        if raw_page.get("_source_mode") == "fixture":
            fixture_count += 1
        else:
            live_count += 1

        try:
            fields = extract_vacancy_fields(raw_page, platform)
        except VacancyExtractionError as exc:
            logger.warning(
                "Skipping %s page %s — extraction failed: %s", platform, url, exc
            )
            continue

        vacancies.append(Vacancy(platform=platform, **fields))

    return vacancies, live_count, fixture_count


def fetch_vacancies(limit: int = 25) -> list[Vacancy]:
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return _fixture_vacancies(limit)

    api_key = os.environ.get("APIFY_API_KEY", "")
    if not api_key:
        warnings.warn(
            "APIFY_API_KEY not set — falling back to fixture vacancies. "
            "Set APIFY_API_KEY or OFFLINE_MODE=true to suppress this warning."
        )
        return _fixture_vacancies(limit)

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    indeed_results: list[Vacancy] = []
    linkedin_results: list[Vacancy] = []

    for title in SEARCH_TITLES:
        _limiter.acquire()
        try:
            resp = requests.post(
                INDEED_ACTOR_URL,
                headers=headers,
                json={
                    "position": title,
                    "location": SEARCH_LOCATION,
                    "country": "ZA",
                    "maxItemsPerSearch": limit,
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            indeed_results.extend(_normalize_indeed(item) for item in resp.json())
        except (requests.RequestException, ValueError):
            pass

        _limiter.acquire()
        try:
            resp = requests.post(
                LINKEDIN_ACTOR_URL,
                headers=headers,
                json={
                    "title": title,
                    "location": SEARCH_LOCATION,
                    "rows": limit,
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            linkedin_results.extend(_normalize_linkedin(item) for item in resp.json())
        except (requests.RequestException, ValueError):
            pass

    total_pages = 0
    fixture_pages = 0
    source_lists = [indeed_results, linkedin_results]
    for platform in CRAWLER_PLATFORMS:
        platform_vacancies, live_count, fixture_count = (
            _fetch_crawler_platform_vacancies(platform, limit)
        )
        source_lists.append(platform_vacancies)
        total_pages += live_count + fixture_count
        fixture_pages += fixture_count

    if fixture_pages:
        logger.warning(
            "%d of %d vacancy-source pages returned fixture data — check "
            "APIFY_API_KEY / network",
            fixture_pages,
            total_pages,
        )

    return _dedupe(_interleave(source_lists))[:limit]


def _interleave(source_lists: list[list[Vacancy]]) -> list[Vacancy]:
    """Round-robin combine per-source result lists — one item from each
    non-empty source in turn, cycling until all are exhausted — so a single
    source (e.g. Indeed alone returning >= limit items) can never fill the
    entire final [:limit] truncation window and starve out the other,
    already-fetched-and-paid-for sources by list position alone (real-run
    bug, 2026-07-31: 10/10 results were Indeed, LinkedIn/PNet/Careers24
    contributed zero despite real network calls being made)."""
    combined: list[Vacancy] = []
    for items in zip_longest(*source_lists, fillvalue=None):
        combined.extend(item for item in items if item is not None)
    return combined
