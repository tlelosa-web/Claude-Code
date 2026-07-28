import os
import re

from src.vacancy_search import crawler_client

# Deterministic listing-page URL-extraction, not an LLM call (Amendment —
# Automated Discovery Redesign, judgment call #1): listing pages have a
# repeated, predictable anchor structure per platform, so harvesting job
# detail URLs is a structural task, unlike the unstructured-text field
# extraction in extractor.py, which is what call_ollama() is justified for.
_JOB_URL_PATTERNS = {
    "careers24": re.compile(r'https://www\.careers24\.com/jobs/vacancy-[^"\'\s<>]+'),
}

# Generic placeholder discovered-URL fixtures — never real scraped content.
# Mirrors crawler_client.py's FIXTURE_RAW_PAGES convention.
_FIXTURE_DISCOVERED_URLS = {
    "careers24": [
        "https://example.co.za/careers24-placeholder-job-1",
        "https://example.co.za/careers24-placeholder-job-2",
    ],
}


def _slugify(value: str) -> str:
    """Lowercase, spaces -> hyphens. No other normalization — matches the
    confirmed live URL shapes exactly (see docs/specs/pnet-careers24-coverage.md
    Amendment's Research section)."""
    return re.sub(r"\s+", "-", value.strip().lower())


def build_search_url(platform: str, title: str, location: str) -> str:
    """Constructs a search-results/listing URL for a platform from a target
    title and location. Confirmed live shapes (2026-07-29):
      careers24: https://www.careers24.com/jobs/lc-<location>/kw-<title>/rmt-incl/
      pnet:      https://www.pnet.co.za/jobs/<title>/in-<location>
    """
    title_slug = _slugify(title)
    location_slug = _slugify(location)

    if platform == "careers24":
        return f"https://www.careers24.com/jobs/lc-{location_slug}/kw-{title_slug}/rmt-incl/"

    raise ValueError(f"Unsupported platform for search URL: {platform}")


def parse_job_urls_from_listing(raw_text: str, platform: str) -> list[str]:
    """Deterministic regex extraction of individual job-detail-page URLs
    from a listing page's raw text/HTML. Not an LLM call — see judgment
    call #1 above. Returns [] for a platform with no known pattern."""
    pattern = _JOB_URL_PATTERNS.get(platform)
    if pattern is None:
        return []
    return list(dict.fromkeys(pattern.findall(raw_text)))


def _fixture_discovered_urls(platform: str) -> list[dict]:
    urls = _FIXTURE_DISCOVERED_URLS.get(platform, [])
    return [{"url": u, "_source_mode": "fixture"} for u in urls]


def discover_job_urls(platform: str, limit: int) -> list[dict]:
    """Constructs the platform's search-results URL, fetches it via
    crawler_client.fetch_raw_page(), and parses individual job-detail URLs
    out of the listing page's text_content. Returns up to `limit` dicts of
    {"url", "_source_mode"} — each URL is tagged with the listing fetch's
    own _source_mode ("live" or "fixture") so a degraded discovery run is
    never silently indistinguishable from a real one downstream.

    OFFLINE_MODE returns a deterministic fixture list without any fetch
    call at all.
    """
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return _fixture_discovered_urls(platform)[:limit]

    # Local import: apify_client.py imports discovery.py (Phase 14), so a
    # module-level import here would create a circular import.
    from src.vacancy_search.apify_client import SEARCH_LOCATION, SEARCH_TITLES

    listing_url = build_search_url(platform, SEARCH_TITLES[0], SEARCH_LOCATION)
    listing_page = crawler_client.fetch_raw_page(listing_url)
    if listing_page is None:
        return []

    job_urls = parse_job_urls_from_listing(listing_page["text_content"], platform)
    source_mode = listing_page["_source_mode"]
    return [{"url": u, "_source_mode": source_mode} for u in job_urls][:limit]
