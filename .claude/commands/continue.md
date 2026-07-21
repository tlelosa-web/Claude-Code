---
# /continue — Nameplate & Test Sheet Session Resume
# Resumes work from where the last session in this project ended.
---

## Step 1 — Orient

Read:
- `docs/todo.md` → current task queue and priorities
- `docs/session-log.md` → last session summary (final entry only)

## Step 1.5 — Shared Core Update Check (ADR-007)

Check whether the shared `CORE.md` (DCOE architecture, sub-agent roster,
model routing, universal hard rules — see the read instruction near the top
of this project's `CLAUDE.md`) has upstream changes not yet pulled on this
machine:

```
git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config fetch --quiet
git -C ~/.claude/plugins/marketplaces/tlelosa-claude-config rev-list HEAD..origin/main --count
```

If the count is > 0, mention it in the Step 2 resume report: "Shared core
template has N new commit(s) upstream — run `/plugin marketplace update
tlelosa-claude-config` to pull them in." This is a signal only — never run
the update automatically, and don't let it block orienting or reporting.
If the marketplace clone doesn't exist on this machine at all, note that
plainly too rather than silently skipping the check.

## Step 2 — Report State

Tell Tebello:
1. **Last completed task** — from `session-log.md`
2. **Next pending task** — from `todo.md`
3. **Spec status** — does a spec exist in `docs/specs/` for the next task,
   if it's a build task?
4. **Blockers** — anything unresolved, pending decisions, or missing
   context (e.g. no automated test suite yet — see `CLAUDE.md` § Testing
   Standards)

Format:

```
## Session Resume — Nameplate & Test Sheet

**Last completed:** [task name]
**Next task:** [task name from todo.md]
**Spec:** [exists at docs/specs/<name>.md | MISSING — must write spec before building | N/A]
**Blockers:** [none | description]

Ready to proceed? Confirm and I'll start.
```

## Step 3 — Wait for Confirmation

Do not begin implementation. Wait for Tebello to confirm the task or
redirect.

## Spec Gate Reminder

If the next task is a build task touching frontend *and* backend (or the
`test_lines` payload contract), remember `App.jsx` ↔ `main.py`'s
`TestLinePayload` ↔ `pdf_generator.py`'s row renderer must move together —
see `CLAUDE.md` § DCOE Rules.
