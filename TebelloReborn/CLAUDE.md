# CLAUDE.md — TebelloReborn (Career Engine)

> DCOE v3.1 — Domain → Context → Orchestrate → Execute
> Loaded at the start of every Claude Code session in this project. Single source of truth for how this project operates.
> Keep under 500 lines. Move deep docs to @imports.

---

## 📁 Project Overview

```
Project:     TebelloReborn (Career Engine)
Type:        Semi-automated job application system (Python CLI, offline-capable core)
Owner:       Tebello Lelosa
Stack:       Python 3.11+ · SQLite · local Ollama (qwen3:8b) · headless Claude Code · Apify (job-board scraping) · fpdf2
Deployment:  Local Windows desktop, offline-capable core logic
Inference:   Local Ollama (`qwen3:8b`, fixed model) — AI Matching | Headless Claude Code (Tebello's own subscription) — Document Generation | no OpenRouter, no model/effort routing (ADR-003)
```

Continuously finds job vacancies matching Tebello's profile, scores them, generates a tailored CV and cover letter per vacancy, and stops for a mandatory human approval gate before anything leaves the system. **No auto-submission in this build** — that's a deferred future phase.

This project supersedes the earlier hand-built prototype that lived in this same folder (Qwen-era scripts, hardcoded recruiter lists, never-run email automation). That prototype is preserved, untouched, in `_archive_qwen_prototype/` for reference — nothing was deleted.

Core docs:

- `docs/todo.md`: live task queue.
- `docs/architecture.md`: pipeline design and data flow.
- `docs/api-patterns.md`: API integration patterns (local Ollama, headless Claude Code, Apify) + rate limiting.
- `docs/session-log.md`: chronological session memory.
- `docs/decisions/`: architecture decision records.

This project is a sibling of `ai-outreach-agency` (also in this Master Vault) and deliberately mirrors its architecture — SQLite source of truth, rate-limited external clients, `OFFLINE_MODE` test fixtures, a structural (not advisory) human-approval gate. Where a pattern already exists there and works, it is reused here rather than reinvented.

---

## ⚙️ Essential Commands

```bash
# Environment (Windows PowerShell)
pip install -e .                          # Install project + deps from pyproject.toml
pip install -e ".[dev]"                   # + pytest and dev extras

# CLI runner (console script: career-engine — placeholder name, confirm before first real use)
career-engine import-profile --file data/profile_seed.json   # Load/update candidate profile
career-engine fetch-vacancies --limit 25                      # Scrape Indeed + LinkedIn via Apify
career-engine list                                             # List vacancies and current status
career-engine run --vacancy-id <id>                            # Score + generate assets for one vacancy
career-engine run-all                                          # Run all eligible vacancies
career-engine submit --vacancy-id <id>                         # Stage 6: submit an approved application, or record why it wasn't
career-engine submit --all                                     # Same, for every approved vacancy
career-engine submit --vacancy-id <id> --manual                # Record that you submitted it by hand

# Tests
python -m pytest                          # Full suite
python -m pytest tests/unit               # Unit only
python -m pytest tests/integration        # Integration only
python -m pytest --cov=src/<module> --cov-fail-under=80        # Coverage gate for new code (needs the dev extra)

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
- **NO APPLICATION SUBMITTED WITHOUT HUMAN APPROVAL GATE.** Non-negotiable. The review module sits between document generation and any future submission stage. No code path may bypass it. This build (MVP) stops at `approved` — no auto-submission exists yet.
- Never expose or hardcode secrets. All keys via `.env` (gitignored).
- **Offline-first**: core logic (profile import, schema validation, approval gate, local transforms) must work fully offline. Only network stages may touch the wire.
- **No schema changes without a migration file.** Ever.
- Update `docs/todo.md` after completed work. Update `docs/session-log.md` when durable context changes.
- **Governance**: `docs/domain-brief.md` at the vault root states *"Do not execute business/career actions without explicit approval."* This project's approval gate is how that rule is enforced in code — never weaken it.

---

## 🎯 Target Candidate Profile

```
Candidate:  Tebello Lelosa — 19+ years, 5 promotions across 3 companies
Titles:     Operations Foreman / Operations Manager, Project Engineer (Mechanical),
            Supply Chain Supervisor/Manager, Production Planner
