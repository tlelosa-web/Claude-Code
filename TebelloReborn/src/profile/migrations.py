import sqlite3

from src.shared.migrations import apply_migrations as _apply

MODULE = "profile"

# Versions are per-module as of ADR-004 — `(profile, 5)` and
# `(vacancy_search, 5)` are different keys in the schema_migrations ledger, so
# there is no shared namespace left to collide in. 5 and 6 are kept rather than
# renumbered to 1 and 2 (ADR-004 §1): the numbers carry no global meaning any
# more, and renumbering would be churn with a real risk of getting the adoption
# of the live career.db wrong.
#
# Both columns are nullable: SQLite rejects ADD COLUMN NOT NULL without a
# default, and no migration can back-fill contact details only Tebello has.
# CandidateProfile.REQUIRED_FIELDS is what enforces presence going forward.
MIGRATIONS: list[tuple[int, str]] = [
    (5, "ALTER TABLE candidate_profile ADD COLUMN email TEXT"),
    (6, "ALTER TABLE candidate_profile ADD COLUMN phone TEXT"),
]


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply this module's migrations via the shared runner (ADR-004).

    The local column-existence guard that used to live here is now the runner's
    §3 rule, with one correction: a skipped ADD COLUMN is *recorded* as applied
    rather than silently passed over. `db.py`'s baseline CREATE TABLE still
    declares email/phone, so on a fresh database these two skip-and-record —
    belt-and-braces now rather than load-bearing, since the ledger no longer
    lets one module's versions strand another's.
    """
    _apply(conn, MODULE, MIGRATIONS)
