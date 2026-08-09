# Spec — Command Center: single status view, agent-roster bootstrap, knowledge-freshness enforcement

**Date:** 2026-08-05 | **Status:** Gap 1 built and landed 2026-08-09; Gaps 2 and 3 landed in
`tlelosa-claude-config` 2026-08-08 — see the 2026-08-09 amendment at the foot of this file
**Basis:** Owner goal stated 2026-08-05: "a command center that has overwatch over everything I
do... launch a project from any interface and get results." Scoped via `AskUserQuestion`:
- **Launch mode:** type a request anywhere (web/mobile/desktop/Slack) and it resumes/starts
  the right project with the right context — a routing/discoverability problem, not a new
  channel to build (the platform already supports cross-surface session access).
- **Priority gaps (all three, not ranked):** (1) no single status view across all repos/
  machines, (2) `~/.claude/agents/` roster bootstrap gap not solved everywhere, (3)
  `knowledge/*.md` cache can silently go stale.

This spec covers the three confirmed gaps. It does **not** cover building a new interface —
the owner confirmed "type a request anywhere" as the launch model, which this platform already
provides; the gap is what happens *after* the request lands, not how it's delivered.

**Build order, locked 2026-08-05:** Gap 1 (`/overwatch`) ships first. Gap 2 (roster bootstrap)
and Gap 3 (knowledge-freshness prompt) follow as separate Executor tasks after — this is a
sequencing decision, not a scope cut; all three remain in this spec.

-----

## Gap 1 — No single status view

### Problem
Status today is scattered: this hub's own `docs/todo.md` (hub-level only, by its own header),
each project's own `docs/todo.md`, and `knowledge/*.md` (facts, not live status). Getting
"what's in flight, what's blocked, what's done" requires manually opening N files.
`tlelosa-claude-config` has its own separate `docs/todo.md` too, config-repo-specific.

**Correction (reviewer finding, 2026-08-05):** the original draft assumed `knowledge/INDEX.md`
could double as `/overwatch`'s project list — "one file per known project" with a resolvable
path. Verified against the actual file: `INDEX.md` has exactly three columns (File / Covers /
Last updated) — a knowledge-topic filename and a prose description, no path to a project's
repo or `docs/todo.md`. Its 14 rows also aren't all individual project repos — two
(`operations-hub.md`, `pappa-t.md`) are machine-level cross-project notes with no `docs/todo.md`
of their own to read. Sourcing the project list from `INDEX.md` as originally proposed would
have `/overwatch` attempt to read nonexistent files for those two rows, and silently
mis-scope every knowledge-topic-that-isn't-a-project row the same way. The "13 known
sub-projects" claim was also wrong by at least 2 on this basis.

