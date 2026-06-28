# Task Queue — ai-outreach-agency

> Updated: 2026-06-28

---

## Pending Decisions

- [ ] **ADR-001**: Choose lead store format — Google Sheets vs SQLite local vs hybrid. Blocks all module scaffolding that touches data persistence. See `docs/architecture.md` § Lead Store for trade-off analysis.

---

## Build Queue

- [ ] Scaffold `lead_import` module — CSV reader + schema validator (dataclass + validation logic)
- [ ] Scaffold `research` module — stub Apify integration, stub Claude summary call
- [ ] Scaffold `asset_gen` module — Claude API call stub via OpenRouter, template selection
- [ ] Scaffold `approval` module — CLI approval loop (print lead + asset, y/n/edit)
- [ ] Scaffold `email_draft` module — Gmail API draft creation stub
- [ ] Write unit tests for `lead_import` schema validator
- [ ] Create `.env.example` with required environment variables
- [ ] Set up `pyproject.toml` with dependencies

---

## Future (not yet scheduled)

- [ ] Implement Apify actor integration for company research
- [ ] Implement OpenRouter client wrapper with model routing
- [ ] Implement Gmail OAuth2 flow + draft creation
- [ ] Implement Google Sheets sync (if hybrid store chosen)
- [ ] Build n8n workflow definitions
- [ ] Add lead deduplication logic
- [ ] Add rate limiting for external API calls
- [ ] Add campaign management (group leads by campaign, configure asset type per campaign)
- [ ] PDF export for generated assets
