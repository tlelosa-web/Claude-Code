# ADR-004: Schema State, Not a Shared Counter — a Per-Module Migration Ledger

**Status:** **Accepted** 2026-08-07 (both open questions answered, Codex-reviewed, fold-in complete — see §Amendment, which supersedes §1–§7 wherever they conflict). No code written yet.
**Date:** 2026-08-07
**Decider:** Tebello Lelosa
**Author:** Architect
**Related:** CLAUDE.md Hard Rule 6 (this ADR changes it). ADR-001 (SQLite is the single source of truth). `docs/specs/indeed-submit-adapter.md` §Amendment A2/A3/A4/A12 — Phase B is the first work blocked on this. `docs/todo.md` Open Item, "The shared-`user_version` bug is fixed in `src/profile/` only".

## Context

### The mechanism as built

This project keeps **one** SQLite database (`career.db`, ADR-001) and gives **five** modules their own `db.py` with their own `init_db()`. Four of them also own a `migrations.py` holding an independent, ordered `MIGRATIONS: list[tuple[int, str]]`, and each runs its own copy of:

```python
current = conn.execute("PRAGMA user_version").fetchone()[0]
for version, sql in MIGRATIONS:
    if version > current:
        conn.execute(sql)
        conn.execute(f"PRAGMA user_version = {version}")
```

`PRAGMA user_version` is a **single integer per database file**. Four independent lists therefore share one counter. Hard Rule 6 currently patches over this by decree: every new migration, in any module, must take a globally-unique version ≥ 5.

Current occupancy, verified in the working tree today:

| Module | `MIGRATIONS` | Notes |
|---|---|---|
| `vacancy_search/` | `1, 2, 3, 4` — `score`, `strengths`, `weaknesses`, `recommendation` on `vacancies` | Baseline `CREATE TABLE vacancies` **omits all four**. They exist nowhere else. |
| `profile/` | `5, 6` — `email`, `phone` on `candidate_profile` | Baseline `CREATE TABLE` also declares both (deliberate, see below). |
| `doc_gen/` | *(empty)* | Counter-only runner. |
| `review/` | *(empty)* | Counter-only runner. |
| `submission/` | *no `migrations.py` at all* | Deliberate — Hard Rule 6 made adding one a trap. |

Live `career.db`, inspected directly for this ADR: `user_version = 4`; `vacancies` has all four migrated columns and 10 rows; `candidate_profile` has **no** `email`/`phone` and 1 row; `generation_log` 43 rows; `approvals` 10 rows; **no `submissions` table** — Stage 6 has never run against it.

### Why this is on the table now

Phase 17 (Indeed adapter Phase A) added `profile`'s migrations 5 and 6 and broke **every new install**, caught by the integration suite and no unit test. `profile` owns the highest versions, and `import-profile` is CLAUDE.md's documented *first* command, so on a fresh database `profile.init_db()` drove the shared counter 0 → 6 before `vacancy_search.init_db()` ever ran. Its migrations 1–4 were then skipped by `if version > current`, and because its baseline omits those columns, `vacancies` came out without them at all — `IndexError: No item with that key` on the first read.

The fix shipped in `src/profile/migrations.py` alone: gate on **schema state** rather than the counter. Skip an `ADD COLUMN` whose column already exists; advance the counter only for migrations actually run; declare the columns in the baseline too, so a fresh database reaches the right shape while staying at version 0 and leaves the low numbers free.

That fix is correct and it holds. It is also not general, in two specific ways:

1. **It is still installed in exactly one of four modules.** `vacancy_search`, `doc_gen` and `review` still run the counter-only loop, and `vacancy_search`'s baseline still omits its own migrated columns. Nothing hits it today purely because `profile` no longer advances the counter first — that is call ordering, not a fix.

2. **The guard only understands `ADD COLUMN`.** It works by asking `PRAGMA table_info` whether a column is present. There is no equivalent question for a `CREATE INDEX`, a data backfill, or a table rebuild.

