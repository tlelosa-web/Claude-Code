# todo.md — Claude-Code hub (cross-project task queue)

Hub-level tasks only — work that spans projects, or new work started at
root. Each project's own `docs/todo.md` (in its own repo) is authoritative
for anything scoped inside that project; this file doesn't duplicate that
detail, only tracks it at a glance and links out.

Per DCOE: update after every completed task; one task = one commit.

## In progress

- [ ] **O-P-C machine consolidation** — Operations and Pappa T subtree-
      merged into this repo (`Pappa T/`, `Operations/`, both with full
      history preserved for their git sub-repos). Old `Claude-Code` Desktop
      folder removed 2026-08-03 (redundant clone, nothing untracked, fully
      superseded by O-P-C's already-pushed history). `Operations` and
      `Pappa T` Desktop folders deliberately **kept, not superseded** —
      both hold live gitignored data with no other copy (SOPS's production
      `instance/sops.db`, delivery-note-system's `.env`/`dev.db`, Pappa T's
      `.env` files/`credentials.json`/`career.db`/`outreach.db`/etc.) that
      the git-based subtree-merges never captured, since that only pulls
      committed history. See `docs/session-log.md`, 2026-08-03 entry. Not
      a task to revisit unless Tebello decides to deliberately migrate that
      live runtime state too (and repoint whatever scripts/services use
      those paths) — no urgency stated.
      The "Next up" items' machine flags were re-checked 2026-08-03 — see
      that section's own note.

## Next up (priority order, set 2026-07-28; specs added 2026-07-29; machine
flags re-checked 2026-08-03 after the O-P-C consolidation — see note below)

> **2026-08-03 re-flag:** the old ⚠️ "Pappa T only"/"Operations only" flags
> meant "unreachable from a cloud session on a different machine." That's
> gone — Operations and Pappa T are now physically on this same machine.
> But O-P-C's `Operations/`/`Pappa T/` folders are a **historical
> consolidation snapshot** (git history only), not the live working copy —
> per `docs/session-log.md`'s 2026-08-03 "old Desktop folders" entry, the
> live databases/secrets/generated output only exist in the original
> `Desktop/Operations/`/`Desktop/Pappa T/` folders. So every item below now
> gets a 📍 flag instead: reachable from this machine, but work must
> happen in the **live** Desktop copy, not O-P-C's snapshot, or the fix
> won't reach the actual running project and O-P-C will need re-merging
> afterward to pick it up.

1. [ ] **TebelloReborn: Indeed site adapter** — **Phases A–D built 2026-08-07;
      Phase E's offline half built 2026-08-08 (676 tests). Phase E's live half is
      paused overnight at Tebello's direction after Cloudflare bot-challenged the
      site.** 📍 Live `Desktop/Pappa T/TebelloReborn/`, vault `1ba6521`, pushed.

      **Resume here:** step 140 in that project's `docs/todo.md` — the questions
      step's selectors and the review step's URL segment are still unknown,
      `inspect_apply_flow()` is unwritten, and the adapter is deliberately **not
      registered** in `eligibility.ADAPTERS` so nothing can reach a prep run that
      could only fail. Everything else in Phase E is done: `questions.py`,
      `drafting.py`, the `IndeedAdapter` shell, `prep.py` + the `prep-submission`
      CLI, and `tools/indeed_login_setup.py`. A signed-in Chrome profile now
      exists at `.session/chrome-profile` (gitignored), so the sign-in does not
      need repeating.

      **Two findings that change the remaining work**, full detail in that
      project's spec §2026-08-08 recon and in `knowledge/tebelloreborn.md`:
      **Indeed refuses an automated sign-in** — resolved by moving the login out
      of automation into ordinary Chrome against a dedicated profile, never by
      defeating the detection, which stays a hard line. And **Cloudflare
      bot-challenges after roughly four automated runs in fifteen minutes**, so
      pacing is now a design constraint — and that is evidence about **Phase G**,
      not only Phase E, since the same detection sits in front of the submit path
      where hitting it costs a real application to a real employer mid-flight.
      Worth a deliberate answer before Phase G rather than discovering it there.

      `TebelloReborn/docs/specs/indeed-submit-adapter.md` §Amendment carries the
      phase-level Build Queue and is authoritative; that project's own
      `docs/todo.md` and `docs/session-log.md` carry the detail. This entry is a
      pointer, per hub-and-spoke.

      **State as of vault `1ba6521` (committed and pushed, verified 2026-08-08
      `0 ahead / 0 behind`):** 676 tests passing, zero regressions across every
      phase (344 → 399 → 456 → 485 → 538 → 676). The adapter registry is still
      empty, so `career.db`'s 6 `approved` Indeed vacancies all route to manual
      today — and will keep doing so until step 140 closes.

      - **Phase D** (Phase 21, steps 128–130) — `src/submission/browser.py`:
        CAPTCHA detection (A7), the combined navigation-state check (A17),
        continuous session-expiry detection (A18), and the plain-text step log
        (C3). Offline throughout and **still no `playwright` dependency**, which
        is only possible because the module separates judgment from observation:
        the adapter observes the page, `browser.py` judges what was observed and
        never queries a DOM. 95% covered — the 6 uncovered lines are the
        playwright body A19 already exempts.

      - **ADR-004** (`docs/decisions/ADR-004-schema-migration-ledger.md`, accepted
        + built, Phase 18 steps 107–117) closed the shared-`user_version` question
        this entry previously listed as a blocker: the counter is replaced by a
        per-module ledger table. It was genuinely blocking, for a reason the old
        entry didn't have — the `profile` fix works by asking `PRAGMA table_info`
        whether a column exists, so it only understands `ADD COLUMN`, and Phase B's
        central migration is a **table rebuild** (SQLite can't alter a CHECK in
        place). No column-existence check could have gated it.
      - **Phase A** (Phase 17, steps 103–104) — `email`/`phone` on
        `CandidateProfile`, migrations 5 and 6, real values from
        `data/Tebello_Lelosa_Master_CV_2026.md` with a CV-drift guard test.
        `career.db` backed up beforehand via the sqlite3 backup API,
        integrity-checked and row-count-verified.
      - **Phase B** (Phase 19, steps 118–122) — `submission_preps` /
        `screening_questions`, the `pending_review` outcome, the widened
        `submissions.outcome` CHECK with its rebuild migration and drift guard,
        and `submission_prep_ready()`.
      - **Phase C** (Phase 20, steps 123–127) — the prep-state gate wired into
        `pipeline.py`, `pending_review` reporting, and the `--all` auto-submit
        refusal.

      **Already confirmed with Tebello, no longer open:** the ToS/account-risk
      exposure (explicit, separate acknowledgement); Indeed's own apply form as
      the only platform; `playwright` as a runtime dependency; and — before Phase C
      was written — that `submit --all` refuses auto-submit, so the 6 approved
      vacancies go out as six deliberate single commands.

      **Standing constraints from the live recon**, unchanged: the apply flow is
      reCAPTCHA-protected (hard rule — detect and abort, never solve or defeat it),
      and employer screening questions are real, per-posting and often open-ended
      free text, so answers are LLM-drafted but held for Tebello's explicit
      per-question approval before any submission.

      Hub spec `docs/specs/2026-08-04-tebelloreborn-playwright-auto-submit.md`
      stays superseded by the project-side specs above — it scoped the build to
      LinkedIn Easy Apply, a platform this project formally dropped on
      2026-08-01, three days before that spec was written.

      **Awaiting Tebello, neither blocking:** two byte-identical `career.db`
      backups, untouched because it's real career data — pick one and the other
      gets deleted.
