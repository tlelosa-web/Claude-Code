import sqlite3

from src.shared.migrations import apply_migrations as _apply

MODULE = "vacancy_search"

# Versions are per-module as of ADR-004 and kept rather than renumbered (§1).
#
# These four columns are also declared in db.py's baseline CREATE TABLE as of
# ADR-004 §6. They used to live here and nowhere else, which is what made the
# Phase 17 regression fatal instead of cosmetic: a module that advanced the
# shared counter past 4 caused all four to be skipped, leaving `vacancies` with
# no `score` column at all and an IndexError on the first read. The duplication
# is safe — the runner skips an ADD COLUMN whose column already exists and
# records it as applied (§3).
MIGRATIONS: list[tuple[int, str]] = [
    (1, "ALTER TABLE vacancies ADD COLUMN score INTEGER"),
    (2, "ALTER TABLE vacancies ADD COLUMN strengths TEXT"),
    (3, "ALTER TABLE vacancies ADD COLUMN weaknesses TEXT"),
    (4, "ALTER TABLE vacancies ADD COLUMN recommendation TEXT"),
]


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply this module's migrations via the shared runner (ADR-004)."""
    _apply(conn, MODULE, MIGRATIONS)
