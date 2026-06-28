import os

import requests

APIFY_RUN_URL = (
    "https://api.apify.com/v2/acts/apify~website-content-crawler/run-sync-get-dataset-items"
)
TIMEOUT = 60
MAX_TEXT_LENGTH = 2000

FALLBACK = {"title": "", "description": "", "text_content": "No data found"}

FIXTURE = {
    "url": "https://example.co.za",
    "title": "Example Engineering Co.",
    "about": "A leading heavy engineering and fabrication firm based in Gauteng.",
    "services": ["Steel fabrication", "Plant maintenance", "Mechanical installations"],
    "recent_news": "Awarded new contract for mine conveyor system upgrade.",
    "description": "Heavy engineering and fabrication.",
    "text_content": "Example Engineering Co. is a leading firm based in Gauteng.",
}


class ApifyClient:
    def scrape_company(self, website: str) -> dict:
        if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
            return {**FIXTURE, "url": website}

        api_key = os.environ.get("APIFY_API_KEY", "")
        if not api_key:
            return {**FALLBACK, "url": website}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "startUrls": [{"url": website}],
            "maxCrawlPages": 3,
            "maxCrawlDepth": 1,
        }

        try:
            resp = requests.post(
                APIFY_RUN_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            items = resp.json()
        except (requests.RequestException, ValueError):
            return {**FALLBACK, "url": website}

        if not items or not isinstance(items, list):
            return {**FALLBACK, "url": website}

        first = items[0]
        text_content = first.get("text", first.get("body", ""))
        if len(text_content) > MAX_TEXT_LENGTH:
            text_content = text_content[:MAX_TEXT_LENGTH]

        return {
            "url": website,
            "title": first.get("title", ""),
            "description": first.get("description", first.get("metadata", {}).get("description", "")),
            "text_content": text_content or "No data found",
        }