### Proposed solution: a `/overwatch` command in this hub
A new slash command, `.claude/commands/overwatch.md`, that:
1. Reads this hub's own `docs/todo.md` (In progress / Next up / Backlog).
2. Reads each sub-project's `docs/todo.md` Open section, from an **explicit project→path list
   maintained inside `overwatch.md` itself** (not derived from `INDEX.md`, per the correction
   above) — accepting the small maintenance cost of a hardcoded list over the false economy of
   a self-updating source that doesn't actually carry the needed structure.

   **Live-vs-stale path ambiguity (reviewer finding, round 2) — resolved:** this repo holds
   two different path sets for the same sub-projects — the O-P-C-merged snapshot folders now
   inside this repo (`Operations/`, `Pappa T/`), which this hub's own `docs/todo.md` explicitly
   warns are a **historical snapshot, not the live working copy**; and the live per-machine
   paths (`Desktop/Operations/`, `Desktop/Pappa T/`) that only exist on the physical machines,
   not in a cloud environment like this one. The list must point at the **live** paths
   (`Desktop/...`) as the canonical target — matching this hub's own stated convention that
   fixes must land in the live copy, not the snapshot. On a machine/environment where a listed
   live path isn't reachable (e.g. any cloud session), `/overwatch` **skips that project with a
   one-line "unreachable from this environment" note** in its output rather than silently
   falling back to the stale snapshot or failing the whole command. The snapshot paths are
   never read by `/overwatch`.

   The list itself is seeded at Execute time from every currently known live project path (per
   this hub's own `docs/todo.md`/`knowledge/` content), and updated by hand going forward
   whenever a project repo is added or removed — same discipline as this hub's other
   hand-maintained lists (e.g. `docs/todo.md` itself). A project with no live `Desktop/...`
   path at all (none currently exist in this repo's tracked project set) is simply never
   seeded into the list in the first place — distinct from a listed project being skipped with
   a note for being unreachable *this run*.
3. Reads `tlelosa-claude-config/docs/todo.md` Open section (the config repo, tracked
   separately since it isn't itself a project in the sense of item 2's list).
4. Renders one consolidated report: per project, its open items (title + one-line status),
   grouped by the 📍/⚠️ machine-reachability flags already in use in this hub's `todo.md`
   convention, plus a top-line count (X open across Y projects, Z blocked on owner decision).
5. Does **not** write anything — read-only aggregation, same spirit as the `reviewer` agent's
   read-only contract.

### Decisions locked (owner, 2026-08-05)
- **Open-items-only.** `/overwatch` never surfaces `docs/session-log.md` — strictly "what's
  open," across every source in step 1-3 above. Recent activity stays a separate,
  already-existing read (`docs/session-log.md` directly) if ever needed.
- **Priority: this gap ships first.** Of the three gaps, the status view is the one to build
  and land before the other two — Gap 2 (roster bootstrap) and Gap 3 (knowledge freshness)
  follow after, not in parallel.
- **Render: plain text in-session.** No Artifact dashboard for `/overwatch` itself (the
  earlier "leaning plain text" option, now locked). An Artifact version stays a possible
  later, separate skill — not part of this spec.

-----

## Gap 2 — Agent-roster bootstrap gap

### Problem
Per `dcoe-roster/docs/specs/2026-07-29-strip-dcoe-roster-agent-bodies.md` (in
`tlelosa-claude-config`), the roster is no longer plugin-installed — each machine needs the 9
files in `agent-bodies-reference/` manually copied into `~/.claude/agents/`. This was
discovered 2026-08-03 when a machine had **no agent files at all**, silently. Confirmed again
today (2026-08-05, this session): this cloud environment also has no `~/.claude/agents/`,
forcing a workaround (a `general-purpose` agent carrying the `reviewer.md` persona verbatim,
substituting for the real `reviewer` agent type) to get a review done at all. That workaround
is a stopgap, not a fix — it lacks the real agent's `tools:`/`model:` frontmatter enforcement
(e.g. read-only tool restriction, permanent Opus pin) since a `general-purpose` agent has
broader tool access than the persona's declared `tools: Read, Grep, Glob`.

This is exactly the "silent gap" pattern the JSON-validation-hook spec (in
`tlelosa-claude-config`) was built to close for manifest JSON — the same shape of problem
recurring in a second place: a manual per-machine/per-environment step with no drift
detection.

### Proposed solution: session-start roster check + a real bootstrap script
1. **Detection, every session, every machine/environment:** add one line to `CLAUDE.md`'s
   SESSION START (in every project that opts into DCOE, i.e. every project with the CORE.md
   read instruction) — check whether `~/.claude/agents/` (**user-level only**; this check is
   unaffected by CORE.md's project-level `.claude/agents/` override precedence, which governs
   a single project substituting one agent, not whether the user-level roster itself exists)
   contains the 9 expected roster filenames. If any are missing, print a one-line warning naming which are missing, same
   pattern as the JSON-hook spec's `core.hooksPath` drift check. This makes the gap visible on
   *every* session (including fresh cloud environments like this one) instead of only being
   discovered when a review is attempted and silently degrades to a workaround.
2. **A real bootstrap mechanism, not manual copy-paste:** `tlelosa-claude-config` gains
   `agent-bodies-reference/bootstrap.sh` — copies all 9 files from
   `agent-bodies-reference/` into `~/.claude/agents/`, idempotent, safe to re-run. The
   session-start warning names this script as the fix. This turns "go manually copy 9 files"
   into "run one script," which is both faster and less error-prone across three-plus
   environments (Operations, Pappa T, and any future cloud session/environment).
3. **Open question this spec surfaces rather than resolves:** should ephemeral cloud
   environments (like this one — reclaimed after inactivity, no persistent `~/.claude/agents/`
   across sessions) get the roster bootstrapped automatically at environment setup instead of
   detected-and-warned every time? That would need a setup script wired into the environment's
   own configuration (outside this repo's control) rather than a `CLAUDE.md` session-start
   check. Flagging for owner decision — out of this spec's scope to solve environment
   provisioning.

-----

## Gap 3 — Knowledge cache can go stale

### Problem
`Claude-Code/CLAUDE.md`'s hard rule 5 already states the obligation ("Update
`docs/todo.md` and `docs/session-log.md` after every hub-level task, same discipline as the
knowledge-cache update rule"), but it is prose only — self-monitored, same trust model as
every other `CLAUDE.md` rule, with nothing that actually checks whether a session that
surfaced a reusable fact went back and wrote it down.

### Proposed solution: a session-end checklist prompt, not a hard gate

**Correction (reviewer finding, 2026-08-05):** the original draft claimed this hub already had
`.claude/commands/session-end.md` "per ADR-010" to extend. Verified against the filesystem:
this hub's `.claude/commands/` contains only `continue.md` — no `session-end.md` exists here,
and `docs/decisions/` contains ADR-007/008/009 only, no ADR-010. Only `tlelosa-claude-config`
actually has a `session-end.md` (its own "minimal instance," per that repo's `docs/todo.md`).
The `[x]` Done entry in `tlelosa-claude-config/docs/todo.md` (2026-08-04) claiming "a full
instance in the Claude-Code hub" recorded work that was never actually completed here — a
stale/incorrect todo entry, not a real prior deliverable. This spec does not attempt to
resolve that discrepancy (out of scope — it's a separate, smaller correction); it just stops
building Gap 3 on a false premise.

Full enforcement (e.g. blocking session end until `knowledge/` is touched) is both technically
awkward (sessions don't have a clean single exit hook comparable to a git commit) and wrong in
spirit — most sessions don't surface a new reusable fact, so a mandatory gate would be a false
positive most of the time. Instead:
1. **Create** (not extend) `.claude/commands/session-end.md` in this hub, adapted from
   `tlelosa-claude-config/.claude/commands/session-end.md` the same way `continue.md` was
   already adapted here (per this hub's own `CLAUDE.md`: "the `/continue` resume command, from
   `tlelosa-claude-config`'s `hub-template/`, copied here 2026-07-28") — same promotion
   pattern, same source of truth, just not yet actually copied over for `session-end`.
2. Include one explicit checklist question near the end of its flow: "Did this session surface
   a reusable fact not yet in `knowledge/`? [If yes, capture it now before closing out.]" — a
   prompt to the *model*, at the point it's already reviewing the session, not a gate the owner
   has to answer.
3. This is now correctly scoped as **creating a new file from an existing template**, not
   "extending an existing command" as the draft wrongly claimed — a materially larger task than
   originally stated, still small in absolute terms (one adapted file), consistent with this
   hub's own hard rules (soft, self-monitored, but at least now prompted explicitly rather than
   left to be remembered).

### Decision locked (owner, 2026-08-05)
- **Session-end prompt only, for now.** Per the owner's "open items [Gap 1] first" sequencing
  call, the periodic-audit Routine option is deferred, not designed or committed in this spec
  — the session-end checklist question is the whole of Gap 3's fix here. Revisit the stronger
  option later, as its own follow-up, only if the soft prompt proves insufficient in practice.

-----

## Out of scope (this spec)

- Building a new interface/channel for "launch from anywhere" — confirmed unnecessary; the
  platform's existing cross-surface session access already covers this. If discoverability of
  *which* session/interface to use turns out to be the remaining gap once the above three are
  fixed, that's a follow-up spec, not bundled here.
- Automated environment provisioning of the agent roster (see Gap 2's open question).
- The stronger knowledge-freshness Routine option (see Gap 3's open question) — flagged, not
  designed, pending owner appetite.
- Any change to `dcoe-roster/CORE.md` itself — all three fixes live in `CLAUDE.md` (per-
  project session-start addition) or `tlelosa-claude-config` (bootstrap script), not the
  universal core, since none of the three are new *rules* so much as *enforcement* of rules
  already stated there.

## Acceptance criteria

1. `/overwatch` run from this hub produces one consolidated report covering this hub's
   `docs/todo.md`, every project in `overwatch.md`'s own hand-maintained project→path list
   (live paths, not the O-P-C snapshot — reachable ones read normally, unreachable ones listed
   with a one-line "unreachable from this environment" note), and
   `tlelosa-claude-config/docs/todo.md` — without editing any file.
2. A session started in an environment with zero files in `~/.claude/agents/` (e.g. this one,
   today) prints a named-missing-files warning at session start, once, referencing the
   bootstrap script.
3. `agent-bodies-reference/bootstrap.sh` in `tlelosa-claude-config`, run twice in a row, ends
   in the same state both times (idempotent) and leaves the 9 expected files present in
   `~/.claude/agents/`, matching their source content — not "exactly 9 files total" (a
   pre-existing unrelated file in that directory is left untouched either way, per the
   reviewer's finding that "exactly 9" is unverifiable without assuming an empty starting
   directory). The script does not silently clobber a locally-modified copy of one of the 9
   without at least a printed notice that it overwrote a file whose content differed from the
   reference.
4. This hub's newly-created `.claude/commands/session-end.md` (adapted from
   `tlelosa-claude-config`'s instance — no ADR-010 exists for this; that citation was a
   rev-1 factual error, see revision history) includes the reusable-fact checklist question in
   its flow, and otherwise matches the behavior of the `tlelosa-claude-config` instance it was
   adapted from.

## Which repo(s) this touches

- `Claude-Code` (this hub): new `.claude/commands/overwatch.md`; `CLAUDE.md` session-start
  addition (agent-roster check); **new** `.claude/commands/session-end.md` (created, not
  amended — adapted from `tlelosa-claude-config`'s instance, per the Gap 3 correction above).
- `tlelosa-claude-config`: new `agent-bodies-reference/bootstrap.sh`; the same `CLAUDE.md`
  session-start addition (since it also opts into DCOE and reads `CORE.md`); its
  `hub-template/session-end.md` (the vault-agnostic source both hubs' `session-end` instances
  derive from) gets the checklist-question addition once, which then flows to both instances
  when each is created/updated from it.
- Any other project with its own `CLAUDE.md` that includes the CORE.md session-start
  instruction inherits the agent-roster check once it's added there — this is a template-level
  change (`CLAUDE.md.template` and/or `hub-template/`), not something each project edits
  independently. Confirm during Execute which projects currently carry that instruction before
  touching each one.
- **Separate, smaller correction — resolved 2026-08-05, after Gap 3 shipped:**
  `tlelosa-claude-config`'s `docs/todo.md` 2026-08-04 entry claimed a "full instance in the
  Claude-Code hub" for `session-end`, and `ADR-010`, were already delivered — both were false
  when written. Gap 3 landing made the first claim true retroactively; `ADR-010` was written
  for real the same day (`Claude-Code/docs/decisions/ADR-010-session-end-command.md`) and the
  `tlelosa-claude-config/docs/todo.md` entry was corrected in place to record the true dates
  rather than silently going along with the original (false) ones.

## Codex second opinion (advisory) — 2026-08-05

`/codex-review` was attempted against this spec. Unavailable this session: the Codex CLI is
not installed on this machine (`command -v codex` failed). Per the codex-gate spec's mandatory
fail-warn behavior, this is logged as a warn, not treated as a blocker or retried. No external
cross-family opinion exists for this spec yet.

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._

## Revision history

- **2026-08-05, rev 2:** Reviewer agent pass (general-purpose agent carrying the `reviewer.md`
  persona, standing in for the unbootstrapped native `reviewer` agent) returned **BLOCK** on
  rev 1, citing two factual errors verified against the filesystem rather than the spec's own
  claims: (1) Gap 3 assumed this hub already had `.claude/commands/session-end.md` "per
  ADR-010" to extend — neither the file nor that ADR exists here; corrected to "create from
  `tlelosa-claude-config`'s template," and flagged the source `docs/todo.md` entry that
  wrongly claimed this was already done. (2) Gap 1's `/overwatch` design assumed
  `knowledge/INDEX.md` carried project paths it doesn't have (three prose columns, no path
  field, and 2 of 14 rows aren't individual projects at all) — corrected to an explicit
  hand-maintained project→path list inside `overwatch.md`. Also fixed as non-blocking:
  loosened AC3's "exactly 9 files" to match-source-content without assuming an empty starting
  directory, and added a note that the roster drift check is user-level-only and independent
  of CORE.md's project-level override precedence.
- **2026-08-05, rev 3:** Reviewer re-review of rev 2 returned **BLOCK** a third time — the
  prose corrections from rev 2 held up under independent filesystem verification, but two
  leftover references (AC1 still pointed at `knowledge/INDEX.md`, AC4 still cited the
  nonexistent "ADR-010") survived in Acceptance Criteria despite being fixed in the body text
  above them — the correction pass hadn't propagated all the way through the doc. Separately,
  the rev-2 fix itself (a hand-maintained project→path list) introduced a new, unresolved
  ambiguity: this repo holds two different path sets for the same sub-projects (the O-P-C
  merged-snapshot folders, explicitly flagged elsewhere in this hub as historical/not-live, vs.
  the actual live per-machine `Desktop/...` paths) with no stated rule for which the list
  should use or how `/overwatch` should behave when a live path isn't reachable from the
  current environment. Fixed by: locking the list to live paths only, specifying a
  skip-with-one-line-note behavior for unreachable projects (never silently falling back to
  the stale snapshot), and rewriting AC1/AC4 to match the already-corrected body text.
- **2026-08-05, rev 4:** Reviewer re-review of rev 3 returned **APPROVE WITH NITS** — both
  round-2 blockers confirmed genuinely resolved. One non-blocking nit: the path-list resolution
  didn't explicitly name the case of a project with no live path at all (distinct from one
  that's temporarily unreachable) — added one clarifying clause. Cleared for Execute.

## 2026-08-09 — Gap 1 landed, and what four days on an unmerged branch cost

This spec and `/overwatch` sat on `claude/continuation-utn4f5` from 2026-08-05 until today,
built and reviewer-approved but unreachable from `main` — the case the 2026-08-08 audit found
sixteen of, and the last open piece of this three-part initiative. Gaps 2 and 3 landed in
`tlelosa-claude-config` on 2026-08-08. Owner call today was to land Gap 1 with its path table
verified first rather than as-is.

**The branch was not merged, and merging it would have been wrong.** Diffed against `main` it
showed 16,050 deletions across 81 files — all of it `main`'s own four days of work that the
branch predates, including the 68-commit vault re-merge. Only two files existed on it that
`main` lacked. Those two were cherry-picked across with `git archive`; the branch was then
deleted. This is rev 3's live-vs-snapshot lesson recurring one level up: **a branch that looks
like it holds work can be holding mostly absence.**

**Verifying the path table before landing it found three wrong entries out of nine** — a 33%
error rate in a hand-maintained list that had passed two reviewer rounds, because a reviewer
reads a path and a filesystem answers it:

1. **`delivery-note-system` and `daily-sales-order-files` both pointed into `C:\Dev\`, a drive
   that does not exist on this machine.** The path came from `knowledge/operations-hub.md`,
   which correctly recorded a relocation off the OneDrive-synced Desktop — back when Operations
   was its own machine. The 2026-08-03 consolidation moved it here. **A knowledge entry that
   was accurate when written is not evidence about where a file is today**, which is the same
   failure class as the stale-session-log problem `/continue` Step 1.9 exists for, applied to
   paths instead of clocks.
2. **Step 3's config-repo path (`../tlelosa-claude-config/`) resolved nowhere.** Worse than
   missing: two clones of that repo exist on this machine, and on 2026-08-08 a fix was applied
   to the stray one and reported done while the governing clone stayed broken. A step that
   tells a session to look around for the repo re-opens exactly that. Now pinned to the
   marketplace path `/continue` Step 1.5 reads.
3. **`ai-outreach-agency`'s path shipped hedged as "inferred from convention."** It was
   correct — but a status view that is unsure whether it is looking at a project is not a
   status view. Verified and the hedge removed.

**One project was missing entirely:** `Desktop/Operations/docs/todo.md`, the Operations
machine-level queue, sibling to this hub's own. Added.

**Smoke-tested end to end after the corrections:** all eight paths resolve, 82 open items
across them. The two corrected `C:\Dev\` entries alone account for 9 of those — 5 NamePlateTool
items and 4 delivery-note-system items that the command as originally written would have
reported as unreachable, silently, on every run. That is the gap this command exists to close,
and it would have shipped with the gap still open.

**The standing lesson, now written into the command itself:** a hand-maintained table is worth
only what its last verification was worth. The file carries the 2026-08-09 verification date
and instructs future sessions to treat a missing path as a defect in the table rather than as
an unreachable project.
