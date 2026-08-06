# Knowledge Index

One line per file: topic, what it covers, last updated. Read this before
searching further — a matching row means the answer is already captured.

| File | Covers | Last updated |
|------|--------|---------------|
| `tlelosa-claude-config.md` | The private Claude Code plugin marketplace repo: structure, machine split (Operations/Pappa T), IT clearance status, CORE.md version, ADR-007/008/009 recorded in this hub's `docs/decisions/`; codex-gate install + network-off smoke-test both confirmed working; `/session-end` promotion + hub adoption, the spec-status/frontmatter gotchas found doing it, and two first-run defects (Step 3 over-appends, Step 5 unreachable) pending upstream backport | 2026-08-06 |
| `nameplatetool.md` | NamePlateTool (Fan Movement work project): stack, frontend/backend/PDF payload contract, uvicorn-supervisor kill gotcha, open Excel-import bug (still unfixed, top cross-project priority), testing status | 2026-07-28 |
| `cratetracker.md` | CrateTracker PWA (F1 Clash premium-crate predictor): structure, deploy steps, service-worker cache-busting, crate-cycle model | 2026-07-23 |
| `pitwall-companion.md` | Pitwall Companion / F1 Clash Resource Sheet PWA: structure, localStorage schema, cache-busting, modeling notes (boost scaling, live loadouts, Series-0 legendaries) | 2026-07-23 |
| `operations-hub.md` | Operations hub (Fan Movement work PC) cross-project findings: OneDrive+git corruption root cause and relocate-plus-junction fix; Operations ↔ cloud-environment git-sync bridge confirmed (clone path `C:\Dev\Claude-Code`); live gitignored runtime-data inventory + backup procedure (sqlite backup API, data/secrets split) | 2026-08-06 |
| `pappa-t.md` | Pappa T (personal machine): what it is vs. Operations, no live remote-environment bridge (git sync only), Pappa T-only items (codex-gate), 2026-07-28 vault survey findings; stale duplicate hub clone removed 2026-08-06 (corrects that survey's gitlink call); vault now pushes to private `tlelosa-web/pappa-t` on `main`, with the pre-push secrets/personal-data audit that cleared it | 2026-08-06 |
| `tebelloreborn.md` | TebelloReborn (Career Engine, Pappa T sub-project): job-application automation pipeline — stack, 5-stage MVP, ADR-003 inference split, doc-gen prompt-injection fix, fpdf2/Apify gotchas; Playwright pre-build verification (LinkedIn-vs-Indeed scope mismatch, shared `PRAGMA user_version` migration trap, storageState gitignore gap) | 2026-08-06 |
| `ai-outreach-agency.md` | ai-outreach-agency (Pappa T sub-project): B2B outreach pipeline — stack, 6-stage pipeline, OpenRouter-credits + Ollama-timeout open items, ADR-004, db_path/approvals wiring bugs | 2026-07-28 |
| `mims-app.md` | MIMS App (Pappa T sub-project): MRP web app — Next.js/Supabase/Tailwind stack, Gemini-driven (not Claude), Shop Floor stage in progress | 2026-07-28 |
| `iq-signal-generator.md` | IQ Option Signal Generator (Pappa T sub-project): regime-filtered trading-signal CLI — ADX/RSI/Stochastic logic, risk-management stops | 2026-07-28 |
| `tenders-sa.md` | Tenders (Pappa T sub-project): SA tender-monitoring automation — structure, `tenders-sa` submodule status, dormant bid-package folder note | 2026-07-28 |
| `sops.md` | SOPS (Fan Movement work project): Flask/SQLAlchemy/SQLite stack, TDD + held-migration convention, stale-dev-server gotcha, git-worktree/OneDrive history, concurrent-session git contamination pattern, AvgMovement-migration-go-ahead + Payment-Status-review outstanding items | 2026-07-28 |
| `delivery-note-system.md` | Delivery Note (Fan Movement work project): Next.js 16/Prisma 7/SQLite stack, Prisma-7 driver-adapter gotcha, Turbopack+Windows junction workaround, DN-number generation fix, no-test-suite outstanding item | 2026-07-28 |
| `daily-sales-order-files.md` | Daily Sales Order Files (Fan Movement work pipeline): 5-stage script pipeline, load-bearing folder layout, external OneDrive dependencies, self-correcting filename resolution, blank-over-stale design decision, healthy/no outstanding items | 2026-07-28 |