2. [ ] **SOPS: give the go-ahead to run the AvgMovement migration against
      `instance/sops.db`** — Supplier/Lead-Time + AMU/Min-Max logic ported
      and fully tested (Batch 32/33, commits `fe06eaa`/`112e321`), held for
      Tebello per SOPS's standing schema-change convention. This is the
      blocking step before `8. AvgMovement` (already Retired in the
      Operations hub project index) can be decommissioned. 📍 **Must** run
      against `Desktop/Operations/2. SOPS/instance/sops.db` — O-P-C's
      `Operations/2. SOPS/` has no `instance/` at all (gitignored, never
      merged), so running this from O-P-C would either fail outright or
      silently create a fresh empty database instead of migrating the real
      one. Spec (ready, but gated — do not run without explicit
      in-session go-ahead): `docs/specs/2026-07-29-sops-avgmovement-migration.md`.
      Detail: `2. SOPS/docs/todo.md`, `knowledge/sops.md`.

### From the 2026-08-08 systems check (config repo + this hub)

Full plan and per-branch verdicts live in `tlelosa-claude-config/docs/specs/`
(`2026-08-08-system-maintenance-plan.md`, `2026-08-08-branch-triage-verdicts.md`).
Phases 1-6 are done; what remains that is *this hub's* to do:

- [ ] **Phase 7a — root `.gitignore`.** This repo has none, and build
      artifacts are tracked: a 31 MB `node-v24.10.0-x64.msi`, a 2 MB
      `backend.log.1`, and ~6 MB of generated PNGs, in a 67 MB repo. Add a
      `.gitignore` and untrack going forward. **Do not rewrite history** —
      that breaks every existing clone on both machines plus any cloud
      session, for a cosmetic size win. Untracking is enough.
- [ ] **Phase 7b — resolve the company-data rule contradiction.** This
      hub's hard rule 4 says "no company or project data beyond what's
      already public in the source project's own repo," but `Operations/`
      holds `CustomerInvoicesReport.csv`,
      `CustomerSalesOrdersByCustomer.csv`, `Contract register 2025.xlsx`
      and the 07.2026 sales order report. The hub-and-spoke design intends
      sub-projects to live here, so the rule and the layout contradict each
      other — decide which is meant and reword the loser. All five repos are
      confirmed **private**, so this is rule clarity, not exposure. One
      related question worth answering explicitly: cloud sessions clone this
      entire vault, company data included, into an Anthropic container. The
      IT clearance on record covers a personal Anthropic account on the work
      PC; whether it covers that is a separate question, and the same class
      as the open codex-gate/OpenAI-egress item. **Owner decision.**
- [ ] **Adopt the Phase 6 branch checks in this hub's own
      `.claude/commands/` copies.** `hub-template/continue.md` gained Step
      1.8 (unmerged-branch check) and `hub-template/session-end.md` gained
      Step 1.5 ("can this session's work be found?") on 2026-08-08. These
      instances are separate files in a separate repo and do not have them.
      Run `hub-template/HUB-CHECKLIST.md` against this vault — it now names
      both step headings specifically, because a copy made before that date
      looks complete and passes every other item.
- [ ] **Decide on `/overwatch`** (held open 2026-08-08). Built 2026-08-05 as
      Gap 1 of `docs/specs/2026-08-05-command-center.md`, still unmerged on
      `claude/continuation-utn4f5`. Gaps 2 and 3 of that spec landed in the
      config repo today, so this is the last piece of a three-part initiative
      that is otherwise complete. Still wanted, or does the spec land as
      historical? The branch is held undeleted until this is answered.

## Parked (committed work, deliberately deferred)

Distinct from "Backlog / ideas" below: these are real, agreed items with
research or specs already done. They are not queued for now, and they are not
abandoned either — no work is lost by leaving them here.

- [ ] **NamePlateTool: add a real automated test suite** — parked 2026-08-06 at
      Tebello's direction, no reason given and none needed; it was never urgent
      (`tests/` is ad-hoc manual-check scripts only, and the tool works).
      Everything needed to restart is already in place: 📍 build in the live
      `Desktop/Operations/3. Nameplate & Test Sheet/`, then push to its own
      GitHub remote — that remote, not O-P-C, is the source of truth O-P-C's
      copy gets re-merged from. Spec (ready, starter scope — confirm before
      building; also carries a 2026-08-03 Codex second-opinion advisory note):
      `docs/specs/2026-07-29-nameplatetool-test-suite.md`.

## Backlog / ideas (not committed)

