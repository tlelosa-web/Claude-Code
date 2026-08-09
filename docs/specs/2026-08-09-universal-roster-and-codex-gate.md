# Spec — Make the agent roster, model routing, and `/codex-review` present on every instance

**Date:** 2026-08-09 | **Requested by:** Tebello Lelosa | **Status:** draft, pending review
**Scope:** `tlelosa-claude-config` (marketplace repo) + `CORE.md` hard rules. Cross-machine.

## Problem

Two capabilities that `CORE.md` treats as universal are in fact per-machine
manual installs, and both were silently absent on at least one machine.

**1. The agent roster and its model routing.** `CORE.md` §"Sub-agent roster"
declares 10 agents deployed at user level and "available automatically in
every project", and §"Model routing" pins `reviewer`/`architect` to Opus and
`Explore` to Haiku 4.5. On Pappa T, on 2026-08-09, `~/.claude/agents/` **did
not exist at all** — roughly six weeks after the roster was declared
authoritative. Observed consequences:

- Every DCOE delegation target (`domain`, `planner`, `architect`, `executor`,
  `tester`, `reviewer`, `doc-writer`, `debugger`, `data-agent`) was
  unavailable; only Claude Code built-ins could be reached. Hard rule 3
  ("sub-agents are specialists") and the entire Orchestrate→Execute split
  were unenforceable, with no error surfaced.
- `Explore` fell back to the built-in, which inherits the session model.
  `~/.claude/settings.json` pins `"model": "opus"`, so read-only search ran
  at Opus. `CORE.md` warns this fallback "silently run[s] search delegations
  at Sonnet 5 prices" — the real fallback on this machine was one tier above
  the documented worst case.

The failure is silent by construction: a missing agent produces no warning,
only a quieter, more expensive session.

**2. `/codex-review`.** Universal hard rule 9 requires running it on *every*
spec in `docs/specs/` before dispatching an Executor. `codex-gate` is
installed per machine and is deliberately excluded from `dcoe-roster` so it
can be limited to machines cleared for OpenAI egress. Operations has no
clearance, so on Operations hard rule 9 is unrunnable. A hard rule that
cannot execute on half the estate is a preference, not a rule.

## Constraint that shapes any solution

`docs/specs/2026-07-29-strip-dcoe-roster-agent-bodies.md` removed
`dcoe-roster/agents/` because Claude Code namespaces marketplace plugins by
install-cache commit SHA, so every session listed each agent three times
(unprefixed, `dcoe-roster:*`, `<sha>:*`). Confirmed cosmetic, but the
decision stands and its accepted tradeoff was explicit: "the plugin no longer
doubles as a new-machine roster-bootstrap vehicle."

That tradeoff is precisely what caused problem 1. **The fix must restore
automatic bootstrap without returning agent bodies to any path the plugin
loader scans.** Reverting the strip is not on the table.

## Decision

### A. Roster self-deploys via a plugin-shipped `SessionStart` hook

Add a `SessionStart` hook to `dcoe-roster` that invokes the existing,
idempotent `agent-bodies-reference/bootstrap.sh`. The bodies stay where the
strip spec put them — off every scanned path — and the plugin regains its
bootstrap role through a hook rather than through loader discovery.

Both machines already have `dcoe-roster` enabled, so no new install step is
required: the roster deploys on next session start and self-heals if
`~/.claude/agents/` is ever emptied.

**A.1 — Overwrite semantics must change first.** `bootstrap.sh` currently
overwrites any destination file whose content differs from the reference
copy, printing a one-line notice. That is correct for a hand-run bootstrap
and **wrong for a per-session hook**: the strip spec directs that "editing
now happens directly in `~/.claude/agents/` on each machine", so a
session-start overwrite would silently revert local roster edits on every
launch. These two behaviors are in direct conflict.

Resolve by adding a copy-if-absent mode (e.g. `bootstrap.sh --missing-only`)
and calling *that* from the hook:

- file absent → copy it
- file present, content differs → leave it, print one notice line
- file present, content identical → no-op

The interactive, hand-run invocation keeps today's overwrite behavior. Only
the hook path becomes non-destructive.

