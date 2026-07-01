---
# /continue — DCOE Session Resume
# Resumes work from where the last session ended.
# Domain-aware: loads the right context before any action.

## Step 1 — Orient

Run the following to establish current state:
```
git log --oneline -5
git status
```

Read:
- `docs/todo.md` → current task queue and priorities
- `docs/session-log.md` → last session summary (final entry only)

## Step 2 — Domain Classify

From the next pending task in todo.md, identify the active domain(s):
- 🔴 **Trading** — signals, Pine Script, market analysis, P&L, risk logic
- 🔵 **Engineering** — calculations, shaft sizing, stress analysis, design specs
- 🟢 **Software / AI** — tooling, automation, Flask/SOPS, dashboards, agentic workflows
- 🟡 **Hybrid** — load both relevant domain contexts

## Step 3 — Context Injection

Based on domain(s) identified above, load the appropriate context from CLAUDE.md:

**Trading:** instrument, timeframe, signal constraints, tool order (web_search → file_read → bash → file_write)
**Engineering:** applicable standards (IEC/ISO), material, load case, calculation discipline
**Software/AI:** stack (Flask · SQLite · Jinja2 for SOPS), UI standard, integration points, tool order (file_read → bash → web_search → file_write)

## Step 4 — Report State

Tell Tebello:
1. **Last completed task** — from session-log.md
2. **Next pending task** — from todo.md (with domain classification)
3. **Spec status** — does a spec exist in `docs/specs/` for the next task? (required before build)
4. **Git state** — last commit + any uncommitted changes
5. **Blockers** — anything unresolved, pending decisions, or missing context

Format:

```
## Session Resume

**Domain:** [Trading | Engineering | Software/AI | Hybrid]
**Last completed:** [task name + commit ref]
**Next task:** [task name from todo.md]
**Spec:** [exists at docs/specs/<name>.md | MISSING — must write spec before building]
**Git:** [clean | N uncommitted changes on branch <name>]
**Blockers:** [none | description]

Ready to proceed? Confirm and I'll start.
```

## Step 5 — Wait for Confirmation

Do not begin implementation. Do not open files outside of the reads above.
Wait for Tebello to confirm the task or redirect.

## Spec Gate Reminder

If the next task is a build task and no spec exists → surface this immediately.
Spec must be written and confirmed before any executor is dispatched.
---