- [ ] **Fold `rev-parse --show-toplevel` back down into this hub's Step 1.9** — the
      reverse direction of PR #14. This hub's Step 1.9 hardcodes the two repo layouts
      it knows (`Desktop/Pappa T/` is one repo covering all its sub-projects;
      Operations' `2. SOPS` and `3. Nameplate` are separate repos). The template
      couldn't name those, so it resolves roots with
      `git -C "<project path>" rev-parse --show-toplevel` instead — which is strictly
      better, since a hub has both shapes at once and a wrong assumption silently
      reads the clock of a path that isn't a repo root. Keep the named examples as
      illustration, but resolve rather than assume. Small, local, no gate.
- [ ] **Widen `/codex-review`'s path guard to `docs/decisions/`** — the skill is
      hard-scoped to `docs/specs/` and refuses ADRs outright. TebelloReborn hit
      this on 2026-08-07 reviewing `ADR-004-schema-migration-ledger.md` and worked
      around it with a direct `codex exec` carrying the identical review
      instruction and payload discipline — so the gate was satisfied in substance,
      by hand. **Second time an ADR has wanted the gate**, which is the argument
      for changing it rather than working around it a third time. Note the guard
      matches CORE.md Universal Hard Rule 9's literal wording ("every spec in
      `docs/specs/`"), so widening the skill without widening that rule leaves the
      two disagreeing — this is a marketplace change (`tlelosa-claude-config`,
      codex-gate plugin + `dcoe-roster/CORE.md`), upstream-first per ADR-008, not
      a local edit.
- [ ] **Add `*.db-shm` / `*.db-wal` to the Pappa T vault `.gitignore`** — the
      2026-08-06 backup run opens each SQLite DB read-only, and opening a
      WAL-mode database creates its `-shm`/`-wal` sidecars. Two now show as
      untracked in the Pappa T repo (`ai-outreach-agency/outreach.db-shm`,
      `-wal`). Harmless and regenerable, but they will reappear after every
      backup run and clutter `git status`. TebelloReborn's own `.gitignore`
      already covers them; the vault-level one does not.
- [ ] **Decide whether backup failures should alert** — the daily task (below)
      writes failures to `~/Backups/backup-runtime.log` and sets a non-zero
      `LastTaskResult`, but nothing tells anyone. A silent failure would look
      identical to success until someone checks. Options range from doing
      nothing (check `Get-ScheduledTaskInfo` occasionally) to a Task Scheduler
      on-failure action or a notification. Not urgent — the backup itself is
      running and verified — but worth a deliberate answer rather than drift.

## Done

- [x] **2026-08-08** — Marketplace clone moved back onto `main`. The clone
      `/continue` Step 1.5 actually reads,
      `~/.claude/plugins/marketplaces/tlelosa-claude-config`, was left on
      `hub-template-continue-reconcile` after the PR #14 work; checked out `main`
      and fast-forwarded `9f85d40..5660e1d` (2 commits), which is PR #14's own
      merge landing in the clone — `hub-template/continue.md` and
      `hub-template/HUB-CHECKLIST.md`.
      **Why this stayed open after being reported fixed once:** there are *two*
      clones of this repo on this machine, and that fix was applied to the wrong
      one. `~/Downloads/tlelosa-claude-config` (a stray clone, already noted in
      `knowledge/pappa-t.md`) is on `main` and always was; the marketplace clone
      under `~/.claude/plugins/` is the one that governs. Always path-qualify with
      `git -C` when touching this repo.

- [x] **2026-08-08** — Folded this hub's `/continue` improvements up into
      `hub-template/` per ADR-008 — **merged** as PR #14
      (https://github.com/tlelosa-web/tlelosa-claude-config/pull/14, merge commit
      `5660e1d`, branch deleted). Step 0.5 category B, Step 1.75, Step 1.9,
      Step 2.5, and Step 3's `Hub state:` + ⚠️ machine-bound fields.
      **Step 1.9 could not be backported alone** — it names Step 1.75 and depends
      on running after it, and the template had no Step 1.75; checking why turned
      up that the template was *four* improvements behind, not one.
      **ADR-008 predicted drift from hubs not taking template updates; the first
      real reconcile showed it runs the other way too**, and nothing detected it
      because `HUB-CHECKLIST.md` only ever handled a *missing* `continue.md` and
      never diffed an existing one. Fixed in the same PR, along with a new item
      for the vault-specific hooks Steps 1.75/1.9/2.5 are inert without.
      **Three vault-specific leaks were already in the template**, against its own
      verbatim-copy contract: the `2. SOPS` parallel-sessions example, a SOPS
      session-title example, and — the one that actively misleads — Step 3's
      "surface the OneDrive/git item from `CLAUDE.md`", one hub's risk hardcoded
      as every hub's, so a fresh vault would be told to report a risk it doesn't
      have. Being *declared* vault-agnostic is not evidence that a file is.
      **The template's version of Step 1.9 came out better than this hub's** — it
      resolves repo roots with `rev-parse --show-toplevel` instead of hardcoding
      layouts, which is now a backlog item to fold back down.
      Landing upstream does **not** update any hub's installed copy (file-copy
      distribution, ADR-008); this hub already has all five steps. See
      `knowledge/tlelosa-claude-config.md`.
- [x] **2026-08-08** — Installed the cross-repo staleness check into `/continue`
      as **Step 1.9**, closing a gap that had been *written down three times and
      never built*. `knowledge/hub-process.md` carried the finding since
      2026-08-07 and the hub still drifted; the 2026-08-07 Phase D session ran
      the check by hand and recorded that the command file had never actually
      been touched. **The reusable part is why that kept happening:**
      `knowledge/` records why something is true, but only the command file
      changes what a session executes — and a finding filed there is read by a
      session that goes looking for it, which is precisely not the session
      confidently reporting stale state. Filing the lesson feels enough like
      closure to hide that the step is missing.
      **The prescription was wrong on placement and needed correcting on
      contact:** the entry said "Step 1, as part of orienting," but Step 1.75 is
      what pulls `origin/main`, so a check at Step 1 compares the project's clock
      against a possibly stale local hub `HEAD` and can report drift *backwards*.
      It went in after the sync check instead, with the ordering dependency
      stated in the step itself. Step 1 gained a paragraph making its two reads
      an unverified claim rather than state.
      Step 1.9 requires the result in the Step 3 report **even when it passes** —
      a silent pass and a check that never ran are indistinguishable, which is
      exactly how three recurrences went unnoticed — and requires the live repo's
      `status --porcelain`, since the hub can be right about what was committed
      and still wrong about what exists. It also names the repo roots explicitly,
      because they aren't the project folders: `Desktop/Pappa T/` is one repo
      covering all its sub-projects, while Operations' `2. SOPS` and
      `3. Nameplate` are separate repos. Finding drift is explicitly *not* made
      this session's task to fix — surface and let Tebello pick.
      Deliberately **not** backported upstream this session: the ADR-008 fold-up
      is blocked on scope, not permission — see the new backlog item. No project
      code touched. See `knowledge/hub-process.md`.
