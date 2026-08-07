## 2026-08-07 — ADR-004 answered the `user_version` question; Phases B and C then built the same day
**Source:** session (this machine, hub `/continue`) — read from the Pappa T vault's
commits, `TebelloReborn/docs/decisions/ADR-004-schema-migration-ledger.md`, and that
project's own `docs/session-log.md` entries for Phases B and C
**Status:** active

Supersedes the *prediction* in the entry below ("Phase B is blocked on an ADR that
does not exist yet"). Its diagnosis of the bug stands unchanged and is still the
best statement of it; only its forecast is now history. The ADR was written,
Codex-reviewed, accepted and **built** on 2026-08-07 (Phase 18, steps 107–117), and
Phases B and C shipped on top of it the same day.

**State now: Stage 6 stands at Phases A, B, C built; D–H remaining.** 485 tests
passing (344 → 399 → 456 → 485 across the ADR, B and C), zero regressions
throughout, still fully offline — nothing on the wire, no `playwright` dependency
declared until Phase H, and the adapter registry is still empty, so all 6 approved
Indeed vacancies route to manual today. Vault is clean and pushed (`63687c5`).

**ADR-004's decision, in one line: `PRAGMA user_version` was a single-writer counter
being used as a multi-writer applied-migrations record.** It stores one number, not a
set, so it cannot answer the only question a migration runner asks — *has this
migration, from this module, already run on this database?* Every symptom was
downstream of that. It is replaced by a per-module ledger table with a shared runner;
Hard Rule 6's "globally-unique version ≥ 5" decree was a manual collision-avoidance
scheme for a namespace that never needed to be shared, and it failed silently because
`if version > current` has no error path. Live `career.db` was inspected directly for
the ADR and stayed at `user_version = 4` throughout.

**Why it was genuinely blocking and not merely untidy — a detail the entry below
didn't have.** The `profile` fix works by asking `PRAGMA table_info` whether a column
exists, so it only understands `ADD COLUMN`. There is no equivalent question for a
`CREATE INDEX`, a backfill, or a table rebuild. **Phase B's central migration is a
table rebuild** — SQLite cannot alter a CHECK constraint in place, so widening
`submissions.outcome` for `pending_review` is the 12-step rebuild. Extending the
`profile` pattern verbatim would not have worked; Phase B would have had to invent a
third mechanism inline, inside a feature build.

**Phase B (Phase 19, steps 118–122) — the design point worth keeping.** The spec's
original `all_questions_reviewed()` could not have worked: counting
`screening_questions` rows cannot distinguish "prep never ran" from "prepped, and
this posting genuinely has no questions." Both are zero rows and exactly one of them
is submittable. Prep state now lives in its own append-only `submission_preps` table,
where the absence of a row is the one state that genuinely is an absence.
Phase B also **deviated from its own spec deliberately**: A4 resolved the CHECK
widening as a DDL edit plus a loud guard, correct when written because the live DB
has no `submissions` table — but on a database where `submit` had run once that
combination fails at `init_db()` with no automated remedy. ADR-004 landed in between
and made the remedy cheap, so it shipped `src/submission/migrations.py` version 1
instead, this project's first table rebuild.

**Phase C (Phase 20, steps 123–127) — two orderings, each with its own test, because
getting either wrong fails silently.** (1) The prep gate runs *before* the session
check: every answer it gives is already-recorded state, so none of it needs a live
session. Session-check-first would tell Tebello "no saved browser session — run the
login setup" for a recorded `external_ats` posting, sending him to fix something that
isn't broken and burying the one finding that means *submit by hand*. (2) The `--all`
refusal is checked *last*, so a vacancy with a real gate reason hears that instead —
"run `prep-submission`" beats "use an explicit `--vacancy-id`" for something you'd
have to prep first anyway.

**General pattern, now confirmed twice in this project:** `pending_review` and
`not_supported` leave the vacancy in the *same* state, so CLI wording is the only
thing separating them for the operator. Its test asserts `"FAILED"` is **absent** as
well as asserting the right substrings present — without a dedicated
`report_attempt()` branch the detail printed under a FAILED label, which is the right
words under the wrong verdict and would have passed a naive substring assertion.
Assert what must not appear, not only what must.

**Open, not blocking:** `/codex-review`'s path guard is hard-scoped to `docs/specs/`
and refused ADR-004 — the review went through a direct `codex exec` with the
identical instruction and payload discipline instead. Second time an ADR has wanted
that gate. Also two byte-identical `career.db` backups are sitting untouched awaiting
Tebello's pick of which to keep.

## 2026-08-07 — Phase A built; the `user_version` fix is scoped to one module and Phase B re-arms it
**Source:** session (this machine, hub `/session-end`) — read from the Pappa T
vault's commits and `TebelloReborn/docs/todo.md` Open Items
**Status:** superseded in part — the diagnosis below stands and is still the clearest
statement of the bug; its closing forecast ("Phase B is blocked, that project wants
an ADR") is resolved by the entry above, which is authoritative for current state

Closes the "Next: Phase A, blocked on…" line in the entry below — both of its
blockers were cleared and Phase A shipped (Phase 17, steps 103–104; vault
`9d4ee17` RED, `379a4b2` GREEN, `b4dd652` close-out). `email`/`phone` are on
`CandidateProfile` behind **migrations 5 and 6**, this project's first ever, with
real values from `data/Tebello_Lelosa_Master_CV_2026.md` and a test asserting the
seed and the CV never drift. `career.db` was backed up beforehand
(`career.pre-migration-5-6-20260807.db`) via the sqlite3 backup API, integrity-
checked and row-count-verified. Phases B–H are not started.

**The finding worth carrying: fixing the shared-`user_version` trap in one module
does not disarm it, and the next migration re-arms it.** The fix was deliberately
scoped to `src/profile/`. `vacancy_search/`, `doc_gen/` and `review/` still carry
the counter-only `apply_migrations` (`if version > current`, no schema check), so
any of them can still be skipped by whichever module advanced the counter first.

What makes it fatal rather than cosmetic is a detail that only shows up in the
baseline: **`vacancy_search`'s `CREATE TABLE vacancies` omits
`score`/`strengths`/`weaknesses`/`recommendation`** — those columns exist *only*
in migrations 1–4. So a fresh database whose counter was advanced past them by
another module gets a `vacancies` table permanently missing four columns the code
expects. That is the shape of the Phase 17 regression, and it is unchanged.
Nothing hits it today only because `profile` no longer advances the counter on a
fresh DB — a coincidence of ordering, not a fix.

**Consequence:** Phase B adds `submission_preps`/`screening_questions` and may
need a `user_version ≥ 5` migration for the `submissions.outcome` CHECK rebuild,
so it is exactly the thing that re-introduces the bug. That project wants an ADR
making schema state the source of truth across all four modules — either a shared
runner in `src/shared/`, or folding each module's migrations into its own baseline
and applying the `profile` guard everywhere — before Phase B starts.

**General pattern:** a migration runner keyed on a counter rather than on observed
schema state is safe only while exactly one module uses it. The bug is latent from
the moment a second module exists, and the "it works today" reassurance comes from
call ordering, which is not a property anyone is maintaining on purpose.

## 2026-08-07 — Indeed adapter: Codex fold-in complete, spec build-ready
**Source:** session (this machine, hub `/continue`) — read the code and the live
`career.db` directly; four of the findings below are not in Codex's review at all.
**Status:** active

Closes the "not yet resolved into the design" gap left by the entry below. Amendment
appended to `TebelloReborn/docs/specs/indeed-submit-adapter.md` (Pappa T vault
`3267cb5`, pushed): 22 accepted changes, 6 clarifications, 4 declined. **No code
written** — this was the spec gate, not the build.

**Reusable, project-independent lesson: a capability predicate that is cheap for the
caller who names it can still be expensive for the callers who don't.** Codex flagged
`can_handle()` as accidentally a networked/browser action. What made it a real defect
rather than a style point only shows up in the code: `eligibility.get_adapter()` calls
`can_handle()` on **every** `submit` invocation — including `--manual` and every
`not_supported` case, neither of which involves the adapter at all. A predicate that
opens a browser would have driven a live session on paths that submit nothing. Fix:
`can_handle()` is a pure `urlsplit` check; everything live moved to
`inspect_apply_flow()`, deliberately outside the `SubmitAdapter` Protocol.

**Two spec claims that would have failed at runtime, both found by reading code the
spec described from memory:**

1. **"No DB migration needed for `email`/`phone`" was a false analogy.** The spec cited
   `VALID_PLATFORMS`/`VALID_STATUSES` as precedent — but those validate *values* in an
   existing unconstrained `TEXT` column. `candidate_profile` is a real table with named
   columns (`id, name, region, skills, experience, target_titles, industries,
   salary_floor`) and `upsert_profile()` writes them by name, so `email`/`phone` are
   **new columns** and would have raised `no such column: email` on first write. Now
   migrations **5 and 6** in `profile/migrations.py` — the first migration this project
   has written since Hard Rule 6 (globally-unique `user_version` ≥ 5, because
   `vacancy_search` holds 1-4 and the live DB is at 4) was recorded. **The general
   form: "it's just Python validation" is only true when the column already exists.**
2. **A `CHECK` constraint inlined in `CREATE TABLE IF NOT EXISTS` has a silent
   expiry.** Adding `pending_review` to `submissions.outcome` requires editing that
   DDL string — which works only while the table doesn't exist. Verified the live
   `career.db` is at `user_version = 4` with tables `candidate_profile`/`vacancies`/
   `generation_log`/`approvals` and **no `submissions` table** (Stage 6 has never been
   run against it), so the window is open today. Run `career-engine submit` once first
   and `IF NOT EXISTS` keeps the old 3-value constraint forever, surfacing as a CHECK
   violation at insert time, far from its cause. Resolution: change the DDL *and* add a
   drift guard in `init_db()` that reads `sqlite_master.sql` and refuses loudly.
   **Same trap family as the shared-`user_version` one, different disguise.**

**Two more code-grounded corrections:** `run_claude_code()` shells to `claude -p`,
which needs connectivity — ADR-003's "local subprocess" framing is about rate-limiting
and cost, not offline capability, so the spec's "local, network-optional drafting pass"
was wrong (`prep-submission` needs network twice: Indeed *and* Claude Code). And
`generation_log` has **no path column**, so nothing in the DB maps a vacancy to its
generated PDFs — the adapter must reconstruct `pdf_export`'s
`{company}_{id}_{cv|cover_letter}.pdf` naming, promoted to a shared
`resolve_export_paths()` rather than duplicated into the adapter.

**Design decisions worth remembering:**
- **`prep_failed` was deleted rather than defined.** Codex asked for outcome-table
  semantics; the better answer was that prep attempts no submission, so its failures
  don't belong in an attempt log at all. They went to a new `submission_preps` table,
  whose seven states also fixed a separate ambiguity — zero `screening_questions` rows
  meant both "genuinely no questions" and "prep never ran", and only one is
  submittable. **Inferring state from the absence of rows was the actual bug.**
- **CAPTCHA detection must name its never-abort states, not just its abort states.**
  The recon established a "protected by reCAPTCHA" notice and a `.grecaptcha-badge` are
  present on every *healthy* run; a detector that treats reCAPTCHA presence as a
  challenge aborts 100% of runs. Five specific abort states, three explicit never-abort.
- **Ambiguity after clicking submit is not `failed`.** Reporting failure on a
  submission that went through invites a duplicate application. Ambiguous outcomes
  record an `UNCONFIRMED:` detail that *blocks* further automated attempts until
  Tebello resolves it with `--manual` or a re-prep.
- **Every employer-authored answer is reviewed** — the `auto_fillable` "matched
  confidently" concept was deleted, not made testable. A location field auto-filled
  from `profile.region` is still an answer his name goes on. Compensation,
  work-authorization and demographic questions are never LLM-drafted at all.
- **`submit --all` refuses auto-submit in this build.** A policy answer to the accepted
  account-risk exposure, chosen over a backoff engine that could be mis-tuned.

**Next:** Phase A, blocked on Tebello's real `email`/`phone` values, and back up
`career.db` first — migrations 5/6 auto-apply on the next `init_db()` from any command.

## 2026-08-07 — Indeed adapter: spec written, Codex-reviewed, real scope findings
**Source:** session (this machine, hub `/continue`) — authoritative, not scrollback.
Directly ran the browser recon and wrote the spec this entry describes.
**Status:** partially superseded by the 2026-08-07 fold-in entry above — its recon
findings and decisions stay accurate; its "not yet resolved into the design" close and
its "not yet pushed" note do not (vault `8c95cf2` and `3267cb5` are both pushed).

**Supersedes the entry immediately below** (which was itself pieced together from a
concurrent terminal session's garbled scrollback, "not from a written spec"). That
concurrent session's work is real and preserved — commit `93f8e5b` in the Pappa T
vault — but it parked at the Indeed sign-in boundary with the ToS/risk questions
still open. **Confirmed with Tebello that session was already closed** before any
further work happened here, so this is a sequential handoff, not an active collision,
but it is worth remembering as a real instance of the class of risk that motivates
this hub's own Hard Rule 6: two Claude Code sessions (this one running Sonnet 5, the
other Opus 5) independently working the identical task in the identical project
folder on the same morning, both editing the same files.

**What actually got resolved, directly with Tebello, this session:**
- **Platform: Indeed's own apply form only** (Indeed is the only live source with
  approved applications — 6 — but per-employer variation and external-ATS redirects
  mean `can_handle()` must decline confidently rather than guess).
- **ToS/account-risk exposure: explicitly accepted.** This is the one the concurrent
  session correctly refused to treat as settled by mere sign-in — it needed a real,
  separate acknowledgement, which happened here.
- **`playwright` accepted** as a new runtime dependency (browser binaries included),
  a deliberate break from the project's three-dependency offline-first footprint.

**Real live-site recon (`claude-in-chrome`, signed in as Tebello himself — no agent
touched credentials at any point), one of the 6 approved vacancies, nothing
submitted.** Three findings reshaped the build beyond what the concurrent session's
scope decisions anticipated:
1. Indeed's native apply flow is a separate app (`smartapply.indeed.com`,
   `/beta/indeedapply/form/<module>/<step>`), not the job-posting page — a
   multi-step wizard with per-step URLs, useful as a navigation-state signal (though
   Codex's review below flags it as too brittle to be the *sole* signal).
2. Resume selection **defaults away from the generated CV** to Indeed's own on-file
   resume — the adapter has to actively select/upload the right PDF every time.
3. The flow is **reCAPTCHA-protected**. No challenge rendered during this
   walkthrough, but the design now carries a hard, non-negotiable rule: detect any
   CAPTCHA challenge and abort immediately, never attempt to solve or defeat it —
   this is a separate risk category from the ToS/account-risk acceptance above, not
   covered by it.
4. **Employer screening questions are real, per-posting, and often open-ended
   free-text** — one posting asked for an essay describing a recent project. Neither
   this session's design nor the concurrent session's scope notes anticipated this;
   it's the finding that turned "one dict entry" into a real sub-pipeline. Tebello
   decided: LLM-drafted answers (headless Claude Code, `wrap_untrusted_text()`-
   wrapped, same untrusted-content discipline as `vacancy.description`), held for his
   explicit per-question approval before any submission — never auto-answered.

**Spec written:** `TebelloReborn/docs/specs/indeed-submit-adapter.md`. Three new CLI
commands (`prep-submission` / `review-questions` / `submit`), a new
`screening_questions` table, a new `pending_review` outcome distinct from
`not_supported`, `CandidateProfile` gaining `email`/`phone` (confirmed missing
entirely — neither `schema.py` nor `profile_seed.json` had either field). Ran
`/codex-review` per that project's Hard Rule 13 — a real second opinion, not a
rubber stamp: flagged `can_handle()` as accidentally a networked/browser action
(mismatches the "cheap predicate" contract `submission-core.md` assumes), no defined
question-drift policy between `prep-submission` and `submit`, underspecified CAPTCHA-
detection criteria, a referenced-but-undefined `prep_failed` outcome, and failure
modes the spec hadn't considered (duplicate-submission risk, mid-wizard session
expiry, ambiguous success-screen detection). **Not yet resolved into the design** —
that's explicitly the next session's first task, before any executor is dispatched.