Industries: Manufacturing, heavy industry, power generation, mining-adjacent
Region:     Gauteng, South Africa
Notes:      Two existing CV variants frame this differently (Ops-lead vs Project-Engineer-lead).
            profile_seed.json should carry both title lanes until the user confirms a single
            primary weighting — do not collapse to one lane by assumption.
```

---

## 🤖 Sub-Agent Roster

Agents live in `.claude/agents/`. Invoke by name or let Claude delegate.

| Agent        | File                    | When to Use                             |
|--------------|-------------------------|------------------------------------------|
| `domain`     | `agents/domain.md`      | Session start, scope confirmation        |
| `planner`    | `agents/planner.md`     | Break features into spec + tasks         |
| `architect`  | `agents/architect.md`   | System design, ADRs, DB schema           |
| `executor`   | `agents/executor.md`    | Implement a single well-defined task     |
| `tester`     | `agents/tester.md`      | Write tests, TDD loops                   |
| `reviewer`   | `agents/reviewer.md`    | Code review, security, quality gate      |
| `doc-writer` | `agents/doc-writer.md`  | Update docs, README, changelogs          |
| `debugger`   | `agents/debugger.md`    | Systematic bug investigation             |
| `data-agent` | `agents/data-agent.md`  | Profile/vacancy data transforms          |

---

## 🧠 Inference Routing (Local Ollama + Headless Claude Code) — v3.1

**As of ADR-003 (2026-07-19), TebelloReborn has no OpenRouter call sites at all** — this isn't a partial migration, OpenRouter is dropped entirely from the project's inference stack. The two inference-bearing pipeline stages each route to a fixed local backend, chosen by workload shape (mirrors the *pattern* — not the code — of `ai-outreach-agency`'s own ADR-004 / ADR-003 split):

- **AI Matching** (`matching/scorer.py`) calls a **local Ollama daemon** (`qwen3:8b`, native `POST /api/generate`, no API key) via `shared/ollama_client.py` (promoted from `matching/ollama_client.py` in Phase 9 once it gained a second consumer, ADR-003 §Alternatives.D). This is a single fixed model — there is no "effort tier" or model-routing concept here, the same shape as `ai-outreach-agency`'s Ollama-routed `research` stage.
- **Document Generation** (`doc_gen/cv_generator.py` + `cover_letter_generator.py`) shells out to **headless Claude Code** (`claude -p ... --allowedTools "Read,Write" --output-format json`) as a local subprocess under Tebello's own Claude subscription — $0 marginal cost, no API key. Also a fixed invocation, not a model/effort-routing table.

Neither backend has an "Opus escalation" concept — there is no OpenRouter model tier left to escalate within, and no per-token cost/pricing-deadline concern (both run at flat cost against local resources). Full reasoning: `docs/decisions/ADR-003-inference-provider-split.md`.

> This section covers **pipeline inference only** (AI Matching, Document Generation). It does not touch DCOE agent-routing — the `.claude/agents/` roster's own model assignments for planner/architect/executor/etc. are a separate concern from pipeline inference and are unaffected by this ADR.

---

## 🔌 Offline-First Rule

Core pipeline logic (profile import, schema validation, approval gate, local data transforms) must work fully offline. Only these stages require network:

- Vacancy fetch (Apify — Indeed + LinkedIn actors, and the generic crawler + local LLM extraction for PNet/Careers24)
- AI matching / scoring (local Ollama)
- Document generation (headless Claude Code)

Design modules so offline stages never import or depend on network-requiring code. An `OFFLINE_MODE` fixture (identical convention to `ai-outreach-agency`) exists across both external clients and must keep the full test suite green without network access.

---

## 🔁 Pipeline Stages (MVP)

```
1. Profile Import   → data/profile_seed.json → SQLite             (one-time / updated as CV evolves)
2. Vacancy Fetch     → Apify (Indeed + LinkedIn) → SQLite          (status: new)
3. AI Matching       → Local Ollama (qwen3:8b) scores profile vs vacancy      (status: scored)
4. Document Gen      → Headless Claude Code generates tailored CV + cover letter (status: asset_ready)
5. Human Review      → approve / reject / edit                     (status: approved | rejected)
```

```
6. Submission        → records an outcome per approved application          (status: submitted | submission_failed | unchanged)
```

Stage 6's **platform-agnostic core is built** (2026-08-06, `docs/specs/submission-core.md`): status vocabulary, the `submissions` attempt log, session-state path handling, capability-based adapter dispatch, and outcome recording. Its **site adapter is not** — the registry ships empty, so every approved application produces a `not_supported` attempt, is reported to the operator with an instruction to submit it by hand, and stays at `approved`. No `playwright` dependency, no browser binary, nothing on the wire.

The Indeed adapter's **Phases A and B are built** (2026-08-07, `docs/specs/indeed-submit-adapter.md`): profile contact details, then the `submission_preps`/`screening_questions` tables, the `pending_review` outcome, and the `submission_prep_ready()` gate. Still offline, still no adapter registered. Phases C–H remain — Indeed's apply flow will add three commands run in sequence:

```
career-engine prep-submission --vacancy-id <id>   (network, read-only recon — extracts screening questions)
career-engine review-questions --vacancy-id <id>  (offline — approve/edit each drafted answer)
career-engine submit --vacancy-id <id>            (network — unchanged command, now question-aware)
```

Building an adapter is gated on the platform question and the ToS/account-risk acknowledgement in that spec's Open Items.

One phase remains explicitly **deferred, not built**:

```
7. Dashboard      → tracking view: applications, match scores, response rate (future)
```

Vacancy status state machine mirrors the lead lifecycle pattern in `ai-outreach-agency` — enforced transitions, no stage may skip ahead.

---

## 🌐 External Client Patterns

The rate-limited network clients share the token-bucket rate limiter pattern from `ai-outreach-agency/src/shared/rate_limiter.py` (copied in, not re-invented):

| Client                              | Source                         | Default rate | Env override                  |
|--------------------------------------|---------------------------------|---------------|--------------------------------|
| `shared/ollama_client.py`            | Mirrors `research/ollama_client.py` pattern (ADR-003); promoted from `matching/ollama_client.py` in Phase 9 once it gained a second consumer (ADR-003 §Alternatives.D) — shared by `matching/scorer.py` and `vacancy_search/extractor.py` | 120 / min | `OLLAMA_RATE_LIMIT_PER_MIN` |
| `vacancy_search/apify_client.py`     | Mirrors `research/apify_client.py` pattern | 30 / min | `APIFY_RATE_LIMIT_PER_MIN`      |
| `vacancy_search/crawler_client.py`   | Mirrors `research/apify_client.py`'s generic-crawler pattern; Apify's `website-content-crawler` actor, used for PNet/Careers24 | 30 / min | `CRAWLER_RATE_LIMIT_PER_MIN` |

`vacancy_search/discovery.py` (PNet/Careers24 search-URL discovery, see below) has **no rate limiter of its own** — it reuses `crawler_client.py`'s limiter transitively via `fetch_raw_page()`.

The `doc_gen/` runner is **not** in this table — it is a local subprocess under a flat-cost subscription, not a rate-limited HTTP client, so no token-bucket applies to it (same distinction `ai-outreach-agency` draws between its handoff runner and its rate-limited clients).

- **Local Ollama**: real inference for matching (`matching/scorer.py`) and PNet/Careers24 field extraction (`vacancy_search/extractor.py`) via `shared/ollama_client.py`, native `POST {OLLAMA_BASE_URL}/api/generate` against `qwen3:8b`, no API key (local daemon). Fails loudly — `OllamaUnreachableError` on connection-refused/connect-timeout ("is it running?"), `OllamaError` on read-timeout ("model may be slow/cold-loading") — distinct exception types for distinct causes, never collapsed into one message. No silent fallback (and after ADR-003 there is no OpenRouter left to fall back to anyway). See ADR-003 and `docs/api-patterns.md`.
- **Headless Claude Code**: real document generation (`doc_gen/cv_generator.py` + `cover_letter_generator.py`) via a `src/doc_gen/` runner that shells out to `claude -p ... --allowedTools "Read,Write" --output-format json` as a local subprocess, under Tebello's own Claude subscription ($0 marginal cost, no API key). This is a **local runtime dependency, not an HTTP client** — the `claude` binary must be on `PATH` and authenticated on whatever machine runs it, which is not pip-installable or CI-verifiable and surfaces as a runtime error, not an import-time failure. Failures are data, not exceptions: the runner returns `throttled`/`error` as result fields so a throttle mid-`run-all` doesn't crash the batch; only a genuinely unexpected condition (`claude` missing from `PATH`) propagates. See ADR-003.
- **Apify**: two dedicated job-board actors (Indeed scraper, LinkedIn Jobs scraper). **PNet and Careers24 have no dedicated actor** (ADR-002) — covered instead via the generic `website-content-crawler` actor (`crawler_client.py`) plus local-Ollama field extraction (`extractor.py`), fed by automated search-URL discovery (`discovery.py`), not deferred any more — see ADR-002's 2026-07-29 amendment and `docs/api-patterns.md`. `OFFLINE_MODE` fixture returns 2–3 fake vacancies per client, matching the `FIXTURE` convention.

See @docs/api-patterns.md for full detail.

---

## 🔑 Environment & Secrets

`.env` (gitignored) — real values live here only. `.env.example` holds placeholders and must **never** contain a real key.

| Var                                | Purpose                                    |
|-------------------------------------|---------------------------------------------|
| `OLLAMA_BASE_URL`                   | Local Ollama daemon URL (default `http://localhost:11434`) |
| `OLLAMA_MODEL`                      | Local Ollama model for AI Matching (default `qwen3:8b`) |
| `APIFY_API_KEY`                     | Apify scraping (shared account — already funded/working)      |
| `DB_PATH`                           | Source-of-truth SQLite (default `career.db`) |
| `OFFLINE_MODE`                      | Force offline stubs for all network stages   |
| `*_RATE_LIMIT_PER_MIN`              | Per-client rate overrides                    |

