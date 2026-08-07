# Session Log — TebelloReborn (Career Engine)

> Chronological record of durable context changes. Ready for the
> `post-task` hook once wired up (currently scaffolded, not firing —
> see hub `CLAUDE.md`'s Hooks section); until then, updated manually
> per Hard Rule #11.

---

## 2026-08-07 (latest) — Indeed adapter Phase D: browser.py, judged offline

Resumed via `/continue` from the hub, which reported Phase D as build-ready with no gate
outstanding — correct this time, and worth noting given the last three sessions each had to
correct a stale hub. Phase D of `docs/specs/indeed-submit-adapter.md` (§Amendment A7/A17/A18/C3)
— Phase 21, steps 128–130, TDD throughout. **538 tests passing, was 485. Zero regressions.**
`browser.py` 95% covered; the 6 uncovered lines are the playwright body inside
`authenticated_page()`, which is exactly what A19 exempts.

**The constraint that shaped the whole phase: `playwright` is not installed on this machine and
is not declared until Phase H, yet Phase D is the module that will import it.** Both hold only if
the module's *decisions* never need a browser. So `browser.py` is split — the adapter observes
the page (which iframes exist, whether each is visible, which landmarks it found) and this module
judges what was observed. Nothing in it queries a DOM. That is what let all twelve A7 states be
pinned by unit test today rather than waiting for Phase E's live recon to exercise any of them,
and it follows the precedent `session.py` already set for the same reason.

**Two orderings, each with its own test, same class as Phase C's:**

1. **Expiry is decided before "unrecognized step".** An auth page fails the landmark check too, so
   branch order alone decides whether Tebello is told to re-run the login setup or to debug a form
   that is fine.
2. **A missing session is reported before a missing `playwright`.** Both are true on a fresh
   machine, and "install playwright" is the wrong first instruction for someone who has simply
   never run the login setup — and much the harder of the two to act on.

**Three places the spec left room, and what was chosen instead of defaulting:**

- **No landmark selectors were invented.** A17 requires a URL segment *and* a structural landmark,
  but the live recon only ever verified the segments — it never recorded a selector. `WizardStep`
  therefore stores landmark *names*, which Phase E maps to real selectors, and it refuses to be
  constructed with an empty landmark tuple (that would silently degrade A17 back into the URL
  contract it exists to replace). `WIZARD_STEPS` carries only the two segments recon actually saw;
  the review step was never reached, so it is absent rather than plausibly guessed. Same
  empty-until-known discipline as `eligibility.ADAPTERS`, and the same lesson as the Apify
  payload-shape bug.
- **A7 rule 5 extended to `recaptcha/enterprise/anchor`.** The spec names only `api2/anchor`, but
  rule 1 already pairs both bframe paths and the escalation reasoning ("invisible v3 never renders
  an interactive checkbox") is identical. Extra detection means extra aborts — the safe direction
  for a rule whose whole purpose is to stop rather than proceed.
- **`INDEED_AUTH_MARKERS` was cut down, not filled out.** Recon ran signed in and never saw an
  expired session, so every marker is inferred. A false positive here tells Tebello to re-run a
  login setup that was fine, so a broad `/auth` was dropped as too easy to hit by accident;
  `login_form_present` is the signal that needs no route guess at all, and Phase E confirms the
  remaining two against real expired-session behavior.

**The never-abort tests are the ones that matter most in this file.** Recon established that a
"protected by reCAPTCHA" notice and a zero-sized anchor frame are present on a *healthy* run, so a
detector that treats either as a challenge aborts 100% of runs — seven tests exist to make that
impossible to reintroduce. The Google `/sorry/` check parses host and path separately for the same
reason: `https://za.indeed.com/sorry/viewjob` is not a block page, and a regex loose enough to span
the whole URL is precisely how it would become one.

**C3's step log takes no field values, and cannot.** There is no parameter to pass one through, so
the guarantee is structural rather than a rule someone has to remember at each call site. Its
directory is derived from the session path (`.session/logs/`), so one `SESSION_STATE_PATH` override
moves both and neither can drift outside `.gitignore`'s coverage.

**Known deviation, recorded rather than quietly accepted:** `browser.py` is 397 lines against
`CLAUDE.md`'s documented 300-line file standard. Not split — the spec names this single module and
`submission/db.py` already sits at 370 — but it deserves a deliberate answer at Phase H's closeout.

**Nothing reached the wire this session, and nothing was submitted.** The adapter registry is still
empty, so `career.db`'s 6 approved Indeed vacancies still route to manual.

**Next:** Phase E — the first networked phase of this build, and the one that needs
`tools/indeed_login_setup.py` built first *and* Tebello present to sign in by hand.

---

## 2026-08-07 (later, 3) — Indeed adapter Phase C: the prep-state gate, wired

Resumed via `/continue` straight after Phase B pushed. Phase C of
`docs/specs/indeed-submit-adapter.md` (§Amendment A2/A3/A15) — Phase 20, steps 123–127, four
commits, TDD throughout. **485 tests passing, was 456. Zero regressions.** Coverage on the phase's
three modules: `pipeline.py` 100%, `cli.py` 100%, `eligibility.py` 100%.

It adds no new state. Everything it needed already existed after Phase B; this phase is the wiring
that makes `submission_prep_ready()` actually gate something.

**What landed**

- `pipeline._decide()` consults `submission_prep_ready()` after the adapter lookup. `PENDING_REVIEW`
  joins `NOT_SUPPORTED` in `_OUTCOME_STATUS` as a no-transition outcome — both mean the application
  still needs Tebello's action, differing only in which action.
- `run_submission(batch=)`, and `--all` passes it. A vacancy that would reach a real
  `adapter.submit()` in a batch is recorded as `pending_review` with
  `"auto-submit requires an explicit --vacancy-id"` instead (A15).
- `report_attempt()` gains a `pending_review` branch; `_submit_all()` counts it in its own bucket.
- `eligibility.can_handle()`'s contract records that it is pure and offline, and that an
  external-ATS posting deliberately *passes* it and is declined one layer down by the gate (A1).
- One submission connection now serves both the gate's read and the attempt's write, rather than
  opening a second one to read what the first is about to record.

**Two orderings decided here — each has its own test, because getting either wrong is silent.**

1. **The gate runs before the session check.** Every answer it gives is state `prep-submission`
   already recorded, so none of it needs a live session to read. Session-check-first would report a
   recorded `external_ats` as "no saved browser session — run the login setup": sending Tebello to
   fix something that isn't broken, and burying the one finding that genuinely means "submit by
   hand".
2. **The `--all` refusal is checked last.** A vacancy that also has a real gate reason hears that
   instead — "run `prep-submission`" beats "use an explicit `--vacancy-id`" for someone who has to
   prep first anyway. Refusal-first would give every un-prepped vacancy in a batch the wrong next
   step.

**A15 was confirmed with Tebello before any code was written**, since the spec's own §Open Items
item 5 exists precisely so the behavior isn't a surprise: submitting the 6 approved Indeed vacancies
will be six deliberate commands. The rationale is that the accepted account-risk exposure is
per-account, and six real applications in ninety seconds is a materially different risk from six
deliberate single runs — refusing needs no tuning and cannot be mis-tuned, where a backoff policy
would need real observed behavior to tune against.

**One thing worth carrying forward:** `pending_review` and `not_supported` leave the vacancy in the
*same* state, so the CLI's wording is the only thing distinguishing them for the operator. The
wording test asserts `"FAILED"` is absent as well as the right substrings being present — without a
dedicated `report_attempt()` branch the detail printed under a FAILED label, which is the right
words under the wrong verdict and would have passed a naive substring assertion.

Still offline. Nothing on the wire, no `playwright` dependency, the adapter registry still empty —
every approved application routes to manual today. **Phase D is next**: `src/submission/browser.py`
(session load, expiry detection, CAPTCHA detection, the combined navigation-state check, step
logging).

---

## 2026-08-07 (later) — Indeed adapter Phase B: screening-question state

Picked up the first thing ADR-004 unblocked, the same day it landed. Phase B of
`docs/specs/indeed-submit-adapter.md`: `submission_preps` and `screening_questions`, the
`pending_review` outcome, the widened `submissions.outcome` CHECK, and `submission_prep_ready()`.
Five steps, four commits, offline throughout — nothing on the wire, no `playwright` dependency, the
adapter registry still empty. **456 tests passing, was 399, zero regressions.**

**The design point worth keeping.** `all_questions_reviewed()` — the name the spec started with —
could not have worked, and the amendment's A2 is why: counting `screening_questions` rows cannot
distinguish "prep never ran" from "prepped, and this posting genuinely has no questions". Both are
zero rows and exactly one of them is submittable. Prep state is now *recorded* in its own
append-only table, and the absence of a prep row is the one state that genuinely is an absence.
`submission_prep_ready()` returns the whole gate decision as a `PrepReadiness`, including which
outcome `pipeline.py` should record and which command to tell the operator to run.

**Deviated from the spec on one point, deliberately.** A4 resolved the `submissions.outcome` CHECK
as a DDL edit plus a guard that refuses loudly — correct when it was written, because the live
database has no `submissions` table yet and `CREATE TABLE IF NOT EXISTS` would therefore produce the
right shape. But on a database where `submit` had run once, that combination fails at `init_db()`
with no automated remedy. ADR-004 landed in between and makes the remedy cheap, so Phase B ships
`src/submission/migrations.py` version 1 — the first table rebuild this project has written, and the
first consumer of the callable payload the ADR's amendment added for exactly this case. A4's own
closing note already prescribed this rebuild *if the guard fires*; the only change is doing it before
it can. Its "globally-unique `user_version ≥ 5`" wording is superseded — version 1, per-module.

**One thing the rebuild had to learn on its own.** The runner's `_already_satisfied` shortcut is
scoped to `ADD COLUMN` strings and never to a callable, which is right — no other migration form has
a general "already done?" predicate. The consequence is that a rebuild running against a fresh
database, where the baseline `CREATE TABLE` has already produced the widened shape, has to read
`sqlite_master` and decline for itself. Without that early return every new install would rebuild a
table it had just correctly created.

**Verified against a copy of the live `career.db`, never the real file** (sqlite3 backup API, not a
file copy — a raw copy of a live WAL-mode database can capture a torn state): 10 vacancies, 10
approvals, 43 `generation_log` rows and the profile intact, `integrity_check = ok`, `user_version`
still frozen at 4, three tables created with the widened CHECK, and all 6 approved vacancies gating
to `pending_review` with "never prepped" — which is the correct answer, since none has been prepped.

Next is **Phase C**: wiring `pending_review` and the prep-state gate into `pipeline.py`, plus the
`--all` auto-submit refusal. Offline, and it adds no new state — it consumes what Phase B built.

---

2026-08-07 codex-review docs/decisions/ADR-004-schema-migration-ledger.md: ran

## 2026-08-07 — ADR-004 accepted, Codex-reviewed, and built: the schema migration ledger

Both open questions answered by Tebello: `vacancy_search`'s baseline **is** fixed in the same change
(§6), and `/codex-review` **was** run first. The skill's path guard refused the file — it is
hard-scoped to `docs/specs/`, matching Hard Rule 13's literal wording — so the identical review
instruction and payload discipline went through a direct `codex exec` call, sending that one file and
nothing else. Worth deciding whether the guard should widen to `docs/decisions/`, since this is the
second time an ADR has wanted the gate.

**The Codex pass earned its place, again — third consecutive review to return something that would
have failed at runtime, and this one hit the ADR's own motivating case.** Verified against this
machine's sqlite3 3.49.1 rather than accepted on the review's word: a migration payload of `str`
cannot express Phase B's table rebuild, because `Connection.execute()` raises `ProgrammingError` on
multi-statement SQL. Worse, and not in the review: `executescript()` is no escape hatch either — it
issues an **implicit COMMIT before running** (`in_transaction` True → False, confirmed), so the ADR's
"commits once at the end" guarantee would have evaporated silently, leaving a half-applied rebuild
with a ledger row claiming success. Fixed as A1 (payload is `str | Callable[[sqlite3.Connection],
None]`) and A2 (one `BEGIN IMMEDIATE` per migration; DDL and its ledger row commit together or not at
all). 13 accepted changes, 3 declined, in the ADR's `§Amendment`.

**Built the same session — Phase 18, steps 107–117, ten commits.** All five modules delegate to
`src/shared/migrations.py`; every applied migration records into
`schema_migrations(module, version, applied_at)`; version numbers are per-module and
`PRAGMA user_version` is frozen, never read or written. `vacancy_search`'s baseline
`CREATE TABLE vacancies` now declares `score`/`strengths`/`weaknesses`/`recommendation` — the one
provably wrong-shaped baseline, and what made the Phase 17 regression a crash rather than a cosmetic
problem. **399 tests passing, was 362, zero regressions.**

**A second finding surfaced from making the rebuild test actually pass, not from review:**
`PRAGMA foreign_keys` is a **no-op inside a transaction**, so SQLite's documented "turn foreign keys
off first" rebuild step is unavailable to a migration the runner has already wrapped.
`PRAGMA defer_foreign_keys` is the one settable mid-transaction. Phase B should follow
`TestPhaseBShapedRebuild` in `tests/unit/test_shared_migrations.py` rather than the SQLite docs
verbatim — that test models the real `submissions.outcome` CHECK widening, with a populated child
table and a live foreign key, and covers the failure path too (a rebuild that dies after the rename
rolls back whole, leaving no `submissions_new` and nothing recorded).

**Verified against a copy of the live `career.db`, never the real file** (sqlite3 backup API,
read-only on the source). Exactly as §4 predicted with no special adoption code path:
`vacancy_search` 1–4 skip-and-record (columns already present), `profile` 5–6 apply, the frozen
counter stays at 4, `integrity_check` ok, `foreign_key_check` clean, and all data intact — 10
vacancies (10/10 scored, 6 approved / 4 rejected), 10 approvals, 43 generation-log rows, 1 profile. A
second init pass in reversed module order was a clean no-op. `get_profile()` raises its actionable
"re-run import-profile" error, as designed.

**Unchanged and still pending:** the real `career.db` has not been migrated — that happens on the
next `init_db()` from any command, after which `career-engine import-profile --file
data/profile_seed.json` must be re-run to populate the contact details. Two byte-identical backups
still exist; one should be deleted once Tebello picks which to keep.

Session housekeeping: archived `Cont-"ADR-004 migration ledger, written & pushed"` and
`Cont-"TebelloReborn vacancy pipeline dashboard"` at Tebello's confirmation. Shared-core marketplace
clone: 0 commits behind upstream.

## 2026-08-07 — ADR-004 written: schema migration ledger (PROPOSED, not decided, no code changed)

`docs/decisions/ADR-004-schema-migration-ledger.md` — the ADR the previous session's Open Item
asked for, written before Phase B rather than inside it. **Status is Proposed and two questions in
it are unanswered**, so no Executor was dispatched and nothing under `src/` moved. 362 tests still
passing, unchanged.

**The finding that changed the answer.** The Open Item offered two routes: a shared runner, or fold
migrations into each baseline and install `profile`'s guard everywhere. Reading the code ruled the
second one out for what comes next. The `profile` guard gates on `PRAGMA table_info` — it only
understands `ADD COLUMN`. **Phase B's central migration is a table rebuild**: spec §Amendment A4
adds `pending_review` to the `submissions.outcome` CHECK, and SQLite cannot alter a CHECK in place,
so it is the 12-step create/copy/drop/rename. No column-existence predicate can gate that. Rolling
the guard out verbatim would leave Phase B inventing a third migration mechanism inline, inside a
feature build, for a rule Hard Rule 6 names explicitly.

**Proposed instead:** a `schema_migrations(module, version, applied_at)` ledger and one shared
runner in `src/shared/migrations.py`. `user_version` is a single-writer counter being used as a
multi-writer applied-migrations record — it cannot answer *"has this migration, from this module,
already run on this database?"*, because it stores one number and not a set. Every symptom traces
back to that. With a ledger keyed by `(module, version)` the namespace stops being shared, version
numbers become per-module, Hard Rule 6's globally-unique-≥5 decree retires, and `submission/` can
finally have a `migrations.py` like every other module.

**Adoption of existing databases needs no special code path.** Keep the `ADD COLUMN` skip but
*record* it as applied, and the ordinary loop is already correct on a legacy file — no
`user_version` archaeology, no one-shot adoption script. On the live `career.db`: `vacancy_search`
1–4 skip-and-record, `profile` 5–6 apply. This is provably safe because **all six migrations in
project history are `ADD COLUMN`**, so a pre-ledger database cannot be carrying an unrecorded
migration of any other form.

Facts verified directly against the real database rather than carried over from `docs/todo.md`:
`user_version = 4`; `vacancies` has all four match columns and 10 rows; `candidate_profile` has no
`email`/`phone` and 1 row; `generation_log` 43 rows; `approvals` 10 rows; **no `submissions`
table** — Stage 6 has still never run against it. Also checked: nothing outside the test suite
reads `user_version` (`tools/dashboard_server.py` included), and exactly four test assertions would
need converting to ledger equivalents — none deleted, each listed by name in the ADR's Consequences.

The ADR carries an 11-step atomic TDD Build Queue, fully offline, with a verify-against-a-copy step
before anything touches the real `career.db`. Open for Tebello: whether to fix `vacancy_search`'s
baseline `CREATE TABLE` in the same change (recommended — it is the one provably wrong-shaped
baseline, and what made the Phase 17 regression fatal rather than cosmetic), and whether to run
`/codex-review` on an ADR given Hard Rule 13 names `docs/specs/` only.

Session housekeeping: renamed a stale `Continuation` session to
`Cont-"Hub session-end, vault push & staleness audit"`, and archived
`Cont-"TebelloReborn Stage 6 submission core"` at Tebello's confirmation — Phase 16 closed out
2026-08-06. Shared-core marketplace clone checked: 0 commits behind upstream.

## 2026-08-07 — Indeed submit adapter Phase A built (contact details + the project's first migrations)

Phase A of `docs/specs/indeed-submit-adapter.md` (§Amendment A5): `CandidateProfile` gains `email`
and `phone`, backed by `profile/migrations.py` versions **5 and 6** — the first migrations this
project has written since Hard Rule 6 was recorded. `9d4ee17` RED, `379a4b2` GREEN. **362 tests
passing, was 344, zero regressions.** Phases B–H are not started.

Real values came from `data/Tebello_Lelosa_Master_CV_2026.md` (`tlelosa@gmail.com`, `078 481 8711`)
after Tebello confirmed the email in-session. A test asserts the seed and the CV never drift apart —
an employer sees both on the same application, and nothing else in the pipeline would notice a
contradiction, since the CV is hand-authored and the form is filled from the database.

**The phase introduced a real regression, and the integration suite caught it — no unit test did.**
Same class of gap as the Phase 7 fpdf2 bug and the Apify payload-shape bugs: every unit test builds
its own `tmp_path` database through a single module's `init_db()`, so none of them exercise two
modules initialising the *same* database in the order a real install uses.

- **Cause.** `profile` owns the highest migration versions (5–6), and CLAUDE.md documents
  `import-profile` as the *first* command. On a fresh database `profile.init_db()` therefore
  advanced the shared `user_version` 0 → 6 before `vacancy_search.init_db()` ever ran. Its
  migrations 1–4 were then skipped by `if version > current` — and because its baseline
  `CREATE TABLE` omits those columns, `vacancies` ended up with no `score`/`strengths`/`weaknesses`/
  `recommendation` at all. First read: `IndexError: No item with that key`. Every new install.
- **Fix, deliberately scoped to `src/profile/`.** Schema state, not the counter, is the source of
  truth. `email`/`phone` sit in profile's baseline `CREATE TABLE` *as well as* in migrations 5/6,
  and `apply_migrations` skips an `ADD COLUMN` whose column already exists, advancing `user_version`
  only for migrations it actually ran. A fresh database reaches the right shape while staying at
  version 0, leaving the low numbers free for `vacancy_search`. Two regression tests lock both init
  orderings and assert they converge on identical schemas.
- **Still armed elsewhere — carried forward as an Open Item.** `vacancy_search`, `doc_gen` and
  `review` all still use the counter-only `apply_migrations`, and `vacancy_search`'s baseline still
  omits its own migrated columns. Nothing hits it today only because `profile` no longer advances
  the counter on a fresh database. **The next module to add a migration re-introduces it, and Phase
  B is exactly that.** Redesigning a mechanism Hard Rule 6 names explicitly does not belong inside a
  feature build, so it wants its own ADR first.

The live `career.db` was **not** migrated — it is still at `user_version = 4`. The whole path was
verified against a copy instead: 4 → 6, both columns added, all 10 vacancies and 6 approved
applications intact, the pre-migration row raising its actionable "re-run import-profile" error, and
`import-profile` repopulating cleanly.

Two housekeeping notes. `.gitignore` gained `*.db.backup-*` — `*.db` does **not** match
`career.db.backup-pre-phase-a-2026-08-07`, because the timestamp suffix means the filename doesn't
end in `.db`, so a `git add -A` would have committed a full copy of the live career data. And
**this session ran concurrently with another one working the same item**: `6c7058e` landed
mid-session, taking its own `career.pre-migration-5-6-20260807.db` backup (sqlite3 backup API,
integrity-checked — the better-made of the two) and rewriting the same `docs/todo.md` paragraph this
session then had to re-read and reconcile. Two byte-identical backups now exist; one should be
deleted once Tebello picks which to keep.

## 2026-08-07 — Indeed submit adapter: Codex fold-in complete, spec now build-ready

Hard Rule 13's gate closed on `docs/specs/indeed-submit-adapter.md`. The `/codex-review` from
earlier the same day had returned real findings that were explicitly left unresolved; this session
folded them into a dated §Amendment (same A/B/C convention `submission-core.md` established) before
any Executor is dispatched. **22 accepted changes (A1-A22), 6 clarifications, 4
considered-and-declined. No code written.**

The four gaps the hub queue named, resolved concretely rather than acknowledged:

- **`can_handle()` (A1)** is now pure, offline and side-effect-free — a `urlsplit` check on
  platform + host + `/viewjob` path, nothing more. Every live action moved to
  `inspect_apply_flow()`, deliberately **outside** the `SubmitAdapter` Protocol, called only by
  `prep-submission`. This matters more than it first looks: `eligibility.get_adapter()` runs
  `can_handle()` on *every* `submit` invocation including `--manual` and every `not_supported`
  case, so a networked predicate would have opened a browser on paths that submit nothing.
- **Question drift (A6)** is a sha256 fingerprint over `norm(text) | field_type | required |
  norm(options)`, compared as a **set** — order and position deliberately excluded (a reordered
  form is the same form), aborting in *both* directions, including a reviewed question that
  vanished.
- **CAPTCHA detection (A7)** is five specific abort states (visible `bframe` iframe, challenge-titled
  iframe, hCaptcha challenge frame, `google.com/sorry/`, a visible `api2/anchor` checkbox) and three
  explicit **never-abort** states — the "protected by reCAPTCHA" notice and the `.grecaptcha-badge`
  are normal and present on every healthy run, so conflating them with a rendered challenge would
  have aborted 100% of runs.
- **`prep_failed` (A3)** was **deleted rather than defined.** Prep attempts no submission, so
  recording its failure in `submissions` would put non-attempts in an attempt log. Prep state moved
  to a new `submission_preps` table whose seven statuses also fix the ambiguity Codex found in
  `all_questions_reviewed()` — zero question rows meant both "genuinely no questions" and "prep
  never ran", and only one of those is submittable. Renamed `submission_prep_ready()`.

**Four findings came from reading the code and the live `career.db`, not from Codex** — two would
have failed at runtime as specced:

- **A5 — `email`/`phone` need real migrations.** The spec claimed no DB migration was needed, "same
  precedent as `VALID_PLATFORMS`/`VALID_STATUSES`". False analogy: those validate *values* in an
  existing unconstrained column, while these are **new columns** on the real `candidate_profile`
  table (verified: `id, name, region, skills, experience, target_titles, industries,
  salary_floor`). `upsert_profile()` writes by name and would have died on `no such column: email`.
  Now migrations **5 and 6** in `profile/migrations.py` — globally-unique per Hard Rule 6, since
  `vacancy_search` holds 1-4 and the live DB is at 4. This is the first migration the project has
  written since that rule was recorded, and it is exactly the case the rule anticipated.
- **A4 — the `submissions.outcome` CHECK trap, with a closing window.** Verified against the live
  `career.db`: `user_version = 4`, tables are `candidate_profile`/`vacancies`/`generation_log`/
  `approvals` — **no `submissions` table**. Stage 6 has never run against it. So editing the inlined
  CHECK to admit `pending_review` works cleanly *today*, but `CREATE TABLE IF NOT EXISTS` silently
  keeps the old 3-value constraint the instant anyone runs `submit` once first, and the failure
  would surface as a CHECK violation at insert time, far from its cause. Phase B adds the value
  **and** a DDL-drift guard in `init_db()` that reads `sqlite_master.sql` and refuses loudly.
- **A9 — `prep-submission` is a network command in two senses.** `run_claude_code()` shells to
  `claude -p`, which needs connectivity. ADR-003's "local subprocess" is about rate-limiting and
  cost, not offline capability; the spec's "local, network-optional drafting pass" was wrong. A
  throttled draft now still persists the extracted questions with `drafted_answer = NULL`, so a
  throttle costs the draft, not the recon.
- **A16 — no PDF path exists in the database.** `generation_log` has no path column, so the adapter
  must reconstruct `pdf_export`'s `{company}_{id}_{cv|cover_letter}.pdf` convention. Phase G
  promotes it to a shared `resolve_export_paths()` rather than duplicating the format string into
  the adapter, which is how the two would drift apart.

Other changes worth carrying forward: every employer-authored question is now reviewed (A10 deletes
the `auto_fillable` "matched confidently" concept — untestable as written, and a location field
auto-filled from `profile.region` is still an answer Tebello's name goes on); sensitive question
classes (compensation, work-authorization, demographic) are **never LLM-drafted** at all (A11);
ambiguous post-submit states record `UNCONFIRMED:` and **block further automated attempts** rather
than reporting a retryable `failed` that would invite a duplicate application (A13/A14); and
`submit --all` refuses auto-submit entirely in this build (A15) — real applications go out one at a
time by explicit id, which is a policy answer to the account-risk exposure rather than an untuned
backoff engine.

Declined on the record: Playwright trace/video capture (C3) — application pages carry contact
details and CV content, and a trace is a rich artifact of all of it outside `.gitignore`'s current
coverage; replaced with a plain-text step log under `.session/logs/` carrying no field values.

**Next:** Phase A. Blocked on Tebello's real `email`/`phone` values for `profile_seed.json`, and
`career.db` should be backed up first — migrations 5/6 auto-apply on the next `init_db()` from any
command, including `career-engine list`.

---

## 2026-08-07 — Indeed submit adapter: spec written, screening-question review scope discovered

Unblocked from hub `docs/todo.md` #1 by Tebello answering the two `submission-core.md` Open Items
directly in a hub `/continue` session: platform = **Indeed's own apply form only**; ToS/account-risk
exposure **explicitly accepted**. A third decision (`playwright` as a new runtime dependency) was
also confirmed.

Before writing the Build Queue, did a live `claude-in-chrome` walkthrough of Indeed's real
SmartApply flow (signed in as Tebello, one of the 6 approved vacancies) rather than guessing
selectors — this project's own Apify-payload-shape lesson. **Nothing was submitted.** Found: the
flow is a separate multi-step app (`smartapply.indeed.com`) with per-step URLs; resume selection
defaults away from the generated CV; the flow is reCAPTCHA-protected (CAPTCHA-abort is now a hard,
non-negotiable design rule — never solve/defeat it, distinct from the already-accepted ToS risk);
and **employer screening questions are real, per-posting, and often open-ended free-text** (one
posting asked for an essay describing a recent project). That last finding reshapes the whole
adapter: it can't be a pure deterministic form-filler. Tebello decided screening-question answers
get **LLM-drafted (headless Claude Code, `wrap_untrusted_text()`-wrapped) but held for his explicit
per-question approval** before any submission — never auto-answered unsupervised.

Wrote `docs/specs/indeed-submit-adapter.md`: three new CLI commands
(`prep-submission`/`review-questions`/`submit`), a new `screening_questions` table, a new
`pending_review` outcome distinct from `not_supported`, `CandidateProfile` gaining `email`/`phone`
(neither existed — verified, not assumed), and a phase-level Build Queue. Ran `/codex-review` per
Hard Rule 13 — real second opinion, not a rubber stamp: flagged `can_handle()` as accidentally a
networked/browser action (architectural mismatch with the cheap-predicate contract), missing drift
policy for questions changing between prep and submit, an underspecified CAPTCHA-detection
criterion, missing `prep_failed` outcome-table semantics, and several failure modes (duplicate
submission risk, session expiry mid-wizard, ambiguous success detection). Folded in as the spec's
own advisory section, not yet resolved into the design — that's the next session's first task before
any executor is dispatched.

**No code written this session** — Hard Rule 2 (plan before code >2 files) and Hard Rule 10 (stop
and ask when acceptance criteria are unclear) both applied throughout; three separate
`AskUserQuestion` checkpoints resolved the platform, risk, dependency, and screening-question-review
decisions before the spec was drafted.

**Last completed:** Indeed submit adapter spec drafted + Codex-reviewed (this entry).
**Next task:** Resolve Codex's spec-level findings (concrete CAPTCHA-detection states, question-drift
policy, `can_handle()` static/live split, `prep_failed` table semantics) before dispatching a build
session. Real `profile_seed.json` email/phone values are also needed first (spec Open Item 1).
**Known risks:** None new beyond what the spec itself now documents (reCAPTCHA, screening-question
variability, account-risk — all explicitly accepted or hard-ruled-around, not hidden).
**Blockers:** Build session needs the spec's Open Items answered first (real contact info, which
posting is the Phase G smoke-test target, login-setup script timing).

## 2026-08-06 — Stage 6 submission core built (Phase 16, steps 81–102)

Built the platform-agnostic half of Stage 6: status vocabulary, the `submissions`
attempt log, session-state path handling, capability-based adapter dispatch, and
outcome recording. **249 → 344 tests, zero regressions, 100% coverage on
`src/submission/`.** No `playwright` dependency, no browser binary, nothing on
the wire. Spec: `docs/specs/submission-core.md`.

**The hub spec it came from targeted the wrong platform.** It scoped the build to
LinkedIn Easy Apply only, with Indeed explicitly out of scope. LinkedIn was
dropped from this project on 2026-08-01 (actor `403 actor-is-not-rented`, renting
declined, `_normalize_linkedin()` and the POST block removed) — three days before
that spec was written — and all 10 rows in `career.db` are Indeed. Built as
written it would have shipped a feature able to submit nothing. Scope became the
core; the adapter is a separate task, and it is blocked on Tebello, not on code.

**Codex review found a real contradiction in the spec, pre-build.** Acceptance
criterion 1 refused anything not `approved`, while the transition table allowed
`submission_failed → submitted` and called failures retryable — the retry path was
unreachable from the only CLI that would use it. Resolved by admitting
`submission_failed` to the gate: it is reachable *only* from `approved`, so the
invariant enforced is "this vacancy passed the human gate," not "it is currently
in one exact state." Nine further points folded in as Amendment A1–A9/B1–B6/C1–C3.

**Two corrections to the pre-build verification notes:**

- **No migration was needed after all.** A net-new table's `CREATE TABLE` belongs
  in `init_db()` per this project's own convention, and `vacancies.status` is
  unconstrained `TEXT`, so extending `VALID_STATUSES` is Python-level only —
  exactly the step-59 `VALID_PLATFORMS` precedent. The shared-`user_version` trap
  is real but this build never steps in it. `src/submission/` deliberately has
  **no** `migrations.py`, since an empty stub invites a `(1, …)` entry that would
  be silently skipped forever. The rule is now written into `CLAUDE.md` Hard Rule 6.
- **`.gitignore` genuinely did not cover the session file** — that one held.
  `.session/` added, with a test that reads `.gitignore` so the protection cannot
  regress silently.

**Two deviations from the spec, both recorded in `docs/todo.md`:** steps 90–91
landed as one commit (the `.gitignore` entry alone leaves the suite failing
collection, and Hard Rule 4 requires green tests before a commit); and step 97's
CLI moved from `main.py` to `src/submission/cli.py` after inlining it pushed
`main.py` to 354 lines, past this project's own 300-line standard — matching how
`run_review_gate` already lives in `src/review/cli.py`.

**Hard Rule 1 is now structural at two layers**: `run_submission()` gates on
`vacancy.status` (never on the presence of an `approvals` row, as
`src/review/cli.py`'s closing comment demands), and adapters never write to the
database or transition status, so no future adapter can route around the gate.

**Found and left unfixed, deliberately:** `black . && ruff check .` — the gate
this project's own CLAUDE.md documents — no longer passes on a clean checkout
under this machine's tooling. It reformats 17 untouched files, 7 of them inside
the Hard-Rule-12-protected `_archive_qwen_prototype/`, and `ruff` reports 10
pre-existing errors. Worked around by scoping both tools to the files actually
changed. A repo-wide reformat is its own decision and its own commit; it should
not ride along inside a feature build. Logged as a Known Issue.

**Next:** the site adapter, blocked on two answers from Tebello — which platform
gets the first adapter, and an explicit ToS/account-risk acknowledgement. Neither
is a coding question.

## 2026-08-06 — codex-review submission-core.md: ran

## 2026-08-01 — Review-gate bug fix: skip gate when doc-gen doesn't reach asset_ready

Real bug found 2026-08-01: a CV generation timeout (headless `claude -p`) left a vacancy at
status `scored` with `cv_text`/`cover_letter_text` still `None`, but `_run_pipeline_for_vacancy()`
in `src/main.py` sent it to the human review gate anyway — a human would see "CV: None / Cover
Letter: None" presented for approval. `run_doc_gen` only transitions status to `asset_ready` if
both documents generate successfully, so the fix checks that status before calling
`run_review_gate` and skips (with a diagnostic print pointing at `generation_log`) otherwise.
Built TDD: `6bbd0d8` (RED — `TestDispatchRun` asserts the mock's `asset_ready_vacancy.status` is
`asset_ready`, exposing the missing guard), `1403c47` (GREEN — the status-check guard in
`_run_pipeline_for_vacancy`). Full suite: 239 passing, zero regressions.

## 2026-08-01 — Live vacancy pipeline dashboard (dev tool, not pipeline code)

Added `tools/dashboard_server.py` + `tools/dashboard.html` (`1be39ca`): a
local stdlib-only dev server that polls `career.db` every 4s and renders
vacancies as a kanban board across the 5 pipeline statuses. `asset_ready`
cards get Approve/Reject buttons that call the *same* review-gate DB
functions `src/review/cli.py::run_review_gate()` uses — `save_approval()`
committed before `update_vacancy_status()` — so the dashboard is a second
front end onto the real human-approval gate, not a bypass of it (Hard
Rule #1). Launched via the Browser pane's `preview_start` using a new
`.claude/launch.json` in this project folder.

Not part of the Build Queue or MVP pipeline — a visualization/control aid
only, requested ad hoc. Also added `*.db-shm`/`*.db-wal` to `.gitignore`
(the dashboard's concurrent read access started generating these SQLite
WAL sidecar files; they were previously absent because nothing else read
`career.db` outside of a single process at a time).

No vacancies have reached `asset_ready` yet (all 20 currently-stored
vacancies are `new`), so the Approve/Reject buttons are wired but
untested against a real click — verify once matching + doc-gen has run.

## 2026-07-31 — W1/W2 reviewer nits fixed, PNet/Careers24 build merged to master, PNet mode flipped to auto

The PNet/Careers24 Automated Discovery build (worktree `agent-a6eb29f112cbc6764`,
steps 63–80) was reviewer-approved "APPROVE WITH NITS" — no blockers, two
follow-ups. Both fixed TDD in the same worktree before merge:

- **W1 (extraction-prompt untrusted-text wrap).** `build_extraction_prompt()`
  embedded `raw_page_text` (untrusted, scraped job-posting text) directly
  into the Ollama extraction prompt with no defense-in-depth wrap — the same
  sink shape as `vacancy.description` in `doc_gen`'s `cv_generator.py`/
  `cover_letter_generator.py`, which already uses `runner.wrap_untrusted_text()`.
  RED test asserted the wrapped-text markers appear in the prompt output
  (`4633dd8`); GREEN applied `wrap_untrusted_text()` to `raw_page_text`
  before embedding it (`a5c3285`).
- **W2 (normalize_url over-strips Indeed's `?jk=`).** `normalize_url()`
  stripped the entire query string before building the
  `(company, title, normalize_url(url))` dedupe key — since Indeed's
  canonical job identity lives in `?jk=<id>`, every Indeed URL collapsed to
  the same bare path, silently merging genuinely distinct postings (e.g.
  two reqs from the same employer, same title). RED test asserted
  `?jk=1` and `?jk=2` normalize to *different* strings, while `?jk=1` and
  `?jk=1&utm_source=x` still normalize the same (`5ffc010`); GREEN switched
  `normalize_url()` to an allowlist-based strip of only known tracking
  params (`utm_source`, `utm_medium`, `utm_campaign`, `utm_term`,
  `utm_content`, `gclid`, `fbclid`), preserving `jk` and any other
  significant identifier param (`6068db4`).

`docs/api-patterns.md` updated to document both behaviors in place (the
extraction-prompt untrusted-text wrap, and the tracking-param allowlist).
Full suite: 232 passing, zero regressions, after both fixes.

Worktree branch fast-forward merged into `master` (`9319b5a` — no separate
merge commit needed, `master` was already the merge-base). Full suite
re-run against merged `master`: 232 passing. Worktree removed
(`git worktree remove`) after the merge was confirmed clean.

Per Tebello's earlier in-browser confirmation that
`https://www.pnet.co.za/jobs/operations-foreman/in-gauteng` (bare path, no
query string) renders a working PNet results page with real matches,
`data/discovery_config.json`'s `pnet.mode` was flipped from
`"manual_pending_verification"` to `"auto"` as its own atomic commit on
`master` (`bd72266`) — resolves Open Item 4 from the Amendment. Verified
this doesn't break the PNet-fallback tests: they all construct their own
`tmp_path` discovery-config fixtures rather than reading the real
`data/discovery_config.json`, so the flip is fully test-isolated (232
still passing after the flip).

## 2026-07-29 — codex-review pnet-careers24-coverage.md: ran

## 2026-07-29 — codex-review pnet-careers24-coverage.md: warned (codex exec argument-list-too-long, exit 126)

## 2026-07-26 — MVP build complete (Phases 0–7)

All 54 Build Queue steps in `docs/specs/mvp-pipeline-build.md` are done —
the 5-stage pipeline (Profile Import → Vacancy Fetch → AI Matching →
Document Generation → Human Review) is wired end-to-end behind the
`career-engine` CLI, with the mandatory human approval gate as the terminal
state. No auto-submission exists past `approved` (Hard Rule #1).

- Phases 0–3 (scaffolding, shared rate-limiter, Profile Import, Vacancy
  Fetch) and Phase 3.5 (ADR-001, ADR-002) were completed in earlier
  sessions.
- ADR-003 (accepted 2026-07-19, ahead of ADR-001/002 for timing reasons)
  dropped OpenRouter from this project entirely: AI Matching routes to
  local Ollama (`qwen3:8b`), Document Generation to headless Claude Code
  (`claude -p`) — both fixed, flat-cost backends with no model/effort
  routing table.
- Phase 4 (AI Matching) and Phase 5 (Document Generation) landed with two
  corrective fixes caught mid-build rather than assumed away:
  - The `vacancies` table had no score/rationale columns when Phase 4 was
    actually built (ADR-003 §2 had assumed otherwise) — added via a proper
    migration (`vacancy_search/migrations.py` versions 1–4) plus
    `save_match_result()`, not by editing the committed baseline schema.
  - ADR-003 §3's literal `--allowedTools "Read,Write"` for the headless
    Claude Code runner was a real vulnerability: both generators embed
    untrusted scraped `vacancy.description` text in the instruction, so
    Write access would let a prompt-injected posting make the agent write
    attacker-controlled content to an arbitrary path. Corrected to
    `"Read"` only, with `runner.wrap_untrusted_text()` added as defense in
    depth. ADR-003 itself was left unedited as the historical record; the
    correction is noted in `docs/todo.md`.
- Phase 6 (Human Review) required Reviewer sign-off before the RED/GREEN
  commits landed (steps 48–49), per the mandatory gate around this stage —
  `review/cli.py` guarantees `save_approval()` is committed before the
  vacancy status transitions, so a failure after persistence never leaves
  an "approved" vacancy with no recorded decision.
- Phase 7 (this session): wired `src/main.py` — the `career-engine` CLI's
  5 subcommands (`import-profile`, `fetch-vacancies`, `list`, `run`,
  `run-all`) dispatching through matching → doc-gen → review in order,
  stopping a `run-all` batch cleanly on the review gate's Quit choice
  instead of crashing it. Added `Vacancy.cv_text`/`cover_letter_text` as
  transient (non-persisted) fields so `run` hands the review gate the
  exact generated text instead of a second generation round-trip.
  - Wrote `tests/integration/test_full_pipeline.py` — the first test in
    this project to exercise the real PDF export path (every prior unit
    test mocks it). That surfaced a genuine bug in `pdf_export.py`:
    fpdf2's `multi_cell` defaults to leaving the cursor at the right
    margin, so two non-blank lines in a row (e.g. a heading directly
    followed by body text) starved the next line of rendering width and
    raised `FPDFException`. Fixed by resetting the cursor
    (`new_x=XPos.LMARGIN, new_y=YPos.NEXT`) after every line — exactly
    the class of bug an integration test exists to catch.
- Phase 8 (this session): wrote `docs/api-patterns.md` (Ollama, headless
  Claude Code, Apify — no OpenRouter section) and this file.

**Known open items carried forward** (see `docs/todo.md`):
- Apify actor slugs (`misceres~indeed-scraper`,
  `bebity~linkedin-jobs-scraper`) are unconfirmed placeholders — verify
  against the live Apify Store before the first non-`OFFLINE_MODE`
  `fetch-vacancies` run.
- PNet/Careers24 coverage, the post-MVP auto-submit phase, and the
  tracking dashboard are all deferred, not scheduled.