Reconciled `TebelloReborn/docs/todo.md` and `docs/session-log.md` as a real union
against the concurrent session's own commit rather than overwriting it, then
committed (`8c95cf2`, Pappa T vault) — not yet pushed to `tlelosa-web/pappa-t`.

**No code written.** Both this project's Hard Rule 2 (plan before touching >2 files)
and Hard Rule 10 (stop and ask when acceptance criteria are unclear) governed the
whole session — three separate points where the honest answer was to stop and ask
Tebello directly rather than assume: the platform/risk/dependency decisions, the
contact-info gap, and how to handle LLM-drafted screening answers.

## 2026-08-07 — Indeed adapter build started; decisions made, ToS gate still open
**Source:** session (this machine), observed from a concurrent terminal session's
scrollback — **not** from a written spec
**Status:** superseded

Supersedes the "still blocked on Tebello" close of the 2026-08-06 entry below.
A separate session began the adapter build and answered most of the gating
questions in its own prompts. Recorded here with that provenance attached: this
came off a terminal scrollback, partly garbled by redraw, so confirm against
`TebelloReborn/docs/todo.md` (reconciled 2026-08-07, vault `93f8e5b`) before
relying on any of it.

- **Indeed, its native apply form only.** A live posting with a real "Apply with
  Indeed" button was confirmed, so the platform's own form genuinely exists and
  isn't only external-ATS redirects. Per-employer variation is unchanged, so
  `can_handle()` must decline confidently — an over-eager `True` converts a clean
  `not_supported` into a silent failure, which is worse than no adapter at all.
