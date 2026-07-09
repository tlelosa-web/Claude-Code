# CLAUDE.md — Project Brain

# Architecture: DCOE (Domain → Context → Orchestrate → Execute)

# Version: 3.2 | Owner: Tebello Lelosa | Stack: see PROJECT OVERVIEW

> Loaded at the start of every Claude Code session.
> Single source of truth for how this project operates.
> Keep under 500 lines. Move deep docs to @imports.

-----

## 📁 PROJECT OVERVIEW

```
Project:     [YOUR PROJECT NAME]   e.g. SOPS / Fan Nameplate Generator / AI Agency Engine
Type:        [Web App / CLI / API / Automation / Desktop Offline]
Stack:       [e.g. Flask · SQLite · Jinja2 · Vanilla JS / FastAPI · React · ReportLab]
Deployment:  [e.g. Local Windows desktop / Vercel / Docker]
Runtime:     [e.g. Python 3.11 / Node 20]
Inference:   OpenRouter  →  claude-sonnet-5 (default, medium effort) | claude-opus-4-8 (evidence-based escalation only)
Owner:       Tebello Lelosa
```

See @docs/architecture.md for full system design.
See @docs/api-patterns.md for API and route conventions.
See @README.md for product overview and setup.

-----

## ⚙️ ESSENTIAL COMMANDS

```bash
# Python projects (Flask / FastAPI)
pip install -r requirements.txt --break-system-packages
flask run                      # Dev server (localhost:5000)
python -m pytest               # Run all tests
python -m pytest tests/unit    # Unit tests only
black . && ruff check .        # Format + lint

# Node / React projects (Vite)
npm install
npm run dev                    # Dev server (localhost:5173)
npm run build
npm run typecheck && npm run lint

# SQLite DB tasks (SOPS pattern)
flask db upgrade               # Run pending migrations
flask db seed                  # Seed dev/test data
sqlite3 sops.db ".tables"      # Quick schema check

# Before every commit:
# Python →  black . && ruff check . && python -m pytest
# Node   →  npm run typecheck && npm run lint && npm test
```

-----

## 🏗️ DCOE AGENT ARCHITECTURE

This workspace runs on the **DCOE pattern**:
**Domain → Context → Orchestrate → Execute**

An evolution of the DOE pattern that adds an explicit Domain layer.
Each complex task is routed through four stages. Never collapse them.

```
┌──────────────────────────────────────────────────────┐
│                    YOU (Human)                        │
│          Describe goal  →  Review output              │
└───────────────────────┬──────────────────────────────┘
                        │
             ┌──────────▼──────────┐
             │     DOMAIN AGENT    │  (Session start / new feature)
             │  - Clarifies scope  │  Reads CLAUDE.md + docs/todo.md
             │  - Confirms stack   │  Stops if acceptance criteria
             │  - Flags ambiguity  │  are unclear. ASK before acting.
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │   CONTEXT AGENT     │  (Planner / Architect)
             │  - Reads codebase   │  Writes spec to docs/specs/
             │  - Writes todo.md   │  Uses ultrathink for design.
             │  - Defines deps     │  Never implements. Routes only.
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │  ORCHESTRATOR       │  (Coordinates parallel work)
             │  - Reads todo.md    │  Spawns Executors in worktrees.
             │  - Tracks state     │  Context stays < 40%.
             │  - Merges results   │  One commit per task. Always.
             └──────────┬──────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │EXECUTOR 1│  │EXECUTOR 2│  │EXECUTOR N│
    │worktree-1│  │worktree-2│  │worktree-n│
    │Fresh ctx │  │Fresh ctx │  │Fresh ctx │
    │One task  │  │One task  │  │One task  │
    │One commit│  │One commit│  │One commit│
    └──────────┘  └──────────┘  └──────────┘
```

### DCOE Rules

1. **Domain Agent** confirms scope, stack, and ambiguities before anything else.
1. **Context Agent** writes the plan — never the code. Spec lives in `docs/specs/`.
1. **Orchestrator** reads `docs/todo.md`, parallelises via git worktrees, merges.
1. **Executors** each get a fresh context. One task. One atomic commit. Done.
1. If acceptance criteria are unclear at any stage → **STOP and ask**.
1. Orchestrator never does heavy lifting. Executors never plan.

-----

## 🤖 SUB-AGENT ROSTER

**Default location: `~/.claude/agents/` (user-level).** The full roster below
is deployed once at the user level and is available automatically in every
project — SOPS, ai-outreach-agency, CrateTracker, Fan Nameplate Generator,
and any future project. No per-project copying required.

