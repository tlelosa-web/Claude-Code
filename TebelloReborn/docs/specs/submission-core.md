# Spec: Submission Core (platform-agnostic, Stage 6 foundation)

> Status: planned, not implemented.
> Author: Planner · Date: 2026-08-06
> Adds the foundation of **Stage 6 (Auto-Submit)**, listed as deferred in `CLAUDE.md`'s
> Pipeline Stages and as "Phase 6 (post-MVP numbering)" in `docs/todo.md`'s Future section.
> Step numbers continue the Build Queue from step 80 (the last step of
> `docs/specs/pnet-careers24-coverage.md`'s Automated Discovery amendment) — `docs/todo.md`
> remains the source of truth for numbering, this file for per-step detail.
> **Supersedes** the hub-written spec `Claude-Code/docs/specs/2026-08-04-tebelloreborn-playwright-auto-submit.md`
> for everything it scoped. That spec was written from a cloud session with no access to this
> code and flagged its own paths as guesses; §"What the hub spec got wrong" below records every
> divergence rather than silently rewriting it.
> Ports Tebello's 2026-08-06 decision to **build the platform-agnostic core first** and leave the
> site-specific adapter as a separate, later task.

---

## Goal

Give this project a **submission stage that records outcomes and refuses to guess** — the durable,
offline-testable half of Stage 6 — without adding Playwright, a browser binary, or any site-specific
automation.

After a human approves an application (Stage 5, unchanged), `career-engine submit` can:

- confirm the vacancy is genuinely `approved` before doing anything at all,
- determine whether an auto-submit adapter exists for that vacancy's platform,
- when none exists — **every case in this build** — route the application to manual submission,
  visibly and on the record, instead of silently mishandling it,
- record the submission attempt and its outcome in the database,
- advance the vacancy's status to reflect what actually happened.

The browser automation itself is deliberately not in this build. What ships here is the contract the
adapter will plug into, plus the guarantee that an application can never reach a submission path
without having passed the human gate.

### Why the core comes first (and is not busywork)

The core is the part that is *knowable* right now. The adapter is not — see the platform question in
§Open Items. Splitting them means:

- **Zero wasted work either way.** Status vocabulary, the `submissions` table, outcome recording,
  eligibility dispatch and the CLI are identical whichever site is automated first.
- **It stays inside the offline-first rule.** With no adapter and no `playwright` import, the entire
  build is unit-testable with no network and no browser — `CLAUDE.md`'s Offline-First Rule holds
  without an exception being carved for it.
- **The dependency decision stays open.** `playwright` is not one of this project's three
  dependencies and pulls browser binaries via `playwright install`. Nothing here forces that choice.

---

## What the hub spec got wrong

Verified against this code on 2026-08-06. Recorded here so no one re-derives it.

**1. It targets a platform this project deliberately dropped.** The hub spec scopes the build to
**LinkedIn Easy Apply only**, with Indeed explicitly out of scope. But `docs/todo.md`'s Resolved
Items records **"LinkedIn dropped — decided and actioned 2026-08-01"** — the actor returned
`403 actor-is-not-rented`, renting was declined, and `LINKEDIN_ACTOR_URL`, the LinkedIn POST block
and `_normalize_linkedin()` were **removed from `apify_client.py`**. That decision predates the hub
spec by three days. `career.db` agrees: 6 `approved` and 4 `rejected` rows, **all `platform =
'indeed'`**, zero LinkedIn. Building the hub spec as written would have shipped a feature unable to
submit any of the 6 pending applications, against a source the project no longer scrapes.

**2. It is wrong that `.gitignore` already covers the session file.** It says to save Playwright's
`storageState` to "a path already covered by the project's existing `.gitignore`". That file covers
`.env`, `*.db`, `*.db-shm`, `*.db-wal`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`
and `exports/` — nothing that would match a `storage_state.json`. It would be **committed**, and a
`storageState` file is a live authenticated session cookie: in git history it is a session-hijack
credential. An explicit ignore entry is part of this build (step 90), added *before* any code can
write such a file.

**3. `playwright` is not a dependency.** The project has exactly three (`requests`,
`python-dotenv`, `fpdf2`). Confirmed not installed in the current environment. Not added here.

**4. A migration is *not* required — correcting the pre-build note that said it was.** See the
Migration Note below. The `PRAGMA user_version` trap is real; this build simply does not step in it.

---

## Migration Note (read before touching any `migrations.py`)

**This build adds no migration, and that is correct, not an oversight.**

Two independent reasons, both grounded in this project's own established conventions:

- **The new `submissions` table needs none.** `docs/todo.md`'s Resolved Items fixes the convention:
  *"initial `CREATE TABLE IF NOT EXISTS` statements live directly in each module's `init_db()`, not
  in `migrations.py`"* — `migrations.py` only tracks changes made *after* a module's baseline.
  `submissions` is a net-new table, so it belongs in `src/submission/db.py`'s `init_db()`, exactly
  as `approvals` sits in `src/review/db.py`.
- **The new statuses need none.** `vacancies.status` is `TEXT NOT NULL DEFAULT 'new'` with **no
  `CHECK` constraint** (verified in `src/vacancy_search/db.py`). `VALID_STATUSES` is a Python
  dataclass validation set only. Extending it is the identical situation to step 59's
  `VALID_PLATFORMS` addition, which `docs/specs/pnet-careers24-coverage.md` explicitly recorded as
  *"no migration — Python-validation only."*

**The trap this build avoids, documented so the next one does too.** All four migration modules
(`profile/`, `vacancy_search/`, `doc_gen/`, `review/`) own separate `MIGRATIONS` lists but read and
write the **same global `PRAGMA user_version`** on the **same** database. `vacancy_search` holds
versions 1–4; the live `career.db` sits at `user_version = 4`. Adding `(1, "ALTER TABLE ...")` to
`review/migrations.py` — the obvious thing to do — would be **silently skipped forever**, because
`apply_migrations` runs `if version > current` and `current` is already 4. No error, no warning, no
migration. **Any future migration in any module must take a globally-unique version ≥ 5.** Step 100
writes this into `CLAUDE.md` so it is a project rule, not a spec footnote.

Consequence for this build: `src/submission/` gets **no `migrations.py` stub at all**. An empty stub
would be an invitation to add `(1, …)` to it later and hit exactly this failure.

---

## Acceptance Criteria

- `career-engine submit --vacancy-id <id>` refuses, with a clear message and a non-zero exit, any
  vacancy whose status is not `approved`. Gating is on **`vacancy.status == "approved"`**, never on
  the mere presence of an `approvals` row — this is the explicit instruction left in
  `src/review/cli.py`'s closing comment, and it is honored literally.
- With no adapter registered for a vacancy's platform (**every vacancy in this build**), `submit`
  records a `not_supported` submission row, prints the vacancy URL and an explicit
  "submit this one by hand" instruction, and **leaves the vacancy at `approved`** — an application
  that still needs manual action must not look submitted.
- `career-engine submit --vacancy-id <id> --manual` records that Tebello submitted it by hand and
  advances the vacancy to `submitted`.
- A failed submission advances the vacancy to `submission_failed` with the failure detail recorded,
  and is retryable. A submission never reports success it did not achieve.
- Every submission attempt is persisted **before** the vacancy status transition, mirroring
  `run_review_gate`'s fail-closed ordering — a crash after persistence leaves a recorded attempt,
  never a `submitted` vacancy with no attempt on file.
- `VALID_STATUSES` gains `submitted` and `submission_failed`; `VALID_TRANSITIONS` allows
  `approved → submitted | submission_failed` and `submission_failed → submitted |
  submission_failed`. `submitted` is terminal. **No transition into `submitted` exists from `new`,
  `scored`, `asset_ready` or `rejected`** — asserted by test, since this is Hard Rule 1 expressed in
  the state machine.
- The session-state path (for the future adapter) resolves from config, defaults to
  `.session/storage_state.json`, and that path is covered by `.gitignore` — asserted by a test that
  reads `.gitignore`, so the protection cannot silently regress.
- No module under `src/submission/` imports `playwright`, and no new project dependency is added.
  The full suite passes with no network and no browser.
- `black . && ruff check . && python -m pytest` clean, coverage ≥ 80% on all new code, and the
  existing **249 tests** continue to pass with zero regressions.

---

## Design

### New module: `src/submission/`

```
src/submission/
├── __init__.py
├── schema.py       ← SubmissionMethod / SubmissionOutcome enums, SubmissionAttempt dataclass
├── db.py           ← submissions table (CREATE TABLE in init_db), save_attempt, getters
├── session.py      ← storageState path resolution + availability check (no playwright import)
├── eligibility.py  ← ADAPTERS registry (empty in this build) + is_auto_submittable()
└── pipeline.py     ← run_submission() — the one entry point, orchestrates the above
```

No `migrations.py` — see Migration Note.

### `submissions` table

```sql
CREATE TABLE IF NOT EXISTS submissions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    vacancy_id   INTEGER NOT NULL REFERENCES vacancies(id),
    method       TEXT NOT NULL CHECK (method IN ('auto','manual')),
    outcome      TEXT NOT NULL CHECK (outcome IN ('submitted','failed','not_supported')),
    detail       TEXT,
    attempted_at TEXT NOT NULL
)
```

Shape and constraints deliberately mirror `approvals` (`src/review/db.py`) — same `REFERENCES
vacancies(id)`, same `CHECK` on the enum-backed column, same `*_at` ISO-8601 TEXT timestamp. Multiple
rows per vacancy are expected and meaningful: a `not_supported` followed later by a `manual`
submission is the ordinary happy path of this build.

### Outcome → status mapping

| `outcome`       | vacancy status after | meaning                                                    |
|-----------------|----------------------|------------------------------------------------------------|
| `submitted`     | `submitted`          | it actually went through (auto adapter, or `--manual`)      |
| `failed`        | `submission_failed`  | an adapter tried and did not succeed — retryable            |
| `not_supported` | `approved` *(unchanged)* | no adapter for this platform — still Tebello's to do    |

`not_supported` deliberately does **not** move the vacancy. The status must keep saying "this
application still needs action," because it does.

### Eligibility dispatch

```python
ADAPTERS: dict[str, SubmitAdapter] = {}   # empty in this build — by design, not by omission
```

`is_auto_submittable(vacancy)` is a registry lookup on `vacancy.platform`. With an empty registry it
returns `False` for every vacancy, so every `submit` run in this build takes the `not_supported`
path. Registering the first adapter is then purely additive — one dict entry, no change to
`pipeline.py`, no `if platform == "indeed"` branching anywhere (same discipline step 76 applied to
`fetch_vacancies()`).

### Untrusted input

Scraped vacancy text (`title`, `company`, `description`) is untrusted — the same exposure that
produced the ADR-003 security correction, where a prompt-injected posting could steer the headless
doc-gen agent. In this build the mitigation is structural and total: **dispatch is a dict lookup on
`platform`, and no scraped field is ever interpreted, executed, or passed to an LLM.** When the
adapter is built, field-matching must use deterministic selectors, not LLM-driven form
interpretation; if an LLM is ever involved, `wrap_untrusted_text()` applies as it does in doc-gen.

### Session state

`session.py` resolves the path only — it does not open a browser and imports nothing from
Playwright. `SESSION_STATE_PATH` joins `Settings` (default `.session/storage_state.json`);
`session_state_available()` reports whether the file exists. The adapter will consume this; the core
uses it to fail with an actionable message ("no saved session — run the one-time login setup")
rather than a stack trace. The `.gitignore` entry lands in the same step as the setting, before any
code path can write the file.

---

## Build Queue — Phase 16 (steps 81–101)

TDD throughout: `[RED]` writes failing tests, `[GREEN]` makes them pass. No step's Output column
touches more than 2 files (same convention as the rest of this project's specs).

| # | Description | Agent | Output | Verification | Network |
|---|---|---|---|---|---|
| 81 | [RED] `tests/unit/test_submission_schema.py` (new) — `SubmissionMethod`/`SubmissionOutcome` enum values; `SubmissionAttempt` requires `vacancy_id`, defaults `attempted_at` to UTC ISO-8601, rejects an unknown method/outcome | tester | 1 test file | pytest fails on missing module | none |
| 82 | [GREEN] `src/submission/schema.py` + `src/submission/__init__.py` — enums + dataclass, mirroring `review/schema.py`'s shape | executor | 2 files | step 81's tests pass | none |
| 83 | [RED] `tests/unit/test_vacancy_schema.py` — `Vacancy(status="submitted")` and `"submission_failed"` construct; an unknown status still raises | tester | 1 test file | pytest RED | none |
| 84 | [GREEN] `src/vacancy_search/schema.py` — add both to `VALID_STATUSES`, with the step-59 precedent cited inline (Python-validation only, no migration) | executor | 1 file | step 83 GREEN; full suite green | none |
| 85 | [RED] `tests/unit/test_vacancy_db.py` — `approved → submitted`, `approved → submission_failed`, retry `submission_failed → submitted`, `submitted` terminal, **and** that `new`/`scored`/`asset_ready`/`rejected` all reject a `submitted` transition (Hard Rule 1 in the state machine) | tester | 1 test file | pytest RED | none |
| 86 | [GREEN] `src/vacancy_search/db.py` — extend `VALID_TRANSITIONS` only; `update_vacancy_status` unchanged | executor | 1 file | step 85 GREEN; full suite green | none |
| 87 | [RED] `tests/unit/test_submission_db.py` (new) — table created by `init_db`, `save_attempt` returns rowid and commits, `get_attempts_for_vacancy` returns newest-first, invalid `method`/`outcome` rejected by the CHECK constraint, FK to a nonexistent vacancy rejected | tester | 1 test file | pytest RED | none |
| 88 | [GREEN] `src/submission/db.py` — `init_db()` with `CREATE TABLE IF NOT EXISTS submissions` (+ `PRAGMA foreign_keys = ON`, as `review/db.py` does), `save_attempt`, `get_attempts_for_vacancy`. **No `migrations.py`** — Migration Note | executor | 1 file | step 87 GREEN | none |
| 89 | [RED] `tests/unit/test_submission_session.py` (new) — default path, `SESSION_STATE_PATH` override, `session_state_available()` false when absent / true when present, **and** an assertion that `.gitignore` contains an entry covering the default path | tester | 1 test file | pytest RED | none |
| 90 | [GREEN] `src/config.py` + `.gitignore` — add `SESSION_STATE_PATH` (default `.session/storage_state.json`) and the matching ignore entry with a comment saying why (live session credential) | executor | 2 files | the gitignore assertion in step 89 passes | none |
| 91 | [GREEN] `src/submission/session.py` — `resolve_session_state_path()`, `session_state_available()`. No playwright import | executor | 1 file | step 89 fully GREEN | none |
| 92 | [RED] `tests/unit/test_submission_eligibility.py` (new) — empty registry ⇒ `is_auto_submittable()` False for `indeed`/`pnet`/`careers24`/`linkedin`; a test-injected fake adapter ⇒ True for that platform only | tester | 1 test file | pytest RED | none |
| 93 | [GREEN] `src/submission/eligibility.py` — `ADAPTERS: dict[str, SubmitAdapter] = {}` + `is_auto_submittable()`; docstring states the registry is intentionally empty and how to add one | executor | 1 file | step 92 GREEN | none |
| 94 | [RED] `tests/unit/test_submission_pipeline.py` (new) — `run_submission()` raises on a non-`approved` vacancy (each of `new`/`scored`/`asset_ready`/`rejected`); no-adapter path records `not_supported` and leaves status `approved`; `--manual` path records `manual`/`submitted` and transitions; an adapter raising ⇒ `failed` + `submission_failed`, exception not propagated; attempt row is committed **before** the status transition (assert via a transition that raises) | tester | 1 test file | pytest RED | none |
| 95 | [GREEN] `src/submission/pipeline.py` — `run_submission(vacancy, *, manual=False, db_path=None)`; opens/closes both connections in `finally` blocks as `review/cli.py` does; the module docstring carries the same HARD RULE banner `review/cli.py` opens with | executor | 1 file | step 94 GREEN | none |
| 96 | [RED] `tests/unit/test_main.py` — `submit` subcommand parses `--vacancy-id`, `--all`, `--manual`; dispatch reaches `cmd_submit`; `--all` iterates only `approved` vacancies | tester | 1 test file | pytest RED | none |
| 97 | [GREEN] `src/main.py` — `submit` subparser + `cmd_submit` + dispatch entry, following the existing argparse/dispatch-dict shape | executor | 1 file | step 96 GREEN | none |
| 98 | [RED→GREEN] `tests/integration/test_full_pipeline.py` — offline end-to-end: seed an `approved` vacancy, run `submit`, assert a `not_supported` row exists, status still `approved`, and the printed output contains the vacancy URL and the manual-submission instruction | tester | 1 test file | passes offline, no network | none |
| 99 | `docs/architecture.md` — Stage 6 (core) added to the pipeline description + data flow; states plainly that no adapter exists yet and every platform routes to manual | doc-writer | 1 file | read-check against implemented signatures | none |
| 100 | `CLAUDE.md` — Pipeline Stages (Stage 6 partially built), Directory Structure (`src/submission/`), status vocabulary, and a new **Hard Rule 6 addendum: any new migration must use a globally-unique `PRAGMA user_version` ≥ 5** (see Migration Note) | doc-writer | 1 file | read-check against actual layout | none |
| 101 | `docs/todo.md` — this Phase 16 section with steps 81–101; move the "Phase 6 (post-MVP): Playwright auto-fill/submit" Future item to reflect core-built / adapter-outstanding | doc-writer | 1 file | read-check: no duplicate tracking | none |

---

## Explicitly out of scope

- **The Playwright site adapter itself** — any browser automation, form-filling, file upload, or
  success-screen confirmation. That is the follow-up task, and it needs the platform question
  answered first.
- **Adding `playwright` as a dependency**, and `playwright install`'s browser binaries.
- **A real-site smoke test.** Nothing in this build touches a job site, so there is nothing to smoke
  test; the requirement carries over to the adapter task, where it genuinely applies (same lesson as
  the Apify payload-shape bug — mocks verify you called the transport, not that the real site
  accepts what you sent).
- **Any weakening of the Stage 5 human-approval gate.** This build strengthens it: the gate becomes
  a precondition enforced by the state machine on a second stage, not just the terminal state.
- **A tracking dashboard** (Stage 7) — the `submissions` table is a foundation it could later read,
  but no view is built here.

---

## Definition of done

- All of §Acceptance Criteria met.
- `black . && ruff check . && python -m pytest` clean; 249 existing tests still pass; new code
  ≥ 80% covered.
- One commit per step (Hard Rule 3), plan written before implementation (Hard Rule 2).
- `docs/todo.md` and `docs/session-log.md` updated; hub `Claude-Code/docs/todo.md` item marked and
  `knowledge/tebelloreborn.md` updated with the outcome (pull `origin/main` first — hub Hard Rule 6).

---

## Open Items (require Tebello — not something an agent should attempt)

1. **Which platform gets the first adapter?** Indeed is the only live source with approved
   applications (6), but its flow varies per employer — many postings redirect to an external ATS
   with no fixed shape, which is precisely why the hub spec avoided it. Realistically the first
   adapter is either "Indeed's own apply form only, everything else `not_supported`" or a decision
   to re-add a different source. **This is the question the core defers, and it must be answered
   before the adapter task starts.**
2. **Terms-of-service and account risk — an explicit acknowledgement is needed before any adapter is
   built.** Driving an authenticated session as Tebello to submit applications is a different
   exposure from scraping via Apify: it is his own account at risk, and it is against LinkedIn's
   User Agreement (and plausibly Indeed's). This build touches none of it. The adapter task cannot
   start on an agent's assumption that the risk is accepted.
3. **Should `submitted` stay terminal?** A future tracking dashboard (Stage 7) would want states
   past submission — `response_received`, `interview`, `closed`. Not needed now; noted so the
   transition table is extended deliberately rather than discovered as a limitation later.
4. **`--all` batching behaviour.** Currently specced to iterate `approved` vacancies one at a time
   with no rate limiting or volume cap — appropriate while every outcome is `not_supported`, and
   worth revisiting when a real adapter can submit at speed (the same volume-cap judgment call
   ADR-003 §6 left open for doc-gen).

---

## Amendment — 2026-08-06 (Codex review fold-in)

Per `CLAUDE.md` Hard Rule 13, the strongest points from the Codex second opinion below are folded
back here **before** any Executor is dispatched. This amendment is authoritative where it conflicts
with the sections above; nothing above is edited in place, so the original reasoning stays readable.

Codex's points are handled in three groups: **A** — accepted, they change the build; **B** —
accepted as clarifications that were implicit and are now explicit; **C** — considered and
deliberately not adopted, with the reason.

### A. Accepted — these change the build

**A1. The retry/gating contradiction — Codex's main finding, and it is correct.**
Acceptance criterion 1 says `submit` refuses any vacancy whose status is not `approved`. The
transition table simultaneously allows `submission_failed → submitted` and calls failures
"retryable." As written, that transition is unreachable from the only CLI that would use it — the
spec contradicts itself.

**Resolution: the gate accepts `approved` *and* `submission_failed`; it forbids `new`, `scored`,
`asset_ready`, and `rejected`.** Hard Rule 1 is fully preserved, and this is worth stating precisely
rather than asserting: `submission_failed` is reachable *only* from `approved` (see the amended
transition table below), so admitting it to the gate cannot let anything reach submission without
having passed the human approval gate first. The invariant enforced is "this vacancy passed the
gate," not "this vacancy is currently in the single state `approved`."

Amended transition table — replaces the version in §Acceptance Criteria:

| from | to | note |
|---|---|---|
| `approved` | `submitted`, `submission_failed` | first attempt |
| `submission_failed` | `submitted`, `submission_failed` | retry, and retry-that-fails-again |
| `submitted` | *(none)* | terminal, subject to Open Item 3 |
| `new`, `scored`, `asset_ready`, `rejected` | *(no path to `submitted`)* | Hard Rule 1 in the state machine |

Step 94's tests change accordingly: the gate must **reject** `new`/`scored`/`asset_ready`/`rejected`
and **accept** `approved`/`submission_failed`. A test asserting `submission_failed` is accepted is
mandatory — it is the test that would have caught this contradiction.

**A2. Pin the `SubmitAdapter` interface now.** Codex is right that naming an interface without
specifying it defeats the purpose of building the contract first. Added to step 93, as a
`typing.Protocol` in `src/submission/eligibility.py`:

```python
class SubmitAdapter(Protocol):
    platform: str
    def can_handle(self, vacancy: Vacancy) -> bool: ...
    def submit(self, vacancy: Vacancy, session_state_path: Path) -> tuple[bool, str]: ...