- [x] **2026-08-07** — TebelloReborn: built Indeed adapter **Phase D**
      (`src/submission/browser.py`, Phase 21 steps 128–130, 3 commits in the Pappa T
      vault, **485 → 538 tests, zero regressions**). CAPTCHA detection, the combined
      navigation-state check, continuous session-expiry detection, and the step log.
      **Offline throughout, and still no `playwright` dependency** — which was the
      real constraint, since Phase D is the module that will eventually import it and
      it isn't installed on this machine. Both hold only if the module's *decisions*
      never need a browser, so `browser.py` separates judgment from observation: the
      adapter observes the page (which iframes exist, whether each is visible, which
      landmarks it found), `browser.py` judges what was observed and never queries a
      DOM. That let all twelve CAPTCHA states be pinned by unit test now instead of
      waiting for Phase E's live recon. 95% covered; the 6 uncovered lines are the
      playwright body A19 already exempts.
      **The never-abort tests matter more than the abort ones here** — recon
      established that a "protected by reCAPTCHA" notice and a zero-sized anchor
      frame appear on a *healthy* run, so a detector tripping on either aborts 100%
      of runs; seven tests exist to keep that from being reintroduced.
      **Three places the spec left room, decided rather than defaulted:** landmark
      selectors were *not* invented (A17 needs a URL segment plus a landmark, but
      recon only verified the segments — so `WizardStep` stores landmark names for
      Phase E to map, and `WIZARD_STEPS` omits the review step entirely because the
      walkthrough never reached it); A7 rule 5 was extended to
      `recaptcha/enterprise/anchor` since rule 1 already pairs both bframe paths and
      the escalation reasoning is identical; and `INDEED_AUTH_MARKERS` was cut down
      rather than filled out, because recon ran signed in and never saw an expiry, so
      a broad `/auth` marker would tell Tebello to re-run a login setup that was fine.
      Two orderings pinned by their own tests, same silent-failure class as Phase C's.
      Recorded as a known deviation rather than quietly accepted: `browser.py` is 397
      lines against that project's documented 300-line standard (not split — the spec
      names one module, and `db.py` already sits at 370). Nothing reached the wire and
      nothing was submitted. See `knowledge/tebelloreborn.md`.
- [x] **2026-08-07** — Caught the hub up to Phases B and C, which landed after its
      last write — **and found why writing the lesson down hadn't stopped it.** The
      hub's previous close-out (`25b0173`, 11:11) was 5h19m behind the vault
      (`63687c5`, 16:30) and asserted three things that were false by the time this
      session read them: "Phases B–H not started" (B and C built), "Phase B is
      blocked on an ADR" (ADR-004 written, accepted, built), and "3 unpushed commits
      in the vault" (pushed). Third occurrence of this drift, and the second one
      *after* `knowledge/hub-process.md` gained an entry specifically about it.
      **The recurrence is structural, not a discipline failure**, which is the new
      finding: `/session-end` runs the staleness check at the moment the hub is last
      correct, so it cannot see work landing afterwards — and work landing
      afterwards is the normal case, since the reason one session is ending is
      usually that another is still going. The check belongs in `/continue`'s orient
      step, because the *reading* session is the one that can be wrong. Recorded as
      a new `hub-process.md` entry rather than as an edit to the existing one, which
      remains correct about the mechanism.
      Item #1 rewritten from "blocked" to a build-ready pointer at Phase D, trimmed
      to hub-and-spoke depth (net −27 lines): ADR-004's decision, the three built
      phases, and the constraints that still bind, with the resolved gates stated as
      resolved rather than re-litigated. `knowledge/tebelloreborn.md` gained a new
      entry; the Phase A entry below it was marked `superseded in part` rather than
      edited — its *diagnosis* of the `user_version` bug is still the clearest
      statement of it and only its forecast expired. Also surfaced two things
      waiting on Tebello that neither project nor hub was tracking: the duplicate
      byte-identical `career.db` backups, and `/codex-review`'s `docs/specs/`-only
      path guard refusing ADRs for the second time (now a backlog item, and a
      marketplace change rather than a local one — the guard matches CORE.md Hard
      Rule 9's literal wording, so widening one without the other leaves them
      disagreeing). No project code touched; the vault was read-only this session.