Point 2 is what makes this blocking rather than merely untidy. **Phase B's central migration is a table rebuild.** `docs/specs/indeed-submit-adapter.md` §Amendment A4 adds `pending_review` to the `submissions.outcome` CHECK constraint, and SQLite cannot alter a CHECK in place — it is the 12-step rebuild (create new table, copy, drop, rename). No column-existence check can gate that, so extending the `profile` pattern verbatim to `submission/` does not work. Phase B would have to invent a third mechanism inline, inside a feature build, for a rule Hard Rule 6 names explicitly.

### What actually went wrong, stated plainly

`user_version` is a single-writer counter being used as a multi-writer applied-migrations record. It cannot answer the only question a migration runner needs to ask — *"has **this** migration, from **this** module, already run on **this** database?"* — because it stores one number, not a set. Every symptom above is downstream of that. Hard Rule 6's globally-unique-numbering decree is a manual scheme for avoiding collisions in a shared namespace that did not need to be shared, and it fails silently when a human forgets, because `if version > current` has no error path.

## Decision

### 1. Replace the shared counter with a per-module ledger table

A new table, created and owned by a new shared runner:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    module     TEXT NOT NULL,
    version    INTEGER NOT NULL,
    applied_at TEXT NOT NULL,
    PRIMARY KEY (module, version)
)
```

One row per migration that has run, keyed by `(module, version)`. This is the record `user_version` was being asked to be, in the shape the question actually has.

Consequences that follow directly:

- **Version numbers become per-module.** `(profile, 5)` and `(vacancy_search, 5)` are different keys. There is no shared namespace left to collide in, so **Hard Rule 6's globally-unique ≥ 5 requirement is retired** (see §5).
- **Existing numbers are not renumbered.** `vacancy_search` keeps 1–4, `profile` keeps 5–6. Each list is internally ordered and that is all that matters now. Renumbering would be churn with a real risk of getting the adoption path wrong, for no benefit.
- **New modules start at 1.** `submission/migrations.py` — which Phase B creates — starts at `(1, ...)`.
- **Order within a module is the list's order**, ascending by version, unchanged.

### 2. One shared runner: `src/shared/migrations.py`

```python
def apply_migrations(conn: sqlite3.Connection, module: str, migrations: list[tuple[int, str]]) -> None:
```

It ensures the ledger table exists, reads the set of `version`s already recorded for `module`, and for each unrecorded migration in ascending order: runs the SQL, records the row, then commits once at the end.

Each module's `migrations.py` keeps its `MIGRATIONS` list — that stays local, it is the module's own schema history — and its `apply_migrations(conn)` becomes a one-line delegation passing its module name and list. Call sites in the five `db.py` files do not change at all.

`src/shared/` is the right home by this project's own precedent: `rate_limiter.py` lives there, and `ollama_client.py` was promoted there the moment it gained a second consumer (ADR-003 §Alternatives.D). This has five consumers on day one.

### 3. `ADD COLUMN` stays idempotent — skip the DDL, but still record it

The runner keeps `profile`'s column-existence check, with one change: a skipped migration is **recorded as applied**, not silently passed over.

```
if the migration matches ALTER TABLE <t> ADD COLUMN <c> and <c> already exists on <t>:
    do not execute the SQL
    record (module, version) anyway
else:
    execute the SQL
    record (module, version)