The headless Claude Code doc-gen runner needs **no new env var** — its auth is the local `claude` CLI's own login state, not a project secret.

No Gmail integration in the MVP (no email-sending stage) — may be added if/when a submission or notification phase is built.

---

## 📐 Architecture Decisions

> Keep this section current. It overrides assumptions from training data.

- **ADR-001**: SQLite is the source of truth for profile + vacancy data (mirrors `ai-outreach-agency` ADR-001).
- **ADR-002**: Job-board scraping via Apify (Indeed + LinkedIn actors) for MVP; PNet/Careers24 covered via the generic crawler + local LLM extraction + automated discovery (2026-07-29 amendment) — no dedicated Apify actor exists for either.
- **ADR-003**: OpenRouter dropped entirely — AI Matching routes to local Ollama (`qwen3:8b`), Document Generation routes to headless Claude Code (`claude -p`), $0 marginal cost on both, no scheduler/volume-cap machinery adopted (no documented need). See `docs/decisions/ADR-003-inference-provider-split.md`.
- **ADR-004**: `PRAGMA user_version` retired as a migration gate — a `schema_migrations(module, version, applied_at)` ledger plus one shared runner in `src/shared/migrations.py`. Versions are per-module; migration payloads may be a SQL string or a callable. See `docs/decisions/ADR-004-schema-migration-ledger.md`.
- **DB access**: SQLite via `sqlite3`. No schema change without a migration file.
- **Config**: `src/config.py` `Settings` via `python-dotenv`. Never hardcode. Never commit `.env`.
- **Approval gate is structural**, not advisory — enforced by the status state machine, not just convention (same principle as `ai-outreach-agency`).
- **Offline-first**: no feature may depend on internet connectivity in its core logic.

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

