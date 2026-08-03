---
description: Resume work by rehydrating project state from docs
---

Resume the current session using the DCOE session-start discipline. Do this in order:

1. Read `docs/todo.md` — current task queue and last known state.
2. Read the latest entries in `docs/session-log.md` — recover durable context.
3. Run `git status` and `git log --oneline -5` — branch, uncommitted changes, recent commits.
4. If a feature is mid-flight, read its spec in `docs/specs/`.
5. Summarise concisely: where we left off, the single next task, and any blockers.
6. Confirm operating mode (Plan vs Edit). For anything touching > 2 files, plan first.

Do not start implementing until I confirm the next step. If acceptance criteria are unclear, STOP and ask.