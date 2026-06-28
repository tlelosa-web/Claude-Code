import os
import time

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"
TIMEOUT = 30


class OpenRouterError(Exception):
    pass


def call_openrouter(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "ai-outreach-agency",
    }

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    last_error = None
    for attempt in range(2):
        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            raise OpenRouterError(f"Request failed: {e}") from e

        if resp.status_code == 429 and attempt == 0:
            retry_after = int(resp.headers.get("Retry-After", "5"))
            time.sleep(min(retry_after, 10))
            last_error = f"Rate limited (429), retrying"
            continue

        if resp.status_code >= 400:
            raise OpenRouterError(
                f"API error {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise OpenRouterError(f"Unexpected response structure: {e}") from e

    raise OpenRouterError(last_error or "Max retries exceeded")
