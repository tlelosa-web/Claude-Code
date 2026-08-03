# CLAUDE.md — ai-outreach-agency

> DCOE v3.1 — Domain → Context → Orchestrate → Execute
> Loaded at the start of every Claude Code session. Single source of truth for how this project operates.
> Keep under 500 lines. Move deep docs to @imports.

---

## 📁 Project Overview

```
Project:     ai-outreach-agency
Type:        B2B outreach automation engine (Python CLI, offline-capable core)
Owner:       Tebello Lelosa
Stack:       Python 3.11+ · SQLite · Claude API via OpenRouter · local Ollama (qwen3:8b) · Apify · Google Sheets · Gmail API
Deployment:  Local Windows desktop, offline-capable core logic
Inference:   OpenRouter → claude-sonnet-5 @ medium (default) | claude-opus-4.8 (escalation) | claude-haiku-4.5 (search/scoring)
```

Automated pipeline that researches heavy engineering firms in Gauteng, generates custom insight assets per lead, and prepares Gmail drafts — with a mandatory human approval gate before any email is created.

Core docs:

- `docs/todo.md`: live task queue.
- `docs/architecture.md`: pipeline design and data flow.
- `docs/api-patterns.md`: API integration patterns (OpenRouter, local Ollama, Apify, Google Sheets, Gmail) + rate limiting.
- `docs/session-log.md`: chronological session memory.
- `docs/decisions/`: architecture decision records.

---

## ⚙️ Essential Commands

```bash
# Environment (Windows PowerShell)
pip install -e .                       # Install project + deps from pyproject.toml
pip install -e ".[dev]"                # + pytest and dev extras

# CLI runner (console script: ai-outreach)
ai-outreach import --file leads.csv    # Import + validate leads
ai-outreach list                       # List leads and current status
ai-outreach run --lead-id <id>         # Run one lead through the pipeline
ai-outreach run-all                    # Run all eligible leads

# Tests
python -m pytest                       # Full suite (currently 85 passing)
python -m pytest tests/unit            # Unit only
python -m pytest tests/integration     # Integration only

# Format + lint
black . && ruff check .

# Before every commit:
#   black . && ruff check . && python -m pytest
```

---

## 🧭 DCOE Rules

Every task follows this sequence:

1. **Domain**: classify the pipeline stage this work belongs to.
2. **Context**: load only the relevant module and its upstream/downstream interfaces.
3. **Orchestrate**: decide which module or agent owns the work.
4. **Execute**: complete one bounded task with a clear output and verification.

Hard rules:

- Domain before planning. Context before implementation.
- No large multi-file work without a plan. One task = one clear output = one atomic commit.
- **NO EMAIL SENDS WITHOUT HUMAN APPROVAL GATE.** Non-negotiable. The approval module sits between asset generation and email drafting. No code path may bypass it. Drafts are created in Gmail as drafts — never auto-sent.
- Never expose or hardcode secrets. All keys via `.env` (gitignored). `credentials.json` and `token.json` are gitignored too.
- **Offline-first**: core logic (lead import, schema validation, approval gate, local transforms) must work fully offline. Only network stages may touch the wire.
- **No schema changes without a migration file.** Ever.
- Update `docs/todo.md` after completed work. Update `docs/session-log.md` when durable context changes.

---

## 🎯 ICP (Ideal Customer Profile)

```
Industry:  Heavy manufacturing, engineering, fabrication, mining supply
Region:    Gauteng, South Africa
Size:      10–200 employees
Persona:   Operations Manager, Engineering Manager, Procurement Manager
```

---

## 🤖 Sub-Agent Roster

Agents live in `.claude/agents/`. Invoke by name or let Claude delegate.

