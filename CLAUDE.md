# CLAUDE.md — Project Brain
# DCOE Agent Architecture — Tebello's Custom Build
# Version: 1.1 | Evolved from DOE (Nick Saraev) + domain-aware extensions + tool manifests

> Loaded at the start of every session.
> Single source of truth for how work gets done.
> Keep under 500 lines. Deep docs go to @imports.

---

## 📁 PROJECT OVERVIEW

```
Owner:       Tebello
Domains:     Trading · Mechanical Engineering · Software / AI Tooling
Mode:        Solo operator — lightweight orchestration, high output quality
Architecture: DCOE — Domain → Context → Orchestrate → Execute
```

---

## 🏗️ DCOE ARCHITECTURE

Standard DOE extended with a **Domain Classification + Context Injection** layer.
Required because tasks span fundamentally different knowledge worlds.
A generic executor without domain context will produce generic, wrong output.

```
┌──────────────────────────────────────────────────┐
│                   YOU (Tebello)                  │
│          describe goal → review output           │
└──────────────────────┬───────────────────────────┘
                       │
           ┌───────────▼───────────┐
           │   DOMAIN CLASSIFIER   │  What world are we in?
           │  - Trading            │  Reads goal, identifies domain(s)
           │  - Engineering        │  Multiple domains = multi-context
           │  - Software / AI      │  Hybrid tasks get both contexts
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │   CONTEXT INJECTOR    │  Load domain knowledge before work
           │  - Standards / rules  │  e.g. IEC norms for engineering,
           │  - Constraints        │  market structure for trading,
           │  - Terminology        │  stack conventions for software
           │  - Tool manifest      │  Which tools this domain uses + order
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │     TOOL ROUTER       │  Point agents to correct tools first
           │  - Tool manifest/task │  Fastest path to right tool
           │  - Tool-first rule    │  No reasoning from memory on
           │  - Fallback chain     │  facts that tools can answer
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │      DISPATCHER       │  Break goal into atomic tasks
           │  - Writes todo.md     │  Spec gate: no build without spec
           │  - Sets priorities    │  Uses ultrathink for planning
           │  - Routes to agents   │  Solo mode: keep overhead minimal
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │     ORCHESTRATOR      │  Coordinate. Never implement.
           │  - Reads todo.md      │  Spawn Executors per task
           │  - Manages deps       │  Context stays < 40%
           │  - Atomic commits     │  Re-plan if task reveals complexity
           └───────────┬───────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │EXECUTOR A│  │EXECUTOR B│  │EXECUTOR N│
   │Domain-   │  │Domain-   │  │Domain-   │
   │aware ctx │  │aware ctx │  │aware ctx │
   │One task  │  │One task  │  │One task  │
   │One commit│  │One commit│  │One commit│
   └──────────┘  └──────────┘  └──────────┘
```

### Core Rules

1. **Domain first** — classify before dispatching. Never skip this step.
2. **Spec gate** — no executor touches implementation without an approved spec.
3. **One task = one commit** — atomic, traceable, revertable.
4. **Orchestrator routes, Executors build** — never reverse this.
5. **Solo mode** — keep orchestration lightweight. No team-coordination overhead.
6. **Production quality on first pass** — not draft → iterate. Get the spec right instead.
7. **If acceptance criteria are unclear → STOP and ask.**

---

## 🌐 DOMAIN CONTEXTS

### 🔴 Trading Domain
```
Active when:  Signal generation, market analysis, risk logic,
              backtest specs, binary options, crash games, P&L calc

Load:
  - Market structure awareness (auction theory, order flow)
  - Instrument context: Binary options, WTI/Brent oil, crash multipliers
  - Risk rules: bankroll management, unit-based staking, drawdown limits
  - Tool context: TradingView Pine Script v5/v6, indicator architecture
  - Output standard: No lookahead bias. No repainting. Signal logic must
    be deterministic and auditable.

Tool priority order:
  1. web_search        → current price data, news, market conditions
  2. file_read         → existing indicators, specs, session logs
  3. bash              → P&L calculations, unit math, scenario tables
  4. file_write        → output Pine Script, save analysis docs
  NEVER: reason from memory about current prices or live market state
```

### 🔵 Engineering Domain
```
Active when:  Mechanical design, shaft sizing, torque calculations,
              stress analysis, component specifications

Load:
  - Standards: IEC, ISO (specify per task)
  - Calculation discipline: show working, units explicit, safety factors stated
  - Design constraints: material properties, failure modes, tolerances
  - Output standard: Calculations reproducible. Assumptions listed.
    Results include verification check.

Tool priority order:
  1. file_read         → existing design files, previous calcs, standards refs
  2. bash              → all numerical calculations (never mental math)
  3. web_search        → standard lookups, material properties, IEC/ISO clauses
  4. file_write        → calculation sheets, design output docs
  NEVER: perform multi-step calculations without bash — rounding errors compound
```

