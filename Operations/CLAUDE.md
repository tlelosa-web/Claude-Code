# CLAUDE.md — Operations Hub Brain

# Architecture: DCOE (Domain → Context → Orchestrate → Execute)

# Version: 1.0 (root hub) | Based on: SOPS CLAUDE.md v3.2 | Owner: Tebello Lelosa

> Loaded at the start of every Claude Code session opened at the Operations root.
> This is the **hub** brain — it governs cross-project work and work done directly
> at root. It does not override a sub-project's own CLAUDE.md/AGENTS.md.
> Keep under 500 lines. Move deep docs to @imports.

**At the start of every session, read
`~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
and treat its contents as part of this hub's operating instructions** — it
carries the shared DCOE architecture, sub-agent roster, model routing, and
universal hard rules (ADR-007). `@import` can't reach that path (verified
2026-07-18), so this is a plain read instruction, not an automatic import —
follow it explicitly each session. Everything below is hub-specific content
that stays local to this file.

-----

## 📁 WHAT THIS FOLDER IS

`Operations` is the umbrella working folder for Fan Movement (Pty) Ltd's internal
tools and projects. It is **not** a single application and is **not** a git
repository itself — each project below owns its own git history.

```
Owner:      Tebello Lelosa
Company:    Fan Movement (Pty) Ltd
Inference:  claude-sonnet-5 (default, medium effort) | claude-opus-4-8 (evidence-based escalation only)
```

-----

## 🧭 HUB-AND-SPOKE RULE

This is the core operating model, chosen deliberately over a single unified brain:

1. **Sub-projects with their own `CLAUDE.md`/`AGENTS.md` govern themselves.**
   When work happens inside `2. SOPS/` or `7. DELIVERY NOTE/delivery-note-system/`,
   that project's own brain is authoritative — read it, not this file, for
   stack rules, code standards, and hard constraints specific to that app.
2. **This root brain governs:** cross-project decisions, new work started
   directly at root, onboarding a new project onto DCOE, and the shared
   pattern library below.
3. **Patterns flow upward, not down.** A workflow proven in one project (SOPS
   is currently the only DCOE-mature project) gets promoted into
   `docs/patterns.md` here once it's reusable, then adopted by other
   projects deliberately — never force-pushed onto them.
4. **No project is migrated to DCOE without a deliberate decision.** See the
   rollout table below. Bringing a new project in is itself a DCOE task
   (Domain confirms scope of the migration first).

See @docs/patterns.md for the cross-project pattern library — this is where
the hub brain "learns" from what each project's work proves out.

-----

## 🏗️ DCOE AGENT ARCHITECTURE & SUB-AGENT ROSTER

Now sourced from `CORE.md` (see the read instruction above) rather than
duplicated here — the 4-stage DCOE diagram, the DCOE Rules, the 9-agent
roster table, and model routing/escalation policy all live there (ADR-007).
Project-specific additions only:

- Root-level specs live in this hub's own `docs/specs/`; sub-project specs
  live in that project's own `docs/specs/`.
- Executors commit inside the relevant project's own repo — root has none.

-----

## 📂 PROJECT INDEX

|Folder                                  |What it is                                  |DCOE status                              |
|-----------------------------------------|---------------------------------------------|------------------------------------------|
|`2. SOPS/`                                |Flask sales-order/works-order system, live prod|✅ Mature — own CLAUDE.md v3.2, full docs/, tests|
|`7. DELIVERY NOTE/delivery-note-system/`  |Next.js delivery note app                     |✅ Full DCOE — own `CLAUDE.md` + `docs/` per ADR-001 (project-local)|
|`1. Daily Sales Order Files/`             |Python pipeline, Sage → sales order report    |✅ Lightweight DCOE — own `CLAUDE.md` per ADR-003|
|`8. AvgMovement/`                         |Python pipeline, inventory movement reporting |🔴 **Retired** 2026-07-17 — superseded by SOPS Batches 32/33 (ADR-006). Folder left in place untouched, not an active runbook|
|`Inventory Management & Reports/`         |Python pipeline, extract → build → report     |Reference resource for SOPS/other projects — deliberately excluded from DCOE rollout (ADR-004)|
|`3. Nameplate & Test Sheet/`              |Full-stack nameplate/test-sheet generator     |✅ Full DCOE — own `CLAUDE.md` + `docs/` per ADR-001 (project-local), ADR-007 opted in 2026-07-21|
|`4. Casing Analysis/`, `Sage Inventory Report/`, `Stock Report Reference/`, `Workshop Stock - */`, `FM Planning & Stock Control/`|Data folders (xlsx masters, ERP exports) |No code, not applicable|
|`0. Agents/`                              |DCOE template/prompt library (reference only) |Source material — not a working project|

**Rollout decision (2026-07-15):** none of the above are being migrated to
DCOE yet. Root hub only, for now. Revisit per-project when there's a
concrete task in that folder worth planning properly.

-----

## 📂 DIRECTORY STRUCTURE (root)

```
Operations/
├── CLAUDE.md                    ← You are here (hub brain)
├── README.md                    ← Orientation for a human landing here cold
├── docs/
│   ├── todo.md                  ← Hub-level task queue
│   ├── patterns.md              ← Cross-project pattern library (the "learning" mechanism)
│   ├── session-log.md           ← Hub session summaries
│   ├── decisions/                ← ADR log (ADR-001-*.md)
│   ├── bugs/                     ← Cross-cutting bug notes (rare — most bugs live in-project)
│   ├── research/                 ← Investigation notes
│   └── specs/                    ← Hub-level feature/setup specs
├── .claude/
│   ├── commands/continue.md      ← /continue — hub session resume
│   └── settings.json             ← Allow/deny permission rules
└── [project folders — each owns its own structure/git repo]
```

Root is **intentionally not a git repository**. See hard rule 2.

**Real location — machine migration (2026-08-03):** the whole `Operations`
tree moved again, this time off the old Fan Movement work PC entirely, onto
the **same physical machine as the Pappa T vault**. It now lives at
`C:\Users\tlelo\Desktop\Operations` — a plain local folder, sibling to
`Desktop\Pappa T` and `Desktop\Claude-Code` under the same Windows user
profile (`tlelo`). Confirmed post-migration: not a reparse point/junction
(`fsutil reparsepoint query` errors "not a reparse point"), not a git repo,
and `Desktop` itself is not OneDrive-redirected on this machine (OneDrive's
own folder is the separate `C:\Users\tlelo\OneDrive`) — so this supersedes
the 2026-07-15 `C:\Dev\Operations` + OneDrive-junction setup below, which no
longer exists on this machine. Each project's own git repo (`2. SOPS`
confirmed clean, tracking `origin/master`) survived the move intact.
**Not yet done:** Pappa T's own `CLAUDE.md` doesn't yet note that it now
shares a machine with this hub — worth a matching update from a session
running there.

-----

## ⚠️ KNOWN RISK — OneDrive + git (RESOLVED 2026-07-15, moot as of 2026-08-03)

Multiple project repos (`2. SOPS`, `3. Nameplate & Test Sheet`,
`7. DELIVERY NOTE/delivery-note-system`) once lived inside an OneDrive-synced
`Desktop\Operations` folder on the old Fan Movement work PC. `2. SOPS` showed
stale lock artifacts (`.git/HEAD.lock.bak.*`, `index.lock.bak.*`) from
OneDrive syncing `.git` internals mid-operation.

**Status:** resolved on that machine 2026-07-15 by relocating to
`C:\Dev\Operations` with a compatibility junction at the old OneDrive path.
That entire machine/setup is now retired — the 2026-08-03 migration moved
the tree to a new machine that has no OneDrive-Desktop redirection at all,
so the underlying risk class doesn't apply here. Kept for history; the
"periodically re-check the OneDrive junction" backlog item is now closed as
moot (see `docs/todo.md`).

-----

## 🔑 CONTEXT MANAGEMENT

Same discipline as every DCOE project:

- **Context budget threshold (ADR-005):** self-monitor remaining context
  each session. At ~45% consumed (55% remaining), stop starting new
  implementation work — write current state to `docs/session-log.md` and
  `docs/todo.md`, then prompt Tebello to `/compact` or start a fresh
  session. This is a self-monitored policy (no harness hook can read live
  context percentage), so it only holds if this file is actually read and
  followed each session — same trust model as every other rule here.
- Use `/compact` every 2–3 large tasks, or immediately once the 55%
  threshold above is hit.
- Use `/clear` between fully unrelated tasks (e.g. switching from SOPS work
  to Daily Sales Order work).
- Reference files with `@path/to/file` rather than pasting content.
- Use the `Explore` subagent for read-only, multi-file investigation.
- `docs/todo.md` is rewritten at the end of every hub-level task.

-----

## 🧠 SESSION START CHECKLIST

1. Read `docs/todo.md` → current hub task queue and last known state.
2. Identify which project folder(s) this session's work touches.
3. If a target folder has its own `CLAUDE.md`/`AGENTS.md` → read and defer
   to it for anything inside that folder.
4. If the goal is ambiguous or spans multiple projects → **ask before
   proceeding**.
5. For any task touching > 2 files → plan first (spec in `docs/specs/`),
   code second.

-----

## ⚠️ HARD RULES — NEVER VIOLATE

1. **This root brain never overrides a sub-project's own CLAUDE.md/AGENTS.md**
   for work done inside that project's folder.
2. **No git repo at root** — the original reason (OneDrive/git risk) is
   resolved as of 2026-07-15, but initializing a root repo is still a
   deliberate decision to make on its own merits, not a side effect of
   the OneDrive fix. Ask/decide explicitly first.
3. **No code without a plan** for any task touching > 2 files.
4. **Ask before deleting or moving** anything under a project's data/production
   paths (`instance/`, `data/`, `uploads/`, any `*.db`, live report xlsx files).
5. **Update `docs/todo.md`** after every completed hub-level task.
6. **A project only gets onboarded to DCOE via a deliberate decision**,
   recorded in `docs/decisions/`, not as a side effect of unrelated work.
7. **Opus is earned, not assigned** — default to Sonnet 5 at medium effort;
   escalate only on evidence (failed attempts, architecture, security).
8. **If acceptance criteria are unclear → STOP and ask** before implementing.

-----

*This CLAUDE.md is a living document, generalized from `2. SOPS/CLAUDE.md`
v3.2. Update it when a new pattern is promoted to `docs/patterns.md`, a
project is onboarded to DCOE, or a hub-level architectural decision is made
(ADR first, then reflect it here).*

*2026-07-18 change: DCOE architecture + sub-agent roster + model routing now
sourced from the shared `CORE.md` (ADR-007) instead of duplicated in this
file — see the read instruction near the top.*

*2026-08-03 change: whole tree migrated to a new machine, now sharing a
physical machine with the Pappa T vault — see § Directory Structure.*

*Last review: 2026-08-03 — Tebello Lelosa*
