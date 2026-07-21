import sqlite3

MIGRATIONS: list[tuple[int, str]] = []


def apply_migrations(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version, sql in MIGRATIONS:
        if version > current:
            conn.execute(sql)
            conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()
