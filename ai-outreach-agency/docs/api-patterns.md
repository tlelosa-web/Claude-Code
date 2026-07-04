# API Patterns — ai-outreach-agency

> Updated: 2026-06-28

---

## OpenRouter (Claude API Inference)

Base URL: `https://openrouter.ai/api/v1/chat/completions`

Auth: `Authorization: Bearer $OPENROUTER_API_KEY`

Model routing:

| Task | Model ID | Max tokens |
|------|----------|------------|
| Planning, architecture | `anthropic/claude-opus-4` | 4096 |
| Asset generation, email drafts, research summaries | `anthropic/claude-sonnet-4` | 4096 |
| Lead scoring, classification, search queries | `anthropic/claude-haiku-4` | 2048 |

Pattern: all LLM calls go through a single `openrouter_client.py` wrapper that handles auth, model selection, retries, and rate limiting.

---

## Apify (Web Scraping)

Base URL: `https://api.apify.com/v2`

Auth: `Authorization: Bearer $APIFY_API_KEY`

Usage: trigger a web scrape actor with a company URL, poll for results, return scraped text content. Actor selection TBD during research module implementation.

---

## Gmail API (Draft Creation)

Auth: OAuth2 via `credentials.json` (local, gitignored)

Scope: `https://www.googleapis.com/auth/gmail.compose` (drafts only — no send scope)

Pattern: create draft with MIME message. Never use `messages.send`. Only `drafts.create`.

---

## Google Sheets API (Lead Import/Sync)

Auth: OAuth2 via same `credentials.json`

Scope: `https://www.googleapis.com/auth/spreadsheets`

Pattern: read rows from a named sheet, map columns to lead schema fields. Optional write-back for status updates.

---

## Common Patterns

- All API keys from environment variables (`.env`, loaded via `python-dotenv`)
- Exponential backoff on 429/5xx responses
- Timeout: 30s default, 60s for asset generation
- All responses logged at DEBUG level (no PII in logs)
- **Proactive rate limiting**: each external client (`shared/openrouter_client.py`, `research/apify_client.py`, `email_draft/gmail_client.py`) holds a module-level `RateLimiter` (`src/shared/rate_limiter.py`, token bucket) and calls `.acquire()` before every real network request. Defaults: OpenRouter 60/min, Apify 30/min, Gmail 20/min — override via `OPENROUTER_RATE_LIMIT_PER_MIN`, `APIFY_RATE_LIMIT_PER_MIN`, `GMAIL_RATE_LIMIT_PER_MIN`. This throttles proactively, independent of the reactive 429 backoff above.
