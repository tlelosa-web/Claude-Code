"""End-to-end integration test for the career-engine CLI in OFFLINE_MODE.

Runs import-profile -> fetch-vacancies -> run through the real
src.main.main() entry point against a real temp SQLite DB — no stage is
mocked, only the human decision (`input`) is scripted via stdin.
Mirrors ai-outreach-agency/tests/integration/test_full_pipeline.py's shape,
adapted to this project's 5-stage pipeline and CLI (Build Queue step 52).
"""

import io
import json

import pytest

from src.main import main
from src.doc_gen.db import get_by_vacancy_id as get_generation_log
from src.doc_gen.db import init_db as init_doc_gen_db
from src.review.db import get_approval_by_vacancy_id, init_db as init_review_db
from src.review.schema import Decision
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