### 🟢 Software / AI Domain
```
Active when:  Tooling, automation, frontends, agentic workflows,
              Claude Code setup, local AI (Agent Zero), scripts

Load:
  - Stack defaults: HTML/CSS/JS for standalone tools, Python for automation
  - UI standard: Functional, cockpit-aesthetic preferred for dashboards
  - Agent context: DOE/DCOE patterns, Claude Code conventions
  - Output standard: Production-ready on delivery. No placeholder code.
    No TODOs in output unless explicitly flagged.

Tool priority order:
  1. file_read         → existing codebase, CLAUDE.md, specs, agent files
  2. bash              → run code, test output, install packages, grep/search
  3. web_search        → library docs, API references, error lookups
  4. file_write        → source files, configs, agent definitions
  NEVER: write code that imports a library without confirming availability via bash
```

---

## 🤖 SPECIALIST EXECUTOR ROSTER

Lives in `.claude/agents/`. Each executor is domain-aware by design.

| Agent | File | Domain | When to Use |
|---|---|---|---|
| `analyst` | `agents/analyst.md` | Trading | Market research, scenario analysis, P&L modeling |
| `quant-builder` | `agents/quant-builder.md` | Trading | Pine Script indicators, signal logic, alert conditions |
| `engineer` | `agents/engineer.md` | Engineering | Calculations, standards compliance, design specs |
| `ui-builder` | `agents/ui-builder.md` | Software | Frontends, dashboards, HTML tools, cockpit UIs |
| `ai-architect` | `agents/ai-architect.md` | Software/AI | Agentic workflows, CLAUDE.md, system design |
| `planner` | `agents/planner.md` | All | Break features into spec + atomic tasks |
| `reviewer` | `agents/reviewer.md` | All | Quality gate before commit — domain-aware review |
| `debugger` | `agents/debugger.md` | All | Systematic root-cause investigation |

**Model routing:**
- Planning, architecture, multi-domain tasks → `opus`
- Standard implementation → `sonnet` (default)
- Search, grep, quick lookups → `haiku`

---

## 🔧 TOOL MANIFEST

**Tool-first rule:** Agents must attempt tool use before reasoning from memory
on any factual, numerical, or file-based question. Memory is for logic, not data.

**Fallback chain (apply in order if primary tool fails):**
```
Primary tool fails → try secondary → if both fail → STOP and report, do not guess
```

### Per-Executor Tool Assignments

| Executor | Primary Tools | Secondary | Never |
|---|---|---|---|
| `analyst` | web_search, file_read | bash | Guess market data from memory |
| `quant-builder` | file_read, file_write | bash, web_search | Repainting logic, lookahead |
| `engineer` | bash, file_read | web_search, file_write | Mental arithmetic on multi-step calcs |
| `ui-builder` | file_read, file_write | bash | Inline styles, placeholder content |
| `ai-architect` | file_read, file_write | bash | Modifying hooks without review |
| `planner` | file_read, file_write | web_search | Building before spec is approved |
| `reviewer` | file_read, bash | web_search | Auto-approving — always flag issues |
| `debugger` | bash, file_read | web_search | Guessing root cause without evidence |

### Tool Behaviour Rules

```
web_search:
  - Always search before stating current prices, news, or live data
  - Include date context in queries for time-sensitive topics
  - Verify library versions before recommending in code

file_read:
  - Read existing files before writing new ones — avoid duplication
  - Read specs before implementing — never work from memory of a spec
  - Read CLAUDE.md at session start — always

bash:
  - All numerical calculations run through bash — no exceptions
  - Verify package/library availability before import
  - Test scripts in bash before writing to output files
  - Use bash to grep codebase before assuming something doesn't exist

file_write:
  - Never overwrite without reading current file first
  - Write to docs/todo.md after every completed task
  - Specs written to docs/specs/ before any build task
```

---

## 📋 WORKFLOW PATTERNS

### Pattern 1: Trading Tool / Indicator

```
1. Classify → Trading domain
2. Inject context: instrument, timeframe, signal logic constraints
3. Spec gate: define inputs, outputs, alert conditions, HUD layout
4. analyst reviews market logic → approves
5. quant-builder implements → no lookahead, no repainting
6. reviewer audits signal integrity → commit
```

### Pattern 2: Engineering Calculation / Design

```
1. Classify → Engineering domain
2. Inject context: applicable standards, material, operating conditions
3. Spec gate: define load case, constraints, acceptance criteria
4. engineer calculates → shows working, lists assumptions
5. reviewer checks units, safety factors, standard compliance → commit
```

### Pattern 3: Software Tool / Automation

```
1. Classify → Software/AI domain
2. Inject context: stack, UI requirements, integration points
3. Spec gate: define inputs, outputs, interaction model
4. ui-builder or ai-architect implements → production-ready
5. reviewer checks quality, no placeholders → commit
```

### Pattern 4: Hybrid Task (e.g. Trading Dashboard)

