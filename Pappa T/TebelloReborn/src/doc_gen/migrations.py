import sqlite3

from src.shared.migrations import apply_migrations as _apply

MODULE = "doc_gen"

# Empty by design. `generation_log`'s CREATE TABLE IF NOT EXISTS lives in
# db.py's init_db(), per this project's baseline-vs-migration convention — a
# net-new table needs no migration. This list holds schema changes made *after*
# that baseline; versions start at 1 and are scoped to this module (ADR-004 §1).
MIGRATIONS: list[tuple[int, str]] = []


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply this module's migrations via the shared runner (ADR-004)."""
    _apply(conn, MODULE, MIGRATIONS)
