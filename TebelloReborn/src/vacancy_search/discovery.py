import json
import os
import re

from src.vacancy_search import crawler_client

DEFAULT_DISCOVERY_CONFIG_PATH = "data/discovery_config.json"
DEFAULT_SEED_URLS_PATH = "data/crawler_seed_urls.json"

# Deterministic listing-page URL-extraction, not an LLM call (Amendment —
# Automated Discovery Redesign, judgment call #1): listing pages have a
# repeated, predictable anchor structure per platform, so harvesting job
# detail URLs is a structural task, unlike the unstructured-text field
# extraction in extractor.py, which is what call_ollama() is justified for.
_JOB_URL_PATTERNS = {
    "careers24": re.compile(r'https://www\.careers24\.com/jobs/vacancy-[^"\'\s<>]+'),
    # Real anchor shape confirmed via direct real-API test (2026-08-01,
    # htmlTransformer: "none"): domain-relative hrefs shaped
    # /jobs--<slug>--<numeric-id>-inline.html. Distinct from the
    # /jobs/<category>/in-<location> "related search" links elsewhere on the
    # same listing page (careful: the leading "--" is what distinguishes a
    # real job-detail link from a category/facet link).
    "pnet": re.compile(r'/jobs--[^"\'\s<>]+?-\d+-inline\.html'),
}

# PNet's real hrefs are domain-relative (no scheme/host) — resolved to
# absolute here since fetch_raw_page() needs a full URL for the follow-up
# job-detail-page fetch. Careers24's pattern already matches absolute URLs.
_PNET_BASE_URL = "https://www.pnet.co.za"

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


def _pnet_slug(value: str) -> str:
    """Stricter slug for PNet URLs only: lowercase, spaces AND "/" -> hyphens
    (bug #3, docs/bugs/pnet-careers24-discovery-zero-results.md: "/" used to
    be silently dropped by the strip step below instead of treated as a
    separator, concatenating e.g. "Foreman/Manager" into "foremanmanager"),
    then strip any remaining character that isn't alphanumeric or a hyphen.
    PNet's live robots.txt (User-agent: *) includes "Disallow: /jobs/*?*"
    (confirmed 2026-07-29) — this makes the disallowed query-string shape
    structurally unreachable from build_search_url("pnet", ...), rather than
    just avoided by convention: no character sequence in `title`/`location`
    can produce a "?" (or any other character requests wouldn't need for a
    bare path) in the returned URL. There is no parameter or code path below
    that appends a query string for the pnet branch."""
    slug = _slugify(value).replace("/", "-")
    slug = re.sub(r"-+", "-", slug)
    return re.sub(r"[^a-z0-9-]", "", slug).strip("-")


def build_search_url(platform: str, title: str, location: str) -> str:
    """Constructs a search-results/listing URL for a platform from a target
    title and location. Confirmed live shapes (2026-07-29):
      careers24: https://www.careers24.com/jobs/lc-<location>/kw-<title>/rmt-incl/
      pnet:      https://www.pnet.co.za/jobs/<title>/in-<location> (bare path
                 only — see _pnet_slug's docstring on why no "?" is ever
                 reachable here)
    """
    if platform == "careers24":
        title_slug = _slugify(title)
        location_slug = _slugify(location)
        return f"https://www.careers24.com/jobs/lc-{location_slug}/kw-{title_slug}/rmt-incl/"

    if platform == "pnet":
        title_slug = _pnet_slug(title)
        location_slug = _pnet_slug(location)
        return f"https://www.pnet.co.za/jobs/{title_slug}/in-{location_slug}"

    raise ValueError(f"Unsupported platform for search URL: {platform}")


def parse_job_urls_from_listing(raw_text: str, platform: str) -> list[str]:
    """Deterministic regex extraction of individual job-detail-page URLs
    from a listing page's raw text/HTML. Not an LLM call — see judgment
    call #1 above. Returns [] for a platform with no known pattern."""
    pattern = _JOB_URL_PATTERNS.get(platform)
    if pattern is None:
        return []
    matches = list(dict.fromkeys(pattern.findall(raw_text)))
    if platform == "pnet":
        matches = [_PNET_BASE_URL + m for m in matches]
    return matches


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

    job_urls = parse_job_urls_from_listing(listing_page.get("html", ""), platform)
    source_mode = listing_page["_source_mode"]
    return [{"url": u, "_source_mode": source_mode} for u in job_urls][:limit]


def _load_discovery_config(discovery_config_path: str) -> dict:
    with open(discovery_config_path, encoding="utf-8") as f:
        return json.load(f)


def get_job_urls(
    platform: str,
    limit: int,
    discovery_config_path: str = DEFAULT_DISCOVERY_CONFIG_PATH,
    seed_urls_path: str = DEFAULT_SEED_URLS_PATH,
) -> list[str]:
    """Single entry point apify_client.py::fetch_vacancies() calls for both
    "pnet" and "careers24" — branches internally on discovery_config.json's
    per-platform mode (judgment call #3, Amendment — Automated Discovery
    Redesign) so no consumer ever special-cases PNet.

    Careers24 has no gate: always discover_job_urls("careers24", limit).
    PNet: "manual_pending_verification" (default, until Tebello confirms the
    bare-path URL renders a usable page) falls back to the URLs already
    present in data/crawler_seed_urls.json's "pnet" list, unchanged; "auto"
    calls discover_job_urls("pnet", limit) instead.
    """
    if platform == "careers24":
        return [d["url"] for d in discover_job_urls(platform, limit)]

    config = _load_discovery_config(discovery_config_path)
    mode = config.get(platform, {}).get("mode", "manual_pending_verification")
    if mode == "auto":
        return [d["url"] for d in discover_job_urls(platform, limit)]

    return crawler_client._load_seed_urls(platform, seed_urls_path)
