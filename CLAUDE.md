# CLAUDE.md — Project Brain

# Architecture: DCOE (Domain → Context → Orchestrate → Execute)

# Version: 3.2 | Owner: Tebello Lelosa | Stack: multi-project (see PROJECT OVERVIEW)

> Loaded at the start of every Claude Code session.
> Single source of truth for how this vault operates.
> Keep under 500 lines. Move deep docs to @imports.

> **Shared core:** at the start of every session, also read
> `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
> and treat its DCOE architecture, sub-agent roster, model routing, and
> universal hard rules as part of this file's operating instructions. This
> file adds Pappa T's own stack, folder layout, and project-specific rules on
> top — it never relaxes anything CORE.md sets as universal.

-----

## 📁 PROJECT OVERVIEW

```
Project:     Pappa T
Type:        Personal operating system + multi-project incubator
Owner:       Tebello Lelosa
Location:    South Africa
Role:        Operations Foreman / Strategic Operations Builder
Inference:   claude-sonnet-5 (default, medium effort) | claude-opus-4-8 (evidence-based escalation only)
```

> Folder on disk is `Pappa T` (`C:\Users\tlelo\Desktop\Pappa T`) — this is the
> project's actual name, not just a path. "TebelloReborn" refers only to the
> `TebelloReborn/` sub-project (CV generation, career automation) below.

| Sub-project | Stack |
|---|---|
| MIMS App | Next.js, Supabase, Tailwind, TypeScript |
| IQ | Python (signal generator, risk management) |
| TebelloReborn | Python (CV generation, email automation), Markdown docs |
| Tenders | Python (scraping, automation) |
| ai-outreach-agency | Python (lead import, research, email drafting, approval dashboard) — self-governing, own `CLAUDE.md` |
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

The full diagram and stage-by-stage DCOE Rules are defined once in the
shared `CORE.md` (read at session start — see the note at the top of this
file) and are not duplicated here. This section covers only what's specific
to Pappa T's use of the pattern.

-----

## 🤖 SUB-AGENT ROSTER

The full 9-role default roster, its deployment mechanism, and model routing
are defined once in the shared `CORE.md` (see the read-instruction at the
top of this file) — not repeated here. Run `/agents` at session start to
confirm the active roster.

> Note on the actual on-disk path: both `CORE.md` and earlier drafts of this
> file describe the default roster as living at `~/.claude/agents/`. On this
> machine that directory doesn't exist — the files are deployed via the
> `dcoe-roster` plugin at
> `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/agents/`
> instead. This is a doc-vs-reality drift in the shared core (out of scope to
> fix from this project, since `CORE.md` lives in a separate repo) — noted
> here so it isn't mistaken for a Pappa T-specific setup issue.

Project-level `.claude/agents/` at **this hub root** is reserved for
**overrides only** — a same-named file here wins over the default roster for
work done at the vault root. This does not extend to sub-projects with their
own `CLAUDE.md`/`AGENTS.md` (see Hub-and-spoke framing under Architecture
Decisions): those projects set their own agent-folder convention.

> **`TebelloReborn/.claude/agents/` carries a full 9-agent roster — verified
> 2026-07-18 as a deliberate, fully-tailored override, not a stale fork.**
> All 9 files are substantively rewritten around the Career Engine's own
> pipeline stages (Profile Import → Vacancy Fetch → AI Matching → Document
> Generation → Human Review) and its specific hard rules (the human-approval
> gate). TebelloReborn's own `CLAUDE.md` explicitly names `.claude/agents/`
> canonical for that project. Per hub-and-spoke precedence, that stands —
> this is not a violation and shouldn't be "cleaned up."

**`.Codex/agents/` is a separate layer**, specific to this vault: life-domain
executors (career-brand, finance-risk, identity-strengths, learning-capability,
operations-systems, strategy-governance, tender-opportunities, venture-builder,
wellbeing-rhythm) plus their own domain/context/planner/architect/executor/
tester/reviewer/doc-writer/debugger set. Use the generic DCOE roster above for
code and doc work; use `.Codex/agents/` when a task should be classified and
routed by life domain first (see `docs/life-domains.md`).

Model routing (Sonnet-5-medium default, Opus escalation triggers, the
permanent-Opus exception for `reviewer`) is defined in `CORE.md` — not
repeated here. **Effort tiers** map onto the Thinking Levels table below —
low effort pairs with *(none)*/`think`, medium with `think hard`, high with
`think harder`/`ultrathink`.

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
- **ai-outreach-agency**: self-governing sub-project with its own `CLAUDE.md`, agents, and hooks. It is physically colocated in this vault but intentionally outside vault-wide DCOE orchestration — read its own `CLAUDE.md` before touching it rather than assuming this file's rules apply directly.
- **Hub-and-spoke framing.** This file governs cross-project decisions and new work started at the vault root. Any sub-project with its own `CLAUDE.md`/`AGENTS.md` (currently: `TebelloReborn/`, `ai-outreach-agency/`) takes precedence over this hub root for work done inside that project's own folder. A sub-project without its own brain file still falls under this hub root's Hard Rules, but stack-specific conventions must be confirmed rather than assumed.
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

> **Status: scaffolded, not wired up.** `.claude/hooks/` and `.Codex/hooks/`
> currently contain only `.gitkeep` placeholders — none of the hooks below
> actually fire yet. The table describes the *target* behavior once
> implemented. Don't assume lint/test gates are enforced automatically until
> this is corrected.

Quality gates should fire automatically once implemented. Do not disable without deliberate decision.

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
├── ai-outreach-agency/            ← Self-governing sub-project (own CLAUDE.md,
│                                     agents, hooks); /continue command lives here
├── tests/
│   ├── unit/
│   └── integration/
└── 00_Index_&_Logs/ … 05_Archive/  ← Vault-level strategy, finance, brand docs

~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/agents/
│                                 ← DEFAULT ROSTER (all projects, via the
│                                    dcoe-roster plugin — see Sub-Agent
│                                    Roster note above re: actual path)
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

> Tip: `/continue` (`.claude/commands/continue.md`) automates this checklist —
> it resumes from `docs/todo.md`/`docs/session-log.md`, identifies whether the
> next task is hub-level or belongs to a specific project folder, and reports
> back before any work begins. Run it manually at the start of a session if
> it wasn't invoked automatically.

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
1. **Agent roster lives at user level** — do not fork a full copy into *this hub root's* `.claude/agents/`; add files there only as single-agent overrides. (Sub-projects with their own `CLAUDE.md`/`AGENTS.md` set their own convention — see Sub-Agent Roster section.)

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
