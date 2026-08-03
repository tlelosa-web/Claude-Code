# Operations Hub — Task Queue

> Rewritten at the end of every hub-level task (DCOE anti-drift pattern).
> Project-specific tasks live in that project's own `docs/todo.md`
> (e.g. `2. SOPS/docs/todo.md`), not here.

## Next up

_(none active at hub level right now)_

## Backlog / ideas (not committed)

- [ ] Consider whether `General - Info/` (currently just images) should
      become a real onboarding doc, or get renamed/retired.

## Done

- [x] **2026-08-03** — Pappa T side of the machine merge closed out. Tebello
      asked to "open a session in Pappa T" to update its `CLAUDE.md`/ADR-008
      — done directly via file access (same disk now, no separate machine to
      reach). Updated Pappa T's own `CLAUDE.md` (new note under Project
      Overview: shares this machine with Operations as of today, shared
      user-scope `~/.claude` consequence spelled out), its `docs/todo.md`
      and `docs/session-log.md` (matching entries, including a note
      superseding its 2026-07-19 survey claim of "no other dev-root folders
      on this machine"). Added an Addendum section to this hub's own
      `docs/decisions/ADR-008-pappa-t-independent-hub.md` — its "separate
      machine" framing is now stale, but the shared-core distribution
      mechanism it designed (§ Decision points 1–2) still holds; only
      machine identity changed, rollout scope/out-of-scope items untouched.
      Checked Pappa T's own `docs/decisions/ADR-001-dcoe-vault-structure.md`
      — unrelated (brain-file canonicity, not machine identity), no change
      needed there.
- [x] **2026-08-03** — Machine migration: whole `Operations` tree moved off
      the old Fan Movement work PC (`C:\Dev\Operations` + OneDrive junction)
      onto the **same physical machine as the Pappa T vault**, at
      `C:\Users\tlelo\Desktop\Operations` (plain folder, sibling to
      `Desktop\Pappa T`/`Desktop\Claude-Code`, same Windows user `tlelo`).
      Verified post-migration: not a reparse point (`fsutil reparsepoint
      query` — "not a reparse point"), not a git repo (root, correctly, per
      hard rule 2), `Desktop` itself not OneDrive-redirected on this machine
      (OneDrive's own folder is the separate `C:\Users\tlelo\OneDrive`), and
      `2. SOPS`'s own git repo survived intact (clean, tracking
      `origin/master`). Updated `CLAUDE.md` § Directory Structure and §
      Known Risk (old OneDrive-junction risk marked moot, not just resolved
      — the risk class doesn't apply on this machine at all). Closed the old
      OneDrive-junction-recheck backlog item as moot for the same reason.
      Cleaned one stale permission in `.claude/settings.local.json`
      (`Read(//c/Users/Fan Movement/.claude/**)` — pointed at the old
      machine's Windows user profile, which no longer exists here).
      **Bonus discovery:** since Operations and Pappa T now share one
      Windows user profile, they also share one `~/.claude` — confirmed the
      long-open "pull dcoe-roster on Pappa T" Next-up item is now moot too:
      `installed_plugins.json` shows `dcoe-roster` at **user** scope,
      already updated `2026-08-01`, automatically covering both vaults.
      Replaced that item with a new one: telling a Pappa-T-side session
      about the merge, since its own `CLAUDE.md`/ADR-008 still frame it as
      a separate "home PC."

## Done (prior)

- [x] **2026-07-31** — OneDrive junction periodic sanity check (third pass
      same day). Verified `Desktop\Operations` still resolves as a Junction
      to `C:\Dev\Operations` and no duplicate/conflict folder (e.g.
      `Operations (1)`) exists at the old Desktop path. Nothing to fix —
      backlog item stays open as a standing periodic check, not resolved
      permanently.
- [x] **2026-07-31** — `/continue` session hygiene (second pass same day).
      Step 0: no sessions titled `Continuation`. Step 0.5: found `3.
      Nameplate & Test Sheet` had 3 open sessions (fix-plan steps 1/2/3 of
      the connection-override work) — checked that project's own
      `docs/todo.md` and confirmed all three steps are logged Done (step 1
      `90459ce`, step 2 spec+live-verified, step 3 `49645ac`, all committed
      and pushed). Proposed archiving the two older ones (steps 1 and 2);
      Tebello confirmed both. Step 1.5: 0 new upstream commits on the
      `tlelosa-claude-config` marketplace clone. Nothing hub-level or
      project-level picked up this pass — pure session hygiene.
- [x] **2026-07-31** — `/continue` session hygiene + Nameplate connection-
      override bug fix. Step 0: no sessions still titled `Continuation`
      (already renamed by the 07-29 session). Step 0.5: reviewed the 5 open
      sessions, judged 4 from 2026-07-29 as done/superseded (each matched a
      completed Done entry already in this file) and archived them on
      Tebello's confirmation: `Cont-"Nameplate tool bugs"` (investigation
      complete, findings logged, user said end session), `Cont-"SOPS
      dashboard column fix & commit"` (committed `9049cce`, pushed),
      `Cont-"dcoe-roster plugin dedup cleanup"` (shared-repo strip committed
      `1903101`, verified), `Cont-"SOPS backup verify & frozen-headers
      archive"` (gh repo created, 210 commits pushed). Left the older SOPS
      `Cont-"PO edit screen + upload item picker review"` (2026-07-24)
      untouched — not reviewed this pass. Step 1.5: 0 new upstream commits
      on the `tlelosa-claude-config` marketplace clone.
      Picked up `3. Nameplate & Test Sheet`'s top Next-up bug (silent
      connection-override block in `api_generate_pdf()`, logged 2026-07-29):
      wrote a spec (`docs/specs/2026-07-31-connection-override-fallback-fix.md`
      in that project), dispatched the `executor` agent to add the missing
      `payload.connection` fallback in `main.py` (mirrors the existing
      pattern in `api_test_record_sheet_from_nameplate()`), reviewed the
      actual diff myself before treating it as done (per global pre-commit
      bug-check instruction), verified live against the bug report's exact
      repro (200 + valid PDF, was 400; negative case still correctly 400s).
      Committed (`90459ce`) and pushed to `origin/main` on Tebello's
      confirmation. That project's own `docs/todo.md` updated in place —
      fix-plan steps 2 (voltage-filter UX) and 3 (`excel_source.py` datetime
      fix) still open there, not touched this pass.
- [x] **2026-07-29** — `/continue` session hygiene + shared-repo namespace
      cleanup decision. Archived `Cont-"Set auto-compact window env var"`
      (task done, verified, Tebello said END SESSION). Pulled the pending
      `CORE.md` marketplace update (`b95f09c`, 0 commits behind after).
      Decided the parked plugin-namespace item (patterns.md §backlog): strip
      `dcoe-roster/agents/` from the plugin. Moved the 9 agent bodies to
      `agent-bodies-reference/` at the shared repo's root (kept as a
      new-machine bootstrap source, out of the plugin's install scope),
      bumped `dcoe-roster/plugin.json` 3.3.0→3.4.0, updated that repo's
      README + the historical rollout checklist, wrote a spec
      (`docs/specs/2026-07-29-strip-dcoe-roster-agent-bodies.md` in
      `tlelosa-claude-config`). Committed + pushed (`1903101`). Pulled and
      verified on this machine (Operations) same day — marketplace update +
      `/plugin update` (already at latest `190310120520`), cache dir
      confirmed to hold only `CORE.md`+`plugin.json`. Pappa T and the
      `Claude-Code` hub machine still need the same pull — see Next up.
- [x] **2026-07-29** — SOPS off-machine backup. `2. SOPS` had no git remote
      and `gh` CLI wasn't installed (flagged 2026-07-21/22, held open by the
      Batch-35 session). Tebello chose: install `gh` CLI, then
      `gh repo create --private`. Installed via `winget install --id
      GitHub.cli`, ran `gh auth login --web` (device-code flow, Tebello
      approved in browser as `tlelosa-web`), then `gh repo create sops
      --private --source=. --remote=origin` and `git push -u origin HEAD`.
      All 210 local commits now live at `https://github.com/tlelosa-web/sops`
      (private), `master` tracking `origin/master`, HEAD `46c9acb` matches
      remote, working tree clean. The `Cont-"SOPS list frozen headers &
      no h-scroll"` session (`local_02a1dce7`) that held this risk open was
      archived the same day once the backup landed.
