import json
import os
import warnings

import requests

from src.shared.rate_limiter import RateLimiter

# Same generic actor ai-outreach-agency/src/research/apify_client.py already
# calls — no dedicated PNet/Careers24 actor exists (ADR-002).
CRAWLER_ACTOR_URL = "https://api.apify.com/v2/acts/apify~website-content-crawler/run-sync-get-dataset-items"
# Bumped 60s -> 180s (2026-08-01): a real PNet crawl took ~150s to complete
# (heavy bot-detection/JS-rendering delay, confirmed via direct real-API
# test) — the previous 60s timeout would have silently returned None on
# every real PNet fetch, masking success as a normal per-call failure.
TIMEOUT = 180

RATE_LIMIT_PER_MIN = int(os.environ.get("CRAWLER_RATE_LIMIT_PER_MIN", "30"))
_limiter = RateLimiter(rate=RATE_LIMIT_PER_MIN, period=60.0)

# Generic placeholder raw pages — never real scraped content. Shape mirrors
# ai-outreach-agency's FIXTURE convention ({"url", "title", "text_content"}).
FIXTURE_RAW_PAGES = [
    {
        "url": "https://example.co.za/pnet-placeholder",
        "title": "Example Operations Foreman Vacancy",
        "text_content": "Oversee workshop production for a heavy engineering manufacturer.",
    },
    {
        "url": "https://example.co.za/careers24-placeholder",
        "title": "Example Project Engineer Vacancy",
        "text_content": "Manage mechanical engineering projects across the power generation sector.",
    },
]


def _fixture_raw_pages(limit: int) -> list[dict]:
    pages = [{**page, "_source_mode": "fixture"} for page in FIXTURE_RAW_PAGES]
    return pages[:limit]


def _load_seed_urls(platform: str, seed_urls_path: str) -> list[str]:
    with open(seed_urls_path, encoding="utf-8") as f:
        config = json.load(f)
    return config.get(platform, [])


def fetch_raw_page(url: str) -> dict | None:
    """Fetch raw page content for a single URL via Apify's generic
    website-content-crawler actor. Returns a raw page dict ("url", "title",
    "text_content", "_source_mode") or None if the real call fails.

    This is the single-URL primitive extracted from fetch_raw_pages()'s old
    per-seed-URL loop body (Amendment — Automated Discovery Redesign,
    judgment call #2) — fetch_raw_pages() calls it once per seed URL below,
    and discovery.py composes on top of it for listing-page and
    job-detail-page fetches, so the POST/timeout/_source_mode/
    exception-handling logic lives in exactly one place.
    """
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return {**FIXTURE_RAW_PAGES[0], "_source_mode": "fixture"}

    api_key = os.environ.get("APIFY_API_KEY", "")
    if not api_key:
        warnings.warn(
            "APIFY_API_KEY not set — falling back to fixture raw pages. "
            "Set APIFY_API_KEY or OFFLINE_MODE=true to suppress this warning."
        )
        return {**FIXTURE_RAW_PAGES[0], "_source_mode": "fixture"}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    _limiter.acquire()
    try:
        resp = requests.post(
            CRAWLER_ACTOR_URL,
            headers=headers,
            json={
                "startUrls": [{"url": url}],
                "maxCrawlPages": 1,
                "maxCrawlDepth": 0,
                "saveHtml": True,
                # "none" disables the actor's default Mozilla-Readability
                # post-processing — confirmed via direct real-API test
                # (2026-08-01) that the default (readableText) mode strips
                # every <a href> from its HTML output too, not just
                # text_content, so discovery.py's link-harvesting has
                # nothing to match against without this.
                "htmlTransformer": "none",
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        items = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if not items or not isinstance(items, list):
        return None

    first = items[0]
    return {
        "url": first.get("url", url),
        "title": first.get("title", ""),
        "text_content": first.get("text", first.get("text_content", "")),
        "html": first.get("html", ""),
        "_source_mode": "live",
    }


def fetch_raw_pages(
    platform: str,
    limit: int,
    seed_urls_path: str = "data/crawler_seed_urls.json",
) -> list[dict]:
    """Fetch raw page content for a platform's configured seed URLs via
    Apify's generic website-content-crawler actor. Returns raw page dicts
    (not Vacancy objects — extraction is a separate concern, Phase 12).

    Each returned dict carries a "_source_mode" of "live" or "fixture" so a
    degraded (fixture-fallback) run is never silently indistinguishable from
    a real one downstream.
    """
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return _fixture_raw_pages(limit)

    api_key = os.environ.get("APIFY_API_KEY", "")
    if not api_key:
        warnings.warn(
            "APIFY_API_KEY not set — falling back to fixture raw pages. "
            "Set APIFY_API_KEY or OFFLINE_MODE=true to suppress this warning."
        )
        return _fixture_raw_pages(limit)

    seed_urls = _load_seed_urls(platform, seed_urls_path)
    results: list[dict] = []

    for seed_url in seed_urls:
        page = fetch_raw_page(seed_url)
        if page is not None:
            results.append(page)

    return results[:limit]