| Agent        | File                    | When to Use                             |
|--------------|-------------------------|-----------------------------------------|
| `domain`     | `agents/domain.md`      | Session start, scope confirmation       |
| `planner`    | `agents/planner.md`     | Break features into spec + tasks        |
| `architect`  | `agents/architect.md`   | System design, ADRs, DB schema          |
| `executor`   | `agents/executor.md`    | Implement a single well-defined task    |
| `tester`     | `agents/tester.md`      | Write tests, TDD loops                   |
| `reviewer`   | `agents/reviewer.md`    | Code review, security, quality gate     |
| `doc-writer` | `agents/doc-writer.md`  | Update docs, README, changelogs         |
| `debugger`   | `agents/debugger.md`    | Systematic bug investigation            |
| `data-agent` | `agents/data-agent.md`  | CSV/Sheets transforms, lead processing  |

---

## 🧠 Inference Routing (OpenRouter) — v3.1

This section covers OpenRouter-routed LLM calls (the `ai-outreach` CLI's own
agent/build-time routing, and `asset_gen`'s runtime inference call).
**`claude-sonnet-5` at medium effort is the universal default for these.**
Opus is reserved for evidence-based escalation, not used by default.
**As of ADR-004, `research` summaries no longer go through OpenRouter** —
they run on a local `qwen3:8b` Ollama daemon instead (see External Client
Patterns below), which has no "effort tier"/model-routing concept — it's a
single fixed local model.

| Task class                                    | Model                     | Effort  | Why                                              |
|-----------------------------------------------|---------------------------|---------|--------------------------------------------------|
| **Default** — all standard work               | `anthropic/claude-sonnet-5` | medium  | Best quality/cost balance; universal baseline    |
| Asset generation, email drafting              | `anthropic/claude-sonnet-5` | medium  | Content generation                               |
| Lead scoring, quick classification, search    | `anthropic/claude-haiku-4.5`| low     | Fast and cheap for simple decisions              |
| **Escalation only** (see triggers below)      | `anthropic/claude-opus-4.8` | high    | Deep reasoning for genuinely hard problems       |
| Reviewer agent (permanent)                    | `anthropic/claude-opus-4.8` | high    | Quality/security gate stays on Opus, always      |

**Opus escalation is evidence-based.** Escalate to `claude-opus-4.8` only when one of these is true:

1. Two failed Executor attempts on the same task.
2. Deep architectural reasoning (ADRs, major planning, cross-cutting design).
3. Security review (auth, credential handling, data-export paths).

Do not reach for Opus on a hunch. Default Sonnet-5-medium; escalate on evidence.

**Effort tiers** map onto the Thinking Levels table below: `low` ≈ think, `medium` ≈ think hard, `high` ≈ think harder / ultrathink.

Set per-agent in frontmatter, e.g. `model: anthropic/claude-haiku-4.5`.

> ⏳ **Pricing deadline:** Sonnet 5 introductory pricing ($2/$10 per MTok) runs through **31 Aug 2026**. Schedule any large batch jobs (bulk lead research, full-corpus asset regen) **before** then. Flag these in `docs/todo.md` with an `[before-aug-31]` tag.

---

## 🔌 Offline-First Rule

Core pipeline logic (lead import, schema validation, approval gate, local data transforms) must work fully offline. Only these stages require network:

- Research (Apify web scraping + local Ollama inference — see ADR-004)
- Asset generation (OpenRouter API)
- Email drafting (Gmail API)
- Lead sync (Google Sheets API)

Design modules so offline stages never import or depend on network-requiring code. `OFFLINE_MODE` fixtures exist across all three external clients and must keep the full test suite green without network access.

---

## 🔁 Pipeline Stages

```
1. Lead Import     → CSV/Sheets → validated lead records          (status: new)
2. Research        → Apify scrape → local Ollama summary → enriched (status: researched)
3. Asset Gen       → Claude API (OpenRouter) → custom mini-report per lead (status: asset_ready)
4. Approval Gate   → Human reviews lead + asset → approve/reject  (status: approved | rejected)
5. Email Draft     → Claude API → Gmail draft (NOT sent)          (status: drafted)
6. Send            → Human clicks send in Gmail (fully manual)
```

> Stage 2 moved off OpenRouter onto a local Ollama daemon (`qwen3:8b`) per
> ADR-004 (2026-07-19) — zero marginal inference cost, and unblocks research
> independent of OpenRouter credit balance. Stage 3 (`asset_gen`) still calls
> OpenRouter as of this note; its own migration to headless Claude Code is a
> separate, not-yet-built track (ADR-003 / Build Queue A) — don't conflate
> the two.

**Lead status state machine** (`lead_import/db.py`, `VALID_TRANSITIONS`):
`new → researched → asset_ready → approved / rejected → drafted`. Transitions are enforced across the research/asset_gen/approval/email_draft pipelines — no stage may skip ahead.

---

## 🌐 External Client Patterns

All four network clients share a token-bucket rate limiter (`src/shared/rate_limiter.py`) applied ahead of every real network call:

| Client                          | Default rate | Env override                    |
|---------------------------------|--------------|---------------------------------|
| `shared/openrouter_client.py`   | 60 / min     | `OPENROUTER_RATE_LIMIT_PER_MIN` |
| `research/apify_client.py`      | 30 / min     | `APIFY_RATE_LIMIT_PER_MIN`      |
| `email_draft/gmail_client.py`   | 20 / min     | `GMAIL_RATE_LIMIT_PER_MIN`      |
| `research/ollama_client.py`     | 120 / min    | `OLLAMA_RATE_LIMIT_PER_MIN`     |

- **OpenRouter**: real inference from `asset_gen/generator.py` only — `research/claude_summariser.py` moved off OpenRouter onto local Ollama (ADR-004, 2026-07-19). 429s retried via mocked `time.sleep`. Watch for **HTTP 402** (out of credits) — top up at openrouter.ai/settings/credits before any batch run.
- **Local Ollama**: real inference from `research/claude_summariser.py` via `research/ollama_client.py`, native `POST /api/generate` against `qwen3:8b`, no API key (local daemon). Fails loudly — `OllamaUnreachableError` on connection-refused/connect-timeout ("is it running?"), `OllamaError` on read-timeout ("model may be slow/cold-loading") — these are distinct exception types for distinct causes, never collapsed into one message. No silent fallback to OpenRouter. See ADR-004 and `docs/api-patterns.md`.
- **Apify**: real website-content-crawler actor, with `OFFLINE_MODE` fixture and fallback on missing key or request failure.
- **Gmail**: OAuth2 via `InstalledAppFlow` against `credentials.json`, token cached/refreshed in `token.json`, real `drafts().create()` using the **`gmail.compose` scope only**. `OFFLINE_MODE` returns a `draft_{timestamp}` stub.

See @docs/api-patterns.md for full detail.

---

## 🔑 Environment & Secrets

`.env` (gitignored) — real values live here only. `.env.example` holds placeholders (e.g. `sk-or-replace-me`) and must **never** contain a real key.

| Var                                | Purpose                                  |
|------------------------------------|------------------------------------------|
| `OPENROUTER_API_KEY`               | OpenRouter inference (asset_gen only, as of ADR-004) |
| `OLLAMA_BASE_URL`                  | Local Ollama daemon URL (default `http://localhost:11434`) |
| `OLLAMA_MODEL`                     | Local Ollama model for research summaries (default `qwen3:8b`) |
| `APIFY_TOKEN`                      | Apify scraping (name per api-patterns)    |
| `DB_PATH`                          | Source-of-truth SQLite (default `outreach.db`) |
| `OFFLINE_MODE`                     | Force offline stubs for all network stages |
| `*_RATE_LIMIT_PER_MIN`             | Per-client rate overrides (see table)     |

Gmail auth files (project root, gitignored): `credentials.json` (Desktop OAuth client from the `ai-outreach-agency` GCP project) and `token.json` (cached after first browser consent). Consent screen is in **Testing** status — the signing-in Google account must be on the test-user list or OAuth returns `Error 403: access_denied`.

> ⚠️ **DB_PATH gotcha:** `main.py` must thread `db_path=settings.DB_PATH` through `research_lead` / `run_asset_gen` / `run_approval_gate` / `run_email_draft`. If it doesn't, they fall back to `lead_import/db.py`'s `DEFAULT_DB_PATH` (`data/leads.db`), which has no `leads` table → `sqlite3.OperationalError: no such table: leads`. Unit tests mock `update_lead_status` out, so only the CLI integration test (`TestMainCLIRunCommand`) catches this. Do not regress it.

---

## 📐 Architecture Decisions

> Keep this section current. It overrides assumptions from training data.

- **ADR-001**: SQLite is the source of truth. Google Sheets and Apollo.io are **CSV-only inputs** — never authoritative stores.
- **DB access**: SQLite via `sqlite3`. No schema change without a migration file.
- **Config**: `src/config.py` `Settings` via `python-dotenv`. Never hardcode. Never commit `.env`.
- **Packaging**: `pyproject.toml` — core deps (`requests`, `python-dotenv`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`); `pytest` as dev extra; `ai-outreach` console-script entry point.
- **Approval gate is structural**, not advisory — enforced by the status state machine, not just convention.
- **Offline-first**: no feature may depend on internet connectivity in its core logic.
- **ADR-002**: n8n retired from the stack — orchestration stays in-process via the `ai-outreach` CLI (`run`/`run-all`). See `docs/decisions/ADR-002-retire-n8n.md`.
- **ADR-004**: `research/claude_summariser.py` moved from OpenRouter to local Ollama (`qwen3:8b`, native `/api/generate`) inference — $0 marginal cost, fails loudly (no silent OpenRouter fallback) on an unreachable daemon, distinguishes connect-timeout ("is it running?") from read-timeout ("model slow/cold-loading") as separate exception types. `nomic-embed-text`/embeddings deliberately scoped out — no consumer exists in the codebase. `asset_gen` is untouched by this ADR and still calls OpenRouter (its own migration is ADR-003, a separate track). See `docs/decisions/ADR-004-local-ollama-research-inference.md`.

See @docs/decisions/ for the full ADR log.

---

## 🧪 Testing Standards

Follow **TDD** for all new features:

```
1. Write failing tests first            (RED)
2. Implement minimal passing code       (GREEN)
3. Refactor for clarity and quality     (IMPROVE)
4. Coverage ≥ 80% on all new code
```

- Unit: `tests/unit/` — pure functions, no DB. `conftest.py` autouse fixture mocks `update_lead_status`.
- Integration: `tests/integration/` — real CLI entry point end-to-end (`TestMainCLIRunCommand` runs through `main([...])`, not stages directly).
- Never delete or skip tests to make them pass. Reviewer (Opus) must approve the suite before merge.
- Current baseline: **153 passing** (as of Build Queue B / ADR-004, 2026-07-19).

---

## 🪝 Hooks

Quality gates fire automatically. Do not disable without a deliberate decision.

| Hook            | Trigger      | Action                                    |
|-----------------|--------------|-------------------------------------------|
| `pre-commit`    | `git commit` | Run lint + format check. Block if fails.  |
| `pre-push`      | `git push`   | Run full test suite. Block if fails.      |
| `post-task`     | Agent stops  | Log summary to `docs/session-log.md`      |
| `session-start` | New session  | Load `docs/todo.md` into context          |

Hook configs: `.claude/hooks/`. **Philosophy:** block at commit time, not write time. Let agents finish before the gate fires.

---

## 🌳 Git Worktree Workflow

Use worktrees for all parallel Executor tasks. Never run concurrent agents on the same branch.

```bash
git worktree add ../worktree-feature-x -b feature/x
git worktree remove ../worktree-feature-x     # after commit
git cherry-pick <commit-hash>                 # Orchestrator integrates
```

Rules: one agent per worktree · each Executor commits atomically before stopping · Orchestrator reviews and integrates, never commits unreviewed code · clean up worktrees after merge.

---

## 🔐 Security & Permissions

- Default to minimal permissions. Expand per-agent only as needed.
- Secrets in `.env` only. Never in code, comments, or agent context. Never paste a real key into `.env.example`.
- No `DROP TABLE`, `DELETE FROM`, or `rm -rf` without explicit confirmation.
- Gmail scope stays `gmail.compose` only — no broader scope without a security review (Opus).
- Reviewer agent (Opus) runs on all auth, file-write, and data-export code.

---

## 📝 Code Standards

```python
def get_lead(lead_id: int, db_path: str) -> dict | None:   # explicit types
    """Fetch a single lead by ID. Returns None if not found."""
    ...
```

- Functions < 50 lines · files < 300 lines · `snake_case` for Python.
- Comments explain **why**, not **what**. No bare `except:`.
- Use a logger, not `print`. Convert `# TODO` into `docs/todo.md` tasks.

---

## 📂 Directory Structure

```
ai-outreach-agency/
├── CLAUDE.md                    ← project brain (this file)
├── pyproject.toml               ← deps + ai-outreach console script
├── .env.example                 ← placeholders only (never real keys)
├── credentials.json / token.json ← Gmail OAuth (gitignored)
├── docs/
│   ├── todo.md                  ← live task queue
│   ├── architecture.md          ← pipeline design
│   ├── api-patterns.md          ← API + rate-limit patterns
│   ├── session-log.md           ← session memory
│   ├── decisions/               ← ADRs (ADR-001: SQLite = source of truth)
│   ├── specs/                   ← feature specs
│   ├── bugs/                    ← bug root-cause reports
│   └── research/                ← research notes
├── .claude/
│   ├── agents/                  ← DCOE agent definitions
│   ├── hooks/                   ← lifecycle hooks
│   └── commands/                ← custom slash commands
├── tests/
│   ├── unit/
│   └── integration/             ← test_full_pipeline.py (TestMainCLIRunCommand)
└── src/
    ├── main.py                  ← CLI runner (import/list/run/run-all)
    ├── config.py                ← Settings via python-dotenv
    ├── shared/
    │   ├── openrouter_client.py ← OpenRouter inference (rate-limited)
    │   └── rate_limiter.py      ← token-bucket RateLimiter
    ├── lead_import/             ← CSV reader + schema validator + db.py (state machine)
    ├── research/                ← apify_client.py + ollama_client.py (ADR-004) + claude_summariser.py
    ├── asset_gen/               ← generator.py (custom asset per lead)
    ├── approval/                ← CLI human approval gate
    └── email_draft/             ← composer + gmail_client.py (OAuth2)
```

---

## ⚠️ Hard Rules — Never Violate

1. **No email sends without the human approval gate.** Drafts only.
2. **No code without a plan** for any task touching > 2 files.
3. **One task = one commit** — atomic, traceable, revertable.
4. **Tests must pass** before any commit. Hooks enforce this.
5. **No secrets in code** — not even in comments, debug prints, or `.env.example`.
6. **No schema changes without a migration file.**
7. **Offline-first always** — core logic never depends on connectivity.
8. **Default Sonnet-5-medium; escalate to Opus only on evidence** (2 failures / deep design / security).
9. **Orchestrator routes. Executors build.** Never reverse this.
10. **If acceptance criteria are unclear → STOP and ask** before implementing.
11. **Update docs/todo.md** after every completed task.
12. **Schedule bulk jobs before 31 Aug 2026** (Sonnet 5 intro pricing ends).
13. **Run `/codex-review` on every spec in `docs/specs/` before dispatching an Executor** — advisory cross-family second opinion, appended to the spec, never blocking. Fold the strongest points (buried assumptions, missing acceptance criteria, real failure modes) back into the spec as a dated Amendment section before build starts. Standard procedure for every spec, not optional. The `reviewer` agent still holds sole APPROVE/BLOCK authority — Codex is advisory only.

---

## 📎 Quick Reference: Thinking Levels

| Prompt Modifier | Effort tier | Use When                                        |
|-----------------|-------------|-------------------------------------------------|
| *(none)*        | —           | Trivial edits, quick lookups                    |
| `think`         | low         | Standard single-module changes                  |
| `think hard`    | medium      | Cross-module work, route/model changes          |
| `think harder`  | high        | Complex debugging, multi-system interactions    |
| `ultrathink`    | high        | Architecture decisions, major planning          |

---

*This CLAUDE.md is a living document. Update it when new ADRs are made, stack/tooling changes, new agents or patterns are added, or hard lessons emerge.*

*Last review: 2026-07-19 — Tebello Lelosa · DCOE v3.1*