- Unit: `tests/unit/` — pure functions, no DB. `conftest.py` autouse fixture forces `OFFLINE_MODE=true` (mirrors `ai-outreach-agency`'s conftest exactly).
- Integration: `tests/integration/` — real CLI entry point end-to-end.
- Never delete or skip tests to make them pass.

---

## 🔐 Security & Permissions

- Default to minimal permissions. Expand per-agent only as needed.
- Secrets in `.env` only. Never in code, comments, or agent context.
- No `DROP TABLE`, `DELETE FROM`, or `rm -rf` without explicit confirmation.
- Personal data handling: this project stores real personal/career data (CV content, contact details). Treat with the same care as credentials — never log full profile/vacancy content at INFO level, no PII in committed fixtures beyond what's already public in the source CVs.
- Reviewer agent runs on all data-handling and any future submission/export code.

---

## 📝 Code Standards

```python
def get_vacancy(vacancy_id: int, db_path: str) -> dict | None:   # explicit types
    """Fetch a single vacancy by ID. Returns None if not found."""
    ...
```

- Functions < 50 lines · files < 300 lines · `snake_case` for Python.
- Comments explain **why**, not **what**. No bare `except:`.
- Use a logger, not `print`. Convert `# TODO` into `docs/todo.md` tasks.

---

## 📂 Directory Structure

```
TebelloReborn/
├── CLAUDE.md                     ← project brain (this file)
├── pyproject.toml                ← deps + career-engine console script
├── .env.example                  ← placeholders only
├── data/
│   ├── profile_seed.json         ← structured candidate profile (to be authored)
│   ├── Tebello_Lelosa_Master_CV_2026.md   ← source CV, copied forward for reference
│   ├── crawler_seed_urls.json    ← PNet fallback seed URLs (job-detail pages only) + Careers24 placeholders
│   ├── discovery_config.json     ← PNet manual-verification gate (mode: auto | manual_pending_verification)
│   └── legacy_reference/         ← old tracker + recruiter DB, read-only history
├── _archive_qwen_prototype/      ← everything from the old hand-built prototype, preserved
├── docs/
│   ├── todo.md
│   ├── architecture.md
│   ├── api-patterns.md
│   ├── session-log.md
│   └── decisions/                ← ADR-001, ADR-002 (+ 2026-07-29 discovery amendment), ADR-003
├── .claude/
│   ├── agents/                   ← DCOE agent definitions
│   └── commands/
├── tests/
│   ├── unit/
│   └── integration/
└── src/
    ├── main.py                   ← CLI runner
    ├── config.py                 ← Settings via python-dotenv
    ├── shared/                   ← rate_limiter.py, ollama_client.py (ADR-003; promoted from matching/ in Phase 9),
    │                                migrations.py (ADR-004 — the one migration runner, five consumers)
    ├── profile/                  ← CandidateProfile schema + db
    ├── vacancy_search/           ← Vacancy schema + db + apify_client.py + crawler_client.py +
    │                                discovery.py + extraction_prompt.py + extractor.py (PNet/Careers24)
    ├── matching/                 ← prompt_builder.py + scorer.py (ADR-003)
    ├── doc_gen/                  ← runner.py, schema.py, db.py, migrations.py (ADR-003) + cv_generator.py, cover_letter_generator.py, pdf_export.py
    ├── review/                   ← approval gate CLI
    └── submission/               ← Stage 6 core: schema.py, db.py, session.py,
                                     eligibility.py, pipeline.py, cli.py +
                                     migrations.py (ADR-004, version 1 — the
                                     submissions.outcome CHECK rebuild, Phase B)
```

`.session/` (gitignored) holds the Playwright `storageState` file once a login is saved — a live authenticated session, treated as a credential.

---

## ⚠️ Hard Rules — Never Violate

1. **No application submitted without the human approval gate.** Stage 6 now exists, and enforces this structurally: `run_submission()` acts only on `approved` or `submission_failed`, and `submission_failed` is reachable only from `approved`. Adapters never write to the database and never transition status, so no adapter can route around the gate. **This extends to every piece of generated text, not just the CV and cover letter** — a screening question's answer is content an employer reads, so `screening_questions.decision` starts `pending`, only `review-questions` moves it, and `submission_prep_ready()` refuses to let a vacancy through while any answer is `pending` or `rejected`.
2. **No code without a plan** for any task touching > 2 files.
3. **One task = one commit** — atomic, traceable, revertable.
4. **Tests must pass** before any commit.
5. **No secrets in code** — not even in comments, debug prints, or `.env.example`.
6. **No schema changes without a migration file** — and **migrations are versioned per module, starting at 1** (ADR-004). Each module's `migrations.py` keeps its own `MIGRATIONS` list and delegates to the one shared runner in `src/shared/migrations.py`, which records every applied migration in a `schema_migrations(module, version, applied_at)` ledger keyed by `(module, version)`. `(profile, 5)` and `(vacancy_search, 5)` are different keys, so there is no shared namespace to collide in. Rules that follow:
   - **A shipped migration is immutable.** Once it may have run anywhere, never edit or renumber it — ship a correction as a new version. The ledger records that a version ran, not what it contained.
   - **A migration's payload is `str | Callable[[sqlite3.Connection], None]`.** Use a callable for anything multi-statement — `Connection.execute()` rejects multi-statement SQL, and `executescript()` implicitly commits, which would break the runner's atomicity. A table rebuild (the only way SQLite can change a CHECK) must be a callable, and owns its own FK handling via `PRAGMA defer_foreign_keys` — `PRAGMA foreign_keys` is a no-op inside a transaction.
   - **A net-new *table* needs no migration at all**: its `CREATE TABLE IF NOT EXISTS` goes in that module's `init_db()`, per `docs/todo.md`'s Resolved Items.
   - **`PRAGMA user_version` is frozen and means nothing.** The live `career.db` keeps its historical 4; the runner never reads or writes it. Do not reintroduce it as a gate.
   - *Superseded:* the old rule required a globally-unique `user_version` ≥ 5 for every migration in any module. That decree was a manual workaround for a shared namespace that did not need to be shared, and it failed silently when forgotten — see ADR-004 for the full reasoning and the Phase 17 regression that forced it.
7. **Offline-first always** — core logic never depends on connectivity.
8. **Default Sonnet-5-medium; escalate to Opus only on evidence.**
9. **Orchestrator routes. Executors build.** Never reverse this.
10. **If acceptance criteria are unclear → STOP and ask** before implementing.
11. **Update docs/todo.md** after every completed task.
12. **Never delete the `_archive_qwen_prototype/` contents** without explicit user confirmation — it's the only copy of some historical records.
13. **Run `/codex-review` on every spec in `docs/specs/` before dispatching an Executor** — advisory cross-family second opinion, appended to the spec, never blocking. Fold the strongest points (buried assumptions, missing acceptance criteria, real failure modes) back into the spec as a dated Amendment section before build starts. Standard procedure for every spec, not optional. The `reviewer` agent still holds sole APPROVE/BLOCK authority — Codex is advisory only.

---

*This CLAUDE.md is a living document. Update it when new ADRs are made, stack/tooling changes, new agents or patterns are added, or hard lessons emerge.*

*v-next change: OpenRouter dropped entirely per ADR-003 — AI Matching now routes to local Ollama (`qwen3:8b`), Document Generation to headless Claude Code, under Tebello's own subscription. See `docs/decisions/ADR-003-inference-provider-split.md`.*

*Last review: 2026-07-19 — Tebello Lelosa · DCOE v3.1*