- **`playwright` accepted as a runtime dependency**, browser binaries included —
  a deliberate break from the three-dependency offline-first footprint.
- **`email`/`phone` to be added to `CandidateProfile`.** Neither
  `src/profile/schema.py` nor `data/profile_seed.json` has any contact field
  today, and an apply form needs both. Found before building, not as a runtime bug.
- **Selectors from live DOM recon, not guesswork** — the Apify payload-shape
  lesson applied deliberately.

**Still open, and the build starting does not retire it:** the ToS/account-risk
acknowledgement is not on record. Signing in to Indeed for read-only DOM
inspection is *not* that acknowledgement. Recon is parked on that sign-in
boundary — no agent handles those credentials under any authorization.

**Live-DB observation (read-only query, 2026-08-07):** `career.db` holds 6
`approved` + 4 `rejected`, all `indeed`, `user_version = 4`. The `submissions`
table **does not exist yet** — `init_db` creates it on first use, so Stage 6 code
is fully built and tested but has never run against the real database. Worth
knowing before the first live `career-engine submit`.

**Also stale as a result:** `TebelloReborn/docs/specs/submission-core.md`
§Open Items 1 and 3 still read as open despite being answered. Amending that spec
belongs to the session doing the build.

## 2026-08-06 — Stage 6 submission core built (platform-agnostic, no Playwright)
**Source:** session (this machine) — Phase 16, steps 81–102
**Status:** active

