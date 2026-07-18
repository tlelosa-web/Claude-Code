# CLAUDE.md — Project Brain

# Architecture: DCOE (Domain → Context → Orchestrate → Execute)

# Version: 3.2 | Owner: Tebello Lelosa | Stack: multi-project (see PROJECT OVERVIEW)

> Loaded at the start of every Claude Code session.
> Single source of truth for how this vault operates.
> Keep under 500 lines. Move deep docs to @imports.

-----

## 📁 PROJECT OVERVIEW

```
Project:     TebelloReborn (Master Vault)
Type:        Personal operating system + multi-project incubator
Owner:       Tebello Lelosa
Location:    South Africa
Role:        Operations Foreman / Strategic Operations Builder
Inference:   claude-sonnet-5 (default, medium effort) | claude-opus-4-8 (evidence-based escalation only)
```

| Sub-project | Stack |
|---|---|
| MIMS App | Next.js, Supabase, Tailwind, TypeScript |
| IQ | Python (signal generator, risk management) |
| TebelloReborn | Python (CV generation, email automation), Markdown docs |
| Tenders | Python (scraping, automation) |
| Vault docs | Markdown |

`AGENTS.md` is the canonical project brain for workflow and life-domain agent behavior —
read it first, alongside this file, at the start of every session.
See @docs/architecture.md for full system design.
See @docs/api-patterns.md for per-project API notes (no shared vault-wide contract).
See @docs/domain-brief.md for the active life-domain classification.

-----

## ⚙️ ESSENTIAL COMMANDS

```bash
# MIMS App (Next.js)
cd "MIMS App" && npm run lint && npx tsc --noEmit

# IQ (Python)
cd IQ && python -m py_compile 4_Scripts/signal_generator.py

# TebelloReborn (Python)
cd TebelloReborn && python -m py_compile 4_Scripts/auto_send_emails.py

# Before every commit, run the validation command for whichever sub-project changed.
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

**Default location: `~/.claude/agents/` (user-level), deployed via the
`dcoe-roster` plugin from [tlelosa-claude-config](https://github.com/tlelosa-web/tlelosa-claude-config).**
The full 9-role roster is installed once at user scope and is available
automatically in every project on this machine. No per-project copying.

Project-level `.claude/agents/` is reserved for **overrides only** — e.g. a
`data-agent` variant tuned to this vault's export format. A same-named file
in this project's own `.claude/agents/` wins over the user-level default.
Run `/agents` at session start to confirm the active roster, and check for
stray project-level files if a name conflict is suspected — none should
exist here unless deliberately added as an override.

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

**`.Codex/agents/` is a separate layer**, specific to this vault: life-domain
executors (career-brand, finance-risk, identity-strengths, learning-capability,
operations-systems, strategy-governance, tender-opportunities, venture-builder,
wellbeing-rhythm) plus their own domain/context/planner/architect/executor/
tester/reviewer/doc-writer/debugger set. Use the generic DCOE roster above for
code and doc work; use `.Codex/agents/` when a task should be classified and
routed by life domain first (see `docs/life-domains.md`).

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
git cherry-pick <commit-hash>
```

**Rules:**

- One agent per worktree.
- Each Executor commits its own work atomically before stopping.
- Orchestrator reviews and integrates; never commits unreviewed code.
- Clean up worktrees after merge.
- Executors run in a shared session by default — confirm the executor agent's
  first action `cd`s into its assigned worktree path before it touches files,
  rather than assuming worktree isolation is automatic.
- `.Codex/worktrees/` is the isolation path for `.Codex/agents/` executors;
  `.claude/worktrees/` (created on demand) is for the generic DCOE roster.

-----

## 📋 WORKFLOW PATTERNS

### Pattern 1 — New Feature

```
1. /plan → Domain confirms scope → Planner writes spec to docs/specs/<feature>.md
2. Review spec → approve or iterate
3. /build docs/specs/<feature>.md → Orchestrator spawns Executors in worktrees
4. Each Executor: implement → test → commit → done
5. Reviewer agent audits → merge to main
```

### Pattern 2 — Bug Fix

