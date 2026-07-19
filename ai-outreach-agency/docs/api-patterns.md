# API Patterns — ai-outreach-agency

> Updated: 2026-07-19

---

## OpenRouter (Claude API Inference)

Base URL: `https://openrouter.ai/api/v1/chat/completions`

Auth: `Authorization: Bearer $OPENROUTER_API_KEY`

Model routing:

| Task | Model ID | Max tokens |
|------|----------|------------|
| Planning, architecture | `anthropic/claude-opus-4` | 4096 |
| Asset generation, email drafts | `anthropic/claude-sonnet-4` | 4096 |
| Lead scoring, classification, search queries | `anthropic/claude-haiku-4` | 2048 |

Pattern: all LLM calls go through a single `openrouter_client.py` wrapper that handles auth, model selection, retries, and rate limiting.

> **As of ADR-004 (2026-07-19): `research/claude_summariser.py` no longer calls
> OpenRouter.** It moved to local Ollama inference — see the new section below.
> The only remaining OpenRouter call site is `asset_gen/generator.py`
> (`email_draft` never had its own OpenRouter call). That call site is
> scheduled to move to headless Claude Code under a separate, not-yet-built
> track (ADR-003 / `docs/specs/handoff-tracking-build.md`, Build Queue A) — as
> of this commit it still calls OpenRouter. Do not assume both tracks have
> landed just because one has.

---

## Local Ollama Inference (research)

Base URL: `http://localhost:11434` (default; overridable via `OLLAMA_BASE_URL`)

Auth: **none.** Ollama is a local daemon — there is no API-key analogue to
`OPENROUTER_API_KEY`. The client (`research/ollama_client.py`) has no
"missing key" guard, deliberately, because there is no key to be missing.

Endpoint: Ollama's **native** `POST /api/generate` — not the OpenAI-compatible
`/v1/chat/completions` surface. Request body:
`{"model": OLLAMA_MODEL, "prompt": prompt, "stream": false, "think": false}`.
`/api/generate` was chosen because it's Ollama's most stable native surface
and needs no message-array shaping for a single-prompt summarization task
(see ADR-004 §Decision.2). `think: false` suppresses `qwen3:8b`'s hybrid
reasoning trace so the `response` field comes back as clean prose; the
client also strips any surviving `<think>...</think>` block as a defensive
fallback in case a future model/version ignores the flag.

Model: `qwen3:8b` (default; overridable via `OLLAMA_MODEL`).

Pattern: `research/ollama_client.py::call_ollama(prompt)` is called from
`research/claude_summariser.py::summarise_lead()`'s non-offline branch — its
**only** consumer (single-consumer clients live beside their consumer module,
not in `shared/` — see ADR-004 §Decision.2 / §Alternatives.D). Rate-limited
via the same `RateLimiter` pattern as the other three clients
(`OLLAMA_RATE_LIMIT_PER_MIN`, default **120/min**) — largely a safety valve
here, since Ollama serialises generation locally and a slow local model will
never realistically approach that rate.

**No silent fallback to OpenRouter.** If Ollama is unreachable or errors,
`summarise_lead()` lets the exception propagate — it does not catch it and
retry against `call_openrouter`. This is deliberate: OpenRouter is also
currently out of credits (see Known Issues in `docs/todo.md`), so a silent
fallback would swap one dead backend for another and surface as a confusing
OpenRouter 402 instead of the actionable "Ollama isn't running" message. Full
reasoning in ADR-004 §Decision.5.

**Two distinct failure paths — do not conflate them:**

- **Connection-refused or connect-timeout → `OllamaUnreachableError`.** A
  short 3-second connect timeout (`CONNECT_TIMEOUT`) means a missing/stopped
  daemon fails fast with `"Ollama not reachable at <url> — is it running?
  Start Ollama or set OFFLINE_MODE=true."` This is the "is it running?" case
  — the TCP connection itself never completed.
- **Read-timeout (60s, `READ_TIMEOUT`) → `OllamaError`, a different exception
  type.** The TCP connection succeeded — the daemon is up and responding — it
  just didn't finish generating in time. Message: `"Ollama timed out
  generating a response after 60s — the model may be slow to respond or still
  cold-loading."` A read-timeout is not evidence the daemon is down, so it
  must not raise `OllamaUnreachableError` and must not share that message —
  the two failure modes call for different remediation (start Ollama vs. wait
  for the model to warm up / check hardware load).

Other error shapes: HTTP status ≥ 400 → `OllamaError` with the response body
(truncated); a 200 response missing the expected `response` field →
`OllamaError` on the `KeyError`/`TypeError`.

OFFLINE_MODE: `summarise_lead()` checks `OFFLINE_MODE` **before** any client
call and returns `_stub_summary()` when set — `call_ollama` is never invoked
by the test suite. No test makes real HTTP to `localhost:11434`; client-level
tests mock `requests.post` directly, matching how OpenRouter/Apify/Gmail are
tested.

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
- **Proactive rate limiting**: each external client (`shared/openrouter_client.py`, `research/apify_client.py`, `email_draft/gmail_client.py`, `research/ollama_client.py`) holds a module-level `RateLimiter` (`src/shared/rate_limiter.py`, token bucket) and calls `.acquire()` before every real network request. Defaults: OpenRouter 60/min, Apify 30/min, Gmail 20/min, Ollama 120/min — override via `OPENROUTER_RATE_LIMIT_PER_MIN`, `APIFY_RATE_LIMIT_PER_MIN`, `GMAIL_RATE_LIMIT_PER_MIN`, `OLLAMA_RATE_LIMIT_PER_MIN`. This throttles proactively, independent of the reactive 429 backoff above (Ollama has no 429 backoff — it's a local daemon, not a rate-limited SaaS API).