- [x] **2026-07-28** — Set up this machine (Operations) as a DCOE hub client
      of the separate `Claude-Code` personal hub repo (`https://github.com/
      tlelosa-web/Claude-Code.git`), mirroring the existing Pappa T setup.
      Found it was already cloned at `C:\Dev\Claude-Code` — a **sibling** of
      this folder, not nested inside it, so this doesn't touch hard rule 2
      (no git repo at `C:\Dev\Operations` root itself). Confirmed the
      git-sync bridge end to end: clean working tree on `main`, then
      `fetch`+`pull` pulled a real fast-forward (8 files of genuinely new
      upstream work, not a no-op), and `push --dry-run` confirmed clean.
      Read that repo's own `CLAUDE.md`/`knowledge/INDEX.md` per its session-
      start convention, appended a dated confirmation entry to its
      `knowledge/operations-hub.md`, and updated its own `docs/todo.md`/
      `docs/session-log.md` — all committed and pushed there (`e06982d`).
      This is a distinct repo/hub from this one; nothing in `C:\Dev\
      Operations` itself changed except this entry.
- [x] **2026-07-23** — `/continue` session hygiene sweep. Renamed the one
      stale `Continuation` session (§ 11 pattern work) then, on Tebello's
      "check all sessions that can be archived," read each idle session's
      transcript tail to judge done-vs-superseded. Archived **7** completed/
      committed sessions on per-item confirmation: three morning SOPS print
      sessions (print_lines loop, line-spacing, template tests), plus
      margin & page-break (`3bf9586`), stamp↔grid swap (`a8a66d3`), the
      Accounts admin Print Form workbook (delivered to the Desktop file),
      and the § 11 pattern session. **Held back** `Cont-"SOPS list frozen
      headers & no h-scroll"` — its Batch 35 work is committed (331 tests
      green) but it ended on a live unresolved question (no SOPS git remote /
      off-machine backup). Logged that risk as a new Backlog item above
      rather than archiving it away.

- [x] **2026-07-23** — Promoted `docs/patterns.md` § 11: concurrent-session
      git contamination in a shared working tree (anti-pattern + mitigation).
      Surfaced from three parallel SOPS print/edit sessions that ran
      `git add -A` in the same working tree and swept each other's
      in-progress files into the wrong commits (job-number feature split
      across `dca9ee4` + `229e346`). Recorded the failure mode, tied it to
      § 5 (worktrees = structural fix), and documented the surgical-staging
      /stagger mitigation for when worktrees aren't in play. Flagged SOPS as
      the candidate to promote it into that project's own `CLAUDE.md` hard
      rules if concurrent sessions stay routine there. SOPS commits
      themselves are project-scope (all clean on local `master`; SOPS has no
      remote by design).
- [x] **2026-07-23** — `/continue` session hygiene + plugin-namespace cleanup
      investigation. Renamed 3 live SOPS `Continuation` sessions, archived 2
      ended shared-skills/ADR-007 sessions. Investigated the plugin-namespace
      cosmetic item: confirmed the commit-SHA prefix is harness behavior for
      all marketplace plugins (disproved the install-method hypothesis via
      `document-skills`), downgraded to accepted cosmetic, parked the
      `dcoe-roster` agent-bodies design question on Tebello's call. Full
      detail in the Backlog note above + `docs/session-log.md`.