Project-level `.claude/agents/` is reserved for **overrides only** — e.g. a
`data-agent` variant tuned to a specific project's export format. A
same-named file in a project's own `.claude/agents/` wins over the
user-level default for that project. Run `/agents` at session start to
confirm the active roster, and `/doctor` if a name conflict is suspected.

|Agent       |Default file                  |When to Use                            |
|------------|-------------------------------|----------------------------------------|
|`domain`    |`~/.claude/agents/domain.md`    |Session start, scope confirmation      |
|`planner`   |`~/.claude/agents/planner.md`   |Break features into spec + tasks       |
|`architect` |`~/.claude/agents/architect.md` |System design, ADRs, DB schema         |
|`executor`  |`~/.claude/agents/executor.md`  |Implement a single well-defined task   |
|`tester`    |`~/.claude/agents/tester.md`    |Write tests, TDD loops                 |
|`reviewer`  |`~/.claude/agents/reviewer.md`  |Code review, security, quality gate    |
|`doc-writer`|`~/.claude/agents/doc-writer.md`|Update docs, README, changelogs        |
|`debugger`  |`~/.claude/agents/debugger.md`  |Systematic bug investigation           |
|`data-agent`|`~/.claude/agents/data-agent.md`|Excel/CSV transforms, report processing|

### Model routing (via OpenRouter)

`claude-sonnet-5` at **medium effort** is the universal default for all agents.
`claude-opus-4-8` is reserved for **evidence-based escalation only** — not assigned up front by task type.

**Escalate to Opus when:**
- Two prior Sonnet attempts on the same task have failed
- The task requires deep architectural reasoning (system-wide redesign, non-trivial ADRs)
- A security review is warranted (auth, data-export, file-write code)

**Standing exception:** the `reviewer` agent runs permanently on `claude-opus-4-8` — code review is treated as a fixed high-stakes gate, not a per-task escalation.

|Role                              |Model              |Effort |
|-----------------------------------|-------------------|-------|
|All agents (default)               |`claude-sonnet-5`  |Medium |
|`reviewer` (permanent)             |`claude-opus-4-8`  |High   |
|Escalation (2 failed attempts / deep architecture / security review)|`claude-opus-4-8`|High|
|Search / grep only                 |`claude-haiku-4-5` |Low    |

Set per-agent in frontmatter: `model: claude-haiku-4-5`

**Effort tiers** map onto the Thinking Levels table below — low effort pairs with *(none)*/`think`, medium with `think hard`, high with `think harder`/`ultrathink`.

**Bulk batch jobs** (large multi-file refactors, project-wide sweeps, mass research runs) should be scheduled **before 31 August 2026** — introductory pricing on current models ends after that date.

-----

## 🌳 GIT WORKTREE WORKFLOW

Use worktrees for all parallel Executor tasks.
Never run concurrent agents on the same branch.

```bash
# Spawn isolated worktrees
git worktree add ../worktree-feature-auth -b feature/auth
git worktree add ../worktree-bugfix-bom   -b bugfix/bom-lookup

# After Executor completes and commits:
git worktree remove ../worktree-feature-auth

# Orchestrator cherry-picks or merges:
git cherry-pick <​commit-hash>
```

**Rules:**

- One agent per worktree.
- Each Executor commits its own work atomically before stopping.
- Orchestrator reviews and integrates; never commits unreviewed code.
- Clean up worktrees after merge.
- Executors run in a shared session by default — confirm the executor agent's
  first action `cd`s into its assigned worktree path before it touches files,
  rather than assuming worktree isolation is automatic.

-----

## 📋 WORKFLOW PATTERNS

### Pattern 1 — New Feature

```
1. /plan → Domain confirms scope → Planner writes spec to docs/specs/<​feature>.md
2. Review spec → approve or iterate
3. /build docs/specs/<​feature>.md → Orchestrator spawns Executors in worktrees
4. Each Executor: implement → test → commit → done
5. Reviewer agent audits → merge to main
```

### Pattern 2 — Bug Fix

```
1. Describe bug → Debugger agent investigates
2. Debugger writes root-cause to docs/bugs/<​slug>.md
3. Executor implements fix + regression test → atomic commit
4. Reviewer audits → merge
```

### Pattern 3 — Large Refactor

```
1. Architect produces ADR + migration plan → docs/decisions/
2. Planner writes 10–20 atomic tasks to docs/todo.md
3. Orchestrator runs 3–5 Executors in parallel worktrees
4. Each task: implement → unit test → atomic commit
5. Integration tests run across merged result
```

### Pattern 4 — Data / Report Processing  *(SOPS / Sales Order Agent)*

