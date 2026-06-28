# Task Queue — ai-outreach-agency

> Updated: 2026-06-28

---

## Completed

- [x] **ADR-001**: Lead store format — SQLite is source of truth, Sheets/Apollo are CSV input only. See `docs/decisions/ADR-001-lead-store.md`.
- [x] Scaffold `lead_import` module — schema dataclass, CSV reader, SQLite layer, 16 unit tests passing.

---

## Build Queue

- [ ] Scaffold `research` module — stub Apify integration, stub Claude summary call
- [ ] Scaffold `asset_gen` module — Claude API call stub via OpenRouter, template selection
- [ ] Scaffold `approval` module — CLI approval loop (print lead + asset, y/n/edit)
- [ ] Scaffold `email_draft` module — Gmail API draft creation stub
- [ ] Create `.env.example` with required environment variables
- [ ] Set up `pyproject.toml` with dependencies

---

## Future (not yet scheduled)

- [ ] Implement Apify actor integration for company research
- [ ] Implement OpenRouter client wrapper with model routing
- [ ] Implement Gmail OAuth2 flow + draft creation
- [ ] Implement Google Sheets sync (optional — not in current architecture)
- [ ] Build n8n workflow definitions
- [ ] Add lead deduplication logic
- [ ] Add rate limiting for external API calls
- [ ] Add campaign management (group leads by campaign, configure asset type per campaign)
- [ ] PDF export for generated assets
