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

## 2026-08-07 — "Is the final log entry accurate?" cannot be answered from the entry
**Source:** session (this machine), second `/session-end` run — hub `bb882ec` vs
Pappa T vault `379a4b2`/`b4dd652`
**Status:** active

`/continue` Step 1 reads only the final `docs/session-log.md` entry, and
`/session-end` Step 3 says to verify that entry's `Last completed:` / `Next task:`
block is still accurate before leaving it alone. Both steps quietly assume the
staleness you're checking for is *inside this repo*. It usually isn't.

Real case: the hub's last write at 09:00:55 recorded item #1 as "waits only on
`email`/`phone`." The Pappa T vault implemented exactly that at 09:10:28 and
closed out the whole phase at 11:00:27. Nothing in the hub was wrong when written
and nothing in it looked stale — `git status` was clean, `rev-list
HEAD..origin/main` was 0, and the entry read as a confident, complete close-out.
The work had simply continued in a different repo that pushes on its own schedule.

**Check that actually catches it** — compare commit clocks across both repos
rather than reading either file:

```
git -C <hub> log -4 --format="%h %ad %s" --date=format:"%H:%M:%S"
git -C <live-project> log -6 --format="%h %ad %s" --date=format:"%H:%M:%S"
```

If the project's newest commit is later than the hub's newest commit touching
that item, the hub entry is stale regardless of how complete it reads. Under the
O-P-C consolidation this is the normal condition, not an edge case: hub-level docs
and the live sub-project are separate repos by design.

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

## 2026-08-07 — The cross-repo staleness check belongs in `/continue`, not `/session-end`
**Source:** session (this machine), third occurrence — hub `25b0173` (11:11) vs
Pappa T vault `63687c5` (16:30)
**Status:** active

The entry above ("cannot be answered from the entry") was written specifically to
stop this, and the drift happened again the same day, at a larger magnitude: the
hub's close-out was 5h19m behind the vault, and it asserted three things that were
each false by the time the next session read them — "Phases B–H not started" (B and
C were built), "Phase B is blocked on an ADR" (ADR-004 was written, accepted and
built), and "3 unpushed commits in the vault" (pushed).

**Writing the lesson down did not prevent recurrence, and the reason is structural,
not a discipline failure.** `/session-end` runs the check at the moment the hub is
last correct. It cannot see work that lands afterwards — and in a hub-plus-live-
sub-project setup, work landing afterwards is the *normal* case, because the reason
a session is ending is usually that a different session is still going. A check
placed at close-out is asking the question at the only time it is guaranteed to
return "fine."

**Where it actually works: `/continue` Step 1, as part of orienting** — the reading
session is the one that can be wrong, so it is the one that must check. Treat
`docs/session-log.md`'s final entry as a *claim with a timestamp*, never as state:
before reporting it, diff the hub's newest commit time against the newest commit in
any live sub-project the entry names, and read the project's own `docs/todo.md`
header before repeating the hub's version of its status.

**Generalises past this hub:** any summary file maintained in a different repo from
the work it summarises is stale by default, and its own confidence is not evidence.
The cost is asymmetric — checking is two `git log` calls; not checking hands the
next session a confident, wrong starting brief.

## 2026-08-08 — A `knowledge/` entry is a record, not a control
**Source:** session (this machine), installing the check the entry above prescribes
**Status:** active

The three entries above are the same finding written down three times, each after a
recurrence, each more emphatic than the last. The fourth session ran the check *by
hand* and noted that it still wasn't in `.claude/commands/continue.md`. The reason is
now clear enough to state as a rule: **`knowledge/` records why something is true;
only the command file changes what a session actually executes.** A finding filed in
`knowledge/` is read by a session that goes looking for it, which is precisely not the
session that needs it — the one confidently reporting stale state has no reason to
suspect it should look. Filing the lesson and installing the step are two different
tasks, and the first one feels enough like closure to hide that the second is missing.
When a finding prescribes a step, the close-out is not done until the step is in the
file that runs.

**The prescription needed one correction on contact.** The entry above says the check
belongs in "Step 1, as part of orienting." It cannot go there: Step 1.75 is what pulls
`origin/main`, so a check at Step 1 compares the project's clock against a possibly
stale local hub `HEAD` and can report drift backwards. It went in as **Step 1.9**,
after the sync check and before Step 2, with the ordering dependency stated in the
step itself. Step 1 instead gained one paragraph saying its two reads are a claim with
a timestamp and are not to be carried into the report until 1.9 has run.

**Reporting a *passing* check is load-bearing, not noise.** Step 1.9 requires a line in
the Step 3 report either way, because a silent pass and a check that never ran look
identical from the outside — which is exactly how three recurrences went unnoticed.
Same reason the step requires the live repo's `status --porcelain` output: the hub can
be accurate about what was committed and still wrong about what exists.

**Backporting it upstream is blocked on scope, not on permission.** ADR-008 makes
folding hub `continue.md` improvements into `tlelosa-claude-config/hub-template/` the
expected direction. Step 1.9 can't go alone: it names Step 1.75 and depends on its
ordering, and upstream's template has no Step 1.75 at all. Checked this session, the
template is also missing Step 0.5's stale/idle category B, Step 2.5, and Step 3's
machine-bound report fields — four hub improvements behind, not one. The fold-up is a
real reconciliation job, so it's a queued item rather than a same-session afterthought.