- [x] **2026-08-07** — TebelloReborn: folded Codex's review into
      `docs/specs/indeed-submit-adapter.md`, closing that project's Hard Rule 13 gate
      before any Executor is dispatched (Pappa T vault `3267cb5`, pushed). 22 accepted
      changes, 6 clarifications, 4 declined. **No code written** — this was the spec
      gate, not the build. The four gaps the queue named are resolved concretely:
      `can_handle()` is now a pure offline URL predicate with all live work moved to a
      non-Protocol `inspect_apply_flow()`; question drift is a sha256 fingerprint
      compared as a set, aborting in both directions; CAPTCHA detection names five
      abort states **and** three never-abort states (the "protected by reCAPTCHA"
      notice is on every healthy run — a detector that trips on it aborts 100% of
      runs); and `prep_failed` was **deleted rather than defined**, since prep attempts
      no submission and its failures don't belong in an attempt log — they went to a
      new `submission_preps` table whose states also fixed a separate bug, inferring
      "prep never ran" from zero question rows.
      **Four findings came from reading the code and the live `career.db`, not from
      Codex, and two would have failed at runtime:** the spec's "no DB migration for
      `email`/`phone`, same precedent as `VALID_STATUSES`" was a false analogy —
      `candidate_profile` is a real table with named columns, so those are *new
      columns* and `upsert_profile()` would have raised `no such column: email` (now
      migrations 5/6, the project's first since Hard Rule 6 was written); and
      `submissions.outcome`'s CHECK sits inside a `CREATE TABLE IF NOT EXISTS`, so the
      DDL edit works only while the table doesn't exist — verified it doesn't yet
      (live DB at `user_version = 4`, no `submissions` table), meaning the window is
      open now and closes the first time anyone runs `submit`. Also: `prep-submission`
      needs network twice (`claude -p` is a local subprocess, not an offline one), and
      `generation_log` has no path column so the adapter must reconstruct
      `pdf_export`'s naming via a shared helper. See `knowledge/tebelloreborn.md`.
- [x] **2026-08-07** — Queue accuracy pass: item #1 corrected from "blocked" to
      "in progress", then reconciled across both files. A separate terminal
      session had started the Indeed adapter build and answered most of the
      gating questions directly (Indeed's native apply form only, `playwright`
      accepted as a runtime dependency, `email`/`phone` to be added to
      `CandidateProfile`, selectors from live DOM recon) — none of which had
      reached either queue, so both still described the work as not-started.
      Reconciled in the **opposite** direction to the usual hub-and-spoke rule:
      the project file is authoritative, but it was the *stale* one, so it got
      brought up to date first (Pappa T vault `93f8e5b`) and this hub's entry was
      then trimmed from ~40 duplicated lines to a pointer (`6e3702f`, net −23).
      Authority over the detail stayed with the project; only the content moved.
      **Deliberately kept in both files:** the ToS/account-risk acknowledgement is
      still not on record, and the build having started does not retire it —
      signing in for read-only DOM inspection is not that acknowledgement. Also
      recorded that `TebelloReborn/docs/specs/submission-core.md` §Open Items 1
      and 3 now read as open despite being answered; amending that spec is the
      building session's call, not this one's. Decisions were observed from that
      session's terminal scrollback, not a written spec, and both entries say so.
      Earlier in the session: committed the close-out correction the previous
      session left hanging (`5904833` — verified the 23-commit claim against the
      vault before committing it), pulled the shared core (`3ceb2f3..9f85d40`,
      docs-only, nothing to re-apply downstream), and archived 3 completed
      sessions.
- [x] **2026-08-06** — TebelloReborn: built the Stage 6 submission core
      (platform-agnostic, no Playwright). 23 commits in the Pappa T vault,
      **249 → 344 tests, zero regressions, 100% coverage on `src/submission/`**,
      and no new runtime dependency. The queue item above is now the *adapter*,
      which is blocked on Tebello's two decisions rather than on code.
      Ported the hub spec into the project's own `docs/specs/submission-core.md`
      with corrections, ran `/codex-review` per that project's Hard Rule 13, and
      folded the results in as a dated Amendment before writing any code.
      **Codex earned its keep:** it caught a real contradiction in the spec —
      the gate refused anything not `approved` while the transition table called
      failures retryable, making `submission_failed → submitted` unreachable
      from the only CLI that would use it. Resolved by admitting
      `submission_failed` to the gate, which is safe precisely because that
      status is reachable only from `approved`.
      Two pre-build findings were corrected during the build: the hub spec
      targeted a platform this project **formally dropped on 2026-08-01** (not
      merely a data mismatch), and **no migration was needed after all** — a
      net-new table's `CREATE TABLE` belongs in `init_db()` per the project's
      own convention, and `vacancies.status` is unconstrained `TEXT`. The
      shared-`user_version` trap is real but never triggered; the rule is now in
      that project's `CLAUDE.md` Hard Rule 6 instead of a spec footnote.
      Found and deliberately **not** fixed: `black . && ruff check .` — the gate
      that project documents — no longer passes on a clean checkout under
      current tooling, reformatting 17 untouched files including 7 in the
      Hard-Rule-12-protected archive. Scoped the formatters to changed files
      instead and logged it as a Known Issue; a repo-wide reformat is its own
      decision and its own commit. See `knowledge/tebelloreborn.md`.
- [x] **2026-08-06** — Scheduled the runtime-data backup daily. Windows task
      `DCOE runtime-data backup`, 12:30, running as the interactive user at
      Limited (unelevated) level, logging to `~/Backups/backup-runtime.log`.
      Runs only while logged on **by design** — the alternative requires
      storing the account password with the task; `-StartWhenAvailable`
      covers missed runs instead. Added a `--log-file` option to the script
      for this (a scheduled task has no console, so `--quiet` would discard
      the detail and leave nothing to diagnose). Verified by triggering it:
      `LastTaskResult = 0` **and** the resulting manifest checked — 7
      databases, all integrity + row-count verified, no failures. Exit code
      alone wouldn't have proved a real backup happened. See
      `knowledge/operations-hub.md` for settings rationale and management
      commands.
- [x] **2026-08-06** — Made the runtime-data backup repeatable:
      `scripts/backup-runtime-data.py`, committed in this hub (cross-vault
      work, so hub territory per hub-and-spoke — and it means the script is
      itself version-controlled, unlike the one-off). Spec:
      `docs/specs/2026-08-06-runtime-data-backup-script.md`. Discovers files
      by pattern instead of a hardcoded list, and immediately found three
      things the manual list had missed (a `.pfx` certificate, two
      `Operations/` agent-memory trees). Verifies every DB by
      `integrity_check` + row-count against source, hard-asserts that no
      secret reaches the synced tree (exit 2 if violated), reports drift
      against the previous run, and prunes to the last N runs. Two bugs
      caught during the build: `*.db` doesn't match SOPS's
      `sops.db.pre-*` rollback snapshots (silently dropped all 7 — found by
      diffing against the hand-run output, not by reading code), and
      `.claude/worktrees/` are live git worktrees that duplicated every match
      three times. Scheduling deliberately left as a separate decision, now
      the one backlog item.
- [x] **2026-08-06** — Backed up the live gitignored runtime data — the last
      thing in this system with no second copy anywhere. 6 live databases
      (incl. production `sops.db`, 13 tables / 6,501 rows), 7 SOPS
      pre-migration snapshots, and 8 agent-memory files → `~/Backups/
      dcoe-runtime/<stamp>/` **and** `~/OneDrive/DCOE-Backups/<stamp>/`.
      The 6 secret files (4× `.env`, `credentials.json`, `token.json`) went
      to `~/Backups/dcoe-secrets/<stamp>/` **local-only, never synced** —
      verified afterwards that zero secret files reached OneDrive. Databases
      copied via Python's sqlite3 backup API rather than file copy (a raw
      copy of a live DB can capture a torn state), then verified by
      `PRAGMA integrity_check` plus per-table row-count comparison against
      source. See `knowledge/operations-hub.md` for the full procedure;
      making it repeatable is now a backlog item.
- [x] **2026-08-06** — Fixed the inert command frontmatter, upstream first.
      Marketplace PR (merged, `3ceb2f3`):
      https://github.com/tlelosa-web/tlelosa-claude-config/pull/12 (commit
      `5ab6b9a`, branch deleted) — `hub-template/continue.md`
      and `hub-template/session-end.md` both opened with a `---`/`# comment`
      block, valid YAML that parses to nothing, so every vault copying them
      got a command with no registered description. Converted both to a real
      `description:` key with the prose moved below the frontmatter. Fixed
      **both** rather than only the reported `continue.md` — identical defect,
      and patching one would leave the other to be rediscovered. Swept the
      rest of both repos: no other inert blocks (`codex-review.md` already had
      proper YAML with `argument-hint`/`allowed-tools`). Hub's own
      `continue.md` updated to match; its `session-end.md` was already correct.