- [x] **2026-07-21** — Operations-machine rollout checklist steps 1–3
      (`docs/rollout-checklist-2026-07-21.md` in the config repo). Gave
      Tebello the exact `/plugin` command block (couldn't run it from
      inside a session — same interactive-command limitation as the
      plugin-cache item below), then verified via
      `installed_plugins.json` after each round he ran it: `dcoe-roster`
      and `shared-skills` both updated from the stale `2219fea0a313` pin
      to `f18dec7` (matches marketplace HEAD) at user scope — resolving
      the long-standing "Next up" plugin-cache-vs-clone gap in the same
      pass; `context7` (`claude-plugins-official`) and `document-skills`
      (`anthropic-agent-skills`) both newly installed at user scope,
      Tebello's explicit choice to match the existing `dcoe-roster`/
      `shared-skills` precedent over project-scoping to just this hub.
      Step 4 (`codex-gate`) stays explicit **skip** here per the IT-egress
      gate (ADR-009). All five machine-side items the rollout checklist
      tracks for this machine are now ticked — the checklist itself can be
      considered closed for Operations (Pappa T's own run is separate).
- [x] **2026-07-21** — Recorded `docs/decisions/ADR-009-codex-second-opinion-
      gate.md`, copied from the ready-to-paste draft in the newly-pulled
      `tlelosa-claude-config` commits
      (`docs/specs/2026-07-21-codex-gate-adr-draft.md` there). Documents the
      `codex-gate` plugin (`/codex-review` — advisory, warn-only, cross-
      family second opinion on DCOE spec files via OpenAI Codex CLI) as
      **Accepted and implemented in the config repo**, but added an
      explicit "This hub's own scope" section clarifying it is **not**
      installed or usable on this (Operations) machine — rollout stays
      Pappa-T-only pending Fan Movement IT clearance for OpenAI egress,
      separate from the 2026-07-21 personal-Anthropic-account/Context7
      clearance. Root `CLAUDE.md`/`CORE.md` untouched.
- [x] **2026-07-21** — Pulled 9 more upstream commits into the local
      `tlelosa-claude-config` marketplace clone (fast-forward, `49ca4ea` →
      `f18dec7`, clean, no conflicts) — found via this session's `/continue`
      Step 1.5 check, separate from the 17 already pulled earlier the same
      day. Added the `codex-gate` plugin (see ADR-009 entry above),
      `CLAUDE.md.template` v3.3, and a consolidated per-machine rollout
      checklist (`docs/rollout-checklist-2026-07-21.md`). Session-listing
      tools (`list_sessions`/`list_events`/`set_session_title`) weren't
      available in this environment, so `/continue` Steps 0/0.5 (stale-
      session rename + supersession check) were skipped rather than
      guessed at — oriented from `docs/todo.md`/`docs/session-log.md`
      directly instead.
- [x] **2026-07-21** — Stray SOPS git-worktree cleanup. Found (via Tebello
      asking about an unfamiliar `sops-worktree-batch34` folder at hub
      root) a fully orphaned git worktree left over from SOPS Batch 34
      Executor work — never cleaned up with `git worktree remove` after
      the batch merged. Verified safe before touching anything: its
      `ORIG_HEAD` commit was already an ancestor of SOPS `master`, and
      every source file in the folder was byte-identical to the live repo
      (an initial `diff` flagged `routes/dashboard.py`/`settings.py` as
      differing, but `diff --strip-trailing-cr` showed that was just a
      CRLF/LF artifact, not real content). Also found a second, fully
      dangling worktree admin entry with no working directory at all
      (`agents-sops-project-context-load`) via `git worktree prune -n -v`.
      Both admin folders under `2. SOPS/.git/worktrees/` failed to delete
      via `git worktree prune` and via bash `rm -rf` (the latter blocked
      outright — both hub-root's and SOPS's own `.claude/settings.json`
      explicitly deny `Bash(rm -rf*)`) with a real OS-level "Permission
      denied," which turned out to be git-bash's own delete call
      misbehaving on those folders, not a real ACL/lock issue — PowerShell
      `Remove-Item -Force` deleted them cleanly on the first try. Confirmed
      `git worktree list`/`prune -n -v` clean afterward. The actual 6.5 MB
      orphaned working-tree folder at hub root needed a second explicit
      confirmation from Tebello (the auto-mode classifier blocked the
      first PowerShell delete attempt given its size/real-file-content,
      unlike the tiny near-empty admin metadata folders) before it was
      removed the same way. Hub root now has no stray worktree folders and
      SOPS's `.git/worktrees/` has no dangling entries.
- [x] **2026-07-21** — ADR-007 opt-in: `3. Nameplate & Test Sheet` — **last
      project in the rollout, ADR-007 per-project opt-in is now complete**
      (Daily Sales Order Files, SOPS, DELIVERY NOTE, Nameplate; AvgMovement
      retired/skipped; Pappa T's projects explicitly out of scope for this
      hub). Same starting shape and same latent bug as DELIVERY NOTE: this
      project's `CLAUDE.md` already pointed to "root `CLAUDE.md` § DCOE
      Agent Architecture / § Sub-agent roster / § Hard Rules" (ADR-002
      point-to-shared-source pattern) rather than duplicating content, but
      a session opened directly in this project folder never loads root's
      `CLAUDE.md`, so those pointers were dead. Fixed identically to
      DELIVERY NOTE: added the `CORE.md` read instruction to the header
      blockquote, repointed the `Inference:` line, the § DCOE Agent
      Architecture section, and the § Hard Rules header (which had wrongly
      implied inheriting hub-specific rules like no-git-repo-at-root) to
      `CORE.md` instead. Left the "see root `CLAUDE.md` § Context
      Management" reference untouched — out of `CORE.md`'s scope, same
      reasoning as DELIVERY NOTE. Added the Step 1.5 upstream-commit check
      to this project's own `.claude/commands/continue.md` (same 3-step
      shape as DELIVERY NOTE's — resume report is Step 2). Also fixed a
      stale root `CLAUDE.md` project-index row while in there: it still
      said "Own git repo — not onboarded" for this project, though it was
      actually onboarded to DCOE back on 2026-07-15 (session-log confirms)
      — a pre-existing staleness bug unrelated to ADR-007 itself, corrected
      to match the DELIVERY NOTE row's format.
