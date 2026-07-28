## 2026-07-28 — What it is, stack, open items
**Source:** Pappa T session (cross-project status survey), ai-outreach-agency's own CLAUDE.md/docs/todo.md/docs/architecture.md
**Status:** active

B2B outreach automation pipeline for heavy-engineering firms in Gauteng — Python
3.11+, SQLite, Claude via OpenRouter, local Ollama (`qwen3:8b`), Apify, Google
Sheets/Gmail APIs. Lives at `Pappa T/ai-outreach-agency/` — self-governing
sub-project with its own `CLAUDE.md`, not its own git repo (folder inside the Pappa
T vault repo, like TebelloReborn — see `tebelloreborn.md`). TebelloReborn's own
architecture deliberately mirrors this project's pipeline shape (SQLite source of
truth, enforced status state machine, `OFFLINE_MODE` fixture convention, structural
human-approval gate) — the two are the closest siblings in this vault.

Six-stage pipeline: Lead Import (CSV/Sheets) → Research (Apify scrape + local Ollama
summary) → Asset Gen (OpenRouter) → **mandatory human Approval Gate** (no code path
bypasses it) → Email Draft (Gmail API, draft-only, never auto-sent) → Send (fully
manual, no code).

**Open items as of 2026-07-19 (`docs/todo.md`):**
- **OpenRouter account out of credits** (HTTP 402 as of 2026-07-04) — blocks
  `asset_gen` from running a real (non-offline) batch until topped up at
  openrouter.ai/settings/credits, or until Build Queue A (headless Claude Code
  migration for `asset_gen`, mirroring TebelloReborn's ADR-003/Phase 5 — see
  `tebelloreborn.md`) lands. `research`'s own OpenRouter dependency is already
  resolved (ADR-004 moved it to local Ollama).
- **Local Ollama generation latency sits close to the 60s `READ_TIMEOUT` ceiling**
  on this (CPU-only) machine — a cold-load call can exceed 60s and raise a correctly-
  typed `OllamaError` (not a false `OllamaUnreachableError`), but this risks
  intermittent errors on an otherwise-healthy daemon during a real batch. Recommended
  fix (small, single-file, not yet implemented): bump `READ_TIMEOUT` 60s → 120s, and
  add `"keep_alive": "30m"` to the `/api/generate` payload to stop Ollama's default
  5-minute idle-unload from forcing a repeat cold-load mid-batch.
- **Build Queue A** (headless Claude Code for `asset_gen`) — planned, not yet built;
  full detail in its own `docs/specs/handoff-tracking-build.md`.

**Reusable gotchas/decisions (public-repo-level):**
- **ADR-004** (2026-07-19): `research`'s OpenRouter call moved to local Ollama
  (`qwen3:8b`, native `/api/generate`, no API key) — fails loud, no silent fallback
  to OpenRouter (which was itself out of credits — a silent fallback would have just
  swapped one dead backend for another with a more confusing error). Two distinct,
  never-conflated exception types: `OllamaUnreachableError` (connection-refused/
  connect-timeout, "is it running?") vs. `OllamaError` (read-timeout, "model may be
  slow/cold-loading") — a real conflation bug between the two was caught and fixed
  in commit `338002f`. `nomic-embed-text`/embeddings scoped out entirely — no
  consumer exists in the codebase (no semantic search/RAG/vector dedup; dedup is
  string-based).
- **Real bug found by an end-to-end (non-mocked) pipeline test, not by any unit
  test:** `src/main.py` wasn't threading `db_path=settings.DB_PATH` through
  `research_lead`/`run_asset_gen`/`run_approval_gate`/`run_email_draft` — a real
  `run`/`run-all` would fall back to `lead_import/db.py`'s `DEFAULT_DB_PATH`
  (`data/leads.db`, no `leads` table) and crash with `sqlite3.OperationalError: no
  such table: leads`. Unit tests mocked `update_lead_status` out, so only a CLI
  integration test caught it. General lesson (same shape as TebelloReborn's Apify
  payload bug, see `tebelloreborn.md`): mocking internal calls in unit tests can hide
  wiring bugs that only a real-path integration/CLI test will surface.
- **`approvals` table never written by the real pipeline**: `run_approval_gate`
  computed an `ApprovalResult` but never called `save_approval`/
  `init_approvals_table` — the table only ever existed in tests. Found while
  building the dashboard's approval-history view (which would otherwise always
  render empty). Same class of bug as the `db_path` one above — a persistence
  side-effect that every existing test mocked around.
- **n8n retired from the stack** (ADR-002) — orchestration is in-process via the
  project's own console script (`ai-outreach import/list/run/run-all`), no external
  workflow engine.
- Gmail integration uses OAuth2 (`credentials.json` + cached `token.json`,
  gitignored), **`gmail.compose` scope only** — no send capability exists in the
  codebase at all, by design, not just by convention.

**Not carried over:** ICP/customer-targeting specifics, lead schema field-level
detail, and full ADR text stay in the project's own `docs/` — this entry captures
reusable architecture/gotchas only, per the no-company-data rule.
