"""RED: src/shared/migrations.py doesn't exist yet — these imports must fail
first.

The shared migration runner from ADR-004. `PRAGMA user_version` is a single
integer per database file, and four modules were using it as a multi-writer
applied-migrations record; it cannot answer "has THIS migration, from THIS
module, already run on THIS database?" because it stores one number, not a
set. A `schema_migrations(module, version, applied_at)` ledger can.

Tests below cover ADR-004 §1-§4 plus the Amendment's A1-A7. The Amendment
findings that shape this file, verified against sqlite3 3.49.1 before it was
written:

- `Connection.execute()` raises ProgrammingError on a multi-statement string,
  so a migration payload of `str` alone cannot carry Phase B's table rebuild
  (A1 — payload becomes `str | Callable[[sqlite3.Connection], None]`).
- `executescript()` issues an implicit COMMIT before running, which would
  void any "commit once at the end" guarantee and leave a half-applied
  rebuild with a ledger row claiming success (A2 — per-migration
  BEGIN IMMEDIATE; DDL and its ledger row commit together or not at all).
"""

import sqlite3

import pytest

from src.shared.migrations import (
    MigrationDefinitionError,
    MigrationLedgerError,
    apply_migrations,
)


def _conn(tmp_path, name="career.db", **kwargs):
    conn = sqlite3.connect(tmp_path / name, **kwargs)
    conn.execute("CREATE TABLE widgets (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    return conn


def _ledger(conn, module=None):
    """Return {(module, version)} recorded in the ledger, optionally filtered."""
    if module is None:
        rows = conn.execute("SELECT module, version FROM schema_migrations")
    else:
        rows = conn.execute(
            "SELECT module, version FROM schema_migrations WHERE module = ?", (module,)
        )
    return {(row[0], row[1]) for row in rows}


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


class TestLedgerTable:
    def test_creates_ledger_table_with_module_version_primary_key(self, tmp_path):
        conn = _conn(tmp_path)
        apply_migrations(conn, "widgets", [])

        cols = {
            row[1]: row for row in conn.execute("PRAGMA table_info(schema_migrations)")
        }
        assert set(cols) == {"module", "version", "applied_at"}
        # (module, version) composite primary key — the whole point of the ledger.
        assert cols["module"][5] == 1
        assert cols["version"][5] == 2
        assert cols["applied_at"][3] == 1  # NOT NULL

    def test_records_applied_at_as_a_timestamp(self, tmp_path):
        conn = _conn(tmp_path)
        apply_migrations(
            conn, "widgets", [(1, "ALTER TABLE widgets ADD COLUMN a TEXT")]
        )

        applied_at = conn.execute(
            "SELECT applied_at FROM schema_migrations"
        ).fetchone()[0]
        assert applied_at
        # ISO-8601, tz-aware — same convention as SubmissionAttempt.attempted_at.
        assert "T" in applied_at
        assert (
            applied_at.endswith("Z") or "+" in applied_at[10:] or "-" in applied_at[10:]
        )

    def test_never_touches_user_version(self, tmp_path):
        """ADR-004 §5: the counter is frozen and demoted to a historical
        artifact. The runner neither reads nor writes it."""
        conn = _conn(tmp_path)
        conn.execute("PRAGMA user_version = 4")
        conn.commit()

        apply_migrations(
            conn, "widgets", [(1, "ALTER TABLE widgets ADD COLUMN a TEXT")]
        )

        assert conn.execute("PRAGMA user_version").fetchone()[0] == 4

    def test_rejects_a_pre_existing_ledger_table_of_the_wrong_shape(self, tmp_path):
        """A5: verify the table rather than trusting any table by that name."""
        conn = _conn(tmp_path)
        conn.execute("CREATE TABLE schema_migrations (whatever TEXT)")
        conn.commit()

        with pytest.raises(MigrationLedgerError):
            apply_migrations(
                conn, "widgets", [(1, "ALTER TABLE widgets ADD COLUMN a TEXT")]
            )


class TestPerModuleIsolation:
    def test_same_version_number_in_two_modules_both_apply(self, tmp_path):
        """The headline fix. Under the shared counter, whichever module ran
        second was silently skipped."""
        conn = _conn(tmp_path)
        conn.execute("CREATE TABLE gadgets (id INTEGER PRIMARY KEY)")
        conn.commit()

        apply_migrations(
            conn, "widgets", [(1, "ALTER TABLE widgets ADD COLUMN a TEXT")]
        )
        apply_migrations(
            conn, "gadgets", [(1, "ALTER TABLE gadgets ADD COLUMN b TEXT")]
        )

        assert "a" in _columns(conn, "widgets")
        assert "b" in _columns(conn, "gadgets")
        assert _ledger(conn) == {("widgets", 1), ("gadgets", 1)}

    def test_a_module_with_higher_versions_does_not_strand_a_lower_one(self, tmp_path):
        """The exact Phase 17 regression, in miniature: profile (5-6) ran
        before vacancy_search (1-4) on a fresh database and skipped it."""
        conn = _conn(tmp_path)
        conn.execute("CREATE TABLE gadgets (id INTEGER PRIMARY KEY)")
        conn.commit()

        apply_migrations(
            conn, "profile", [(5, "ALTER TABLE gadgets ADD COLUMN email TEXT")]
        )
        apply_migrations(
            conn,
            "vacancy_search",
            [(1, "ALTER TABLE widgets ADD COLUMN score INTEGER")],
        )

        assert "score" in _columns(conn, "widgets")
        assert _ledger(conn) == {("profile", 5), ("vacancy_search", 1)}


class TestIdempotence:
    def test_re_running_is_a_no_op(self, tmp_path):
        conn = _conn(tmp_path)
        migrations = [(1, "ALTER TABLE widgets ADD COLUMN a TEXT")]

        apply_migrations(conn, "widgets", migrations)
        apply_migrations(conn, "widgets", migrations)
        apply_migrations(conn, "widgets", migrations)

        assert _ledger(conn, "widgets") == {("widgets", 1)}
        assert sorted(_columns(conn, "widgets")) == ["a", "id", "name"]

    def test_a_non_add_column_migration_runs_exactly_once(self, tmp_path):
        """No column-existence predicate exists for these — the ledger alone
        gates them. Running CREATE INDEX twice without IF NOT EXISTS raises."""
        conn = _conn(tmp_path)
        migrations = [(1, "CREATE INDEX idx_widgets_name ON widgets(name)")]

        apply_migrations(conn, "widgets", migrations)
        apply_migrations(conn, "widgets", migrations)  # must not re-execute

        assert _ledger(conn, "widgets") == {("widgets", 1)}


class TestAddColumnAutoSkip:
    def test_add_column_on_an_existing_column_is_skipped_but_recorded(self, tmp_path):
        """ADR-004 §3. Recorded, not silently passed over — this is what makes
        §4's adoption of the live career.db need no special code path."""
        conn = _conn(tmp_path)
        conn.execute("ALTER TABLE widgets ADD COLUMN a TEXT")  # baseline already has it
        conn.commit()

        apply_migrations(
            conn, "widgets", [(1, "ALTER TABLE widgets ADD COLUMN a TEXT")]
        )

        assert _ledger(conn, "widgets") == {("widgets", 1)}

    def test_adopts_a_ledgerless_database_whose_columns_already_exist(self, tmp_path):
        """§4's table, in miniature: the live career.db has vacancy_search's
        four columns but no ledger. They must record without re-running, while
        genuinely-absent ones apply."""
        conn = _conn(tmp_path)
        conn.execute("ALTER TABLE widgets ADD COLUMN score INTEGER")
        conn.commit()

        apply_migrations(
            conn,
            "vacancy_search",
            [
                (1, "ALTER TABLE widgets ADD COLUMN score INTEGER"),
                (2, "ALTER TABLE widgets ADD COLUMN strengths TEXT"),
            ],
        )

        assert _ledger(conn, "vacancy_search") == {
            ("vacancy_search", 1),
            ("vacancy_search", 2),
        }
        assert {"score", "strengths"} <= _columns(conn, "widgets")

    def test_auto_skip_does_not_recognise_quoted_identifiers(self, tmp_path):
        """A4: the auto-skip is narrowed to simple unquoted identifiers and
        documented as the only supported form. Anything else is not skipped —
        it runs, and fails loudly, rather than being silently assumed done."""
        conn = _conn(tmp_path)
        conn.execute("ALTER TABLE widgets ADD COLUMN a TEXT")
        conn.commit()

        with pytest.raises(sqlite3.OperationalError):
            apply_migrations(
                conn, "widgets", [(1, 'ALTER TABLE "widgets" ADD COLUMN "a" TEXT')]
            )

    def test_auto_skip_never_applies_to_a_callable(self, tmp_path):
        """A4: callables are gated by the ledger alone."""
        calls = []

        def migration(conn):
            calls.append(1)
            conn.execute("ALTER TABLE widgets ADD COLUMN a TEXT")

        conn = _conn(tmp_path)
        apply_migrations(conn, "widgets", [(1, migration)])
        apply_migrations(conn, "widgets", [(1, migration)])

        assert calls == [1]


class TestCallableMigrations:
    def test_a_callable_may_issue_multiple_statements(self, tmp_path):
        """A1 — the blocker. `Connection.execute()` raises ProgrammingError on
        a multi-statement string, so Phase B's rebuild has to arrive as a
        callable. Asserted here against the real sqlite3 rather than assumed."""
        conn = _conn(tmp_path)
        conn.execute("INSERT INTO widgets (name) VALUES ('keep me')")
        conn.commit()

        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("CREATE TABLE x (a); CREATE TABLE y (b);")

        def rebuild(conn):
            conn.execute(
                "CREATE TABLE widgets_new (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT INTO widgets_new (id, name) SELECT id, name FROM widgets"
            )
            conn.execute("DROP TABLE widgets")
            conn.execute("ALTER TABLE widgets_new RENAME TO widgets")

        apply_migrations(conn, "widgets", [(1, rebuild)])

        assert _ledger(conn, "widgets") == {("widgets", 1)}
        assert conn.execute("SELECT name FROM widgets").fetchall() == [("keep me",)]

    def test_a_callable_runs_inside_the_runners_transaction(self, tmp_path):
        """A2: its writes must be rolled back with the ledger row if it raises
        partway through — which is precisely what executescript() could not
        give us, since it commits before running."""
        conn = _conn(tmp_path)

        def half_done(conn):
            conn.execute("CREATE TABLE leftover (a TEXT)")
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            apply_migrations(conn, "widgets", [(1, half_done)])

        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "leftover" not in tables
        assert _ledger(conn, "widgets") == set()


class TestFailureAtomicity:
    def test_a_failed_migration_is_not_recorded(self, tmp_path):
        """A9."""
        conn = _conn(tmp_path)

        with pytest.raises(sqlite3.OperationalError):
            apply_migrations(
                conn, "widgets", [(1, "ALTER TABLE nonexistent ADD COLUMN a TEXT")]
            )

        assert _ledger(conn, "widgets") == set()

    def test_migrations_after_a_failure_do_not_run(self, tmp_path):
        """A9: no half-declared-complete schema."""
        conn = _conn(tmp_path)

        with pytest.raises(sqlite3.OperationalError):
            apply_migrations(
                conn,
                "widgets",
                [
                    (1, "ALTER TABLE widgets ADD COLUMN a TEXT"),
                    (2, "ALTER TABLE nonexistent ADD COLUMN b TEXT"),
                    (3, "ALTER TABLE widgets ADD COLUMN c TEXT"),
                ],
            )

        assert _ledger(conn, "widgets") == {("widgets", 1)}
        assert "a" in _columns(conn, "widgets")
        assert "c" not in _columns(conn, "widgets")

    def test_a_failed_run_can_be_resumed(self, tmp_path):
        """A2: earlier migrations stay applied AND recorded, so a re-run picks
        up where it stopped rather than restarting."""
        conn = _conn(tmp_path)
        broken = [
            (1, "ALTER TABLE widgets ADD COLUMN a TEXT"),
            (2, "ALTER TABLE nonexistent ADD COLUMN b TEXT"),
        ]
        with pytest.raises(sqlite3.OperationalError):
            apply_migrations(conn, "widgets", broken)

        fixed = [
            (1, "ALTER TABLE widgets ADD COLUMN a TEXT"),
            (2, "ALTER TABLE widgets ADD COLUMN b TEXT"),
        ]
        apply_migrations(conn, "widgets", fixed)

        assert _ledger(conn, "widgets") == {("widgets", 1), ("widgets", 2)}
        assert {"a", "b"} <= _columns(conn, "widgets")


class TestDefinitionValidation:
    """A3: validate the list, don't sort it. Sorting would make list order
    non-authoritative and hide the mistake."""

    def test_duplicate_versions_within_a_module_raise(self, tmp_path):
        conn = _conn(tmp_path)
        with pytest.raises(MigrationDefinitionError):
            apply_migrations(
                conn,
                "widgets",
                [
                    (1, "ALTER TABLE widgets ADD COLUMN a TEXT"),
                    (1, "ALTER TABLE widgets ADD COLUMN b TEXT"),
                ],
            )

    def test_out_of_order_versions_raise(self, tmp_path):
        conn = _conn(tmp_path)
        with pytest.raises(MigrationDefinitionError):
            apply_migrations(
                conn,
                "widgets",
                [
                    (2, "ALTER TABLE widgets ADD COLUMN b TEXT"),
                    (1, "ALTER TABLE widgets ADD COLUMN a TEXT"),
                ],
            )

    def test_non_positive_versions_raise(self, tmp_path):
        conn = _conn(tmp_path)
        with pytest.raises(MigrationDefinitionError):
            apply_migrations(
                conn, "widgets", [(0, "ALTER TABLE widgets ADD COLUMN a TEXT")]
            )

    def test_validation_happens_before_anything_is_applied(self, tmp_path):
        conn = _conn(tmp_path)
        with pytest.raises(MigrationDefinitionError):
            apply_migrations(
                conn,
                "widgets",
                [
                    (1, "ALTER TABLE widgets ADD COLUMN a TEXT"),
                    (1, "ALTER TABLE widgets ADD COLUMN b TEXT"),
                ],
            )

        assert "a" not in _columns(conn, "widgets")

    def test_an_empty_migration_list_is_valid(self, tmp_path):
        """doc_gen/ and review/ both ship empty lists."""
        conn = _conn(tmp_path)
        apply_migrations(conn, "doc_gen", [])

        assert _ledger(conn, "doc_gen") == set()


class TestConcurrency:
    def test_takes_the_write_lock_before_applying_anything(self, tmp_path):
        """A7: BEGIN IMMEDIATE up front, so two simultaneous init_db() calls
        serialize instead of both attempting the same DDL. If the lock can't be
        had, nothing is applied and nothing is recorded."""
        holder = _conn(tmp_path)
        holder.isolation_level = None
        holder.execute("BEGIN IMMEDIATE")

        conn = sqlite3.connect(tmp_path / "career.db", timeout=0)

        with pytest.raises(sqlite3.OperationalError):
            apply_migrations(
                conn, "widgets", [(1, "ALTER TABLE widgets ADD COLUMN a TEXT")]
            )

        holder.rollback()
        assert "a" not in _columns(conn, "widgets")


class TestPhaseBShapedRebuild:
    """A8 — the acceptance test the ADR's stated blocker demands.

    Phase B adds `pending_review` to the `submissions.outcome` CHECK, and
    SQLite cannot alter a CHECK in place: it is the create/copy/drop/rename
    rebuild. This models that exact shape — a populated child table with a
    foreign key and a CHECK — and proves the runner carries it. Without this,
    the ADR's whole premise is asserted but never demonstrated.
    """

    OLD_CHECK = "'submitted', 'failed', 'not_supported'"
    NEW_CHECK = "'submitted', 'failed', 'not_supported', 'pending_review'"

    def _seed(self, tmp_path):
        conn = sqlite3.connect(tmp_path / "career.db")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("CREATE TABLE vacancies (id INTEGER PRIMARY KEY, company TEXT)")
        conn.execute(f"""
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
                outcome TEXT NOT NULL CHECK (outcome IN ({self.OLD_CHECK})),
                attempted_at TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO vacancies (id, company) VALUES (1, 'Utopia')")
        conn.execute(
            "INSERT INTO submissions (vacancy_id, outcome, attempted_at) "
            "VALUES (1, 'not_supported', '2026-08-06T00:00:00+00:00')"
        )
        conn.commit()
        return conn

    def _rebuild(self, conn):
        """The 12-step rebuild, as a callable (A1).

        `PRAGMA foreign_keys` is a no-op inside a transaction, so the documented
        "turn it off first" step is unavailable to a migration the runner has
        already wrapped. `defer_foreign_keys` is the one that *is* settable
        mid-transaction — it postpones enforcement to COMMIT — which is what
        A11's "the rebuild owns its foreign-key handling" means in practice.
        """
        conn.execute("PRAGMA defer_foreign_keys = ON")
        conn.execute(f"""
            CREATE TABLE submissions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
                outcome TEXT NOT NULL CHECK (outcome IN ({self.NEW_CHECK})),
                attempted_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO submissions_new (id, vacancy_id, outcome, attempted_at) "
            "SELECT id, vacancy_id, outcome, attempted_at FROM submissions"
        )
        conn.execute("DROP TABLE submissions")
        conn.execute("ALTER TABLE submissions_new RENAME TO submissions")
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise AssertionError(f"rebuild left FK violations: {violations}")

    def test_the_old_check_really_does_reject_the_new_value(self, tmp_path):
        """Establishes the premise — otherwise the test below proves nothing."""
        conn = self._seed(tmp_path)

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO submissions (vacancy_id, outcome, attempted_at) "
                "VALUES (1, 'pending_review', '2026-08-07T00:00:00+00:00')"
            )

    def test_rebuild_widens_the_check_and_preserves_existing_rows(self, tmp_path):
        conn = self._seed(tmp_path)

        apply_migrations(conn, "submission", [(1, self._rebuild)])

        assert conn.execute(
            "SELECT id, vacancy_id, outcome FROM submissions"
        ).fetchall() == [(1, 1, "not_supported")]
        conn.execute(
            "INSERT INTO submissions (vacancy_id, outcome, attempted_at) "
            "VALUES (1, 'pending_review', '2026-08-07T00:00:00+00:00')"
        )
        assert _ledger(conn, "submission") == {("submission", 1)}

    def test_rebuild_records_exactly_one_ledger_row_and_reruns_as_a_no_op(
        self, tmp_path
    ):
        conn = self._seed(tmp_path)
        migrations = [(1, self._rebuild)]

        apply_migrations(conn, "submission", migrations)
        apply_migrations(conn, "submission", migrations)  # must not rebuild again

        assert _ledger(conn, "submission") == {("submission", 1)}
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "submissions_new" not in tables
        assert conn.execute("SELECT count(*) FROM submissions").fetchone()[0] == 1

    def test_the_rebuilt_table_still_enforces_its_foreign_key(self, tmp_path):
        """A11: constraints must survive the rebuild, not just the data."""
        conn = self._seed(tmp_path)

        apply_migrations(conn, "submission", [(1, self._rebuild)])

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO submissions (vacancy_id, outcome, attempted_at) "
                "VALUES (999, 'submitted', '2026-08-07T00:00:00+00:00')"
            )

    def test_a_failed_rebuild_leaves_the_original_table_untouched(self, tmp_path):
        """The failure mode Codex named: a rebuild can fail after creating the
        new table, after copying, or after the drop. A2 makes all three the
        same outcome — full rollback, nothing recorded, no leftovers."""
        conn = self._seed(tmp_path)

        def failing_rebuild(conn):
            self._rebuild(conn)
            raise RuntimeError("failed after the rename")

        with pytest.raises(RuntimeError):
            apply_migrations(conn, "submission", [(1, failing_rebuild)])

        assert _ledger(conn, "submission") == set()
        assert conn.execute("SELECT outcome FROM submissions").fetchall() == [
            ("not_supported",)
        ]
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO submissions (vacancy_id, outcome, attempted_at) "
                "VALUES (1, 'pending_review', '2026-08-07T00:00:00+00:00')"
            )
