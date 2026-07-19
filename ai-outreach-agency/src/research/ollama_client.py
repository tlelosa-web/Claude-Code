import os
import re

import requests

from src.shared.rate_limiter import RateLimiter

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:8b"
CONNECT_TIMEOUT = 3
READ_TIMEOUT = 60

RATE_LIMIT_PER_MIN = int(os.environ.get("OLLAMA_RATE_LIMIT_PER_MIN", "120"))
_limiter = RateLimiter(rate=RATE_LIMIT_PER_MIN, period=60.0)

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class OllamaError(Exception):
    pass


class OllamaUnreachableError(OllamaError):
    pass


def _strip_think_block(text: str) -> str:
    return _THINK_BLOCK_RE.sub("", text).strip()


def call_ollama(
    prompt: str,
    model: str | None = None,
    base_url: str | None = None,
) -> str:
    """Call Ollama's native /api/generate endpoint. No API key required —
    Ollama is a local daemon. Fails loudly (OllamaUnreachableError) rather
    than hanging or silently falling back to another backend."""
    model = model or os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)
    base_url = base_url or os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
    }

    _limiter.acquire()
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
    except requests.exceptions.ReadTimeout as e:
        # The connection succeeded — the daemon is running and responding —
        # it just didn't finish generating within READ_TIMEOUT. This is a
        # different failure mode from "Ollama isn't running" and must not
        # share that message (see ADR-004).
        raise OllamaError(
            f"Ollama timed out generating a response after {READ_TIMEOUT}s — "
            "the model may be slow to respond or still cold-loading."
        ) from e
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        raise OllamaUnreachableError(
            f"Ollama not reachable at {base_url} — is it running? "
            "Start Ollama or set OFFLINE_MODE=true."
        ) from e
    except requests.RequestException as e:
        raise OllamaError(f"Request failed: {e}") from e

    if resp.status_code >= 400:
        raise OllamaError(f"API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    try:
        return _strip_think_block(data["response"])
    except (KeyError, TypeError) as e:
        raise OllamaError(f"Unexpected response structure: {e}") from e
