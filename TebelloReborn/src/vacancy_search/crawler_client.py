import json
import os
import warnings

import requests

from src.shared.rate_limiter import RateLimiter

# Same generic actor ai-outreach-agency/src/research/apify_client.py already
# calls — no dedicated PNet/Careers24 actor exists (ADR-002).
CRAWLER_ACTOR_URL = "https://api.apify.com/v2/acts/apify~website-content-crawler/run-sync-get-dataset-items"
TIMEOUT = 60

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
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    results: list[dict] = []

    for seed_url in seed_urls:
        _limiter.acquire()
        try:
            resp = requests.post(
                CRAWLER_ACTOR_URL,
                headers=headers,
                json={
                    "startUrls": [{"url": seed_url}],
                    "maxCrawlPages": 1,
                    "maxCrawlDepth": 0,
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            items = resp.json()
        except (requests.RequestException, ValueError):
            continue

        if not items or not isinstance(items, list):
            continue

        first = items[0]
        results.append(
            {
                "url": first.get("url", seed_url),
                "title": first.get("title", ""),
                "text_content": first.get("text", first.get("text_content", "")),
                "_source_mode": "live",
            }
        )

    return results[:limit]
