"""End-to-end integration test for the career-engine CLI in OFFLINE_MODE.

Runs import-profile -> fetch-vacancies -> run through the real
src.main.main() entry point against a real temp SQLite DB — no stage is
mocked, only the human decision (`input`) is scripted via stdin.
Mirrors ai-outreach-agency/tests/integration/test_full_pipeline.py's shape,
adapted to this project's 5-stage pipeline and CLI (Build Queue step 52).
"""

import io
import json
import sqlite3

import pytest

from src.main import main
from src.profile.db import init_db as init_profile_db
from src.doc_gen.db import get_by_vacancy_id as get_generation_log
from src.doc_gen.db import init_db as init_doc_gen_db
from src.review.db import get_approval_by_vacancy_id, init_db as init_review_db
from src.review.schema import Decision
from src.submission.db import (
    get_attempts_for_vacancy,
    init_db as init_submission_db,
)
from src.submission.schema import SubmissionMethod, SubmissionOutcome
from src.vacancy_search.db import get_by_id, get_by_status, init_db as init_vacancy_db


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "true")


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Real temp SQLite DB + a temp CWD, since doc_gen's PDF export writes
    to a relative `exports/` dir with no settings wiring yet — chdir keeps
    that side effect inside the test sandbox instead of the repo root."""
    path = tmp_path / "career.db"
    monkeypatch.setenv("DB_PATH", str(path))
    monkeypatch.chdir(tmp_path)
    return path


def _profile_json(tmp_path) -> str:
    data = {
        "name": "Tebello Lelosa",
        "region": "Gauteng, South Africa",
        "email": "tlelosa@gmail.com",
        "phone": "078 481 8711",
        "skills": ["Operations Management", "Lean Manufacturing"],
        "experience": [
            {
                "title": "Operations Foreman",
                "company": "Acme Engineering",
                "start_date": "2020-01",
            }
        ],
        "target_titles": [
            {"title": "Operations Foreman/Manager", "primary": True, "weight": 1.0}
        ],
        "industries": ["Manufacturing"],
    }
    path = tmp_path / "profile_seed.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def _import_and_fetch(tmp_path, db_path) -> int:
    """import-profile + fetch-vacancies via the real CLI, return the id of
    the first fetched (status=new) vacancy."""
    main(["import-profile", "--file", _profile_json(tmp_path)])
    main(["fetch-vacancies", "--limit", "3"])

    conn = init_vacancy_db(db_path)
    try:
        vacancy_id = get_by_status(conn, "new")[0].id
    finally:
        conn.close()
    return vacancy_id


class TestHappyPath:
    def test_run_approve_reaches_approved_status(self, tmp_path, monkeypatch, db_path):
        monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))
        vacancy_id = _import_and_fetch(tmp_path, db_path)

        main(["run", "--vacancy-id", str(vacancy_id)])

        conn = init_vacancy_db(db_path)
        try:
            final = get_by_id(conn, vacancy_id)
        finally:
            conn.close()
        assert final.status == "approved"
        assert final.score is not None

        review_conn = init_review_db(db_path)
        try:
            approval = get_approval_by_vacancy_id(review_conn, vacancy_id)
        finally:
            review_conn.close()
        assert approval is not None
        assert approval.decision == Decision.APPROVED

        doc_gen_conn = init_doc_gen_db(db_path)
        try:
            log_entries = get_generation_log(doc_gen_conn, vacancy_id)
        finally:
            doc_gen_conn.close()
        assert {e.doc_type for e in log_entries} == {"cv", "cover_letter"}
        assert all(e.status.value == "success" for e in log_entries)

        pdfs = list((tmp_path / "exports").glob("*.pdf"))
        assert len(pdfs) == 2

    def test_run_all_processes_every_new_vacancy(self, tmp_path, monkeypatch, db_path):
        monkeypatch.setattr("sys.stdin", io.StringIO("a\na\na\n"))
        main(["import-profile", "--file", _profile_json(tmp_path)])
        main(["fetch-vacancies", "--limit", "3"])

        main(["run-all"])

        conn = init_vacancy_db(db_path)
        try:
            still_new = get_by_status(conn, "new")
            approved = get_by_status(conn, "approved")
        finally:
            conn.close()
        assert still_new == []
        assert len(approved) == 3


class TestRejectionPath:
    def test_run_reject_leaves_vacancy_rejected_with_no_assets_lost(
        self, tmp_path, monkeypatch, db_path
    ):
        monkeypatch.setattr("sys.stdin", io.StringIO("r\n"))
        vacancy_id = _import_and_fetch(tmp_path, db_path)

        main(["run", "--vacancy-id", str(vacancy_id)])

        conn = init_vacancy_db(db_path)
        try:
            final = get_by_id(conn, vacancy_id)
        finally:
            conn.close()
        assert final.status == "rejected"

        review_conn = init_review_db(db_path)
        try:
            approval = get_approval_by_vacancy_id(review_conn, vacancy_id)
        finally:
            review_conn.close()
        assert approval is not None
        assert approval.decision == Decision.REJECTED


class TestOfflineIsolation:
    """Offline-First hard rule (CLAUDE.md): matching and doc-gen must never
    reach a real local Ollama daemon or spawn a real `claude` subprocess
    while OFFLINE_MODE is set, however deep the CLI call chain gets."""

    def test_zero_ollama_or_claude_code_calls_during_offline_run(
        self, tmp_path, monkeypatch, db_path
    ):
        monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))

        def _fail_ollama(*args, **kwargs):
            raise AssertionError("Real HTTP request attempted against Ollama")

        def _fail_claude_code(*args, **kwargs):
            raise AssertionError("Real subprocess spawned for headless Claude Code")

        monkeypatch.setattr("src.shared.ollama_client.requests.post", _fail_ollama)
        monkeypatch.setattr("src.doc_gen.runner.subprocess.run", _fail_claude_code)

        vacancy_id = _import_and_fetch(tmp_path, db_path)
        main(["run", "--vacancy-id", str(vacancy_id)])

        conn = init_vacancy_db(db_path)
        try:
            final = get_by_id(conn, vacancy_id)
        finally:
            conn.close()
        assert final.status == "approved"


class TestSubmissionStage:
    """Stage 6 end-to-end through the real CLI, fully offline.

    With no adapter registered, every approved application routes to manual —
    the whole point of this build. These assert the operator actually gets told
    that, and that the vacancy keeps saying it still needs action.
    """

    def _approved_vacancy_id(self, tmp_path, monkeypatch, db_path) -> int:
        monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))
        vacancy_id = _import_and_fetch(tmp_path, db_path)
        main(["run", "--vacancy-id", str(vacancy_id)])
        return vacancy_id

    def test_submit_records_not_supported_and_keeps_vacancy_approved(
        self, tmp_path, monkeypatch, db_path, capsys
    ):
        vacancy_id = self._approved_vacancy_id(tmp_path, monkeypatch, db_path)

        main(["submit", "--vacancy-id", str(vacancy_id)])

        conn = init_vacancy_db(db_path)
        try:
            final = get_by_id(conn, vacancy_id)
        finally:
            conn.close()
        assert final.status == "approved"

        submission_conn = init_submission_db(db_path)
        try:
            attempts = get_attempts_for_vacancy(submission_conn, vacancy_id)
        finally:
            submission_conn.close()
        assert len(attempts) == 1
        assert attempts[0].outcome == SubmissionOutcome.NOT_SUPPORTED
        assert attempts[0].method == SubmissionMethod.AUTO

        out = capsys.readouterr().out
        assert "submit this one by hand" in out
        assert final.url in out

    def test_submit_refuses_a_vacancy_that_never_reached_the_gate(
        self, tmp_path, db_path
    ):
        """Hard Rule 1, end to end: a freshly fetched vacancy has no path to a
        submission, and nothing is recorded for it."""
        vacancy_id = _import_and_fetch(tmp_path, db_path)

        with pytest.raises(SystemExit):
            main(["submit", "--vacancy-id", str(vacancy_id)])

        submission_conn = init_submission_db(db_path)
        try:
            attempts = get_attempts_for_vacancy(submission_conn, vacancy_id)
        finally:
            submission_conn.close()
        assert attempts == []

    def test_manual_submission_advances_the_vacancy(
        self, tmp_path, monkeypatch, db_path
    ):
        vacancy_id = self._approved_vacancy_id(tmp_path, monkeypatch, db_path)

        main(["submit", "--vacancy-id", str(vacancy_id), "--manual"])

        conn = init_vacancy_db(db_path)
        try:
            final = get_by_id(conn, vacancy_id)
        finally:
            conn.close()
        assert final.status == "submitted"

    def test_submit_all_reports_a_summary_without_failing(
        self, tmp_path, monkeypatch, db_path, capsys
    ):
        monkeypatch.setattr("sys.stdin", io.StringIO("a\na\na\n"))
        main(["import-profile", "--file", _profile_json(tmp_path)])
        main(["fetch-vacancies", "--limit", "3"])
        main(["run-all"])

        main(["submit", "--all"])  # must not raise SystemExit

        out = capsys.readouterr().out
        assert "not supported: 3" in out
        assert "failed: 0" in out

        conn = init_vacancy_db(db_path)
        try:
            assert len(get_by_status(conn, "approved")) == 3
        finally:
            conn.close()


class TestMigrationLedgerAcrossModules:
    """ADR-004 build step 10. This is the test class that caught the Phase 17
    regression — a fresh install where `import-profile` ran first came out with
    a `vacancies` table that had no `score` column, because profile's
    migrations 5-6 advanced the shared PRAGMA user_version past
    vacancy_search's 1-4 and skipped them silently.

    No unit test caught it: each module's migrations were correct in isolation,
    and the bug only existed in the interaction between two of them on one
    database. So the proof that ADR-004 did its job belongs here, exercising
    every module's real init_db() against a single file in both orders.
    """

    MODULES = {
        "profile": init_profile_db,
        "vacancy_search": init_vacancy_db,
        "doc_gen": init_doc_gen_db,
        "review": init_review_db,
        "submission": init_submission_db,
    }

    MATCH_COLUMNS = {"score", "strengths", "weaknesses", "recommendation"}

    def _init_all(self, db_path, order):
        for name in order:
            conn = self.MODULES[name](db_path)
            conn.close()

    def _schema(self, db_path):
        """Every table's full column set — the thing that must not depend on
        which module happened to run first."""
        conn = sqlite3.connect(str(db_path))
        try:
            tables = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            return {
                table: {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
                for table in tables
            }
        finally:
            conn.close()

    def _ledger(self, db_path):
        conn = sqlite3.connect(str(db_path))
        try:
            return {
                (row[0], row[1])
                for row in conn.execute("SELECT module, version FROM schema_migrations")
            }
        finally:
            conn.close()

    def test_both_init_orders_converge_on_an_identical_schema(self, tmp_path):
        documented = ["profile", "vacancy_search", "doc_gen", "review", "submission"]
        reversed_order = list(reversed(documented))

        first = tmp_path / "documented.db"
        second = tmp_path / "reversed.db"
        self._init_all(first, documented)
        self._init_all(second, reversed_order)

        assert self._schema(first) == self._schema(second)

    def test_vacancies_has_its_match_columns_whichever_module_ran_first(self, tmp_path):
        """The Phase 17 regression itself. `import-profile` is the documented
        first command, and profile owns the highest version numbers."""
        db_path = tmp_path / "career.db"
        self._init_all(db_path, ["profile", "vacancy_search", "doc_gen", "review"])

        assert self.MATCH_COLUMNS <= self._schema(db_path)["vacancies"]

    def test_the_ledger_records_every_module_that_owns_migrations(self, tmp_path):
        db_path = tmp_path / "career.db"
        self._init_all(
            db_path, ["profile", "vacancy_search", "doc_gen", "review", "submission"]
        )

        assert self._ledger(db_path) == {
            ("vacancy_search", 1),
            ("vacancy_search", 2),
            ("vacancy_search", 3),
            ("vacancy_search", 4),
            ("profile", 5),
            ("profile", 6),
            # Phase B. `(submission, 1)` sitting beside `(vacancy_search, 1)` is
            # the ledger's whole point — under the old shared counter this
            # migration could not have existed at all.
            ("submission", 1),
        }

    def test_re_initialising_every_module_is_a_no_op(self, tmp_path):
        db_path = tmp_path / "career.db"
        order = ["profile", "vacancy_search", "doc_gen", "review", "submission"]
        self._init_all(db_path, order)
        schema_before = self._schema(db_path)

        self._init_all(db_path, order)
        self._init_all(db_path, list(reversed(order)))

        assert self._schema(db_path) == schema_before
        assert len(self._ledger(db_path)) == 7

    def test_the_frozen_counter_is_never_written(self, tmp_path):
        """ADR-004 §5. A fresh database stays at 0 forever now."""
        db_path = tmp_path / "career.db"
        self._init_all(db_path, ["profile", "vacancy_search", "doc_gen", "review"])

        conn = sqlite3.connect(str(db_path))
        try:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        finally:
            conn.close()