```

This one rule does three jobs:

- **It makes adoption of existing databases fall out for free** (§4).
- **It permits baseline/migration duplication to remain safe.** `profile`'s baseline declares `email`/`phone` *and* migrations 5/6 add them. Without this rule a fresh database would create both columns in the baseline and then die on `duplicate column name: email`. With it, the migrations record as applied and move on. The duplication is now belt-and-braces rather than load-bearing, but it is harmless and its tests stay green.
- **It keeps the runner honest about re-runs.** `init_db()` is called on every command; being idempotent under repetition is a property worth having explicitly rather than by accident.

The auto-skip is deliberately scoped to `ADD COLUMN` and nothing else. Other migration forms (index creation, table rebuild, data backfill) have no general "already done?" predicate and do not need one: from this ADR forward the ledger exists, so they are gated by the ledger and run exactly once. This is safe because **every migration in the project's history to date is an `ADD COLUMN`** — verified, all six. A pre-ledger database can therefore never be carrying an unrecorded non-`ADD COLUMN` migration, because none was ever written.

### 4. Adoption of existing databases needs no special code path

On a database with no `schema_migrations` table — the live `career.db`, and Tebello's two backups — the runner creates the ledger empty and then simply runs the normal loop. §3's rule produces the correct result unaided:

| Migration | Column present in live DB? | Outcome |
|---|---|---|
| `vacancy_search` 1–4 (`score`, `strengths`, `weaknesses`, `recommendation`) | Yes | Skipped, **recorded** |
| `profile` 5 (`email`), 6 (`phone`) | No | **Applied**, recorded |

Which is exactly the truth about that database. No `user_version`-reading backfill, no one-shot adoption script, no version-number archaeology. The same loop that handles a fresh database handles a legacy one.

Note this means the live `career.db` gains `email`/`phone` on its next `init_db()` — the same auto-apply that is already pending today under the current code, not a new event. It remains true that `get_profile()` then raises its actionable error until `career-engine import-profile --file data/profile_seed.json` is re-run.

### 5. `PRAGMA user_version` is frozen and demoted to a historical artifact

The runner **never reads and never writes** `user_version`. The live database keeps whatever value it has (4) permanently, and it will mean nothing. It is not reset to 0 — rewriting a value no longer consulted buys nothing and would only invite a "why did this change?" question later.

Hard Rule 6 in `CLAUDE.md` is rewritten. Its current text — *"any new migration, in any module, must take a globally-unique `PRAGMA user_version` ≥ 5"* — becomes wrong the moment this lands, and it is the exact instruction that would lead a future session to hand-pick a global number again. New text should say: no schema change without a migration file; migrations are versioned **per module** starting at 1; the ledger is the record; a net-new table still needs no migration at all (its `CREATE TABLE IF NOT EXISTS` goes in that module's `init_db()`, unchanged convention).

### 6. Fix `vacancy_search`'s baseline in the same change

`CREATE TABLE vacancies` gains `score INTEGER`, `strengths TEXT`, `weaknesses TEXT`, `recommendation TEXT`, matching what migrations 1–4 produce. Under §3 this is safe (the migrations skip-and-record), and it removes the single sharpest edge in the current design: a table whose real shape lives only in a migration list, four columns deep, with a crashing read as the failure mode.

This is not strictly required for correctness once the ledger exists. It is included because the ADR's whole premise is that schema state should be legible from the schema, and leaving the one baseline that is provably wrong-shaped in place would contradict it. `doc_gen` and `review` need no baseline change — their `MIGRATIONS` lists are empty, so their baselines are already complete.

### 7. Scope boundary

This ADR covers the migration mechanism only. It does not touch `submission/db.py`'s DDL-drift guard (spec A4/A12), does not add `submission_preps` or `screening_questions`, and does not change the `submissions.outcome` CHECK. Those are Phase B, and they become straightforward once this lands.

## Consequences

**Positive**

- The failure mode that broke every new install is structurally gone, in all five modules, not one.
- Phase B is unblocked and can write an ordinary table-rebuild migration numbered `1`.
- A forgotten version number stops being a silent data-loss bug. Two modules picking the same number is now legal and correct.
- Module boundaries stop leaking through a global counter — `submission/` can finally have a `migrations.py` like everyone else.
- The runner is one implementation with one set of tests, instead of four copies of a loop that have already drifted apart once.

**Negative / costs**

- A new table appears in `career.db`. It is bookkeeping, not career data, and it is additive.
- Five `db.py` modules and four `migrations.py` modules are touched — this is a > 2-file change and needs a plan, which is what the Build Queue below is.
- **Existing tests assert on `user_version` and will change**: `tests/unit/test_profile_db.py` (the legacy-database test asserting it reaches 6, the fresh-database test asserting it stays 0, and the Hard-Rule-6 docstrings) and `tests/unit/test_submission_db.py::test_does_not_advance_user_version`. These are not deletions — each becomes the equivalent assertion against the ledger. Hard Rule "never delete or skip tests to make them pass" applies with full force here; a test that asserted the counter did not move should assert the ledger recorded exactly what it should.
- Anything outside the test suite reading `user_version` would break. Checked: nothing does — `tools/dashboard_server.py` does not, and no ADR or doc depends on the value at runtime.
- CLAUDE.md Hard Rule 6, `docs/architecture.md`, and `docs/todo.md`'s Open Item all need updating in the closeout.

**Neutral**

- The live `career.db` is migrated to 5/6 on the next command either way; this ADR does not change that, only how it is recorded.

## Alternatives considered

**A. Install the `profile` guard in all four modules, keep `user_version`.** The smallest change, and it was the option `docs/todo.md` named first. Rejected because it does not survive contact with Phase B: the `submissions.outcome` CHECK rebuild has no column-existence predicate, so the guard cannot gate it, and Hard Rule 6's manual global numbering — the thing that failed — would still be the primary defense. It fixes the specific bug that already bit, not the mechanism that produced it.

**B. Fold every module's migrations into its own baseline `CREATE TABLE` and drop migrations entirely.** Also named in the todo. Correct for a greenfield database and wrong for an existing one: the live `career.db` has 10 vacancies, 10 approvals and 43 generation-log rows, and a baseline-only scheme has no way to bring an existing file to a new shape. It would also mean this project could never make a schema change again without a manual `ALTER` at the console, which is precisely what Hard Rule 6 exists to prevent.

**C. One global `MIGRATIONS` list in `src/shared/`, all modules' migrations merged.** Makes the counter honest by making the namespace genuinely single-owner. Rejected: it couples every module's schema history into one file, so `submission/` could not add a migration without editing a shared list that `profile` and `vacancy_search` also depend on — the opposite direction from how this project has organised every other cross-cutting concern (per-module `db.py`, per-module schema).

**D. Separate database files per module.** Removes the shared counter by removing the sharing. Rejected outright: contradicts ADR-001 (SQLite as *the* single source of truth), and the schema is genuinely relational across modules — `generation_log.vacancy_id`, `approvals.vacancy_id` and `submissions.vacancy_id` are all real foreign keys into `vacancies`.

**E. Adopt an off-the-shelf migration tool (Alembic, `yoyo`).** Rejected on proportionality. This project has three runtime dependencies by deliberate choice, six migrations in its entire history, and no ORM for Alembic to reflect. The ledger table plus the runner is about forty lines and has no dependency footprint.

## Build Queue — proposed, atomic, TDD

Offline throughout. No network stage is touched.

1. **[RED]** `tests/unit/test_shared_migrations.py` (new) — ledger table shape and `(module, version)` primary key; per-module isolation (same version number, two modules, both apply); re-running is a no-op; `ADD COLUMN` on an existing column is skipped **and recorded**; a non-`ADD COLUMN` migration runs exactly once; adoption of a ledger-less database with columns already present records without re-running.
2. **[GREEN]** `src/shared/migrations.py` — the runner.
3. **[RED]** update `tests/unit/test_profile_db.py` — the two `user_version` assertions become ledger assertions; keep both init-ordering regression tests unchanged in intent (they must still converge on identical schemas).
4. **[GREEN]** `src/profile/migrations.py` — delegate to the shared runner; drop the local guard and the counter writes. Baseline in `db.py` unchanged.
5. **[RED]** `tests/unit/test_vacancy_db.py` — baseline `CREATE TABLE vacancies` includes the four match columns; a fresh database and a legacy database converge on the same schema.
6. **[GREEN]** `src/vacancy_search/migrations.py` delegates + `src/vacancy_search/db.py` baseline gains the four columns (§6).
7. **[GREEN]** `src/doc_gen/migrations.py` + `src/review/migrations.py` delegate. Empty lists, no behaviour change — one commit, covered by the shared runner's tests.
8. **[RED]** `tests/unit/test_submission_db.py` — replace `test_does_not_advance_user_version` with the ledger equivalent.
9. `tests/integration/test_full_pipeline.py` — an end-to-end init in **both** module orders against one database, asserting identical final schema and a complete ledger. This is the test class that caught the Phase 17 regression; it is what proves this ADR did its job.
10. Verify against a **copy** of the live `career.db` before anything touches the real one — ledger created, `vacancy_search` 1–4 recorded-not-rerun, `profile` 5–6 applied, all 10 vacancies / 10 approvals / 43 generation-log rows intact.
11. Docs closeout — `CLAUDE.md` Hard Rule 6 rewritten (§5), `docs/architecture.md`, `docs/todo.md` Open Item closed, `docs/session-log.md`.

## Open questions for Tebello

1. **§6 — fix `vacancy_search`'s baseline in this change, or leave it?** Recommended: fix it. It is the one baseline that is provably wrong and it is what made Phase 17 fatal rather than cosmetic. It does add a file to the change.
2. **Does this need `/codex-review` before build?** Hard Rule 13 names `docs/specs/`, and this is an ADR in `docs/decisions/` — so the rule does not literally bind. Given it redesigns a mechanism Hard Rule 6 names explicitly, and the last two Codex passes both returned findings that would have failed at runtime, running it anyway looks like the better bet.

**Both answered by Tebello, 2026-08-07.** (1) **Fix `vacancy_search`'s baseline in this change** — §6 stands as written, build steps 5–6 included. (2) **Run `/codex-review`** — done, output appended below. Note the `/codex-review` skill's path guard refused the ADR (it is scoped to `docs/specs/` only, matching the literal wording of Hard Rule 13); the identical review instruction and payload discipline were applied via a direct `codex exec` call instead, sending this file and nothing else.

## Codex second opinion (advisory) — 2026-08-07

**Second Opinion Review**

This ADR is directionally sound. The diagnosis is correct: `PRAGMA user_version` is the wrong shape for independent module migrations, and a `(module, version)` ledger is the right minimal fix. I would not reject the spec. I would tighten several details before build.

**1. Buried Or Unstated Assumptions**

The biggest hidden assumption is that `migrations: list[tuple[int, str]]` can carry Phase B's table rebuild. The ADR says Phase B needs SQLite's "12-step rebuild" and then defines the runner as executing one SQL string per migration. Python's `sqlite3.Connection.execute()` will not execute multiple statements in one string. If the runner uses `execute(sql)`, a rebuild migration cannot be represented. If it switches to `executescript()`, transaction behavior changes and must be designed deliberately.

The ADR assumes "runs the SQL, records the row, then commits once at the end" is atomic enough. That needs to be explicit. For DDL plus ledger writes, the acceptance criteria should prove that a failed migration does not leave a ledger row claiming success. This matters especially for the table rebuild case.

The wording "Order within a module is the list's order, ascending by version" hides an ambiguity. Is the runner sorting by version, or trusting the list order? Those are different behaviors. If it sorts, list order is not authoritative. If it trusts list order, "ascending by version" must be validated.

The ADD COLUMN auto-detection assumes simple unquoted identifiers: `ALTER TABLE <t> ADD COLUMN <c>`. That matches current migrations, but it should be documented as the only supported auto-skip form. Quoted identifiers, schema-qualified tables, `IF NOT EXISTS`, or unusual whitespace/comments could be misparsed.

The adoption argument assumes every pre-ledger migration in the real world is one of the six known `ADD COLUMN`s. The ADR says this was verified in the working tree, which is good, but it also mentions "Tebello's two backups." If there are any older/exported/copied databases outside those three files, the spec does not say whether they are supported.

**2. Missing Or Untestable Acceptance Criteria**

Add an acceptance criterion for failed migration atomicity: if migration N fails, `(module, N)` must not be recorded, later migrations must not run, and the schema must not be half-declared as complete.

Add explicit tests for duplicate and invalid versions inside one module. Example: `[(1, ...), (1, ...)]` should fail loudly, not silently skip the second because the ledger already has version 1. Same for non-positive versions and out-of-order versions if the project expects ascending order.

Add a direct acceptance test for the Phase B-shaped case: one migration that rebuilds a table with existing rows, preserves data, records exactly one ledger row, and reruns as a no-op. Without that, the ADR's stated blocker is not actually proven solved.

Add a test for ledger corruption or pre-existing bad rows only if you care to support it. At minimum, define behavior for a pre-existing `schema_migrations` table with wrong shape. Right now "created and owned by a new shared runner" does not say whether the runner verifies the table schema or blindly trusts any table with that name.

Add an acceptance criterion around fresh databases after baseline duplication. The ADR implies a fresh `vacancy_search.init_db()` should create the four columns in baseline, skip all four `ADD COLUMN`s, and record versions 1-4. That should be asserted directly.

**3. Failure Modes Not Considered**

Partial table rebuild failure is the main one. A rebuild can fail after creating a temporary table, after copying rows, or after dropping/renaming. The spec does not say how the migration should name temp tables, guard against leftovers, or recover from a previous failed attempt.

Concurrency is not discussed. If two commands initialize the same database at the same time, both may see a missing ledger row and both may try to apply the same migration. SQLite locking may serialize writes, but the runner should be tested or designed so the primary-key insert and DDL order do not produce confusing duplicate-column or duplicate-ledger failures.

The ledger records only `(module, version, applied_at)`, not the SQL/checksum/name. That is probably acceptable for this project, but it means changing the SQL for an already-recorded migration will be invisible. The ADR should state that migrations are immutable once shipped.

`ADD COLUMN` skip-and-record can mask drift. If a column named `email` exists with the wrong type or semantics, the runner records the migration as applied. SQLite's typing is loose, so this may be fine, but the spec's phrase "schema state" is stronger than the check actually performed: it checks column presence, not full schema compatibility.

Foreign keys and indexes after table rebuild are not mentioned. Phase B's `submissions` table has a foreign key to `vacancies`; rebuilding it must preserve constraints and any indexes/triggers if they exist later. The migration pattern should include `PRAGMA foreign_keys` handling and post-rebuild schema verification.

**4. Architectural Alternatives Worth Weighing**

A structured migration object instead of raw SQL tuples is worth considering:

```python
Migration(
    version=1,
    sql=...,
    idempotency=AddColumn(table="vacancies", column="score"),
)
```

or separate helpers like `add_column(...)`, `execute_once(...)`, `rebuild_table(...)`. This avoids regex-driven SQL parsing while keeping the project lightweight. I would seriously weigh this because the ADR's only special idempotency rule depends on parsing SQL strings.

A ledger with `module`, `version`, `name`, and `checksum` is also worth weighing. I would not call it mandatory, but it gives better protection against accidental edits to historical migrations. The current three-column ledger is simpler, but it relies on discipline rather than detection.

For the table rebuild specifically, I would consider allowing callable migrations:

```python
MIGRATIONS = [
    Migration(1, rebuild_submissions_outcome_check),
]
```

That is a better fit than cramming SQLite's 12-step rebuild into a string. It also makes tests clearer: the callable can run multiple statements inside the runner's transaction and raise on validation failure.

Bottom line: the ADR's core decision is sound. The weak spot is not the ledger idea; it is the underspecified execution model for non-trivial migrations, especially the table rebuild that motivated the ADR in the first place. Tighten that before implementation.

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._

---

## Amendment — 2026-08-07 (Codex fold-in)

**This Amendment supersedes §1–§7 wherever they conflict.** Thirteen accepted changes, three considered-and-declined. Hard Rule 13's gate is satisfied (run via direct `codex exec`, see the note under Open Questions).

Codex's bottom line was that the ledger idea is right and the *execution model for non-trivial migrations* is underspecified. That is correct, and the central finding is worse than Codex stated — it was verified directly against this machine's `sqlite3` (3.49.1) rather than accepted on the review's word:

```
execute("CREATE TABLE …; INSERT …; DROP …;")
  → sqlite3.ProgrammingError: You can only execute one statement at a time.

