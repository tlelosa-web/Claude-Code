"""Migrations for the submission module (ADR-004).

This module had no migrations.py until Phase B, and the reason it has one now
is worth stating: `submissions` was net-new in Stage 6, so its CREATE TABLE
belongs in `init_db()` and needed no migration. Phase B *changes* that table —
`outcome` gains `pending_review` (indeed-submit-adapter.md Amendment A3) — and
SQLite cannot alter a CHECK constraint in place. That is the create/copy/drop/
rename rebuild, which is exactly the case ADR-004's runner was built and proven
against (`TestPhaseBShapedRebuild` in tests/unit/test_shared_migrations.py).

Version 1 is correct here. Under the ledger, versions are per-module —
`(submission, 1)` and `(vacancy_search, 1)` are different keys — so the old
hazard that made an empty stub safer (a `(1, ...)` entry stranded forever
behind a shared counter already at 4) no longer exists.

The two net-new Phase B tables, `submission_preps` and `screening_questions`,
are deliberately *not* here: a net-new table's CREATE TABLE IF NOT EXISTS goes
in `init_db()`, per CLAUDE.md Hard Rule 6.
"""

import sqlite3

from src.shared.migrations import apply_migrations as _apply

MODULE = "submission"

# Kept in sync with SubmissionOutcome by db.py's drift guard, which fails at
# init if the stored DDL and the enum ever disagree.
_NEW_OUTCOME_CHECK = "'submitted','failed','not_supported','pending_review'"


def _outcome_check_is_current(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='submissions'"
    ).fetchone()
    return row is not None and "pending_review" in row[0]


def _widen_outcome_check(conn: sqlite3.Connection) -> None:
    """Rebuild `submissions` with `pending_review` added to the outcome CHECK.

    Self-guarding, because this migration runs against two shapes of database.
    On a fresh one, `init_db()`'s baseline CREATE TABLE has already produced the
    widened table, so there is nothing to rebuild and the run only records the
    ledger row. On a database where `submit` ran before Phase B, the baseline
    was a no-op against the old 3-value table and this is what actually widens
    it.

    `PRAGMA foreign_keys` is a no-op inside a transaction, and the runner has
    already opened one, so SQLite's documented "turn foreign keys off first"
    rebuild step is unavailable. `defer_foreign_keys` is the one settable
    mid-transaction — it postpones enforcement to COMMIT — and is what makes the
    DROP/RENAME pair survivable. Same shape as TestPhaseBShapedRebuild.
    """
    if _outcome_check_is_current(conn):
        return

    conn.execute("PRAGMA defer_foreign_keys = ON")
    conn.execute(f"""
        CREATE TABLE submissions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
            method TEXT NOT NULL CHECK (method IN ('auto','manual')),
            outcome TEXT NOT NULL CHECK (outcome IN ({_NEW_OUTCOME_CHECK})),
            detail TEXT,
            attempted_at TEXT NOT NULL
        )
    """)
    conn.execute(
        "INSERT INTO submissions_new "
        "(id, vacancy_id, method, outcome, detail, attempted_at) "
        "SELECT id, vacancy_id, method, outcome, detail, attempted_at "
        "FROM submissions"
    )
    conn.execute("DROP TABLE submissions")
    conn.execute("ALTER TABLE submissions_new RENAME TO submissions")

    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        # Raising rolls the whole migration and its ledger row back together, so
        # a re-run retries rather than recording a rebuild that corrupted rows.
        raise sqlite3.IntegrityError(
            f"widening submissions.outcome left foreign-key violations: {violations}"
        )


MIGRATIONS = [
    (1, _widen_outcome_check),
]


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply this module's migrations via the shared runner (ADR-004)."""
    _apply(conn, MODULE, MIGRATIONS)