- [x] **2026-08-06** — Gave the Pappa T vault a remote: private
      `tlelosa-web/pappa-t`, branch renamed `master` → `main` to match every
      other repo, all 215 commits pushed (including `897610e` from the clone
      removal below). Closes the "no remote at all" risk. Audited before
      pushing — the vault tracks real personal material (CVs, cold-email and
      job-tracker files, strategy/financial folders), so private is the only
      correct visibility, not a preference; secrets check was clean across
      the **full history**, not just the current tree, with only `.env.example`
      templates tracked. Note this backs up the *repo*, not the gitignored
      live runtime data (`career.db`, `outreach.db`, `credentials.json`, real
      `.env` files), which stays single-disk by design. See
      `knowledge/pappa-t.md`.
- [x] **2026-08-06** — Full-system cleanliness audit, then removed the stale
      duplicate hub clone. Verified every repo clean and synced (hub,
      marketplace, `2. SOPS`, `3. Nameplate`, Pappa T vault). Audit found
      `Desktop/Pappa T/Claude-Code/` was a second clone of this hub repo on
      the same remote, frozen at `afa0e20` (2026-08-01) — a duplicate hub
      root a session could silently do work in. Removed along with the
      dangling gitlink pointing at it (Pappa T repo commit `897610e`; it was
      mode `160000` with no `.gitmodules` entry, same defect class as
      `b76e942`). Also removed the empty `O-P-C/Pappa T/Claude-Code/`
      leftover. Corrected the 2026-07-28 `knowledge/pappa-t.md` survey bullet
      that had cleared this folder as "not a submodule, not a violation to
      clean up" — true when written, invalidated by the 2026-08-03
      consolidation. See `knowledge/pappa-t.md`.
- [x] **2026-08-06** — Fixed the two `/session-end` defects found on its
      first real run, upstream first then re-copied down. Marketplace PR
      (merged, `e6d381a`):
      https://github.com/tlelosa-web/tlelosa-claude-config/pull/11 (commit
      `9bd83aa`, branch deleted) — reworded the
      session-log step to reconcile-not-duplicate, and the title step to
      report "not available" outright rather than implying an attempt that
      can't be constructed on this tool surface. Fix 1 touches
      `hub-template/` only (the marketplace keeps no session log); fix 2
      touches both it and the marketplace's own instance. Also recorded in
      that spec that its `Status: Implemented` predated item 3. Hub instance
      updated to match in the same session — per ADR-008 the file-copy
      distribution means each vault needs this applied by hand.