**A.2 — Loader-scan assumption (must be verified before build).** This design
assumes Claude Code's plugin loader scans only `<plugin>/agents/` and does
not walk the plugin tree recursively. If it does recurse, nothing changes —
bodies remain at repo root in `agent-bodies-reference/`, and the hook reaches
them relative to `${CLAUDE_PLUGIN_ROOT}` (`../agent-bodies-reference/`),
which resolves inside the marketplace checkout. Verify by observation before
building; do not assume.

**A.3 — Interpreter portability (must be verified before build).**
`bootstrap.sh` is bash. Pappa T has Git Bash on PATH (confirmed 2026-08-09).
Operations is **unverified**. If Git Bash is absent there, the hook fails at
every session start on that machine — reintroducing the same silent gap on
the other machine. Mitigations, in preference order: (1) confirm Git Bash on
Operations and require it; (2) ship a PowerShell sibling and dispatch by
platform; (3) rewrite bootstrap as a portable Node script, since Claude Code
already requires Node.

**A.4 — Failure must be loud.** A bootstrap hook that fails quietly rebuilds
the original defect one layer up. The hook prints a single line on any
failure naming the reason. Silence means success; it must never mean
"never ran".

### B. `/codex-review` — separate presence from function

These are two different problems and must not be conflated.

**B.1 Presence (in scope).** Enable `codex-gate` on every machine. Its step 4
already fail-warns on *any* failure — CLI missing, no credentials, network or
proxy failure, rate limit, non-zero exit, empty output, 90 s timeout — and
exits successfully with "proceeding solo". On an uncleared machine the
command therefore degrades correctly instead of erroring. Presence is safe.

**B.2 Function on Operations (out of scope — external blocker).** Making
`/codex-review` actually *work* on Operations requires OpenAI egress, which
is pending Fan Movement IT clearance. No change in this repo can grant that.

**B.3 Compliance caveat — flagged for the owner's decision.** Auto-enabling a
plugin whose command attempts OpenAI egress on a corporate machine *before*
IT clearance is a compliance question, not a config one. `codex-gate`'s own
plugin description states it is kept out of `dcoe-roster` specifically so it
can be withheld from uncleared machines. **Recommendation:** do not fold
`codex-gate` into `dcoe-roster` and do not auto-enable it on Operations.
Instead amend hard rule 9 to state its own precondition honestly:

> Run `/codex-review` on every spec before dispatching an Executor **on any
> machine cleared for OpenAI egress**. Where the gate is unavailable, record
> `codex: unavailable (<reason>)` in the spec so the omission is visible
> rather than silent. The `reviewer` agent's APPROVE/BLOCK authority is
> unchanged either way.

That makes the rule true everywhere and keeps the omission auditable, without
shipping unsanctioned egress onto a work machine.

## Acceptance criteria

1. On a machine with `dcoe-roster` enabled and `~/.claude/agents/` deleted, a
   new session start leaves all 10 roster files present. Verified by
   `ls ~/.claude/agents/` returning 10 `.md` files.
2. Running two sessions back to back produces identical end state (hook is
   idempotent) and emits no output on the second.
3. A hand-edited `~/.claude/agents/reviewer.md` still contains its local edit
   after a session start, and one notice line names the file.
4. `/agents` lists each roster agent exactly once — no `dcoe-roster:*` or
   `<sha>:*` duplicates (regression guard on the 2026-07-29 decision).
5. A delegation to `Explore` resolves to the roster override and runs on
   `claude-haiku-4-5`, not the session model.
6. With `bash` unavailable on PATH, session start prints exactly one line
   naming the failure and the session continues normally.
7. `/codex-review` on a machine with no OpenAI egress prints
   "Codex second opinion unavailable (<reason>) — proceeding solo", appends
   the warned status to the spec, and exits successfully.
8. `CORE.md` hard rule 9 states its egress precondition; `CORE.md` version
   and `dcoe-roster/plugin.json` version are both bumped.

## Alternatives weighed

- **Revert the strip spec** (ship bodies in `dcoe-roster/agents/` again).
  Rejected: reintroduces triple-listing, the exact defect 2026-07-29 fixed.
- **Documentation only** — write the bootstrap step into `/continue` prose or
  a knowledge entry. Rejected on this hub's own evidence:
  `knowledge/hub-process.md` records that "a `knowledge/` entry is a record
  and not a control — three write-ups did not stop three recurrences; only
  the command file changes what runs." A hook is a control; a paragraph is
  not.