```
1. Data-agent reads source file (Excel / CSV / SQLite query)
2. Applies transform rules from docs/specs/<​report>.md
3. Outputs to designated path (print template / export file)
4. No UI changes without Executor. No DB writes without schema check first.
```

### Pattern 5 — Research / Unknown Territory

```
1. Explore subagent: parallel read-only investigation
2. Report synthesised to docs/research/<​slug>.md
3. Architect reviews → proceed to Pattern 1 or 3
```

-----

## 📐 ARCHITECTURE DECISIONS

> Keep this section current. It overrides assumptions from training data.

- **Routes**: RESTful. Blueprint-per-module. No logic in route handlers — delegate to service layer.
- **DB access**: SQLite via raw `sqlite3` or SQLAlchemy. No ORM magic without explicit migration.
- **Templates**: Jinja2. Component partials in `templates/partials/`. Print templates separate from UI templates.
- **State**: Server-side sessions (Flask). No client-side state management libraries unless justified.
- **Error handling**: All errors bubble to a centralised handler. Flash messages for user-facing errors.
- **Env vars**: `.env` file via `python-dotenv`. Never hardcode. Never commit `.env`.
- **Offline-first**: All features must work without internet. No CDN dependencies in production templates.

See @docs/decisions/ for full ADR log.

-----

## 🧪 TESTING STANDARDS

Follow **TDD** for all new features:

```
1. Write failing tests first            (RED)
2. Implement minimal passing code       (GREEN)
3. Refactor for clarity and quality     (IMPROVE)
4. Coverage ≥ 80% on all new code
```

- Unit tests: `tests/unit/` — pure functions, no DB
- Integration tests: `tests/integration/` — routes, DB, templates
- Never delete or skip tests to make them pass
- Reviewer agent must approve test suite before merging

-----

## 🪝 HOOKS

Quality gates fire automatically. Do not disable without deliberate decision.

|Hook           |Trigger     |Action                                  |
|---------------|------------|----------------------------------------|
|`pre-commit`   |`git commit`|Run lint + format check. Block if fails.|
|`pre-push`     |`git push`  |Run full test suite. Block if fails.    |
|`post-task`    |Agent stops |Log summary to `docs/session-log.md`    |
|`session-start`|New session |Load `docs/todo.md` into context        |

Hook configs: `.claude/hooks/`

**Philosophy:** Block at commit time, not write time.
Let agents complete their work before the gate fires.
Non-blocking hints during implementation > blocking walls mid-task.

-----

## 🔑 CONTEXT MANAGEMENT

Claude has no memory between sessions.
This file + structured docs = persistent project memory.

**Per-session discipline:**

- Use `/compact` every 2–3 large tasks or when context approaches 50%.
- Use `/clear` between fully unrelated tasks.
- Use `/cost` to monitor token burn.
- Start a **new session** for unrelated work — never chain everything.
- Reference files with `@path/to/file` rather than pasting content.
- Use the `Explore` subagent for read-only codebase searches.

**todo.md anti-drift pattern:**
`docs/todo.md` is rewritten by agents at the end of every task.
This pulls the current plan into the model's recent attention window
and prevents goal drift across long sessions.

**Context budget targets:**

|Session type      |Target        |
|------------------|--------------|
|Main orchestrator |< 40% always  |
|Executor subagents|Fresh per task|
|CLAUDE.md         |< 500 lines   |

-----

## 🔐 SECURITY & PERMISSIONS

- **Default mode**: minimal permissions. Expand per-agent only as needed.
- Secrets in `.env` only. Never in code, comments, or agent context.
- No `DROP TABLE`, `DELETE FROM`, or `rm -rf` without explicit confirmation.
- No production DB writes from dev sessions.
- Reviewer agent runs on all auth, file-write, and data-export code.
- Allow-listed safe commands live in `.claude/settings.json` (see `permissions.allow`). Destructive commands are explicitly denied there (see `permissions.deny`) rather than left to per-prompt approval.

-----

## 📝 CODE STANDARDS

```python
# ✅ Preferred — Python
def get_works_order(order_id: int) -> dict | None:   # explicit return type
    """Fetch a single works order by ID. Returns None if not found."""
    ...

raise AppError("WORKS_ORDER_NOT_FOUND", context={"order_id": order_id})

# ❌ Avoid
def get_data(x):          # vague name, no type hint
    print(x)              # use logger, not print
    # TODO fix this       # convert to docs/todo.md task
```

- Functions: < 50 lines. Extract if larger.
- Files: < 300 lines. Split by responsibility.
- Naming: `snake_case` for Python, `camelCase` for JS. Descriptive > clever.
- Comments: explain **why**, not **what**.
- No `any` in TypeScript. No bare `except:` in Python.

