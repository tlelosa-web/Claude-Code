# CLAUDE.md — TebelloReborn DCOE v3.0

## Project

```
Name:       TebelloReborn (Master Vault)
Type:       Personal operating system + multi-project incubator
Owner:      Tebello Lelosa
Location:   South Africa
Role:       Operations Foreman / Strategic Operations Builder
```

## Stack

| Sub-project | Stack |
|---|---|
| MIMS App | Next.js, Supabase, Tailwind, TypeScript |
| IQ | Python (signal generator, risk management) |
| TebelloReborn | Python (CV generation, email automation), Markdown docs |
| Tenders | Python (scraping, automation) |
| Vault docs | Markdown |

## DCOE Workflow

Every task follows: **Domain -> Context -> Orchestrate -> Execute**

1. Read `AGENTS.md` — the canonical project brain.
2. Read `docs/domain-brief.md` — active domain classification.
3. Read `docs/todo.md` — live task queue.
4. Classify the task into a life domain (see `docs/life-domains.md`).
5. Route to the correct executor agent.

## Key Files

| Purpose | File |
|---|---|
| Project brain | `AGENTS.md` |
| Task queue | `docs/todo.md` |
| Domain brief | `docs/domain-brief.md` |
| Architecture | `docs/architecture.md` |
| Code conventions | `docs/code-conventions.md` |
| API patterns | `docs/api-patterns.md` |
| Session log | `docs/session-log.md` |
| Life domains | `docs/life-domains.md` |
| Strengths | `docs/strengths-inventory.md` |

## Agent Roster

DCOE agents live in `.claude/agents/`. Domain-specific executors live in `.Codex/agents/`.

| Agent | Role | Model |
|---|---|---|
| domain | Classify tasks into life domains | claude-sonnet-4-6 |
| planner | Decompose tasks into atomic steps | claude-sonnet-4-6 |
| architect | Design structure and data models | claude-sonnet-4-6 |
| executor | Implement bounded tasks | claude-sonnet-4-6 |
| tester | Validate output and run tests | claude-sonnet-4-6 |
| reviewer | Review for quality and security | claude-sonnet-4-6 |
| doc-writer | Create and maintain documentation | claude-sonnet-4-6 |
| debugger | Diagnose and fix bugs | claude-sonnet-4-6 |
| data-agent | Data extraction and transformation | claude-haiku-4-5 |

## Conventions

- No large multi-file work without a plan.
- One task = one clear output.
- Preserve source data and personal records.
- Never hardcode secrets.
- Update `docs/todo.md` after completed work.
- Update `docs/session-log.md` when durable context changes.

## Validation Commands

| Sub-project | Command |
|---|---|
| MIMS App | `cd "MIMS App" && npm run lint && npx tsc --noEmit` |
| IQ | `cd IQ && python -m py_compile 4_Scripts/signal_generator.py` |
| TebelloReborn | `cd TebelloReborn && python -m py_compile 4_Scripts/auto_send_emails.py` |

## Directory Structure

```
.claude/agents/     — DCOE v3 agent definitions
.claude/hooks/      — automation hooks
.claude/commands/   — custom slash commands
.Codex/agents/      — domain-specific executor agents
docs/               — architecture, conventions, decisions, specs, bugs, research
tests/unit/         — unit tests
tests/integration/  — integration tests
```