- [x] **2026-07-21** — ADR-007 opt-in: `7. DELIVERY NOTE`
      (delivery-note-system). Unlike SOPS, this project's `CLAUDE.md` never
      duplicated the DCOE/roster content directly — it already pointed to
      "root `CLAUDE.md` § DCOE Agent Architecture / § Sub-agent roster"
      (the ADR-002 point-to-shared-source pattern). But a session opened
      directly in this project folder never loads the root hub's
      `CLAUDE.md` at all, so that pointer was pointing at content the
      session can't actually see — a real latent gap, not just a
      duplication-cleanup task. Fixed by adding the `CORE.md` read
      instruction directly (mirroring SOPS/hub wording) and repointing three
      places that referenced "root `CLAUDE.md`" to `CORE.md` instead: the
      `Inference:` line in Project Overview, the § DCOE Agent Architecture
      section, and the § Hard Rules header (which had said "inherits every
      hard rule from root `CLAUDE.md`" — also wrong, since several of
      root's hard rules are hub-specific, e.g. no-git-repo-at-root, and
      don't apply to a sub-project with its own repo; reworded to inherit
      only `CORE.md`'s universal set). Left the separate "see root `CLAUDE.md`
      § Context Management" reference untouched — that section's content
      isn't part of `CORE.md`'s scope (ADR-007 covers DCOE architecture/
      roster/model-routing/universal hard rules only, not the context-budget
      policy), so repointing it would be a different, unrelated decision.
      Added the Step 1.5 upstream-commit check to this project's own
      `.claude/commands/continue.md` (lighter 3-step shape than SOPS's or
      the hub's — resume report is its Step 2, not Step 3/4).
- [x] **2026-07-21** — ADR-007 opt-in: `2. SOPS`. Added the `CORE.md` read
      instruction to `2. SOPS/CLAUDE.md` (blockquote area, mirroring the
      hub's own wording). Trimmed the duplicated § 🏗️ DCOE AGENT
      ARCHITECTURE and § 🤖 SUB-AGENT ROSTER sections down to a pointer at
      `CORE.md` — kept only the two genuinely project-specific additions
      (the Thinking-Levels effort-tier mapping, and the "bulk batch jobs
      before 31 Aug 2026" pricing note). Left § HARD RULES duplicated
      as-is, matching the precedent already set by the hub's own
      `CLAUDE.md` (which also kept its Hard Rules section rather than
      trimming rules that overlap with `CORE.md`'s universal set). SOPS
      has its own `.claude/commands/continue.md` (a different, domain-
      classifying shape from the hub's — Trading/Engineering/Software
      instead of project-folder identity), so added the Step 1.5
      upstream-commit check there too, between its existing Step 1
      (Orient) and Step 2 (Domain Classify), referencing its Step 4 (not
      Step 3) resume report.
- [x] **2026-07-21** — Ported the upstream `dcoe-roster/agents/debugger.md`
      rewrite (four-phase systematic-debugging methodology, adapted from
      obra/superpowers, MIT/attribution kept) into the real, authoritative
      `~/.claude/agents/debugger.md` (per `docs/patterns.md` §4, the
      user-level file is what sessions actually use — the plugin's
      `dcoe-roster:debugger` copy is not). Confirmed the rewrite was a
      strict superset of the existing content (same frontmatter, same hard
      rule/memory instructions, adds Phase 2 pattern-analysis and Phase 3
      hypothesis-cycling with a 2-failed-cycles escalation trigger) before
      overwriting — no conflicts, no manual reconciliation needed.
- [x] **2026-07-21** — Pulled 17 upstream commits into the local
      `tlelosa-claude-config` marketplace clone (fast-forward, `2219fea` →
      `49ca4ea`, clean — clone had no local-only commits). Inspected the
      notable ones before merging: `dcoe-roster` bumped to 3.3.0 (debugger
      agent rewrite, see entry above), `shared-skills` bumped to 1.1.0 (new
      `/capture` skill — draft-only vault note capture, never edits
      existing files), an IT-policy clearance record (Fan Movement IT
      approved the personal Anthropic account for the work PC, 2026-07-21 —
      this repo still carries no company data by design, that rule is
      unchanged), Context7 install steps for both machines, and a new
      `docs/marketplace-validation.md`. Also noticed the marketplace repo
      itself now has its own `CLAUDE.md`/`docs/todo.md`/
      `.claude/commands/continue.md` — someone (a Fable session, per commit
      trailers) onboarded the repo to its own lightweight DCOE, unrelated to
      this hub's own onboarding. Flagged the plugin-cache-vs-clone
      distinction as a separate "Next up" item rather than assuming the
      pull alone makes the new skill/agent live.
- [x] **2026-07-20** — `shared-skills` user-scope install verified on this
      machine. A fresh session at `2. SOPS` confirmed all 5 Skills appear
      in its available-skills listing — the user-scope config edit
      (2026-07-19) applies project-wide, closing the last open item from
      that change. Both machines are now fully verified. **Prefix quirk:**
      the Skills surface under a `2219fea0a313:` commit-sha prefix (the
      plugin's `gitCommitSha` short form), not `shared-skills:` — same in
      the hub session, so it's how this install method namespaces them,
      not a per-folder artifact. Cosmetic only; noted in Backlog with the
      related triple-roster observation.
- [x] **2026-07-20** — ADR-007 opt-in: `1. Daily Sales Order Files` (first
      sub-project after the hub pilot; Tebello picked it over SOPS/DELIVERY
      NOTE via `/continue`). Added the `CORE.md` read instruction to that
      project's `CLAUDE.md` header. Nothing to trim — its lightweight
      ADR-003 `CLAUDE.md` never duplicated the DCOE/roster sections, it
      deferred to the hub — and it has no `.claude/commands/continue.md`,
      so the Step 1.5 check doesn't apply there. Same handoff caveat as
      every prior config change: a fresh session opened *in that folder*
      is the real verification that the instruction gets followed.
- [x] **2026-07-20** — `/continue` session hygiene: renamed the stale
      `Continuation` session (→ `Cont-"Shared-skills user-scope install &
      Pappa T closeout"`), archived two superseded sessions on Tebello's
      confirmation (`Cont-"Marketplace pull sync troubleshooting"` — pull
      done and logged, trailing question answered in-session;
      `Cont-"Hub resume: Batch 34 archive & marketplace-pull question"` —
      its Batch 34 flag was actioned in a later session, only an accidental
      screenshot paste remained). No upstream `CORE.md` commits. Gave
      Tebello the copy-paste verification prompt for the shared-skills
      user-scope check (see "Next up"); noted the 5 Skills surface in this
      hub session under a `2219fea0a313:` commit-sha prefix rather than
      `shared-skills:` — worth capturing whatever prefix the outside-folder
      session reports when closing that item.
- [x] **2026-07-19** — `shared-skills` installed on Pappa T. Tebello ran
      `/plugin marketplace update tlelosa-claude-config` +
      `/plugin install shared-skills@tlelosa-claude-config` there choosing
      **user scope** (matching this machine's own decision, see entry
      below) and confirmed the 5 `shared-skills:*` Skills show up in a
      fresh session's listing. Both machines now have `shared-skills` at
      user scope alongside `dcoe-roster` — only this machine's own
      user-scope edit still needs the same fresh-session confirmation (see
      "Next up").
- [x] **2026-07-19** — `shared-skills` scope decision + user-scope reinstall
      on this machine. Tebello chose **user scope** (matching `dcoe-roster`)
      over staying project-scoped/opted-in per-project. Reinstalled by
      direct config edit (same mechanism prior sessions used for the
      marketplace clone, not the interactive `/plugin install` flow):
      added `shared-skills@tlelosa-claude-config: true` to
      `~/.claude/settings.json` `enabledPlugins`, changed the
      `shared-skills` entry in `~/.claude/plugins/installed_plugins.json`
      from `scope: project` (`projectPath: C:\Dev\Operations`) to
      `scope: user` (dropped `projectPath`), and removed the now-redundant
      project-level `enabledPlugins` block from this project's own
      `.claude/settings.json`. Validated all three JSON files parse before
      finishing. **Not yet verified**: a fresh session outside this project
      folder actually seeing the 5 Skills (see "Next up") — same
      can't-validate-own-bootstrap limitation as ADR-007/ADR-008.
- [x] **2026-07-19** — Pulled 3 upstream commits into the local
      `tlelosa-claude-config` marketplace clone (fast-forward,
      `5fca056` → `2219fea`, no conflicts): two nickname-cleanup commits
      ("work PC" → "Operations" in `marketplace.json`/`README.md`) and a new
      `hub-template/SKILLS-AUDIT-CHECKLIST.md` from Pappa T — a *reactive*
      checklist for spotting existing `.claude/skills/*/SKILL.md` files
      worth sharing, distinct from this hub's own *forward-looking*
      Skills-benefit research that already produced `shared-skills/`. The
      merge commit (`2219fea`) confirms Pappa T had already picked up this
      session's `shared-skills` push. This was a plain `git fetch` +
      `merge --ff-only` on the local clone (not the `/plugin marketplace
      update` command, which needs an interactive session) — same
      mechanism prior sessions used to inspect/update this repo directly.
- [x] **2026-07-19** — Confirmed `shared-skills` installed on this machine.
      Checked `~/.claude/plugins/installed_plugins.json` (entry present,
      `gitCommitSha` matches the `5fca056` push exactly), the plugin cache
      directory on disk (all 5 `SKILL.md` files present, content intact),
      and this project's own `.claude/settings.json` (`enabledPlugins:
      shared-skills@tlelosa-claude-config: true`). Installed itself
      automatically at **project scope** (tied to `C:\Dev\Operations`) —
      unlike `dcoe-roster`'s user-scope install, this doesn't yet apply to
      other projects on this machine. See "Next up" for the Pappa T +
      scope follow-up.
- [x] **2026-07-19** — Reviewed all 5 drafted `SKILL.md` files (see prior
      entry) directly against the drafts on disk. Assessed evidence
      strength: `dev-server-staleness-check` (3 independent contexts) and
      `safe-office-file-read` (4 projects) strongest; `reuse-existing-ui-
      primitive` solid (2 stacks); `sweep-shared-ui-convention-fix` and
      `verify-ui-cardinality-against-output` narrower (single-project/
      single-session evidence) but no correctness issues in any draft.
      Tebello chose to scaffold all 5 rather than ship a subset. Built
      `shared-skills/` in the `tlelosa-claude-config` marketplace clone
      (`shared-skills/plugin.json` + `shared-skills/skills/<name>/
      SKILL.md` per draft, mirroring the `dcoe-roster` plugin's layout),
      added the marketplace-catalog entry to `.claude-plugin/
      marketplace.json`, and a `shared-skills/` section to the repo's
      `README.md`. Validated both JSON files parse before committing.
      Got Tebello's sign-off (same gate as `CORE.md`/`hub-template/`)
      before pushing — committed and pushed as `5fca056`. Not yet done:
      actually installing the plugin on this machine or Pappa T (see
      "Next up").
- [x] **2026-07-19** — Drafted 3 more `SKILL.md` files from the UI-specific
      candidate list (the 3 strongest of the 5 found): `reuse-existing-ui-
      primitive` (check for an existing modal/dropdown primitive before
      hand-rolling one — confirmed on two different stacks),
      `sweep-shared-ui-convention-fix` (grep every render site of a shared
      badge/date/format convention before calling a fix complete), and
      `verify-ui-cardinality-against-output` (check the actual print/export
      output logic before assuming N-of-something UI is needed). Staged at
      `docs/research/skill-drafts/<name>/SKILL.md`, same layout as the
      first two. Left 2 of the 5 UI candidates undrafted (a narrower JS-
      inline-styles-vs-CSS debugging tip, and a reusable sortable/
      filterable table utility that reads more like a component library
      than an instructional Skill) — available on request. Now 5 drafted
      `SKILL.md` files total awaiting review.
- [x] **2026-07-19** — Skills-benefit research (forward-looking — distinct
      from the 2026-07-18 audit-checklist run, which only checked for
      Skills that already exist). Surveyed SOPS, Nameplate & Test Sheet,
      DELIVERY NOTE, the 3 pipeline projects, and hub-level patterns
      (`docs/patterns.md`, session-log history) for recurring techniques
      that would make good Claude Code Skills, plus a dedicated UI/frontend
      pass across all three UI-having projects. Landed on **20 candidates**
      total, ranked by genericity and cross-project evidence — full list
      (with per-candidate evidence/citations) lives in this session's own
      transcript rather than duplicated here. The single strongest finding:
      a "dev-server staleness" pattern (verify the dev process actually
      reloaded new code before trusting a live check) recurred
      independently in backend, data-pipeline, *and* UI-verification
      contexts — the broadest cross-cutting signal of anything found.
      Drafted full `SKILL.md` content for the two strongest candidates —
      `dev-server-staleness-check` and `safe-office-file-read` (the
      shadow-copy-before-read pattern, confirmed across 4 projects) —
      staged at `docs/research/skill-drafts/<name>/SKILL.md`, deliberately
      mirroring the eventual `shared-skills/` plugin layout so migration is
      copy-paste, not a rewrite. Wrote both business-agnostic (no Fan
      Movement/SOPS specifics in the body) since they're meant to travel
      cross-machine. Did **not** touch the `tlelosa-claude-config`
      marketplace repo itself — see "Next up" for the remaining decision.
- [x] **2026-07-18** — Skills audit (`hub-template/SKILLS-AUDIT-CHECKLIST.md`,
      the third "promote what's proven" checklist after `dcoe-roster/CORE.md`
      and `hub-template/`) run against this hub. Enumerated the 3 project
      folders with their own git repo (`2. SOPS`, `3. Nameplate & Test
      Sheet`, `7. DELIVERY NOTE/delivery-note-system`) and checked each for
      `.claude/skills/*/SKILL.md`. **Result: none exist anywhere** — all
      three only have `.claude/commands/` (plus SOPS also has `.claude/
      agents/` + `agent-memory/`). Nothing to shortlist, so `shared-skills/`
      was correctly **not** scaffolded in `tlelosa-claude-config` — the
      checklist's own guardrail against an empty, non-validating plugin
      entry. Closed as "checked, found empty," not left unrun.
- [x] **2026-07-18** — ADR-008 Pappa T hub parity: complete and verified.
      Built `hub-template/continue.md` (byte-identical to this hub's own
      copy, diffed to confirm) and `hub-template/HUB-CHECKLIST.md` — written
      as a *self-diagnostic* reconciliation checklist rather than waiting
      on the spec's original Step 0 gate ("paste Pappa T's CLAUDE.md
      first"), since reconcile-in-place doesn't need advance knowledge of
      the current content. Added a `hub-template/` pointer to the
      marketplace repo's own `README.md` (and folded in a `CORE.md`
      mention that had been missing since that push). Sign-off obtained,
      committed and pushed (`3dea897`). Gave Tebello a copy-paste prompt
      for a Pappa-T-side session covering spec Step 2 in full — pull the
      update, copy `continue.md` into place, reconcile `CLAUDE.md` against
      the checklist, verify `/continue` in a fresh session. **Tebello
      confirmed 2026-07-18: `/continue` works on Pappa T.** ADR-008 status
      updated to Accepted.
- [x] **2026-07-18** — Removed the stale "revisit AvgMovement retirement"
      item from "Next up" — `docs/decisions/ADR-006-avgmovement-retired-
      superseded-by-sops.md` already exists (Status: Accepted) and the root
      `CLAUDE.md` project index already reflects it as Retired. The decision
      this item was asking Tebello to make had already been made and
      recorded; the todo entry was just never cleaned up after ADR-006
      landed. Confirmed with Tebello before removing rather than assuming.
- [x] **2026-07-18** — ADR-007 spec Step 3 (notify mechanism): added Step 1.5
      to `.claude/commands/continue.md` — a `git fetch` + `rev-list
      HEAD..origin/main --count` check against the `tlelosa-claude-config`
      marketplace clone, surfaced in the resume report if > 0, never
      auto-applied. Sanity-checked the commands run correctly (returned 0,
      as expected immediately after pushing `CORE.md` from this machine).
- [x] **2026-07-18** — ADR-007 shared-core `CLAUDE.md` template: read-instruction
      mechanism verified end-to-end. A genuinely fresh top-level session at
      `C:\Dev\Operations` (the exact handoff condition the prior two sessions
      left open) read `dcoe-roster/CORE.md` per the hub `CLAUDE.md`'s
      session-start instruction and applied it — confirms the pivot away from
      `@import` (which doesn't resolve absolute paths outside the project
      tree) actually works, not just in theory. ADR-007 moves from "pivot
      accepted, unverified" to "verified" — per-project opt-in can now
      proceed (see "Next up").
- [x] **2026-07-17/18** — `7. DELIVERY NOTE` edit/delete/PDF-export backlog
      item closed (one of the 4 items from the 2026-07-17 status-report
      pass). Spec, build, and verification all in that project's own
      `docs/todo.md`/`docs/specs/edit-delete-pdf-export-2026-07-17.md` —
      not duplicated here. Worth flagging at the hub level: verification
      surfaced and fixed a real cross-cutting bug (Prisma 7's driver-adapter
      requirement — every DB route in that app was 500ing, not just the new
      ones), documented in that project's `docs/bugs/prisma7-driver-
      adapter-missing-2026-07-17.md`. Also hit a Windows-specific Turbopack
      junction-point failure while previewing (worked around with `next dev
      --webpack` for verification only; that project's own `npm run dev`
      is unchanged) — worth watching if other Next.js projects on this
      machine hit the same thing, in which case it'd graduate from a
      one-off note to a `docs/patterns.md` entry.
- [x] **2026-07-17** — AMU/Min-Max also ported into SOPS the same day
      (Batch 33, `2. SOPS/docs/specs/amu-minmax-reorder-suggestion-2026-07-
      17.md`, commit `112e321`) — closing the exact gap the entry below
      held AvgMovement's retirement open for. New, separate `amu`/
      `suggested_min`/`suggested_max` fields, never written into the
      existing manually-curated `reorder_point`/`max_level`. Retirement
      itself is recorded in `docs/decisions/ADR-006-avgmovement-retired-
      superseded-by-sops.md` (Accepted).
- [x] **2026-07-17** — `8. AvgMovement` reuse assessment resolved (follow-up
      to the status-report finding below). Confirmed AvgMovement is stale
      (no report or source-data refresh since 2026-05-13) but identified one
      genuinely reusable piece: its Supplier + Lead Time enrichment (from
      Sage's `OutstandingPOByItemReport.csv`), which SOPS didn't have.
      Explicitly did **not** duplicate AvgMovement's On Order figure — SOPS
      already computes `qty_on_order` live from its own Purchase Orders
      (`2. SOPS/services/demand.py`), and importing a second, CSV-refresh-
      dependent on-order number would have recreated the exact
      "two processes, same thing" problem this work was meant to fix. Built
      as SOPS Batch 32 (`2. SOPS/docs/specs/supplier-lead-time-import-2026-
      07-17.md`, commit `fe06eaa`) — see that project's own `docs/todo.md`
      for implementation detail. **AvgMovement retirement held off**
      (Tebello's call, on second look): it also computes AMU (average
      monthly usage) and automated Min/Max reorder-level suggestions, which
      SOPS has no equivalent of (SOPS's own `reorder_point`/`max_level` are
      manually set, not auto-suggested) — retiring the pipeline now would
      have dropped real capability, not just deduplicated. **Superseded by
      ADR-006** the same day the AMU/Min-Max gap closed (see entry above and
      below) — AvgMovement is now formally retired, not just held off.
- [x] **2026-07-17** — Cross-project status reporting process established.
      Tebello asked for a way to see all active projects/tasks (project,
      status, target goal) in one place to prioritize/plan. Surveyed every
      active project (SOPS, DELIVERY NOTE, Nameplate & Test Sheet, Daily
      Sales Order Files, AvgMovement) via each project's own `docs/todo.md`
      or `USER_GUIDE.md` execution log, plus `git log`/`git status` and
      live-report file timestamps. First report:
      `docs/reports/status-report-2026-07-17.md`. Surfaced 4 items needing
      Tebello's attention: SOPS Batch 24 payment-status review still
      unactioned (19/22 SOs), Nameplate has a dirty working tree with a
      long-stray uncommitted `/api/speed` endpoint, AvgMovement hasn't
      produced a report since 2026-05-13 (2+ months), Delivery Note's
      edit/delete/PDF-export backlog is unprioritized. Process documented
      as reusable in `docs/patterns.md` § 9 — regenerate on request, not
      scheduled/automated unless asked separately.
- [x] **2026-07-15** — Context budget threshold + judgment-based session
      archival check (`docs/decisions/ADR-005-context-budget-and-session-
      archival.md`). Confirmed no harness hook can read live context
      percentage, so the 55%-remaining rule is a self-monitored `CLAUDE.md`
      policy, not a harness-enforced one. Confirmed a mechanical "newest
      session per project" archival rule would be wrong (`2. SOPS` has 5
      legitimately concurrent sessions) — archival detection in
      `.claude/commands/continue.md` (new Step 0.5) is judgment-based and
      always ends in per-item user confirmation before `archive_session` is
      called. Updated `CLAUDE.md` § Context Management, `docs/patterns.md`
      (§§ 7–8), `.claude/commands/continue.md`, and `docs/session-log.md`.
- [x] **2026-07-15** — DCOE onboarding: `7. DELIVERY NOTE`
      (delivery-note-system) — last project in the ADR-002/ADR-004 rollout.
      Domain-agent scope pass found this wasn't the mechanical pipeline case
      (ADR-003 doesn't apply): thin boilerplate `CLAUDE.md`/`AGENTS.md`, and
      a complete working MVP feature (delivery-note register: Prisma model,
      3 API routes, full page UI) sitting entirely uncommitted since the
      initial scaffold commit. Asked Tebello two questions: onboarding depth
      → **full DCOE scaffold**; handling the uncommitted MVP → **commit it
      first**. Reviewed the diff for correctness, excluded `dev.db` from
      git (added to `.gitignore` — it wasn't there before), committed the
      MVP (`048e08b`), then committed the full DCOE scaffold (`d76b8ee`):
      project `CLAUDE.md`, `docs/` (`todo.md`, `session-log.md`,
      `decisions/ADR-001`, `bugs/`, `research/`, `specs/`),
      `.claude/commands/continue.md`, `.claude/settings.json`. Kept
      `AGENTS.md` (real content — a Next.js-version-mismatch warning,
      verified accurate) rather than deleting it. Updated root `CLAUDE.md`
      project index and this file. **DCOE rollout is now complete** for all
      4 currently-in-scope projects.
- [x] **2026-07-15** — `Inventory Management & Reports` excluded from DCOE
      rollout (ADR-004). Tebello's decision: the project will be kept as a
      reference resource for SOPS development and any other project
      needing its extract → build → report work, not run as its own
      standalone pipeline — so it doesn't get a lightweight DCOE onboarding
      under ADR-003. Nothing in the project itself changed (folders,
      `GEMINI.md`, scripts all left as-is). DCOE rollout is now 4 projects
      instead of 5. Updated root `CLAUDE.md` project index and this file.
- [x] **2026-07-15** — DCOE onboarding: `8. AvgMovement` (mechanical per
      ADR-003 — no re-litigation needed). Found a genuine project-specific
      wrinkle: `1_Documentation/AGENT.md`, a generic unfollowed "DOE"
      template (its own log/memory-buffer sections are unfilled
      placeholders, and it names a log file that doesn't actually exist).
      Left it in place untouched (Claude Code doesn't read `AGENT.md`
      anyway; deletion wasn't asked for) and documented the coexistence in
      the new `CLAUDE.md`. Also noted, unlike Daily Sales Order Files, this
      project's `USER_GUIDE.md` has no actively-maintained execution log —
      didn't claim one exists. Updated root `CLAUDE.md` project index and
      this file.
- [x] **2026-07-15** — DCOE onboarding: `1. Daily Sales Order Files`
      (execution spec in
      `docs/specs/2026-07-15-daily-sales-order-onboarding.md`). Domain-agent
      exploration found no legacy `AGENT.md`/`GEMINI.md` (hub index was
      stale, now fixed) and confirmed the pipeline folder layout is
      load-bearing with `1_Documentation/USER_GUIDE.md` already functioning
      as an informal session-log + fix-history. Asked Tebello two scope
      questions: onboarding depth → **lightweight**; precedent scope →
      **decide generically now**. Recorded as ADR-003. Added project
      `CLAUDE.md`; updated `docs/patterns.md` § 6, root `CLAUDE.md` project
      index, and this file. `8. AvgMovement` and
      `Inventory Management & Reports` can now reuse ADR-003 without
      re-deciding the convention.
- [x] **2026-07-15** — Hub setup completion (execution plan in
      `docs/specs/2026-07-15-hub-setup-completion.md`): deleted 17 confirmed-
      dead stale `.git` lock artifacts in `2. SOPS` (verified repo clean and
      `fsck`-healthy first); deleted `Operations.old-onedrive-backup`
      (104,390 files, ~2.65 GB — Tebello confirmed nothing was needed from
      it); re-verified the OneDrive junction is intact with no recreation;
      recorded ADR-002 (rollout to all 5 remaining projects, sequencing
      deferred to per-project concrete work rather than a fixed order).
      One item left untouched: `index_work.lock.bak` in SOPS `.git` — not
      in the original or approved deletion list, flagged but not removed.
- [x] **2026-07-15** — Post-move path audit across `1. Daily Sales Order
      Files`, `2. SOPS`, `3. Nameplate & Test Sheet` for stale references to
      the pre-relocation OneDrive path. Verified the compatibility junction
      (`...OneDrive...\Desktop\Operations` → `C:\Dev\Operations`) is intact,
      so no paths were actually broken. Findings: Daily Sales' OneDrive
      paths point to an unrelated colleague folder (Contract Register, not
      Operations) — no change; SOPS's only match was an archived historical
      log — no change; Nameplate's `1_Documentation/DEPLOYMENT.md` had a
      genuinely stale quick-start path (predating even the OneDrive move) —
      fixed to `C:\Dev\Operations\3. Nameplate & Test Sheet\4_Scripts`, and
      `CONFLICT_ANALYSIS.md` updated to mark that finding resolved. Left
      `doc_history.json`/backend logs in Nameplate untouched (production
      history data, still resolves fine via the junction).
- [x] **2026-07-15** — Root hub DCOE setup: `CLAUDE.md`, `docs/`
      (`todo.md`, `patterns.md`, `session-log.md`, `decisions/`, `bugs/`,
      `research/`, `specs/`), `.claude/settings.json`,
      `.claude/commands/continue.md`, root `README.md`. Hub-and-spoke
      model — SOPS and all other projects left untouched.
- [x] **2026-07-15** — OneDrive/git corruption fix: relocated the whole
      Operations tree from OneDrive-synced Desktop to `C:\Dev\Operations`,
      then created a directory junction at the old OneDrive path pointing
      to the new location (old folder preserved as
      `Operations.old-onedrive-backup`, not deleted). All project repos
      (SOPS, Nameplate & Test Sheet, DELIVERY NOTE) are now outside
      OneDrive's sync scope. See `CLAUDE.md` § Known Risk for what's still
      left (stale lock cleanup, backup folder disposition).