See @docs/code-conventions.md for full style guide.

-----

## 📂 DIRECTORY STRUCTURE

```
project-root/
├── CLAUDE.md                    ← You are here (project brain)
├── docs/
│   ├── todo.md                  ← Live task queue (agents update this)
│   ├── architecture.md          ← System overview
│   ├── api-patterns.md          ← Route and API conventions
│   ├── code-conventions.md      ← Style guide
│   ├── session-log.md           ← Agent session summaries
│   ├── decisions/               ← ADR log (ADR-001-*.md)
│   ├── bugs/                    ← Bug root-cause reports
│   ├── research/                ← Investigation notes
│   └── specs/                   ← Feature specs (pre-build)
├── .claude/
│   ├── agents/                  ← PROJECT-LEVEL OVERRIDES ONLY.
│   │                                Default 9-agent roster lives in
│   │                                ~/.claude/agents/ (user-level) and
│   │                                applies to this project automatically.
│   │                                Only add a file here to override a
│   │                                specific agent for this project.
│   ├── hooks/                   ← Lifecycle hooks
│   ├── commands/                ← Custom slash commands
│   ├── settings.json            ← Allow/deny permission rules
│   └── worktrees/               ← Parallel execution sandboxes
├── src/ (or app/)               ← Application source
│   ├── routes/                  ← Blueprint route files
│   ├── services/                ← Business logic layer
│   ├── models/                  ← DB models / schema
│   └── templates/               ← Jinja2 templates
│       └── partials/
├── tests/
│   ├── unit/
│   └── integration/
└── [project-specific files]

~/.claude/agents/                ← USER-LEVEL DEFAULT ROSTER (all projects)
├── domain.md
├── planner.md
├── architect.md
├── executor.md
├── tester.md
├── reviewer.md
├── doc-writer.md
├── debugger.md
└── data-agent.md
```

-----

## 🧠 SESSION START CHECKLIST

At the start of every session, Claude must:

1. Read `docs/todo.md` → understand current task queue and last known state.
1. Run `git status` → know current branch and uncommitted changes.
1. Read the relevant spec in `docs/specs/` if a feature is in progress.
1. Confirm operating mode: **Plan Mode** (think before touching files) or **Edit Mode**.
1. For any task touching > 2 files → **plan first, code second**.
1. If the goal is ambiguous → **ask before proceeding**.

-----

## ⚠️ HARD RULES — NEVER VIOLATE

1. **No code without a plan** for any task touching > 2 files.
1. **One task = one commit** — atomic, traceable, revertable. No bundling.
1. **Tests must pass** before any commit. Hooks enforce this.
1. **No secrets in code** — not even in comments or debug prints.
1. **Ask before deleting** anything in production data paths.
1. **Update docs/todo.md** after every completed task.
1. **Sub-agents are specialists** — never make one agent do everything.
1. **Orchestrator routes. Executors build.** Never reverse this.
1. **Use /compact before context hits 60%** — don't let it auto-compact mid-task.
1. **If acceptance criteria are unclear → STOP and ask** before implementing.
1. **Offline-first always** — no feature may depend on internet connectivity.
1. **No schema changes without a migration file.** Ever.
1. **Opus is earned, not assigned** — default to Sonnet 5 at medium effort; escalate only on evidence (failed attempts, architecture, security).
1. **Agent roster lives at user level** (`~/.claude/agents/`) — do not fork a full copy into a project's `.claude/agents/`; add project files there only as single-agent overrides.

-----

## 📎 QUICK REFERENCE: THINKING LEVELS

|Prompt Modifier|Use When                                       |Effort Tier|
|---------------|-----------------------------------------------|-----------|
|*(none)*       |Trivial edits, quick lookups                   |Low        |
|`think`        |Standard feature work, single-module changes   |Low–Medium |
|`think hard`   |Cross-module work, route/model changes         |Medium     |
|`think harder` |Complex debugging, multi-system interactions   |High       |
|`ultrathink`   |Architecture decisions, major planning sessions|High       |

-----

*This CLAUDE.md is a living document. Update it when:*

- *New architectural decisions are made (add ADR first, then update here)*
- *Stack or tooling changes*
- *New agents or workflow patterns are added*
- *Hard lessons emerge from real sessions*

*v3.2 change: sub-agent roster deployment moved from project-level
`.claude/agents/` to user-level `~/.claude/agents/`, shared across all
projects. Project-level now reserved for per-project overrides only.*

*Last review: July 2026 — Tebello Lelosa*