The platform-agnostic half of Stage 6 is built and committed in the Pappa T vault
(23 commits, pushed, `10b9e3f` latest). **249 → 344 tests, zero regressions, 100%
coverage on `src/submission/`.** No `playwright` dependency, no browser binary,
nothing on the wire. Project spec: `TebelloReborn/docs/specs/submission-core.md`.

**A stronger version of the platform finding below.** The hub spec didn't just
mismatch the data — it targeted a platform the project had *formally dropped*.
`docs/todo.md`'s Resolved Items records "LinkedIn dropped — decided and actioned
2026-08-01": the Apify actor returned `403 actor-is-not-rented`, renting was
declined, and `LINKEDIN_ACTOR_URL` / the POST block / `_normalize_linkedin()`
were removed from `apify_client.py`. That is three days before the hub spec was
written. Lesson worth keeping: a spec written without repo access can be stale
against a decision the repo already recorded, not merely imprecise about paths.

**Correcting entry 2 below: no migration was needed.** A net-new table's
`CREATE TABLE IF NOT EXISTS` belongs in its module's `init_db()` per this
project's own convention, and `vacancies.status` is unconstrained `TEXT`, so
extending `VALID_STATUSES` is Python-level validation only — the same situation
as step 59's `VALID_PLATFORMS`. The shared-`user_version` trap is real and still
worth knowing, but this build never steps in it. `src/submission/` deliberately
ships **no `migrations.py`**: an empty stub is an invitation to add `(1, …)`
later and hit the silent skip. The rule ("any new migration anywhere needs a
globally-unique version ≥ 5") is now written into that project's `CLAUDE.md`
Hard Rule 6 rather than living only in a spec footnote.

**Design worth reusing.** The registry ships empty on purpose, so every approved
application produces a `not_supported` attempt, is reported with its URL and an
explicit "submit this one by hand", and **stays at `approved`** — the status has
to keep saying the application still needs action. Dispatch is capability-based
(`ADAPTERS[platform]` then `adapter.can_handle(vacancy)`), so a registered
adapter can decline an individual posting — Indeed's per-employer ATS redirects
are exactly that case. Adapters never write to the database and never transition
status; the pipeline owns all persistence, which is what makes it structurally
impossible for a future adapter to route around the human approval gate.

**Codex second opinion earned its place.** It found a real contradiction *before*
any code: the gate refused anything not `approved`, while the transition table
allowed `submission_failed → submitted` and called failures retryable — the retry
path was unreachable from the only CLI that would use it. Fixed by admitting
`submission_failed` to the gate, which is safe precisely because that status is
reachable only from `approved`. General pattern: state-machine specs are worth
checking for states that are declared reachable but have no caller that can reach
them.

**Two process findings, both left as recorded issues rather than silently fixed:**

- **`black . && ruff check .` — the gate that project's own `CLAUDE.md`
  documents — no longer passes on a clean checkout** under current tooling
  (black 26.5.1, ruff 0.15.22). It reformats 17 untouched files, 7 of them inside
  the Hard-Rule-12-protected `_archive_qwen_prototype/`, and ruff reports 10
  pre-existing errors. Worked around by scoping both tools to the files actually
  changed. A repo-wide reformat is its own decision and its own commit — it
  should not ride along inside a feature build. General lesson: a documented
  `black .` gate silently becomes a repo-wide reformat command the moment the
  formatter version drifts.
- **Inlining a new CLI into `main.py` pushed it to 354 lines**, past that
  project's own 300-line file standard. Moved to `src/submission/cli.py`,
  matching how `run_review_gate` already lives in `src/review/cli.py`.

**Still blocked on Tebello, not on code** — the site adapter needs (1) which
platform gets the first adapter (Indeed is the only live source, but its flow
varies per employer), and (2) an explicit ToS/account-risk acknowledgement:
driving an authenticated session to submit is a different exposure from scraping
via Apify, it is his own account at risk, and it is against LinkedIn's User
Agreement and plausibly Indeed's.

## 2026-08-06 — Playwright auto-submit: pre-build verification (no code written yet)
**Source:** session (this machine) — first look at the real TebelloReborn code
**Status:** active

The hub spec `docs/specs/2026-08-04-tebelloreborn-playwright-auto-submit.md` was
written from a cloud session with no access to this code and flagged its own
file names as guesses. They were verified against the live
`Desktop/Pappa T/TebelloReborn/`. Most held; four things did not.

**Confirmed as guessed:** `src/review/` exists with `cli.py` (130 lines),
`db.py`, `migrations.py`, `schema.py`; `doc_gen/pdf_export.py` exists; the
`approvals` table carries a `CHECK (decision IN ('approved','rejected','edited'))`;
the approval gate is structural, enforced by the status state machine.

**1. The spec targets the wrong platform — the blocking finding.** It scopes the
build to **LinkedIn Easy Apply only** and puts Indeed explicitly out of scope.
But every row in `career.db` is Indeed:

```
indeed  approved  6
indeed  rejected  4
```

Zero LinkedIn vacancies exist. Building the spec as written would ship a feature
unable to submit any of the 6 pending approved applications. Tebello chose
(2026-08-06) to **build the platform-agnostic core first** — submission status +
migration, session/`storageState` handling, "not auto-submittable → fall back to
manual" detection, and outcome recording — leaving the site-specific adapter as
a second task once the platform question is settled. No work is wasted either
way, and the core is testable offline under the project's TDD rule.

**2. `PRAGMA user_version` is a single global counter shared by four independent
migration modules.** `profile/`, `vacancy_search/`, `doc_gen/` and `review/`
each own a `MIGRATIONS: list[tuple[int, str]]` and an `apply_migrations()` that
reads and writes the *same* `PRAGMA user_version` on the *same* database.
Currently only `vacancy_search` has entries (1–4) and the live DB sits at
`user_version = 4`.

**The trap:** adding `(1, "ALTER TABLE ...")` to `review/migrations.py` would be
**silently skipped forever** — `apply_migrations` runs `if version > current`,
and `current` is already 4. No error, no warning, no migration. Any new
migration in *any* module must take a globally-unique version ≥ 5. This is not
documented in the project's `CLAUDE.md`, whose rule is only "no schema change
without a migration file."

**3. The spec is wrong about `.gitignore` covering the session file.** It says to
save Playwright's `storageState` to "a path already covered by the project's
existing `.gitignore`". That file covers `.env`, `*.db`, `*.db-shm`, `*.db-wal`,
`exports/` and caches — nothing else. A `storage_state.json` would be
**committed**. That file is a live authenticated session cookie; in git history
it is a session-hijack credential. An explicit ignore entry has to be added as
part of this work, not assumed.

**4. `playwright` is not a dependency.** The project has exactly three
(`requests`, `python-dotenv`, `fpdf2`). Adding it also pulls browser binaries via
`playwright install` — a large, non-pip-clean runtime dependency in a project
whose stated stance is offline-first. Worth a deliberate decision, not a silent
`pip install`.

**Schema change this needs:** `VALID_STATUSES` is
`{new, scored, asset_ready, approved, rejected}` with no `submitted` /
`submission_failed`, and `vacancies` has no column for a submission outcome.
Both are required, and both need a migration file per the project's hard rule.

**Process required before any code** (project `CLAUDE.md`, which takes precedence
over the hub under hub-and-spoke): Hard Rule 13 — `/codex-review` must run on the
spec in the project's own `docs/specs/` and its strongest points folded back as a
dated Amendment *before* an Executor is dispatched. Hard Rule 2 — a plan is
required for anything touching more than 2 files, which this does. Plus TDD
(failing tests first, ≥80% coverage) and `black . && ruff check . && python -m pytest`
before every commit.

**Also flagged, unrelated to this build:** automating submissions while logged in
as Tebello is against LinkedIn's User Agreement, and the account at risk is his.
Scraping via Apify is a different exposure from driving an authenticated session.

## 2026-08-04 — Post-MVP scope decision: Playwright auto-submit picked
**Source:** cloud session, via `docs/specs/2026-07-29-tebelloreborn-scope-decision.md`
**Status:** active

Of the three undecided post-MVP items (Playwright auto-submit,
recruiter/cold-outreach revival, doc-gen volume-cap/scheduler), Tebello
picked **Playwright auto-submit only** — the other two are not committed to
build. Explicit constraint: the Stage 5 human-approval gate stays exactly
as-is; Playwright only automates the mechanical job-site form-filling/
submission step **after** a human has already approved that application's
documents. Full unattended auto-submit (no review step) was considered and
declined as too risky given AI-generated documents and untrusted scraped
vacancy text.

Build spec written: `docs/specs/2026-08-04-tebelloreborn-playwright-auto-submit.md`
— written without direct access to TebelloReborn's actual code (Pappa
T-only), so its proposed file/module names are informed guesses pending
confirmation in a real Pappa T session. Key scoping calls already made:
start with LinkedIn Easy Apply only (bounded, scriptable flow) and
explicitly fall back to manual for anything else (Indeed's flow varies too
much per employer to generic-form-fill reliably); reuse the same
untrusted-scraped-text discipline already applied to the doc-gen ADR-003
correction if any LLM-driven form interpretation is involved; use
Playwright `storageState` for session/login, not stored credentials.

