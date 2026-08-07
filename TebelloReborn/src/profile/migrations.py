import re
import sqlite3

# Versions are GLOBAL, not per-module: profile/, vacancy_search/, doc_gen/ and
# review/ each own a separate MIGRATIONS list but read and write the same
# PRAGMA user_version on the same database (CLAUDE.md Hard Rule 6).
# vacancy_search holds 1-4 and the live career.db is at 4, so numbering these
# (1, ...) and (2, ...) — the obvious move — would make apply_migrations'
# `if version > current` skip them forever, silently, with no error at all.
#
# Both columns are nullable: SQLite rejects ADD COLUMN NOT NULL without a
# default, and no migration can back-fill contact details only Tebello has.
# CandidateProfile.REQUIRED_FIELDS is what enforces presence going forward.
MIGRATIONS: list[tuple[int, str]] = [
    (5, "ALTER TABLE candidate_profile ADD COLUMN email TEXT"),
    (6, "ALTER TABLE candidate_profile ADD COLUMN phone TEXT"),
]

_ADD_COLUMN = re.compile(r"ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(\w+)", re.IGNORECASE)


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply this module's migrations, gating on the actual schema rather than
    on `user_version` alone.

    The counter is shared across every module (Hard Rule 6) but the migration
    lists are not, so the counter alone is not a safe gate in either direction:

    - It can be *ahead* of us. Another module may already have advanced it past
      our versions on a database where our columns were never added.
    - Advancing it ourselves can strand *another* module. `profile` owns the
      highest versions (5-6) and `import-profile` is the documented first
      command, so on a fresh database this used to jump 0 -> 6 before
      `vacancy_search` ever ran — silently skipping its migrations 1-4, whose
      columns exist nowhere else (its baseline CREATE TABLE omits them). The
      result was a `vacancies` table with no `score` column and an IndexError
      on the first read.

    So: skip a migration whose column is already present, and only advance the
    counter for migrations we actually ran. A database that reaches our target
    shape without us is left at whatever version it had, free for the modules
    holding lower numbers to apply theirs.
    """
    current = conn.execute("PRAGMA user_version").fetchone()[0]

    for version, sql in MIGRATIONS:
        match = _ADD_COLUMN.match(sql.strip())
        if match and _column_exists(conn, match.group(1), match.group(2)):
            continue
        if version > current:
            conn.execute(sql)
            conn.execute(f"PRAGMA user_version = {version}")

    conn.commit()
