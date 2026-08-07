"""Shared migration runner — ADR-004.

`PRAGMA user_version` is a single integer per database file. Four modules
were each running their own copy of `if version > current: ...` against it,
which made it a multi-writer applied-migrations record it cannot be: it
stores one number, not a set, so it cannot answer the only question a
migration runner asks — *has this migration, from this module, already run on
this database?* A `schema_migrations(module, version, applied_at)` ledger can,
and version numbers become per-module as a result (ADR-004 §1).

The counter is frozen and never read or written here (§5). Whatever value a
database carries, it keeps, and it means nothing.

Two properties of Python's sqlite3 shape this module, both verified against
3.49.1 rather than assumed (ADR-004 §Amendment):

- `Connection.execute()` raises ProgrammingError on a multi-statement string.
  A migration payload of `str` alone therefore cannot express a table rebuild,
  which is what Phase B needs for the `submissions.outcome` CHECK. Hence A1:
  a payload is `str | Callable[[sqlite3.Connection], None]`.
- `executescript()` is not the way out — it issues an implicit COMMIT before
  running, so a rebuild that failed halfway would leave its earlier statements
  committed and the ledger inconsistent. Hence A2: one BEGIN IMMEDIATE per
  migration, with the DDL and its ledger row committing together or not at all.
"""

import re
import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone

MigrationPayload = str | Callable[[sqlite3.Connection], None]
Migration = tuple[int, MigrationPayload]

LEDGER_TABLE = "schema_migrations"
_LEDGER_COLUMNS = {"module", "version", "applied_at"}

_LEDGER_DDL = f"""
CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
    module     TEXT NOT NULL,
    version    INTEGER NOT NULL,
    applied_at TEXT NOT NULL,
    PRIMARY KEY (module, version)
)
"""

# A4: deliberately narrow. Simple unquoted identifiers only — quoted or
# schema-qualified names, IF NOT EXISTS, and embedded comments are not
# recognised and are not auto-skipped. They run under ordinary ledger gating
# and fail loudly rather than being silently assumed done.
_ADD_COLUMN = re.compile(
    r"^ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(\w+)\b", re.IGNORECASE
)


class MigrationError(Exception):
    """Base for migration-mechanism failures."""


class MigrationDefinitionError(MigrationError):
    """A module's MIGRATIONS list is malformed (A3)."""


class MigrationLedgerError(MigrationError):
    """The ledger table exists but is not the table we own (A5)."""


def _validate(module: str, migrations: list[Migration]) -> None:
    """A3: validate the list, don't sort it.

    Sorting would make list order non-authoritative and quietly absorb the
    mistake. A duplicate version is the dangerous case — the ledger would
    record the first and skip the second forever, which is the same silent
    class of failure the shared counter produced.
    """
    previous = 0
    for entry in migrations:
        version, _ = entry
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise MigrationDefinitionError(
                f"{module}: migration versions must be positive integers, got {version!r}"
            )
        if version <= previous:
            raise MigrationDefinitionError(
                f"{module}: migration versions must be strictly ascending — "
                f"{version} follows {previous}"
            )
        previous = version


def _ensure_ledger(conn: sqlite3.Connection) -> None:
    conn.execute(_LEDGER_DDL)
    info = list(conn.execute(f"PRAGMA table_info({LEDGER_TABLE})"))
    if {row[1] for row in info} != _LEDGER_COLUMNS:
        raise MigrationLedgerError(
            f"{LEDGER_TABLE} exists with an unexpected shape: "
            f"{sorted(row[1] for row in info)}. Refusing to use it as the migration ledger."
        )
    primary_key = {row[1]: row[5] for row in info}
    if primary_key.get("module") != 1 or primary_key.get("version") != 2:
        raise MigrationLedgerError(
            f"{LEDGER_TABLE} exists without a (module, version) primary key. "
            "Refusing to use it as the migration ledger."
        )


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def _already_satisfied(conn: sqlite3.Connection, payload: MigrationPayload) -> bool:
    """True when an ADD COLUMN migration's column is already present.

    Scoped to ADD COLUMN and nothing else, and never to a callable: no other
    migration form has a general "already done?" predicate, and from ADR-004
    forward none needs one, because the ledger gates them. This rule exists so
    adoption of a pre-ledger database needs no special code path (§4) — every
    migration in this project's history to date is an ADD COLUMN.

    It checks column *presence*, not type or semantics (A12, a documented
    limitation).
    """
    if not isinstance(payload, str):
        return False
    match = _ADD_COLUMN.match(payload.strip())
    return bool(match) and _column_exists(conn, match.group(1), match.group(2))


def _applied_versions(conn: sqlite3.Connection, module: str) -> set[int]:
    rows = conn.execute(
        f"SELECT version FROM {LEDGER_TABLE} WHERE module = ?", (module,)
    )
    return {row[0] for row in rows}


def apply_migrations(
    conn: sqlite3.Connection, module: str, migrations: list[Migration]
) -> None:
    """Apply `module`'s unrecorded migrations, in list order, on `conn`.

    Each migration runs in its own BEGIN IMMEDIATE transaction together with
    the ledger row recording it (A2). On failure the migration and its ledger
    row roll back as one, no later migration runs, and the exception
    propagates — so a re-run resumes from the failure rather than restarting
    (nothing already recorded is re-applied).

    Taking the write lock *before* reading the ledger is what makes concurrent
    callers safe (A7): two simultaneous `init_db()` calls serialize, and the
    second sees the rows the first recorded instead of both attempting the
    same DDL.
    """
    _validate(module, migrations)

    previous_isolation = conn.isolation_level
    conn.isolation_level = None  # we drive the transactions explicitly
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            _ensure_ledger(conn)
            applied = _applied_versions(conn, module)
            conn.execute("COMMIT")
        except Exception:
            conn.rollback()
            raise

        for version, payload in migrations:
            if version in applied:
                continue
            _apply_one(conn, module, version, payload)
    finally:
        conn.isolation_level = previous_isolation


def _apply_one(
    conn: sqlite3.Connection, module: str, version: int, payload: MigrationPayload
) -> None:
    conn.execute("BEGIN IMMEDIATE")
    try:
        if not _already_satisfied(conn, payload):
            if isinstance(payload, str):
                conn.execute(payload)
            else:
                payload(conn)
        conn.execute(
            f"INSERT INTO {LEDGER_TABLE} (module, version, applied_at) VALUES (?, ?, ?)",
            (module, version, datetime.now(timezone.utc).isoformat()),
        )
        conn.execute("COMMIT")
    except Exception:
        conn.rollback()
        raise