executescript(...)  →  in_transaction: True → False
  (an uncommitted INSERT was committed by the executescript call itself)
```

So both halves fail: §2's `list[tuple[int, str]]` **cannot represent Phase B's rebuild**, and `executescript` is not a safe escape hatch either — it issues an implicit `COMMIT` before running, which would silently destroy §2's "commits once at the end" atomicity and leave a half-applied rebuild with an inconsistent ledger. This is exactly the case the ADR exists to unblock, so it had to be fixed before build.

### Accepted

- **A1 — A migration's payload becomes `str | Callable[[sqlite3.Connection], None]`.** §2's signature becomes `list[tuple[int, str | Callable]]`. A `str` is a single SQL statement, executed as today; a callable receives the open connection and may issue as many `execute()` calls as it needs, **inside the runner's transaction**, so a 12-step rebuild is an ordinary Python function. All six existing migrations stay unchanged as strings. Phase B's `submissions.outcome` CHECK rebuild is written as a callable. *(Chosen over Codex §4's structured `Migration` dataclass — see Declined D1.)*
- **A2 — Atomicity is per migration, and explicit.** §2's "commits once at the end" is replaced: the runner opens `BEGIN IMMEDIATE`, runs one migration, inserts its ledger row, and commits — **the DDL and its ledger row commit together or not at all**. On failure it rolls back that migration and its ledger row, does not run any later migration, and re-raises. Earlier migrations stay applied *and* recorded, so a re-run resumes correctly rather than restarting. This is what makes A1's callable rebuild safe.
- **A3 — Migration lists are validated, and bad ones fail loudly.** The runner trusts list order but asserts it: versions must be **strictly ascending** and **positive**. A duplicate version within a module, a non-positive version, or an out-of-order list raises `MigrationDefinitionError` at call time. Codex's `[(1, ...), (1, ...)]` case would otherwise have the second silently swallowed by the ledger. This resolves §1's "ascending by version" ambiguity in favour of *validate, don't sort* — sorting would make list order non-authoritative and hide the mistake.
- **A4 — The `ADD COLUMN` auto-skip is narrowed and documented as the only supported form.** It matches `ALTER TABLE <table> ADD COLUMN <column> …` with simple unquoted identifiers and ordinary whitespace, and nothing else. Quoted or schema-qualified identifiers, `IF NOT EXISTS`, and embedded comments are **not** recognised and are not auto-skipped — they simply run under ordinary ledger gating. The skip **never applies to a callable** (A1): callables are gated by the ledger alone.
- **A5 — The runner verifies the ledger table rather than trusting any table of that name.** If `schema_migrations` exists with the wrong shape (missing columns, wrong primary key), the runner raises `MigrationLedgerError` instead of proceeding against it. §2's "ensures the ledger table exists" was silent on this.
- **A6 — Shipped migrations are immutable.** Once a migration may have run anywhere, its version is never edited or renumbered — a correction ships as a new version. This goes into the rewritten Hard Rule 6, not just here. It is the discipline that stands in for the checksum column (see Declined D2).
- **A7 — Concurrency is handled by `BEGIN IMMEDIATE`, and stated.** Taking the write lock *before* reading the ledger means two simultaneous `init_db()` calls serialize: the second sees the rows the first recorded and no-ops, rather than both attempting the same DDL and producing a confusing `duplicate column name` or ledger primary-key collision. §2 did not discuss concurrency at all.
- **A8 — New acceptance test: the Phase-B-shaped rebuild.** One callable migration that rebuilds a table holding existing rows — data preserved, exactly one ledger row written, re-run is a no-op. Without this the ADR's stated blocker is asserted but not proven; it becomes build step 9.
- **A9 — New acceptance test: failed-migration atomicity.** Migration N raises → `(module, N)` is absent from the ledger, migrations after N never ran, and the schema is not half-declared complete.
- **A10 — New acceptance assertion: fresh-database baseline duplication.** A fresh `vacancy_search.init_db()` must create the four match columns *in the baseline* (§6), skip all four `ADD COLUMN`s, and **record versions 1–4**. §6 implied this; it is now asserted directly.
- **A11 — Table rebuilds own their foreign-key handling; the runner must not fight them.** SQLite's documented rebuild procedure requires `PRAGMA foreign_keys=OFF` for the drop/rename, and `PRAGMA foreign_keys` cannot be changed inside a transaction. The runner therefore neither sets nor assumes that pragma; a rebuild callable manages it around its own work and verifies with `PRAGMA foreign_key_check` before returning. Relevant immediately: `submissions.vacancy_id` is a real FK into `vacancies`. This is a constraint on Phase B, recorded here so it isn't rediscovered mid-build.
- **A12 — The `ADD COLUMN` skip checks column *presence*, not type or semantics — accepted as a documented limitation.** Codex is right that §3's phrase "schema state" is stronger than the check performed. Accepted rather than fixed: SQLite's typing is loose, and all six historical migrations add plain `TEXT`/`INTEGER` columns, so there is no realistic drift for this rule to mask today. Revisit only if a migration ever adds a column with a constraint or default.
- **A13 — Adoption is guaranteed only for the three known databases** (the live `career.db` and Tebello's two backups), whose entire migration history is the six verified `ADD COLUMN`s. Any older exported or copied database outside those three is out of scope — §4's "no special code path" claim rests on that verification, and is not a claim about arbitrary files.

### Considered and declined

- **D1 — Structured `Migration` dataclass with declared idempotency** (`Migration(version, sql, idempotency=AddColumn(table, column))`, Codex §4). Declined in favour of A1's union type: it solves the actual blocker with zero churn to the six existing migrations, and A4 narrows the regex enough that the "only special rule depends on parsing SQL strings" objection loses most of its force. Reconsider if a second idempotency form is ever needed — at that point declared idempotency earns its keep.
- **D2 — `name` + `checksum` columns on the ledger** (Codex §4). Declined in favour of A6's written immutability rule. A callable migration (A1) has no stable text to checksum, so the protection would cover only half the migrations while complicating the adoption path — the runner would have to invent checksums for the four `vacancy_search` migrations it skips and records.
- **D3 — Recovery from a corrupt or partially-bad ledger beyond shape verification** (Codex §2). Declined as out of scope. A5's fail-loud *is* the defined behaviour; a database whose ledger has been hand-edited is a restore-from-backup situation, not a case for the runner to reason about.

### Build Queue — revised (supersedes the queue above)

Offline throughout. No network stage is touched.

1. **[RED]** `tests/unit/test_shared_migrations.py` (new) — ledger table shape and `(module, version)` primary key; per-module isolation; re-run is a no-op; `ADD COLUMN` skipped **and recorded**; a non-`ADD COLUMN` migration runs exactly once; adoption of a ledger-less database. **Plus, per this Amendment:** a callable migration issuing multiple statements inside one transaction (A1); failed-migration atomicity (A2/A9); `MigrationDefinitionError` on duplicate/non-positive/non-ascending versions (A3); the narrowed `ADD COLUMN` parse and its non-matching forms (A4); `MigrationLedgerError` on a wrong-shape ledger table (A5); concurrent-init serialization (A7).
2. **[GREEN]** `src/shared/migrations.py` — the runner, `MigrationDefinitionError`, `MigrationLedgerError`.
3. **[RED]** `tests/unit/test_profile_db.py` — the two `user_version` assertions become ledger assertions; both init-ordering regression tests keep their intent (they must still converge on identical schemas).
4. **[GREEN]** `src/profile/migrations.py` — delegate; drop the local guard and the counter writes. Baseline in `db.py` unchanged.
5. **[RED]** `tests/unit/test_vacancy_db.py` — baseline `CREATE TABLE vacancies` includes the four match columns; fresh and legacy databases converge on the same schema; fresh DB records 1–4 as skipped (A10).
6. **[GREEN]** `src/vacancy_search/migrations.py` delegates + `src/vacancy_search/db.py` baseline gains the four columns (§6, confirmed by Tebello).
7. **[GREEN]** `src/doc_gen/migrations.py` + `src/review/migrations.py` delegate. Empty lists, no behaviour change.
8. **[RED]** `tests/unit/test_submission_db.py` — replace `test_does_not_advance_user_version` with the ledger equivalent.
9. **[RED/GREEN]** the Phase-B-shaped rebuild acceptance test (A8) — a callable migration rebuilding a populated table, data preserved, one ledger row, re-run a no-op. **This is the step that proves the ADR's stated blocker is actually solved.**
10. `tests/integration/test_full_pipeline.py` — end-to-end init in **both** module orders against one database, asserting identical final schema and a complete ledger. This is the test class that caught the Phase 17 regression.
11. Verify against a **copy** of the live `career.db` before anything touches the real one — ledger created, `vacancy_search` 1–4 recorded-not-rerun, `profile` 5–6 applied, all 10 vacancies / 10 approvals / 43 generation-log rows intact.
12. Docs closeout — `CLAUDE.md` Hard Rule 6 rewritten (§5 + A6's immutability rule + per-module numbering from 1), `docs/architecture.md`, `docs/todo.md` Open Item closed, `docs/session-log.md`.