## 2026-07-28 — What it is, stack, pipeline
**Source:** Pappa T session (cross-project status survey), TebelloReborn's own CLAUDE.md/docs/todo.md/docs/architecture.md
**Status:** active

Fills the gap flagged in `pappa-t.md`'s "Pappa T-only items" entry
(2026-07-26): TebelloReborn ("Career Engine") is a personal job-application
automation pipeline for Tebello — Python 3.11+, SQLite, local Ollama
(`qwen3:8b`), headless Claude Code, Apify (job-board scraping), `fpdf2`. Lives
at `Pappa T/TebelloReborn/` — not its own git repo, just a folder inside the
Pappa T vault repo.

Five-stage MVP pipeline (Phases 1-5 of an original 7-phase plan; phases 6-7
— Playwright auto-submit, tracking dashboard — deferred, not built):

1. **Profile Import** (offline) — `data/profile_seed.json` → SQLite `CandidateProfile`.
2. **Vacancy Fetch** (Apify) — Indeed (`misceres~indeed-scraper`) + LinkedIn Jobs
   (`bebity~linkedin-jobs-scraper`) actors, confirmed live 2026-07-26. PNet/Careers24
   have no dedicated actor — deferred (ADR-002).
3. **AI Matching** (local Ollama, `qwen3:8b`, native `POST /api/generate`, no API key) —
   fails loud, no fallback backend.