- **Add the check to `/continue`** as another numbered step, alongside the
  existing Step 1.8 and 1.9 guards. Viable and cheaper, but only fires when
  someone runs `/continue`; a `SessionStart` hook covers every session
  including cloud and one-off ones. Worth keeping as a fallback if the hook
  proves unportable (A.3).
- **Fold `codex-gate` into `dcoe-roster`** so one install covers both.
  Rejected — see B.3; it would push OpenAI egress onto an uncleared corporate
  machine.

## Out of scope

Agent body *content*, the DCOE stage definitions, the model-routing table's
values, `shared-skills` enablement, and anything in a sub-project repo.

## Amendment — 2026-08-09 (post-Codex, pre-build)

Folds the strongest points of the advisory review below into the decision,
per universal hard rule 9. Where this amendment and the original Decision
section disagree, **this amendment governs.**

**A.1 → adopt Node, not bash.** Codex is right that acceptance criterion 6
was unsatisfiable as written: if the hook is `bash bootstrap.sh`, a missing
bash means the script never runs and therefore cannot print its own failure.
The bash dependency is replaced with `agent-bodies-reference/bootstrap.mjs`,
run by the Node that Claude Code already requires (`v24.14.0` confirmed on
Pappa T, 2026-08-09). This also retires the A.3 Git-Bash-on-Operations
unknown rather than leaving it as a build-time blocker. `bootstrap.sh` is
kept as the hand-run fallback and is no longer on the hook path.

**A.2 → assumption removed, not verified.** Rather than depend on how the
plugin loader scans, the bodies stay at repo root in
`agent-bodies-reference/`, outside every plugin directory. Concrete path,
confirmed to resolve on 2026-08-09:

```
${CLAUDE_PLUGIN_ROOT}                     = <marketplace>/tlelosa-claude-config/dcoe-roster
${CLAUDE_PLUGIN_ROOT}/../agent-bodies-reference
                                          = <marketplace>/tlelosa-claude-config/agent-bodies-reference
```

The `..` leaves the plugin directory but stays inside the marketplace
checkout, which is the intended layout.

*Corrected 2026-08-09 after testing:* an earlier draft of this amendment
claimed that with `CLAUDE_PLUGIN_ROOT` unset the script "exits with one line
naming that as the reason." That is false and was never true. The script
self-locates from `import.meta.url` and never reads `CLAUDE_PLUGIN_ROOT` at
all; the env var is used only by the hook's command string. With it unset,
Node fails to resolve the module path and prints a multi-line
`MODULE_NOT_FOUND` stack (observed, exit 1). That is loud, which is what the
A.4 rule actually requires, but it is not a clean one-liner and the spec must
not claim otherwise. Accepted as-is: an unset `CLAUDE_PLUGIN_ROOT` is a
Claude Code contract violation, and a visible stack at session start is a
correct response to one.

**New — manifest-driven, replacing directory globbing.** Adopted from Codex.
`agent-bodies-reference/roster-manifest.json` lists the 10 expected agent
filenames and each one's intended model, and is the single source of truth
for "what the roster is". Benefits: criterion 1 can assert exact identity
rather than a count of 10; drift is detectable without overwriting; and the
routing table in `CORE.md` gains a machine-checkable counterpart.

**New — two modes, resolving the drift objection.** Default (hook path) is
missing-only and never destructive. `--repair` restores every file from the
reference copy. Without an explicit repair path, Codex correctly notes that
missing-only mode would preserve a locally broken agent — obsolete
frontmatter, wrong model, invalid YAML — forever and silently.

**B — codex-gate: owner's decision, unconditional enable.** The B.1/B.3
contradiction Codex identified is resolved in favour of B.1.
**Tebello's decision, 2026-08-09, taken with the compliance caveat in B.3
stated and understood:** enable `codex-gate` on every machine now, including
Operations, without waiting for Fan Movement IT clearance on OpenAI egress.
Hard rule 9 stays universal and unqualified; the conditional rewording
proposed in B.3 is **not** adopted. B.2 still holds as fact — the command
will fail-warn to "proceeding solo" on Operations until egress exists — but
that is now a runtime outcome, not a policy caveat. Recorded here as an
owner decision so the reasoning is auditable if IT raises it later.

