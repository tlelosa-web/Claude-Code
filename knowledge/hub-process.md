# hub-process

Findings about how this hub's own rules behave in practice — hub-and-spoke,
the contention files, queue discipline. The rules themselves live in
`CLAUDE.md`; this file records what using them has actually taught.

## 2026-08-07 — "The project file wins" is about ownership, not correctness
**Source:** session (this machine), hub `6e3702f` + Pappa T vault `93f8e5b`
**Status:** active

Hub-and-spoke says a project's own `docs/todo.md` is authoritative and the hub
entry is an at-a-glance pointer. The unstated assumption is that the
authoritative file is also the *current* one. It isn't always.

Real case: hub item #1 had just been corrected to reflect that the TebelloReborn
adapter build had started. The project-side entry still read "blocked on two
answers from Tebello." Following "reconcile with the project file" literally —
making the hub match the project — would have reverted the correct entry to the
stale one.

**Resolution that works:** bring the *authoritative* file up to date first, then
trim the hub entry to a pointer at it. Authority over the detail stays where
hub-and-spoke puts it; only the content moves. Reconciliation direction is a
question about which copy is *correct*; the hub-and-spoke rule answers a
different question — which copy is *owned* by whom.

**Corollary worth keeping:** when a hub entry exists to enforce a gate (an
unacknowledged risk, a required sign-off), state that gate in full in **both**
files rather than delegating it to the pointer. Everything else compresses to a
link; a gate should not, because a pointer is easy not to follow.

## 2026-08-07 — Contention-file discipline needs a re-check immediately before writing
**Source:** session (this machine)
**Status:** active

Hard Rule 6 / `/continue` Step 1.75 say to `git fetch` + check
`rev-list HEAD..origin/main` at session start. That is not sufficient when
another session is live in the same repo at the same time — the gap between
orienting and committing can be an hour of conversation.

**Do the check again in the same command as the commit**, and abort rather than
commit if the count moved:

```
git -C <repo> fetch origin main --quiet
$b = git -C <repo> rev-list HEAD..origin/main --count
if ($b -ne "0") { "ABORT: $b behind" } else { git -C <repo> commit -F <msg>; git -C <repo> push origin main }
```

Also note which failure mode you are exposed to when writing into a repo another
agent session is working in: an `Edit` against text that session has changed
fails loudly (good), but a full-file `Write` from that session silently discards
your commit's content on its next write. Prefer surgical edits, commit
immediately to shrink the window, and say in the report that the risk was taken
knowingly rather than pretending it wasn't there.
