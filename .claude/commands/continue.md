---
# /continue — DELIVERY NOTE Session Resume
# Resumes work from where the last session in this project ended.
---

## Step 1 — Orient

Read:
- `docs/todo.md` → current task queue and priorities
- `docs/session-log.md` → last session summary (final entry only)

## Step 2 — Report State

Tell Tebello:
1. **Last completed task** — from `session-log.md`
2. **Next pending task** — from `todo.md`
3. **Spec status** — does a spec exist in `docs/specs/` for the next task,
   if it's a build task?
4. **Blockers** — anything unresolved, pending decisions, or missing
   context (e.g. no automated test suite yet — see `docs/todo.md` §
   Next up)

Format:

```
## Session Resume — DELIVERY NOTE

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

If the next task touches anything Next.js-version-specific, read
`node_modules/next/dist/docs/` first — this project runs Next.js 16.2.6,
newer than any AI assistant's training data, with documented breaking
changes from what training data assumes. See `CLAUDE.md` § Hard Rules.