**Acceptance criteria corrections** (Codex, all accepted):

- **1** — assert the exact 10 filenames from the manifest, not a count.
- **2** — "emits no output" applies only when no file is missing or
  divergent; otherwise it conflicts with criterion 3.
- **3** — test a hand-edited `executor.md` as well as `reviewer.md`, since
  one file cannot demonstrate a generic code path.
- **6** — restated: with Node present but the reference directory missing or
  `CLAUDE_PLUGIN_ROOT` unset, session start prints exactly one line naming
  the reason and the session continues. The unsatisfiable bash variant is
  withdrawn.
- **8** — add `codex-gate` enablement and its version/release path, since B
  now changes that plugin's deployment.
- **New 9** — settings mutation is atomic: `~/.claude/settings.json` is
  parsed, backed up, written to a temp file, validated as JSON, then renamed
  over the original. A malformed write must never be able to break Claude
  Code's config on either machine.
- **New 10** — two bootstraps racing at concurrent session start leave a
  valid end state (Codex's concurrency failure mode).

**Deferred, with reason.** Checksums in the manifest (Codex suggested
filename + checksum + model) are out of this build: the roster is edited
per machine by design under the 2026-07-29 decision, so a checksum would
report drift on every legitimately customised machine. Filenames and models
are stable; content is not. Revisit if per-machine editing is ever retired.

## Codex second opinion (advisory) — 2026-08-09

**Second-Opinion Review**

The spec is directionally sound on separating roster bootstrap from loader discovery, and the `codex-gate` compliance caveat is appropriately skeptical. I would not rubber-stamp it as implementation-ready, though. Several acceptance criteria depend on behavior the spec has not made observable or enforceable.

**1. Buried Or Unstated Assumptions**

- The spec assumes a `SessionStart` hook is guaranteed to run before `/agents`, delegation resolution, and model routing are evaluated. That ordering is critical to criteria 1, 4, and 5, but it is never stated or verified.

- A.2 says: "If it does recurse, nothing changes — bodies remain at repo root in `agent-bodies-reference/`." That is inconsistent with the stated risk. If the loader recursively scans for agent-like files anywhere under the plugin tree, then `agent-bodies-reference/` may still be discovered unless the loader only scans specifically named `agents/` directories. The spec needs to distinguish "recursive under `agents/`" from "recursive under plugin root."

- The hook path assumption is muddy: it says the hook reaches bodies relative to `${CLAUDE_PLUGIN_ROOT}` using `../agent-bodies-reference/`, "which resolves inside the marketplace checkout." If `CLAUDE_PLUGIN_ROOT` points to the plugin directory, `../agent-bodies-reference` sounds outside that plugin directory unless the marketplace layout is unusual. This needs a concrete expected path example.

- The spec assumes environment variables such as `${CLAUDE_PLUGIN_ROOT}` exist and are stable across machines and plugin-cache SHA installs. That is a deployment contract, but it is not included in acceptance criteria.

- The phrase "Both machines already have `dcoe-roster` enabled" narrows the real cross-machine guarantee. The title says "on every instance," but the mechanism only covers instances where the plugin is already installed and enabled.

- A.1 assumes local edits in `~/.claude/agents/` are valid long-term source of truth. That matches the strip spec quote, but it creates configuration drift across machines. The spec does not say whether drift is acceptable, how it is audited, or how intended roster updates propagate later.

- B.1 says "Enable `codex-gate` on every machine," while B.3 recommends "do not auto-enable it on Operations." The final decision is ambiguous. Acceptance criterion 7 tests behavior on a machine with no egress, but criterion 8 asks only for a `dcoe-roster/plugin.json` version bump, not a `codex-gate` installation/enabling change. The spec needs to pick one policy.

**2. Missing Or Untestable Acceptance Criteria**

- Criterion 1 says `ls ~/.claude/agents/` returns 10 `.md` files. That only verifies count, not that the exact 10 expected agents are present, nor that their names match `CORE.md`.

- Criterion 2 says the second session "emits no output." That conflicts with criterion 3, where a local edit emits a notice line. The criterion should specify "when no files are missing or divergent."

- Criterion 3 verifies `reviewer.md` only. Since overwrite behavior is generic, test at least one non-reviewer file or state that testing one file is representative because all files use the same code path.

- Criterion 4 depends on `/agents` output, but the spec does not define an automated or manual verification method. It should state the expected names and forbidden prefixes.

- Criterion 5 is likely hard to prove. "A delegation to `Explore` resolves to the roster override and runs on `claude-haiku-4-5`" requires observing routing, not just file presence. The spec should define the evidence: CLI trace, log line, model banner, or agent metadata.

- Criterion 6 says with `bash` unavailable on PATH, session start prints exactly one line and continues. If the hook itself is configured as `bash bootstrap.sh`, then absence of bash may prevent the script from running at all, meaning the script cannot print the failure. The hook wrapper must be implemented in something available before bash detection, or this criterion is impossible.

- Criterion 7 says `/codex-review` "appends the warned status to the spec." Earlier B.1 says `codex-gate` step 4 fail-warns and exits successfully, but not that it edits the spec. Is appending existing behavior or new behavior? If new, the target location and exact format need to be specified.

- Criterion 8 requires `CORE.md` version and `dcoe-roster/plugin.json` version bumps, but the decision also discusses `codex-gate`. If `codex-gate` is changed or enabled, its versioning and release path should be included.

**3. Failure Modes Not Considered**

- Partial bootstrap: some files copied, then failure occurs. The spec does not say whether the hook should continue copying remaining files, roll back, or report partial success.

- Permission failures: `~/.claude/agents/` may be missing but not creatable, or individual files may be read-only. These should produce the "loud" failure line with enough path detail.

- Corrupt or missing `agent-bodies-reference/`: if the plugin package omits the reference directory, the hook will fail every session. That should be tested directly.

- Concurrent session starts: two sessions may create `~/.claude/agents/` and copy files simultaneously. Copy-if-absent should be atomic enough or tolerant of races.

- Version skew across plugin cache entries: if multiple cached versions exist, the hook may deploy stale references unless the enabled plugin path is deterministic.

- Local edits plus upstream roster changes: missing-only mode preserves local edits forever, including obsolete frontmatter, wrong model routing, or broken YAML. This directly threatens criterion 5 over time.

- Windows path and shell quoting: spaces in profile paths, CRLF vs LF, executable bit handling, and Git Bash path translation can all affect `bootstrap.sh`.

- Session performance/noise: a `SessionStart` hook running every session must be fast and quiet. No timing budget is specified.

- "Exactly one line" failure reporting can be brittle if the shell or hook runner emits its own error. The spec should avoid overconstraining output unless the hook wrapper controls all failure modes.

**4. Architectural Alternatives Worth Serious Consideration**

- **Use `/continue` guard plus explicit health check command.** The spec dismisses this because it only fires when `/continue` runs, which is fair. But it may be more debuggable and less risky than a session hook if hook portability is unknown. I would weigh this seriously if `SessionStart` has weak logging or uncertain ordering.

- **Portable Node bootstrap.** A.3 lists this as third preference, but I would move it higher. Since the spec itself says Claude Code already requires Node, Node avoids the bash-on-Windows problem and makes criterion 6 testable from inside the hook wrapper.

- **Manifest-driven roster deployment.** Instead of copying all `.md` files from a directory, ship a manifest listing expected agent filenames, checksums, and intended models. That would make criteria 1, 3, and 5 much more testable and would expose drift without overwriting local edits.

- **Two-mode sync: install missing by default, explicit repair/update command for drift.** The hook can stay non-destructive, but there should be a deliberate command for "restore roster to reference" or "update stale agents." Otherwise local drift becomes permanent and silent.

- **Make hard rule 9 conditional, not universally executable.** The spec's B.3 recommendation is stronger than B.1 and should probably be the actual decision. If Operations is not cleared for OpenAI egress, auto-enabling `codex-gate` there is not just an implementation detail; it contradicts the plugin's stated separation rationale.

**Bottom Line**

The roster bootstrap approach is plausible, but the spec is not yet tight enough to implement safely. The biggest fixes are: resolve the `codex-gate` contradiction, define the hook execution contract and paths precisely, make the loader-scan verification concrete, and replace bash dependency with a portable wrapper or Node implementation. The acceptance criteria also need to test exact agent identity, routing evidence, failure paths, and drift behavior rather than just file counts.

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._
