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
Stack:       Python 3.11+ · SQLite · Claude API via OpenRouter · Apify (job-board scraping) · fpdf2
Deployment:  Local Windows desktop, offline-capable core logic
Inference:   OpenRouter → claude-sonnet-5 @ medium (default) | claude-opus-4.8 (escalation) | claude-haiku-4.5 (scoring)
```

Continuously finds job vacancies matching Tebello's profile, scores them, generates a tailored CV and cover letter per vacancy, and stops for a mandatory human approval gate before anything leaves the system. **No auto-submission in this build** — that's a deferred future phase.

This project supersedes the earlier hand-built prototype that lived in this same folder (Qwen-era scripts, hardcoded recruiter lists, never-run email automation). That prototype is preserved, untouched, in `_archive_qwen_prototype/` for reference — nothing was deleted.

Core docs:

- `docs/todo.md`: live task queue.
- `docs/architecture.md`: pipeline design and data flow.
- `docs/api-patterns.md`: API integration patterns (OpenRouter, Apify) + rate limiting.
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

# Tests
python -m pytest                          # Full suite
python -m pytest tests/unit               # Unit only
python -m pytest tests/integration        # Integration only

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

## 🧠 Inference Routing (OpenRouter) — v3.1

All LLM calls go through OpenRouter, same convention as `ai-outreach-agency`. **`claude-sonnet-5` at medium effort is the universal default.**

| Task class                                    | Model                        | Effort  | Why                                           |
|------------------------------------------------|------------------------------|---------|------------------------------------------------|
| **Default** — all standard work                | `anthropic/claude-sonnet-5`  | medium  | Best quality/cost balance; universal baseline  |
| Vacancy match scoring, quick classification    | `anthropic/claude-haiku-4.5` | low     | Fast and cheap for a simple scoring pass       |
| CV tailoring, cover letter generation          | `anthropic/claude-sonnet-5`  | medium  | Content generation, needs real quality         |
| **Escalation only** (see triggers below)       | `anthropic/claude-opus-4.8`  | high    | Deep reasoning for genuinely hard problems     |
| Reviewer agent (permanent)                     | `anthropic/claude-opus-4.8`  | high    | Quality/security gate stays on Opus, always    |

**Opus escalation is evidence-based** — same triggers as `ai-outreach-agency`: two failed executor attempts, deep architectural reasoning, or a security review (credential handling, any future submission/data-export path). Do not reach for Opus on a hunch.

> ⏳ Same pricing deadline as `ai-outreach-agency`: Sonnet 5 introductory pricing runs through **31 Aug 2026**. `OPENROUTER_API_KEY` is currently out of credits (shared blocker across both projects) — top up before any real batch run.

---

## 🔌 Offline-First Rule

Core pipeline logic (profile import, schema validation, approval gate, local data transforms) must work fully offline. Only these stages require network:

- Vacancy fetch (Apify — Indeed + LinkedIn actors)
- AI matching / scoring (OpenRouter)
- Document generation (OpenRouter)

Design modules so offline stages never import or depend on network-requiring code. An `OFFLINE_MODE` fixture (identical convention to `ai-outreach-agency`) exists across both external clients and must keep the full test suite green without network access.

---

## 🔁 Pipeline Stages (MVP)

```
1. Profile Import   → data/profile_seed.json → SQLite             (one-time / updated as CV evolves)
2. Vacancy Fetch     → Apify (Indeed + LinkedIn) → SQLite          (status: new)
3. AI Matching       → Claude scores profile vs vacancy            (status: scored)
4. Document Gen      → Claude generates tailored CV + cover letter (status: asset_ready)
5. Human Review      → approve / reject / edit                     (status: approved | rejected)
```

`approved` is the current terminal state. Two phases are explicitly **deferred, not built**:

```
6. Auto-Submit    → Playwright form-fill, paused before final submission   (future)
7. Dashboard      → tracking view: applications, match scores, response rate (future)
```

Vacancy status state machine mirrors the lead lifecycle pattern in `ai-outreach-agency` — enforced transitions, no stage may skip ahead.

---

## 🌐 External Client Patterns

Both network clients share the token-bucket rate limiter pattern from `ai-outreach-agency/src/shared/rate_limiter.py` (copied in, not re-invented):

| Client                              | Source                         | Default rate | Env override                  |
|--------------------------------------|---------------------------------|---------------|--------------------------------|
| `shared/openrouter_client.py`        | Copied/adapted from ai-outreach-agency | 60 / min | `OPENROUTER_RATE_LIMIT_PER_MIN` |
| `vacancy_search/apify_client.py`     | Mirrors `research/apify_client.py` pattern | 30 / min | `APIFY_RATE_LIMIT_PER_MIN`      |

- **OpenRouter**: real inference for matching (`matching/scorer.py`) and document generation (`doc_gen/`). Watch for **HTTP 402** (out of credits) — same account/blocker as `ai-outreach-agency`.
- **Apify**: two dedicated job-board actors (Indeed scraper, LinkedIn Jobs scraper) confirmed available on the Apify Store. **PNet and Careers24 have no dedicated actor** — deferred; could later use the generic `website-content-crawler` actor (same one `ai-outreach-agency` already uses) plus LLM-based extraction. `OFFLINE_MODE` fixture returns 2–3 fake vacancies, matching the `apify_client.FIXTURE` convention.

See @docs/api-patterns.md for full detail.

---

## 🔑 Environment & Secrets

`.env` (gitignored) — real values live here only. `.env.example` holds placeholders and must **never** contain a real key.

| Var                                | Purpose                                    |
|-------------------------------------|---------------------------------------------|
| `OPENROUTER_API_KEY`                | OpenRouter inference (shared account with ai-outreach-agency) |
| `APIFY_API_KEY`                     | Apify scraping (shared account — already funded/working)      |
| `DB_PATH`                           | Source-of-truth SQLite (default `career.db`) |
| `OFFLINE_MODE`                      | Force offline stubs for all network stages   |
| `*_RATE_LIMIT_PER_MIN`              | Per-client rate overrides                    |

No Gmail integration in the MVP (no email-sending stage) — may be added if/when a submission or notification phase is built.

---

## 📐 Architecture Decisions

> Keep this section current. It overrides assumptions from training data.

- **ADR-001**: SQLite is the source of truth for profile + vacancy data (mirrors `ai-outreach-agency` ADR-001).
- **ADR-002**: Job-board scraping via Apify (Indeed + LinkedIn actors) for MVP; PNet/Careers24 deferred — no dedicated Apify actor exists for either as of this decision.
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
│   └── legacy_reference/         ← old tracker + recruiter DB, read-only history
├── _archive_qwen_prototype/      ← everything from the old hand-built prototype, preserved
├── docs/
│   ├── todo.md
│   ├── architecture.md
│   ├── api-patterns.md
│   ├── session-log.md
│   └── decisions/                ← ADR-001, ADR-002
├── .claude/
│   ├── agents/                   ← DCOE agent definitions
│   └── commands/
├── tests/
│   ├── unit/
│   └── integration/
└── src/
    ├── main.py                   ← CLI runner
    ├── config.py                 ← Settings via python-dotenv
    ├── shared/                   ← rate_limiter.py, openrouter_client.py
    ├── profile/                  ← CandidateProfile schema + db
    ├── vacancy_search/           ← Vacancy schema + apify_client.py + db
    ├── matching/                 ← prompt_builder.py + scorer.py
    ├── doc_gen/                  ← cv_generator.py, cover_letter_generator.py, pdf_export.py
    └── review/                   ← approval gate CLI
```

---

## ⚠️ Hard Rules — Never Violate

1. **No application submitted without the human approval gate.** This build stops at `approved` — no submission code exists yet, and none should be added without this rule in mind.
2. **No code without a plan** for any task touching > 2 files.
3. **One task = one commit** — atomic, traceable, revertable.
4. **Tests must pass** before any commit.
5. **No secrets in code** — not even in comments, debug prints, or `.env.example`.
6. **No schema changes without a migration file.**
7. **Offline-first always** — core logic never depends on connectivity.
8. **Default Sonnet-5-medium; escalate to Opus only on evidence.**
9. **Orchestrator routes. Executors build.** Never reverse this.
10. **If acceptance criteria are unclear → STOP and ask** before implementing.
11. **Update docs/todo.md** after every completed task.
12. **Never delete the `_archive_qwen_prototype/` contents** without explicit user confirmation — it's the only copy of some historical records.

---

*This CLAUDE.md is a living document. Update it when new ADRs are made, stack/tooling changes, new agents or patterns are added, or hard lessons emerge.*

*Last review: 2026-07-05 — Tebello Lelosa · DCOE v3.1*
