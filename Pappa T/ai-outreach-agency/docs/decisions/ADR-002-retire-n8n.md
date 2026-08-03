# ADR-002: Retire n8n from the Stack

**Status:** Accepted
**Date:** 2026-07-04
**Decider:** Tebello Lelosa

## Context

`docs/architecture.md` originally described n8n as an external orchestrator calling into each pipeline stage via `python -m src.<module>` CLI entry points, with n8n handling scheduling, retries, batch processing, and status webhooks. CLAUDE.md itself flagged this as unresolved: "n8n: listed historically in the stack but the pipeline is pure-Python CLI. Treat orchestration as in-process unless a future ADR reintroduces n8n. (Confirm/retire this in an ADR.)"

In practice, the pipeline has never called out to n8n. Orchestration already happens in-process: `src/main.py`'s `run-all` command fetches all leads matching a status (and now a campaign), loops over them, and calls `_run_single_lead` for each — with retry/backoff already handled per-client by the rate limiter and exponential backoff in `shared/openrouter_client.py`. No n8n workflow definitions exist, and the `ai-outreach` console script (not `python -m src.<module>`) is the actual entry point used throughout.

## Decision

**n8n is not part of the stack.** Orchestration stays in-process via the `ai-outreach` CLI (`run` for a single lead, `run-all` for a batch). No external workflow engine is introduced.

## Consequences

- No new dependency, no n8n workflow JSON files to build or maintain.
- Batch processing, retries, and rate limiting continue to be handled by the CLI and the shared `RateLimiter` (`src/shared/rate_limiter.py`), not by an external scheduler.
- `docs/architecture.md`'s "n8n Integration" section is replaced with a short pointer to this ADR.
- If a real orchestration need emerges later (e.g., scheduled unattended batch runs), it should be proposed as a new ADR rather than by reviving the original n8n section.