```
1. Describe bug → Debugger agent investigates
2. Debugger writes root-cause to docs/bugs/<slug>.md
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

### Pattern 4 — Data / Report Processing *(IQ signal exports, TebelloReborn CV/report generation)*

```
1. Data-agent reads source file (Excel / CSV / SQLite query)
2. Applies transform rules from docs/specs/<report>.md
3. Outputs to designated path (print template / export file)
4. No UI changes without Executor. No DB writes without schema check first.
```

### Pattern 5 — Research / Unknown Territory

```
1. Explore subagent: parallel read-only investigation
2. Report synthesised to docs/research/<slug>.md
3. Architect reviews → proceed to Pattern 1 or 3
```

-----

## 📐 ARCHITECTURE DECISIONS

> Keep this section current. It overrides assumptions from training data.

- **No shared API contract across sub-projects.** Inspect the target sub-project before assuming conventions carry over (see @docs/api-patterns.md).
- **MIMS App**: Next.js/Supabase/Tailwind — follow that stack's own idioms, not vault-wide ones.
- **IQ / TebelloReborn / Tenders**: Python automation scripts — no framework assumed; keep scripts single-responsibility per `4_Scripts/`.
- **Env vars**: `.env` file(s) per sub-project. Never hardcode secrets. Never commit `.env`.
- **Personal data**: this vault holds real CVs, financial strategy, and personal records — preserve source data, never overwrite without explicit confirmation.
- **Vault-level docs** (`00_Index_&_Logs/` … `05_Archive/`): strategy, finance, operations, brand — treated as source-of-record, not scratch space.

See @docs/decisions/ for the full ADR log.

-----

## 🧪 TESTING STANDARDS

Follow **TDD** where a sub-project has executable code (Python/TypeScript):

```
1. Write failing tests first            (RED)
2. Implement minimal passing code       (GREEN)
3. Refactor for clarity and quality     (IMPROVE)
4. Coverage ≥ 80% on all new code
```

- Unit tests: `tests/unit/` — pure functions, no DB
- Integration tests: `tests/integration/` — cross-module, external calls
- Never delete or skip tests to make them pass
- Reviewer agent must approve test suite before merging
- Markdown-only vault docs are exempt — validate by reading, not by test suite

-----

## 🪝 HOOKS

Quality gates fire automatically. Do not disable without deliberate decision.

|Hook           |Trigger     |Action                                  |
|---------------|------------|----------------------------------------|
|`pre-commit`   |`git commit`|Run lint + format check. Block if fails.|
|`pre-push`     |`git push`  |Run full test suite. Block if fails.    |
|`post-task`    |Agent stops |Log summary to `docs/session-log.md`    |
|`session-start`|New session |Load `docs/todo.md` into context        |

Hook configs: `.claude/hooks/` (generic roster), `.Codex/hooks/` (life-domain executors)

**Philosophy:** Block at commit time, not write time.
Let agents complete their work before the gate fires.
Non-blocking hints during implementation > blocking walls mid-task.

-----

## 🔑 CONTEXT MANAGEMENT

Claude has no memory between sessions.
This file + `AGENTS.md` + structured docs = persistent project memory.

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
- Allow-listed safe commands live in `.claude/settings.json` (`permissions.allow`). Destructive commands are explicitly denied there (`permissions.deny`) rather than left to per-prompt approval. Machine-specific allowances go in the gitignored `.claude/settings.local.json` instead.

-----

## 📝 CODE STANDARDS

```python
# ✅ Preferred — Python
def get_lead_status(lead_id: int) -> dict | None:   # explicit return type
    """Fetch a single lead by ID. Returns None if not found."""
    ...

raise AppError("LEAD_NOT_FOUND", context={"lead_id": lead_id})

# ❌ Avoid
def get_data(x):          # vague name, no type hint
    print(x)              # use logger, not print
    # TODO fix this       # convert to docs/todo.md task
```

- Functions: < 50 lines. Extract if larger.
- Files: < 300 lines. Split by responsibility.
- Naming: `snake_case` for Python, `camelCase` for TypeScript. Descriptive > clever.
- Comments: explain **why**, not **what**.
- No `any` in TypeScript. No bare `except:` in Python.

See @docs/code-conventions.md for full style guide.

-----

## 📂 DIRECTORY STRUCTURE

```
project-root/
├── CLAUDE.md                    ← You are here (project brain, workflow)
├── AGENTS.md                    ← Canonical brain for life-domain agent behavior
├── docs/
│   ├── todo.md                  ← Live task queue (agents update this)
│   ├── architecture.md          ← System overview
│   ├── api-patterns.md          ← Per-project API notes
│   ├── code-conventions.md      ← Style guide
│   ├── session-log.md           ← Agent session summaries
│   ├── domain-brief.md          ← Active life-domain classification
│   ├── life-domains.md          ← Life-domain taxonomy
│   ├── decisions/                — ADR log (ADR-001-*.md)
│   ├── bugs/                     — Bug root-cause reports
│   ├── research/                 — Investigation notes
│   └── specs/                    — Feature specs (pre-build)
├── .claude/
│   ├── agents/                  ← PROJECT-LEVEL OVERRIDES ONLY.
│   │                                Default 9-agent roster lives in
│   │                                ~/.claude/agents/ (dcoe-roster plugin)
│   │                                and applies to this project automatically.
│   │                                Only add a file here to override a
│   │                                specific agent for this project.
│   ├── hooks/                   ← Lifecycle hooks
│   ├── commands/                ← Custom slash commands
│   ├── settings.json            ← Shared allow/deny permission rules
│   ├── settings.local.json      ← Machine-specific permissions (gitignored)
│   └── worktrees/               ← Parallel execution sandboxes (created on demand)
├── .Codex/
│   ├── agents/                  ← Life-domain executor roster (this vault only)
│   ├── commands/
│   ├── hooks/
│   └── worktrees/
├── MIMS App/ · IQ/ · TebelloReborn/ · Tenders/  ← Sub-project source trees
├── tests/
│   ├── unit/
│   └── integration/
└── 00_Index_&_Logs/ … 05_Archive/  ← Vault-level strategy, finance, brand docs

~/.claude/agents/                ← USER-LEVEL DEFAULT ROSTER (all projects,
│                                    via the dcoe-roster plugin)
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

1. Read `AGENTS.md` and `docs/todo.md` → understand current task queue and last known state.
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
1. **Ask before deleting** anything in production data paths or personal records.
1. **Update docs/todo.md** after every completed task.
1. **Sub-agents are specialists** — never make one agent do everything.
1. **Orchestrator routes. Executors build.** Never reverse this.
1. **Use /compact before context hits 60%** — don't let it auto-compact mid-task.
1. **If acceptance criteria are unclear → STOP and ask** before implementing.
1. **No schema changes without a migration file.** Ever.
1. **Opus is earned, not assigned** — default to Sonnet 5 at medium effort; escalate only on evidence (failed attempts, architecture, security).
1. **Agent roster lives at user level** (`~/.claude/agents/`) — do not fork a full copy into this project's `.claude/agents/`; add project files there only as single-agent overrides.

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
`.claude/agents/` to user-level `~/.claude/agents/` via the `dcoe-roster`
plugin, shared across all projects. Project-level now reserved for
per-project overrides only. `.Codex/agents/` life-domain layer unchanged.*

*Last review: July 2026 — Tebello Lelosa*
