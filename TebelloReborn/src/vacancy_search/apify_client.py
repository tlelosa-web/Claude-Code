import os
import warnings

import requests

from src.shared.rate_limiter import RateLimiter

from .schema import Vacancy

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


def _dedupe(vacancies: list[Vacancy]) -> list[Vacancy]:
    seen = set()
    deduped = []
    for v in vacancies:
        key = (v.company, v.title, v.url)
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
    results: list[Vacancy] = []

    for title in SEARCH_TITLES:
        _limiter.acquire()
        try:
            resp = requests.post(
                INDEED_ACTOR_URL,
                headers=headers,
                json={
                    "position": title,
                    "location": SEARCH_LOCATION,
                    "maxItemsPerSearch": limit,
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            results.extend(_normalize_indeed(item) for item in resp.json())
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
            results.extend(_normalize_linkedin(item) for item in resp.json())
        except (requests.RequestException, ValueError):
            pass

    return _dedupe(results)[:limit]