```
1. Classify → Trading + Software (dual context)
2. Inject both domain contexts
3. Dispatcher separates concerns: logic tasks → quant-builder,
   UI tasks → ui-builder
4. Orchestrator runs in parallel, integrates output
5. reviewer checks both domains before commit
```

### Pattern 5: Research / Unknown Territory

```
1. Explore subagent: read-only parallel investigation
2. Synthesize to docs/research/<slug>.md
3. Domain expert agent reviews → proceed to standard pattern
```

---

## 📐 SPEC GATE (MANDATORY)

**No executor builds without a signed-off spec.**
This is the highest-leverage rule in the architecture.
Tebello's working style: detail-rich upfront. Lean into it.

Spec template lives at: `docs/specs/_template.md`

Minimum spec fields:

```markdown
## Task: [name]
**Domain:** Trading | Engineering | Software | Hybrid
**Goal:** One sentence.
**Inputs:** What goes in
**Outputs:** What comes out (format, location)
**Constraints:** Standards, rules, non-negotiables
**Acceptance Criteria:** How we know it's done
**Out of Scope:** What this task does NOT do
```

---

## 🌳 GIT WORKTREE WORKFLOW

```bash
# Parallel execution — one agent per worktree
claude --worktree trading-indicator
claude --worktree engineering-calc
claude --worktree ui-dashboard

# Each agent commits atomically
# Orchestrator merges after review
```

---

## 📋 CONTEXT MANAGEMENT

**Session discipline:**
- `/compact` every 2–3 large tasks
- `/clear` between unrelated domain tasks (Trading → Engineering = clear)
- `/cost` to monitor token burn
- Fresh session for unrelated work — don't chain everything
- Use `@file-references` over pasting content

**Context budget:**
- Orchestrator session: < 40% at all times
- Executors: fresh context per task
- CLAUDE.md: < 500 lines

**todo.md pattern:**
Keep `docs/todo.md` live. Agents rewrite at end of each task.
Prevents goal drift across long sessions.

---

## 🪝 HOOKS

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit` | `git commit` | Typecheck + lint. Block if fails. |
| `pre-push` | `git push` | Full test suite. Block if fails. |
| `post-task` | Subagent stops | Log to `docs/session-log.md` |
| `session-start` | New session | Load `docs/todo.md` + detect domain |
| `spec-gate` | Dispatcher done | Block executor spawn until spec approved |

---

## 🧠 SESSION START CHECKLIST

1. Read `docs/todo.md` → current task queue
2. Check `git status` → branch + uncommitted changes
3. **Identify domain** → load appropriate context
4. Confirm spec exists for any build task
5. For large tasks: **plan before coding, always**

---

## 📎 THINKING LEVELS

| Modifier | Use When |
|---|---|
| *(none)* | Trivial edits, quick lookups |
| `think` | Standard feature work |
| `think hard` | Domain-specific design decisions |
| `think harder` | Cross-domain / hybrid tasks, complex debugging |
| `ultrathink` | Major planning, new architecture, breaking down large features |

---

## ⚠️ HARD RULES

1. **Domain classify before every task** — no exceptions
2. **Spec gate before every build** — no exceptions
3. **Tool-first before every factual/numerical task** — no reasoning from memory
4. **No code without a plan** for tasks > 2 files
5. **One task = one commit** — atomic, traceable
6. **No secrets in code** — not even comments
7. **No lookahead bias** in any trading output
8. **Show working** in all engineering calculations — bash, not mental math
9. **Read before write** — always read existing files before creating new ones
10. **Production-ready on delivery** — no placeholder output
11. **Ask before deleting** anything in production paths
12. **Update docs/todo.md** after every completed task

---

## 📂 DIRECTORY STRUCTURE

```
project-root/
├── CLAUDE.md                    ← You are here
├── docs/
│   ├── todo.md                  ← Live task queue
│   ├── session-log.md           ← Post-task summaries
│   ├── specs/                   ← Feature specs (pre-build)
│   │   └── _template.md
│   ├── research/                ← Investigation notes
│   ├── bugs/                    ← Root-cause reports
│   └── decisions/               ← ADR log
├── .claude/
│   ├── agents/                  ← Specialist executor definitions
│   │   ├── analyst.md
│   │   ├── quant-builder.md
│   │   ├── engineer.md
│   │   ├── ui-builder.md
│   │   ├── ai-architect.md
│   │   ├── planner.md
│   │   ├── reviewer.md
│   │   └── debugger.md
│   ├── hooks/                   ← Lifecycle hooks
│   ├── commands/                ← Custom slash commands
│   └── worktrees/               ← Parallel execution sandboxes
├── trading/                     ← Trading tools, indicators, scripts
├── engineering/                 ← Calculation files, design docs
├── tools/                       ← Software / AI tooling
└── docs/
```

---

*This CLAUDE.md is a living document. Update when:*
- *New domain or sub-domain identified*
- *New executor type needed*
- *A hard-learned lesson from a session*
- *Stack or tooling changes*

*Version 1.1 — DCOE + Tool Manifests + Tool Router layer*
