# Task Queue — ai-outreach-agency

> Updated: 2026-06-28

---

## Completed

- [x] **ADR-001**: Lead store format — SQLite is source of truth, Sheets/Apollo are CSV input only. See `docs/decisions/ADR-001-lead-store.md`.
- [x] Scaffold `lead_import` module — schema dataclass, CSV reader, SQLite layer, 16 unit tests passing.
- [x] Scaffold `research` module — Apify stub, Claude summariser stub, pipeline with missing-website handling.
- [x] Scaffold `asset_gen` module — prompt builder, generator stub, AssetType enum, pipeline with logging.
- [x] Scaffold `approval` module — CLI approval gate (approve/reject/edit/quit), SQLite persistence.
- [x] Scaffold `email_draft` module — composer, Gmail stub, pipeline guard on approval decision.
- [x] Create `.env.example` + `.gitignore` + `src/config.py` (Settings from .env via python-dotenv).
- [x] Create `src/main.py` CLI runner — import, list, run, run-all commands. 53 tests passing.

---

## Build Queue

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