4. **Document Generation** (headless Claude Code, `claude -p ... --allowedTools "Read" --output-format json`
   subprocess under Tebello's own Claude subscription, $0 marginal cost) — tailored
   CV + cover letter, exported via `fpdf2`.
5. **Human Review** (offline CLI) — approve/reject/edit; **structural, non-negotiable
   human-approval gate** before anything would leave the system (no auto-submit exists).

**MVP build is complete as of 2026-07-26** — all 54 Build Queue steps done (Phases
0-8), 182 tests passing.

**Reusable gotchas/decisions (public-repo-level, own repo already documents these):**
- **ADR-003** (2026-07-19): dropped OpenRouter entirely, pre-build — routed by
  workload shape instead: cheap/structured scoring → local Ollama (mirrors
  `ai-outreach-agency`'s ADR-004 research stage); quality-sensitive generation →
  headless Claude Code (mirrors `ai-outreach-agency`'s planned-but-not-yet-built
  ADR-003/Build-Queue-A). Neither backend has an Opus-style effort-tier concept —
  each is a single fixed model/invocation.
- **Security correction to ADR-003** (post-build): the ADR's literal
  `--allowedTools "Read,Write"` was a real vulnerability — both doc-gen generators
  embed untrusted scraped job-posting text (`vacancy.description`) into the headless
  agent's instruction, so a prompt-injected posting could make the agent write
  attacker-controlled content to an arbitrary file. Neither generator actually needs
  Write (`pdf_export.py`, trusted Python, does the real file write from the JSON
  `result` field) — corrected to `"Read"` only, plus a `wrap_untrusted_text()` helper
  that delimits untrusted text with explicit "don't follow embedded instructions"
  markers as defense in depth. General pattern worth remembering for any project that
  feeds scraped/external text into a headless-agent instruction string.
- **fpdf2 `multi_cell` gotcha**, found by an offline integration test (not caught by
  any unit test, since every unit test mocked the PDF export call): two non-blank
  lines in a row (e.g. a `## ` heading directly followed by body text) starved the
  next line of width — `FPDFException: Not enough horizontal space to render a single
  character`. fpdf2's default `new_x=XPos.RIGHT` left the cursor at the right margin
  after a `multi_cell` call. Fix: pass `new_x=XPos.LMARGIN, new_y=YPos.NEXT` on every
  `multi_cell` call.
- **Apify payload-shape bug**, caught during a live actor-slug verification pass
  (2026-07-26): `fetch_vacancies()` was sending `{"maxItems": limit}` as the entire
  request body to both actors — not a valid field for either, and neither actor had
  a search title/location to search on. Because HTTP errors were swallowed per-call
  by design, a real run would have silently returned zero results with no visible
  failure. No unit test caught it because every test mocked `requests.post` directly
  rather than exercising a real payload shape. General lesson: mocking the transport
  layer verifies your code calls `requests.post`, not that the payload you send is
  valid against the real API's schema — worth an occasional real-payload smoke test
  against actor/API docs, not just against your own mocks.
- Deliberately did **not** copy `ai-outreach-agency`'s fuller `handoff/` scheduler /
  volume-cap / weekly-report machinery — no documented volume-throttling requirement
  existed for this project, and copying machinery "because the sibling project has it"
  was called out as a judgment call to resist without an actual confirmed need.

**Not carried over (deliberately, per no-company-data discipline):** the migration
convention detail, exact schema/table layouts, and full ADR text stay in
TebelloReborn's own `docs/`/`CLAUDE.md` — this entry is the reusable-pattern summary,
not a mirror of the source docs.
