# ADR-001: Lead Store Format

**Status:** Accepted
**Date:** 2026-06-28
**Decider:** Tebello Lelosa

## Context

The outreach pipeline needs a central data store for lead records. All pipeline stages (import, research, asset gen, approval, email draft) read from and write to this store. Options considered:

- **A. Google Sheets only** — visible, editable, but network-dependent and schema-weak
- **B. SQLite only** — offline-first, proper schema, fast, no rate limits
- **C. Hybrid** — SQLite as source of truth, Sheets as dashboard via API sync

## Decision

**SQLite is the pipeline source of truth.**

Google Sheets and Apollo.io are input sources via CSV export only. There is no live Google Sheets API integration. Leads enter the system through CSV files exported from Apollo.io or manually prepared spreadsheets.

## Consequences

- All pipeline modules read/write a local SQLite database
- No Google Sheets API dependency — removes OAuth complexity and rate limit concerns
- The pipeline works fully offline for all stages except research (Apify), asset gen (OpenRouter), and email draft (Gmail)
- Manual lead entry happens via CSV, not via Sheets API
- If a visual dashboard is needed later, it can be added as a read-only SQLite viewer or a lightweight web UI — not by re-introducing Sheets as a data layer