- [x] **2026-08-06** — Adopted `/session-end` in this hub:
      `.claude/commands/session-end.md` written as the full hub instance the
      upstream spec (`tlelosa-claude-config/docs/specs/2026-08-04-session-end-command.md`,
      item 3) already called for. Adapted rather than copied — adds a Step 0
      Hard Rule 6 pull-first gate (it writes all three contention files, so
      it's the highest-risk command here for stale-base edits), an explicit
      post-append ordering check on `session-log.md` (the defect fixed
      earlier the same day), the `knowledge/` + `INDEX.md` step (Hard Rule
      5), the hub-and-spoke note for project-scoped work, and the 📍
      live-Desktop-copy caveat. Found that spec's `Status: Implemented` was
      only true for its marketplace-side items 1-2 — item 3 was never
      created, which is why this was still outstanding. Not corrected
      upstream from here (different repo, not this session's call) — see
      `knowledge/tlelosa-claude-config.md`.

- [x] **2026-08-06** — Hub housekeeping. Fixed a real `docs/session-log.md`
      ordering defect: PR #14's merge inserted the 2026-08-04 TebelloReborn
      entry *above* two 2026-08-03 entries instead of appending it, and since
      `/continue` Step 1 reads only the final entry, every future run would
      have reported stale state and never seen the 2026-08-04 decision.
      Moved it to the end (left the `codex-review ... : ran` marker in place
      — its adjacency to the codex-gate entry is load-bearing). Pulled the
      shared core (`dac2258` → `9a18c8f`, adds `/session-end`; backlog item
      above). Archived the superseded `Cont-"TebelloReborn scope decision &
      exports"` session after renaming it from generic `Continuation`.
      Note: Hard Rule 6's pull-before-edit prevents *conflicts*, not
      *misordering* — a clean auto-merge is how this defect got through.
      See `docs/session-log.md`, 2026-08-06 entry.

- [x] **2026-08-03** — SOPS: Payment Status data-migration review completed.
      Reviewed all 19 flagged SOs directly against the live
      `Desktop/Operations/2. SOPS/instance/sops.db` with Tebello: 18
      confirmed correct as-migrated, 1 (SO4722) corrected — a leftover
      best-guess mapping from the original migration, fixed after backing
      up the DB first. Every flagged SO now has an explicit human decision
      on record. See `knowledge/sops.md` and SOPS's own
      `docs/todo.md`/`docs/session-log.md` (2026-08-03 entries) for detail.
- [x] **2026-08-03** — codex-gate: install + network-off smoke-test
      completed. Confirmed installed (user-level `~/.claude/plugins`,
      applies machine-wide on `TshepangLelosa` since Operations and Pappa T
      are now the same physical machine). Ran both paths: network-available
      `/codex-review` against `docs/specs/2026-07-29-nameplatetool-test-suite.md`
      succeeded and appended a real advisory note to that spec; network-off
      (simulated via an unreachable proxy for one command, not a real
      adapter change) confirmed the fail-warn design — found that `codex
      exec` doesn't fail fast on its own (retries its own reconnect logic
      for the full duration), so the skill's 90s `timeout` cap is what
      actually bounds it, not a formality. See
      `knowledge/tlelosa-claude-config.md` for full detail. Fan Movement IT
      confirmation on Operations OpenAI-egress remains open but was never a
      tracked checkbox here (external answer, no spec, not
      session-executable).
- [x] **2026-08-03** — ai-outreach-agency: Ollama `READ_TIMEOUT`/`keep_alive`
      fix — found already implemented and committed (`3ec16cd`, 2026-07-31,
      in a Pappa T session predating the O-P-C consolidation, never logged
      back to this queue). Verified `READ_TIMEOUT = 120` and
      `"keep_alive": "30m"` are both present in
      `Pappa T/ai-outreach-agency/src/research/ollama_client.py` and that
      the fix is already part of O-P-C's merged history (`3ec16cd` is an
      ancestor of this repo's current `HEAD`). Ran the unit suite fresh
      (17/17 pass) before closing out. See `knowledge/ai-outreach-agency.md`.
- [x] **2026-07-31** — pitwall-companion: made the Loadouts GP Event
      availability filter collapsible (renamed to just "GP Event") — merged
      as PR #19; doesn't need to be visible all the time per Tebello's
      direction. Reused the Boosts tab's "New Boost" `<details>`/`<summary>`
      collapsible pattern (generalized its CSS from `.nb-*` to `.coll-*`
      since it's now shared by two features), collapsed by default with the
      active tier still shown in the summary line. Found and fixed a
      state-loss bug while testing: the app's full re-render on every
      tier/legendary-checkbox click would have snapped the panel shut after
      each interaction, so added an explicit `gpFilterOpen` state variable
      instead of relying on the native `<details>` open attribute surviving
      a DOM rebuild. Not its own queue item for the same reason as the
      entries below. See `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: added a Boosts scope to Tools →
      Compare, alongside Drivers/Components — sortable table of owned
      consumable Boosts (qty > 0) across all 13 boost stats plus a computed
      Total, reusing the same table markup/sort mechanic as the existing
      two scopes. Merged as PR #18 (together with the Spa entry below — both
      landed on the same branch and were opened as one PR). Not its own
      queue item for the same reason as the entries below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: added Spa (Belgium) to the `TRACKS`
      Track Stats list (driver stat Overtaking, component stat Power Unit),
      transcribed from an in-game screenshot — merged as PR #18. Not its own
      queue item for the same reason as the entries below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: made the Loadouts → By Track
      loadout customizable, matching By Attribute — merged as PR #15 (final
      pitwall-companion change of the day; the app was then shared to
      Tebello's Discord for a trusted-tester trial week). The loadout card
      was previously locked to the track's single official component stat;
      it now has its own attribute toggle bar (independent of By Attribute
      mode's selection), defaulting to the track's stat but adjustable from
      there, and resetting to that default whenever the track changes. The
      driver ranking and Suggested Boost stay tied to the track's official
      stats by design — only the loadout became customizable. Hit the same
      class of merge-conflict issue as PR #14 (long-lived branch, several of
      its own prior PRs squash-merged into `main` without the branch ever
      restarting from it) — resolved the same way: keep the branch's newer
      code, then verify with an executability check + full regression pass
      rather than trusting a clean "no conflict markers" diff alone. Not its
      own queue item for the same reason as the entries below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: Loadouts → By Track, Suggested
      Boost, and a Boosts-ownership tab — merged as PR #14 (after resolving a
      real merge conflict that briefly resurrected already-superseded code;
      see `docs/session-log.md` for how). Loadouts gained a mode switch (By
      Attribute / By Track); By Track adds a 21-circuit dropdown showing the
      best 2 owned drivers for the track's driver stat, a Suggested Boost
      (top 3 owned consumable Boosts ranked by driver stat then component
      stat), and the same full loadout card as before for the component
      stat. New 4th Tools tab "Boosts" tracks quantities owned per consumable
      Boost (dropdown picker, not a 65-item scroll) and includes a New Boost
      form for boosts the game adds faster than this app can track — custom
      entries compete in Suggested Boost rankings alongside built-ins. Added
      4 newly-discovered boosts (Livewire Plus, Midnight, Mushroom,
      Succession) transcribed from Tebello's own in-game screenshots.
      Overhauled README.md, which had gone stale across the last several
      merges (still described single-mode Loadouts, no mention of Boosts tab
      or Track Spec, undercounted boosts at 65 instead of 69). Not its own
      queue item for the same reason as the entries below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: follow-up polish batch after the
      workbook audit + Loadouts picker (below) — merged as PRs #11 and #12:
      fixed the header's small icon (was still the pre-rename inline-SVG
      placeholder, now uses the real `icons/icon-192.png` pit-wall artwork)
      and centered the header title; renamed the app's user-facing branding
      from "F1 Clash Resource Sheet" to **PitWall Companion** (title, header,
      manifest name/short_name, export filename/tag, QR alt text) per
      Tebello's copyright-exposure concern about the app's own name leaning
      on the game's trademark — left factual/disclaimed game and workbook
      references untouched (already covered by the existing "unaffiliated
      fan tool" disclaimer), and left the internal `localStorage` keys /
      cache-version string (`f1sheet.*`) untouched since renaming those
      would silently wipe existing users' saved card levels; and laid out
      both the Loadouts attribute-toggle buttons and the aggregate stat
      chips as equal-size grids (2x2 and 2x3) instead of uneven flex-wrap
      rows. Not its own queue item for the same reason as below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: audited the app against the
      community "F1 Clash 2026 Resource Sheet" workbook (v1.1, the
      confirmed source-of-truth version) — no gaps found, driver/part
      rosters, per-level stats, Series unlocks, and CCData/rewards
      constants all in sync. Then, per Tebello's direction, replaced the
      Suggested Loadouts tool's 9 stacked fixed-strategy cards with 4
      multi-select attribute toggle buttons (Speed/Cornering/Power
      Unit/Qualifying) rendering a single live card, removing the need to
      scroll; selection persists via its own localStorage key. Verified
      with a headless-browser smoke test (single-card render, multi-select
      combine, last-attribute deselect guard, reload persistence, zero
      console errors) before pushing. Merged as PR #9
      (tlelosa-web/pitwall-companion), then updated `README.md`'s Loadouts
      description to match (PR #10, merged) since it still described the
      old fixed-strategy list. Not tracked as its own queue item since
      pitwall-companion isn't part of this hub's machine-bound spec queue
      and has no `docs/todo.md` of its own — logged here per Hard Rule 5
      since Tebello asked for the hub log to be updated. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-29** — NamePlateTool Excel-import spot-check completed
      (Operations session): ran a live `uvicorn` backend against the real
      `NAME PLATE PROCEDURE.xlsx`, confirmed `GET /api/nameplate/from-excel`
      returns `200` with no datetime-serialization crash and a correctly
      formatted `date_of_manuf`, then fed that data through
      `POST /api/generate-pdf` and confirmed the generated PDF has every
      Excel-sourced field populated and non-blank. Commit `777be76`'s fix
      is fully verified — see `knowledge/nameplatetool.md`. Also: pulling
      `origin/main` on the NamePlateTool sub-repo to obtain that fix
      surfaced an unrelated uncommitted merge-conflict situation (prior
      session's bug-hunt findings vs. the pulled fix), resolved as a real
      union and staged but left uncommitted per standing policy — flagged
      to Tebello, not committed automatically.
- [x] **2026-07-29** — codex-gate: copied the drafted ADR into this hub's
      `docs/decisions/` (`ADR-009-codex-second-opinion-gate.md`), closing
      the documentation sub-item — done via git directly from a cloud
      session (no Operations machine access needed, since this hub repo
      is git-synced there, not filesystem-only). Discovered `docs/decisions/`
      didn't exist yet and neither ADR-007 nor ADR-008 were actually
      recorded there despite being referenced from `tlelosa-claude-config`.
      codex-gate install itself stays Pappa T-only, unaffected by this.
- [x] **2026-07-29** — Wrote up `ADR-007-core-md-read-not-import.md` and
      `ADR-008-hub-template-promotion.md` in this hub's `docs/decisions/`,
      closing the gap found above — both reconstructed from what's
      documented across `tlelosa-claude-config` (CORE.md's own
      distribution note, README, `HUB-CHECKLIST.md`), not from source
      commits (this session doesn't have `tlelosa-claude-config`'s git
      history). ADR-008's date is approximate.
- [x] **2026-07-29** — Wrote a ready-to-execute spec for every machine-bound
      item in this queue (`docs/specs/2026-07-29-*.md`, 8 files: NamePlateTool
      spot-check + test suite, codex-gate Pappa T smoke-test + Operations
      ADR copy, TebelloReborn scope decision, ai-outreach-agency Ollama
      timeout, SOPS AvgMovement migration (gated) + Payment Status review)
      — so the moment `/continue` runs on Pappa T or Operations, the next
      task on that machine already has exact steps, no fresh research
      needed. Linked each spec from its `docs/todo.md` item and split the
      3-part codex-gate item into 3 numbered items (2 machine-bound specs +
      1 externally-gated item with no spec) since they don't share a
      machine. Fixed a numbering gap (item "3" had been skipped since the
      2026-07-29 renumbering).
- [x] **2026-07-29** — Removed the "ai-outreach-agency: top up OpenRouter
      credits" item per Tebello's direction — treated as a dead end, not
      pursued. `asset_gen` stays blocked on OpenRouter until the
      headless-Claude-Code migration (Build Queue A) lands instead; see
      `knowledge/ai-outreach-agency.md` for the superseded entry.
- [x] **2026-07-29** — Hub process review: promoted the NamePlateTool
      Excel-import spot-check (previously just a prose caveat in
      `session-log.md`) to a tracked `docs/todo.md` item; resolved the
      numbering-backlog question by keeping fixed numbering (renumbered
      1-9) since the priority set hasn't cleared yet and the "fold to flat
      checklist" question only mattered once it does; added `CLAUDE.md`
      Hard Rule 6 and `/continue` Step 1.75 ("Sync Check") to fix the root
      cause of the two real merge conflicts already hit on
      `docs/todo.md`/`session-log.md`/`knowledge/INDEX.md` — pull
      `origin/main` before editing any of the three contention files.
- [x] **2026-07-28** — Pappa T vault survey (second pass, from a Pappa T
      session running concurrently with the hub-setup work above): resolved
      the `Claude-Code/` folder's earlier "untracked nested repo" flag from
      a Pappa T `/continue` run (it's this repo itself — deliberate, not
      stray work); replaced the inline TebelloReborn note in
      `knowledge/pappa-t.md` with a dedicated `knowledge/tebelloreborn.md`
      (more detail, and resolves that note's "[scraping specifics unclear]"
      gap); added four more Pappa T sub-project knowledge files
      (`ai-outreach-agency.md`, `mims-app.md`, `iq-signal-generator.md`,
      `tenders-sa.md`) — none of Pappa T's five sub-projects are independent
      git repos, so none had ever been individually tracked here. Confirmed
      no other dev-root exists on the Pappa T machine; noted `~/OneDrive/`
      and `~/Documents/Codex/` as data-only, `~/python-sdk/` as a runtime
      download, and the extra `~/Downloads/tlelosa-claude-config/` clone as
      already covered by its existing entry. Surfaced two new tasks from the
      survey (ai-outreach-agency credits + Ollama timeout, above).
- [x] **2026-07-28** — Added a machine-bound-task check to `/continue`
      (Step 2.5 in `.claude/commands/continue.md`): before reporting,
      flag candidate next-tasks that need local access on a specific
      machine (Pappa T, Operations) this session can't reach, and surface
      that in both the Step 3 report and the `AskUserQuestion` option
      descriptions. Prompted by this session offering the Pappa T vault
      survey as pickable from a cloud session where it wasn't actually
      runnable.
- [x] **2026-07-28** — Confirmed NamePlateTool's Excel-import bug (former
      #1 priority) was fixed in a separate session (commit `777be76`):
      datetime crash and dead `"Table 1"` sheet check both resolved.
      Discovered while syncing repo state across all 5 tracked repos after
      the Operations vault survey — only NamePlateTool had new activity.
      Updated `knowledge/nameplatetool.md`, removed the item from this
      queue. Not yet manually re-verified against a generated PDF from this
      session — worth a spot-check.
- [x] **2026-07-28** — Operations vault survey: enumerated every project
      folder on the Operations machine, confirmed no new project roots
      beyond the already-tracked ones plus three gaps (SOPS,
      delivery-note-system, Daily Sales Order Files — `8. AvgMovement`
      folded into `sops.md` as a note, not a separate file, since it's
      Retired and its logic was ported into SOPS). Wrote
      `knowledge/sops.md`, `knowledge/delivery-note-system.md`,
      `knowledge/daily-sales-order-files.md`; updated `knowledge/INDEX.md`;
      added two new outstanding items (#5, #6 above) to this queue.
- [x] **2026-07-28** — Set up Operations (work PC) as a DCOE hub client of
      this repo, mirroring the Pappa T setup: confirmed already cloned at
      `C:\Dev\Claude-Code` (sibling of `C:\Dev\Operations`, on `main`),
      confirmed the git-sync bridge end to end (`fetch` + `pull` pulled a
      real fast-forward of 8 files, `push --dry-run` confirmed clean),
      read root `CLAUDE.md` + `knowledge/INDEX.md`, and recorded the
      confirmation in `knowledge/operations-hub.md`.
- [x] **2026-07-28** — Cross-project status survey: cloned and checked
      live GitHub state for all 5 repos, merged `tlelosa-claude-config` PR
      #9, closed this repo's stale/conflicting PR #1, confirmed the
      Pappa T ↔ cloud-environment git-sync bridge end to end, and filled
      the TebelloReborn knowledge gap. Published as a dashboard artifact.
- [x] **2026-07-28** — Set this repo up as the real DCOE hub root per
      `hub-template`: `.claude/commands/continue.md`, this file, and
      `docs/session-log.md` added; root `CLAUDE.md` reconciled against
      `hub-template/HUB-CHECKLIST.md`.