```

Fixed contract, and the pipeline depends on nothing beyond it:
- `submit()` returns `(succeeded, detail)`. `detail` is a human-readable string recorded verbatim in
  `submissions.detail` on **both** paths — a success detail is as useful as a failure one.
- An adapter that raises is caught by `pipeline.py` and recorded as `failed` with the exception text
  as `detail`. Adapters never write to the database and never transition status — `pipeline.py` owns
  all persistence, so a future adapter cannot bypass the gate by writing its own rows.
- Adapters receive the resolved `session_state_path`, never `Settings` — nothing site-specific gets
  handed the whole config surface.

**A3. Capability-based dispatch, adopted now rather than later.** Codex's point that
`ADAPTERS[platform]` is "the first thing you outgrow" lands, because Indeed's mixed
direct-apply/external-ATS flows are exactly the known first case. `is_auto_submittable(vacancy)`
becomes: platform present in the registry **and** `adapter.can_handle(vacancy)` returns True.
Costs one line now and means the Indeed adapter can accept its own apply form while declining ATS
redirects, without any change to `pipeline.py`. Step 92's tests gain a fake adapter whose
`can_handle` returns False, asserting that a *registered* adapter can still decline a vacancy and
that it falls to `not_supported`.

**A4. `PRAGMA foreign_keys = ON` is per-connection.** A real SQLite gotcha: setting it in `init_db`
protects only that connection. Step 88's tests must assert the FK rejection **on the connection
actually used by `save_attempt`**, not on a freshly opened one — otherwise the test passes while the
constraint is inert in production.

**A5. Assert stable output substrings.** "Clear message" is untestable. Step 94/98 tests assert the
CLI output for a `not_supported` outcome contains the **vacancy id**, the **vacancy URL**, and the
literal phrase **`submit this one by hand`**. Vague criteria let usability regress silently.

**A6. `--all` partial-failure semantics — previously unspecified.** `--all` iterates every eligible
vacancy, **continues past individual failures**, prints a per-vacancy line, ends with a summary
(`submitted: N, failed: N, not supported: N`), and exits non-zero if any vacancy ended `failed`.
`not_supported` does **not** make the run fail — in this build it is the expected outcome of every
vacancy, so a non-zero exit would make normal operation look broken.

**A7. Make the coverage claim enforceable or drop it.** Codex is right that `python -m pytest` does
not enforce "≥ 80% on all new code" — this project's dev extras contain only `pytest`, so the rule
in `CLAUDE.md`'s Testing Standards is currently aspirational. New **step 102**: add `pytest-cov` to
`[project.optional-dependencies].dev` and verify this build with
`python -m pytest --cov=src/submission --cov-fail-under=80`. This is a **dev-only** dependency —
pip-clean, no binaries — and the acceptance criterion "no new project dependency" is hereby scoped
to **runtime** dependencies, which remain exactly three.

**A8. `attempted_at` must be timezone-aware.** Specified explicitly:
`datetime.now(timezone.utc).isoformat()`, identical to `ReviewResult.decided_at` and
`Vacancy.scraped_at`. Never `datetime.utcnow()`, which produces a naive string that sorts
inconsistently against the aware ones already in the database.

**A9. `--manual` is an operator assertion the system cannot verify.** Reworded: `--manual` records
that **the operator asserts a manual submission has already happened**. The CLI prints that framing
back before recording, and `submissions.detail` for a manual row is set to
`"operator-asserted manual submission"`. The system is not claiming to have witnessed it.

### B. Accepted as clarifications (implicit before, explicit now)

**B1. Status is the sole source of truth for approval; record drift is ignored.** If
`vacancies.status == "approved"` but no `approvals` row exists (a manual DB edit, or a bug), `submit`
proceeds — `src/review/cli.py`'s own closing comment mandates gating on status and *not* on the
presence of an approval row, and adding a second check would quietly re-introduce the failure mode
that comment exists to prevent. The reverse case (an approval row with a non-approved status) is
refused by the gate, which is the fail-closed direction.

**B2. A malformed or empty vacancy URL is already structurally impossible.** `Vacancy.__post_init__`
enforces `REQUIRED_FIELDS = ("company", "title", "url")` non-empty at construction, and every read
path builds through `_vacancy_from_row`. No extra handling is added; a test documents the guarantee
rather than duplicating it.

**B3. The failure path is only reachable via an injected fake adapter, and that is stated.** With an
empty registry there is no way to produce a real `failed` outcome in this build. Step 94's failure
tests inject a fake adapter that raises and one that returns `(False, detail)`. The acceptance
criterion now says so, instead of implying a reachable production path.

**B4. Duplicate attempt rows are allowed by design.** Repeated `--all` runs will append another
`not_supported` row per vacancy. `submissions` is an append-only attempt log — the same shape as
`approvals`, where `get_approval_by_vacancy_id` already resolves multiplicity with
`ORDER BY id DESC LIMIT 1`. `get_attempts_for_vacancy` returns newest-first for the same reason. Any
future reader must take `vacancies.status` as current state and `submissions` as history; this is
recorded in step 99's `docs/architecture.md` text so a Stage 7 dashboard does not misread an old
`not_supported` row as current.

**B5. Two connections, two commits, deliberately.** The attempt row is committed on the submission
connection before the status transition runs on the vacancy connection — copied knowingly from
`run_review_gate`, whose comment documents the same trade-off. Partial state is possible and is the
*preferred* failure: a recorded attempt with a stale status (fails closed) beats a `submitted`
vacancy with no attempt on file (fails open). If the transition raises after persistence, the CLI
prints that the attempt was recorded but the status was not advanced, names the vacancy id, and
exits non-zero — Codex's "split-brain" case, now specified rather than left to a generic traceback.

**B6. Concurrency is out of scope, explicitly.** Two simultaneous `submit` runs on the same vacancy
could both observe `approved`. This is a single-operator local CLI with no daemon; no locking is
added. Recorded here so it is an accepted trade-off rather than an oversight.

### C. Considered, not adopted

**C1. A dedicated `unsupported_platform` vacancy status.** Codex agreed with leaving the vacancy
`approved`, and that stands: the vacancy genuinely still needs action, and a distinct status would
split the "needs action" queue across two values for no gain. B4 covers the duplicate-row
consequence.

**C2. Returning a pure result object with no exceptions.** Adopted in part, not in full.
`run_submission()` returns a `SubmissionAttempt` for every real outcome (`submitted`, `failed`,
`not_supported`) and the CLI decides output and exit code — Codex's testability point, taken. But a
**gate violation raises** `SubmissionNotAllowedError` rather than returning a value. Hard Rule 1 is
the one condition that must be impossible to ignore by discarding a return value, and an exception
is the only construct that guarantees that. Step 94 tests both shapes.

**C3. A single transaction across attempt-persistence and status transition.** Rejected for the
reason in B5: one transaction would make the two writes atomic, but the failure it produces is
"neither recorded" — which is the fails-open direction this project's review gate deliberately
rejected. Consistency loses to auditability here, and the choice is now documented rather than
inherited by accident.

### Build Queue changes from this amendment

No renumbering. Steps 85, 86, 88, 92, 93, 94, 95, 97, 98 and 99 are **amended in content** as
described above (the amendment governs where it conflicts). One step is added:

| # | Description | Agent | Output | Verification | Network |
|---|---|---|---|---|---|
| 102 | Add `pytest-cov` to `[project.optional-dependencies].dev` in `pyproject.toml`; verify this build with `python -m pytest --cov=src/submission --cov-fail-under=80`. Dev-only — runtime dependencies stay at three (A7) | executor | 1 file | the coverage command passes at ≥ 80% | none |

Step 101 (`docs/todo.md`) now records steps 81–102.

---

## Codex second opinion (advisory) — 2026-08-06

**Second Opinion**

The spec is mostly sound as a platform-agnostic Stage 6 foundation. The strongest parts are the explicit refusal to add Playwright, the `approved` gate, the `not_supported` outcome, and the decision to leave vacancies `approved` when manual action is still required. I would not block implementation, but I would tighten several areas before building.

**1. Buried Or Unstated Assumptions**

- The spec assumes `vacancy.status == "approved"` is always the single source of truth for human approval. It says gating is “never on the mere presence of an `approvals` row,” which is good, but it does not address drift: what if an approval row exists but status was reverted, or status is `approved` with no approval row due to manual DB edits or a bug? If status is the source of truth, say explicitly that inconsistent approval records are ignored, or add an integrity check.

- `--manual` assumes the user has already submitted externally. The wording says it “records that Tebello submitted it by hand,” but the CLI cannot know that. Acceptance criteria should require confirmation wording, e.g. `--manual` means “operator asserts manual submission has already happened.”

- The spec assumes multiple submission rows per vacancy are enough to reconstruct the truth. That is probably fine, but there is no unique “current submission state” other than `vacancies.status`. If later tools read `submissions` directly, they may misinterpret older `not_supported` or `failed` rows.

- The spec assumes all future adapters can fit `ADAPTERS: dict[str, SubmitAdapter]` keyed only by `vacancy.platform`. The Open Item admits Indeed may redirect to external ATS flows, which suggests platform alone may be too coarse. Some dispatch may eventually need platform + apply URL shape + employer ATS detection.

- The spec assumes `attempted_at` UTC ISO-8601 text is enough, but does not say whether it must be timezone-aware, e.g. `2026-08-06T12:34:56Z` versus naive `datetime.utcnow().isoformat()`. That matters for tests and downstream ordering.

**2. Missing Or Untestable Acceptance Criteria**

- “A failed submission advances the vacancy to `submission_failed`” is not directly reachable in this build unless tests inject a fake adapter. The build has no real adapter, so the acceptance criterion should explicitly say failure behavior is tested through an injected adapter.

- “Every submission attempt is persisted before the vacancy status transition” is important, but the current table has no transaction guidance. If persistence and status transition happen on separate connections, you get the desired crash behavior, but also possible partial state. The spec should define whether this is intentional and tested.

- “Clear message” and “explicit ‘submit this one by hand’ instruction” are vague. Tests should assert stable substrings, including the vacancy URL and perhaps the vacancy id. Otherwise future wording changes could weaken operator usability without failing tests.

- “`--all` iterates only `approved` vacancies” lacks acceptance criteria for partial failure. If one vacancy errors, does the command continue, stop, return non-zero, summarize counts, or preserve per-vacancy exit behavior?

- “No module under `src/submission/` imports `playwright`” is good, but “no new project dependency is added” needs a concrete check: inspect `requirements.txt` / lockfile / project metadata. Otherwise it is easy to claim manually but not enforce.

- Coverage “≥ 80% on all new code” is not always enforced by plain `python -m pytest`. If the repo does not already have per-file coverage thresholds, this is aspirational rather than a build gate.

**3. Failure Modes Not Considered**

- Race conditions: two `career-engine submit --vacancy-id <id>` invocations could both see `approved`, both record attempts, and both transition. For this local tool that may be acceptable, but the spec should say duplicate attempts are allowed or add a locking/idempotency rule.

- Missing or malformed vacancy URL: the `not_supported` path must print the vacancy URL, but the spec does not say what happens if URL is null, empty, or invalid.

- Foreign keys in SQLite: step 88 says `PRAGMA foreign_keys = ON`, but SQLite requires that per connection. Any code path saving attempts must enable it on that connection, not just table initialization.

- Status transition failure after attempt persistence: the spec wants the attempt committed first. Good. But the CLI output and exit code for that split-brain case should be specified. Otherwise the operator may see a generic failure while the DB contains a persisted attempt.

- Adapter contract ambiguity: `SubmitAdapter` is named but not specified. Does it return an outcome object, raise exceptions, include detail, have access to session path, receive a vacancy dataclass, or own DB writes? This is the foundation the adapter plugs into, so the interface should be pinned now.

- Manual submission from `submission_failed`: `VALID_TRANSITIONS` allows `submission_failed → submitted`, but acceptance criteria for `--manual` only mention approved vacancies. Can `--manual` be used after a failed auto attempt? The transition table says yes; the CLI criteria imply maybe no because submit refuses any vacancy whose status is not `approved`.

That last point is a real contradiction: the first acceptance criterion says `submit --vacancy-id <id>` refuses any vacancy whose status is not `approved`. Later, `VALID_TRANSITIONS` allows `submission_failed → submitted`, and failure is “retryable.” If retries use the same `submit` command, then `submission_failed` must be eligible for at least some submission path. The spec needs to resolve this.

**4. Architectural Alternatives Worth Weighing**

- Use an explicit service result instead of exceptions for `run_submission()`. For example, return `SubmissionResult(outcome, status_after, attempt_id, message)` and let CLI decide exit/output. This makes the command easier to test and avoids hidden behavior around swallowed adapter exceptions.

- Add an `operator_confirmed` or `method=manual` detail convention for manual submissions. Since `--manual` records a real-world action the system cannot verify, the schema could preserve that distinction clearly. Current `method='manual', outcome='submitted'` is probably enough, but the CLI wording must be exact.

- Consider an `unsupported_platform` vacancy status instead of leaving it `approved`. I agree with the spec’s choice to leave it `approved`, because action is still needed. But the tradeoff is repeated `--all` runs will keep creating `not_supported` rows unless deduped. If the intended workflow includes repeated `--all`, you may want either dedupe behavior or a separate queue concept later.

- Define adapter dispatch as capability-based, not platform-only. Instead of `ADAPTERS[platform]`, an adapter could expose `can_handle(vacancy)`. That would better fit Indeed’s mixed direct/external apply flows. The platform-only registry is simpler and fine for this build, but it may be the first thing you outgrow.

- Consider one DB transaction with an audit guarantee instead of two commits. The spec prefers “attempt persisted before status transition,” which is defensible. The alternative is one transaction for consistency, plus a separate append-only operation log before external side effects. Since there is no real external side effect in this build except `--manual`, the current ordering is acceptable, but it should be acknowledged as a deliberate partial-state design.

**Main Fix Before Implementation**

Resolve the retry/gating contradiction. Either:

- `submit` only accepts `approved`, in which case `submission_failed → submitted` is dead for this CLI, or
- `submit` accepts `approved` and `submission_failed`, while still forbidding `new`, `scored`, `asset_ready`, and `rejected`.

Given the spec says failed submissions are “retryable,” I would change the gate to allow `submission_failed` for retry paths, while preserving the hard rule that nothing bypasses human approval.

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._
